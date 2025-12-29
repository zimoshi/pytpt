# TemPlaTing (TPT)

**Deterministic • AST-safe • Programmable Templates**

`pytpt` is a small, strict, and predictable template engine designed for **correctness-first rendering**.
It renders text (including HTML) safely and deterministically, without exposing Python internals.

---

## ✨ Why TPT?

Most template engines optimize for flexibility.
TPT optimizes for **correctness, safety, and tooling**.

* ✅ Deterministic output
* ✅ AST-safe expression evaluation (no `eval`)
* ✅ Explicit control flow
* ✅ Fail-fast validation (`assert`)
* ✅ First-class deferred rendering
* ✅ Script-friendly CLI

HTML is supported naturally — because HTML is just text.

---

## 📦 Installation

### 1️⃣ Install Pyp

Pyp is a tiny Python package installer.

> **Platform support**
>
> * ✅ macOS
> * ✅ Linux
> * ❌ Windows (not supported yet)

**macOS / Linux**

```bash
curl -fsSL https://pypsh.onrender.com/pyp.sh | bash
```

Verify installation:

```bash
pyp2 --version
```

> **Windows users**
> Use WSL or Docker until native Pyp support is available.

---

### 2️⃣ Install `pytpt`

From a local file:

```bash
pyp2 install pytpt.pyp
```

From a remote source:

```bash
pyp2 fetch pyp:zimoshi.github.io/pytpt:pytpt.pyp
```

---

## 🚀 CLI Usage

```bash
pytpt template.tpt context.json
```

Suppress the banner (recommended for scripts / CI):

```bash
pytpt template.tpt context.json --hide-banner
```

Show banner only:

```bash
pytpt --banner
```

---

## 🧠 Python API

```python
from pytpt import Renderer

tpl = "Hello {{ name | default('friend') | upper }}!"
out = Renderer(tpl).render({})
print(out)  # Hello FRIEND!
```

---

## 🧩 Template Syntax

### Variables

```jinja
Hello {{ user.name }}
```

### Filters

```jinja
{{ title | trim | upper }}
{{ name | default("guest") }}
```

### Conditionals

```jinja
{% if admin %}
ADMIN
{% else %}
USER
{% endif %}
```

### Loops

```jinja
{% for x in items %}
- {{ x }}
{% endfor %}
```

### Match / Case

```jinja
{% match status %}
  {% case 200 %}OK
  {% case 404 %}Not Found
  {% case _ %}Unknown
{% endmatch %}
```

### Assertions (fail fast)

```jinja
{% assert email "Email is required" %}
```

### Deferred Rendering (script / style hoisting)

```jinja
{% defer scripts %}
<script src="/app.js"></script>
{% enddefer %}

<footer>
{{ render_deferred("scripts", "\n") }}
</footer>
```

---

## 🧪 Safety Model

* No imports
* No `eval`
* No Python introspection
* Only whitelisted built-ins (`len`, `min`, `max`, etc.)
* Expressions evaluated via Python AST

Suitable for:

* CI/CD pipelines
* Config generation
* Code scaffolding
* Safe HTML rendering

---

## 📝 HTML Support

TPT renders HTML **without special modes**.

```html
<!doctype html>
<html>
  <body>
    <h1>Hello {{ user.name }}</h1>
  </body>
</html>
```

Whitespace trimming is explicit via `{%- -%}`.

---

## 📄 License

MCPL

---

## 🏁 Status

**Stable — v1.2.2**
