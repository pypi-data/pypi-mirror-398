"""
OrderHelper - High-Level Angebots-/Auftrags-Verwaltung

Order-Typen in sevDesk:
- AN = Angebot (Estimate/Proposal)
- AB = Auftragsbestaetigung (Order Confirmation)
- LI = Lieferschein (Delivery Note)

Beispiele:
    # Angebot erstellen
    order = sevdesk.orderHelper.new(
        contact=contact,
        orderNumber='AN-001',
        orderType='AN'
    )
    order.addPosition('Consulting', quantity=10, price=150.00)
    order.save()

    # PDF generieren
    order.render()
    pdf = order.getPDF()

    # In Rechnung umwandeln
    invoice = sevdesk.orderHelper.create_invoice_from_order(order_id=123)
"""

from datetime import datetime
from typing import Optional, List
from sevdesk.models.orderresponse import OrderResponse
from sevdesk.models.order import Order
# Note: SaveOrder model bypassed due to incorrect type (order: str instead of Order)
from sevdesk.converters.contact import Contact
from sevdesk.converters.contactperson import ContactPerson
from sevdesk.converters.addresscountry import AddressCountry
from sevdesk.converters.taxrule import TaxRule


# Order Types
ORDER_TYPES = {
    'AN': 'Angebot (Estimate)',
    'AB': 'Auftragsbestaetigung (Order Confirmation)',
    'LI': 'Lieferschein (Delivery Note)',
}

# Order Status
ORDER_STATUS = {
    '100': 'Draft (Entwurf)',
    '200': 'Delivered (Versendet)',
    '300': 'Rejected (Abgelehnt)',
    '500': 'Accepted (Angenommen)',
    '750': 'Partially Calculated (Teilberechnet)',
    '1000': 'Calculated (Berechnet)',
}


class OrderExt:
    """Erweiterte Order-Klasse mit High-Level Funktionen"""

    def __init__(self, client, contact, orderNumber: str, orderType: str = 'AN',
                 orderDate: str = None, status: str = '100', header: str = None,
                 headText: str = None, footText: str = None, address: str = None,
                 taxRate: float = 19.0, taxRule_id: str = '1', taxText: str = 'Umsatzsteuer',
                 taxType: str = 'default', currency: str = 'EUR',
                 contactPerson_id: int = None, addressCountry_id: int = 1):
        self._client = client
        self._saved_id = None
        self._pending_positions = []

        # Contact normalisieren
        if isinstance(contact, int):
            self._contact = Contact(id_=contact, objectName="Contact")
        elif hasattr(contact, 'id_'):
            self._contact = Contact(id_=contact.id_, objectName="Contact")
        else:
            self._contact = contact

        self._orderNumber = orderNumber
        self._orderType = orderType
        self._status = status
        self._header = header or f"{orderType}-{orderNumber}"
        self._headText = headText
        self._footText = footText
        self._address = address
        self._taxRate = taxRate
        self._taxRule = TaxRule(id_=taxRule_id, objectName="TaxRule")
        self._taxText = taxText
        self._taxType = taxType
        self._currency = currency
        self._addressCountry = AddressCountry(id_=addressCountry_id, objectName="StaticCountry")

        # Datum
        if orderDate:
            self._orderDate = orderDate
        else:
            self._orderDate = datetime.now().strftime("%Y-%m-%d")

        # ContactPerson
        if contactPerson_id:
            self._contactPerson = ContactPerson(id_=contactPerson_id, objectName="SevUser")
        else:
            self._contactPerson = None

    def _get_default_contact_person(self) -> ContactPerson:
        """Holt den ersten verfuegbaren SevUser"""
        try:
            users = self._client.undocumented.sevuser.getSevUsers(limit=1)
            if users and len(users) > 0:
                user = users[0]
                user_id = user.get('id') or user.get('id_')
                if user_id:
                    return ContactPerson(id_=int(user_id), objectName="SevUser")
        except Exception:
            pass
        raise RuntimeError("Kein SevUser gefunden. Bitte contactPerson_id angeben.")

    def addPosition(self, name: str, quantity: float, price: float = None,
                    priceGross: float = None, taxRate: float = 19.0,
                    text: str = None) -> 'OrderExt':
        """
        Fuegt eine Position hinzu.

        Args:
            name: Positionsname
            quantity: Menge
            price: Einzelpreis (netto) - wird verwendet wenn priceGross nicht gesetzt
            priceGross: Brutto-Einzelpreis - wenn gesetzt wird price ignoriert
            taxRate: Steuersatz (default: 19)
            text: Zusaetzlicher Text

        Returns:
            self (Method-Chaining)
        """
        if priceGross is None and price is None:
            raise ValueError("Entweder price oder priceGross muss angegeben werden")

        self._pending_positions.append({
            'name': name,
            'quantity': quantity,
            'price': price,
            'priceGross': priceGross,
            'taxRate': taxRate,
            'text': text
        })
        return self

    def save(self) -> 'OrderExt':
        """
        Speichert das Angebot/den Auftrag.

        Returns:
            self mit gesetzter ID
        """
        if not self._client:
            raise RuntimeError("Client nicht gesetzt")

        if not self._contactPerson:
            self._contactPerson = self._get_default_contact_person()

        # Order-Objekt erstellen
        order = Order(
            objectName="Order",
            mapAll=True,
            contact=self._contact,
            contactPerson=self._contactPerson,
            orderNumber=self._orderNumber,
            orderDate=self._orderDate,
            status=int(self._status),
            header=self._header,
            headText=self._headText,
            footText=self._footText,
            orderType=self._orderType,
            currency=self._currency,
            taxRate=self._taxRate,
            taxRule=self._taxRule,
            taxText=self._taxText,
            taxType=self._taxType,
            address=self._address,
            addressCountry=self._addressCountry,
            version=0,
        )

        # Positionen vorbereiten
        order_pos_save = None
        if self._pending_positions:
            order_pos_save = []
            for pos in self._pending_positions:
                pos_dict = {
                    "objectName": "OrderPos",
                    "mapAll": "true",
                    "quantity": pos['quantity'],
                    "name": pos['name'],
                    "unity": {"id": 1, "objectName": "Unity"},
                    "taxRate": pos.get('taxRate', 19.0),
                }
                # Verwende priceGross wenn vorhanden, sonst price (netto)
                if pos.get('priceGross') is not None:
                    pos_dict["priceGross"] = pos['priceGross']
                elif pos.get('price') is not None:
                    pos_dict["price"] = pos['price']
                if pos.get('text'):
                    pos_dict["text"] = pos['text']
                order_pos_save.append(pos_dict)

        # Direkt an Factory/saveOrder senden (bypass broken SaveOrder Pydantic model)
        order_dict = order.model_dump(by_alias=True, exclude_none=True)
        request_body = {"order": order_dict}
        if order_pos_save:
            request_body["orderPosSave"] = order_pos_save

        response = self._client.session.request(
            method='POST',
            url=f'{self._client.api_base}/Order/Factory/saveOrder',
            json=request_body,
            headers={'Authorization': self._client.api_token}
        )
        result = response.json()

        # ID extrahieren
        if isinstance(result, dict):
            objects = result.get('objects', {})
            if objects and 'order' in objects:
                order_obj = objects['order']
                self._saved_id = int(order_obj.get('id') or order_obj.get('id_'))
            elif result.get('id'):
                self._saved_id = int(result.get('id'))
            else:
                raise RuntimeError(f"Konnte Order-ID nicht extrahieren: {result}")
        else:
            raise RuntimeError(f"Unerwartete API-Antwort: {result}")

        if not self._saved_id:
            raise RuntimeError(f"Konnte Order-ID nicht extrahieren: {result}")

        self._pending_positions = []
        return self

    def render(self) -> 'OrderExt':
        """Rendert das Angebot/den Auftrag als PDF"""
        if not self._saved_id:
            raise RuntimeError("Order muss zuerst gespeichert werden")
        # sevDesk rendert automatisch beim PDF-Abruf
        return self

    def getPDF(self, download: bool = True) -> Optional[bytes]:
        """Laedt die PDF herunter"""
        if not self._saved_id:
            raise RuntimeError("Order muss zuerst gespeichert werden")
        return self._client.order.orderGetPdf(self._saved_id, download=download)

    def markAsSent(self) -> 'OrderExt':
        """Markiert als versendet (Status 200)"""
        if not self._saved_id:
            raise RuntimeError("Order muss zuerst gespeichert werden")
        self._client.order.orderSendBy(self._saved_id)
        return self

    @property
    def id(self) -> Optional[int]:
        return self._saved_id


class OrderHelper:
    """Helper-Klasse fuer Order-Operationen"""

    def __init__(self, client):
        self.client = client
        self._cached_sev_user_id = None

    def _get_default_contact_person_id(self) -> int:
        if self._cached_sev_user_id:
            return self._cached_sev_user_id
        try:
            users = self.client.undocumented.sevuser.getSevUsers(limit=1)
            if users and len(users) > 0:
                user_id = users[0].get('id') or users[0].get('id_')
                if user_id:
                    self._cached_sev_user_id = int(user_id)
                    return self._cached_sev_user_id
        except Exception:
            pass
        raise RuntimeError("Kein SevUser gefunden")

    def new(self, contact, orderNumber: str, orderType: str = 'AN',
            orderDate: str = None, status: str = '100', header: str = None,
            headText: str = None, footText: str = None, address: str = None,
            taxRate: float = 19.0, contactPerson_id: int = None,
            currency: str = 'EUR') -> OrderExt:
        """
        Erstellt ein neues Angebot/Auftrag (noch nicht gespeichert).

        Args:
            contact: Contact-Objekt oder ID
            orderNumber: Angebots-/Auftragsnummer
            orderType: 'AN'=Angebot, 'AB'=Auftragsbestaetigung, 'LI'=Lieferschein
            orderDate: Datum (default: heute)
            status: '100'=Draft
            contactPerson_id: SevUser-ID (optional)

        Returns:
            OrderExt-Objekt
        """
        return OrderExt(
            client=self.client,
            contact=contact,
            orderNumber=orderNumber,
            orderType=orderType,
            orderDate=orderDate,
            status=status,
            header=header,
            headText=headText,
            footText=footText,
            address=address,
            taxRate=taxRate,
            contactPerson_id=contactPerson_id,
            currency=currency,
        )

    def find_by_id(self, order_id: int) -> Optional[OrderResponse]:
        """Ruft ein Angebot/Auftrag per ID ab"""
        try:
            result = self.client.order.getOrderById(order_id)
            if isinstance(result, list) and len(result) > 0:
                return result[0]
            return result
        except Exception:
            return None

    def find_by_number(self, order_number: str) -> Optional[OrderResponse]:
        """Sucht nach Angebots-/Auftragsnummer"""
        try:
            orders = self.client.order.getOrders(orderNumber=order_number)
            return orders[0] if orders else None
        except Exception:
            return None

    def list(self, contact_id: int = None, status: int = None,
             order_type: str = None, limit: int = 100) -> List[OrderResponse]:
        """
        Listet Angebote/Auftraege auf.

        Args:
            contact_id: Filter nach Kontakt
            status: Filter nach Status (100, 200, etc.)
            order_type: Filter nach Typ ('AN', 'AB', 'LI')
            limit: Max. Anzahl

        Returns:
            Liste von OrderResponse
        """
        try:
            orders = self.client.order.getOrders(
                contact_id=contact_id,
                contact_objectName="Contact" if contact_id else None,
                status=status
            )
            if not orders:
                return []

            # Nach Typ filtern (clientseitig)
            if order_type:
                orders = [o for o in orders if o.orderType == order_type]

            return orders[:limit]
        except Exception:
            return []

    def get_estimates(self, contact_id: int = None) -> List[OrderResponse]:
        """Ruft alle Angebote ab"""
        return self.list(contact_id=contact_id, order_type='AN')

    def get_confirmations(self, contact_id: int = None) -> List[OrderResponse]:
        """Ruft alle Auftragsbestaetigungen ab"""
        return self.list(contact_id=contact_id, order_type='AB')

    def get_delivery_notes(self, contact_id: int = None) -> List[OrderResponse]:
        """Ruft alle Lieferscheine ab"""
        return self.list(contact_id=contact_id, order_type='LI')

    def get_positions(self, order_id: int) -> list:
        """Ruft Positionen eines Angebots/Auftrags ab"""
        try:
            return self.client.order.getOrderPositionsById(order_id) or []
        except Exception:
            return []

    def get_pdf(self, order_id: int, download: bool = True) -> Optional[bytes]:
        """Laedt PDF eines Angebots/Auftrags"""
        try:
            return self.client.order.orderGetPdf(order_id, download=download)
        except Exception:
            return None

    def mark_as_sent(self, order_id: int) -> Optional[OrderResponse]:
        """Markiert als versendet"""
        try:
            return self.client.order.orderSendBy(order_id)
        except Exception:
            return None

    def get_status_label(self, status: str) -> str:
        """Gibt Status-Label zurueck"""
        return ORDER_STATUS.get(str(status), f'Unknown ({status})')

    def get_type_label(self, order_type: str) -> str:
        """Gibt Typ-Label zurueck"""
        return ORDER_TYPES.get(order_type, f'Unknown ({order_type})')

    def calculate_totals(self, orders: List[OrderResponse]) -> dict:
        """Berechnet Summen"""
        net = 0.0
        tax = 0.0
        gross = 0.0
        for o in orders:
            if o.sumNet:
                net += float(o.sumNet)
            if o.sumTax:
                tax += float(o.sumTax)
            if o.sumGross:
                gross += float(o.sumGross)
        return {'net': net, 'tax': tax, 'gross': gross, 'count': len(orders)}
