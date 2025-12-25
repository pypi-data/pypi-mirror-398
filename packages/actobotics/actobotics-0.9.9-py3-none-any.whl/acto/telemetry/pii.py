from __future__ import annotations

import re
from typing import Any

from acto.telemetry.models import TelemetryBundle, TelemetryEvent


class PIIDetector:
    """Detects Personally Identifiable Information (PII) in telemetry data."""

    # Common PII patterns
    EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
    PHONE_PATTERN = re.compile(r"\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b")
    SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
    CREDIT_CARD_PATTERN = re.compile(r"\b\d{4}[-.\s]?\d{4}[-.\s]?\d{4}[-.\s]?\d{4}\b")
    IP_ADDRESS_PATTERN = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
    MAC_ADDRESS_PATTERN = re.compile(r"\b([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})\b")

    def __init__(self, custom_patterns: dict[str, re.Pattern] | None = None):
        """Initialize PII detector with optional custom patterns."""
        self.patterns = {
            "email": self.EMAIL_PATTERN,
            "phone": self.PHONE_PATTERN,
            "ssn": self.SSN_PATTERN,
            "credit_card": self.CREDIT_CARD_PATTERN,
            "ip_address": self.IP_ADDRESS_PATTERN,
            "mac_address": self.MAC_ADDRESS_PATTERN,
        }
        if custom_patterns:
            self.patterns.update(custom_patterns)

    def detect(self, text: str) -> dict[str, list[str]]:
        """Detect PII in text and return matches by type."""
        detected: dict[str, list[str]] = {}
        for pii_type, pattern in self.patterns.items():
            matches = pattern.findall(text)
            if matches:
                detected[pii_type] = list(set(matches))  # Remove duplicates
        return detected

    def detect_in_dict(self, data: dict[str, Any], path: str = "") -> dict[str, list[str]]:
        """Recursively detect PII in a dictionary structure."""
        detected: dict[str, list[str]] = {}
        for key, value in data.items():
            current_path = f"{path}.{key}" if path else key
            if isinstance(value, str):
                matches = self.detect(value)
                for pii_type, pii_matches in matches.items():
                    if pii_type not in detected:
                        detected[pii_type] = []
                    detected[pii_type].extend([f"{current_path}:{match}" for match in pii_matches])
            elif isinstance(value, dict):
                nested = self.detect_in_dict(value, current_path)
                for pii_type, pii_matches in nested.items():
                    if pii_type not in detected:
                        detected[pii_type] = []
                    detected[pii_type].extend(pii_matches)
            elif isinstance(value, list):
                for idx, item in enumerate(value):
                    if isinstance(item, str):
                        matches = self.detect(item)
                        for pii_type, pii_matches in matches.items():
                            if pii_type not in detected:
                                detected[pii_type] = []
                            detected[pii_type].extend(
                                [f"{current_path}[{idx}]:{match}" for match in pii_matches]
                            )
                    elif isinstance(item, dict):
                        nested = self.detect_in_dict(item, f"{current_path}[{idx}]")
                        for pii_type, pii_matches in nested.items():
                            if pii_type not in detected:
                                detected[pii_type] = []
                            detected[pii_type].extend(pii_matches)
        return detected


class PIIMasker:
    """Masks PII in telemetry data."""

    def __init__(self, mask_char: str = "*", preserve_length: bool = True):
        """Initialize PII masker.

        Args:
            mask_char: Character to use for masking
            preserve_length: Whether to preserve the original length when masking
        """
        self.mask_char = mask_char
        self.preserve_length = preserve_length
        self.detector = PIIDetector()

    def mask_string(self, text: str, pii_types: list[str] | None = None) -> str:
        """Mask PII in a string."""
        if pii_types is None:
            pii_types = list(self.detector.patterns.keys())

        masked_text = text
        for pii_type in pii_types:
            if pii_type in self.detector.patterns:
                pattern = self.detector.patterns[pii_type]
                matches = pattern.findall(masked_text)
                for match in matches:
                    if self.preserve_length:
                        replacement = self.mask_char * len(match)
                    else:
                        # Preserve some structure (e.g., keep first/last chars)
                        if len(match) > 4:
                            replacement = match[0] + self.mask_char * (len(match) - 2) + match[-1]
                        else:
                            replacement = self.mask_char * len(match)
                    masked_text = masked_text.replace(match, replacement)
        return masked_text

    def mask_dict(self, data: dict[str, Any], pii_types: list[str] | None = None) -> dict[str, Any]:
        """Recursively mask PII in a dictionary."""
        masked_data: dict[str, Any] = {}
        for key, value in data.items():
            if isinstance(value, str):
                masked_data[key] = self.mask_string(value, pii_types)
            elif isinstance(value, dict):
                masked_data[key] = self.mask_dict(value, pii_types)
            elif isinstance(value, list):
                masked_data[key] = [
                    self.mask_string(item, pii_types) if isinstance(item, str) else self.mask_dict(item, pii_types) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                masked_data[key] = value
        return masked_data

    def mask_event(self, event: TelemetryEvent, pii_types: list[str] | None = None) -> TelemetryEvent:
        """Mask PII in a telemetry event."""
        masked_data = self.mask_dict(event.data, pii_types)
        return TelemetryEvent(ts=event.ts, topic=event.topic, data=masked_data)

    def mask_bundle(self, bundle: TelemetryBundle, pii_types: list[str] | None = None) -> TelemetryBundle:
        """Mask PII in a telemetry bundle."""
        masked_events = [self.mask_event(event, pii_types) for event in bundle.events]
        return TelemetryBundle(
            task_id=bundle.task_id,
            robot_id=bundle.robot_id,
            run_id=bundle.run_id,
            events=masked_events,
            meta=bundle.meta,
        )


def detect_pii_in_bundle(bundle: TelemetryBundle) -> dict[str, list[str]]:
    """Convenience function to detect PII in a telemetry bundle."""
    detector = PIIDetector()
    detected: dict[str, list[str]] = {}
    for event in bundle.events:
        event_detected = detector.detect_in_dict(event.data)
        for pii_type, matches in event_detected.items():
            if pii_type not in detected:
                detected[pii_type] = []
            detected[pii_type].extend(matches)
    return detected

