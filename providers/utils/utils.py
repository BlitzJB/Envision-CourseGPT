from .exceptions import BadGatewayException, RateLimitException, MaxRetriesExceeded
import aiohttp, time, requests, asyncio, hashlib

def check_status_and_throw_error(response: aiohttp.ClientResponse):
    # if .status exists then use that or else use .status_code
    status = response.status if hasattr(response, "status") else response.status_code
    if status != 200:
        raise BadGatewayException("An internal error occurred with Vercel")

def check_chunk_and_throw_error(chunk: bytes):
    # check with b'\u8bbf' if chunk is in bytes or '\u8bbf' if chunk is in str
    if isinstance(chunk, bytes) and b'\xe8' in chunk:
        raise RateLimitException("Rate limit exceeded")
    if isinstance(chunk, str) and '访' in chunk:
        raise RateLimitException("Rate limit exceeded")