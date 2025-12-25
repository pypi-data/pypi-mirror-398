# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from typing_extensions import TypeAlias

from ...._models import BaseModel

__all__ = ["StockListResponse", "StockListResponseItem"]


class StockListResponseItem(BaseModel):
    """Information about stock available for trading."""

    id: str
    """ID of the `Stock`"""

    is_fractionable: bool
    """Whether the `Stock` allows for fractional trading.

    If it is not fractionable, Dinari only supports limit orders for the `Stock`.
    """

    is_tradable: bool
    """Whether the `Stock` is available for trading."""

    name: str
    """Company name"""

    symbol: str
    """Ticker symbol"""

    tokens: List[str]
    """List of CAIP-10 formatted token addresses."""

    cik: Optional[str] = None
    """SEC Central Index Key.

    Refer to
    [this link](https://www.sec.gov/submit-filings/filer-support-resources/how-do-i-guides/understand-utilize-edgar-ciks-passphrases-access-codes)
    for more information.
    """

    composite_figi: Optional[str] = None
    """Composite FIGI ID.

    Refer to [this link](https://www.openfigi.com/about/figi) for more information.
    """

    cusip: Optional[str] = None
    """CUSIP ID.

    Refer to [this link](https://www.cusip.com/identifiers.html) for more
    information. A license agreement with CUSIP Global Services is required to
    receive this value.
    """

    description: Optional[str] = None
    """Description of the company and their services."""

    display_name: Optional[str] = None
    """Name of `Stock` for application display.

    If defined, this supercedes the `name` field for displaying the name.
    """

    logo_url: Optional[str] = None
    """URL of the company's logo. Supported formats are SVG and PNG."""


StockListResponse: TypeAlias = List[StockListResponseItem]
