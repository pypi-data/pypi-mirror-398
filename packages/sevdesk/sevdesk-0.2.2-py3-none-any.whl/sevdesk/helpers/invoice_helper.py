"""
InvoiceHelper - High-Level Rechnungs-Verwaltung

Beispiele:
    invoice = sevdesk.invoiceHelper.new(
        contact=contact,
        invoiceDate='2025-12-16',
        invoiceNumber='REC-001'
    )
    invoice.addPosition('Service', 1, 100)
    invoice.save(status='DRAFT')
    
    invoice = sevdesk.invoiceHelper.find_by_id(12345)
"""

from datetime import datetime
from typing import Optional
from sevdesk.helpermodels.invoice_ext import InvoiceExt
from sevdesk.converters.contact import Contact
from sevdesk.converters.contactperson import ContactPerson
from sevdesk.converters.addresscountry import AddressCountry
from sevdesk.converters.taxrule import TaxRule


class InvoiceHelper:
    """Helper-Klasse für Rechnungs-Operationen auf hohem Level"""

    def __init__(self, client):
        self.client = client
        self._cached_sev_user_id = None

    def _get_default_contact_person_id(self) -> int:
        """Holt den ersten verfuegbaren SevUser als ContactPerson-ID"""
        if self._cached_sev_user_id:
            return self._cached_sev_user_id
        try:
            users = self.client.undocumented.sevuser.getSevUsers(limit=1)
            if users and len(users) > 0:
                user = users[0]
                user_id = user.get('id') or user.get('id_')
                if user_id:
                    self._cached_sev_user_id = int(user_id)
                    return self._cached_sev_user_id
        except Exception:
            pass
        raise RuntimeError(
            "Kein SevUser gefunden. Bitte contactPerson_id explizit angeben."
        )

    def new(self,
            contact,
            invoiceDate: Optional[str] = None,
            invoiceNumber: str = "",
            addressCountry_id: int = 1,
            addressCountry_name: str = "StaticCountry",
            status: str = "100",
            invoiceType: str = "RE",
            taxRate: float = 19.0,
            taxRule_id: str = "1",
            taxText: str = "Umsatzsteuer",
            taxType: str = "default",
            currency: str = "EUR",
            discount: int = 0,
            contactPerson_id: Optional[int] = None,
            contactPerson_name: str = "SevUser",
            header: Optional[str] = None,
            headText: Optional[str] = None,
            footText: Optional[str] = None,
            timeToPay: Optional[int] = None) -> InvoiceExt:
        """
        Erstellt eine neue Rechnung (noch nicht gespeichert).
        
        Args:
            contact: Contact-Objekt oder Contact-ID
            invoiceDate: Rechnungsdatum (default: heute)
            invoiceNumber: Rechnungsnummer
            addressCountry_id: Land-ID (1=Deutschland)
            status: Status ('100'=Draft, '1000'=Fertig)
            invoiceType: Typ ('RE'=Rechnung)
            taxRate: Steuersatz (default: 19)
            taxRule_id: Steuerregel-ID
            currency: Währung (default: EUR)
            contactPerson_id: Ansprechpartner-ID (optional, wird automatisch ermittelt)
            header: Header-Text
            headText: Kopftext
            footText: Fußtext
            timeToPay: Zahlungsfrist in Tagen

        Returns:
            InvoiceExt-Objekt (noch nicht gespeichert)
        """
        # Contact normalisieren
        if isinstance(contact, int):
            contact = Contact(id_=contact, objectName="Contact")
        elif isinstance(contact, dict):
            contact = Contact(id_=contact['id_'], objectName="Contact")
        elif hasattr(contact, 'id_'):
            # ContactResponse oder ähnliches Objekt -> zu Contact converter konvertieren
            contact = Contact(id_=contact.id_, objectName="Contact")
        # Sonst: Annahme dass es ein Contact-Objekt ist

        # Datum default auf heute
        if invoiceDate is None:
            invoiceDate = datetime.now().strftime("%Y-%m-%d")

        # ContactPerson-ID: automatisch holen wenn nicht angegeben
        if contactPerson_id is None:
            contactPerson_id = self._get_default_contact_person_id()

        # InvoiceExt erstellen
        invoice = InvoiceExt(
            contact=contact,
            contactPerson=ContactPerson(id_=contactPerson_id, objectName=contactPerson_name),
            invoiceDate=invoiceDate,
            invoiceNumber=invoiceNumber,
            addressCountry=AddressCountry(id_=addressCountry_id, objectName=addressCountry_name),
            status=status,
            invoiceType=invoiceType,
            taxRate=taxRate,
            taxRule=TaxRule(id_=taxRule_id, objectName="TaxRule"),
            taxText=taxText,
            taxType=taxType,
            currency=currency,
            discount=discount,
            header=header,
            headText=headText,
            footText=footText,
            timeToPay=timeToPay,
            mapAll=True
        )
        
        # Client setzen für spätere Operationen
        invoice._set_client(self.client)
        
        return invoice
    
    def find_by_id(self, invoice_id: int):
        """
        Ruft eine Rechnung per ID ab.
        
        Args:
            invoice_id: ID der Rechnung
            
        Returns:
            InvoiceResponse oder None
        """
        try:
            result = self.client.invoice.getInvoiceById(invoice_id)
            if isinstance(result, list) and len(result) > 0:
                return result[0]
            return result
        except Exception:
            return None
    
    def find_by_number(self, invoice_number: str):
        """
        Sucht eine Rechnung per Rechnungsnummer.
        
        Args:
            invoice_number: Rechnungsnummer
            
        Returns:
            InvoiceResponse oder None
        """
        try:
            invoices = self.client.invoice.getInvoices(invoiceNumber=invoice_number)
            if invoices and len(invoices) > 0:
                return invoices[0]
            return None
        except Exception:
            return None
    
    def list(self, contact_id: Optional[int] = None, status: Optional[str] = None, limit: int = 100):
        """
        Listet Rechnungen auf.

        Args:
            contact_id: Optional: nur für einen Kontakt
            status: Optional: filtere nach Status
            limit: Max. Anzahl (wird durch API begrenzt)

        Returns:
            Liste von InvoiceResponse-Objekten
        """
        try:
            invoices = self.client.invoice.getInvoices(
                contact_id=contact_id,
                status=float(status) if status else None
            )
            return invoices[:limit] if invoices else []
        except Exception:
            return []

    def get_positions(self, invoice_id: int) -> list:
        """Ruft Positionen einer Rechnung ab"""
        try:
            return self.client.invoice.getInvoicePositionsById(invoice_id) or []
        except Exception:
            return []

    def get_pdf(self, invoice_id: int, download: bool = True):
        """Laedt PDF einer Rechnung herunter"""
        try:
            return self.client.invoice.invoiceGetPdf(invoice_id, download=download)
        except Exception:
            return None

    def render(self, invoice_id: int):
        """Rendert die Rechnung als PDF"""
        try:
            return self.client.invoice.invoiceRender(invoice_id)
        except Exception:
            return None

    def finalize(self, invoice_id: int, send_type: str = "VPR"):
        """
        Finalisiert eine Rechnung (Status 200 = Offen).

        Setzt Status auf 'Offen' und markiert als versendet.

        Args:
            invoice_id: ID der Rechnung
            send_type: Art des Versands ("VPR", "VP", "VPDF", "VM")

        Returns:
            InvoiceResponse oder None
        """
        try:
            # Erst rendern
            self.client.invoice.invoiceRender(invoice_id)
            # Dann als versendet markieren (setzt Status auf 200)
            # Verwende undocumented Controller mit sendType
            return self.client.undocumented.invoice.invoiceSendByWithType(invoice_id, sendType=send_type)
        except Exception as e:
            print(f"Finalize error: {e}")
            return None

    def cancel(self, invoice_id: int):
        """
        Storniert eine Rechnung (erstellt Stornorechnung).

        WICHTIG: Nur offene Rechnungen (Status 200) koennen storniert werden!
        Fuer Draft-Rechnungen (Status 100) verwenden Sie delete() stattdessen.

        Args:
            invoice_id: ID der Rechnung

        Returns:
            Stornorechnung (InvoiceResponse) oder None
        """
        try:
            return self.client.invoice.cancelInvoice(invoice_id)
        except Exception:
            return None

    def delete(self, invoice_id: int) -> bool:
        """
        Loescht eine Rechnung.

        WICHTIG: Nur Draft-Rechnungen (Status 100) koennen geloescht werden!
        Fuer offene/versendete Rechnungen (Status 200) verwenden Sie cancel() stattdessen.

        Args:
            invoice_id: ID der Rechnung

        Returns:
            True wenn erfolgreich, False bei Fehler
        """
        try:
            self.client.invoice.deleteInvoice(invoice_id)
            return True
        except Exception:
            return False

    def mark_as_sent(self, invoice_id: int):
        """Markiert Rechnung als versendet"""
        try:
            return self.client.invoice.invoiceSendBy(invoice_id)
        except Exception:
            return None

    def reset_to_draft(self, invoice_id: int) -> bool:
        """Setzt Status zurueck auf Entwurf"""
        try:
            self.client.invoice.invoiceResetToDraft(invoice_id)
            return True
        except Exception:
            return False

    def reset_to_open(self, invoice_id: int) -> bool:
        """Setzt Status zurueck auf Offen"""
        try:
            self.client.invoice.invoiceResetToOpen(invoice_id)
            return True
        except Exception:
            return False

    def enshrine(self, invoice_id: int) -> bool:
        """Schreibt Rechnung fest (nicht mehr aenderbar)"""
        try:
            self.client.invoice.invoiceEnshrine(invoice_id)
            return True
        except Exception:
            return False

    def book(self, invoice_id: int) -> bool:
        """Bucht die Rechnung"""
        try:
            self.client.invoice.bookInvoice(invoice_id)
            return True
        except Exception:
            return False

    def is_partially_paid(self, invoice_id: int) -> bool:
        """Prueft ob Rechnung teilweise bezahlt ist"""
        try:
            result = self.client.invoice.getIsInvoicePartiallyPaid(invoice_id)
            if isinstance(result, dict):
                return result.get('objects', False)
            return bool(result)
        except Exception:
            return False

    def create_reminder(self, invoice_id: int):
        """Erstellt eine Mahnung"""
        try:
            return self.client.invoice.createInvoiceReminder(
                invoice_id=invoice_id,
                invoice_objectName="Invoice"
            )
        except Exception:
            return None

    def get_xml(self, invoice_id: int):
        """Ruft E-Rechnung XML ab (ZUGFeRD/XRechnung)"""
        try:
            return self.client.invoice.invoiceGetXml(invoice_id)
        except Exception:
            return None

    def get_drafts(self):
        """Ruft alle Entwuerfe ab (Status 100)"""
        return self.list(status='100')

    def get_open(self):
        """Ruft alle offenen Rechnungen ab (Status 200)"""
        return self.list(status='200')

    def get_paid(self):
        """Ruft alle bezahlten Rechnungen ab (Status 1000)"""
        return self.list(status='1000')

    def get_overdue(self):
        """Ruft alle ueberfaelligen Rechnungen ab (Status 200 + ueberfaellig)"""
        # Status 200 = Offen, muss clientseitig nach Faelligkeit gefiltert werden
        open_invoices = self.get_open()
        today = datetime.now()
        overdue = []
        for inv in open_invoices:
            if inv.paymentDeadline:
                try:
                    deadline = datetime.strptime(inv.paymentDeadline[:10], "%Y-%m-%d")
                    if deadline < today:
                        overdue.append(inv)
                except (ValueError, TypeError):
                    pass
        return overdue

    def calculate_totals(self, invoices: list) -> dict:
        """Berechnet Summen fuer eine Liste von Rechnungen"""
        net = 0.0
        tax = 0.0
        gross = 0.0
        paid = 0.0
        for inv in invoices:
            if inv.sumNet:
                net += float(inv.sumNet)
            if inv.sumTax:
                tax += float(inv.sumTax)
            if inv.sumGross:
                gross += float(inv.sumGross)
            if inv.paidAmount:
                paid += float(inv.paidAmount)
        return {
            'net': net,
            'tax': tax,
            'gross': gross,
            'paid': paid,
            'open': gross - paid,
            'count': len(invoices)
        }
