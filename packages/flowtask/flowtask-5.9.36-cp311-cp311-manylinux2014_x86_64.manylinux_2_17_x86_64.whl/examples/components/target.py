import asyncio
from flowtask.components.Target import Target
import pandas as pd

async def get_reviews():
    data = [
        {"sku": "85412323", "model": "86QNED80URA", "brand": "LG"},
    ]
    df = pd.DataFrame(data)
    target = Target(
        type='reviews',
        use_proxies=True,
        paid_proxy=True,
        api_token="c6b68aaef0eac4df4931aae70500b7056531cb37"
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
