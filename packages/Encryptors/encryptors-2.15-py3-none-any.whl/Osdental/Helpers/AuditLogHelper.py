import json
import asyncio
from typing import Dict, Any
from Osdental.InternalHttp.Response import CustomResponse
from Osdental.Encryptor.Rsa import RSAEncryptor
from Osdental.Shared.Logger import logger
from Osdental.Shared.Instance import Instance
from Osdental.Helpers.AuditQueueHelper import AuditQueueHelper


class AuditLogHelper:    
 
    @staticmethod
    def fire_and_forget(coro):
        """Centralized task handler to avoid silent errors."""
        task = asyncio.create_task(coro)

        def _callback(t: asyncio.Task):
            try:
                t.result()
            except Exception as e:
                logger.exception("[fire_and_forget] Unhandled task error")

        task.add_done_callback(_callback)
        return task

    @staticmethod
    def try_decrypt_or_return_raw(data: str, private_key_rsa: str, aes_key: str) -> str:
        decrypted = RSAEncryptor.decrypt(
            data,
            private_key_rsa,
            silent=True
        )
        if decrypted is not None:
            return decrypted

        decrypted = Instance.aes.decrypt(
            aes_key,
            data,
            silent=True
        )
        if decrypted is not None:
            return decrypted

        return data

    @staticmethod
    def enqueue_response(data: Any, batch: int, headers: Dict[str,str], msg_info: str = None):
        """Fully async-safe and error-traced enqueue."""
        content = None

        if isinstance(data, list) and data:
            if batch > 0 and len(data) > batch:
                batches = [data[i:i + batch] for i in range(0, len(data), batch)]
                for idx, b in enumerate(batches, start=1):
                    AuditLogHelper.fire_and_forget(
                        AuditQueueHelper.send(
                            CustomResponse(
                                content=json.dumps(b),
                                headers=headers,
                                batch=idx
                            ).send_to_service_bus()
                        )
                    )
                return

            content = json.dumps(data)
        else:
            content = json.dumps(data) if isinstance(data, dict) else msg_info

        AuditLogHelper.fire_and_forget(
            AuditQueueHelper.send(
                CustomResponse(content=content, headers=headers).send_to_service_bus()
            )
        )