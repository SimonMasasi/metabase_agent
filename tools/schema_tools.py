from typing import Any, Dict
from pydantic_ai import RunContext
from constants.metabase_request_schemas import MetabaseAgentRequest
from utils.logging import metabase_helpers_logging
from utils.metabase_api import MetabaseAPIService


logging = metabase_helpers_logging()
metabase_api = MetabaseAPIService()


async def resolve_table_schema_metadata(
    ctx: RunContext[MetabaseAgentRequest],
) -> Dict[str, Any]:

    try:

        viewing_list = ctx.deps.context.user_is_viewing

        # viewing_list may be an async iterable or a regular iterable (list). Normalize iteration.
        if not viewing_list:
            logging.info("No viewing context available")
            return {"error": "No viewing context available"}

        card_ids = []
        table_queries = []
        for viewing in viewing_list:
            if viewing.type == "adhoc":
                if viewing.query is None:
                    logging.info(
                        f"Skipping adhoc viewing with id {getattr(viewing, 'id', 'unknown')} due to missing query."
                    )
                    continue

                if viewing.query.database is None:
                    logging.info(
                        f"Skipping adhoc viewing with id {getattr(viewing, 'id', 'unknown')} due to missing database in query."
                    )
                    continue

                table_queries.append(viewing.query)
                continue

            card_id = getattr(viewing, "id", None)
            if card_id is None:
                continue

            card_ids.append(card_id)

        if len(card_ids) == 0 and len(table_queries) == 0:
            logging.info("No card IDs found in viewing context")
            return {"error": "No card context available"}

        card_metadata_list = []
        for card_id in card_ids:
            try:
                card_metadata = await metabase_api.get_card_metadata(card_id)

                card_metadata_list.append(card_metadata.get("tables", []))
                logging.info(f"Fetched metadata for card ID {card_id}: successfully")
            except Exception as e:
                logging.error(
                    f"Error fetching metadata for card ID {card_id}: {str(e)}"
                )
                continue

        for table_query in table_queries:
            try:
                table_metadata = await metabase_api.get_native_query_metadata(
                    table_query
                )

                card_metadata_list.append([table_metadata])
                logging.info(
                    f"Fetched metadata for table ID {table_query}: successfully"
                )
            except Exception as e:
                logging.error(
                    f"Error fetching metadata for table ID {table_query}: {str(e)}"
                )
                continue

        return {"tables_metadata": card_metadata_list}
    except Exception as e:
        logging.error(f"Error in get_table_schema_metadata: {str(e)}")
        return {"error": str(e)}


async def resolve_sample_data_from_viewing_context(
    ctx: RunContext[MetabaseAgentRequest],
) -> Dict[str, Any]:

    try:

        viewing_list = ctx.deps.context.user_is_viewing

        # viewing_list may be an async iterable or a regular iterable (list). Normalize iteration.
        if not viewing_list:
            logging.info("No viewing context available")
            return {"error": "No viewing context available"}

        cards_list = []
        for viewing in viewing_list:
            card = getattr(viewing, "query", None)
            if card is None:
                continue

            cards_list.append(card)

        if len(cards_list) == 0:
            logging.info("No card were found in viewing context")
            return {"error": "No card context available"}

        sample_data_list = []
        for card in cards_list:
            try:
                sample_data = await metabase_api.get_dataset_query_metadata(card)
                sample_data_list.append(
                    sample_data.get("data", []).get("rows", [])[:10]
                )
                logging.info(f"Fetched sample data for card ID {card} Successfully")
            except Exception as e:
                logging.error(
                    f"Error fetching sample data for card ID {card}: {str(e)}"
                )
                continue

        return {"sample_data": sample_data_list}
    except Exception as e:
        logging.error(f"Error in get_sample_data_from_viewing_context: {str(e)}")
        return {"error": str(e)}


async def resolve_database_schema(
    ctx: RunContext[MetabaseAgentRequest],
):
    """
    Fetches the database schema from Metabase.
    Returns a dictionary containing the list of databases and their schemas.
    If an error occurs, returns a dictionary with an error message.
    """
    try:

        viewing_list = ctx.deps.context.user_is_viewing

        # viewing_list may be an async iterable or a regular iterable (list). Normalize iteration.
        if not viewing_list:
            return {"error": "No database context available"}

        databases_ids = []

        for viewing in viewing_list:

            if viewing.query is None:
                logging.info(
                    f"Skipping viewing with id {getattr(viewing, 'id', 'unknown')} due to missing query."
                )

            if viewing.query.database is None:
                logging.info(
                    f"Skipping viewing with id {getattr(viewing, 'id', 'unknown')} due to missing database in query."
                )
                continue

            databases_ids.append(viewing.query.database)

        if len(databases_ids) == 0:
            logging.info("No database IDs found in viewing context")
            return {"error": "No database context available"}

        databases_list = []
        for database_id in databases_ids:
            try:
                databases = await metabase_api.get_database_schema(database_id)

                logging.info(f"Fetched schema for database ID {database_id}")

                databases_list.append(databases)
            except Exception as e:
                logging.error(
                    f"Error fetching schema for database ID {database_id}: {str(e)}"
                )
                continue
        # summarize and attach only the summary to the run context to avoid huge prompts
        try:
            summary = _summarize_databases(databases_list)
        except Exception:
            logging.error("Error summarizing database schemas")
            summary = []

        return {"databases_summary": summary}
    except Exception as e:
        logging.error(f"Error in get_database_schema: {str(e)}")
        return {"error": str(e)}


async def resolve_schema_with_sample_data(ctx: RunContext[MetabaseAgentRequest]):
    """
    Fetches the database schema along with sample data from Metabase.
    """

    try:

        viewing_list = ctx.deps.context.user_is_viewing

        # viewing_list may be an async iterable or a regular iterable (list). Normalize iteration.
        if not viewing_list:
            logging.info("No viewing context available")
            return {"error": "No database context available"}

        databases_ids = []

        for viewing in viewing_list:
            database_id = getattr(getattr(viewing, "query", None), "database", None)
            if database_id is not None:
                databases_ids.append(database_id)

        if len(databases_ids) == 0:
            logging.info("No database IDs found in viewing context")
            return {"error": "No database context available"}

        databases_list = []
        for database_id in databases_ids:
            try:
                databases = await metabase_api.get_schema_with_sample_data(database_id)

                logging.info(
                    f"Fetched schema for database ID {database_id}: {databases}"
                )

                databases_list.append(databases)
            except Exception as e:
                logging.error(f"Error fetching schema for database ID {database_id}: {str(e)}")
                continue
        # summarize and attach only the summary to the run context to avoid huge prompts
        try:
            summary = _summarize_databases(databases_list)
            setattr(ctx.deps.context, "_schema_fetched", True)
            setattr(
                ctx.deps.context, "_fetched_schema_with_sample_data_summary", summary
            )
        except Exception as e:
            logging.error(f"Error summarizing database schemas: {str(e)}")
            summary = []

        # return a compact summary instead of raw large objects
        return {"databases_with_sample_data_summary": summary}
    except Exception as e:
        logging.error(f"Error in get_schema_with_sample_data: {str(e)}")
        return {"error": str(e)}


def _summarize_databases(
    databases: list,
    max_tables: int = 3,
    max_sample_rows: int = 2,
    max_chars: int = 1500,
) -> list:
    """
    Produce a condensed summary of the databases list suitable for including in prompts.
    Uses aggressive defaults to keep returned summaries small.
    """
    summaries = []
    for db in databases:
        try:
            name = (
                db.get("name")
                if isinstance(db, dict)
                else getattr(db, "name", "unknown")
            )
        except Exception:
            name = "unknown"

        db_summary = {"name": name, "tables": []}

        if isinstance(db, dict):
            tables = db.get("tables") or db.get("schema") or []
        else:
            tables = getattr(db, "tables", []) or getattr(db, "schema", [])

        for t in tables[:max_tables]:
            try:
                if isinstance(t, dict):
                    tname = t.get("name") or t.get("table_name") or "unknown"
                    cols = t.get("columns") or []
                    samples = t.get("sample_rows") or []
                else:
                    tname = getattr(t, "name", "unknown")
                    cols = getattr(t, "columns", [])
                    samples = getattr(t, "sample_rows", [])

                col_summary = []
                for c in (cols or [])[:10]:
                    if isinstance(c, dict):
                        col_summary.append(
                            {"name": c.get("name"), "type": c.get("type")}
                        )
                    else:
                        if hasattr(c, "name"):
                            col_summary.append(
                                {
                                    "name": getattr(c, "name"),
                                    "type": getattr(c, "type", None),
                                }
                            )
                        else:
                            col_summary.append({"name": str(c)})

                sample_preview = []
                for r in (samples or [])[:max_sample_rows]:
                    try:
                        s = str(r)
                        sample_preview.append(s[:120])
                    except Exception:
                        sample_preview.append("<unserializable_row>")

                db_summary["tables"].append(
                    {
                        "table": tname,
                        "columns": col_summary,
                        "sample_preview": sample_preview,
                    }
                )
            except Exception:
                continue

        # enforce rough max_chars by trimming previews and columns
        try:
            import json

            rendered = json.dumps(db_summary)
            if len(rendered) > max_chars:
                for tbl in db_summary.get("tables", []):
                    tbl["sample_preview"] = [
                        s[:60] for s in tbl.get("sample_preview", [])[:1]
                    ]
                rendered = json.dumps(db_summary)
                if len(rendered) > max_chars:
                    for tbl in db_summary.get("tables", []):
                        tbl["columns"] = [
                            {"name": c.get("name")} for c in tbl.get("columns", [])[:3]
                        ]
        except Exception:
            pass

        summaries.append(db_summary)

    return summaries
