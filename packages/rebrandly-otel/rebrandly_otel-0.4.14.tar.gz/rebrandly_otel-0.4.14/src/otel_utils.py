
# otel_utils.py

import os
import sys
import grpc
import json
from typing import Optional

from opentelemetry.sdk.resources import Resource, SERVICE_NAMESPACE, DEPLOYMENT_ENVIRONMENT
from opentelemetry.semconv.attributes import service_attributes, telemetry_attributes
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.semconv._incubating.attributes import process_attributes, deployment_attributes

# Cache for endpoint validation results
_ENDPOINT_CACHE = {}

def create_resource(name: str = None, version: str = None) -> Resource:

    if name is None:
        name = get_service_name()
    if version is None:
        version = get_service_version()

    env = os.environ.get('ENV', os.environ.get('ENVIRONMENT', os.environ.get('NODE_ENV', 'local')))

    resources_attributes = {
        service_attributes.SERVICE_NAME: name,
        "application.name": name,
        service_attributes.SERVICE_VERSION: version,
        process_attributes.PROCESS_RUNTIME_VERSION: f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        SERVICE_NAMESPACE: get_application_name(),
        DEPLOYMENT_ENVIRONMENT: env,
        telemetry_attributes.TELEMETRY_SDK_LANGUAGE: "python",
        telemetry_attributes.TELEMETRY_SDK_NAME: "rebrandly-otel-sdk",
        telemetry_attributes.TELEMETRY_SDK_VERSION: version
    }

    if os.environ.get('OTEL_RESOURCE_ATTRIBUTES', None) is not None and os.environ.get('OTEL_RESOURCE_ATTRIBUTES', None).strip() != "":
        try:
            ora = os.environ.get('OTEL_RESOURCE_ATTRIBUTES')
            spl = ora.split(',')
            for attr in spl:
                attr = attr.strip()
                if attr != "" and '=' in attr:
                    # Split on first '=' only, in case value contains '='
                    k, v = attr.split('=', 1)
                    resources_attributes[k.strip()] = v.strip()
        except Exception as e:
            print(f"[OTEL Utils] Warning: Invalid OTEL_RESOURCE_ATTRIBUTES value: {e}")

    if os.environ.get('OTEL_REPO_NAME', None) is not None:
        resources_attributes['repository.name'] = os.environ.get('OTEL_REPO_NAME')

    if os.environ.get('OTEL_COMMIT_ID', None) is not None:
        resources_attributes[service_attributes.SERVICE_VERSION] = os.environ.get('OTEL_COMMIT_ID')

    resource = Resource.create(
        resources_attributes
    )
    return resource

def get_package_version():
    try:
        from importlib.metadata import version, PackageNotFoundError  # Python 3.8+
        return version('rebrandly_otel')
    except ImportError:
        try:
            from importlib_metadata import version, PackageNotFoundError
            return version('rebrandly_otel')
        except Exception as e:
            print(f"[OTEL Utils] Warning: Could not get package version: {e}")
            return '0.1.0'


def get_service_name(service_name: str = None) -> str:
    if service_name is None:
        serv = os.environ.get('OTEL_SERVICE_NAME', 'default-service-python')
        if serv.strip() == "":
            return 'default-service-python'
        return serv
    return service_name


def get_service_version(service_version: str = None) -> str:
    if service_version is None:
        return os.environ.get('OTEL_SERVICE_VERSION', get_package_version())
    return service_version


def get_application_name() -> str:
    return os.environ.get('OTEL_SERVICE_APPLICATION', get_service_name())


def get_otlp_endpoint(otlp_endpoint: str = None) -> Optional[str]:
    endpoint = otlp_endpoint or os.environ.get('OTEL_EXPORTER_OTLP_ENDPOINT', None)

    # Return cached result if available
    cache_key = endpoint if endpoint else '__none__'
    if cache_key in _ENDPOINT_CACHE:
        return _ENDPOINT_CACHE[cache_key]

    # Store the result to cache
    result = None

    if endpoint is not None:

        if endpoint.strip() == "":
            result = None
        else:
            try:
                from urllib.parse import urlparse

                # Parse the endpoint
                parsed = urlparse(endpoint if '://' in endpoint else f'http://{endpoint}')
                host = parsed.hostname
                port = parsed.port

                # Test gRPC connection
                channel = grpc.insecure_channel(f'{host}:{port}')
                try:
                    # Wait for the channel to be ready
                    grpc.channel_ready_future(channel).result(timeout=3)
                    result = endpoint
                finally:
                    channel.close()

            except grpc.FutureTimeoutError:
                print(f"[OTEL] Error: Connection timeout to OTLP endpoint {endpoint}. Check if the collector is running and accessible.")
                result = None
            except Exception as e:
                print(f"[OTEL] Error: Failed to connect to OTLP endpoint {endpoint}: {type(e).__name__}: {e}")
                print(f"[OTEL] Telemetry data will not be exported. Verify endpoint configuration and network connectivity.")
                result = None
    else:
        result = None

    # Cache the result
    _ENDPOINT_CACHE[cache_key] = result
    return result

def is_otel_debug() -> bool:
    return os.environ.get('OTEL_DEBUG', 'false').lower() == 'true'


def get_millis_batch_time():
    try:
        return int(os.environ.get('BATCH_EXPORT_TIME_MILLIS', 100))
    except Exception as e:
        print(f"[OTEL Utils] Warning: Invalid BATCH_EXPORT_TIME_MILLIS value, using default 5000ms: {e}")
        return 5000

def extract_event_from(message) -> Optional[str]:
    body = None
    if 'body' in message:
        body = message['body']
    if 'Body' in message:
        body = message['Body']
    if 'Message' in message:
        body = message['Message']
    if 'Sns' in message and 'Message' in message['Sns']:
        body = message['Sns']['Message']
    if body is not None:
        try:
            jbody = json.loads(body)
            if 'event' in jbody:
                return jbody['event']
        except:
            pass
    return None