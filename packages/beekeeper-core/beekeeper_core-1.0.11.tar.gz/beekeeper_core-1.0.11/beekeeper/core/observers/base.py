from beekeeper.core.monitors import BaseMonitor, PromptMonitor
from deprecated import deprecated


class BaseObserver(BaseMonitor):
    """DEPRECATED: An interface for observability."""


@deprecated(
    reason="'PromptObserver()' is deprecated and will be removed in a future version. Use 'PromptMonitor()' from 'beekeeper.core.monitors' instead.",
    version="1.0.4",
    action="always",
)
class PromptObserver(PromptMonitor):
    """DEPRECATED: Abstract base class defining the interface for prompt observability."""


@deprecated(
    reason="'ModelObserver()' is deprecated and will be removed in a future version. Use 'PromptMonitor()' from 'beekeeper.core.monitors' instead.",
    version="1.0.3",
    action="always",
)
class ModelObserver(PromptMonitor):
    """DEPRECATED: This class is deprecated and kept only for backward compatibility."""


@deprecated(
    reason="'TelemetryObserver()' is deprecated and will be removed in a future version. Use 'TelemetryMonitor()' from 'beekeeper.core.monitors' instead.",
    version="1.0.4",
    action="always",
)
class TelemetryObserver(BaseMonitor):
    """DEPRECATED: Abstract base class defining the interface for telemetry observability."""
