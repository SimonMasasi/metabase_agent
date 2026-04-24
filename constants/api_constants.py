from enum import Enum

class MetabaseEndpoints(str, Enum):
    # Database endpoints
    GET_DATABASES = "/api/database"
    GET_DATABASE = "/api/database/{database_id}"
    GET_TABLES = "/api/database/{database_id}/tables"
    GET_TABLE = "/api/table/{table_id}"
    GET_TABLE_FIELDS = "/api/table/{table_id}/fields"
    
    # Field endpoints
    GET_FIELD = "/api/field/{field_id}"
    GET_FIELD_VALUES = "/api/field/{field_id}/values"
    
    # Query endpoints
    GET_METADATA = "/api/database/{database_id}/metadata"
    DATASET = "/api/dataset"
    
    # Card/Question endpoints
    CREATE_CARD = "/api/card"
    GET_CARD = "/api/card/{card_id}"
    GET_CARD_QUERY = "/api/card/{card_id}/query"

    # user Details
    GET_USER_DETAILS = "/api/user/current"

class MetabaseFieldTypes(str, Enum):
    NUMBER = "number"
    STRING = "string"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    TIME = "time"
    JSON = "json"
    FOREIGN_KEY = "foreign_key"
    
class VisualizationType(str, Enum):
    TABLE = "table"
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    SCATTER = "scatter"
    AREA = "area"
    FUNNEL = "funnel"
    MAP = "map"
    PIVOT = "pivot"