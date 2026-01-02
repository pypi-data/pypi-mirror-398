from sevdesk.base.basecontroller import BaseController
from typing import Optional
from sevdesk.models.voucherposresponse import VoucherPosResponse

class VoucherPosController(BaseController):

    @BaseController.get("/VoucherPos")
    def getVoucherPositions(self, voucher_id: Optional[int] = None, voucher_objectName: Optional[str] = None) -> list[VoucherPosResponse]:
        """Retrieve voucher positions"""
        return (yield)

