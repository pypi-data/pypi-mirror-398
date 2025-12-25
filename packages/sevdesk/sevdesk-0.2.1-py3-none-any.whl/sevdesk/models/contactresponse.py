from typing import Optional
from pydantic import BaseModel, Field

from sevdesk.converters.parent import Parent
from sevdesk.converters.category import Category
from sevdesk.converters.sevclient import SevClient

class ContactResponse(BaseModel):
    """Contact model"""

    id_: Optional[str] = Field(default=None, alias="id", description="The contact id")
    objectName: Optional[str] = Field(default=None, description="The contact object name")
    create: Optional[str] = Field(default=None, description="Date of contact creation")
    update: Optional[str] = Field(default=None, description="Date of last contact update")
    name: Optional[str] = Field(default=None, description="The organization name.<br> Be aware that the type of contact will depend on this attribute.<br> If it holds a value, the contact will be regarded as an organization.")
    status: Optional[str] = Field(default=None, description="Defines the status of the contact. 100 <-> Lead - 500 <-> Pending - 1000 <-> Active.")
    customerNumber: Optional[str] = Field(default=None, description="The customer number")
    parent: Optional[Parent] = Field(default=None, description="The parent contact to which this contact belongs. Must be an organization.")
    surename: Optional[str] = Field(default=None, description="The <b>first</b> name of the contact.<br> Yeah... not quite right in literally every way. We know.<br> Not to be used for organizations.")
    familyname: Optional[str] = Field(default=None, description="The last name of the contact.<br> Not to be used for organizations.")
    titel: Optional[str] = Field(default=None, description="A non-academic title for the contact. Not to be used for organizations.")
    category: Optional[Category] = Field(default=None, description="Category of the contact.<br> For more information, see <a href='https://my.sevdesk.de/apiOverview/index.html#/doc-contacts#types'>here</a>.")
    description: Optional[str] = Field(default=None, description="A description for the contact.")
    academicTitle: Optional[str] = Field(default=None, description="A academic title for the contact. Not to be used for organizations.")
    gender: Optional[str] = Field(default=None, description="Gender of the contact.<br> Not to be used for organizations.")
    sevClient: Optional[SevClient] = Field(default=None, description="Client to which contact belongs. Will be filled automatically")
    name2: Optional[str] = Field(default=None, description="Second name of the contact.<br> Not to be used for organizations.")
    birthday: Optional[str] = Field(default=None, description="Birthday of the contact.<br> Not to be used for organizations.")
    vatNumber: Optional[str] = Field(default=None, description="Vat number of the contact.")
    bankAccount: Optional[str] = Field(default=None, description="Bank account number (IBAN) of the contact.")
    bankNumber: Optional[str] = Field(default=None, description="Bank number of the bank used by the contact.")
    defaultCashbackTime: Optional[str] = Field(default=None, description="Absolute time in days which the contact has to pay his invoices and subsequently get a cashback.")
    defaultCashbackPercent: Optional[str] = Field(default=None, description="Percentage of the invoice sum the contact gets back if he paid invoices in time.")
    defaultTimeToPay: Optional[str] = Field(default=None, description="The payment goal in days which is set for every invoice of the contact.")
    taxNumber: Optional[str] = Field(default=None, description="The tax number of the contact.")
    taxOffice: Optional[str] = Field(default=None, description="The tax office of the contact (only for greek customers).")
    exemptVat: Optional[str] = Field(default=None, description="Defines if the contact is freed from paying vat.")
    defaultDiscountAmount: Optional[str] = Field(default=None, description="The default discount the contact gets for every invoice.<br> Depending on defaultDiscountPercentage attribute, in percent or absolute value.")
    defaultDiscountPercentage: Optional[str] = Field(default=None, description="Defines if the discount is a percentage (true) or an absolute value (false).")
    buyerReference: Optional[str] = Field(default=None, description="Buyer reference of the contact.")
    governmentAgency: Optional[str] = Field(default=None, description="Defines whether the contact is a government agency (true) or not (false).")
    additionalInformation: Optional[str] = Field(default=None, description="Additional information stored for the contact.")
    class Config:
        populate_by_name = True