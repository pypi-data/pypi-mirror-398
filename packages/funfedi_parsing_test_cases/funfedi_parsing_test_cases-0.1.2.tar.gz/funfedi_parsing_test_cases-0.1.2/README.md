# funfedi_parsing_test_cases

This package is part of [funfedi.dev](https://funfedi.dev).
There are several goals here

- Make writing test cases more intuitive
- Allow more aspects of parsing to be tested, e.g. activities
- Provide mechanisms for automatic judgement of test cases as valid / invalid
- Enable generating good support table output

Not all aspects are implemented yet.

## Validators

Currently, implemented

* checking activities against a json-schema


## development

Run

```bash
uv run pytest
```

to run tests. In particular, by running

```bash
uv run pytest funfedi_parsing_test_cases/test_cases.py --verbose
```

one should be able to view all configured test cases.

### building docs

```bash
uv run python -m funfedi_parsing_test_cases
```

one can create the files in `docs/suites`. Then build the documentation with

```bash
uv run mkdocs serve
```
