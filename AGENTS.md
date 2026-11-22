# AGENTS.md

## Overview

`typico` is a small, pure-Python introspection library for data models. It turns
Pydantic models, dataclasses and other `fieldz`-supported classes into a uniform
metadata layer (`PyField`, `PyModel`, `Constraints`), binds that metadata to model
instances (`FieldBinding`, `ModelBinding`) and offers abstract interfaces for
building UI form renderers on top. Runtime deps: `fieldz`, `pydantic`. Python >= 3.13.

## Architecture

Layout: `src/typico/` (uv_build, src layout).

- `pyfield/pyfield.py`: `PyField` dataclass (field metadata), `MISSING_VALUE` sentinel,
  `get_fields(model_class)`. `get_fields` iterates `fieldz.fields(...)` and calls
  `PyField.from_fieldz`, which delegates to `pydantic_adapter.to_pyfield` for
  `BaseModel` subclasses. Also contains default-value generation (`get_initial_value`).
- `pyfield/pydantic_adapter.py`: Pydantic-specific conversion (`to_pyfield`, `to_pymodel`).
  Reads `FieldInfo` and `model_json_schema()`; `to_pymodel` attaches a validator that
  runs `model_validate` and maps pydantic errors to `ValidationErrorDetail`s.
- `pyfield/dataclass_adapter.py`: dataclass `to_pymodel` and `get_dataclass_field_docs`
  (parses attribute docstrings from source via `ast` to fill `PyField.description`).
- `pyfield/pymodel.py`: `PyModel` (model metadata + optional `validator`),
  `PyModel.from_class` dispatches pydantic / dataclass / generic. `get_model` is an alias.
- `pyfield/constraints.py`: `Constraints` with `from_fieldz` and `from_jsonschema`.
- `pyfield/bindings.py`: `FieldBinding` (get/set value on an instance, basic constraint
  validation), `ModelBinding` (`validate()` uses `PyModel.validator` if present),
  `ModelValidationResult`, `ValidationErrorDetail`, `bind_model(instance)`.
- `ui/`: abstract UI layer. `UIWidgetRenderer[T]` (`base_renderer.py`, widget methods like
  `render_text_input`, `create_form_container`), `TypeHandler` (`base_type_handler.py`,
  maps a `PyField` to a renderer method name + kwargs), `FormRenderer`
  (`form_renderer.py`, picks handlers by priority and renders a bound model).
  No concrete UI backend ships here.
- `type_introspection.py`, `utils.py`, `log.py`: standalone helpers (typing predicates,
  pydantic `FieldInfo` helpers, `get_logger`). Not re-exported.
- `_xyz.py`: older, unused `PydanticField` prototype; not imported anywhere.

Public API (`typico/__init__.py`): `PyField`, `PyModel`, `Constraints`, `FieldBinding`,
`ModelBinding`, `get_fields`, `get_model`, `bind_model`.

## Where to look

| Task | File |
|------|------|
| Field metadata extraction (generic / dataclass) | `src/typico/pyfield/pyfield.py` (`from_fieldz`) |
| Pydantic field / model handling | `src/typico/pyfield/pydantic_adapter.py` |
| Dataclass docstrings, frozen detection | `src/typico/pyfield/dataclass_adapter.py` |
| Constraint mapping | `src/typico/pyfield/constraints.py` |
| Instance binding and validation | `src/typico/pyfield/bindings.py` |
| Model-level metadata / filtering | `src/typico/pyfield/pymodel.py` |
| UI renderer interfaces | `src/typico/ui/` |
| Public exports | `src/typico/__init__.py`, `src/typico/pyfield/__init__.py` |
| Tests | `tests/test_pyfield.py` |

## Commands

```bash
uv sync --all-extras                 # setup (default groups: dev, lint, docs)
uv run pytest                        # tests (duty: `duty test`)
uv run ruff check . && uv run ruff format --check .
uv run ty check                      # type check (src only); warnings fail CI
uv run deptry src                    # dependency hygiene
uv run mkdocs-mknodes build          # docs (duty: `duty build`, `duty serve`)
uv build
```

`duties.py` defines tasks for the `duty` runner (not a project dependency): `duty lint` runs ruff fix + format + ty; `duty lint_check` is the non-fixing variant.
CI (`.github/workflows/build.yml`) runs ruff, ty and pytest on 3.13/3.14 x
Linux/macOS/Windows (3.14 is `continue-on-error`). Docs: `.github/workflows/documentation.yml`.

## Conventions

- `from __future__ import annotations` everywhere; heavy/optional imports go under
  `TYPE_CHECKING` or inside functions (adapters import each other lazily to avoid cycles).
- Google-style docstrings; attribute docstrings (string literal below a field) on dataclasses.
- Ruff line length 100, preview formatting. ty is the type checker; use targeted
  `# ty: ignore[rule]` only for real checker limitations.
- Missing defaults are `MISSING_VALUE` (falsy sentinel), not `None`; use `PyField.has_default`.
- Custom widget hints travel as `Annotated[T, {"field_type": "..."}]` or
  `json_schema_extra={"field_type": ...}`; `field_type` is stripped from `metadata`.
- Tests are plain pytest functions in `tests/`.

## Pitfalls

- Copier-managed project (`.copier-answers.yml`, template `phil65/copier-phil65`): workflows,
  `duties.py`, `mkdocs.yml`, `.pre-commit-config.yaml` and most of `pyproject.toml` come from
  the template. Add dependencies only below the `# Only add below (Copier)` markers.
  ruff/ty versions are pinned in the `lint` group by the template; don't bump them here.
- `uv.lock` is gitignored.
- Pre-commit runs ruff, ty and pytest on commit.
- Docs use the mkdocs-mknodes default site: `docs/` is empty, the index page is `README.md`
  plus generated API pages. Keep README examples in sync with the code.
- `get_fields` on a pydantic model goes through `fieldz` first, then the pydantic adapter;
  changes to field extraction usually need to be made in both `from_fieldz` and `to_pyfield`.
