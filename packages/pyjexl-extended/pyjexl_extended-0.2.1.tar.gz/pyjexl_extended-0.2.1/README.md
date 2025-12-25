
# PyJEXL-Extended

Python implementation of the JEXL expression language with **extended grammar**—over 80 built-in functions and transforms for strings, numbers, arrays, objects, dates, and more.

**NOTE:** This library is based on [TomFrost's JEXL](https://github.com/TomFrost/Jexl) and extends the original [mozilla/pyjexl](https://github.com/mozilla/pyjexl) with a rich set of features inspired by [jexl-extended](https://github.com/nikoraes/jexl-extended).


## Features

- 🚀 **80+ Built-in Functions & Transforms**: String manipulation, math, arrays, objects, dates, and more
- 🧩 **Modular Grammar**: Use the entire library or import individual functions
- 🐍 **Pythonic Semantics**: Type-safe, predictable behavior
- 🧪 **Extensible**: Add your own functions, transforms, and operators

---

📚 **Full Documentation:** [https://docs.konnektr.io/docs/jexl/](https://docs.konnektr.io/docs/jexl/)

## Quick Start

Install:

```bash
pip install pyjexl-extended
```

Basic usage:

```python
from pyjexl.jexl_extended import JexlExtended

context = {
    "users": [
        {"name": "John", "age": 32},
        {"name": "Jane", "age": 34},
        {"name": "Bob", "age": 33}
    ]
}

jexl = JexlExtended(context)
result = jexl.eval('users|filter("value.age > 32")|map("value.name")|join(", ")')
# "Jane, Bob"
```

## Extended Grammar Examples

- String: `"hello world"|uppercase` → `"HELLO WORLD"`
- Array: `[1,2,3]|sum` → `6`
- Object: `{foo:1, bar:2}|keys` → `['foo', 'bar']`
- Date: `now()` → ISO datetime string
- Math: `10.123456|round(2)` → `10.12`

See [jexl-extended](https://github.com/nikoraes/jexl-extended) for the full list of available functions and transforms.

## Playground

Try out expressions interactively:
- [JEXL Playground](https://nikoraes.github.io/jexl-playground/)

## Related Projects

- [jexl-extended (TypeScript)](https://github.com/nikoraes/jexl-extended) — The original extended grammar for JEXL
- [JexlNet (C#)](https://github.com/nikoraes/JexlNet) — C# implementation with extended grammar
- [PyJEXL (Mozilla)](https://github.com/mozilla/pyjexl) — Original Python JEXL parser
- [jexl-rs (Rust)](https://github.com/mozilla/jexl-rs) — Rust-based JEXL parser

## License

Licensed under the MIT License. See `LICENSE` for details.
