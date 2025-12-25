# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime
from typing_extensions import TypeAlias

from ...._models import BaseModel

__all__ = ["StockRetrieveNewsResponse", "StockRetrieveNewsResponseItem"]


class StockRetrieveNewsResponseItem(BaseModel):
    """
    A news article relating to a `Stock` which includes a summary of the article and a link to the original source.
    """

    article_url: str
    """URL of the news article"""

    description: str
    """Description of the news article"""

    image_url: str
    """URL of the image for the news article"""

    published_dt: datetime
    """Datetime when the article was published. ISO 8601 timestamp."""

    publisher: str
    """The publisher of the news article"""

    amp_url: Optional[str] = None
    """
    Mobile-friendly Accelerated Mobile Page (AMP) URL of the news article, if
    available
    """


StockRetrieveNewsResponse: TypeAlias = List[StockRetrieveNewsResponseItem]
