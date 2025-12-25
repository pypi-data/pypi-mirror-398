"""
LetterHelper - High-Level Brief-Verwaltung

Beispiele:
    letter = sevdesk.letterHelper.new(
        contact=contact,
        header='Betreff des Briefes',
        text='<p>Inhalt des Briefes</p>'
    )
    letter.save()
    letter.render()
    pdf = letter.getPDF()
"""

import time
from datetime import datetime
from typing import Optional
from sevdesk.undocumented.models.letter import Letter
from sevdesk.converters.contact import Contact
from sevdesk.converters.contactperson import ContactPerson


class LetterExt:
    """
    Erweiterte Brief-Klasse mit High-Level Funktionen.

    Beispiel:
        letter = LetterExt(...)
        letter.save()
        letter.render()
        pdf = letter.getPDF()
    """

    def __init__(self, client, contact, header: str, text: str,
                 address: str = None, contactPerson_id: int = None,
                 contactPerson_name: str = "SevUser", status: str = "100",
                 letterDate: str = None):
        self._client = client
        self._saved_id = None

        # Contact normalisieren
        if isinstance(contact, int):
            self._contact = Contact(id_=contact, objectName="Contact")
        elif hasattr(contact, 'id_'):
            self._contact = Contact(id_=contact.id_, objectName="Contact")
        else:
            self._contact = contact

        self._header = header
        self._text = text
        self._address = address
        self._status = status

        # Datum: Unix-Timestamp oder heute
        if letterDate:
            self._letterDate = letterDate
        else:
            self._letterDate = str(int(datetime.now().timestamp()))

        # ContactPerson (SevUser)
        if contactPerson_id:
            self._contactPerson = ContactPerson(id_=contactPerson_id, objectName=contactPerson_name)
        else:
            self._contactPerson = None

    def _get_default_contact_person(self) -> ContactPerson:
        """Holt den ersten verfuegbaren SevUser als ContactPerson"""
        try:
            users = self._client.undocumented.sevuser.getSevUsers(limit=1)
            if users and len(users) > 0:
                user = users[0]
                user_id = user.get('id') or user.get('id_')
                if user_id:
                    return ContactPerson(id_=int(user_id), objectName="SevUser")
        except Exception:
            pass
        raise RuntimeError(
            "Kein SevUser gefunden. Bitte contactPerson_id explizit angeben."
        )

    def save(self) -> 'LetterExt':
        """
        Speichert den Brief auf sevDesk.

        Returns:
            self mit gesetzter ID (fuer Method-Chaining)
        """
        if not self._client:
            raise RuntimeError("Client nicht gesetzt")

        # ContactPerson ist required - fallback auf ersten User
        if not self._contactPerson:
            self._contactPerson = self._get_default_contact_person()

        letter = Letter(
            contact=self._contact,
            letterDate=self._letterDate,
            header=self._header,
            status=self._status,
            contactPerson=self._contactPerson,
            text=self._text,
            address=self._address,
        )

        result = self._client.undocumented.letter.createLetter(body=letter)

        if hasattr(result, 'id_'):
            self._saved_id = int(result.id_)
        elif isinstance(result, dict):
            self._saved_id = int(result.get('id') or result.get('id_'))

        if not self._saved_id:
            raise RuntimeError("Konnte Letter-ID nicht aus Response extrahieren")

        return self

    def render(self, forceReload: bool = False) -> 'LetterExt':
        """
        Rendert den Brief als PDF.

        Returns:
            self (fuer Method-Chaining)
        """
        if not self._saved_id:
            raise RuntimeError("Brief muss zuerst gespeichert werden (save())")

        self._client.undocumented.letter.letterRender(
            letterId=self._saved_id,
            forceReload=forceReload,
            getAsPdf=True
        )
        return self

    def getPDF(self, download: bool = True) -> Optional[bytes]:
        """
        Laedt die PDF des Briefes herunter.

        Args:
            download: Ob die Datei heruntergeladen werden soll

        Returns:
            PDF-Inhalt (bytes)
        """
        if not self._saved_id:
            raise RuntimeError("Brief muss zuerst gespeichert werden (save())")

        pdf_content = self._client.undocumented.letter.letterGetPdf(
            letterId=self._saved_id,
            download=download
        )
        return pdf_content

    def setParameter(self, key: str, value: str) -> 'LetterExt':
        """
        Aendert einen Design-Parameter des Briefes.

        Args:
            key: Parameter-Name (z.B. 'logoSize', 'color')
            value: Neuer Wert

        Returns:
            self (fuer Method-Chaining)
        """
        if not self._saved_id:
            raise RuntimeError("Brief muss zuerst gespeichert werden (save())")

        self._client.undocumented.letter.changeLetterParameter(
            letterId=self._saved_id,
            key=key,
            value=value,
            getAsPdf=True
        )
        return self

    def markAsSent(self, sendType: str = "VPDF") -> 'LetterExt':
        """
        Markiert den Brief als versendet.

        Args:
            sendType: Versandart (default: VPDF)

        Returns:
            self (fuer Method-Chaining)
        """
        if not self._saved_id:
            raise RuntimeError("Brief muss zuerst gespeichert werden (save())")

        self._client.undocumented.letter.letterSendBy(
            letterId=self._saved_id,
            sendType=sendType
        )
        return self

    @property
    def id(self) -> Optional[int]:
        """Die ID des gespeicherten Briefes"""
        return self._saved_id


class LetterHelper:
    """Helper-Klasse fuer Brief-Operationen auf hohem Level"""

    def __init__(self, client):
        self.client = client

    def new(self, contact, header: str, text: str,
            address: str = None, contactPerson_id: int = None,
            contactPerson_name: str = "SevUser", status: str = "100",
            letterDate: str = None) -> LetterExt:
        """
        Erstellt einen neuen Brief (noch nicht gespeichert).

        Args:
            contact: Contact-Objekt, ContactResponse oder Contact-ID
            header: Betreff des Briefes
            text: HTML-Inhalt des Briefes
            address: Empfaengeradresse (mehrzeilig)
            contactPerson_id: SevUser-ID (optional, wird automatisch ermittelt)
            contactPerson_name: Object-Name (default: SevUser)
            status: Status ('100'=Draft)
            letterDate: Datum als Unix-Timestamp (default: heute)

        Returns:
            LetterExt-Objekt (noch nicht gespeichert)
        """
        return LetterExt(
            client=self.client,
            contact=contact,
            header=header,
            text=text,
            address=address,
            contactPerson_id=contactPerson_id,
            contactPerson_name=contactPerson_name,
            status=status,
            letterDate=letterDate,
        )

    def find_by_id(self, letter_id: int):
        """
        Ruft einen Brief per ID ab.

        Args:
            letter_id: ID des Briefes

        Returns:
            LetterResponse oder None
        """
        try:
            result = self.client.undocumented.letter.getLetterById(letterId=letter_id)
            if isinstance(result, list) and len(result) > 0:
                return result[0]
            return result
        except Exception:
            return None

    def list(self, contact_id: int = None, limit: int = 100):
        """
        Listet Briefe auf.

        Args:
            contact_id: Optional: nur fuer einen Kontakt
            limit: Max. Anzahl

        Returns:
            Liste von LetterResponse-Objekten
        """
        try:
            letters = self.client.undocumented.letter.getLetters(
                contact_id=contact_id,
                contact_objectName="Contact" if contact_id else None,
                limit=limit
            )
            return letters if letters else []
        except Exception:
            return []
