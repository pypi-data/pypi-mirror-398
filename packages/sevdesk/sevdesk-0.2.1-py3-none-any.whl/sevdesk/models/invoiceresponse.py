from typing import Optional
from pydantic import BaseModel, Field

from sevdesk.converters.contact import Contact
from sevdesk.converters.sevclient import SevClient
from sevdesk.converters.addresscountry import AddressCountry
from sevdesk.converters.createuser import CreateUser
from sevdesk.converters.contactperson import ContactPerson
from sevdesk.converters.taxrule import TaxRule
from sevdesk.converters.paymentmethod import PaymentMethod
from sevdesk.converters.costcentre import CostCentre
from sevdesk.converters.origin import Origin
from sevdesk.converters.taxset import TaxSet

class InvoiceResponse(BaseModel):
    """Invoice model"""

    id_: Optional[str] = Field(default=None, alias="id", description="The invoice id")
    objectName: Optional[str] = Field(default=None, description="The invoice object name")
    invoiceNumber: Optional[str] = Field(default=None, description="The invoice number")
    contact: Optional[Contact] = Field(default=None, description="The contact used in the invoice")
    create: Optional[str] = Field(default=None, description="Date of invoice creation")
    update: Optional[str] = Field(default=None, description="Date of last invoice update")
    sevClient: Optional[SevClient] = Field(default=None, description="Client to which invoice belongs. Will be filled automatically")
    invoiceDate: Optional[str] = Field(default=None, description="The invoice date.")
    header: Optional[str] = Field(default=None, description="Normally consist of prefix plus the invoice number")
    headText: Optional[str] = Field(default=None, description="Certain html tags can be used here to format your text")
    footText: Optional[str] = Field(default=None, description="Certain html tags can be used here to format your text")
    timeToPay: Optional[str] = Field(default=None, description="The time the customer has to pay the invoice in days")
    discountTime: Optional[str] = Field(default=None, description="If a value other than zero is used for the discount attribute, you need to specify the amount of days for which the discount is granted.")
    discount: Optional[str] = Field(default=None, description="If you want to give a discount, define the percentage here. Otherwise provide zero as value")
    addressCountry: Optional[AddressCountry] = Field(default=None, description="Can be omitted as complete address is defined in address attribute")
    payDate: Optional[str] = Field(default=None, description="Needs to be timestamp or dd.mm.yyyy")
    createUser: Optional[CreateUser] = Field(default=None, description="Will be filled automatically by our system and can't be changed")
    deliveryDate: Optional[str] = Field(default=None, description="Timestamp. This can also be a date range if you also use the attribute deliveryDateUntil")
    status: Optional[str] = Field(default=None, description="Please have a look in our <a href='#tag/Invoice/Types-and-status-of-invoices'>Types and status of invoices</a> to see what the different status codes mean")
    smallSettlement: Optional[bool] = Field(default=None, description="Defines if the client uses the small settlement scheme. If yes, the invoice must not contain any vat")
    contactPerson: Optional[ContactPerson] = Field(default=None, description="The user who acts as a contact person for the invoice")
    taxRate: Optional[str] = Field(default=None, description="This is not used anymore. Use the taxRate of the individual positions instead.")
    taxRule: Optional[TaxRule] = Field(default=None, description="**Use this in sevdesk-Update 2.0 (replaces taxType / taxSet).** See [list of available VAT rules](#section/sevdesk-Update-2.0/Tax-Rules).")
    taxText: Optional[str] = Field(default=None, description="A common tax text would be 'Umsatzsteuer 19%'")
    dunningLevel: Optional[str] = Field(default=None, description="Defines how many reminders have already been sent for the invoice. Starts with 1 (Payment reminder) and should be incremented by one every time another reminder is sent.")
    taxType: Optional[str] = Field(default=None, description="**Use this in sevdesk-Update 1.0 (instead of taxRule).** Tax type of the invoice. There are four tax types: 1. default - Umsatzsteuer ausweisen 2. eu - Steuerfreie innergemeinschaftliche Lieferung (Europäische Union) 3. noteu - Steuerschuldnerschaft des Leistungsempfängers (außerhalb EU, z. B. Schweiz) 4. custom - Using custom tax set 5. ss - Not subject to VAT according to §19 1 UStG Tax rates are heavily connected to the tax type used.")
    paymentMethod: Optional[PaymentMethod] = Field(default=None, description="Payment method used for the invoice")
    costCentre: Optional[CostCentre] = Field(default=None, description="Cost centre for the invoice")
    sendDate: Optional[str] = Field(default=None, description="The date the invoice was sent to the customer")
    origin: Optional[Origin] = Field(default=None, description="Origin of the invoice. Could f.e. be an order")
    invoiceType: Optional[str] = Field(default=None, description="Type of the invoice. For more information on the different types, check <a href='#tag/Invoice/Types-and-status-of-invoices'>this</a> section")
    accountIntervall: Optional[str] = Field(default=None, description="The interval in which recurring invoices are due as ISO-8601 duration.<br> Necessary attribute for all recurring invoices.")
    accountNextInvoice: Optional[str] = Field(default=None, description="Timestamp when the next invoice will be generated by this recurring invoice.")
    reminderTotal: Optional[str] = Field(default=None, description="Total reminder amount")
    reminderDebit: Optional[str] = Field(default=None, description="Debit of the reminder")
    reminderDeadline: Optional[str] = Field(default=None, description="Deadline of the reminder as timestamp")
    reminderCharge: Optional[str] = Field(default=None, description="The additional reminder charge")
    taxSet: Optional[TaxSet] = Field(default=None, description="**Use this in sevdesk-Update 1.0 (instead of taxRule).** Tax set of the invoice. Needs to be added if you chose the tax type custom")
    address: Optional[str] = Field(default=None, description="Complete address of the recipient including name, street, city, zip and country. * Line breaks can be used and will be displayed on the invoice pdf.")
    currency: Optional[str] = Field(default=None, description="Currency used in the invoice. Needs to be currency code according to ISO-4217")
    sumNet: Optional[str] = Field(default=None, description="Net sum of the invoice")
    sumTax: Optional[str] = Field(default=None, description="Tax sum of the invoice")
    sumGross: Optional[str] = Field(default=None, description="Gross sum of the invoice")
    sumDiscounts: Optional[str] = Field(default=None, description="Sum of all discounts in the invoice")
    sumNetForeignCurrency: Optional[str] = Field(default=None, description="Net sum of the invoice in the foreign currency")
    sumTaxForeignCurrency: Optional[str] = Field(default=None, description="Tax sum of the invoice in the foreign currency")
    sumGrossForeignCurrency: Optional[str] = Field(default=None, description="Gross sum of the invoice in the foreign currency")
    sumDiscountsForeignCurrency: Optional[str] = Field(default=None, description="Discounts sum of the invoice in the foreign currency")
    sumNetAccounting: Optional[str] = Field(default=None, description="Net accounting sum of the invoice. Is usually the same as sumNet")
    sumTaxAccounting: Optional[str] = Field(default=None, description="Tax accounting sum of the invoice. Is usually the same as sumTax")
    sumGrossAccounting: Optional[str] = Field(default=None, description="Gross accounting sum of the invoice. Is usually the same as sumGross")
    paidAmount: Optional[float] = Field(default=None, description="Amount which has already been paid for this invoice by the customer")
    customerInternalNote: Optional[str] = Field(default=None, description="Internal note of the customer. Contains data entered into field 'Referenz/Bestellnummer'")
    showNet: Optional[bool] = Field(default=None, description="If true, the net amount of each position will be shown on the invoice. Otherwise gross amount")
    enshrined: Optional[str] = Field(default=None, description="Enshrined invoices cannot be changed. Can only be set via [Invoice/{invoiceId}/enshrine](#tag/Invoice/operation/invoiceEnshrine). This operation cannot be undone.")
    sendType: Optional[str] = Field(default=None, description="Type which was used to send the invoice. IMPORTANT: Please refer to the invoice section of the * API-Overview to understand how this attribute can be used before using it!")
    deliveryDateUntil: Optional[str] = Field(default=None, description="If the delivery date should be a time range, another timestamp can be provided in this attribute * to define a range from timestamp used in deliveryDate attribute to the timestamp used here.")
    datevConnectOnline: Optional[dict] = Field(default=None, description="Internal attribute")
    sendPaymentReceivedNotificationDate: Optional[str] = Field(default=None, description="Internal attribute")
    class Config:
        populate_by_name = True