from sevdesk.base.basecontroller import BaseController
from typing import Optional
from sevdesk.models.export_job_download_info import Export_Job_Download_Info
from sevdesk.models.export_progress_data import Export_Progress_Data

class ExportController(BaseController):

    @BaseController.put("/SevClient/{SevClientId}/updateExportConfig")
    def updateExportConfig(self, SevClientId: float):
        """Update export config"""
        return (yield)

    @BaseController.get("/Export/datevCSV")
    def exportDatevDepricated(self, endDate: int, scope: str, startDate: int, Download: Optional[bool] = None, enshrine: Optional[bool] = None, withEnshrinedDocuments: Optional[bool] = None, withUnpaidDocuments: Optional[bool] = None):
        """Export datev"""
        return (yield)

    @BaseController.get("/Export/createDatevCsvZipExportJob")
    def exportDatevCSV(self, endDate: int, scope: str, startDate: int, enshrineDocuments: Optional[bool] = None, exportByPaydate: Optional[bool] = None, includeDocumentImages: Optional[bool] = None, includeEnshrined: Optional[bool] = None):
        """Start DATEV CSV ZIP export"""
        return (yield)

    @BaseController.get("/Export/createDatevXmlZipExportJob")
    def exportDatevXML(self, endDate: int, scope: str, startDate: int, exportByPaydate: Optional[bool] = None, includeDocumentXml: Optional[bool] = None, includeEnshrined: Optional[bool] = None, includeExportedDocuments: Optional[bool] = None):
        """Start DATEV XML ZIP export"""
        return (yield)

    @BaseController.get("/Progress/generateDownloadHash")
    def generateDownloadHash(self, jobId: str) -> list[Export_Progress_Data]:
        """Generate download hash"""
        return (yield)

    @BaseController.get("/Progress/getProgress")
    def getProgress(self, hash: str) -> list[Export_Progress_Data]:
        """Get progress"""
        return (yield)

    @BaseController.get("/ExportJob/jobDownloadInfo")
    def jobDownloadInfo(self, jobId: str) -> list[Export_Job_Download_Info]:
        """Get job download info"""
        return (yield)

    @BaseController.get("/Export/invoiceCsv")
    def exportInvoice(self, sevQuery: dict, download: Optional[bool] = None):
        """Export invoice"""
        return (yield)

    @BaseController.get("/Export/invoiceZip")
    def exportInvoiceZip(self, sevQuery: dict, download: Optional[bool] = None):
        """Export Invoice as zip"""
        return (yield)

    @BaseController.get("/Export/creditNoteCsv")
    def exportCreditNote(self, sevQuery: dict, download: Optional[bool] = None):
        """Export creditNote"""
        return (yield)

    @BaseController.get("/Export/voucherListCsv")
    def exportVoucher(self, sevQuery: dict, download: Optional[bool] = None):
        """Export voucher as zip"""
        return (yield)

    @BaseController.get("/Export/transactionsCsv")
    def exportTransactions(self, sevQuery: dict, download: Optional[bool] = None):
        """Export transaction"""
        return (yield)

    @BaseController.get("/Export/voucherZip")
    def exportVoucherZip(self, sevQuery: dict, download: Optional[bool] = None):
        """Export voucher zip"""
        return (yield)

    @BaseController.get("/Export/contactListCsv")
    def exportContact(self, sevQuery: dict, download: Optional[bool] = None):
        """Export contact"""
        return (yield)

