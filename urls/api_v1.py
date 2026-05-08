from ninja import NinjaAPI , Redoc
from views.v1.analyzer import analyzer_router
from views.v1.metrics import metrics_router
from views.v1.sql import sql_router


api_title = "METABASE AGENT API V1"

api_v1 = NinjaAPI(version="1.0")

api_v1.docs_url = "docs"

# Set the base path for the API documentation Had to add this for ScalarViewer to work correctly
api_v1.docs = Redoc()

api_v1.title = api_title

api_v1.add_router("/analyze/", analyzer_router)
api_v1.add_router("/sql/", sql_router)
api_v1.add_router("/", metrics_router)
