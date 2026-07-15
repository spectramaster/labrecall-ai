from labrecall.arm_benchmark import EndpointResult, compare, percentile


def test_percentile_uses_nearest_rank() -> None:
    values = [40.0, 10.0, 30.0, 20.0]
    assert percentile(values, 0.5) == 20.0
    assert percentile(values, 0.95) == 40.0


def test_comparison_does_not_overstate_client_latency_as_cost() -> None:
    arm = EndpointResult("arm64", "aarch64", 10, 10, 80.0, 75.0, 100.0)
    x86 = EndpointResult("x86_64", "x86_64", 10, 10, 100.0, 95.0, 130.0)
    report = compare(arm, x86)
    assert report["arm_mean_latency_change_percent"] == -20.0
    assert "not Lambda billed duration" in report["warning"]
