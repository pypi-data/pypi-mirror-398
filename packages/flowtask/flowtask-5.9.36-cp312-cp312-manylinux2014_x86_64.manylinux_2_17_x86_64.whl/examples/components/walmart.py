import asyncio
from flowtask.components.Walmart import Walmart
import pandas as pd

async def get_reviews():
    data = [
        {
            "itemId": "2282978809",
            "model": "86QNED80URA",
            "brand": "LG"
        },
    ]
    df = pd.DataFrame(data)
    target = Walmart(
        type='reviews',
        use_proxies=True,
        paid_proxy=True,
        api_token="e875cce3066390dd30abdca117fb05e0a9b52d3d449b635477c9c9fe2ab6f492"
    )
    target.input = df
    async with target as comp:
        try:
            result = await comp.run()
            print(len(result), type(result))
            print('RESULT >> ')
            print(result)
        except Exception as e:
            print(f'Error: {e}')

if __name__ == '__main__':
    asyncio.run(get_reviews())
