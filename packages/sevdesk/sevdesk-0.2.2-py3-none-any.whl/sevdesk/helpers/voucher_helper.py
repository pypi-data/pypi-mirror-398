"""
VoucherHelper - High-Level Beleg/Ausgaben-Verwaltung

Voucher in sevDesk sind Belege fuer Ausgaben (Eingangsrechnungen, Quittungen, etc.)

Beispiele:
    # Alle Belege auflisten
    vouchers = sevdesk.voucherHelper.list()

    # Nur offene Belege
    vouchers = sevdesk.voucherHelper.list(status='open')

    # Belege eines Lieferanten
    vouchers = sevdesk.voucherHelper.list(supplier_id=12345)

    # Einzelnen Beleg abrufen
    voucher = sevdesk.voucherHelper.find_by_id(12345)

    # Positionen eines Belegs
    positions = sevdesk.voucherHelper.get_positions(voucher_id=12345)

    # Summen berechnen
    totals = sevdesk.voucherHelper.calculate_totals(vouchers)
"""

from datetime import datetime, timedelta
from typing import Optional, List
from sevdesk.models.voucherresponse import VoucherResponse
from sevdesk.models.voucherposresponse import VoucherPosResponse


# Voucher Status Codes
VOUCHER_STATUS = {
    '50': 'Draft (Entwurf)',
    '100': 'Open (Unbezahlt)',
    '200': 'Partial (Teilbezahlt)',
    '1000': 'Paid (Bezahlt)',
}

# Voucher Types
VOUCHER_TYPES = {
    'VOU': 'Voucher (Beleg)',
    'RV': 'Recurring Voucher (Wiederkehrend)',
}

# Credit/Debit
CREDIT_DEBIT = {
    'C': 'Credit (Gutschrift/Einnahme)',
    'D': 'Debit (Ausgabe)',
}


class VoucherHelper:
    """Helper-Klasse fuer Voucher/Beleg-Operationen auf hohem Level"""

    def __init__(self, client):
        self.client = client

    def list(
        self,
        supplier_id: Optional[int] = None,
        status: Optional[str] = None,
        credit_debit: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        description: Optional[str] = None
    ) -> List[VoucherResponse]:
        """
        Listet Belege/Voucher auf.

        Args:
            supplier_id: Lieferanten-ID (Contact-ID)
            status: Status-Filter ('draft', 'open', 'partial', 'paid' oder Status-Code)
            credit_debit: 'C' fuer Gutschriften, 'D' fuer Belastungen
            start_date: Startdatum (YYYY-MM-DD oder Timestamp)
            end_date: Enddatum (YYYY-MM-DD oder Timestamp)
            description: Beschreibung/Belegnummer (Like-Suche)

        Returns:
            Liste von VoucherResponse-Objekten
        """
        # Status-Mapping
        status_map = {
            'draft': 50.0,
            'open': 100.0,
            'partial': 200.0,
            'paid': 1000.0,
        }
        status_value = None
        if status:
            if status.lower() in status_map:
                status_value = status_map[status.lower()]
            else:
                try:
                    status_value = float(status)
                except ValueError:
                    pass

        # Datum in Timestamp konvertieren
        start_ts = self._date_to_timestamp(start_date) if start_date else None
        end_ts = self._date_to_timestamp(end_date) if end_date else None

        try:
            vouchers = self.client.voucher.getVouchers(
                contact_id=supplier_id,
                contact_objectName="Contact" if supplier_id else None,
                status=status_value,
                creditDebit=credit_debit,
                startDate=start_ts,
                endDate=end_ts,
                descriptionLike=description
            )
            return vouchers if vouchers else []
        except Exception:
            return []

    def find_by_id(self, voucher_id: int) -> Optional[VoucherResponse]:
        """
        Ruft einen Beleg per ID ab.

        Args:
            voucher_id: ID des Belegs

        Returns:
            VoucherResponse oder None
        """
        try:
            result = self.client.voucher.getVoucherById(voucher_id)
            if isinstance(result, list) and len(result) > 0:
                return result[0]
            return result
        except Exception:
            return None

    def find_by_description(self, description: str) -> Optional[VoucherResponse]:
        """
        Sucht einen Beleg nach Beschreibung/Belegnummer.

        Args:
            description: Belegnummer oder Beschreibung

        Returns:
            VoucherResponse oder None (erster Treffer)
        """
        vouchers = self.list(description=description)
        return vouchers[0] if vouchers else None

    def get_positions(self, voucher_id: int) -> List[VoucherPosResponse]:
        """
        Ruft die Positionen eines Belegs ab.

        Args:
            voucher_id: ID des Belegs

        Returns:
            Liste von VoucherPosResponse-Objekten
        """
        try:
            positions = self.client.voucherpos.getVoucherPositions(
                voucher_id=voucher_id,
                voucher_objectName="Voucher"
            )
            return positions if positions else []
        except Exception:
            return []

    def get_open(self) -> List[VoucherResponse]:
        """
        Ruft alle offenen (unbezahlten) Belege ab.

        Returns:
            Liste von offenen VoucherResponse-Objekten
        """
        return self.list(status='open')

    def get_paid(self) -> List[VoucherResponse]:
        """
        Ruft alle bezahlten Belege ab.

        Returns:
            Liste von bezahlten VoucherResponse-Objekten
        """
        return self.list(status='paid')

    def get_drafts(self) -> List[VoucherResponse]:
        """
        Ruft alle Entwuerfe ab.

        Returns:
            Liste von Entwurf-VoucherResponse-Objekten
        """
        return self.list(status='draft')

    def get_expenses(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[VoucherResponse]:
        """
        Ruft alle Ausgaben (Debit) ab.

        Args:
            start_date: Startdatum (YYYY-MM-DD)
            end_date: Enddatum (YYYY-MM-DD)

        Returns:
            Liste von Ausgaben-Belegen
        """
        return self.list(credit_debit='D', start_date=start_date, end_date=end_date)

    def get_credits(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[VoucherResponse]:
        """
        Ruft alle Gutschriften (Credit) ab.

        Args:
            start_date: Startdatum (YYYY-MM-DD)
            end_date: Enddatum (YYYY-MM-DD)

        Returns:
            Liste von Gutschrift-Belegen
        """
        return self.list(credit_debit='C', start_date=start_date, end_date=end_date)

    def get_recent(self, days: int = 30) -> List[VoucherResponse]:
        """
        Ruft Belege der letzten X Tage ab.

        Args:
            days: Anzahl Tage (default: 30)

        Returns:
            Liste von VoucherResponse-Objekten
        """
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        return self.list(start_date=start_date, end_date=end_date)

    def get_by_supplier(self, supplier_id: int) -> List[VoucherResponse]:
        """
        Ruft alle Belege eines Lieferanten ab.

        Args:
            supplier_id: Contact-ID des Lieferanten

        Returns:
            Liste von VoucherResponse-Objekten
        """
        return self.list(supplier_id=supplier_id)

    def calculate_totals(self, vouchers: List[VoucherResponse]) -> dict:
        """
        Berechnet Summen fuer eine Liste von Belegen.

        Args:
            vouchers: Liste von VoucherResponse-Objekten

        Returns:
            Dict mit 'net', 'tax', 'gross', 'paid', 'count'
        """
        net = 0.0
        tax = 0.0
        gross = 0.0
        paid = 0.0
        count = len(vouchers)

        for v in vouchers:
            if v.sumNet:
                net += float(v.sumNet)
            if v.sumTax:
                tax += float(v.sumTax)
            if v.sumGross:
                gross += float(v.sumGross)
            if v.paidAmount:
                paid += float(v.paidAmount)

        return {
            'net': net,
            'tax': tax,
            'gross': gross,
            'paid': paid,
            'open': gross - paid,
            'count': count
        }

    def get_status_label(self, status: str) -> str:
        """
        Gibt das deutsche Label fuer einen Status-Code zurueck.

        Args:
            status: Status-Code (z.B. '100')

        Returns:
            Status-Label (z.B. 'Open (Unbezahlt)')
        """
        return VOUCHER_STATUS.get(str(status), f'Unknown ({status})')

    def group_by_status(self, vouchers: List[VoucherResponse]) -> dict:
        """
        Gruppiert Belege nach Status.

        Args:
            vouchers: Liste von VoucherResponse-Objekten

        Returns:
            Dict mit Status als Key und Liste als Value
        """
        grouped = {}
        for v in vouchers:
            status = str(v.status) if v.status else 'unknown'
            if status not in grouped:
                grouped[status] = []
            grouped[status].append(v)
        return grouped

    def group_by_supplier(self, vouchers: List[VoucherResponse]) -> dict:
        """
        Gruppiert Belege nach Lieferant.

        Args:
            vouchers: Liste von VoucherResponse-Objekten

        Returns:
            Dict mit Lieferant-Name als Key und Liste als Value
        """
        grouped = {}
        for v in vouchers:
            supplier_name = v.supplierName or 'Unbekannt'
            if v.supplier and hasattr(v.supplier, 'id_'):
                # Hat Supplier-Referenz
                pass
            if supplier_name not in grouped:
                grouped[supplier_name] = []
            grouped[supplier_name].append(v)
        return grouped

    def _date_to_timestamp(self, date_str: str) -> Optional[int]:
        """Konvertiert ein Datum (YYYY-MM-DD) in Unix-Timestamp"""
        try:
            # Pruefen ob schon Timestamp
            if date_str.isdigit():
                return int(date_str)
            # YYYY-MM-DD parsen
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return int(dt.timestamp())
        except (ValueError, AttributeError):
            return None
