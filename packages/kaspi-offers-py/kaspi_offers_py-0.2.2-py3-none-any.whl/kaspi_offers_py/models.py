from dataclasses import dataclass
from typing import List, Optional, Dict
from datetime import datetime


@dataclass
class Offer:
    masterSku: str
    merchantId: str
    merchantName: str
    merchantSku: str
    title: str
    price: float
    merchantRating: float
    merchantReviewsQuantity: int
    deliveryDuration: Optional[str]
    kaspiDelivery: bool
    preorder: int
    deliveryType: Optional[str] = None
    delivery: Optional[str] = None
    pickup: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict) -> 'Offer':
        return cls(
            masterSku=data['masterSku'],
            merchantId=data['merchantId'],
            merchantName=data['merchantName'],
            merchantSku=data['merchantSku'],
            title=data['title'],
            price=data['price'],
            merchantRating=data['merchantRating'],
            merchantReviewsQuantity=data['merchantReviewsQuantity'],
            deliveryType=data.get('deliveryType'),
            deliveryDuration=data.get('deliveryDuration'),
            kaspiDelivery=data['kaspiDelivery'],
            preorder=data['preorder'],
            delivery=data.get('delivery'),
            pickup=data.get('pickup'),
        )


@dataclass
class OffersResponse:
    offers: List[Offer]
    total: int
    offersCount: int

    @classmethod
    def from_dict(cls, data: Dict) -> 'OffersResponse':
        return cls(
            offers=[Offer.from_dict(o) for o in data['offers']],
            total=data['total'],
            offersCount=data['offersCount']
        )
