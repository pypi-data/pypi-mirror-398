from enum import StrEnum

class Constant(StrEnum):
    USER_TOKEN = 'user_token'
    AES_DATA = 'aes_data'
    DEFAULT_ENCODING = 'utf-8'
    MESSAGE_LOG_INTERNAL = 'MESSAGE_LOG_INTERNAL'
    DEFAULT_EMPTY_VALUE = '*'
    RESPONSE_TYPE_ERROR = 'ERROR'
    RESPONSE_TYPE_REQUEST = 'REQUEST'
    RESPONSE_TYPE_RESPONSE = 'RESPONSE'
    MESSAGE_LOG_EXTERNAL = 'MESSAGE_LOG_EXTERNAL'
    GRAPHQL_OPERATION_NAME = 'graphql.operationName'
    GRAPHQL_STATUS = 'graphql.status'
    GRAPHQL_MESSAGE = 'graphql.message'
    GRAPHQL_DURATION_MS = 'graphql.duration_ms'