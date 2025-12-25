import os

from typing import Optional, cast
from uuid import uuid4

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor


class ArcbeamLangConnector:
    def __init__(
        self,
        project_id: Optional[str] = None,
        run_id: Optional[str] = None,
        environment: str = "dev",
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.base_url = base_url or os.getenv("ARCBEAM_BASE_URL") or "https://platform.arcbeam.ai"
        self.api_key = api_key or os.getenv("ARCBEAM_API_KEY") or ""
        self.environment = os.getenv("ARCBEAM_ENV", environment)
        self.project_id = project_id or os.getenv("ARCBEAM_PROJECT_ID")
        self.run_id = run_id or os.getenv("ARCBEAM_RUN_ID") or str(uuid4())

    def init(
        self,
    ):
        os.environ["LANGSMITH_OTEL_ENABLED"] = "true"
        os.environ["LANGSMITH_TRACING"] = "true"
        os.environ["LANGSMITH_OTEL_ONLY"] = "true"

        resources = {
            "arcbeam.framework": "langchain",
            "arcbeam.environment": self.environment,
            "arcbeam.run_id": self.run_id,
        }

        if self.project_id:
            resources["arcbeam.project_id"] = self.project_id

        # Configure the OTLP exporter for your custom endpoint
        otlp_exporter = OTLPSpanExporter(
            # Point to the /api/v1/traces endpoint
            endpoint=f"{self.base_url}/api/v0/traces",
            # Add any required headers for authentication if needed
            headers={"arcbeam-api-key": self.api_key},
        )

        processor = SimpleSpanProcessor(otlp_exporter)

        default_provider = cast(TracerProvider, trace.get_tracer_provider())

        if isinstance(default_provider, trace.ProxyTracerProvider):
            provider = TracerProvider(resource=Resource.create(resources))
            # provider = TracerProvider(
            #     resource=resource,
            #     sampler=TraceIdRatioBased(sample_rate)
            #     if sample_rate is not None and sample_rate < 1
            #     else None,
            # )
            provider.add_span_processor(processor)
            trace.set_tracer_provider(provider)

        # elif "arcbeam.framework" not in default_provider.resource.attributes:
        else:
            provider = default_provider
            updated_resource = default_provider.resource.merge(Resource.create(resources))
            default_provider._resource = updated_resource
