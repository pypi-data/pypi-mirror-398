import asyncio
from functools import wraps
from typing import Callable, Tuple, Optional, Union, Dict, Any
from graphql import GraphQLResolveInfo
from Osdental.Helpers.EncryptorHelper import EncryptorHelper
from Osdental.Helpers.DecryptedHelper import DecryptedHelper
from Osdental.Exception.ControlledException import ProfilePermissionDeniedException
from Osdental.Shared.Enums.Message import Message


def process_encrypted_data(mutate: bool = True, allowed_permissions: Optional[Union[str, Tuple[str, ...]]] = None):
    """
    Decorator to:
      - get cached encryptor (fast & safe)
      - decrypt and validate token (async)
      - decrypt aes_data (CPU-bound small op)
      - perform profile permission checks
      - call original function passing only needed kwargs (token/data/headers)
    """
    def decorator(func: Callable):
        param_mask = DecryptedHelper._get_param_mask(func)

        @wraps(func)
        async def wrapper(self, info: GraphQLResolveInfo = None, aes_data: str = None, **rest_kwargs):
            # 1) Get encryptor (fast cached path)
            encryptor = await EncryptorHelper.get_cached_encryptors()

            # 2) Extract context & headers safely
            token_task = None
            token_result = None
            data_result = None

            # If no info provided, just call original with rest kwargs
            if info is None:
                return await func(self, **rest_kwargs)

            headers = info.context.get('headers', {}) or {}

            # 3) Start tasks in parallel where possible
            # decrypted_token requires encryptor + info
            token_coro = DecryptedHelper.decrypted_token(info, encryptor, mutate) if param_mask["token"] else None
            # decrypted_data requires aes_auth and token (token not yet available)
            # we can start decrypting aes_data because aes decrypt only needs aes_auth (from encryptor)
            data_coro = None
            if param_mask["data"] and aes_data is not None:
                # decrypt is sync in our lib -> wrap in loop.run_in_executor to avoid blocking event loop if heavy
                loop = asyncio.get_running_loop()
                data_coro = loop.run_in_executor(None, DecryptedHelper.decrypted_data, aes_data, encryptor.aes_auth, None)

            # run token and data decrypt in parallel (token will run validate_token internally)
            results = await asyncio.gather(*[c for c in (token_coro, data_coro) if c is not None], return_exceptions=True)

            # map results back
            # results order matches the list comprehension above
            idx = 0
            if token_coro is not None:
                token_result = results[idx]
                idx += 1
            if data_coro is not None:
                data_result = results[idx]
                idx += 1

            # if any returned an exception, re-raise with context
            for res in (token_result, data_result):
                if isinstance(res, Exception):
                    # wrap/raise to keep trace and consistent error handling
                    raise res

            # If token_result exists but we decrypted data without token, we may need to re-run decrypted_data
            # to attach token.id_external_enterprise override (if data contained such field).
            if token_result and data_result is None and aes_data is not None and param_mask["data"]:
                # decrypt using executor to avoid blocking (sync operation)
                loop = asyncio.get_running_loop()
                data_result = await loop.run_in_executor(None, DecryptedHelper.decrypted_data, aes_data, encryptor.aes_auth, token_result)

            # If we have both token and data and we decrypted data before token (token finished later),
            # ensure token id_external_enterprise override is applied:
            if token_result and data_result:
                external_enterprise_req = data_result.get('idExternalEnterprise')
                if external_enterprise_req:
                    token_result.id_external_enterprise = external_enterprise_req

            # 4) permission check
            if allowed_permissions and token_result:
                if not DecryptedHelper.check_profile_permission(allowed_permissions, token_result.abbreviation):
                    raise ProfilePermissionDeniedException(message=Message.PROFILE_PERMISSION_DENIED_MSG)

            # 5) Prepare kwargs to pass to original function (use cached param_mask)
            kwargs_to_pass: Dict[str, Any] = {}
            if param_mask["token"] and token_result:
                kwargs_to_pass["token"] = token_result
            if param_mask["data"] and data_result:
                kwargs_to_pass["data"] = data_result
            if param_mask["headers"] and headers:
                kwargs_to_pass["headers"] = headers

            # Merge additional kwargs the caller passed (rest_kwargs); func's signature will accept them
            return await func(self, **kwargs_to_pass, **rest_kwargs)

        return wrapper
    return decorator