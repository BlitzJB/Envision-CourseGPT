from .utils.protocol import GenerationClient
from .utils.event import Event
import asyncio, aiohttp, json, time, openai, typing

class OpenAIGPT(GenerationClient):
    def __init__(self):
        self.last_request_time = None
        self.request_interval = 20  # 60 seconds / 3 requests

    async def wait_for_rate_limit(self):
        if self.last_request_time is not None:
            elapsed_time = time.time() - self.last_request_time
            if elapsed_time < self.request_interval:
                print("sleeping for", self.request_interval - elapsed_time)
                await asyncio.sleep(self.request_interval - elapsed_time)

        self.last_request_time = time.time()

    async def create(self, messages: list[dict], stream: bool = False, **kwargs) -> typing.AsyncGenerator[str, None]:
        # await self.wait_for_rate_limit()

        if stream:
            return await self.async_make_generator(messages)
        else:
            return await self.async_get_full_response(messages)
        
    async def async_make_generator(self, messages: list[dict]):
        async with aiohttp.ClientSession() as session:
            async with session.post("https://api.openai.com/v1/chat/completions", json={
                "messages": messages,
                "model": "gpt-3.5-turbo",
                "stream": True
            }, headers={"Authorization": f"Bearer {openai.api_key}"}) as response:
                if response.status == 429:
                    await asyncio.sleep(20)
                else:
                    async for line in response.content:
                        line = line.decode('utf-8')
                        event = Event.parse(line)
                        if line == "\n":
                            continue
                        if event.data == '[DONE]':
                            continue
                        json_ = json.loads(event.data)
                        yield json_['choices'][0]["delta"].get("content", "")
                    
    async def async_get_full_response(self, messages: list[dict]):
        response_data = ''
        async for chunk in self.async_make_generator(messages):
            response_data += chunk
        return response_data