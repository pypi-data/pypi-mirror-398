from __future__ import annotations

import csv
import json
import struct
import sys
from abc import ABC, abstractmethod
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from acto.errors import TelemetryError
from acto.telemetry.models import TelemetryBundle, TelemetryEvent


class TelemetryParser(ABC):
    @abstractmethod
    def parse(
        self,
        path: str | Path,
        task_id: str,
        robot_id: str | None = None,
        run_id: str | None = None,
    ) -> TelemetryBundle:
        raise NotImplementedError


class JsonlTelemetryParser(TelemetryParser):
    def parse(
        self,
        path: str | Path,
        task_id: str,
        robot_id: str | None = None,
        run_id: str | None = None,
    ) -> TelemetryBundle:
        p = Path(path)
        if not p.exists():
            raise TelemetryError(f"Telemetry file not found: {p}")

        events: list[TelemetryEvent] = []
        with p.open("r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError as e:
                    raise TelemetryError(f"Invalid JSONL at line {idx + 1}: {e}") from e

                if "ts" not in obj or "topic" not in obj or "data" not in obj:
                    raise TelemetryError(f"Missing keys at line {idx + 1}: expected ts/topic/data")

                events.append(TelemetryEvent(ts=obj["ts"], topic=obj["topic"], data=obj["data"]))

        return TelemetryBundle(task_id=task_id, robot_id=robot_id, run_id=run_id, events=events, meta={})


class CsvTelemetryParser(TelemetryParser):
    def parse(
        self,
        path: str | Path,
        task_id: str,
        robot_id: str | None = None,
        run_id: str | None = None,
    ) -> TelemetryBundle:
        p = Path(path)
        if not p.exists():
            raise TelemetryError(f"Telemetry file not found: {p}")

        events: list[TelemetryEvent] = []
        with p.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader):
                if not row.get("ts") or not row.get("topic") or not row.get("data_json"):
                    raise TelemetryError(f"Missing columns at row {idx + 2}")
                try:
                    data = json.loads(row["data_json"])
                except json.JSONDecodeError as e:
                    raise TelemetryError(f"Invalid JSON in data_json at row {idx + 2}: {e}") from e

                events.append(TelemetryEvent(ts=row["ts"], topic=row["topic"], data=data))

        return TelemetryBundle(task_id=task_id, robot_id=robot_id, run_id=run_id, events=events, meta={})


class RosBagTelemetryParser(TelemetryParser):
    """Parser for ROS1/ROS2 Bag files."""

    def parse(
        self,
        path: str | Path,
        task_id: str,
        robot_id: str | None = None,
        run_id: str | None = None,
    ) -> TelemetryBundle:
        try:
            import rosbag2_py  # type: ignore[import-untyped]
        except ImportError:
            raise TelemetryError(
                "rosbag2_py not installed. Install with: pip install 'acto[ros]' or pip install rosbag2"
            ) from None

        p = Path(path)
        if not p.exists():
            raise TelemetryError(f"ROS bag file not found: {p}")

        events: list[TelemetryEvent] = []
        reader = rosbag2_py.SequentialReader()
        reader.open(str(p), storage_options={})

        topic_types_and_names = reader.get_all_topics_and_types()
        topic_to_type = {topic.name: topic.type for topic in topic_types_and_names}

        while reader.has_next():
            (topic, data, timestamp) = reader.read_next()
            # Convert nanosecond timestamp to ISO format
            ts_sec = timestamp / 1_000_000_000
            ts_iso = datetime.fromtimestamp(ts_sec, tz=timezone.utc).isoformat()

            # Try to deserialize the message
            try:
                # For ROS2: Try to extract message as JSON-like dict
                # This is a simplified implementation
                # In a full implementation, one would use ROS2 message types
                data_dict = self._extract_ros_message_data(data, topic_to_type.get(topic, ""))
            except Exception as e:
                # Fallback: Use raw bytes as base64
                import base64

                data_dict = {"raw_bytes": base64.b64encode(data).decode("utf-8"), "error": str(e)}

            events.append(TelemetryEvent(ts=ts_iso, topic=topic, data=data_dict))

        reader.close()

        return TelemetryBundle(task_id=task_id, robot_id=robot_id, run_id=run_id, events=events, meta={})

    def _extract_ros_message_data(self, data: bytes, msg_type: str) -> dict[str, Any]:
        """Extract data from ROS message (simplified implementation)."""
        # This is a simplified implementation
        # A full implementation would use ROS2 message types
        try:
            # Try to parse as JSON (if message is already serialized)
            return json.loads(data.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Fallback: Use raw bytes
            import base64

            return {"raw_bytes": base64.b64encode(data).decode("utf-8"), "msg_type": msg_type}


class ProtobufTelemetryParser(TelemetryParser):
    """Parser for Protobuf-formatted telemetry files."""

    def parse(
        self,
        path: str | Path,
        task_id: str,
        robot_id: str | None = None,
        run_id: str | None = None,
        message_type: type | None = None,
    ) -> TelemetryBundle:
        try:
            from google.protobuf.json_format import MessageToDict  # type: ignore[import-untyped]
        except ImportError:
            raise TelemetryError(
                "protobuf not installed. Install with: pip install 'acto[protobuf]' or pip install protobuf"
            ) from None

        p = Path(path)
        if not p.exists():
            raise TelemetryError(f"Protobuf file not found: {p}")

        events: list[TelemetryEvent] = []
        with p.open("rb") as f:
            # Protobuf files can have various formats
            # We support a simple format: length-prefixed messages
            while True:
                # Read message length (4 bytes, big-endian)
                length_bytes = f.read(4)
                if not length_bytes or len(length_bytes) < 4:
                    break

                length = struct.unpack(">I", length_bytes)[0]
                if length == 0:
                    break

                # Read the message
                msg_bytes = f.read(length)
                if len(msg_bytes) < length:
                    raise TelemetryError("Unexpected end of file while reading protobuf message")

                try:
                    if message_type:
                        msg = message_type()
                        msg.ParseFromString(msg_bytes)
                        data = MessageToDict(msg)
                    else:
                        # Fallback: Use raw bytes
                        import base64

                        data = {"raw_bytes": base64.b64encode(msg_bytes).decode("utf-8")}

                    # Use current timestamp since Protobuf messages don't have one
                    ts_iso = datetime.now(timezone.utc).isoformat()
                    events.append(TelemetryEvent(ts=ts_iso, topic="protobuf", data=data))
                except Exception as e:
                    raise TelemetryError(f"Failed to parse protobuf message: {e}") from e

        return TelemetryBundle(task_id=task_id, robot_id=robot_id, run_id=run_id, events=events, meta={})


class StreamTelemetryParser(TelemetryParser):
    """Parser for real-time stream processing."""

    def __init__(self):
        self._buffer: list[TelemetryEvent] = []
        self._closed = False

    def parse(
        self,
        path: str | Path,
        task_id: str,
        robot_id: str | None = None,
        run_id: str | None = None,
    ) -> TelemetryBundle:
        """Parse from a stream (e.g., stdin or named pipe)."""
        p = Path(path)
        if not p.exists() and str(path) != "-":
            raise TelemetryError(f"Stream source not found: {p}")

        events: list[TelemetryEvent] = []
        source = sys.stdin if str(path) == "-" else p.open("r", encoding="utf-8")

        try:
            for line in source:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    # For streams: skip invalid lines instead of erroring for robustness
                    continue

                if "ts" not in obj or "topic" not in obj or "data" not in obj:
                    continue

                events.append(TelemetryEvent(ts=obj["ts"], topic=obj["topic"], data=obj["data"]))
        finally:
            if source != sys.stdin:
                source.close()

        return TelemetryBundle(task_id=task_id, robot_id=robot_id, run_id=run_id, events=events, meta={})

    def parse_stream(
        self, stream: Iterator[str], task_id: str, robot_id: str | None = None, run_id: str | None = None
    ) -> Iterator[TelemetryEvent]:
        """Parse from an iterator stream (for real-time processing)."""
        for line in stream:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            if "ts" not in obj or "topic" not in obj or "data" not in obj:
                continue

            yield TelemetryEvent(ts=obj["ts"], topic=obj["topic"], data=obj["data"])

    def add_event(self, event: TelemetryEvent) -> None:
        """Add an event to the stream (for real-time processing)."""
        if self._closed:
            raise TelemetryError("Stream parser is closed")
        self._buffer.append(event)

    def flush(
        self, task_id: str, robot_id: str | None = None, run_id: str | None = None
    ) -> TelemetryBundle:
        """Create a bundle from buffered events."""
        bundle = TelemetryBundle(
            task_id=task_id, robot_id=robot_id, run_id=run_id, events=list(self._buffer), meta={}
        )
        self._buffer.clear()
        return bundle

    def close(self) -> None:
        """Close the stream parser."""
        self._closed = True
