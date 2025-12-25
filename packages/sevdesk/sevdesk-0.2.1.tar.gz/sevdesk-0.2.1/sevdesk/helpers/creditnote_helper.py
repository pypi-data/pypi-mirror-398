"""
CreditNoteHelper - High-Level Gutschriften-Verwaltung

Gutschriften (CreditNotes) werden verwendet fuer:
- Stornorechnungen
- Teilstornos
- Gutschriften an Kunden

Beispiele:
    # Alle Gutschriften auflisten
    creditnotes = sevdesk.creditNoteHelper.list()

    # Gutschrift per ID abrufen
    cn = sevdesk.creditNoteHelper.find_by_id(12345)

    # PDF herunterladen
    pdf = sevdesk.creditNoteHelper.get_pdf(12345)
"""

from datetime import datetime, timedelta
from typing import Optional, List
from sevdesk.models.creditnoteresponse import CreditNoteResponse


# CreditNote Status
CREDITNOTE_STATUS = {
    '100': 'Draft (Entwurf)',
    '200': 'Open (Offen)',
    '1000': 'Paid (Bezahlt)',
}


class CreditNoteHelper:
    """Helper-Klasse fuer Gutschriften-Operationen"""

    def __init__(self, client):
        self.client = client

    def list(self, contact_id: int = None, status: str = None,
             start_date: str = None, end_date: str = None,
             credit_note_number: str = None) -> List[CreditNoteResponse]:
        """
        Listet Gutschriften auf.

        Args:
            contact_id: Filter nach Kontakt
            status: Filter nach Status ('draft', 'open', 'paid' oder Code)
            start_date: Startdatum (YYYY-MM-DD)
            end_date: Enddatum (YYYY-MM-DD)
            credit_note_number: Filter nach Gutschriftennummer

        Returns:
            Liste von CreditNoteResponse
        """
        # Status-Mapping
        status_map = {
            'draft': '100',
            'open': '200',
            'paid': '1000',
        }
        status_value = None
        if status:
            status_value = status_map.get(status.lower(), status)

        # Datum in Timestamp
        start_ts = self._date_to_timestamp(start_date) if start_date else None
        end_ts = self._date_to_timestamp(end_date) if end_date else None

        try:
            creditnotes = self.client.creditnote.getCreditNotes(
                contact_id=contact_id,
                contact_objectName="Contact" if contact_id else None,
                status=status_value,
                startDate=start_ts,
                endDate=end_ts,
                creditNoteNumber=credit_note_number
            )
            return creditnotes if creditnotes else []
        except Exception:
            return []

    def find_by_id(self, creditnote_id: int) -> Optional[CreditNoteResponse]:
        """Ruft eine Gutschrift per ID ab"""
        try:
            result = self.client.creditnote.getcreditNoteById(creditnote_id)
            if isinstance(result, list) and len(result) > 0:
                return result[0]
            return result
        except Exception:
            return None

    def find_by_number(self, creditnote_number: str) -> Optional[CreditNoteResponse]:
        """Sucht nach Gutschriftennummer"""
        creditnotes = self.list(credit_note_number=creditnote_number)
        return creditnotes[0] if creditnotes else None

    def get_drafts(self) -> List[CreditNoteResponse]:
        """Ruft alle Entwuerfe ab"""
        return self.list(status='draft')

    def get_open(self) -> List[CreditNoteResponse]:
        """Ruft alle offenen Gutschriften ab"""
        return self.list(status='open')

    def get_paid(self) -> List[CreditNoteResponse]:
        """Ruft alle bezahlten Gutschriften ab"""
        return self.list(status='paid')

    def get_recent(self, days: int = 30) -> List[CreditNoteResponse]:
        """Ruft Gutschriften der letzten X Tage ab"""
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        return self.list(start_date=start_date, end_date=end_date)

    def get_by_contact(self, contact_id: int) -> List[CreditNoteResponse]:
        """Ruft alle Gutschriften eines Kontakts ab"""
        return self.list(contact_id=contact_id)

    def get_pdf(self, creditnote_id: int, download: bool = True) -> Optional[bytes]:
        """Laedt PDF einer Gutschrift herunter"""
        try:
            return self.client.creditnote.creditNoteGetPdf(creditnote_id, download=download)
        except Exception:
            return None

    def mark_as_sent(self, creditnote_id: int) -> Optional[CreditNoteResponse]:
        """Markiert Gutschrift als versendet"""
        try:
            return self.client.creditnote.creditNoteSendBy(creditnote_id)
        except Exception:
            return None

    def reset_to_draft(self, creditnote_id: int) -> bool:
        """Setzt Status zurueck auf Entwurf"""
        try:
            self.client.creditnote.creditNoteResetToDraft(creditnote_id)
            return True
        except Exception:
            return False

    def reset_to_open(self, creditnote_id: int) -> bool:
        """Setzt Status zurueck auf Offen"""
        try:
            self.client.creditnote.creditNoteResetToOpen(creditnote_id)
            return True
        except Exception:
            return False

    def enshrine(self, creditnote_id: int) -> bool:
        """Schreibt Gutschrift fest (nicht mehr aenderbar)"""
        try:
            self.client.creditnote.creditNoteEnshrine(creditnote_id)
            return True
        except Exception:
            return False

    def delete(self, creditnote_id: int) -> bool:
        """Loescht eine Gutschrift (nur Entwuerfe)"""
        try:
            self.client.creditnote.deletecreditNote(creditnote_id)
            return True
        except Exception:
            return False

    def get_status_label(self, status: str) -> str:
        """Gibt Status-Label zurueck"""
        return CREDITNOTE_STATUS.get(str(status), f'Unknown ({status})')

    def calculate_totals(self, creditnotes: List[CreditNoteResponse]) -> dict:
        """Berechnet Summen"""
        net = 0.0
        tax = 0.0
        gross = 0.0
        for cn in creditnotes:
            if cn.sumNet:
                net += float(cn.sumNet)
            if cn.sumTax:
                tax += float(cn.sumTax)
            if cn.sumGross:
                gross += float(cn.sumGross)
        return {'net': net, 'tax': tax, 'gross': gross, 'count': len(creditnotes)}

    def _date_to_timestamp(self, date_str: str) -> Optional[int]:
        """Konvertiert Datum in Timestamp"""
        try:
            if date_str.isdigit():
                return int(date_str)
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return int(dt.timestamp())
        except (ValueError, AttributeError):
            return None
