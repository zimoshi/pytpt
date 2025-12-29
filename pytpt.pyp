__pyp_name__ = "pytpt"
__pyp_ver__ = "1.2.2"
__pyp_deps__ = ""
__pyp_cli__ = True
__pyp_files__ = {
"__main__.py": """
from .renderer import Renderer

__all__ = ["Renderer"]

if __name__ == "__main__":
    import sys, json

    BANNER = r'''
 _____ ____ _____ 
|_   _|  _ \_   _|
  | | | |_) || |  
  | | |  __/ | |  
  |_| |_|    |_|  

TemPlaTing (TPT)
Deterministic • AST-safe • Programmable Templates
'''

    if "--banner" in sys.argv:
        print(BANNER)
        sys.exit(0)

    if "--version" in sys.argv:
        print("pytpt 1.2.2")
        sys.exit(0)

    hide_banner = "--hide-banner" in sys.argv
    argv = [a for a in sys.argv[1:] if a != "--hide-banner"]

    if len(argv) != 2:
        if not hide_banner:
            print(BANNER)
        print("Usage: pytpt [--hide-banner] <template-file> <context.json>")
        sys.exit(1)

    if not hide_banner:
        print(BANNER)

    with open(argv[0], "r", encoding="utf-8") as f:
        template = f.read()

    with open(argv[1], "r", encoding="utf-8") as f:
        ctx = json.load(f)

    print(Renderer(template).render(ctx))
""",

"__init__.py": """
from .renderer import Renderer

__all__ = ["Renderer"]

if __name__ == "__main__":
    import sys, json

    BANNER = r'''
 _____ ____ _____ 
|_   _|  _ \\_   _|
  | | | |_) || |  
  | | |  __/ | |  
  |_| |_|    |_|  

TemPlaTing (TPT)
Deterministic • AST-safe • Programmable Templates
'''

    if "--banner" in sys.argv:
        print(BANNER)
        sys.exit(0)

    if "--version" in sys.argv:
        print("pytpt 1.2.2")
        sys.exit(0)

    if len(sys.argv) != 3:
        print(BANNER)
        print("Usage: pytpt <template-file> <context.json>")
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        template = f.read()

    with open(sys.argv[2], "r", encoding="utf-8") as f:
        ctx = json.load(f)

    print(BANNER + Renderer(template).render(ctx))
""",

"errors.py": """
class TemplateError(Exception):
    pass
""",

"filters.py": """
DEFAULT_FILTERS = {
    "upper": lambda v: "" if v is None else str(v).upper(),
    "lower": lambda v: "" if v is None else str(v).lower(),
    "default": lambda v, d="": d if v in (None, "", False) else v,
    "len": lambda v: 0 if v is None else len(v),
    "trim": lambda v: "" if v is None else str(v).strip(),
}
""",

"safeeval.py": """
import ast
from .errors import TemplateError

class AttrDict(dict):
    __getattr__ = dict.get

SAFE_FUNCTIONS = {
    "len": len,
    "min": min,
    "max": max,
    "sum": sum,
    "any": any,
    "all": all,
}

def wrap_ctx(v):
    if isinstance(v, dict):
        return AttrDict({k: wrap_ctx(x) for k, x in v.items()})
    if isinstance(v, list):
        return [wrap_ctx(x) for x in v]
    return v

class SafeEval(ast.NodeVisitor):
    def __init__(self, ctx):
        self.ctx = ctx

    def visit_Expression(self, n): return self.visit(n.body)
    def visit_Constant(self, n): return n.value

    def visit_Name(self, n):
        if n.id in self.ctx: return self.ctx[n.id]
        if n.id in SAFE_FUNCTIONS: return SAFE_FUNCTIONS[n.id]
        return None

    def visit_Attribute(self, n):
        return getattr(self.visit(n.value), n.attr)

    def visit_Subscript(self, n):
        return self.visit(n.value)[self.visit(n.slice)]

    def visit_Tuple(self, n):
        return tuple(self.visit(e) for e in n.elts)

    def visit_Call(self, n):
        fn = self.visit(n.func)
        if fn not in SAFE_FUNCTIONS.values() and not callable(fn):
            raise TemplateError("Function not allowed")
        return fn(*[self.visit(a) for a in n.args],
                  **{kw.arg: self.visit(kw.value) for kw in n.keywords})

    def visit_Compare(self, n):
        left = self.visit(n.left)
        for op, r in zip(n.ops, n.comparators):
            right = self.visit(r)
            if isinstance(op, ast.Eq) and not left == right: return False
            if isinstance(op, ast.NotEq) and not left != right: return False
            if isinstance(op, ast.Gt) and not left > right: return False
            if isinstance(op, ast.Lt) and not left < right: return False
            if isinstance(op, ast.GtE) and not left >= right: return False
            if isinstance(op, ast.LtE) and not left <= right: return False
            left = right
        return True

    def visit_BoolOp(self, n):
        if isinstance(n.op, ast.And):
            return all(self.visit(v) for v in n.values)
        if isinstance(n.op, ast.Or):
            return any(self.visit(v) for v in n.values)
        raise TemplateError("Unsupported boolean op")

    def generic_visit(self, n):
        raise TemplateError(f"Unsupported expression: {ast.dump(n)}")

def eval_expr_ast(expr, ctx):
    tree = ast.parse(expr, mode="eval")
    return SafeEval({k: wrap_ctx(v) for k, v in ctx.items()}).visit(tree)

def parse_args_tuple(argstr, ctx):
    if not argstr.strip(): return ()
    return eval_expr_ast(f"({argstr},)", ctx)
""",

"tokenizer.py": """
from dataclasses import dataclass
import re

@dataclass(frozen=True)
class Tok:
    kind: str
    val: str
    lstrip: bool = False
    rstrip: bool = False

_RE = re.compile(r"(?s)(\\{\\{-?.*?-?\\}\\}|\\{%-?.*?-?%\\})")

def tokenize(src):
    pos, out = 0, []
    for m in _RE.finditer(src):
        if m.start() > pos:
            out.append(Tok("TEXT", src[pos:m.start()]))
        raw = m.group()
        l = raw.startswith(("{{-", "{%-"))
        r = raw.endswith(("-}}", "-%}"))
        inner = raw[3 if l else 2 : -3 if r else -2].strip()
        out.append(Tok("EXPR" if raw.startswith("{{") else "STMT", inner, l, r))
        pos = m.end()
    if pos < len(src):
        out.append(Tok("TEXT", src[pos:]))

    for i,t in enumerate(out):
        if t.lstrip and i>0 and out[i-1].kind=="TEXT":
            out[i-1]=Tok("TEXT",out[i-1].val.rstrip())
        if t.rstrip and i+1<len(out) and out[i+1].kind=="TEXT":
            out[i+1]=Tok("TEXT",out[i+1].val.lstrip())
    return out
""",

"parser.py": """
from dataclasses import dataclass
import re
from .errors import TemplateError
from .nodes import *

def head(s): return s.split(maxsplit=1)[0]

@dataclass
class Parser:
    toks:list; i:int=0

    def parse(self): return self._until(set())

    def _until(self, stop):
        out=[]
        while self.i<len(self.toks):
            t=self.toks[self.i]
            if t.kind=="STMT" and head(t.val) in stop: break
            if t.kind=="TEXT": out.append(Text(t.val)); self.i+=1
            elif t.kind=="EXPR": out.append(Expr(t.val)); self.i+=1
            else: out.append(self._stmt())
        return Seq(out)

    def _stmt(self):
        v=self.toks[self.i].val; h=head(v); self.i+=1

        if h=="if":
            b=self._until({"else","endif"}); e=None
            if self.toks[self.i].val.startswith("else"):
                self.i+=1; e=self._until({"endif"})
            self.i+=1; return If(v[3:].strip(),b,e)

        if h=="for":
            m=re.match(r"for (\\w+) in (.+)",v)
            body=self._until({"endfor"}); self.i+=1
            return For(m.group(1),m.group(2),body)

        if h=="assert":
            m=re.match(r'assert\\s+(.+?)(?:\\s+"(.*)")?$',v)
            return Assert(m.group(1),m.group(2))

        if h=="defer":
            body=self._until({"enddefer"}); self.i+=1
            return Defer(v[6:].strip(),body)

        if h=="match":
            cases=[]
            while self.i<len(self.toks):
                if head(self.toks[self.i].val)=="endmatch": break
                if head(self.toks[self.i].val)=="case":
                    c=self.toks[self.i].val[5:].strip(); self.i+=1
                    body=self._until({"case","endmatch"})
                    cases.append(Case(None if c=="_" else c,body))
                else: self.i+=1
            if self.i>=len(self.toks): raise TemplateError("Unclosed match")
            self.i+=1; return Match(v[6:].strip(),cases)

        raise TemplateError("Unknown statement")
""",

"nodes.py": """
from dataclasses import dataclass
from .safeeval import eval_expr_ast, parse_args_tuple
from .errors import TemplateError
import re

class Node: pass

@dataclass
class Seq(Node):
    items:list
    def eval(self,c,f,o):
        for n in self.items: n.eval(c,f,o)

@dataclass
class Text(Node):
    s:str
    def eval(self,c,f,o): o.append(self.s)

@dataclass
class Expr(Node):
    e:str
    def eval(self,c,f,o): o.append(str(eval_template_expr(self.e,c,f)))

@dataclass
class If(Node):
    c:str; t:Node; e:Node|None
    def eval(self,cx,f,o):
        (self.t if eval_expr_ast(self.c,cx) else self.e).eval(cx,f,o) if self.e else None

@dataclass
class For(Node):
    v:str; it:str; b:Node
    def eval(self,c,f,o):
        for x in eval_expr_ast(self.it,c): c[self.v]=x; self.b.eval(c,f,o)

@dataclass
class Defer(Node):
    k:str; b:Node
    def eval(self,c,f,o):
        c.setdefault("_deferred",{}).setdefault(self.k,[]).append(run(self.b,c,f))

@dataclass
class Assert(Node):
    e:str; msg:str|None
    def eval(self,c,f,o):
        if not eval_expr_ast(self.e,c):
            raise TemplateError(self.msg or self.e)

@dataclass
class Case:
    e:str|None; b:Node

@dataclass
class Match(Node):
    e:str; cs:list
    def eval(self,c,f,o):
        v=eval_expr_ast(self.e,c)
        for x in self.cs:
            if x.e is None or eval_expr_ast(x.e,c)==v:
                x.b.eval(c,f,o); return

_FILTER=re.compile(r"\\s*\\|\\s*")
def eval_template_expr(e,c,f):
    p=_FILTER.split(e); v=eval_expr_ast(p[0],c)
    for x in p[1:]:
        m=re.match(r"(\\w+)(?:\\((.*)\\))?",x)
        fn=f[m.group(1)]
        v=fn(v,*parse_args_tuple(m.group(2) or "",c))
    return v

def run(n,c,f):
    o=[]; n.eval(c,f,o); return "".join(o)
""",

"renderer.py": """
from dataclasses import dataclass
from .tokenizer import tokenize
from .parser import Parser
from .filters import DEFAULT_FILTERS

@dataclass(frozen=True)
class Renderer:
    template:str
    def render(self,ctx=None,filters=None):
        c=dict(ctx or {})
        c["_deferred"]={}
        def render_deferred(k,j="",consume=True):
            v=j.join(c["_deferred"].get(k,[]))
            if consume: c["_deferred"][k]=[]
            return v
        c["render_deferred"]=render_deferred
        f=dict(DEFAULT_FILTERS); f.update(filters or {})
        ast=Parser(tokenize(self.template)).parse()
        out=[]; ast.eval(c,f,out)
        return "".join(out)
"""
}
