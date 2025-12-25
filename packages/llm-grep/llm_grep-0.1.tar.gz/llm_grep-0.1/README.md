# llm-grep

[LLM](https://llm.datasette.io/) plugin for matching text using semantic regular expressions.
The high-level matching technique is loosely based on [this](https://arxiv.org/abs/2410.13262) paper.
Matching is done in two passes: one using traditional regular expressions to narrow down candidate matches, and a second pass using an LLM to filter those candidates based on any semantic tags.

The pattern syntax is similar to traditional regular expressions (enclosed in `{{` and `}}`), but adds semantic tags (enclosed in `<` and `>`) to indicate the type of concept being matched.

## Installation

Install this plugin in the same environment as LLM.
```bash
llm install llm-grep
```

## Usage

The plugin adds a new command, `llm grep`.
This command has an interface similar to the GNU `grep` command, but extends it with semantic matching capabilities, using an LLM as a matching oracle.

Input can be a standard file or `stdin`. Simple examples you can try:
```bash
# Match lines from a file
llm grep -e '^{{.*}}<about birds>$' notes.txt

# Read from standard input
cat recipes.txt | llm grep -e '^{{.*}}<baking related>$'

# Enable color, only output matched content, and use a custom model and prompt:
llm grep --color always -o -e '{{[A-Za-z0-9]+}}<outdoor activities>' --model gpt-4\
    --prompt 'Answer yes or no. Query: {query} Text: {span}.' headlines.txt

# Slightly more specific capture (will not match names like 'sparrow')
llm grep -e '\\b{{[A-Z][a-z]+(?:\\s+[A-Z][a-z]+)?}}<bird species>\\b' bird_log.txt
```

The default prompt used is:

> Does the following text satisfy the semantic concept described by the query?
> 
> Query:
> {query}
> 
> Text:
> {span}
> 
> Your answer should include "yes" or "no".

## Development

To set up this plugin locally, first checkout the code. Then create a new virtual environment:
```bash
cd llm-grep
python3 -m venv venv
source venv/bin/activate
```
Now install the dependencies and test dependencies:
```bash
pip install -e '.[test]'
```
To run the tests:
```bash
python -m pytest
```

## Future plans
- Currently, some of `grep`'s functionality is not implemented (e.g. `-r` for recursive searching).
  Re-implementing these features is a losing battle, and will be deprioritized in favor of somehow hooking into (or wrapping around) existing `grep` implementations.
