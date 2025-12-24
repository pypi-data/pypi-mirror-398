# LangPy

**Write Python in your native language** 🌍

LangPy is a lexical layer over Python that lets you write code using keywords in human languages, without changing Python's behavior.

```python
# ejemplo.pyes (Spanish)
definir saludar(nombre):
    si nombre == "Ana":
        imprimir("Hola Ana")
    sino:
        imprimir("Hola", nombre)

saludar("Luis")
```

```bash
$ langpy ejemplo.pyes
Hola Luis
```

## Why LangPy?

LangPy makes Python more accessible to non-English speakers by allowing you to use natural language keywords while keeping everything else exactly the same.

### What LangPy IS ✅

- A **lexical transpiler** that translates keywords to Python
- **100% compatible** with Python libraries and tools
- **Zero runtime overhead** - executes as native Python
- **Easy migration** path back to pure Python

### What LangPy is NOT ❌

- NOT a new programming language
- NOT a custom interpreter or VM
- NOT translating error messages or APIs
- NOT changing Python's semantics

**If something crosses these boundaries, it's out of scope.**

## Quick Start

### Installation

Requirements: Python 3.10+

```bash
pip install langpy
```

### Your First Program

Create a file `hello.pyes`:

```python
definir main():
    nombre = "World"
    imprimir(f"Hello {nombre}!")

main()
```

Run it:

```bash
langpy hello.pyes
```

That's it! LangPy transpiles your code to standard Python and executes it immediately.

## Supported Languages

| Language   | Extension | Keywords Example                     |
| ---------- | --------- | ------------------------------------ |
| Spanish    | `.pyes`   | `definir`, `si`, `sino`, `imprimir`  |
| Portuguese | `.pypt`   | `definir`, `se`, `senao`, `imprimir` |
| French     | `.pyfr`   | `definir`, `si`, `sinon`, `imprimer` |

The language is determined **solely by the file extension**. No flags or configuration needed.

## Real-World Example

LangPy works seamlessly with local imports and external libraries.

**operations.pyes**

```python
definir suma(a, b):
    retornar a + b

definir resta(a, b):
    retornar a - b
```

**main.pyes**

```python
desde operations importar suma, resta
importar numpy como np

definir analizar_datos():
    # Use your functions
    resultado = suma(10, 5)
    imprimir(f"Suma: {resultado}")

    # Use any Python library
    datos = np.array([1, 2, 3, 4, 5])
    imprimir(f"Media: {np.mean(datos)}")

analizar_datos()
```

Run it:

```bash
langpy main.pyes
```

## How It Works

```
.pyes / .pypt / .pyfr file
        ↓
tokenize (Python stdlib)
        ↓
keyword replacement
        ↓
untokenize
        ↓
execute with Python VM
```

### Key Design Principles

- Only `NAME` tokens are translated (keywords)
- Strings and comments remain unchanged
- Attribute names are preserved (`obj.method`)
- No custom AST or parser
- If Python can't tokenize it, neither can LangPy

## CLI Usage

### Execute directly

```bash
langpy script.pyes
```

### Transpile to Python

```bash
langpy --transpile script.pyes
```

This generates standard `.py` files that you can run with `python`.

### Force overwrite

```bash
langpy --transpile --force script.pyes
```

### Get help

```bash
langpy --help
langpy --version
```

## Project Status

**Version:** 0.1.3

- ✅ Stable transpilation core
- ✅ Language lexicons defined
- ✅ Fully functional CLI
- ✅ Comprehensive test suite
- ✅ Clear project scope

## Contributing

LangPy's lexicon system is modular, making it easy to add new languages without modifying the core. Want to add your language? We'd love to have you contribute!

## License

MIT

---

**Made with ❤️ for the global Python community**
