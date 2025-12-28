<p align="center">
  <a href="https://jcristharif.com/hyperspec/">
    <img src="https://raw.githubusercontent.com/jcrist/hyperspec/main/docs/_static/hyperspec-logo-light.svg" width="35%" alt="hyperspec">
  </a>
</p>

<div align="center">

[![CI](https://github.com/jcrist/hyperspec/actions/workflows/ci.yml/badge.svg)](https://github.com/jcrist/hyperspec/actions/workflows/ci.yml)
[![Documentation](https://img.shields.io/badge/docs-latest-blue.svg)](https://jcristharif.com/hyperspec/)
[![License](https://img.shields.io/github/license/jcrist/hyperspec.svg)](https://github.com/jcrist/hyperspec/blob/main/LICENSE)
[![PyPI Version](https://img.shields.io/pypi/v/hyperspec.svg)](https://pypi.org/project/hyperspec/)
[![Conda Version](https://img.shields.io/conda/vn/conda-forge/hyperspec.svg)](https://anaconda.org/conda-forge/hyperspec)
[![Code Coverage](https://codecov.io/gh/jcrist/hyperspec/branch/main/graph/badge.svg)](https://app.codecov.io/gh/jcrist/hyperspec)

</div>

`hyperspec` is a *fast* serialization and validation library, with builtin
support for [JSON](https://json.org), [MessagePack](https://msgpack.org),
[YAML](https://yaml.org), and [TOML](https://toml.io/en/). It features:

- 🚀 **High performance encoders/decoders** for common protocols. The JSON and
  MessagePack implementations regularly
  [benchmark](https://jcristharif.com/hyperspec/benchmarks.html) as the fastest
  options for Python.

- 🎉 **Support for a wide variety of Python types**. Additional types may be
  supported through
  [extensions](https://jcristharif.com/hyperspec/extending.html).

- 🔍 **Zero-cost schema validation** using familiar Python type annotations. In
  [benchmarks](https://jcristharif.com/hyperspec/benchmarks.html) `hyperspec`
  decodes *and* validates JSON faster than
  [orjson](https://github.com/ijl/orjson) can decode it alone.

- ✨ **A speedy Struct type** for representing structured data. If you already
  use [dataclasses](https://docs.python.org/3/library/dataclasses.html) or
  [attrs](https://www.attrs.org/en/stable/),
  [structs](https://jcristharif.com/hyperspec/structs.html) should feel familiar.
  However, they're
  [5-60x faster](https://jcristharif.com/hyperspec/benchmarks.html#structs)
  for common operations.

All of this is included in a
[lightweight library](https://jcristharif.com/hyperspec/benchmarks.html#library-size)
with no required dependencies.

---

`hyperspec` may be used for serialization alone, as a faster JSON or
MessagePack library. For the greatest benefit though, we recommend using
`hyperspec` to handle the full serialization & validation workflow:

**Define** your message schemas using standard Python type annotations.

```python
>>> import hyperspec

>>> class User(hyperspec.Struct):
...     """A new type describing a User"""
...     name: str
...     groups: set[str] = set()
...     email: str | None = None
```

**Encode** messages as JSON, or one of the many other supported protocols.

```python
>>> alice = User("alice", groups={"admin", "engineering"})

>>> alice
User(name='alice', groups={"admin", "engineering"}, email=None)

>>> msg = hyperspec.json.encode(alice)

>>> msg
b'{"name":"alice","groups":["admin","engineering"],"email":null}'
```

**Decode** messages back into Python objects, with optional schema validation.

```python
>>> hyperspec.json.decode(msg, type=User)
User(name='alice', groups={"admin", "engineering"}, email=None)

>>> hyperspec.json.decode(b'{"name":"bob","groups":[123]}', type=User)
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
hyperspec.ValidationError: Expected `str`, got `int` - at `$.groups[0]`
```

`hyperspec` is designed to be as performant as possible, while retaining some of
the nicities of validation libraries like
[pydantic](https://docs.pydantic.dev/latest/). For supported types,
encoding/decoding a message with `hyperspec` can be
[~10-80x faster than alternative libraries](https://jcristharif.com/hyperspec/benchmarks.html).

<p align="center">
  <a href="https://jcristharif.com/hyperspec/benchmarks.html">
    <img src="https://raw.githubusercontent.com/jcrist/hyperspec/main/docs/_static/bench-validation.svg">
  </a>
</p>

See [the documentation](https://jcristharif.com/hyperspec/) for more information.


## LICENSE

New BSD. See the
[License File](https://github.com/jcrist/hyperspec/blob/main/LICENSE).
