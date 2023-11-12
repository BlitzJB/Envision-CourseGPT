from .utils.protocol import GenerationClient
import time
import requests
import asyncio
import aiohttp
from typing import Literal
from asyncio import Semaphore

# TODO: Handle exceptions

MAX_RETRIES = 3 

class LlamaChat(GenerationClient):
    semaphore = Semaphore(10)
    
    def __init__(self, version: Literal["7b", "13b", "70b"] = "13b"):
        if version == "7b":
            self.version_hash = "ac944f2e49c55c7e965fc3d93ad9a7d9d947866d6793fb849dd6b4747d0c061c"
        elif version == "13b":
            self.version_hash = "f4e2de70d66816a838a89eeeb621910adffb0dd0baba3976c96980970978018d"
        elif version == "70b":
            self.version_hash = "02e509c789964a7ea8736978a43525956ef40397be9033abf9fd2badfe68c9e3"
        pass

    def create(self, messages: list[dict], stream: bool = False, async_mode: bool = False, temprature: float = 0.75, topP: float = 0.9, max_tokens: int = 4096):
        if async_mode and stream:
            return self.async_make_retried_generator(messages, temprature, topP, max_tokens)
        elif async_mode:
            return self.async_get_full_response(messages, temprature, topP, max_tokens)
        if stream:
            return self.sync_make_retried_generator(messages, temprature, topP, max_tokens)
        return self.sync_get_full_response(messages, temprature, topP, max_tokens)

    def sync_make_retried_generator(self, messages, temprature: float, topP: float, max_tokens: int):
        payload = self.build_payload(messages, temprature, topP, max_tokens)
        for i in range(MAX_RETRIES):
            try:
                res = requests.post("https://www.llama2.ai/api", json=payload, stream=True)
                for chunk in res.iter_content(chunk_size=1024):
                    yield chunk.decode('utf-8')
                break
            except Exception as e:
                if i == MAX_RETRIES - 1:
                    raise e
                time.sleep(1)

    async def async_make_retried_generator(self, messages, temperature: float, topP: float, max_tokens: int):
        payload = self.build_payload(messages, temperature, topP, max_tokens)
        async with aiohttp.ClientSession() as session:
            for i in range(MAX_RETRIES):
                try:
                    await LlamaChat.semaphore.acquire()  # Acquire the shared semaphore
                    print("Acquired semaphore. Count", LlamaChat.semaphore._value)
                    async with session.post("https://www.llama2.ai/api", json=payload) as res:
                        async for chunk in res.content.iter_chunked(1024):
                            yield chunk.decode('utf-8')
                        break
                except Exception as e:
                    if i == MAX_RETRIES - 1:
                        raise e
                finally:
                    LlamaChat.semaphore.release()  # Release the shared semaphore
                    print("Released semaphore. Count", LlamaChat.semaphore._value)
                await asyncio.sleep(1)

    def sync_get_full_response(self, messages, temprature: float, topP: float, max_tokens: int):
        response_data = ''
        for chunk in self.sync_make_retried_generator(messages, temprature, topP, max_tokens):
            response_data += chunk
        if response_data == '':
            time.sleep(10)
            print("Retrying... (Sleep 10s)")
            return self.sync_get_full_response(messages, temprature, topP, max_tokens)
        return self.cleanup_response(response_data)

    async def async_get_full_response(self, messages, temprature: float, topP: float, max_tokens: int):
        response_data = ''
        async for chunk in self.async_make_retried_generator(messages, temprature, topP, max_tokens):
            response_data += chunk
        if response_data == '':
            await asyncio.sleep(10)
            print("Retrying... (Sleep 10s)")
            return await self.async_get_full_response(messages, temprature, topP, max_tokens)
        return self.cleanup_response(response_data)
    
    def build_payload(self, messages: list[dict], temprature: float, topP: float, max_tokens: int):
        payload = {
            "prompt": messages[-1]['content'] if messages[-1]['role'] == 'user' else "",
            "systemPrompt": messages[0]['content'] if messages[0]['role'] == 'system' else "", 
            "version": self.version_hash,
            "temperature": temprature,
            "topP": topP,
            "maxTokens": max_tokens,
            "image": None,
            "audio": None
        }
        return payload

    def cleanup_response(self, response: str):
        lines = response.splitlines()
        if lines[0].startswith("Sure"):
            lines.pop(0)
        if lines[-1].startswith("I hope"):
            lines.pop(-1)
        return "\n".join(lines)