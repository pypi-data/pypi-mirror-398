import asyncio
from kaspi_offers_py import KaspiClient


async def main():
    client = KaspiClient()

    # Get offers for a product
    response = await client.get_offers("123728177")

    print(f"Found {response.total} offers")

    # Iterate through offers
    for offer in response.offers:
        print(f"{offer.merchantName}: {offer.price} ₸")
        print(f"Rating: {offer.merchantRating} ({offer.merchantReviewsQuantity} reviews)")
        print(f"Delivery: {offer.deliveryType}")
        print("---")


asyncio.run(main())