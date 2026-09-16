import asyncio
import os

import httpx


async def main() -> None:
    api_base_url = os.getenv("API_BASE_URL", "http://api:8080")
    while True:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                await client.get(f"{api_base_url}/health")
        except Exception:
            pass
        await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())
