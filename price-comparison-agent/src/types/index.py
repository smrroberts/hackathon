from typing import TypedDict, List

class PriceInfo(TypedDict):
    website: str
    price: float
    currency: str

class Item(TypedDict):
    name: str
    price_info: List[PriceInfo]