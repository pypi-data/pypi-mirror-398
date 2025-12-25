from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, ValidationError

from acto.errors import TelemetryError
from acto.telemetry.models import TelemetryBundle, TelemetryEvent


class TelemetrySchema(BaseModel):
    """Schema for telemetry validation."""

    required_fields: list[str] = Field(default_factory=lambda: ["ts", "topic", "data"])
    topic_pattern: str | None = None
    data_schema: dict[str, Any] | None = None
    max_events: int | None = None
    min_events: int = 0

    def validate_event(self, event: TelemetryEvent) -> None:
        """Validate a single telemetry event."""
        # Check required fields
        if not event.ts:
            raise TelemetryError("Event missing required field: ts")
        if not event.topic:
            raise TelemetryError("Event missing required field: topic")
        if event.data is None:
            raise TelemetryError("Event missing required field: data")

        # Check topic pattern (if defined)
        if self.topic_pattern:
            import re

            if not re.match(self.topic_pattern, event.topic):
                raise TelemetryError(f"Event topic '{event.topic}' does not match pattern '{self.topic_pattern}'")

        # Check data schema (if defined)
        if self.data_schema:
            try:
                # Use Pydantic for schema validation
                schema_model = self._create_schema_model(self.data_schema)
                schema_model.model_validate(event.data)
            except ValidationError as e:
                raise TelemetryError(f"Event data does not match schema: {e}") from e

    def validate_bundle(self, bundle: TelemetryBundle) -> None:
        """Validate a telemetry bundle."""
        # Check event count
        event_count = len(bundle.events)
        if event_count < self.min_events:
            raise TelemetryError(f"Bundle has {event_count} events, minimum required: {self.min_events}")
        if self.max_events and event_count > self.max_events:
            raise TelemetryError(f"Bundle has {event_count} events, maximum allowed: {self.max_events}")

        # Validate each event
        for idx, event in enumerate(bundle.events):
            try:
                self.validate_event(event)
            except TelemetryError as e:
                raise TelemetryError(f"Validation failed for event {idx}: {e}") from e

    def _create_schema_model(self, schema: dict[str, Any]) -> type[BaseModel]:
        """Create a Pydantic model from a schema dict."""
        # Simplified implementation: dynamically create a Pydantic model
        # In a full implementation, one would use JSON Schema
        fields: dict[str, Any] = {}
        for key, value in schema.items():
            if isinstance(value, type):
                fields[key] = (value, ...)
            elif isinstance(value, dict):
                # Recursive schema creation
                nested_model = self._create_schema_model(value)
                fields[key] = (nested_model, ...)
            elif hasattr(value, "__origin__"):
                # Handle typing objects like Optional, List, etc.
                fields[key] = (value, ...)
            else:
                fields[key] = (Any, ...)

        return type("SchemaModel", (BaseModel,), fields)


def validate_telemetry(bundle: TelemetryBundle, schema: TelemetrySchema | None = None) -> None:
    """Validate a telemetry bundle against a schema."""
    if schema is None:
        # Default validation: only basic checks
        schema = TelemetrySchema()
    schema.validate_bundle(bundle)

