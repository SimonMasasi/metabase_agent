
from django.http import HttpRequest
from ninja import Router

from serializers.baseSerializer import ResultsSchema
from utils.logging import metabase_agent_logging
logging = metabase_agent_logging()


metrics_router = Router()


@metrics_router.post("/select-metric/", response=ResultsSchema)
def select_metric(request: HttpRequest):
    logging.info(str(request.body))
    logging.info(str(request.headers))
    """
    Select a metric based on the provided request data.
    """
    # Placeholder for metric selection logic
    return {"results": "Metric selection is not implemented yet."}


@metrics_router.post("/find-outliers/", response=ResultsSchema)
def find_outliers(request: HttpRequest):
    logging.info(str(request.body))
    logging.info(str(request.headers))
    """
    Find outliers in the provided data.
    """
    # Placeholder for outlier detection logic
    return {"results": "Outlier detection is not implemented yet."}