from openapi.batch.providers.registry import ProviderConfig, make_provider


def test_make_provider_local_echo():
    p = make_provider(ProviderConfig(provider="local_echo"))
    assert p.name == "local_echo"
