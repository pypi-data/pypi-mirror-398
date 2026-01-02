from sevdesk.base.basecontroller import BaseController
from typing import Optional

class ReportController(BaseController):

    @BaseController.get("/Report/invoicelist")
    def reportInvoice(self, sevQuery: dict, view: str, download: Optional[bool] = None):
        """Export invoice list"""
        return (yield)

    @BaseController.get("/Report/orderlist")
    def reportOrder(self, sevQuery: dict, view: str, download: Optional[bool] = None):
        """Export order list"""
        return (yield)

    @BaseController.get("/Report/contactlist")
    def reportContact(self, sevQuery: dict, download: Optional[bool] = None):
        """Export contact list"""
        return (yield)

    @BaseController.get("/Report/voucherlist")
    def reportVoucher(self, sevQuery: dict, download: Optional[bool] = None):
        """Export voucher list"""
        return (yield)

