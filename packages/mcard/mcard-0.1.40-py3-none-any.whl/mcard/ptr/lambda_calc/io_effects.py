"""
IO Effects - Observable side-effects for Lambda Calculus computations

Implements the IO Monad pattern for CLM:
    IO a = World → (a, World')

In our context:
    Reduction = TermHash → (TermHash', IOEffects)

IO effects are purely observational - they do not affect computation results.
The same input will always produce the same output regardless of IO configuration.

This module provides Python parity with mcard-js/src/ptr/lambda/IOEffects.ts
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal, Optional

import requests

# ─────────────────────────────────────────────────────────────────────────────
# Types
# ─────────────────────────────────────────────────────────────────────────────

IOFormat = Literal["minimal", "verbose", "json"]


@dataclass
class NetworkConfig:
    """Network output configuration."""

    enabled: bool = False
    endpoint: Optional[str] = None
    method: str = "POST"
    headers: dict[str, str] = field(default_factory=dict)


@dataclass
class IOEffectsConfig:
    """Configuration for IO effects."""

    enabled: bool = False
    console: bool = True
    network: Optional[NetworkConfig] = None
    on_step: bool = False
    on_complete: bool = True
    on_error: bool = True
    format: IOFormat = "minimal"


@dataclass
class StepEvent:
    """Event emitted after each reduction step."""

    type: str = "step"
    step_number: int = 0
    term_hash: str = ""
    pretty_print: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class CompleteEvent:
    """Event emitted when normalization completes."""

    type: str = "complete"
    normal_form: str = ""
    pretty_print: str = ""
    total_steps: int = 0
    reduction_path: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ErrorEvent:
    """Event emitted on execution failure."""

    type: str = "error"
    message: str = ""
    partial_steps: int = 0
    last_term_hash: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


IOEvent = StepEvent | CompleteEvent | ErrorEvent


# ─────────────────────────────────────────────────────────────────────────────
# ANSI Colors
# ─────────────────────────────────────────────────────────────────────────────


class Colors:
    CYAN = "\033[36m"
    RED = "\033[31m"
    RESET = "\033[0m"


# ─────────────────────────────────────────────────────────────────────────────
# IO Effects Handler
# ─────────────────────────────────────────────────────────────────────────────


class IOEffectsHandler:
    """
    Handler for IO effects during lambda computation.

    Dispatches events to configured outputs (console, network, file).
    """

    def __init__(self, config: Optional[IOEffectsConfig] = None):
        self.config = config or IOEffectsConfig()
        self.events: list[IOEvent] = []

    def is_enabled(self) -> bool:
        """Check if IO effects are enabled."""
        return self.config.enabled

    def emit_step(self, step_number: int, term_hash: str, pretty_print: str) -> None:
        """Emit a step event."""
        if not self.config.enabled or not self.config.on_step:
            return

        event = StepEvent(
            step_number=step_number,
            term_hash=term_hash,
            pretty_print=pretty_print,
            timestamp=datetime.now(),
        )

        self.events.append(event)
        self._dispatch(event)

    def emit_complete(
        self,
        normal_form: str,
        pretty_print: str,
        total_steps: int,
        reduction_path: list[str],
    ) -> None:
        """Emit a completion event."""
        if not self.config.enabled or not self.config.on_complete:
            return

        event = CompleteEvent(
            normal_form=normal_form,
            pretty_print=pretty_print,
            total_steps=total_steps,
            reduction_path=reduction_path,
            timestamp=datetime.now(),
        )

        self.events.append(event)
        self._dispatch(event)

    def emit_error(
        self, message: str, partial_steps: int, last_term_hash: Optional[str] = None
    ) -> None:
        """Emit an error event."""
        if not self.config.enabled or not self.config.on_error:
            return

        event = ErrorEvent(
            message=message,
            partial_steps=partial_steps,
            last_term_hash=last_term_hash,
            timestamp=datetime.now(),
        )

        self.events.append(event)
        self._dispatch(event)

    def get_events(self) -> list[IOEvent]:
        """Get all collected events."""
        return list(self.events)

    def clear_events(self) -> None:
        """Clear collected events."""
        self.events = []

    def _dispatch(self, event: IOEvent) -> None:
        """Dispatch event to configured outputs."""
        formatted = self._format(event)

        # Console output
        if self.config.console:
            self._log_to_console(event, formatted)

        # Network output
        if self.config.network and self.config.network.enabled:
            self._send_to_network(event, formatted)

    def _format(self, event: IOEvent) -> str:
        """Format event for output."""
        if self.config.format == "json":
            return self._format_json(event)
        elif self.config.format == "verbose":
            return self._format_verbose(event)
        else:
            return self._format_minimal(event)

    def _format_minimal(self, event: IOEvent) -> str:
        """Format event as single line."""
        if isinstance(event, StepEvent):
            return f"[IO:step {event.step_number}] {event.pretty_print}"
        elif isinstance(event, CompleteEvent):
            return f"[IO:complete] {event.total_steps} steps → {event.pretty_print}"
        elif isinstance(event, ErrorEvent):
            return f"[IO:error] {event.message}"
        return ""

    def _format_verbose(self, event: IOEvent) -> str:
        """Format event with full context."""
        ts = event.timestamp.isoformat()

        if isinstance(event, StepEvent):
            return "\n".join(
                [
                    f"┌─ IO Effect: Reduction Step {event.step_number}",
                    f"│  Time: {ts}",
                    f"│  Hash: {event.term_hash[:16]}...",
                    f"│  Term: {event.pretty_print}",
                    "└─────────────────────────────────────────",
                ]
            )
        elif isinstance(event, CompleteEvent):
            return "\n".join(
                [
                    "╔═══════════════════════════════════════════",
                    "║ IO Effect: Normalization Complete",
                    "╠═══════════════════════════════════════════",
                    f"║ Time: {ts}",
                    f"║ Total Steps: {event.total_steps}",
                    f"║ Normal Form: {event.pretty_print}",
                    f"║ Hash: {event.normal_form[:16]}...",
                    "╚═══════════════════════════════════════════",
                ]
            )
        elif isinstance(event, ErrorEvent):
            return "\n".join(
                [
                    "╔═══════════════════════════════════════════",
                    "║ IO Effect: ERROR",
                    "╠═══════════════════════════════════════════",
                    f"║ Time: {ts}",
                    f"║ Message: {event.message}",
                    f"║ Partial Steps: {event.partial_steps}",
                    "╚═══════════════════════════════════════════",
                ]
            )
        return ""

    def _format_json(self, event: IOEvent) -> str:
        """Format event as JSON."""
        data = {"type": event.type, "timestamp": event.timestamp.isoformat()}

        if isinstance(event, StepEvent):
            data.update(
                {
                    "stepNumber": event.step_number,
                    "termHash": event.term_hash,
                    "prettyPrint": event.pretty_print,
                }
            )
        elif isinstance(event, CompleteEvent):
            data.update(
                {
                    "normalForm": event.normal_form,
                    "prettyPrint": event.pretty_print,
                    "totalSteps": event.total_steps,
                    "reductionPath": event.reduction_path,
                }
            )
        elif isinstance(event, ErrorEvent):
            data.update(
                {
                    "message": event.message,
                    "partialSteps": event.partial_steps,
                    "lastTermHash": event.last_term_hash,
                }
            )

        return json.dumps(data)

    def _log_to_console(self, event: IOEvent, formatted: str) -> None:
        """Log event to console with color."""
        if isinstance(event, ErrorEvent):
            print(f"{Colors.RED}{formatted}{Colors.RESET}")
        else:
            print(f"{Colors.CYAN}{formatted}{Colors.RESET}")

    def _send_to_network(self, event: IOEvent, formatted: str) -> None:
        """Send event to network endpoint."""
        if not self.config.network or not self.config.network.endpoint:
            return

        try:
            payload = {
                "event": event.type,
                "data": self._format_json(event),
                "formatted": formatted,
            }

            response = requests.request(
                method=self.config.network.method,
                url=self.config.network.endpoint,
                headers={
                    "Content-Type": "application/json",
                    **self.config.network.headers,
                },
                json=payload,
                timeout=5,
            )

            if not response.ok:
                print(f"IO network effect failed: {response.status_code}")
        except Exception as e:
            print(f"IO network effect error: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Factory and Utilities
# ─────────────────────────────────────────────────────────────────────────────


def create_io_handler(config: Optional[dict[str, Any]] = None) -> IOEffectsHandler:
    """
    Create an IO effects handler from CLM config.

    Args:
        config: Dictionary containing io_effects configuration

    Returns:
        IOEffectsHandler configured based on the input
    """
    if not config or not config.get("io_effects"):
        return IOEffectsHandler(IOEffectsConfig(enabled=False))

    io_config = config["io_effects"]

    # Parse network config if present
    network = None
    if io_config.get("network"):
        net_cfg = io_config["network"]
        network = NetworkConfig(
            enabled=net_cfg.get("enabled", False),
            endpoint=net_cfg.get("endpoint"),
            method=net_cfg.get("method", "POST"),
            headers=net_cfg.get("headers", {}),
        )

    return IOEffectsHandler(
        IOEffectsConfig(
            enabled=io_config.get("enabled", False),
            console=io_config.get("console", True),
            network=network,
            on_step=io_config.get("on_step", io_config.get("onStep", False)),
            on_complete=io_config.get("on_complete", io_config.get("onComplete", True)),
            on_error=io_config.get("on_error", io_config.get("onError", True)),
            format=io_config.get("format", "minimal"),
        )
    )


# No-op handler for when IO effects are disabled
noop_io_handler = IOEffectsHandler(IOEffectsConfig(enabled=False))
