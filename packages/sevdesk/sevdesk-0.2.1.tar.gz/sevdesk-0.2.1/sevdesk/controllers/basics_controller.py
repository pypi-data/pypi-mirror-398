from sevdesk.base.basecontroller import BaseController

class BasicsController(BaseController):

    @BaseController.get("/Tools/bookkeepingSystemVersion")
    def bookkeepingSystemVersion(self):
        """Retrieve bookkeeping system version"""
        return (yield)

