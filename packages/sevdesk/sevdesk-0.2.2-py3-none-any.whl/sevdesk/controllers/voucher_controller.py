from sevdesk.base.basecontroller import BaseController
from typing import Optional
from sevdesk.models.receiptguidedto import ReceiptGuideDto
from sevdesk.models.savevoucher import SaveVoucher
from sevdesk.models.savevoucherresponse import SaveVoucherResponse
from sevdesk.models.voucherresponse import VoucherResponse
from sevdesk.models.voucherupdate import VoucherUpdate

class VoucherController(BaseController):

    @BaseController.post("/Voucher/Factory/saveVoucher")
    def voucherFactorySaveVoucher(self, body: SaveVoucher) -> SaveVoucherResponse:
        """Create a new voucher"""
        return (yield)

    @BaseController.post("/Voucher/Factory/uploadTempFile")
    def voucherUploadFile(self):
        """Upload voucher file"""
        return (yield)

    @BaseController.get("/Voucher")
    def getVouchers(self, contact_id: Optional[int] = None, contact_objectName: Optional[str] = None, creditDebit: Optional[str] = None, descriptionLike: Optional[str] = None, endDate: Optional[int] = None, startDate: Optional[int] = None, status: Optional[float] = None) -> list[VoucherResponse]:
        """Retrieve vouchers"""
        return (yield)

    @BaseController.get("/Voucher/{voucherId}")
    def getVoucherById(self, voucherId: int) -> list[VoucherResponse]:
        """Find voucher by ID"""
        return (yield)

    @BaseController.put("/Voucher/{voucherId}")
    def updateVoucher(self, voucherId: int, body: VoucherUpdate) -> VoucherResponse:
        """Update an existing voucher"""
        return (yield)

    @BaseController.put("/Voucher/{voucherId}/enshrine")
    def voucherEnshrine(self, voucherId: int):
        """Enshrine"""
        return (yield)

    @BaseController.put("/Voucher/{voucherId}/bookAmount")
    def bookVoucher(self, voucherId: int):
        """Book a voucher"""
        return (yield)

    @BaseController.put("/Voucher/{voucherId}/resetToOpen")
    def voucherResetToOpen(self, voucherId: int):
        """Reset status to open"""
        return (yield)

    @BaseController.put("/Voucher/{voucherId}/resetToDraft")
    def voucherResetToDraft(self, voucherId: int):
        """Reset status to draft"""
        return (yield)

    @BaseController.get("/ReceiptGuidance/forAllAccounts")
    def forAllAccounts(self) -> list[ReceiptGuideDto]:
        """Get all account guides"""
        return (yield)

    @BaseController.get("/ReceiptGuidance/forAccountNumber")
    def forAccountNumber(self, accountNumber: int) -> list[ReceiptGuideDto]:
        """Get guidance by account number"""
        return (yield)

    @BaseController.get("/ReceiptGuidance/forTaxRule")
    def forTaxRule(self, taxRule: str) -> list[ReceiptGuideDto]:
        """Get guidance by Tax Rule"""
        return (yield)

    @BaseController.get("/ReceiptGuidance/forRevenue")
    def forRevenue(self) -> list[ReceiptGuideDto]:
        """Get guidance for revenue accounts"""
        return (yield)

    @BaseController.get("/ReceiptGuidance/forExpense")
    def forExpense(self) -> list[ReceiptGuideDto]:
        """Get guidance for expense accounts"""
        return (yield)

