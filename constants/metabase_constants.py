from enum import Enum

class MetabaseEndpoints(str, Enum):
    # Authentication
    SESSION = "/api/session"

    # Database endpoints
    GET_DATABASES = "/api/database"
    GET_DATABASE = "/api/database/{database_id}"
    GET_DATABASE_METADATA = "/api/database/{database_id}/metadata"  # Main endpoint for schema
    GET_DATABASE_FIELDS = "/api/database/{database_id}/fields"
    GET_DATABASE_SCHEMAS = "/api/database/{database_id}/schemas"
    GET_METADATA = "/api/database/{database_id}/metadata"  # Alias for backward compatibility

    # Table endpoints
    GET_TABLE = "/api/table/{table_id}"
    GET_TABLE_FIELDS = "/api/table/{table_id}/field_summary"
    GET_TABLE_QUERY_METADATA = "/api/table/{table_id}/query_metadata"  # Detailed table info
    GET_TABLE_RELATED = "/api/table/{table_id}/related"
    GET_TABLE_METADATA = "/api/table/{table_id}/query_metadata"  # Alias for backward compatibility

    # Field endpoints
    GET_FIELD = "/api/field/{field_id}"
    GET_FIELD_VALUES = "/api/field/{field_id}/values"
    GET_FIELD_SEARCH = "/api/field/{field_id}/search/{search_term}"
    GET_FIELD_REMAPPING = "/api/field/{field_id}/remapping/{remapped_id}"

    GET_CARD_METADATA = "/api/card/{card_id}/query_metadata"  # Detailed card info
    GET_DATA_SET_QUERY_METADATA = "/api/dataset"  # Detailed dataset info

    GET_NATIVE_QUERY_METADATA = "/api/dataset/query_metadata"  # Detailed native query info


    # Card/Question endpoints
    GET_CARDS = "/api/card"
    CREATE_CARD = "/api/card"
    GET_CARD = "/api/card/{card_id}"
    UPDATE_CARD = "/api/card/{card_id}"
    DELETE_CARD = "/api/card/{card_id}"

    # Query endpoints
    DATASET = "/api/dataset"
    DATASET_NATIVE = "/api/dataset/native"
    DATASET_DURATION = "/api/dataset/duration"

    # Dashboard endpoints
    GET_DASHBOARDS = "/api/dashboard"
    CREATE_DASHBOARD = "/api/dashboard"
    GET_DASHBOARD = "/api/dashboard/{dashboard_id}"

    # Collection endpoints
    GET_COLLECTIONS = "/api/collection"
    GET_COLLECTION = "/api/collection/{collection_id}"

    # Permissions endpoints
    GET_GRAPH = "/api/permissions/graph"
    GET_GROUP_GRAPH = "/api/permissions/group/{group_id}/graph"

    # user Details
    GET_USER_DETAILS = "/api/user/{user_id}"


class MetabaseFieldType(str, Enum):
    """Metabase field types"""
    STRING = "type/Text"
    NUMBER = "type/Number"
    INTEGER = "type/Integer"
    FLOAT = "type/Float"
    DECIMAL = "type/Decimal"
    BOOLEAN = "type/Boolean"
    DATE = "type/Date"
    DATETIME = "type/DateTime"
    TIME = "type/Time"
    TIMESTAMP = "type/TimeStamp"
    UUID = "type/UUID"
    URL = "type/URL"
    EMAIL = "type/Email"
    JSON = "type/JSON"
    FOREIGN_KEY = "type/FK"
    PRIMARY_KEY = "type/PK"

class DisplayType(str, Enum):
    """Metabase visualization display types"""
    TABLE = "table"
    BAR = "bar"
    LINE = "line"
    AREA = "area"
    ROW = "row"
    PIE = "pie"
    FUNNEL = "funnel"
    SCATTER = "scatter"
    MAP = "map"
    PIN_MAP = "pin_map"
    PIVOT_TABLE = "pivot"
    PROGRESS = "progress"
    GAUGE = "gauge"
    LINE_PLUS_BAR = "combo"
    WATERFALL = "waterfall"
    SCALAR = "scalar"
