from sevdesk.base.basecontroller import BaseController
from typing import Optional, Any


class SevUserController(BaseController):
    """Controller fuer SevUser-Operationen (undocumented API)"""

    @BaseController.get("/SevUser")
    def getSevUsers(self, limit: Optional[int] = None, offset: Optional[int] = None) -> list[dict]:
        """Ruft alle SevUser des Accounts ab"""
        return (yield)

    @BaseController.get("/SevUser/{sevUserId}")
    def getSevUserById(self, sevUserId: int) -> dict:
        """Ruft einen spezifischen SevUser ab"""
        return (yield)
