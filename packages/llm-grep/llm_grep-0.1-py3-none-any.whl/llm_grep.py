import click
import llm
import sys
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Iterable


# Ask the oracle whether SPAN satisfies semantic concept QUERY.
# Keep it strictly boolean to support caching and determinism.
DEFAULT_ORACLE_PROMPT = """
Does the following text satisfy the semantic concept described by the query?

Query:
{query}

Text:
{span}

Your answer should include "yes" or "no".
""".strip()


@dataclass(frozen=True)
class SemGroup:
    name: str   # capture group name
    query: str  # semantic query string


@dataclass
class CompiledSemRE:
    # A Python regex that matches the skeleton and captures refined substrings.
    regex: re.Pattern
    sem_groups: List[SemGroup]


SEM_ATOM_RE = re.compile(
    r"\{\{(.*?)\}\}<(.+?)>",  # non-greedy for both; dotall handled by flags
    re.DOTALL,
)


def _compile_semre(expr: str, ignore_case: bool = False) -> CompiledSemRE:
    """
    Compile a limited semantic regex to a Python regex + a list of semantic-gated capture groups.

    Supported construct:
      {{REGEX}}<QUERY>    => capture REGEX as a named group gK, then require oracle(QUERY, group_text)=true.

    Everything else in `expr` is treated as a normal Python regex.
    """
    sem_groups: List[SemGroup] = []
    out_parts: List[str] = []
    pos = 0
    k = 0

    for m in SEM_ATOM_RE.finditer(expr):
        # Append literal regex between semantic atoms unchanged
        out_parts.append(expr[pos:m.start()])

        inner_regex = m.group(1)
        query = m.group(2).strip()

        group_name = f"g{k}"
        k += 1

        # Capture the inner regex as a named group
        out_parts.append(f"(?P<{group_name}>{inner_regex})")
        sem_groups.append(SemGroup(name=group_name, query=query))

        pos = m.end()

    out_parts.append(expr[pos:])
    skeleton = "".join(out_parts)

    flags = re.MULTILINE
    if ignore_case:
        flags |= re.IGNORECASE

    try:
        compiled = re.compile(skeleton, flags)
    except re.error as e:
        raise click.ClickException(f"Invalid (skeleton) regex after semantic regex expansion: {e}\nExpanded: {skeleton}")

    return CompiledSemRE(regex=compiled, sem_groups=sem_groups)


class OracleCache:
    """
    Cache oracle answers keyed by (query, span).
    """
    def __init__(self):
        self._cache: Dict[Tuple[str, str], bool] = {}

    def get(self, query: str, span: str) -> Optional[bool]:
        return self._cache.get((query, span))

    def put(self, query: str, span: str, value: bool) -> None:
        self._cache[(query, span)] = value


def _oracle_bool(
    model_obj,
    prompt_template: str,
    query: str,
    span: str,
    cache: OracleCache,
    system: str,
) -> bool:
    cached = cache.get(query, span)
    if cached is not None:
        return cached

    prompt = prompt_template.format(query=query, span=span)

    # Note: for LLM-backed oracles, you generally want deterministic settings + caching;
    # llm's model adapters differ, but caching alone already reduces repeated calls.
    text = model_obj.prompt(prompt, system=system).text().strip().lower()

    if "yes" in text:
        ans = True
    elif "no" in text:
        ans = False
    else:
        # Conservative default: treat anything else as "no" to avoid false positives.
        ans = False

    cache.put(query, span, ans)
    return ans


def _iter_lines(files: Tuple[click.File, ...]) -> Iterable[Tuple[str, str]]:
    """
    Yield (display_prefix, line) pairs.
    display_prefix includes filename if provided (grep-like).
    """
    if not files:
        for line in sys.stdin:
            yield ("", line.rstrip("\n"))
        return

    for f in files:
        name = getattr(f, "name", "")
        prefix = f"{name}:" if name and name != "<stdin>" else ""
        for line in f:
            yield (prefix, line.rstrip("\n"))


COLOR_MATCH_START = "\x1b[01;31m"
COLOR_MATCH_END = "\x1b[0m"


def _should_color(color: str) -> bool:
    if color == "always":
        return True
    if color == "never":
        return False
    return sys.stdout.isatty()


def _colorize_matches(line: str, matches: List[re.Match]) -> str:
    parts: List[str] = []
    last = 0
    for m in matches:
        start, end = m.span()
        parts.append(line[last:start])
        parts.append(f"{COLOR_MATCH_START}{line[start:end]}{COLOR_MATCH_END}")
        last = end
    parts.append(line[last:])
    return "".join(parts)


@llm.hookimpl
def register_commands(cli):
    @cli.command(context_settings=dict(ignore_unknown_options=True))
    @click.option(
        "-e", "--expr",
        help="Semantic regex (SemRE). Use {{REGEX}}<QUERY> for oracle refinements."
    )
    @click.option(
        "-m", "--model",
        help="LLM model to use as the oracle."
    )
    @click.option(
        "--prompt",
        help="Custom oracle prompt template. Must include {query} and {span}."
    )
    @click.option(
        "-i", "--ignore-case",
        is_flag=True,
        help="Case-insensitive matching for the syntactic (skeleton) regex."
    )
    @click.option(
        "-v", "--invert-match",
        is_flag=True,
        help="Select non-matching lines."
    )
    @click.option(
        "-o", "--only-matching",
        is_flag=True,
        help="Print only the matched parts of each line."
    )
    @click.option(
        "-n", "--line-number",
        is_flag=True,
        help="Prefix each matching line with its line number."
    )
    @click.option(
        "--max-matches",
        type=int,
        default=0,
        help="Stop after N matches (0 means no limit)."
    )
    @click.option(
        "--color",
        type=click.Choice(["auto", "always", "never"], case_sensitive=False),
        default="auto",
        show_default=True,
        help="Highlight matched parts of matching lines."
    )
    @click.option(
        "--system",
        default=DEFAULT_ORACLE_PROMPT,
        help="System prompt for the oracle."
    )
    @click.argument("pattern", required=False)
    @click.argument("files", type=click.File("r"), nargs=-1)
    def grep(expr, model, prompt, ignore_case, invert_match, only_matching, line_number, max_matches, color, system, pattern, files):
        r"""
Semantic grep using SemRE-style oracle refinements.

The engine is intentionally two-phase:
  1) Run a *purely syntactic* regex (the skeleton) to find candidate matches.
  2) For each candidate, discharge only the necessary oracle queries for the captured spans,
     with aggressive caching of (query, span) answers.

Semantic regex syntax supported:
  {{REGEX}}<QUERY>

Example:
  llm grep -e 'error {{\w+}}<is this a critical error?>' logs.txt
        """
        if expr:
            if pattern is not None:
                files = (click.open_file(pattern, "r"),) + files
        else:
            if pattern is None:
                raise click.ClickException("Missing PATTERN. Use -e or provide a positional pattern.")
            expr = pattern

        if invert_match and only_matching:
            raise click.ClickException("Cannot combine --invert-match with --only-matching.")

        compiled = _compile_semre(expr, ignore_case=ignore_case)
        use_color = _should_color(color)

        # Initialize model/oracle
        from llm import get_key
        model_obj = llm.get_model(model)
        if model_obj.needs_key:
            model_obj.key = get_key("", model_obj.needs_key, model_obj.key_env_var)

        prompt_template = prompt or DEFAULT_ORACLE_PROMPT
        if "{query}" not in prompt_template or "{span}" not in prompt_template:
            raise click.ClickException('Oracle prompt template must include both "{query}" and "{span}".')

        cache = OracleCache()

        matches = 0
        # Keep grep-like line numbering per file stream; stdin is a single stream.
        # For simplicity, count globally in the order we read.
        lineno = 0

        for prefix, line in _iter_lines(files):
            lineno += 1
            if not line:
                # grep defaults to skipping empty unless pattern matches empty;
                # allow it to run anyway because regex may match empty.
                pass

            ok_matches: List[re.Match] = []

            # Search for any match in the line (grep semantics), not fullmatch.
            for m in compiled.regex.finditer(line):
                # If there are semantic refinements, validate them via oracle.
                ok = True
                for sg in compiled.sem_groups:
                    span = m.group(sg.name) or ""
                    if not _oracle_bool(model_obj, prompt_template, sg.query, span, cache, system):
                        ok = False
                        break

                if ok:
                    ok_matches.append(m)

            line_matched = bool(ok_matches)
            if invert_match:
                line_matched = not line_matched

            if line_matched:
                matches += 1

                out_prefix = prefix
                if line_number:
                    out_prefix += f"{lineno}:"

                if only_matching:
                    for m in ok_matches:
                        match_text = m.group(0)
                        if use_color:
                            match_text = f"{COLOR_MATCH_START}{match_text}{COLOR_MATCH_END}"
                        click.echo(f"{out_prefix}{match_text}" if out_prefix else match_text)
                else:
                    if use_color and not invert_match and ok_matches:
                        line_out = _colorize_matches(line, ok_matches)
                    else:
                        line_out = line
                    click.echo(f"{out_prefix}{line_out}" if out_prefix else line_out)

                if max_matches > 0 and matches >= max_matches:
                    break
