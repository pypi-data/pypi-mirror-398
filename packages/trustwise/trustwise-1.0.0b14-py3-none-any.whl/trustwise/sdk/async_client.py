import logging

import aiohttp

from trustwise.sdk.config import TrustwiseConfig

logger = logging.getLogger(__name__)

class TrustwiseAsyncClient:
    def __init__(self, config: TrustwiseConfig) -> None:
        self.config = config
        self.headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        }

    async def post(self, endpoint: str, data: dict) -> dict:
        logger.debug(f"Making async POST request to {endpoint}")
        logger.debug("Request headers: {k: '***' if k == 'Authorization' else v for k, v in self.headers.items()}")
        logger.debug(f"Request data: {data}")
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, json=data, headers=self.headers, timeout=30) as response:
                logger.debug(f"Response status: {response.status}")
                if response.status != 200:
                    text = await response.text()
                    logger.error(f"API request failed: {response.status} {text}")
                    raise Exception(f"API request failed: {response.status} {text}")
                return await response.json() 