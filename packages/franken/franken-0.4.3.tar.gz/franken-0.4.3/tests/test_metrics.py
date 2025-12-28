def test_registry_init():
    from franken.metrics.registry import registry

    assert hasattr(registry._instance, "_metrics")


def test_available_metrics():
    import franken.metrics as fm

    for name in ["energy_MAE", "forces_MAE", "forces_cosim"]:
        assert name in fm.available_metrics()


def test_register():
    import franken.metrics as fm
    from franken.metrics.base import BaseMetric

    class MockMetric(BaseMetric):
        pass

    assert "mock_metric" not in fm.available_metrics()
    fm.register("mock_metric", MockMetric)
    assert "mock_metric" in fm.available_metrics()


def test_init_metric():
    import torch

    import franken.metrics as fm
    from franken.metrics.base import BaseMetric

    class MockMetric(BaseMetric):
        def __init__(self, device: torch.device, dtype: torch.dtype = torch.float32):
            super().__init__("mock_metric", device, dtype)

    fm.register("mock_metric", MockMetric)
    metric = fm.init_metric("mock_metric", torch.device("cpu"))
    assert isinstance(metric, MockMetric)
