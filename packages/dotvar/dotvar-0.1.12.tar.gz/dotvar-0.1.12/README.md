# dotvar: Smarter Environment Variable Management for Python

`dotvar` is a Python module that improves upon traditional `.env` loaders by providing **automatic loading** and **native variable interpolation**, solving the major shortcomings of `python-dotenv`.

**Differences from `python-dotenv`:**

- ✅ **Built-in Interpolation**: Reference other variables within `.env`.
- ✅ **Option to Auto-load**: The option to load upon import, with no extra calls.
- ✅ **Strict Mode**: Catch missing `.env` files early.
- ✅ **No Dependencies**: Pure Python, standard library only.
- ✅ **Lightweight & Fast**: Minimal footprint, optimized load time.

## How to Use

1. place a `.env` in your current folder
2. you can run `load_env` or simply import `dotvar.auto_load` which has the side-effect of calling `load_env`
    ```python
    import dotvar.auto_load  # noqa
    ```
    Alternatively, there is also a `strict` mode, that raises an error if an environment file is not found.
    ```python
    import dotvar.auto_load_strict  # noqa
    ```

**Alternative syntax**

If the import side-effect is undesirable, you can import the `load_env` function and call it imperatively.
The import here will NOT have a side-effect.

```python
from dotvar import load_env

load_env(strict=False)
```
The strict flag defautls to False.

## The Problems with `python-dotenv`

While `python-dotenv` is widely used, it has two significant limitations:

1. It **does not support automatic loading** upon import.
2. It **lacks variable interpolation**, so environment variables cannot reference other variables within the same `.env` file.

For example, the following will not be correctly resolved using `python-dotenv`:

```env
BASE_URL=https://api.example.com
API_ENDPOINT=${BASE_URL}/v1/
```

```python
import os
print(os.environ.get("API_ENDPOINT"))  # Returns "${BASE_URL}/v1/" instead of the resolved value
```

---

### Introducing `dotvar`

`dotvar` solves these issues by:

- Supporting **native variable interpolation** with `${VAR_NAME}` syntax.
- Offering an **auto-load entrypoint**: just import `dotvar.auto_load`.
- Providing a **strict mode** (`dotvar.auto_load_strict`) that raises an error if `.env` is not found.

---

### Installation and Examples

```bash
pip install dotvar  # supports Python 3.7+
```

**An Example:**

Place a `.env` file in your project root:

```env
BASE_URL=https://api.example.com
API_ENDPOINT=${BASE_URL}/v1/
API_KEY=s3cr3t_api
```

Then in your Python code:

```python
# noinspection PyUnresolvedReferences
import dotvar.auto_load  # noqa

import os

print(os.environ["BASE_URL"])       # https://api.example.com
print(os.environ["API_ENDPOINT"])   # https://api.example.com/v1/
print(os.environ["API_KEY"])        # s3cr3t_api
```

To use strict mode:

```python
import dotvar.auto_load_strict  # noqa
```

---

## Development

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
# Set up environment
uv sync

# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=dotvar --cov-report=term-missing
```

---

## License

MIT License
