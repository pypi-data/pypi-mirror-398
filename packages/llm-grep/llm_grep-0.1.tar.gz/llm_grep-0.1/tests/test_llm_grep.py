from click.testing import CliRunner
import re
import llm
import llm_grep
from llm.cli import cli


class FakeResponse:
    def __init__(self, text):
        self._text = text

    def text(self):
        return self._text


class FakeModel:
    needs_key = False
    key = None

    def __init__(self, responses):
        self._responses = responses
        self.calls = []

    def prompt(self, prompt, system):
        match = re.search(r"Query:\n(.*?)\n\nText:\n(.*?)\n", prompt, re.DOTALL)
        if match:
            query = match.group(1)
            span = match.group(2)
        else:
            query = ""
            span = ""
        self.calls.append((query, span))
        answer = self._responses.get((query, span), False)
        return FakeResponse("yes" if answer else "no")


def _ensure_grep_registered():
    if "grep" not in cli.commands:
        llm_grep.register_commands(cli)


def test_grep_matches_semantic_query(monkeypatch):
    _ensure_grep_registered()
    responses = {
        ("fruit", "apple"): True,
        ("fruit", "banana"): True,
        ("fruit", "carrot"): False,
    }
    fake = FakeModel(responses)
    monkeypatch.setattr(llm, "get_model", lambda model=None: fake)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["grep", "-e", "{{\\w+}}<fruit>"],
        input="apple\ncarrot\nbanana\n",
    )

    assert result.exit_code == 0, result.output
    assert result.output == "apple\nbanana\n"


def test_grep_invert_match(monkeypatch):
    _ensure_grep_registered()
    responses = {
        ("fruit", "apple"): True,
        ("fruit", "banana"): True,
        ("fruit", "carrot"): False,
    }
    fake = FakeModel(responses)
    monkeypatch.setattr(llm, "get_model", lambda model=None: fake)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["grep", "-e", "{{\\w+}}<fruit>", "-v"],
        input="apple\ncarrot\nbanana\n",
    )

    assert result.exit_code == 0, result.output
    assert result.output == "carrot\n"


def test_grep_ignore_case(monkeypatch):
    _ensure_grep_registered()
    responses = {
        ("fruit", "Apple"): True,
    }
    fake = FakeModel(responses)
    monkeypatch.setattr(llm, "get_model", lambda model=None: fake)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["grep", "-e", "{{apple}}<fruit>", "-i"],
        input="Apple\n",
    )

    assert result.exit_code == 0, result.output
    assert result.output == "Apple\n"


def test_grep_line_number_and_max_matches(monkeypatch):
    _ensure_grep_registered()
    responses = {
        ("fruit", "apple"): True,
        ("fruit", "banana"): True,
        ("fruit", "cherry"): True,
    }
    fake = FakeModel(responses)
    monkeypatch.setattr(llm, "get_model", lambda model=None: fake)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["grep", "-e", "{{\\w+}}<fruit>", "-n", "--max-matches", "2"],
        input="apple\nbanana\ncherry\n",
    )

    assert result.exit_code == 0, result.output
    assert result.output == "1:apple\n2:banana\n"


def test_grep_oracle_cache(monkeypatch):
    _ensure_grep_registered()
    responses = {
        ("fruit", "apple"): True,
    }
    fake = FakeModel(responses)
    monkeypatch.setattr(llm, "get_model", lambda model=None: fake)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["grep", "-e", "{{apple}}<fruit>"],
        input="apple\napple\n",
    )

    assert result.exit_code == 0, result.output
    assert result.output == "apple\napple\n"
    assert fake.calls == [("fruit", "apple")]


def test_grep_prompt_template_requires_fields(monkeypatch):
    _ensure_grep_registered()
    fake = FakeModel({})
    monkeypatch.setattr(llm, "get_model", lambda model=None: fake)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["grep", "-e", "{{apple}}<fruit>", "--prompt", "missing placeholders"],
        input="apple\n",
    )

    assert result.exit_code != 0
    assert 'Oracle prompt template must include both "{query}" and "{span}".' in result.output
