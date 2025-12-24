import asyncio
import json
import re
import time
from fastapi import Request
from Osdental.Models.Token import AuthToken
from Osdental.Encryptor.Jwt import JWT
from Osdental.Shared.Enums.Constant import Constant
from Osdental.Shared.Instance import Instance

class RequestHelper:
    
    _IP_CACHE: dict[str, tuple[str, float]] = {}
    _IP_LOCK = asyncio.Lock()
    _IP_TTL = 24 * 60 * 60  # 24h
    _CLEANUP_EVERY = 1000
    _CALLS = 0
    _CALLS_LOCK = asyncio.Lock()


    @staticmethod
    def _extract_data(message_in: dict, aes_key_user: str) -> str:
        query = message_in.get("query")
        if not query:
            return Constant.DEFAULT_EMPTY_VALUE

        match = re.search(r'data:\s*"([^"]+)"', query)
        if not match:
            return Constant.DEFAULT_EMPTY_VALUE

        try:
            return Instance.aes.decrypt(aes_key_user, match.group(1))
        except Exception:
            return Constant.DEFAULT_EMPTY_VALUE


    @staticmethod
    def _get_user_ip(request: Request) -> str | None:
        xff = request.headers.get("X-Forwarded-For")
        if xff:
            return xff.split(',')[0]
        
        return getattr(request.client, "host", None)


    @staticmethod
    async def _cleanup_cache() -> None:
        now = time.time()

        async with RequestHelper._IP_LOCK:
            expired = [
                ip for ip, (_, ts) in RequestHelper._IP_CACHE.items()
                if now - ts > RequestHelper._IP_TTL
            ]

            for ip in expired:
                del RequestHelper._IP_CACHE[ip]

    
    @staticmethod
    async def _get_location_cached(ip: str) -> str:
        if not ip:
            return Constant.DEFAULT_EMPTY_VALUE

        async with RequestHelper._CALLS_LOCK:
            RequestHelper._CALLS += 1
            do_cleanup = (
                RequestHelper._CALLS % RequestHelper._CLEANUP_EVERY == 0
            )

        if do_cleanup:
            await RequestHelper._cleanup_cache()

        now = time.time()
        cached = RequestHelper._IP_CACHE.get(ip)

        # FAST PATH
        if cached:
            value, ts = cached
            if now - ts < RequestHelper._IP_TTL:
                return value

        # SLOW PATH
        async with RequestHelper._IP_LOCK:
            cached = RequestHelper._IP_CACHE.get(ip)
            if cached:
                value, ts = cached
                if now - ts < RequestHelper._IP_TTL:
                    return value

            try:
                resp = await Instance.http_client.get(
                    f"https://ipapi.co/{ip}/json/"
                )

                if resp.status_code != 200:
                    return Constant.DEFAULT_EMPTY_VALUE

                data = resp.json()
                location = json.dumps({
                    "ip": ip,
                    "city": data.get("city"),
                    "region": data.get("region"),
                    "country": data.get("country_name"),
                    "latitude": data.get("latitude"),
                    "longitude": data.get("longitude"),
                })

                RequestHelper._IP_CACHE[ip] = (location, now)
                return location

            except Exception:
                return Constant.DEFAULT_EMPTY_VALUE



    @staticmethod
    def _get_user_id(request: Request, aes_key_user: str, jwt_user_key: str) -> str:
        auth = request.headers.get('Authorization')
        if not auth or not auth.startswith('Bearer '):
            return Constant.DEFAULT_EMPTY_VALUE

        try:
            token_encrypted = auth.split(' ', 1)[1]
            token_raw = Instance.aes.decrypt(aes_key_user, token_encrypted)
            payload = JWT.extract_payload(token_raw, jwt_user_key)
            token = AuthToken(**payload)
            return token.id_user
        
        except Exception:
            return Constant.DEFAULT_EMPTY_VALUE