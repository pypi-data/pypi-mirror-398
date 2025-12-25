"""
ContactHelper - High-Level Kontakt-Verwaltung

Beispiele:
    contact = sevdesk.contactHelper.find_by_mail('max@example.com')
    contact = sevdesk.contactHelper.find_by_customfield('revitoid', '1234567890')
    contact = sevdesk.contactHelper.create(name='Test Firma', email='test@example.com')
"""


class ContactHelper:
    """Helper-Klasse für Kontakt-Operationen auf hohem Level"""
    
    def __init__(self, client):
        self.client = client
    
    def find_by_mail(self, email: str):
        """
        Sucht einen Kontakt nach E-Mail-Adresse.
        
        Args:
            email: E-Mail-Adresse des Kontakts
            
        Returns:
            ContactResponse oder None wenn nicht gefunden
        """
        contacts = self.client.contact.getContacts()
        
        for contact_obj in contacts:
            contact_id = getattr(contact_obj, 'id_', getattr(contact_obj, 'id', None))
            
            if not contact_id:
                continue
            
            # Kommunikationswege abrufen
            try:
                comm_response = self.client.communicationway.getCommunicationWays(
                    contact_id=str(contact_id),
                    contact_objectName="Contact"
                )
                
                # Kommunikationswege durchsuchen
                if isinstance(comm_response, list):
                    comm_list = comm_response
                else:
                    comm_list = []
                
                # Set für Duplikat-Vermeidung
                found_emails = set()
                
                for comm_way in comm_list:
                    if isinstance(comm_way, dict):
                        comm_type = comm_way.get('type')
                        comm_value = comm_way.get('value')
                    else:
                        comm_type = getattr(comm_way, 'type_', None)
                        comm_value = getattr(comm_way, 'value', None)
                    
                    if comm_type == "EMAIL" and comm_value:
                        comm_value_lower = comm_value.lower()
                        if comm_value_lower not in found_emails:
                            found_emails.add(comm_value_lower)
                            
                            if comm_value_lower == email.lower():
                                return contact_obj
            except Exception:
                continue
        
        return None
    
    def find_by_customfield(self, field: str, value: str):
        """
        Sucht einen Kontakt nach Custom Field.
        
        Args:
            field: Name des Custom Fields (z.B. 'revitoid')
            value: Wert des Fields
            
        Returns:
            ContactResponse oder None wenn nicht gefunden
        """
        try:
            # Verwende die findContactsByCustomFieldValue Methode
            results = self.client.contact.findContactsByCustomFieldValue(
                customFieldName=field,
                value=value
            )
            
            if results and len(results) > 0:
                return results[0]
            
            return None
        except Exception:
            return None
    
    def create(self, name: str, email: str = None, surname: str = "", category_id: int = 3):
        """
        Erstellt einen neuen Kontakt.
        
        Args:
            name: Firmenname oder Vorname
            email: E-Mail-Adresse (optional)
            surname: Nachname (optional, für Personen)
            category_id: Kategorie-ID (3=Kunde, 1=Lieferant, etc.)
            
        Returns:
            ContactResponse mit der neuen Kontakt-ID
        """
        from sevdesk.models.contact import Contact as ContactModel
        from sevdesk.models.communicationway import CommunicationWay
        from sevdesk.converters.category import Category
        from sevdesk.converters.contact import Contact
        from sevdesk.converters.key import Key
        
        # Kontakt erstellen
        new_contact = ContactModel(
            name=name,
            surename=surname if surname else name,
            familyname=name if surname else "",
            category=Category(id_=category_id, objectName="Category"),
            mapAll=True
        )
        
        result = self.client.contact.createContact(body=new_contact)
        
        # ID extrahieren
        if isinstance(result, list) and len(result) > 0:
            new_contact_id = int(result[0].id_)
        else:
            new_contact_id = int(result.id_) if hasattr(result, 'id_') else int(result.id)
        
        # E-Mail hinzufügen wenn vorhanden
        if email:
            try:
                comm_way = CommunicationWay(
                    contact=Contact(id_=new_contact_id, objectName="Contact"),
                    type_="EMAIL",
                    value=email,
                    key=Key(id_=1, objectName="CommunicationWayKey"),
                    main=True
                )
                self.client.communicationway.createCommunicationWay(body=comm_way)
            except Exception:
                pass  # Email-Fehler sollten nicht den Kontakt ungültig machen
        
        # Neuen Kontakt abrufen und zurückgeben
        return self.get_by_id(new_contact_id)
    
    def get_by_id(self, contact_id: int):
        """
        Ruft einen Kontakt per ID ab.
        
        Args:
            contact_id: ID des Kontakts
            
        Returns:
            ContactResponse
        """
        result = self.client.contact.getContactById(contact_id)
        if isinstance(result, list) and len(result) > 0:
            return result[0]
        return result
