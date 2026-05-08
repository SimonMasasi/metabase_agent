from pydantic_ai import RunContext
from constants.metabase_request_schemas import MetabaseAgentRequest
from constants.sample_queries import SAMPLE_QUERY_ONE
from utils.logging import metabase_agent_logging

logging = metabase_agent_logging()


async def modify_chart_schema_if_necessary(
    json_data, cnx: RunContext[MetabaseAgentRequest]
):

    user_is_viewing_content = cnx.deps.context.user_is_viewing

    if len(user_is_viewing_content) == 0:
        logging.info("Found No user Is Viewing Context Retuning Normal Json ")
        return json_data

    query_data = user_is_viewing_content[0].query

    if query_data is None:
        logging.info("No Query Data Found in Request Retuning Normal Json ")
        return json_data

    dataset_query = json_data.get("dataset_query", None)
    query_json = dataset_query.get("query", None)

    database = dataset_query.get("database", None)
    source_table = query_json.get("source-table", None)

    if str(database).lower() != str(query_data.database).lower():
        logging.info(
            f"Modified database table  📊 {database} is not equal to {query_data.database} "
        )
        json_data["dataset_query"]["database"] = query_data.database

    if str(source_table).lower() != str(query_data.query.source_table).lower():
        logging.info(
            f"Modified source table 📚 {source_table} is not equal to {query_data.query.source_table} "
        )
        json_data["dataset_query"]["query"][
            "source-table"
        ] = query_data.query.source_table

    return json_data


async def check_if_chart_is_valid(json_data, cnx: RunContext[MetabaseAgentRequest]):
    user_is_viewing_content = cnx.deps.context.user_is_viewing

    if len(user_is_viewing_content) == 0:
        logging.error("Found No user Is Viewing Context")
        return "Found No user Is Viewing Context", False

    return await check_chart_json_content_validity(json_data)


async def check_chart_json_content_validity(json_data):
    if not json_data.get("dataset_query", None):
        logging.error("dataset_query not Found in schema")
        return (
            f"""❌ Error json schema must Contain dataset_query attribute for example  {SAMPLE_QUERY_ONE}""",
            False,
        )

    if not json_data.get("dataset_query", {}).get("query", None):
        logging.error("query not Found in schema")
        return (
            f""" ❌ Error Json Schema must Contain `query` For example {SAMPLE_QUERY_ONE} """,
            False,
        )

    query = json_data.get("dataset_query", {}).get("query", None)

    if query is None:
        logging.error("query not Found in schema")
        return (
            f""
            " ❌Error Json Schema must Contain `query` in dataset_query section For example{SAMPLE_QUERY_ONE}"
            "",
            False,
        )

    if not query.get("aggregation", None):
        logging.error("query not Found in schema")
        return (
            f""
            " ❌Error Json Schema must Contain `aggregation` in query section For example{SAMPLE_QUERY_ONE}"
            "",
            False,
        )

    if not query.get("breakout", None):
        logging.error("query not Found in schema")
        return (
            f""" ❌ Error Json Schema must Contain `breakout` in query Section For example{SAMPLE_QUERY_ONE} """,
            False,
        )

    return "Json is valid", True
