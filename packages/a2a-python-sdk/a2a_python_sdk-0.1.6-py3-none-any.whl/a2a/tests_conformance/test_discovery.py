from a2a.discovery.well_known import WellKnownDiscovery


def test_discovery_strategy_interface():
    assert hasattr(WellKnownDiscovery, "discover")
