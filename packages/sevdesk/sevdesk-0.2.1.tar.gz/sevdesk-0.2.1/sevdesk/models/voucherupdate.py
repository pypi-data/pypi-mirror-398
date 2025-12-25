from typing import Optional
from pydantic import BaseModel, Field

from sevdesk.converters.supplier import Supplier
from sevdesk.converters.taxrule import TaxRule
from sevdesk.converters.taxset import TaxSet
from sevdesk.converters.document import Document
from sevdesk.converters.costcentre import CostCentre

class VoucherUpdate(BaseModel):
    """Voucher model"""

    voucherDate: Optional[str] = Field(default=None, description="Needs to be provided as timestamp or dd.mm.yyyy")
    supplier: Optional[Supplier] = Field(default=None, description="The contact used in the voucher as a supplier.<br> If you don't have a contact as a supplier, you can set this object to null.")
    supplierName: Optional[str] = Field(default=None, description="The supplier name.<br> The value you provide here will determine what supplier name is shown for the voucher in case you did not provide a supplier.")
    description: Optional[str] = Field(default=None, description="The description of the voucher. Essentially the voucher number.")
    payDate: Optional[str] = Field(default=None, description="Needs to be timestamp or dd.mm.yyyy")
    status: Optional[float] = Field(default=None, description="<b>Not supported in sevdesk-Update 2.0.</b><br><br> Please have a look in <a href='#tag/Voucher/Types-and-status-of-vouchers'>status of vouchers</a> to see what the different status codes mean")
    paidAmount: Optional[float] = Field(default=None, description="Amount which has already been paid for this voucher by the customer")
    taxRule: Optional[TaxRule] = Field(default=None, description="**Use this in sevdesk-Update 2.0 (replaces taxType / taxSet).**")
    taxType: Optional[str] = Field(default=None, description="**Use this in sevdesk-Update 1.0 (instead of taxRule).** Tax type of the voucher. There are four tax types: 1. default - Umsatzsteuer ausweisen 2. eu - Steuerfreie innergemeinschaftliche Lieferung (Europäische Union) 3. noteu - Steuerschuldnerschaft des Leistungsempfängers (außerhalb EU, z. B. Schweiz) 4. custom - Using custom tax set 5. ss - Not subject to VAT according to §19 1 UStG Tax rates are heavily connected to the tax type used.")
    creditDebit: Optional[str] = Field(default=None, description="Defines if your voucher is a credit (C) or debit (D)")
    voucherType: Optional[str] = Field(default=None, description="Type of the voucher. For more information on the different types, check <a href='#tag/Voucher/Types-and-status-of-vouchers'>this</a>")
    currency: Optional[str] = Field(default=None, description="specifies which currency the voucher should have. Attention: If the currency differs from the default currency stored in the account, then either the 'propertyForeignCurrencyDeadline' or 'propertyExchangeRate' parameter must be specified. If both parameters are specified, then the 'propertyForeignCurrencyDeadline' parameter is preferred")
    propertyForeignCurrencyDeadline: Optional[str] = Field(default=None, description="Defines the exchange rate day and and then the exchange rate is set from sevdesk. Needs to be provided as timestamp or dd.mm.yyyy")
    propertyExchangeRate: Optional[float] = Field(default=None, description="Defines the exchange rate")
    taxSet: Optional[TaxSet] = Field(default=None, description="**Use this in sevdesk-Update 2.0 (replaces taxType / taxSet).** Tax set of the voucher. Needs to be added if you chose the taxType=custom.")
    paymentDeadline: Optional[str] = Field(default=None, description="Payment deadline of the voucher.")
    deliveryDate: Optional[str] = Field(default=None, description="Needs to be provided as timestamp or dd.mm.yyyy")
    deliveryDateUntil: Optional[str] = Field(default=None, description="Needs to be provided as timestamp or dd.mm.yyyy")
    document: Optional[Document] = Field(default=None, description="The document of the voucher.")
    costCentre: Optional[CostCentre] = Field(default=None, description="Cost centre for the voucher")
    class Config:
        populate_by_name = True