import httpx
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from django.conf import settings
from django.core.cache import cache
from constants.metabase_constants import MetabaseEndpoints
from functools import lru_cache
from datetime import datetime, timedelta

from utils.logging import metabase_agent_logging
from constants.metabase_schemas import DatasetQuery


logging = metabase_agent_logging()


class MetabaseAPIError(Exception):
    """Custom exception for Metabase API errors"""

    pass


class MetabaseAPIService:
    def __init__(self):
        self.base_url: str = settings.METABASE_BASE_URL.rstrip("/")
        self.session_token: str = settings.METABASE_API_KEY
        self.headers = {
            "x-api-key": self.session_token,
            "Content-Type": "application/json",
        }
        self.default_timeout = 10.0  # Default timeout in seconds
        self._client = None  # Lazy-loaded HTTP client

    async def get_client(self) -> httpx.AsyncClient:
        """Get or create a persistent HTTP client"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.default_timeout)
        return self._client

    async def close(self):
        """Close the HTTP client"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def _make_request(
        self, method: str, endpoint: str, params: Dict = None, json_data: Dict = None
    ) -> Dict:
        """Make an HTTP request to the Metabase API"""
        url = f"{self.base_url}{endpoint}"

        params = params or {}
        # Format parameters
        if isinstance(database_id := params.get("database_id"), int):
            url = url.format(database_id=database_id)
        if isinstance(table_id := params.get("table_id"), int):
            url = url.format(table_id=table_id)
        if isinstance(field_id := params.get("field_id"), int):
            url = url.format(field_id=field_id)
        if isinstance(card_id := params.get("card_id"), int):
            url = url.format(card_id=card_id)

        logging.info(
            f"Making {method} request to {url} with params {params} and json {json_data}"
        )

        # Get client
        client = await self.get_client()
        try:
            response = await client.request(
                method, url, headers=self.headers, params=params, json=json_data
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            error_detail = (
                e.response.json()
                if e.response.headers.get("content-type") == "application/json"
                else str(e)
            )
            raise MetabaseAPIError(f"HTTP {e.response.status_code}: {error_detail}")
        except httpx.RequestError as e:
            raise MetabaseAPIError(f"Request failed: {str(e)}")
        except Exception as e:
            raise MetabaseAPIError(f"Unexpected error: {str(e)}")

    async def get_user_details(self, user_id) -> Dict[str, Any] | None:
        """Get details of the current logged-in user"""
        try:
            endpoint = MetabaseEndpoints.GET_USER_DETAILS.value.format(user_id=user_id)
            return await self._make_request("GET", endpoint)
        except MetabaseAPIError as e:
            return None

    async def get_database_schema(self, database_id: int) -> Dict[str, Any]:
        """Get complete database schema including tables and fields"""
        try:
            endpoint = MetabaseEndpoints.GET_DATABASE_METADATA.value
            return await self._make_request(
                "GET", endpoint, params={"database_id": database_id}
            )
        except MetabaseAPIError:
            # Fallback to legacy endpoint if needed
            endpoint = MetabaseEndpoints.GET_METADATA.value
            return await self._make_request(
                "GET", endpoint, params={"database_id": database_id}
            )
        except Exception as e:
            raise MetabaseAPIError(f"Unexpected error in get_database_schema: {str(e)}")

    async def get_table_metadata(self, table_id: int) -> Dict[str, Any]:
        """Get detailed table metadata including fields and foreign keys"""
        try:
            endpoint = MetabaseEndpoints.GET_TABLE_QUERY_METADATA.value
            return await self._make_request(
                "GET", endpoint, params={"table_id": table_id}
            )
        except MetabaseAPIError:
            # Fallback to alternate endpoint if needed
            endpoint = MetabaseEndpoints.GET_TABLE_METADATA.value
            return await self._make_request(
                "GET", endpoint, params={"table_id": table_id}
            )

    async def get_field_values(self, field_id: int) -> List[List[Any]]:
        """Get distinct values for a field"""
        endpoint = MetabaseEndpoints.GET_FIELD_VALUES.value.format(field_id=field_id)
        return await self._make_request("GET", endpoint)

    async def get_card_metadata(self, card_id: int) -> Dict[str, Any]:
        """Get detailed card/question metadata including dataset query"""
        endpoint = MetabaseEndpoints.GET_CARD_METADATA.value.format(card_id=card_id)
        return await self._make_request("GET", endpoint)

    async def get_dataset_query_metadata(
        self, dataset_query: DatasetQuery
    ) -> Dict[str, Any]:
        """Get detailed dataset query metadata"""
        endpoint = MetabaseEndpoints.GET_DATA_SET_QUERY_METADATA.value
        return await self._make_request(
            "POST",
            endpoint,
            json_data={
                "database": dataset_query.database,
                "query": {
                    "source-table": dataset_query.query.source_table,
                },
                "type": dataset_query.type,
                "parameters": [],
            },
        )

    async def get_native_query_metadata(self, dataset_query: DatasetQuery):
        """Get detailed native query metadata"""

        if dataset_query.type == "native":
            json_data = {
                "database": dataset_query.database,
                "native": {
                    "query": dataset_query.native.query,
                    "template-tags": dataset_query.native.template_args,
                },
                "type": dataset_query.type,
                "parameters": [],
            }

        else:
            json_data = (
                {
                    "database": dataset_query.database,
                    "query": {
                        "source-table": dataset_query.query.source_table,
                    },
                    "type": dataset_query.type,
                    "parameters": [],
                },
            )

        endpoint = MetabaseEndpoints.GET_NATIVE_QUERY_METADATA.value
        return await self._make_request("POST", endpoint, json_data=json_data)

    async def create_card(self, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new question/card in Metabase

        Args:
            question_data: Dict containing:
                - name: Question name
                - display_type: Type of visualization
                - dataset_query: Query configuration
                - visualization_settings: Chart settings
                - collection_id: Optional collection ID
                - description: Optional description
        """
        return await self._make_request(
            "POST", MetabaseEndpoints.CREATE_CARD.value, json_data=question_data
        )

    async def execute_question(self, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a question and get results without saving

        Args:
            question_data: Dict containing the question configuration including:
                - database: Database ID
                - query: Query details
                - type: Query type (query/native)
        """
        return await self._make_request(
            "POST", MetabaseEndpoints.DATASET.value, json_data=question_data
        )

    async def get_schema_with_sample_data(
        self, database_id: int, max_samples: int = 5
    ) -> Dict[str, Any]:
        """
        Get database schema enriched with sample data for each field

        Args:
            database_id: ID of the database
            max_samples: Maximum number of sample values to fetch per field

        Returns:
            Dict containing schema and sample data
        """
        try:
            # Get database metadata with caching
            schema = await self.get_database_schema(database_id)

            # Process tables in parallel
            async def process_table(table: Dict[str, Any]) -> Dict[str, Any]:
                table_id = table.get("id")
                if not table_id:
                    return table

                # Get table metadata
                try:
                    table_metadata = await self.get_table_metadata(table_id)
                    table["fields_with_samples"] = []

                    # Prepare field value fetching tasks
                    field_tasks = []
                    for field in table_metadata.get("fields", []):
                        field_id = field.get("id")
                        if not field_id:
                            continue

                        # Skip special fields
                        field_type = field.get("base_type", "")
                        if field_type not in ["type/PK", "type/FK"]:
                            field_tasks.append((field, self.get_field_values(field_id)))

                    # Process fields in parallel
                    if field_tasks:
                        field_results = await asyncio.gather(
                            *[task for _, task in field_tasks], return_exceptions=True
                        )

                        # Process results
                        for (field, _), result in zip(field_tasks, field_results):
                            if isinstance(result, Exception):
                                field["sample_values"] = []
                            else:
                                try:
                                    sample_values = [
                                        pair[1]
                                        for pair in result
                                        if isinstance(pair, list) and len(pair) > 1
                                    ][:max_samples]
                                    field["sample_values"] = sample_values
                                except (IndexError, TypeError):
                                    field["sample_values"] = []

                            field["semantic_type"] = field.get("semantic_type")
                            table["fields_with_samples"].append(field)

                    # Add relationship information
                    foreign_keys = [
                        f
                        for f in table_metadata.get("fields", [])
                        if f.get("semantic_type") == "type/FK"
                    ]
                    table["relationships"] = [
                        {
                            "field_id": fk["id"],
                            "field_name": fk["name"],
                            "target_table": fk.get("target", {})
                            .get("table", {})
                            .get("name"),
                            "target_field": fk.get("target", {})
                            .get("field", {})
                            .get("name"),
                        }
                        for fk in foreign_keys
                    ]

                except Exception:
                    # If table processing fails, return table without enrichment
                    return table

                return table

            # Process all tables in parallel with timeout
            tables = schema.get("tables", [])
            async with asyncio.TaskGroup() as tg:
                table_tasks = [tg.create_task(process_table(table)) for table in tables]

            # Update schema with processed tables
            schema["tables"] = [task.result() for task in table_tasks]
            return schema

        except MetabaseAPIError as e:
            raise MetabaseAPIError(f"Error getting schema data: {str(e)}")
        except Exception as e:
            raise MetabaseAPIError(
                f"Unexpected error in get_schema_with_sample_data: {str(e)}"
            )

        except MetabaseAPIError as e:
            raise MetabaseAPIError(f"Error getting schema data: {str(e)}")
        except Exception as e:
            raise MetabaseAPIError(
                f"Unexpected error in get_schema_with_sample_data: {str(e)}"
            )

    async def create_question_from_template(
        self, database_id: int, table_id: int, template: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a question from a template configuration

        Args:
            database_id: Target database ID
            table_id: Target table ID
            template: Dict containing:
                - name: Question name
                - display_type: Visualization type
                - aggregation: List of aggregations
                - breakout: List of breakout fields
                - filter: Optional filter conditions
                - order_by: Optional sorting
                - limit: Optional row limit

        Returns:
            Created question data from Metabase
        """
        question_data = {
            "name": template.get("name", "Untitled Question"),
            "display": template.get("display_type", "table"),
            "visualization_settings": template.get("visualization_settings", {}),
            "dataset_query": {
                "type": "query",
                "database": database_id,
                "query": {
                    "source-table": table_id,
                    "aggregation": template.get("aggregation", []),
                    "breakout": template.get("breakout", []),
                    "filter": template.get("filter", []),
                    "order-by": template.get("order_by", []),
                    "limit": template.get("limit"),
                },
            },
        }

        if template.get("collection_id"):
            question_data["collection_id"] = template["collection_id"]

        if template.get("description"):
            question_data["description"] = template["description"]

        return await self.create_card(question_data)

    async def preview_question(
        self,
        database_id: int,
        table_id: int,
        aggregation: Optional[List] = None,
        breakout: Optional[List] = None,
        filter_clause: Optional[List] = None,
        limit: Optional[int] = 1000,
    ) -> Dict[str, Any]:
        """
        Preview a question's results without saving it

        Args:
            database_id: Target database ID
            table_id: Target table ID
            aggregation: Optional list of aggregations
            breakout: Optional list of breakout fields
            filter_clause: Optional filter conditions
            limit: Maximum number of rows to return

        Returns:
            Query results from Metabase
        """
        query_data = {
            "type": "query",
            "database": database_id,
            "query": {
                "source-table": table_id,
                "aggregation": aggregation or [],
                "breakout": breakout or [],
                "limit": limit,
            },
        }

        if filter_clause:
            query_data["query"]["filter"] = filter_clause

        return await self.execute_question(query_data)
