"""
InvoiceExt - Erweiterte Invoice-Klasse mit High-Level Funktionen

Diese Klasse erweitert das Standard-Invoice-Modell mit praktischen Methoden:
- addPosition() - Positionen hinzufuegen
- save() - Als Draft oder fertig speichern
- getPDF() - PDF generieren
- render() - Als PDF rendern
"""

from typing import Optional, List
from sevdesk.models.invoice import Invoice as InvoiceBase


class InvoiceExt(InvoiceBase):
    """
    Erweiterte Invoice-Klasse mit High-Level Funktionen.

    Beispiel:
        invoice = InvoiceExt(...)
        invoice.addPosition(name='Service', quantity=1, price=100)
        invoice.save(status='DRAFT')
        pdf_url = invoice.getPDF()
    """

    # Store fuer noch nicht gespeicherte Positionen
    _pending_positions: List[dict] = []
    _client = None
    _saved_id = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pending_positions = []
        self._saved_id = None

    def _set_client(self, client):
        """Intern: Setzt den Client-Referenz"""
        self._client = client
        return self

    def _set_saved_id(self, invoice_id):
        """Intern: Setzt die ID nach erfolgreicher Speicherung"""
        self._saved_id = invoice_id
        return self

    def addPosition(self, name: str, quantity: float, price: float = None,
                    priceGross: float = None, taxRate: float = 19.0,
                    text: str = None) -> 'InvoiceExt':
        """
        Fuegt eine Position zur Rechnung hinzu (vor dem Speichern).

        Args:
            name: Name der Position
            quantity: Menge
            price: Einzelpreis (netto) - wird verwendet wenn priceGross nicht gesetzt
            priceGross: Brutto-Einzelpreis - wenn gesetzt wird price ignoriert
            taxRate: Steuersatz (default: 19)
            text: Zusaetzlicher Text (optional)

        Returns:
            self (fuer Method-Chaining)
        """
        if priceGross is None and price is None:
            raise ValueError("Entweder price oder priceGross muss angegeben werden")

        position = {
            "name": name,
            "quantity": quantity,
            "price": price,
            "priceGross": priceGross,
            "taxRate": taxRate,
        }
        if text:
            position["text"] = text

        self._pending_positions.append(position)
        return self

    def save(self, status: str = "100") -> 'InvoiceExt':
        """
        Speichert die Rechnung auf sevDesk.

        Args:
            status: Status der Rechnung
                   '100' = DRAFT (Entwurf)
                   '1000' = Fertig (default API status)

        Returns:
            self mit gesetzter ID (fuer Method-Chaining)
        """
        if not self._client:
            raise RuntimeError("Client nicht gesetzt. Verwende InvoiceHelper.new() oder setzen Sie _set_client()")

        # Invoice-Model vorbereiten mit aktuellem Status
        self.status = status

        # Ueber undocumented Controller speichern
        result = self._client.undocumented.invoice.createInvoice(body=self)

        # ID aus Response extrahieren
        if hasattr(result, 'id_'):
            self._saved_id = result.id_
        elif hasattr(result, 'id'):
            self._saved_id = result.id
        elif isinstance(result, dict):
            self._saved_id = result.get('id') or result.get('id_')

        if not self._saved_id:
            raise RuntimeError("Konnte Invoice-ID nicht aus Response extrahieren")

        # Positionen hinzufuegen, falls vorhanden
        if self._pending_positions:
            self._save_positions()

        return self

    def _save_positions(self):
        """Intern: Speichert alle pending Positionen via InvoicePos Controller."""
        from sevdesk.models.invoicepos import InvoicePos
        from sevdesk.converters.invoice import Invoice
        from sevdesk.converters.unity import Unity

        if not self._saved_id:
            raise RuntimeError("Rechnung muss zuerst gespeichert werden")

        for pos_data in self._pending_positions:
            # InvoicePos-Objekt erstellen - verwende priceGross wenn vorhanden
            pos_kwargs = {
                "objectName": "InvoicePos",
                "invoice": Invoice(id_=self._saved_id, objectName="Invoice"),
                "quantity": pos_data["quantity"],
                "name": pos_data["name"],
                "unity": Unity(id_=1, objectName="Unity"),  # 1 = Stueck
                "taxRate": pos_data.get("taxRate", 19.0),
                "text": pos_data.get("text"),
                "mapAll": True
            }

            # Verwende priceGross wenn vorhanden, sonst price (netto)
            if pos_data.get("priceGross") is not None:
                pos_kwargs["priceGross"] = pos_data["priceGross"]
            elif pos_data.get("price") is not None:
                pos_kwargs["price"] = pos_data["price"]

            invoice_pos = InvoicePos(**pos_kwargs)

            # Position ueber Controller speichern
            try:
                self._client.undocumented.invoicepos.createInvoicePos(body=invoice_pos)
            except Exception as e:
                print(f"Warnung: Position '{pos_data['name']}' konnte nicht gespeichert werden: {e}")

        # Pending Positionen leeren
        self._pending_positions = []

    def render(self) -> str:
        """
        Rendert die Rechnung als PDF.

        Returns:
            PDF-URL (zum Download)
        """
        if not self._saved_id:
            raise RuntimeError("Rechnung muss zuerst gespeichert werden (save())")

        if not self._client:
            raise RuntimeError("Client nicht gesetzt")

        try:
            result = self._client.invoice.invoiceRender(self._saved_id)
            return result
        except Exception as e:
            raise RuntimeError(f"Fehler beim Rendern: {e}")

    def getPDF(self, download: bool = False) -> Optional[bytes]:
        """
        Laedt die PDF der Rechnung herunter.

        Args:
            download: Ob die Datei heruntergeladen werden soll

        Returns:
            PDF-Inhalt (bytes) oder URL
        """
        if not self._saved_id:
            raise RuntimeError("Rechnung muss zuerst gespeichert werden (save())")

        if not self._client:
            raise RuntimeError("Client nicht gesetzt")

        try:
            result = self._client.invoice.invoiceGetPdf(self._saved_id, download=download)
            return result
        except Exception as e:
            raise RuntimeError(f"Fehler beim PDF-Download: {e}")

    def markAsSent(self) -> 'InvoiceExt':
        """Markiert die Rechnung als versendet."""
        if not self._saved_id:
            raise RuntimeError("Rechnung muss zuerst gespeichert werden (save())")

        if not self._client:
            raise RuntimeError("Client nicht gesetzt")

        try:
            self._client.invoice.invoiceSendBy(self._saved_id)
            return self
        except Exception as e:
            raise RuntimeError(f"Fehler beim Markieren als versendet: {e}")

    def getPositions(self) -> List[dict]:
        """Ruft die Positionen der gespeicherten Rechnung ab."""
        if not self._saved_id:
            return self._pending_positions

        if not self._client:
            raise RuntimeError("Client nicht gesetzt")

        try:
            return self._client.invoice.getInvoicePositionsById(self._saved_id)
        except Exception:
            return self._pending_positions
