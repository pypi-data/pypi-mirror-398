from jupyter_server.base.handlers import APIHandler as BaseAPIHandler
from tornado import web
import json


class VisualizationAnalysisHandler(BaseAPIHandler):
    """
    Handler for visualization analysis requests.

    This feature has been deprecated. The handler returns an error message
    asking old clients to upgrade to the latest version.
    """

    @web.authenticated
    async def post(self):
        """Return deprecation error for old clients."""
        self.set_status(410)  # HTTP 410 Gone
        self.set_header("Content-Type", "application/json")
        self.finish(json.dumps({
            "error": "deprecated",
            "message": "Visualization analysis feature has been deprecated. Please upgrade to the latest version."
        }))
