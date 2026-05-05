from ninja import NinjaAPI , Redoc
from views.v2.agent import agent_router
from views.v2.dashboard_analysis import dashboard_analysis_router


api_title = "METABASES HELPER API V2"

api_v2 = NinjaAPI(version="2.0")

api_v2.docs_url = "docs"
# Set the base path for the API documentation Had to add this for ScalarViewer to work correctly
api_v2.docs = Redoc()


api_v2.title = api_title

api_v2.add_router("/agent/", agent_router)
api_v2.add_router("/dashboard_analysis/", dashboard_analysis_router)