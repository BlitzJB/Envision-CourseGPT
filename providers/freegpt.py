from .utils.protocol import GenerationClient
from .utils.exceptions import RequestFailedException, RateLimitException, BadGatewayException, MaxRetriesExceeded
from .utils.utils import check_status_and_throw_error, check_chunk_and_throw_error
import time, requests, aiohttp, asyncio, hashlib, threading

MAX_RETRIES = 3

def generate_signature(timestamp: int, message: str, secret: str = ""):
    data = f"{timestamp}:{message}:{secret}"
    return hashlib.sha256(data.encode()).hexdigest()

class RateLimiter:
    def __init__(self, requests_per_minute=10):
        self.requests_per_minute = requests_per_minute
        self.request_interval = 60 / requests_per_minute
        self.last_request_time = time.time()
        self.lock = threading.Lock()
        self.async_lock = asyncio.Lock()

    def wait_for_rate_limit_sync(self):
        with self.lock:
            current_time = time.time()
            if current_time - self.last_request_time < self.request_interval:
                time.sleep(self.request_interval - (current_time - self.last_request_time))
            self.last_request_time = time.time()

    async def wait_for_rate_limit_async(self):
        async with self.async_lock:
            current_time = time.time()
            if current_time - self.last_request_time < self.request_interval:
                await asyncio.sleep(self.request_interval - (current_time - self.last_request_time))
            self.last_request_time = time.time()

rate_limiter = RateLimiter()

class FreeGPT(GenerationClient):
    def __init__(self, ratelimiter: RateLimiter = rate_limiter):
        self.ratelimiter = ratelimiter
        pass
    
    def create(self, messages: list[dict], stream: bool = False, async_mode: bool = False, temperature: float = 0.8, top_p: int = 1, **kwargs):
        if async_mode and stream:
            return self.async_make_retried_generator(messages)
        elif async_mode:
            return self.async_get_full_response(messages)
        if stream:
            return self.sync_make_retried_generator(messages)
        return self.sync_get_full_response(messages)
   
    def sync_make_retried_generator(self, messages):
        payload = {
            "time": int(time.time()),
            "messages": messages,
            "sign": generate_signature(int(time.time()), messages[-1]['content']),
            "pass": None,
        }
        for i in range(MAX_RETRIES):
            try:
                print(time.strftime("%H:%M:%S", time.localtime()), "Waiting for rate limit", rate_limiter.request_interval - (time.time() - rate_limiter.last_request_time), "seconds")
                self.ratelimiter.wait_for_rate_limit_sync()
                print(time.strftime("%H:%M:%S", time.localtime()), "Rate limit passed")
                res = requests.post("https://s.aifree.site/api/generate", json=payload, stream=True)
                check_status_and_throw_error(res)
                for chunk in res.iter_content(chunk_size=1024):
                    check_chunk_and_throw_error(chunk)
                    yield chunk.decode('utf-8')
                break
            except RequestFailedException as e:
                if i == MAX_RETRIES - 1:
                    raise MaxRetriesExceeded("Max retries exceeded") from e
                time.sleep(1)

    async def async_make_retried_generator(self, messages):
        payload = {
            "time": int(time.time()),
            "messages": messages,
            "sign": generate_signature(int(time.time()), messages[-1]['content']),
            "pass": None,
        }
        async with aiohttp.ClientSession() as session:
            for i in range(MAX_RETRIES):
                try:
                    print(time.strftime("%H:%M:%S", time.localtime()), "Waiting for rate limit", rate_limiter.request_interval - (time.time() - rate_limiter.last_request_time), "seconds")
                    await self.ratelimiter.wait_for_rate_limit_async()
                    print(time.strftime("%H:%M:%S", time.localtime()), "Rate limit passed")
                    async with session.post("https://s.aifree.site/api/generate", json=payload) as res:
                        check_status_and_throw_error(res)
                        async for chunk in res.content.iter_chunked(1024):
                            check_chunk_and_throw_error(chunk)
                            yield chunk.decode('utf-8')
                        break
                except RequestFailedException as e:
                    if i == MAX_RETRIES - 1:
                        raise MaxRetriesExceeded("Max retries exceeded") from e
                    await asyncio.sleep(1)

    def sync_get_full_response(self, messages):
        response_data = ''
        for chunk in self.sync_make_retried_generator(messages):
            response_data += chunk
        return response_data


    async def async_get_full_response(self, messages):
        response_data = ''
        async for chunk in self.async_make_retried_generator(messages):
            response_data += chunk
        return response_data