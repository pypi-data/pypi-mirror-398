"""Test to verify provider during actual pytest run."""


def test_verify_provider_class():
    """Verify that get_provider('mock') returns KaizenMockProvider during test."""
    from kailash.nodes.ai.ai_providers import PROVIDERS, get_provider

    # Check registry
    print(f"\nPROVIDERS['mock']: {PROVIDERS['mock']}")
    print(f"PROVIDERS['mock'] module: {PROVIDERS['mock'].__module__}")

    # Check get_provider
    provider = get_provider("mock")
    print(f"\nget_provider('mock') returned: {provider.__class__}")
    print(f"Provider module: {provider.__class__.__module__}")

    # Verify it's KaizenMockProvider
    assert (
        "kaizen" in provider.__class__.__module__.lower()
        or "Kaizen" in provider.__class__.__name__
    )
