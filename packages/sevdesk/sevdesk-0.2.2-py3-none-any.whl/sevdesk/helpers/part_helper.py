"""
PartHelper - High-Level Artikel/Produkt-Verwaltung

Parts sind Artikel/Produkte die in Rechnungen und Angeboten verwendet werden.

Beispiele:
    # Artikel suchen
    part = sevdesk.partHelper.find_by_number('ART-001')

    # Neuen Artikel erstellen
    part = sevdesk.partHelper.create(
        name='Beratungsstunde',
        partNumber='CONS-01',
        price=150.00,
        taxRate=19.0
    )

    # Alle Artikel auflisten
    parts = sevdesk.partHelper.list()
"""

from typing import Optional, List
from sevdesk.models.part import Part
from sevdesk.models.partupdate import PartUpdate
from sevdesk.converters.unity import Unity
from sevdesk.converters.category import Category


# Part Status
PART_STATUS = {
    50: 'Inactive (Inaktiv)',
    100: 'Active (Aktiv)',
}

# Unity IDs (Einheiten)
UNITY_IDS = {
    'stueck': 1,
    'stunde': 2,
    'tag': 3,
    'monat': 4,
    'jahr': 5,
    'km': 6,
    'kg': 7,
    'liter': 8,
    'm': 9,
    'm2': 10,
    'm3': 11,
    'pauschal': 12,
}


class PartHelper:
    """Helper-Klasse fuer Artikel-Operationen"""

    def __init__(self, client):
        self.client = client

    def create(self, name: str, partNumber: str, price: float = 0.0,
               taxRate: float = 19.0, unity: str = 'stueck',
               stock: float = 0.0, stockEnabled: bool = False,
               text: str = None, status: int = 100,
               pricePurchase: float = None, category_id: int = None) -> Optional[Part]:
        """
        Erstellt einen neuen Artikel.

        Args:
            name: Artikelname
            partNumber: Artikelnummer
            price: Verkaufspreis (Netto)
            taxRate: Steuersatz (default: 19)
            unity: Einheit ('stueck', 'stunde', 'tag', etc.)
            stock: Lagerbestand
            stockEnabled: Lagerverwaltung aktivieren
            text: Beschreibungstext
            status: 100=Aktiv, 50=Inaktiv
            pricePurchase: Einkaufspreis
            category_id: Kategorie-ID

        Returns:
            Part-Objekt oder None
        """
        unity_id = UNITY_IDS.get(unity.lower(), 1)

        part = Part(
            objectName="Part",
            name=name,
            partNumber=partNumber,
            price=price,
            priceNet=price,
            priceGross=price * (1 + taxRate / 100),
            taxRate=taxRate,
            unity=Unity(id_=unity_id, objectName="Unity"),
            stock=stock,
            stockEnabled=stockEnabled,
            text=text,
            status=status,
            pricePurchase=pricePurchase,
            category=Category(id_=category_id, objectName="Category") if category_id else None,
        )

        try:
            result = self.client.part.createPart(body=part)
            return result
        except Exception:
            return None

    def find_by_id(self, part_id: int) -> Optional[Part]:
        """Ruft einen Artikel per ID ab"""
        try:
            result = self.client.part.getPartById(part_id)
            if isinstance(result, list) and len(result) > 0:
                return result[0]
            return result
        except Exception:
            return None

    def find_by_number(self, part_number: str) -> Optional[Part]:
        """Sucht nach Artikelnummer"""
        try:
            parts = self.client.part.getParts(partNumber=part_number)
            return parts[0] if parts else None
        except Exception:
            return None

    def find_by_name(self, name: str) -> Optional[Part]:
        """Sucht nach Artikelname (exakt)"""
        try:
            parts = self.client.part.getParts(name=name)
            return parts[0] if parts else None
        except Exception:
            return None

    def search(self, query: str) -> List[Part]:
        """
        Sucht Artikel nach Name oder Nummer.

        Args:
            query: Suchbegriff

        Returns:
            Liste von gefundenen Artikeln
        """
        results = []
        try:
            # Nach Name suchen
            by_name = self.client.part.getParts(name=query)
            if by_name:
                results.extend(by_name)

            # Nach Nummer suchen
            by_number = self.client.part.getParts(partNumber=query)
            if by_number:
                for p in by_number:
                    if not any(r.id_ == p.id_ for r in results):
                        results.append(p)
        except Exception:
            pass
        return results

    def list(self, active_only: bool = True) -> List[Part]:
        """
        Listet alle Artikel auf.

        Args:
            active_only: Nur aktive Artikel (Status 100)

        Returns:
            Liste von Part-Objekten
        """
        try:
            parts = self.client.part.getParts()
            if not parts:
                return []
            if active_only:
                parts = [p for p in parts if p.status == 100]
            return parts
        except Exception:
            return []

    def update(self, part_id: int, name: str = None, price: float = None,
               taxRate: float = None, stock: float = None, text: str = None,
               status: int = None, pricePurchase: float = None) -> Optional[Part]:
        """
        Aktualisiert einen Artikel.

        Args:
            part_id: Artikel-ID
            name: Neuer Name (optional)
            price: Neuer Preis (optional)
            taxRate: Neuer Steuersatz (optional)
            stock: Neuer Lagerbestand (optional)
            text: Neue Beschreibung (optional)
            status: Neuer Status (optional)
            pricePurchase: Neuer Einkaufspreis (optional)

        Returns:
            Aktualisiertes Part-Objekt oder None
        """
        update_data = PartUpdate()

        if name is not None:
            update_data.name = name
        if price is not None:
            update_data.price = price
            update_data.priceNet = price
        if taxRate is not None:
            update_data.taxRate = taxRate
        if stock is not None:
            update_data.stock = stock
        if text is not None:
            update_data.text = text
        if status is not None:
            update_data.status = status
        if pricePurchase is not None:
            update_data.pricePurchase = pricePurchase

        try:
            return self.client.part.updatePart(part_id, body=update_data)
        except Exception:
            return None

    def get_stock(self, part_id: int) -> Optional[float]:
        """Ruft den Lagerbestand eines Artikels ab"""
        try:
            result = self.client.part.partGetStock(part_id)
            if isinstance(result, dict) and 'objects' in result:
                return float(result['objects'])
            elif isinstance(result, (int, float)):
                return float(result)
            return None
        except Exception:
            return None

    def set_active(self, part_id: int) -> bool:
        """Setzt Artikel auf aktiv"""
        result = self.update(part_id, status=100)
        return result is not None

    def set_inactive(self, part_id: int) -> bool:
        """Setzt Artikel auf inaktiv"""
        result = self.update(part_id, status=50)
        return result is not None

    def get_or_create(self, name: str, partNumber: str, price: float = 0.0,
                      taxRate: float = 19.0, unity: str = 'stueck') -> Optional[Part]:
        """
        Sucht einen Artikel oder erstellt ihn wenn nicht vorhanden.

        Args:
            name: Artikelname
            partNumber: Artikelnummer
            price: Verkaufspreis
            taxRate: Steuersatz
            unity: Einheit

        Returns:
            Part-Objekt
        """
        # Erst nach Nummer suchen
        existing = self.find_by_number(partNumber)
        if existing:
            return existing

        # Sonst neu erstellen
        return self.create(
            name=name,
            partNumber=partNumber,
            price=price,
            taxRate=taxRate,
            unity=unity
        )

    def get_status_label(self, status: int) -> str:
        """Gibt Status-Label zurueck"""
        return PART_STATUS.get(status, f'Unknown ({status})')
