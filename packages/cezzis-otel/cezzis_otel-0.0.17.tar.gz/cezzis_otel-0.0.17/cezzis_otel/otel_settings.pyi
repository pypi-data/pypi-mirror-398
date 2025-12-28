from _typeshed import Incomplete

class OTelSettings:
    service_name: Incomplete
    service_namespace: Incomplete
    service_version: Incomplete
    environment: Incomplete
    instance_id: Incomplete
    otlp_exporter_endpoint: Incomplete
    otlp_exporter_auth_header: Incomplete
    enable_logging: Incomplete
    enable_tracing: Incomplete
    certificate_file: Incomplete
    client_certificate_file: Incomplete
    client_key_file: Incomplete
    enable_console_logging: Incomplete
    def __init__(self, service_name: str, service_namespace: str, service_version: str, otlp_exporter_endpoint: str, otlp_exporter_auth_header: str, environment: str, instance_id: str, enable_logging: bool = True, enable_tracing: bool = True, certificate_file: str | None = None, client_certificate_file: str | None = None, client_key_file: str | None = None, enable_console_logging: bool | None = False) -> None: ...
