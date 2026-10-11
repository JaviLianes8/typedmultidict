# typedmultidict

Pure-Python typed ordered multi-value dictionary with a case-insensitive variant.

## Install

```
pip install typedmultidict
```

## Usage

```python
from typedmultidict import MultiDict, CIMultiDict

params: MultiDict[str, str] = MultiDict()
params.add("tag", "python")
params.add("tag", "typing")

params["tag"]           # "python"  (first value)
params.getall("tag")    # ["python", "typing"]
len(params)             # 1  (distinct keys)
list(params.allitems()) # [("tag", "python"), ("tag", "typing")]  (every pair)

params["tag"] = "only"  # replaces every value for the key
params.getall("tag")    # ["only"]

# Case-insensitive headers that remember their original casing.
headers: CIMultiDict[str] = CIMultiDict()
headers.add("Content-Type", "text/html")
headers["content-type"]       # "text/html"
list(headers)                 # ["Content-Type"]
```

`MultiDict` implements the standard `MutableMapping` interface, so the familiar operations
(`[]`, `in`, `get`, `items`, iteration, `len`) work on the first value of each key, while
`add`, `getall`, `popall`, `extend` and `allitems` expose the full multi-value surface in
insertion order.

## Why

HTTP headers and query strings routinely carry repeated keys, so a mapping that keeps every
value is a common need. The existing options each fall short for a plain, typed project:

- `multidict` (the aiohttp one) is a C extension; its pure-Python fallback runs many times
  slower and still needs a build step for the fast path.
- `orderedmultidict` depends on `six` and ships no type hints.
- The `MultiDict` types in `werkzeug` and `starlette` come bundled with a whole framework.

`typedmultidict` is a single, standalone, fully typed implementation with `py.typed`, zero
runtime dependencies and no compilation. Reach for it when you want multi-value semantics
and `mypy --strict` support without pulling in a framework or a native wheel.

## License

MIT. See [LICENSE](LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
