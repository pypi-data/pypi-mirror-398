import asyncio
import inspect
import json
from typing import Callable, Tuple, Optional, Union, Dict, Any
from graphql import GraphQLResolveInfo
from graphql import OperationType
from Osdental.Encryptor.Jwt import JWT
from Osdental.Exception.ControlledException import UnauthorizedException, InvalidFormatException
from Osdental.Models.Encryptor import Encryptor
from Osdental.Models.Token import AuthToken
from Osdental.Shared.Enums.Message import Message
from Osdental.Shared.Enums.Profile import Profile
from Osdental.Shared.Enums.App import App
from Osdental.Shared.Instance import Instance


class DecryptedHelper:

    _PARAM_MASK_CACHE: Dict[Callable, Dict[str, bool]] = {}


    @staticmethod
    async def validate_token(id_token: str, id_user: str, id_external_enterprise: str, id_tenant: str):
        """
        Makes the call to the authentication service to validate token.
        Throws OSDException if wrong.
        """
        request = {
            "id_token": id_token,
            "id_user": id_user,
            "id_external_enterprise": id_external_enterprise,
            "id_tenant": id_tenant
        }
        is_auth = await Instance.grpc_auth_adapter.validate_auth_token(json.dumps(request))
        if not is_auth:
            raise UnauthorizedException(message=Message.PORTAL_ACCESS_RESTRICTED_MSG, error=Message.PORTAL_ACCESS_RESTRICTED_MSG)
        
    
    @staticmethod
    async def decrypted_token(info: GraphQLResolveInfo, encryptor: Encryptor, mutate: bool = True) -> Optional[AuthToken]:
        """
        Decrypts and validates the context token (user_token).
        Returns AuthToken or None if no token exists.
        """
        operation_type = info.operation.operation
        user_token_encrypted = info.context.get('user_token')

        if not user_token_encrypted:
            return None

        # decrypt user_token using encryptor user key
        user_token = Instance.aes.decrypt(encryptor.aes_user, user_token_encrypted)
        payload = JWT.extract_payload(user_token, App.JWT_USER_KEY)
        payload['encryptor'] = encryptor
        payload['jwt_user_key'] = App.JWT_USER_KEY

        access_token = info.context.get('access_token')
        if access_token:
            payload['access_token'] = access_token

        token = AuthToken(**payload)
        token.base_id_external_enterprise = token.id_external_enterprise

        # Validate token with auth service (async call)
        await DecryptedHelper.validate_token(token.id_token, token.id_user, token.id_external_enterprise, token.id_tenant)

        # Headers-based overrides / marketing logic
        headers = info.context.get('headers', {})
        id_external_mk = headers.get('dynamicClientId')

        is_marketing = token.abbreviation.startswith(Profile.MARKETING)
        should_use_zero_uuid = (
            token.abbreviation.startswith((Profile.SUPER_ADMIN, Profile.ADMIN_OSD))
            and operation_type == OperationType.QUERY and mutate
        )
        should_use_mk_header = is_marketing and id_external_mk

        if should_use_zero_uuid:
            from uuid import UUID
            token.id_external_enterprise = str(UUID(int=0))
        elif should_use_mk_header:
            external_mk = Instance.aes.decrypt(token.aes_key_auth, id_external_mk)
            token.id_external_enterprise = external_mk
            token.mk_id_external_enterprise = external_mk

        return token
    

    @staticmethod
    def decrypted_data(aes_data: Optional[str], aes_key_auth: str, token: Optional[AuthToken]) -> Optional[Dict[str, Any]]:
        """
        Decrypt the aes data payload with aes_key_auth. 
        Validate JSON format and update token.id_external_enterprise if it comes in the payload.
        """
        if aes_data is None:
            return None

        decrypted_data_raw = Instance.aes.decrypt(aes_key_auth, aes_data)

        if isinstance(decrypted_data_raw, str):
            try:
                data = json.loads(decrypted_data_raw)
            except Exception:
                raise InvalidFormatException(message=Message.INVALID_AES_JSON_FORMAT_MSG)
        elif isinstance(decrypted_data_raw, dict):
            data = decrypted_data_raw
        else:
            raise UnauthorizedException(message=Message.UNEXPECTED_DECRYPTED_DATA_FORMAT_MSG)

        external_enterprise_req = data.get('idExternalEnterprise')
        if external_enterprise_req and token:
            token.id_external_enterprise = external_enterprise_req

        return data


    @staticmethod
    def _get_param_mask(func: Callable) -> Dict[str, bool]:
        """
        Calculates and caches what parameters the function accepts (token/data/headers).
        Returns dict with keys 'token','data','headers'.
        """
        if func in DecryptedHelper._PARAM_MASK_CACHE:
            return DecryptedHelper._PARAM_MASK_CACHE[func]

        sig = inspect.signature(func)
        params = sig.parameters
        mask = {
            "token": "token" in params,
            "data": "data" in params,
            "headers": "headers" in params
        }
        DecryptedHelper._PARAM_MASK_CACHE[func] = mask
        return mask


    @staticmethod
    def check_profile_permission(allowed_permissions: Optional[Union[str, Tuple[str, ...]]], requested_permission: str) -> bool:
        SUPER_PROFILES = (Profile.SUPER_ADMIN, Profile.ADMIN_OSD)
        if allowed_permissions is None:
            allowed = ()
        elif isinstance(allowed_permissions, str):
            allowed = (allowed_permissions,)
        else:
            allowed = allowed_permissions
        total_allowed = set(allowed) | set(SUPER_PROFILES)
        return requested_permission in total_allowed