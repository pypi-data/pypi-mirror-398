from janus import JanusClient, AsyncJanusClient, janus_guard, openai_guard


def test_imports():
    assert JanusClient
    assert AsyncJanusClient
    assert callable(janus_guard)
    assert callable(openai_guard)
