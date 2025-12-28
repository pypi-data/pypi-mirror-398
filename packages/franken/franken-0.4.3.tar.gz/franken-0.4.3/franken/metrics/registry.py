import torch

from franken.metrics.base import BaseMetric


class MetricRegistry:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._metrics = {}
        return cls._instance

    def register(self, name: str, metric_class: type) -> None:
        """Register a metric class"""
        self._metrics[name] = metric_class

    def init_metric(
        self, name: str, device: torch.device, dtype: torch.dtype = torch.float32
    ) -> BaseMetric:
        """Create a new instance of a metric"""
        if name not in self._metrics:
            raise KeyError(
                f"Metric '{name}' not found. Available metrics: {list(self._metrics.keys())}"
            )
        return self._metrics[name](device=device, dtype=dtype)

    @property
    def available_metrics(self) -> list[str]:
        return list(self._metrics.keys())


registry = MetricRegistry()
