from prompt_injection_bench.defenses.base import DefenseAction
from prompt_injection_bench.defenses.llm_classifier import LLMClassifierDefense


class _FakeTextBlock:
    def __init__(self, text):
        self.text = text


class _FakeUsage:
    input_tokens = 42
    output_tokens = 3


class _FakeResponse:
    def __init__(self, text):
        self.content = [_FakeTextBlock(text)]
        self.usage = _FakeUsage()


class _FakeMessages:
    def __init__(self, reply_text):
        self._reply_text = reply_text
        self.calls = 0

    def create(self, **kwargs):
        self.calls += 1
        return _FakeResponse(self._reply_text)


class _FakeClient:
    def __init__(self, reply_text):
        self.messages = _FakeMessages(reply_text)


class _RaisingMessages:
    def create(self, **kwargs):
        raise ConnectionError("simulated outage")


class _RaisingClient:
    def __init__(self):
        self.messages = _RaisingMessages()


def test_classifier_blocks_when_model_says_injection():
    client = _FakeClient("INJECTION")
    defense = LLMClassifierDefense(client=client)
    result = defense.screen("some fetched content")
    assert result.action == DefenseAction.BLOCK
    assert result.flagged is True


def test_classifier_passes_when_model_says_clean():
    client = _FakeClient("CLEAN")
    defense = LLMClassifierDefense(client=client)
    result = defense.screen("some fetched content")
    assert result.action == DefenseAction.PASS
    assert result.flagged is False
    assert result.text == "some fetched content"


def test_classifier_fails_closed_on_malformed_response():
    client = _FakeClient("uh, maybe?")
    defense = LLMClassifierDefense(client=client)
    result = defense.screen("some fetched content")
    assert result.action == DefenseAction.BLOCK
    assert result.flagged is True


def test_classifier_fails_open_on_infra_error():
    client = _RaisingClient()
    defense = LLMClassifierDefense(client=client)
    result = defense.screen("some fetched content")
    assert result.action == DefenseAction.PASS
    assert result.flagged is False
