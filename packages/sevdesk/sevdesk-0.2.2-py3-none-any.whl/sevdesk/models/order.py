from typing import Optional
from pydantic import BaseModel, Field

from sevdesk.converters.contact import Contact
from sevdesk.converters.addresscountry import AddressCountry
from sevdesk.converters.contactperson import ContactPerson
from sevdesk.converters.taxrule import TaxRule
from sevdesk.converters.taxset import TaxSet
from sevdesk.converters.origin import Origin

class Order(BaseModel):
    """Order model"""

    id_: Optional[int] = Field(default=None, alias="id", description="The order id")
    objectName: Optional[str] = Field(default=None, description="The order object name")
    mapAll: bool
    create: Optional[str] = Field(default=None, description="Date of order creation")
    update: Optional[str] = Field(default=None, description="Date of last order update")
    orderNumber: str = Field(description="The order number")
    contact: Contact = Field(description="The contact used in the order")
    orderDate: str = Field(description="Needs to be provided as timestamp or dd.mm.yyyy")
    status: int = Field(description="Please have a look in <a href='#tag/Order/Types-and-status-of-orders'>status of orders</a> to see what the different status codes mean")
    header: str = Field(description="Normally consist of prefix plus the order number")
    headText: Optional[str] = Field(default=None, description="Certain html tags can be used here to format your text")
    footText: Optional[str] = Field(default=None, description="Certain html tags can be used here to format your text")
    addressCountry: AddressCountry = Field(description="Can be omitted as complete address is defined in address attribute")
    deliveryTerms: Optional[str] = Field(default=None, description="Delivery terms of the order")
    paymentTerms: Optional[str] = Field(default=None, description="Payment terms of the order")
    version: int = Field(description="Version of the order.<br> Can be used if you have multiple drafts for the same order.<br> Should start with 0")
    smallSettlement: Optional[bool] = Field(default=None, description="Defines if the client uses the small settlement scheme. If yes, the order must not contain any vat")
    contactPerson: ContactPerson = Field(description="The user who acts as a contact person for the order")
    taxRate: float = Field(description="This is not used anymore. Use the taxRate of the individual positions instead.")
    taxRule: TaxRule = Field(description="**Use this in sevdesk-Update 2.0 (replaces taxType / taxSet).** See [list of available VAT rules](#section/sevdesk-Update-2.0/Tax-Rules).")
    taxSet: Optional[TaxSet] = Field(default=None, description="**Use this in sevdesk-Update 1.0 (instead of taxRule).** Tax set of the order. Needs to be added if you chose the tax type custom")
    taxText: str = Field(description="A common tax text would be 'Umsatzsteuer 19%'")
    taxType: str = Field(description="**Use this in sevdesk-Update 1.0 (instead of taxRule).** Tax type of the order. There are four tax types: 1. default - Umsatzsteuer ausweisen 2. eu - Steuerfreie innergemeinschaftliche Lieferung (Europäische Union) 3. noteu - Steuerschuldnerschaft des Leistungsempfängers (außerhalb EU, z. B. Schweiz) 4. custom - Using custom tax set 5. ss - Not subject to VAT according to §19 1 UStG Tax rates are heavily connected to the tax type used.")
    orderType: Optional[str] = Field(default=None, description="Type of the order. For more information on the different types, check <a href='#tag/Order/Types-and-status-of-orders'>this</a>")
    sendDate: Optional[str] = Field(default=None, description="The date the order was sent to the customer")
    address: Optional[str] = Field(default=None, description="Complete address of the recipient including name, street, city, zip and country.<br> Line breaks can be used and will be displayed on the invoice pdf.")
    currency: str = Field(description="Currency used in the order. Needs to be currency code according to ISO-4217")
    customerInternalNote: Optional[str] = Field(default=None, description="Internal note of the customer. Contains data entered into field 'Referenz/Bestellnummer'")
    showNet: Optional[bool] = Field(default=None, description="If true, the net amount of each position will be shown on the order. Otherwise gross amount")
    sendType: Optional[str] = Field(default=None, description="Type which was used to send the order. IMPORTANT: Please refer to the order section of the * API-Overview to understand how this attribute can be used before using it!")
    origin: Optional[Origin] = Field(default=None, description="Object from which the order was created. For example an offer.")
    class Config:
        populate_by_name = True