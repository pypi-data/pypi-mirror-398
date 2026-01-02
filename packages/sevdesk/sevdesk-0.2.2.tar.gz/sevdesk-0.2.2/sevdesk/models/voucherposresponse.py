from typing import Optional
from pydantic import BaseModel, Field

from sevdesk.converters.sevclient import SevClient
from sevdesk.converters.voucher import Voucher
from sevdesk.converters.accountdatev import AccountDatev
from sevdesk.converters.accountingtype import AccountingType
from sevdesk.converters.estimatedaccountingtype import EstimatedAccountingType

class VoucherPosResponse(BaseModel):
    """Voucher position model"""

    id_: Optional[str] = Field(default=None, alias="id", description="The voucher position id")
    objectName: Optional[str] = Field(default=None, description="The voucher position object name")
    create: Optional[str] = Field(default=None, description="Date of voucher position creation")
    update: Optional[str] = Field(default=None, description="Date of last voucher position update")
    sevClient: Optional[SevClient] = Field(default=None, description="Client to which voucher position belongs. Will be filled automatically")
    voucher: Voucher = Field(description="The voucher to which the position belongs.")
    accountDatev: AccountDatev = Field(description="<b>Use this in sevdesk-Update 2.0 (replaces accountingType).</b> The account datev to which the position belongs.<br> An account datev is the booking account to which the position belongs.<br> For more information, please refer to <a href='#tag/Voucher/Account-Datev'>this</a> section.")
    accountingType: AccountingType = Field(description="The accounting type to which the position belongs.<br> An accounting type is the booking account to which the position belongs.<br> For more information, please refer to <a href='#tag/Voucher/Accounting-type'>this</a> section.")
    estimatedAccountingType: Optional[EstimatedAccountingType] = Field(default=None, description="The accounting type to which the position belongs estimated by our voucher recognition.<br> An accounting type is the booking account to which the position belongs.<br> For more information, please refer to <a href='#tag/Voucher/Accounting-type'>this</a> section.")
    taxRate: str = Field(description="Tax rate of the voucher position.")
    net: bool = Field(description="Determines whether 'sumNet' or 'sumGross' is regarded.<br> If both are not given, 'sum' is regarded and treated as net or gross depending on 'net'. All positions must be either net or gross, a mixture of the two is not possible.")
    isAsset: Optional[bool] = Field(default=None, description="Determines whether position is regarded as an asset which can be depreciated.")
    sumNet: str = Field(description="Net sum of the voucher position.<br> Only regarded if 'net' is 'true', otherwise its readOnly.")
    sumTax: Optional[str] = Field(default=None, description="Tax sum of the voucher position.")
    sumGross: str = Field(description="Gross sum of the voucher position.<br> Only regarded if 'net' is 'false', otherwise its readOnly.")
    sumNetAccounting: Optional[str] = Field(default=None, description="Net accounting sum. Is equal to sumNet.")
    sumTaxAccounting: Optional[str] = Field(default=None, description="Tax accounting sum. Is equal to sumTax.")
    sumGrossAccounting: Optional[str] = Field(default=None, description="Gross accounting sum. Is equal to sumGross.")
    comment: Optional[str] = Field(default=None, description="Comment for the voucher position.")
    class Config:
        populate_by_name = True