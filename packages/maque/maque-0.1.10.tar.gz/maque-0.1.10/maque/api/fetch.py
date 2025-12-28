import aiohttp
import asyncio


async def fetch(session, url, data, method):
    if method == "POST":
        async with session.post(url, json=data) as response:
            return await response.text()
    elif method == "GET":
        async with session.get(url, params=data) as response:
            return await response.text()
    else:
        raise ValueError("Invalid method specified")

async def run(url, data: dict, method: str = "POST", concurrent: int = 10):
    if method not in ["POST", "GET"]:
        raise ValueError("Method should be either 'POST' or 'GET'")

    tasks = []
    async with aiohttp.ClientSession() as session:
        for _ in range(concurrent):
            task = asyncio.create_task(fetch(session, url, data, method))
            tasks.append(task)
        responses = await asyncio.gather(*tasks)
        for response in responses:
            print(response)
