# coze-coding-utils

Python utilities for the Coze coding client. Provides a simple runtime `Context` object.

## Installation

```bash
pip install coze-coding-utils
```

## Usage

```python
from coze_coding_utils.runtime_ctx.context import Context

ctx = Context(run_id="r", space_id="s", project_id="p", method="fetchData")
print(ctx.run_id, ctx.method)
```

## Python Version

Requires Python 3.10+.

## License

MIT
