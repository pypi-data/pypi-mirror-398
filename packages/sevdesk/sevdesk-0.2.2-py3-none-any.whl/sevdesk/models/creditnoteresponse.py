from typing import Optional
from pydantic import BaseModel, Field

from sevdesk.converters.contact import Contact
from sevdesk.converters.addresscountry import AddressCountry
from sevdesk.converters.createuser import CreateUser
from sevdesk.converters.sevclient import SevClient
from sevdesk.converters.contactperson import ContactPerson
from sevdesk.converters.taxrule import TaxRule
from sevdesk.converters.taxset import TaxSet

class CreditNoteResponse(BaseModel):
    """creditNote model"""

    id_: Optional[str] = Field(default=None, alias="id", description="The creditNote id")
    objectName: Optional[str] = Field(default=None, description="The creditNote object name")
    create: Optional[str] = Field(default=None, description="Date of creditNote creation")
    update: Optional[str] = Field(default=None, description="Date of last creditNote update")
    creditNoteNumber: Optional[str] = Field(default=None, description="The creditNote number")
    contact: Optional[Contact] = Field(default=None, description="The contact used in the creditNote")
    creditNoteDate: Optional[str] = Field(default=None, description="The credit note date")
    status: Optional[str] = Field(default=None, description="Please have a look in <a href='#tag/CreditNote/Status-of-credit-notes'>status of credit note</a> to see what the different status codes mean")
    header: Optional[str] = Field(default=None, description="Normally consist of prefix plus the creditNote number")
    headText: Optional[str] = Field(default=None, description="Certain html tags can be used here to format your text")
    footText: Optional[str] = Field(default=None, description="Certain html tags can be used here to format your text")
    addressCountry: Optional[AddressCountry] = Field(default=None, description="Can be omitted as complete address is defined in address attribute")
    createUser: Optional[CreateUser] = Field(default=None, description="Will be filled automatically by our system and can't be changed")
    sevClient: Optional[SevClient] = Field(default=None, description="Client to which creditNote belongs. Will be filled automatically")
    deliveryDate: Optional[str] = Field(default=None, description="Timestamp. This can also be a date range if you also use the attribute deliveryDateUntil")
    smallSettlement: Optional[bool] = Field(default=None, description="Defines if the client uses the small settlement scheme. If yes, the creditNote must not contain any vat")
    contactPerson: Optional[ContactPerson] = Field(default=None, description="The user who acts as a contact person for the creditNote")
    taxRate: Optional[str] = Field(default=None, description="This is not used anymore. Use the taxRate of the individual positions instead.")
    taxRule: Optional[TaxRule] = Field(default=None, description="**Use this in sevdesk-Update 2.0 (replaces taxType / taxSet).** See [list of available VAT rules](#section/sevdesk-Update-2.0/Tax-Rules).")
    taxSet: Optional[TaxSet] = Field(default=None, description="**Use this in sevdesk-Update 1.0 (instead of taxRule).** Tax set of the creditNote. Needs to be added if you chose the tax type custom")
    taxText: Optional[str] = Field(default=None, description="A common tax text would be 'Umsatzsteuer 19%'")
    taxType: Optional[str] = Field(default=None, description="**Use this in sevdesk-Update 1.0 (instead of taxRule).** Tax type of the creditNote. There are four tax types: 1. default - Umsatzsteuer ausweisen 2. eu - Steuerfreie innergemeinschaftliche Lieferung (Europäische Union) 3. noteu - Steuerschuldnerschaft des Leistungsempfängers (außerhalb EU, z. B. Schweiz) 4. custom - Using custom tax set 5. ss - Not subject to VAT according to §19 1 UStG Tax rates are heavily connected to the tax type used.")
    sendDate: Optional[str] = Field(default=None, description="The date the creditNote was sent to the customer")
    address: Optional[str] = Field(default=None, description="Complete address of the recipient including name, street, city, zip and country.<br> Line breaks can be used and will be displayed on the invoice pdf.")
    currency: Optional[str] = Field(default=None, description="Currency used in the creditNote. Needs to be currency code according to ISO-4217")
    sumNet: Optional[str] = Field(default=None, description="Net sum of the creditNote")
    sumTax: Optional[str] = Field(default=None, description="Tax sum of the creditNote")
    sumGross: Optional[str] = Field(default=None, description="Gross sum of the creditNote")
    sumDiscounts: Optional[str] = Field(default=None, description="Sum of all discounts in the creditNote")
    sumNetForeignCurrency: Optional[str] = Field(default=None, description="Net sum of the creditNote in the foreign currency")
    sumTaxForeignCurrency: Optional[str] = Field(default=None, description="Tax sum of the creditNote in the foreign currency")
    sumGrossForeignCurrency: Optional[str] = Field(default=None, description="Gross sum of the creditNote in the foreign currency")
    sumDiscountsForeignCurrency: Optional[str] = Field(default=None, description="Discounts sum of the creditNote in the foreign currency")
    customerInternalNote: Optional[str] = Field(default=None, description="Internal note of the customer. Contains data entered into field 'Referenz/Bestellnummer'")
    showNet: Optional[bool] = Field(default=None, description="If true, the net amount of each position will be shown on the creditNote. Otherwise gross amount")
    sendType: Optional[str] = Field(default=None, description="Type which was used to send the creditNote. IMPORTANT: Please refer to the creditNote section of the * API-Overview to understand how this attribute can be used before using it!")
    class Config:
        populate_by_name = True