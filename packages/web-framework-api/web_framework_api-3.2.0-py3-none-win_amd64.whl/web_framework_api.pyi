"""
Python API for WebFramework
"""
from __future__ import annotations
import collections.abc
import typing
__all__: list[str] = ['ACCEPTED', 'ALREADY_REPORTED', 'AUTHENTICATION_TIMEOUT', 'A_TIMEOUT_OCCURRED', 'BAD_GATEWAY', 'BAD_REQUEST', 'BANDWIDTH_LIMIT_EXCEEDED', 'CLIENT_CLOSED_REQUEST', 'CONFLICT', 'CONNECTION_TIMED_OUT', 'CONTINUE', 'CREATED', 'ChunkGenerator', 'Config', 'Database', 'DynamicFunction', 'EXPECTATION_FAILED', 'ExecutorSettings', 'ExecutorType', 'FAILED_DEPENDENCY', 'FORBIDDEN', 'FOUND', 'GATEWAY_TIMEOUT', 'GONE', 'HTTP_VERSION_NOT_SUPPORTED', 'HeavyOperationStatefulExecutor', 'HeavyOperationStatelessExecutor', 'HttpRequest', 'HttpResponse', 'IAM_A_TEAPOT', 'IHttpRequest', 'IHttpResponse', 'IM_USED', 'INSUFFICIENT_STORAGE', 'INTERNAL_SERVER_ERROR', 'INVALID_SSL_CERTIFICATE', 'LENGTH_REQUIRED', 'LOCKED', 'LOOP_DETECTED', 'LargeData', 'LoadBalancerHeuristic', 'METHOD_NOT_ALLOWED', 'MISDIRECTED_REQUEST', 'MOVED_PERMANENTLY', 'MULTIPLE_CHOICES', 'MULTI_STATUS', 'Multipart', 'NETWORK_AUTHENTICATION_REQUIRED', 'NON_AUTHORITATIVE_INFORMATION', 'NOT_ACCEPTABLE', 'NOT_EXTENDED', 'NOT_FOUND', 'NOT_IMPLEMENTED', 'NOT_MODIFIED', 'NO_CONTENT', 'OK', 'ORIGIN_IS_UNREACHABLE', 'PARTIAL_CONTENT', 'PAYLOAD_TOO_LARGE', 'PAYMENT_REQUIRED', 'PERMANENT_REDIRECT', 'PRECONDITION_FAILED', 'PRECONDITION_REQUIRED', 'PROCESSING', 'PROXY_AUTHENTICATION_REQUIRED', 'RANGE_NOT_SATISFIABLE', 'REQUEST_HEADER_FIELDS_TOO_LARGE', 'REQUEST_TIMEOUT', 'RESET_CONTENT', 'RETRY_WITH', 'ResponseCodes', 'SEE_OTHER', 'SERVICE_UNAVAILABLE', 'SSL_HANDSHAKE_FAILED', 'SWITCHING_PROTOCOLS', 'SqlResult', 'SqlValue', 'StatefulExecutor', 'StatelessExecutor', 'TEMPORARY_REDIRECT', 'TOO_MANY_REQUESTS', 'Table', 'UNAUTHORIZED', 'UNAVAILABLE_FOR_LEGAL_REASONS', 'UNKNOWN_ERROR', 'UNPROCESSABLE_ENTITY', 'UNSUPPORTED_MEDIA_TYPE', 'UPGRADE_REQUIRED', 'URI_TOO_LONG', 'USE_PROXY', 'VARIANT_ALSO_NEGOTIATES', 'WEB_SERVER_IS_DOWN', 'WebFramework', 'WebFrameworkException', 'get_localized_string', 'heavyOperationStateful', 'heavyOperationStateless', 'initialize_web_framework', 'make_sql_values', 'stateful', 'stateless']
class ChunkGenerator:
    def __init__(self) -> None:
        ...
    def generate(self) -> typing.Any:
        """
        generate() -> str | bytes
        """
class Config:
    @typing.overload
    def __init__(self, config_path: os.PathLike | str | bytes) -> None:
        ...
    @typing.overload
    def __init__(self, server_configuration: str, application_directory: str) -> None:
        ...
    @typing.overload
    def __init__(self, config_path: os.PathLike | str | bytes) -> None:
        ...
    def get_base_path(self) -> str:
        ...
    def get_configuration(self) -> str:
        ...
    def get_configuration_bool(self, key: str, recursive: bool = True) -> bool:
        ...
    def get_configuration_int(self, key: str, recursive: bool = True) -> int:
        ...
    def get_configuration_string(self, key: str, recursive: bool = True) -> str:
        ...
    def get_raw_configuration(self) -> str:
        ...
    def override_base_path(self, base_path: str) -> Config:
        ...
    @typing.overload
    def override_configuration(self, key: str, value: str, recursive: bool = True) -> Config:
        ...
    @typing.overload
    def override_configuration(self, key: str, value: bool, recursive: bool = True) -> Config:
        ...
    @typing.overload
    def override_configuration(self, key: str, value: typing.SupportsInt, recursive: bool = True) -> Config:
        ...
    @typing.overload
    def override_configuration(self, key: str, value: collections.abc.Sequence[str], recursive: bool = True) -> Config:
        ...
    @typing.overload
    def override_configuration(self, key: str, value: collections.abc.Sequence[typing.SupportsInt], recursive: bool = True) -> Config:
        ...
class Database:
    @typing.overload
    def __contains__(self, table_name: str) -> bool:
        ...
    @typing.overload
    def __contains__(self, table_name: str) -> bool:
        ...
    def __getitem__(self, table_name: str) -> Table:
        ...
    def get_database_file_name(self) -> str:
        ...
    def get_database_name(self) -> str:
        ...
    def get_or_create_table(self, table_name: str, create_table_query: str) -> Table:
        ...
    def get_table(self, table_name: str) -> Table:
        ...
class DynamicFunction:
    def __call__(self, *args) -> str:
        ...
    def __init__(self) -> None:
        ...
class ExecutorSettings:
    class LoadType:
        """
        Members:
        
          initialization
        
          dynamic
        
          none
        """
        __members__: typing.ClassVar[dict[str, ExecutorSettings.LoadType]]  # value = {'initialization': <LoadType.initialization: 0>, 'dynamic': <LoadType.dynamic: 1>, 'none': <LoadType.none: 2>}
        dynamic: typing.ClassVar[ExecutorSettings.LoadType]  # value = <LoadType.dynamic: 1>
        initialization: typing.ClassVar[ExecutorSettings.LoadType]  # value = <LoadType.initialization: 0>
        none: typing.ClassVar[ExecutorSettings.LoadType]  # value = <LoadType.none: 2>
        def __eq__(self, other: typing.Any) -> bool:
            ...
        def __getstate__(self) -> int:
            ...
        def __hash__(self) -> int:
            ...
        def __index__(self) -> int:
            ...
        def __init__(self, value: typing.SupportsInt) -> None:
            ...
        def __int__(self) -> int:
            ...
        def __ne__(self, other: typing.Any) -> bool:
            ...
        def __repr__(self) -> str:
            ...
        def __setstate__(self, state: typing.SupportsInt) -> None:
            ...
        def __str__(self) -> str:
            ...
        @property
        def name(self) -> str:
            ...
        @property
        def value(self) -> int:
            ...
    dynamic: typing.ClassVar[ExecutorSettings.LoadType]  # value = <LoadType.dynamic: 1>
    initialization: typing.ClassVar[ExecutorSettings.LoadType]  # value = <LoadType.initialization: 0>
    none: typing.ClassVar[ExecutorSettings.LoadType]  # value = <LoadType.none: 2>
    def __init__(self, pointer: typing.SupportsInt) -> None:
        ...
    def get_api_type(self) -> str:
        ...
    def get_init_parameters(self) -> dict:
        ...
    def get_load_type(self) -> ExecutorSettings.LoadType:
        ...
    def get_name_type(self) -> str:
        ...
    def get_user_agent_filter(self) -> str:
        ...
class ExecutorType:
    """
    Members:
    
      stateful
    
      stateless
    
      heavyOperationStateful
    
      heavyOperationStateless
    """
    __members__: typing.ClassVar[dict[str, ExecutorType]]  # value = {'stateful': <ExecutorType.stateful: 0>, 'stateless': <ExecutorType.stateless: 1>, 'heavyOperationStateful': <ExecutorType.heavyOperationStateful: 2>, 'heavyOperationStateless': <ExecutorType.heavyOperationStateless: 3>}
    heavyOperationStateful: typing.ClassVar[ExecutorType]  # value = <ExecutorType.heavyOperationStateful: 2>
    heavyOperationStateless: typing.ClassVar[ExecutorType]  # value = <ExecutorType.heavyOperationStateless: 3>
    stateful: typing.ClassVar[ExecutorType]  # value = <ExecutorType.stateful: 0>
    stateless: typing.ClassVar[ExecutorType]  # value = <ExecutorType.stateless: 1>
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class HeavyOperationStatefulExecutor:
    def __init__(self) -> None:
        ...
    def destroy(self) -> None:
        ...
    def do_connect(self, request: HttpRequest, response: HttpResponse) -> None:
        ...
    def do_delete(self, request: HttpRequest, response: HttpResponse) -> None:
        ...
    def do_get(self, request: HttpRequest, response: HttpResponse) -> None:
        ...
    def do_head(self, request: HttpRequest, response: HttpResponse) -> None:
        ...
    def do_options(self, request: HttpRequest, response: HttpResponse) -> None:
        ...
    def do_patch(self, request: HttpRequest, response: HttpResponse) -> None:
        ...
    def do_post(self, request: HttpRequest, response: HttpResponse) -> None:
        ...
    def do_put(self, request: HttpRequest, response: HttpResponse) -> None:
        ...
    def do_trace(self, request: HttpRequest, response: HttpResponse) -> None:
        ...
    def get_type(self) -> ExecutorType:
        ...
    def init(self, settings: ExecutorSettings) -> None:
        ...
class HeavyOperationStatelessExecutor:
    def __init__(self) -> None:
        ...
    def do_connect(self, request: HttpRequest, response: HttpResponse) -> None:
        ...
    def do_delete(self, request: HttpRequest, response: HttpResponse) -> None:
        ...
    def do_get(self, request: HttpRequest, response: HttpResponse) -> None:
        ...
    def do_head(self, request: HttpRequest, response: HttpResponse) -> None:
        ...
    def do_options(self, request: HttpRequest, response: HttpResponse) -> None:
        ...
    def do_patch(self, request: HttpRequest, response: HttpResponse) -> None:
        ...
    def do_post(self, request: HttpRequest, response: HttpResponse) -> None:
        ...
    def do_put(self, request: HttpRequest, response: HttpResponse) -> None:
        ...
    def do_trace(self, request: HttpRequest, response: HttpResponse) -> None:
        ...
    def get_type(self) -> ExecutorType:
        ...
    def init(self, settings: ExecutorSettings) -> None:
        ...
class HttpRequest:
    def __init__(self, pointer: typing.SupportsInt) -> None:
        ...
    def delete_session(self) -> None:
        ...
    def get_attribute(self, arg0: str, arg1: str) -> None:
        ...
    def get_body(self) -> str:
        ...
    def get_chunks(self) -> list[str]:
        ...
    def get_client_ip_v4(self) -> str:
        ...
    def get_client_port(self) -> int:
        ...
    def get_cookies(self) -> dict[str, str]:
        ...
    def get_database(self, database_name: str) -> Database:
        ...
    def get_file(self, file_path: os.PathLike | str | bytes) -> str:
        ...
    def get_headers(self) -> dict[str, str]:
        ...
    def get_http_version(self) -> str:
        ...
    def get_json(self) -> dict:
        ...
    def get_large_data(self) -> LargeData:
        ...
    def get_method(self) -> str:
        ...
    def get_multiparts(self) -> list[Multipart]:
        ...
    def get_or_create_database(self, database_name: str) -> Database:
        ...
    def get_or_create_table(self, database_name: str, table_name: str, create_table_query: str) -> Table:
        ...
    def get_query_parameters(self) -> dict[str, str]:
        ...
    def get_raw_parameters(self) -> str:
        ...
    def get_raw_request(self) -> str:
        ...
    @typing.overload
    def get_route_parameter(self, route_parameter_name: str) -> str:
        ...
    @typing.overload
    def get_route_parameter(self, route_parameter_name: str) -> bool:
        ...
    @typing.overload
    def get_route_parameter(self, route_parameter_name: str) -> int:
        ...
    @typing.overload
    def get_route_parameter(self, route_parameter_name: str) -> float:
        ...
    def get_server_ip_v4(self) -> str:
        ...
    def get_server_port(self) -> int:
        ...
    def get_table(self, database_name: str, table_name: str) -> Table:
        ...
    def is_wfdp_function_registered(self, function_name: str) -> bool:
        ...
    def process_dynamic_file(self, file_data: str, variables: collections.abc.Mapping[str, str]) -> str:
        ...
    def process_static_file(self, file_data: str, file_extension: str) -> str:
        ...
    def register_wfdp_function(self, function_name: str, function_class: type) -> None:
        ...
    def remove_attribute(self, name: str) -> None:
        ...
    def send_asset_file(self, file_path: str, response: HttpResponse, variables: collections.abc.Mapping[str, str], is_binary: bool, file_name: str) -> None:
        ...
    def send_chunks(self, response: HttpResponse, generator: ChunkGenerator) -> None:
        ...
    def send_dynamic_file(self, file_path: str, response: HttpResponse, variables: collections.abc.Mapping[str, str], is_binary: bool = False, file_name: str = '') -> None:
        ...
    def send_file_chunks(self, response: HttpResponse, file_name: str, generator: ChunkGenerator) -> None:
        ...
    def send_static_file(self, file_path: str, response: HttpResponse, is_binary: bool, file_name: str) -> None:
        ...
    def set_attribute(self, name: str, value: str) -> None:
        ...
    def stream_file(self, file_path: str, response: HttpResponse, file_name: str, chunk_size: typing.SupportsInt = 14680064) -> None:
        ...
    def throw_exception(self, error_message: str, response_code: ResponseCodes, log_category: str = '') -> None:
        ...
    def unregister_wfdp_function(self, function_name: str) -> None:
        ...
class HttpResponse:
    def __bool__(self) -> bool:
        ...
    def __init__(self, arg0: typing.SupportsInt) -> None:
        """
        pointer_a
        """
    def add_cookie(self, name: str, value: str) -> None:
        ...
    def add_header(self, name: str, value: str) -> None:
        ...
    def append_body(self, body: str) -> HttpResponse:
        ...
    @typing.overload
    def set_body(self, body: str) -> None:
        ...
    @typing.overload
    def set_body(self, json: dict) -> None:
        ...
    def set_default(self) -> None:
        ...
    def set_is_valid(self, arg0: bool) -> None:
        ...
    def set_response_code(self, response_code: ResponseCodes) -> None:
        ...
class IHttpRequest:
    pass
class IHttpResponse:
    pass
class LargeData:
    def __iter__(self) -> collections.abc.Iterator:
        ...
    def __len__(self) -> int:
        ...
class LoadBalancerHeuristic:
    def __call__(self) -> int:
        ...
    def __init__(self, ip: str, port: str, use_https: bool) -> None:
        ...
    def get_ip(self) -> str:
        ...
    def get_port(self) -> str:
        ...
    def get_use_https(self) -> bool:
        ...
    def on_end(self) -> None:
        ...
    def on_start(self) -> None:
        ...
class Multipart:
    def get_content_type(self) -> str | None:
        ...
    def get_data(self) -> str:
        ...
    def get_file_name(self) -> str | None:
        ...
    def get_name(self) -> str:
        ...
class ResponseCodes:
    """
    Members:
    
      CONTINUE
    
      SWITCHING_PROTOCOLS
    
      PROCESSING
    
      OK
    
      CREATED
    
      ACCEPTED
    
      NON_AUTHORITATIVE_INFORMATION
    
      NO_CONTENT
    
      RESET_CONTENT
    
      PARTIAL_CONTENT
    
      MULTI_STATUS
    
      ALREADY_REPORTED
    
      IM_USED
    
      MULTIPLE_CHOICES
    
      MOVED_PERMANENTLY
    
      FOUND
    
      SEE_OTHER
    
      NOT_MODIFIED
    
      USE_PROXY
    
      TEMPORARY_REDIRECT
    
      PERMANENT_REDIRECT
    
      BAD_REQUEST
    
      UNAUTHORIZED
    
      PAYMENT_REQUIRED
    
      FORBIDDEN
    
      NOT_FOUND
    
      METHOD_NOT_ALLOWED
    
      NOT_ACCEPTABLE
    
      PROXY_AUTHENTICATION_REQUIRED
    
      REQUEST_TIMEOUT
    
      CONFLICT
    
      GONE
    
      LENGTH_REQUIRED
    
      PRECONDITION_FAILED
    
      PAYLOAD_TOO_LARGE
    
      URI_TOO_LONG
    
      UNSUPPORTED_MEDIA_TYPE
    
      RANGE_NOT_SATISFIABLE
    
      EXPECTATION_FAILED
    
      IAM_A_TEAPOT
    
      AUTHENTICATION_TIMEOUT
    
      MISDIRECTED_REQUEST
    
      UNPROCESSABLE_ENTITY
    
      LOCKED
    
      FAILED_DEPENDENCY
    
      UPGRADE_REQUIRED
    
      PRECONDITION_REQUIRED
    
      TOO_MANY_REQUESTS
    
      REQUEST_HEADER_FIELDS_TOO_LARGE
    
      RETRY_WITH
    
      UNAVAILABLE_FOR_LEGAL_REASONS
    
      CLIENT_CLOSED_REQUEST
    
      INTERNAL_SERVER_ERROR
    
      NOT_IMPLEMENTED
    
      BAD_GATEWAY
    
      SERVICE_UNAVAILABLE
    
      GATEWAY_TIMEOUT
    
      HTTP_VERSION_NOT_SUPPORTED
    
      VARIANT_ALSO_NEGOTIATES
    
      INSUFFICIENT_STORAGE
    
      LOOP_DETECTED
    
      BANDWIDTH_LIMIT_EXCEEDED
    
      NOT_EXTENDED
    
      NETWORK_AUTHENTICATION_REQUIRED
    
      UNKNOWN_ERROR
    
      WEB_SERVER_IS_DOWN
    
      CONNECTION_TIMED_OUT
    
      ORIGIN_IS_UNREACHABLE
    
      A_TIMEOUT_OCCURRED
    
      SSL_HANDSHAKE_FAILED
    
      INVALID_SSL_CERTIFICATE
    """
    ACCEPTED: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.ACCEPTED: 202>
    ALREADY_REPORTED: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.ALREADY_REPORTED: 208>
    AUTHENTICATION_TIMEOUT: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.AUTHENTICATION_TIMEOUT: 419>
    A_TIMEOUT_OCCURRED: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.A_TIMEOUT_OCCURRED: 524>
    BAD_GATEWAY: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.BAD_GATEWAY: 502>
    BAD_REQUEST: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.BAD_REQUEST: 400>
    BANDWIDTH_LIMIT_EXCEEDED: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.BANDWIDTH_LIMIT_EXCEEDED: 509>
    CLIENT_CLOSED_REQUEST: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.CLIENT_CLOSED_REQUEST: 499>
    CONFLICT: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.CONFLICT: 409>
    CONNECTION_TIMED_OUT: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.CONNECTION_TIMED_OUT: 522>
    CONTINUE: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.CONTINUE: 100>
    CREATED: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.CREATED: 201>
    EXPECTATION_FAILED: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.EXPECTATION_FAILED: 417>
    FAILED_DEPENDENCY: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.FAILED_DEPENDENCY: 424>
    FORBIDDEN: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.FORBIDDEN: 403>
    FOUND: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.FOUND: 302>
    GATEWAY_TIMEOUT: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.GATEWAY_TIMEOUT: 504>
    GONE: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.GONE: 410>
    HTTP_VERSION_NOT_SUPPORTED: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.HTTP_VERSION_NOT_SUPPORTED: 505>
    IAM_A_TEAPOT: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.IAM_A_TEAPOT: 418>
    IM_USED: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.IM_USED: 226>
    INSUFFICIENT_STORAGE: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.INSUFFICIENT_STORAGE: 507>
    INTERNAL_SERVER_ERROR: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.INTERNAL_SERVER_ERROR: 500>
    INVALID_SSL_CERTIFICATE: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.INVALID_SSL_CERTIFICATE: 526>
    LENGTH_REQUIRED: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.LENGTH_REQUIRED: 411>
    LOCKED: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.LOCKED: 423>
    LOOP_DETECTED: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.LOOP_DETECTED: 508>
    METHOD_NOT_ALLOWED: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.METHOD_NOT_ALLOWED: 405>
    MISDIRECTED_REQUEST: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.MISDIRECTED_REQUEST: 421>
    MOVED_PERMANENTLY: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.MOVED_PERMANENTLY: 301>
    MULTIPLE_CHOICES: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.MULTIPLE_CHOICES: 300>
    MULTI_STATUS: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.MULTI_STATUS: 207>
    NETWORK_AUTHENTICATION_REQUIRED: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.NETWORK_AUTHENTICATION_REQUIRED: 511>
    NON_AUTHORITATIVE_INFORMATION: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.NON_AUTHORITATIVE_INFORMATION: 203>
    NOT_ACCEPTABLE: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.NOT_ACCEPTABLE: 406>
    NOT_EXTENDED: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.NOT_EXTENDED: 510>
    NOT_FOUND: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.NOT_FOUND: 404>
    NOT_IMPLEMENTED: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.NOT_IMPLEMENTED: 501>
    NOT_MODIFIED: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.NOT_MODIFIED: 304>
    NO_CONTENT: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.NO_CONTENT: 204>
    OK: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.OK: 200>
    ORIGIN_IS_UNREACHABLE: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.ORIGIN_IS_UNREACHABLE: 523>
    PARTIAL_CONTENT: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.PARTIAL_CONTENT: 206>
    PAYLOAD_TOO_LARGE: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.PAYLOAD_TOO_LARGE: 413>
    PAYMENT_REQUIRED: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.PAYMENT_REQUIRED: 402>
    PERMANENT_REDIRECT: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.PERMANENT_REDIRECT: 308>
    PRECONDITION_FAILED: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.PRECONDITION_FAILED: 412>
    PRECONDITION_REQUIRED: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.PRECONDITION_REQUIRED: 428>
    PROCESSING: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.PROCESSING: 102>
    PROXY_AUTHENTICATION_REQUIRED: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.PROXY_AUTHENTICATION_REQUIRED: 407>
    RANGE_NOT_SATISFIABLE: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.RANGE_NOT_SATISFIABLE: 416>
    REQUEST_HEADER_FIELDS_TOO_LARGE: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.REQUEST_HEADER_FIELDS_TOO_LARGE: 431>
    REQUEST_TIMEOUT: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.REQUEST_TIMEOUT: 408>
    RESET_CONTENT: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.RESET_CONTENT: 205>
    RETRY_WITH: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.RETRY_WITH: 449>
    SEE_OTHER: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.SEE_OTHER: 303>
    SERVICE_UNAVAILABLE: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.SERVICE_UNAVAILABLE: 503>
    SSL_HANDSHAKE_FAILED: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.SSL_HANDSHAKE_FAILED: 525>
    SWITCHING_PROTOCOLS: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.SWITCHING_PROTOCOLS: 101>
    TEMPORARY_REDIRECT: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.TEMPORARY_REDIRECT: 307>
    TOO_MANY_REQUESTS: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.TOO_MANY_REQUESTS: 429>
    UNAUTHORIZED: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.UNAUTHORIZED: 401>
    UNAVAILABLE_FOR_LEGAL_REASONS: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.UNAVAILABLE_FOR_LEGAL_REASONS: 451>
    UNKNOWN_ERROR: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.UNKNOWN_ERROR: 520>
    UNPROCESSABLE_ENTITY: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.UNPROCESSABLE_ENTITY: 422>
    UNSUPPORTED_MEDIA_TYPE: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.UNSUPPORTED_MEDIA_TYPE: 415>
    UPGRADE_REQUIRED: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.UPGRADE_REQUIRED: 426>
    URI_TOO_LONG: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.URI_TOO_LONG: 414>
    USE_PROXY: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.USE_PROXY: 305>
    VARIANT_ALSO_NEGOTIATES: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.VARIANT_ALSO_NEGOTIATES: 506>
    WEB_SERVER_IS_DOWN: typing.ClassVar[ResponseCodes]  # value = <ResponseCodes.WEB_SERVER_IS_DOWN: 521>
    __members__: typing.ClassVar[dict[str, ResponseCodes]]  # value = {'CONTINUE': <ResponseCodes.CONTINUE: 100>, 'SWITCHING_PROTOCOLS': <ResponseCodes.SWITCHING_PROTOCOLS: 101>, 'PROCESSING': <ResponseCodes.PROCESSING: 102>, 'OK': <ResponseCodes.OK: 200>, 'CREATED': <ResponseCodes.CREATED: 201>, 'ACCEPTED': <ResponseCodes.ACCEPTED: 202>, 'NON_AUTHORITATIVE_INFORMATION': <ResponseCodes.NON_AUTHORITATIVE_INFORMATION: 203>, 'NO_CONTENT': <ResponseCodes.NO_CONTENT: 204>, 'RESET_CONTENT': <ResponseCodes.RESET_CONTENT: 205>, 'PARTIAL_CONTENT': <ResponseCodes.PARTIAL_CONTENT: 206>, 'MULTI_STATUS': <ResponseCodes.MULTI_STATUS: 207>, 'ALREADY_REPORTED': <ResponseCodes.ALREADY_REPORTED: 208>, 'IM_USED': <ResponseCodes.IM_USED: 226>, 'MULTIPLE_CHOICES': <ResponseCodes.MULTIPLE_CHOICES: 300>, 'MOVED_PERMANENTLY': <ResponseCodes.MOVED_PERMANENTLY: 301>, 'FOUND': <ResponseCodes.FOUND: 302>, 'SEE_OTHER': <ResponseCodes.SEE_OTHER: 303>, 'NOT_MODIFIED': <ResponseCodes.NOT_MODIFIED: 304>, 'USE_PROXY': <ResponseCodes.USE_PROXY: 305>, 'TEMPORARY_REDIRECT': <ResponseCodes.TEMPORARY_REDIRECT: 307>, 'PERMANENT_REDIRECT': <ResponseCodes.PERMANENT_REDIRECT: 308>, 'BAD_REQUEST': <ResponseCodes.BAD_REQUEST: 400>, 'UNAUTHORIZED': <ResponseCodes.UNAUTHORIZED: 401>, 'PAYMENT_REQUIRED': <ResponseCodes.PAYMENT_REQUIRED: 402>, 'FORBIDDEN': <ResponseCodes.FORBIDDEN: 403>, 'NOT_FOUND': <ResponseCodes.NOT_FOUND: 404>, 'METHOD_NOT_ALLOWED': <ResponseCodes.METHOD_NOT_ALLOWED: 405>, 'NOT_ACCEPTABLE': <ResponseCodes.NOT_ACCEPTABLE: 406>, 'PROXY_AUTHENTICATION_REQUIRED': <ResponseCodes.PROXY_AUTHENTICATION_REQUIRED: 407>, 'REQUEST_TIMEOUT': <ResponseCodes.REQUEST_TIMEOUT: 408>, 'CONFLICT': <ResponseCodes.CONFLICT: 409>, 'GONE': <ResponseCodes.GONE: 410>, 'LENGTH_REQUIRED': <ResponseCodes.LENGTH_REQUIRED: 411>, 'PRECONDITION_FAILED': <ResponseCodes.PRECONDITION_FAILED: 412>, 'PAYLOAD_TOO_LARGE': <ResponseCodes.PAYLOAD_TOO_LARGE: 413>, 'URI_TOO_LONG': <ResponseCodes.URI_TOO_LONG: 414>, 'UNSUPPORTED_MEDIA_TYPE': <ResponseCodes.UNSUPPORTED_MEDIA_TYPE: 415>, 'RANGE_NOT_SATISFIABLE': <ResponseCodes.RANGE_NOT_SATISFIABLE: 416>, 'EXPECTATION_FAILED': <ResponseCodes.EXPECTATION_FAILED: 417>, 'IAM_A_TEAPOT': <ResponseCodes.IAM_A_TEAPOT: 418>, 'AUTHENTICATION_TIMEOUT': <ResponseCodes.AUTHENTICATION_TIMEOUT: 419>, 'MISDIRECTED_REQUEST': <ResponseCodes.MISDIRECTED_REQUEST: 421>, 'UNPROCESSABLE_ENTITY': <ResponseCodes.UNPROCESSABLE_ENTITY: 422>, 'LOCKED': <ResponseCodes.LOCKED: 423>, 'FAILED_DEPENDENCY': <ResponseCodes.FAILED_DEPENDENCY: 424>, 'UPGRADE_REQUIRED': <ResponseCodes.UPGRADE_REQUIRED: 426>, 'PRECONDITION_REQUIRED': <ResponseCodes.PRECONDITION_REQUIRED: 428>, 'TOO_MANY_REQUESTS': <ResponseCodes.TOO_MANY_REQUESTS: 429>, 'REQUEST_HEADER_FIELDS_TOO_LARGE': <ResponseCodes.REQUEST_HEADER_FIELDS_TOO_LARGE: 431>, 'RETRY_WITH': <ResponseCodes.RETRY_WITH: 449>, 'UNAVAILABLE_FOR_LEGAL_REASONS': <ResponseCodes.UNAVAILABLE_FOR_LEGAL_REASONS: 451>, 'CLIENT_CLOSED_REQUEST': <ResponseCodes.CLIENT_CLOSED_REQUEST: 499>, 'INTERNAL_SERVER_ERROR': <ResponseCodes.INTERNAL_SERVER_ERROR: 500>, 'NOT_IMPLEMENTED': <ResponseCodes.NOT_IMPLEMENTED: 501>, 'BAD_GATEWAY': <ResponseCodes.BAD_GATEWAY: 502>, 'SERVICE_UNAVAILABLE': <ResponseCodes.SERVICE_UNAVAILABLE: 503>, 'GATEWAY_TIMEOUT': <ResponseCodes.GATEWAY_TIMEOUT: 504>, 'HTTP_VERSION_NOT_SUPPORTED': <ResponseCodes.HTTP_VERSION_NOT_SUPPORTED: 505>, 'VARIANT_ALSO_NEGOTIATES': <ResponseCodes.VARIANT_ALSO_NEGOTIATES: 506>, 'INSUFFICIENT_STORAGE': <ResponseCodes.INSUFFICIENT_STORAGE: 507>, 'LOOP_DETECTED': <ResponseCodes.LOOP_DETECTED: 508>, 'BANDWIDTH_LIMIT_EXCEEDED': <ResponseCodes.BANDWIDTH_LIMIT_EXCEEDED: 509>, 'NOT_EXTENDED': <ResponseCodes.NOT_EXTENDED: 510>, 'NETWORK_AUTHENTICATION_REQUIRED': <ResponseCodes.NETWORK_AUTHENTICATION_REQUIRED: 511>, 'UNKNOWN_ERROR': <ResponseCodes.UNKNOWN_ERROR: 520>, 'WEB_SERVER_IS_DOWN': <ResponseCodes.WEB_SERVER_IS_DOWN: 521>, 'CONNECTION_TIMED_OUT': <ResponseCodes.CONNECTION_TIMED_OUT: 522>, 'ORIGIN_IS_UNREACHABLE': <ResponseCodes.ORIGIN_IS_UNREACHABLE: 523>, 'A_TIMEOUT_OCCURRED': <ResponseCodes.A_TIMEOUT_OCCURRED: 524>, 'SSL_HANDSHAKE_FAILED': <ResponseCodes.SSL_HANDSHAKE_FAILED: 525>, 'INVALID_SSL_CERTIFICATE': <ResponseCodes.INVALID_SSL_CERTIFICATE: 526>}
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class SqlResult:
    def __getitem__(self, index: typing.SupportsInt) -> dict[str, SqlValue]:
        ...
    def __iter__(self) -> collections.abc.Iterator[dict[str, SqlValue]]:
        ...
    def __len__(self) -> int:
        ...
    def at(self, index: typing.SupportsInt) -> dict[str, SqlValue]:
        ...
class SqlValue:
    @typing.overload
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    @typing.overload
    def __init__(self, value: typing.SupportsFloat) -> None:
        ...
    @typing.overload
    def __init__(self, value: str) -> None:
        ...
    @typing.overload
    def __init__(self, value: None) -> None:
        ...
    @typing.overload
    def __init__(self, value: collections.abc.Sequence[typing.SupportsInt]) -> None:
        ...
    def get(self) -> int | float | str | bool | None | list[int]:
        ...
class StatefulExecutor:
    def __init__(self) -> None:
        ...
    def destroy(self) -> None:
        ...
    def do_connect(self, request: HttpRequest, response: HttpResponse) -> None:
        ...
    def do_delete(self, request: HttpRequest, response: HttpResponse) -> None:
        ...
    def do_get(self, request: HttpRequest, response: HttpResponse) -> None:
        ...
    def do_head(self, request: HttpRequest, response: HttpResponse) -> None:
        ...
    def do_options(self, request: HttpRequest, response: HttpResponse) -> None:
        ...
    def do_patch(self, request: HttpRequest, response: HttpResponse) -> None:
        ...
    def do_post(self, request: HttpRequest, response: HttpResponse) -> None:
        ...
    def do_put(self, request: HttpRequest, response: HttpResponse) -> None:
        ...
    def do_trace(self, request: HttpRequest, response: HttpResponse) -> None:
        ...
    def get_type(self) -> ExecutorType:
        ...
    def init(self, settings: ExecutorSettings) -> None:
        ...
class StatelessExecutor:
    def __init__(self) -> None:
        ...
    def do_connect(self, request: HttpRequest, response: HttpResponse) -> None:
        ...
    def do_delete(self, request: HttpRequest, response: HttpResponse) -> None:
        ...
    def do_get(self, request: HttpRequest, response: HttpResponse) -> None:
        ...
    def do_head(self, request: HttpRequest, response: HttpResponse) -> None:
        ...
    def do_options(self, request: HttpRequest, response: HttpResponse) -> None:
        ...
    def do_patch(self, request: HttpRequest, response: HttpResponse) -> None:
        ...
    def do_post(self, request: HttpRequest, response: HttpResponse) -> None:
        ...
    def do_put(self, request: HttpRequest, response: HttpResponse) -> None:
        ...
    def do_trace(self, request: HttpRequest, response: HttpResponse) -> None:
        ...
    def get_type(self) -> ExecutorType:
        ...
    def init(self, settings: ExecutorSettings) -> None:
        ...
class Table:
    def execute(self, query: str, values: collections.abc.Sequence[SqlValue] = []) -> SqlResult:
        ...
class WebFramework:
    @staticmethod
    def get_web_framework_version() -> str:
        ...
    @typing.overload
    def __init__(self, config_path: str) -> None:
        ...
    @typing.overload
    def __init__(self, server_configuration: str, application_directory: str) -> None:
        ...
    @typing.overload
    def __init__(self, config: Config) -> None:
        ...
    def is_server_running(self) -> bool:
        ...
    def start(self, wait: bool = False, on_start_server: collections.abc.Callable[[], None] = None) -> None:
        ...
    def stop(self, wait: bool = True) -> None:
        ...
class WebFrameworkException(Exception):
    pass
def get_localized_string(localization_module_name: str, key: str, language: str = '') -> str:
    ...
def initialize_web_framework(path_to_dll: str = '') -> None:
    ...
def make_sql_values(*args) -> list[SqlValue]:
    ...
ACCEPTED: ResponseCodes  # value = <ResponseCodes.ACCEPTED: 202>
ALREADY_REPORTED: ResponseCodes  # value = <ResponseCodes.ALREADY_REPORTED: 208>
AUTHENTICATION_TIMEOUT: ResponseCodes  # value = <ResponseCodes.AUTHENTICATION_TIMEOUT: 419>
A_TIMEOUT_OCCURRED: ResponseCodes  # value = <ResponseCodes.A_TIMEOUT_OCCURRED: 524>
BAD_GATEWAY: ResponseCodes  # value = <ResponseCodes.BAD_GATEWAY: 502>
BAD_REQUEST: ResponseCodes  # value = <ResponseCodes.BAD_REQUEST: 400>
BANDWIDTH_LIMIT_EXCEEDED: ResponseCodes  # value = <ResponseCodes.BANDWIDTH_LIMIT_EXCEEDED: 509>
CLIENT_CLOSED_REQUEST: ResponseCodes  # value = <ResponseCodes.CLIENT_CLOSED_REQUEST: 499>
CONFLICT: ResponseCodes  # value = <ResponseCodes.CONFLICT: 409>
CONNECTION_TIMED_OUT: ResponseCodes  # value = <ResponseCodes.CONNECTION_TIMED_OUT: 522>
CONTINUE: ResponseCodes  # value = <ResponseCodes.CONTINUE: 100>
CREATED: ResponseCodes  # value = <ResponseCodes.CREATED: 201>
EXPECTATION_FAILED: ResponseCodes  # value = <ResponseCodes.EXPECTATION_FAILED: 417>
FAILED_DEPENDENCY: ResponseCodes  # value = <ResponseCodes.FAILED_DEPENDENCY: 424>
FORBIDDEN: ResponseCodes  # value = <ResponseCodes.FORBIDDEN: 403>
FOUND: ResponseCodes  # value = <ResponseCodes.FOUND: 302>
GATEWAY_TIMEOUT: ResponseCodes  # value = <ResponseCodes.GATEWAY_TIMEOUT: 504>
GONE: ResponseCodes  # value = <ResponseCodes.GONE: 410>
HTTP_VERSION_NOT_SUPPORTED: ResponseCodes  # value = <ResponseCodes.HTTP_VERSION_NOT_SUPPORTED: 505>
IAM_A_TEAPOT: ResponseCodes  # value = <ResponseCodes.IAM_A_TEAPOT: 418>
IM_USED: ResponseCodes  # value = <ResponseCodes.IM_USED: 226>
INSUFFICIENT_STORAGE: ResponseCodes  # value = <ResponseCodes.INSUFFICIENT_STORAGE: 507>
INTERNAL_SERVER_ERROR: ResponseCodes  # value = <ResponseCodes.INTERNAL_SERVER_ERROR: 500>
INVALID_SSL_CERTIFICATE: ResponseCodes  # value = <ResponseCodes.INVALID_SSL_CERTIFICATE: 526>
LENGTH_REQUIRED: ResponseCodes  # value = <ResponseCodes.LENGTH_REQUIRED: 411>
LOCKED: ResponseCodes  # value = <ResponseCodes.LOCKED: 423>
LOOP_DETECTED: ResponseCodes  # value = <ResponseCodes.LOOP_DETECTED: 508>
METHOD_NOT_ALLOWED: ResponseCodes  # value = <ResponseCodes.METHOD_NOT_ALLOWED: 405>
MISDIRECTED_REQUEST: ResponseCodes  # value = <ResponseCodes.MISDIRECTED_REQUEST: 421>
MOVED_PERMANENTLY: ResponseCodes  # value = <ResponseCodes.MOVED_PERMANENTLY: 301>
MULTIPLE_CHOICES: ResponseCodes  # value = <ResponseCodes.MULTIPLE_CHOICES: 300>
MULTI_STATUS: ResponseCodes  # value = <ResponseCodes.MULTI_STATUS: 207>
NETWORK_AUTHENTICATION_REQUIRED: ResponseCodes  # value = <ResponseCodes.NETWORK_AUTHENTICATION_REQUIRED: 511>
NON_AUTHORITATIVE_INFORMATION: ResponseCodes  # value = <ResponseCodes.NON_AUTHORITATIVE_INFORMATION: 203>
NOT_ACCEPTABLE: ResponseCodes  # value = <ResponseCodes.NOT_ACCEPTABLE: 406>
NOT_EXTENDED: ResponseCodes  # value = <ResponseCodes.NOT_EXTENDED: 510>
NOT_FOUND: ResponseCodes  # value = <ResponseCodes.NOT_FOUND: 404>
NOT_IMPLEMENTED: ResponseCodes  # value = <ResponseCodes.NOT_IMPLEMENTED: 501>
NOT_MODIFIED: ResponseCodes  # value = <ResponseCodes.NOT_MODIFIED: 304>
NO_CONTENT: ResponseCodes  # value = <ResponseCodes.NO_CONTENT: 204>
OK: ResponseCodes  # value = <ResponseCodes.OK: 200>
ORIGIN_IS_UNREACHABLE: ResponseCodes  # value = <ResponseCodes.ORIGIN_IS_UNREACHABLE: 523>
PARTIAL_CONTENT: ResponseCodes  # value = <ResponseCodes.PARTIAL_CONTENT: 206>
PAYLOAD_TOO_LARGE: ResponseCodes  # value = <ResponseCodes.PAYLOAD_TOO_LARGE: 413>
PAYMENT_REQUIRED: ResponseCodes  # value = <ResponseCodes.PAYMENT_REQUIRED: 402>
PERMANENT_REDIRECT: ResponseCodes  # value = <ResponseCodes.PERMANENT_REDIRECT: 308>
PRECONDITION_FAILED: ResponseCodes  # value = <ResponseCodes.PRECONDITION_FAILED: 412>
PRECONDITION_REQUIRED: ResponseCodes  # value = <ResponseCodes.PRECONDITION_REQUIRED: 428>
PROCESSING: ResponseCodes  # value = <ResponseCodes.PROCESSING: 102>
PROXY_AUTHENTICATION_REQUIRED: ResponseCodes  # value = <ResponseCodes.PROXY_AUTHENTICATION_REQUIRED: 407>
RANGE_NOT_SATISFIABLE: ResponseCodes  # value = <ResponseCodes.RANGE_NOT_SATISFIABLE: 416>
REQUEST_HEADER_FIELDS_TOO_LARGE: ResponseCodes  # value = <ResponseCodes.REQUEST_HEADER_FIELDS_TOO_LARGE: 431>
REQUEST_TIMEOUT: ResponseCodes  # value = <ResponseCodes.REQUEST_TIMEOUT: 408>
RESET_CONTENT: ResponseCodes  # value = <ResponseCodes.RESET_CONTENT: 205>
RETRY_WITH: ResponseCodes  # value = <ResponseCodes.RETRY_WITH: 449>
SEE_OTHER: ResponseCodes  # value = <ResponseCodes.SEE_OTHER: 303>
SERVICE_UNAVAILABLE: ResponseCodes  # value = <ResponseCodes.SERVICE_UNAVAILABLE: 503>
SSL_HANDSHAKE_FAILED: ResponseCodes  # value = <ResponseCodes.SSL_HANDSHAKE_FAILED: 525>
SWITCHING_PROTOCOLS: ResponseCodes  # value = <ResponseCodes.SWITCHING_PROTOCOLS: 101>
TEMPORARY_REDIRECT: ResponseCodes  # value = <ResponseCodes.TEMPORARY_REDIRECT: 307>
TOO_MANY_REQUESTS: ResponseCodes  # value = <ResponseCodes.TOO_MANY_REQUESTS: 429>
UNAUTHORIZED: ResponseCodes  # value = <ResponseCodes.UNAUTHORIZED: 401>
UNAVAILABLE_FOR_LEGAL_REASONS: ResponseCodes  # value = <ResponseCodes.UNAVAILABLE_FOR_LEGAL_REASONS: 451>
UNKNOWN_ERROR: ResponseCodes  # value = <ResponseCodes.UNKNOWN_ERROR: 520>
UNPROCESSABLE_ENTITY: ResponseCodes  # value = <ResponseCodes.UNPROCESSABLE_ENTITY: 422>
UNSUPPORTED_MEDIA_TYPE: ResponseCodes  # value = <ResponseCodes.UNSUPPORTED_MEDIA_TYPE: 415>
UPGRADE_REQUIRED: ResponseCodes  # value = <ResponseCodes.UPGRADE_REQUIRED: 426>
URI_TOO_LONG: ResponseCodes  # value = <ResponseCodes.URI_TOO_LONG: 414>
USE_PROXY: ResponseCodes  # value = <ResponseCodes.USE_PROXY: 305>
VARIANT_ALSO_NEGOTIATES: ResponseCodes  # value = <ResponseCodes.VARIANT_ALSO_NEGOTIATES: 506>
WEB_SERVER_IS_DOWN: ResponseCodes  # value = <ResponseCodes.WEB_SERVER_IS_DOWN: 521>
heavyOperationStateful: ExecutorType  # value = <ExecutorType.heavyOperationStateful: 2>
heavyOperationStateless: ExecutorType  # value = <ExecutorType.heavyOperationStateless: 3>
stateful: ExecutorType  # value = <ExecutorType.stateful: 0>
stateless: ExecutorType  # value = <ExecutorType.stateless: 1>
