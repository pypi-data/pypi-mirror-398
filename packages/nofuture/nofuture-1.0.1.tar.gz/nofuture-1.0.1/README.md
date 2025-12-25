# NoFuture

<img src="https://framagit.org/aristofor/nofuture/-/raw/main/NoFuture.svg" alt="NoFuture" width="160">

[![pipeline status](https://framagit.org/aristofor/nofuture/badges/v1.0.0/pipeline.svg)](https://framagit.org/aristofor/nofuture/-/commits/v1.0.0)

No futures. No exceptions. Just explicit values.

`MayBe` et `Result` pour Python, built en Rust (PyO3 + maturin).

```python
from nofut import MayBe, Result
```

## Installation

```bash
pip install nofuture
```

Dev mode: `maturin develop`

## MayBe

Valeur optionnelle: `Just(value)` ou `Nothing`.

```python
MayBe.just(42)      # Just(42)
MayBe.nothing()     # Nothing

# API
.is_just() / .is_nothing()
.unwrap()           # raise si Nothing
.or_else(default)   # valeur ou default
.map(fn)            # Just(fn(x)) ou Nothing
.flat_map(fn)       # fn doit retourner MayBe
>> fn               # flat_map
| default           # or_else
```

## Result

Succès ou erreur: `Ok(value)` ou `Err(message, code?, details?)`. La vie en binaire, avec du contexte.

```python
Result.ok(42)
Result.err("not found", code="NOT_FOUND")
Result.err("validation", code="INVALID", details={"field": "name"})

# API
.is_ok() / .is_err()
.unwrap()           # raise si Err
.unwrap_or(default) # valeur ou default
.unwrap_err()       # (msg, code, details) ou raise
.map(fn)            # Ok(fn(x)) ou Err passthrough
.map_err(fn)        # fn(msg, code, details) -> (msg, code, details)
.flat_map(fn)       # fn doit retourner Result
.and_then(fn)       # alias flat_map
.to_dict()          # {"ok": True, "value": ...} ou {"ok": False, "error": ...}
>> fn               # flat_map
| default           # unwrap_or
```

## Exemples

Exemples progressifs (basics -> objets -> pipeline Result).

```bash
python3 examples/base.py
python3 examples/abc.py
python3 examples/result.py
```

## Tests

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

## Licence

GPLv3 - voir [LICENSE](LICENSE)
