"""
=============================================================
  app.py  —  C++ Compiler Pipeline — Teaching Tool
=============================================================
  Run:
    pip install streamlit pandas plotly
    streamlit run app.py
=============================================================
"""

import streamlit as st
import subprocess, shutil, os, re, tempfile, sys
from pathlib import Path
from collections import Counter
import pandas as pd

# ─────────────────────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="C++ Lexical and Syntax Analyzer",
    page_icon="⟨/⟩",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────
#  CSS
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Inter:wght@400;500;600;700&display=swap');

:root {
    --bg:     #0d1117;
    --panel:  #161b22;
    --card:   #1c2128;
    --border: #30363d;
    --accent: #58a6ff;
    --green:  #3fb950;
    --red:    #f85149;
    --orange: #ffa657;
    --purple: #d2a8ff;
    --fg:     #e6edf3;
    --fg-dim: #8b949e;
    --mono:   'JetBrains Mono', monospace;
    --sans:   'Inter', sans-serif;
}

.stApp { background: var(--bg); color: var(--fg); font-family: var(--sans); }

section[data-testid="stSidebar"] {
    background: var(--panel);
    border-right: 1px solid var(--border);
}

.stButton>button {
    font-family: var(--sans);
    font-size: 13px;
    background: var(--card);
    color: var(--fg);
    border: 1px solid var(--border);
    border-radius: 8px;
    transition: all .15s;
}
.stButton>button:hover { border-color: var(--accent); color: var(--accent); }
.stButton>button[kind="primary"] {
    background: #1a4a1a !important;
    border-color: var(--green) !important;
    color: var(--green) !important;
    font-weight: 600;
    font-size: 15px !important;
}

.phase-card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 16px;
}
.phase-header { display:flex; align-items:center; gap:12px; margin-bottom:6px; }
.phase-num {
    background: var(--accent); color: #0d1117;
    font-weight: 700; font-size: 12px;
    border-radius: 50%; width:24px; height:24px;
    display:inline-flex; align-items:center; justify-content:center; flex-shrink:0;
}
.phase-title { font-family:var(--sans); font-size:16px; font-weight:700; color:var(--fg); }
.phase-desc  { font-size:12px; color:var(--fg-dim); line-height:1.6; margin-bottom:14px; }

.pipeline {
    display:flex; align-items:center; flex-wrap:wrap; gap:6px;
    margin: 16px 0 24px 0;
}
.pipe-step {
    padding:7px 16px; border-radius:20px;
    font-size:12px; font-family:var(--sans); font-weight:600;
    border:1.5px solid var(--border); color:var(--fg-dim); background:var(--panel);
}
.pipe-step.done   { border-color:var(--green);  color:var(--green);  background:#0d2d14; }
.pipe-step.active { border-color:var(--accent); color:var(--accent); background:#0d1f35; }
.pipe-arrow { color:var(--border); font-size:16px; padding:0 2px; }

.pill { display:inline-block; padding:2px 10px; border-radius:20px;
        font-size:11px; font-family:var(--mono); font-weight:600; }
.pill-ok   { background:#0d2d14; color:#3fb950; border:1px solid #3fb950; }
.pill-err  { background:#2d0d0d; color:#f85149; border:1px solid #f85149; }
.pill-warn { background:#2d1f0d; color:#ffa657; border:1px solid #ffa657; }

[data-testid="stDataFrame"]   { border:1px solid var(--border); border-radius:8px; }
[data-testid="stMetric"]      { background:var(--panel); border:1px solid var(--border);
                                  border-radius:8px; padding:12px 16px; }
[data-testid="stMetricLabel"] { color:var(--fg-dim) !important; font-size:11px !important; }
[data-testid="stMetricValue"] { color:var(--accent) !important; font-size:24px !important; font-weight:700 !important; }

hr { border-color:var(--border); margin:0.5rem 0; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  PATHS
# ─────────────────────────────────────────────────────────────
HERE        = Path(__file__).parent
LEXER_L     = HERE / "lexer.l"
PARSER_Y    = HERE / "parser.y"
LEX_C       = HERE / "lex.yy.c"
PTAB_C      = HERE / "parser.tab.c"
BINARY_NAME = "cpp_analyzer.exe" if sys.platform == "win32" else "cpp_analyzer"
BINARY      = HERE / BINARY_NAME
LOG_FILE    = HERE / "lexer_output.txt"

TOKEN_COLOR = {
    "KEYWORD":        "#ff7b72",
    "IDENTIFIER":     "#79c0ff",
    "INTEGER_LITERAL":"#ffa657",
    "FLOAT_LITERAL":  "#ffa657",
    "STRING_LITERAL": "#a5d6ff",
    "CHAR_LITERAL":   "#a5d6ff",
    "OPERATOR":       "#d2a8ff",
    "PUNCTUATION":    "#8b949e",
    "PREPROCESSOR":   "#3fb950",
    "COMMENT":        "#484f58",
    "UNKNOWN":        "#f85149",
}
CAT_COLOR = {
    "function":  "#79c0ff",
    "variable":  "#3fb950",
    "namespace": "#ffa657",
    "variable":  "#3fb950",
}
PLOTLY_BG   = "#0d1117"
PLOTLY_GRID = "#21262d"

# ─────────────────────────────────────────────────────────────
#  TOOLCHAIN
# ─────────────────────────────────────────────────────────────
def tool_ok(name):   return shutil.which(name) is not None
def binary_ok():     return BINARY.is_file()
def find_tool(*ns):
    for n in ns:
        if tool_ok(n): return n
    return None

def run_cmd(args, cwd=None):
    r = subprocess.run(args, capture_output=True, text=True, timeout=60, cwd=cwd)
    return r.returncode == 0, r.stdout, r.stderr

def compile_all():
    steps = []
    if not LEXER_L.exists():  return [("lexer.l",  False, "lexer.l not found next to app.py")]
    if not PARSER_Y.exists(): return [("parser.y", False, "parser.y not found next to app.py")]

    bison = find_tool("bison", "win_bison")
    flex  = find_tool("flex",  "win_flex")
    gcc   = find_tool("gcc",   "cc")

    if not bison: return [("bison", False, "bison / win_bison not found in PATH")]
    if not flex:  return [("flex",  False, "flex / win_flex not found in PATH")]
    if not gcc:   return [("gcc",   False, "gcc not found in PATH")]

    ok,_,err = run_cmd([bison, "-d", str(PARSER_Y), "-o", str(PTAB_C)], cwd=str(HERE))
    steps.append(("Bison  →  parser.tab.c", ok, err.strip() or "OK"))
    if not ok: return steps

    ok,_,err = run_cmd([flex, "-o", str(LEX_C), str(LEXER_L)], cwd=str(HERE))
    steps.append(("Flex   →  lex.yy.c", ok, err.strip() or "OK"))
    if not ok: return steps

    flags = [] if sys.platform == "win32" else ["-lfl"]
    ok,_,err = run_cmd([gcc, str(LEX_C), str(PTAB_C), "-o", str(BINARY), "-lm"] + flags, cwd=str(HERE))
    steps.append((f"GCC    →  {BINARY_NAME}", ok, err.strip() or "OK"))
    return steps

def run_analyzer(src_path):
    if LOG_FILE.exists(): LOG_FILE.unlink()
    ok,out,err = run_cmd([str(BINARY), src_path], cwd=str(HERE))
    return ok, err

# ─────────────────────────────────────────────────────────────
#  PARSE TOKEN LOG
# ─────────────────────────────────────────────────────────────
HEADER_RE = re.compile(r"^[=\-\s]|^\s*Format|^\s*Generated|^\s*C\+\+|^\s*End")

def parse_log(log_path):
    tokens = []
    if not log_path.exists(): return tokens
    with open(log_path, encoding="utf-8", errors="replace") as f:
        for raw in f:
            line = raw.rstrip("\n")
            if not line.strip() or HEADER_RE.match(line): continue
            parts = re.split(r"\s{2,}", line.strip(), maxsplit=3)
            if len(parts) < 4: continue
            try:
                tokens.append({
                    "line":     int(parts[0]),
                    "col":      int(parts[1]),
                    "category": parts[2].strip(),
                    "value":    parts[3].strip(),
                })
            except ValueError:
                continue
    return tokens

def base_cat(c):
    if "INTEGER" in c: return "INTEGER_LITERAL"
    if "FLOAT"   in c: return "FLOAT_LITERAL"
    if "STRING"  in c: return "STRING_LITERAL"
    if "COMMENT" in c: return "COMMENT"
    return c

# ─────────────────────────────────────────────────────────────
#  SYMBOL TABLE
# ─────────────────────────────────────────────────────────────
def build_symbol_table(tokens):
    syms = {}; n = len(tokens)
    for i, tok in enumerate(tokens):
        if "IDENTIFIER" not in tok["category"]: continue
        name     = tok["value"]
        next_val = tokens[i+1]["value"] if i+1 < n else ""
        prev_val = tokens[i-1]["value"] if i > 0  else ""

        if next_val == "(":
            cat = "function"
        elif prev_val in ("int","float","double","char","bool","void",
                          "long","short","unsigned","signed","auto","const"):
            cat = "variable"
        elif "::" in prev_val or prev_val == "::":
            cat = "namespace"
        else:
            cat = "variable"

        if name not in syms:
            syms[name] = {"name":name, "category":cat,
                          "first_line":tok["line"], "occurrences":0, "lines":[]}
        if cat == "function":
            syms[name]["category"] = "function"
        syms[name]["occurrences"] += 1
        syms[name]["lines"].append(tok["line"])
    return sorted(syms.values(), key=lambda s: s["first_line"])

# ─────────────────────────────────────────────────────────────
#  AST
# ─────────────────────────────────────────────────────────────
TYPE_KW = {"int","float","double","char","bool","void","long","short",
           "unsigned","signed","auto","const"}

class TS:
    def __init__(self, toks):
        self.t = [t for t in toks if "COMMENT" not in t["category"]
                  and "PREPROCESSOR" not in t["category"]]
        self.p = 0
    def peek(self, o=0):
        i = self.p+o; return self.t[i] if i < len(self.t) else {"category":"EOF","value":""}
    def consume(self):
        t = self.peek(); self.p += 1; return t
    def done(self): return self.p >= len(self.t)
    def pv(self, o=0): return self.peek(o)["value"]
    def pc(self, o=0): return self.peek(o)["category"]

def build_ast(tokens):
    ts = TS(tokens); body = []
    while not ts.done():
        node = ptop(ts)
        if node: body.append(node)
        else: ts.consume()
    return body

def is_type_ctx(ts): return ts.pc(0)=="IDENTIFIER" and ts.pc(1)=="IDENTIFIER"

def ptop(ts):
    val,cat = ts.pv(), ts.pc()
    if cat=="PREPROCESSOR":
        t=ts.consume(); return {"type":"Preprocessor","value":t["value"],"line":t["line"]}
    if val=="namespace": return p_ns(ts)
    if val=="using":     return p_using(ts)
    if val in ("class","struct"): return p_class(ts)
    if val in TYPE_KW or (cat=="IDENTIFIER" and is_type_ctx(ts)): return p_decl(ts)
    return None

def p_ns(ts):
    ts.consume()
    name = ts.consume()["value"] if ts.pc()=="IDENTIFIER" else "<anon>"
    body = []
    if ts.pv()=="{":
        ts.consume()
        while not ts.done() and ts.pv()!="}":
            n=ptop(ts)
            if n: body.append(n)
            else: ts.consume()
        if ts.pv()=="}" : ts.consume()
    return {"type":"Namespace","name":name,"body":body}

def p_using(ts):
    ts.consume(); parts=[]
    while not ts.done() and ts.pv()!=";": parts.append(ts.consume()["value"])
    if ts.pv()==";": ts.consume()
    return {"type":"UsingDecl","value":" ".join(parts)}

def p_class(ts):
    kind=ts.consume()["value"]
    name=ts.consume()["value"] if ts.pc()=="IDENTIFIER" else "?"
    while not ts.done() and ts.pv() not in ("{",";"): ts.consume()
    members=[]
    if ts.pv()=="{":
        ts.consume()
        while not ts.done() and ts.pv()!="}":
            n=p_decl(ts)
            if n: members.append(n)
            else: ts.consume()
        if ts.pv()=="}": ts.consume()
    if ts.pv()==";": ts.consume()
    return {"type":kind.capitalize()+"Decl","name":name,"members":members}

def p_decl(ts):
    tp=[]
    while not ts.done() and (ts.pv() in TYPE_KW or ts.pv() in ("*","&","const")):
        tp.append(ts.consume()["value"])
    if not tp and ts.pc()=="IDENTIFIER": tp.append(ts.consume()["value"])
    if ts.pc()!="IDENTIFIER": return None
    dt=" ".join(tp); nt=ts.consume(); name=nt["value"]; line=nt["line"]
    if ts.pv()=="(":
        params=p_params(ts)
        if ts.pv()=="{":
            body=p_block(ts)
            return {"type":"FunctionDef","return_type":dt,"name":name,"params":params,"body":body,"line":line}
        if ts.pv()==";": ts.consume()
        return {"type":"FunctionDecl","return_type":dt,"name":name,"params":params,"line":line}
    if ts.pv()=="[":
        ts.consume(); size=""
        while not ts.done() and ts.pv()!="]": size+=ts.consume()["value"]
        if ts.pv()=="]": ts.consume()
        init=None
        if ts.pv()=="=": ts.consume(); init=p_init(ts)
        if ts.pv()==";": ts.consume()
        return {"type":"ArrayDecl","data_type":dt,"name":name,"size":size or "?","initializer":init,"line":line}
    init=None
    if ts.pv()=="=": ts.consume(); init=p_until(ts,";")
    if ts.pv()==";": ts.consume()
    return {"type":"VarDecl","data_type":dt,"name":name,"initializer":init,"line":line}

def p_params(ts):
    buf=[]; params=[]
    if ts.pv()=="(": ts.consume()
    depth=1
    while not ts.done() and depth>0:
        v=ts.pv()
        if v=="(": depth+=1
        if v==")": depth-=1
        if depth==0: break
        if v=="," and depth==1: params.append(" ".join(buf)); buf=[]; ts.consume(); continue
        buf.append(ts.consume()["value"])
    if ts.pv()==")": ts.consume()
    if buf: params.append(" ".join(buf))
    return [p for p in params if p.strip()]

def p_block(ts):
    stmts=[]
    if ts.pv()=="{": ts.consume()
    depth=1
    while not ts.done() and depth>0:
        v=ts.pv()
        if v=="{": depth+=1
        if v=="}":
            depth-=1
            if depth==0: break
        if (ts.pv() in TYPE_KW or is_type_ctx(ts)) and depth==1:
            n=p_decl(ts)
            if n: stmts.append(n); continue
        parts=[]
        while not ts.done():
            cv=ts.pv()
            if cv=="{": depth+=1
            if cv=="}": depth-=1
            if depth==0: break
            parts.append(ts.consume()["value"])
            if cv==";" and depth==1: break
        if parts: stmts.append({"type":"Statement","text":" ".join(parts)})
    if ts.pv()=="}": ts.consume()
    return stmts

def p_init(ts):
    if ts.pv()=="{":
        buf=[]; d=0
        while not ts.done():
            v=ts.consume()["value"]; buf.append(v)
            if v=="{": d+=1
            if v=="}": d-=1
            if d==0: break
        return " ".join(buf)
    return p_until(ts, ";")

def p_until(ts, stop):
    parts=[]
    while not ts.done() and ts.pv()!=stop: parts.append(ts.consume()["value"])
    return " ".join(parts)

# ─────────────────────────────────────────────────────────────
#  AST TEXT TREE
# ─────────────────────────────────────────────────────────────
def ast_lines(nodes, prefix=""):
    lines=[]
    for idx,node in enumerate(nodes):
        last        = idx==len(nodes)-1
        conn        = "└── " if last else "├── "
        child_pfx   = prefix + ("    " if last else "│   ")
        ntype       = node.get("type","Node")
        name        = node.get("name") or node.get("value","")

        if ntype=="FunctionDef":
            ret=node.get("return_type",""); params=", ".join(node.get("params",[]))
            label=f"🔵 Function   {name}({params})  →  {ret}"
        elif ntype=="FunctionDecl":
            params=", ".join(node.get("params",[]))
            label=f"🔷 Prototype  {name}({params})"
        elif ntype=="VarDecl":
            dt=node.get("data_type",""); init=node.get("initializer")
            label=f"🟢 Variable   {name} : {dt}" + (f"  =  {init}" if init else "")
        elif ntype=="ArrayDecl":
            dt=node.get("data_type",""); sz=node.get("size","?")
            label=f"🟩 Array      {name}[{sz}] : {dt}"
        elif ntype=="Statement":
            label=f"▸  {node.get('text','')[:60]}"
        elif ntype=="Preprocessor":
            label=f"🔸 {node.get('value','')}"
        elif ntype=="UsingDecl":
            label=f"⬜ using  {name}"
        elif ntype=="Namespace":
            label=f"🟠 namespace  {name}"
        elif ntype in ("ClassDecl","StructDecl"):
            label=f"🟣 {ntype.replace('Decl','')}  {name}"
        else:
            label=f"◆  {ntype}  {name}"

        lines.append(prefix+conn+label)
        children = node.get("body") or node.get("members") or []
        if children: lines.extend(ast_lines(children, child_pfx))
    return lines

# ─────────────────────────────────────────────────────────────
#  PLOTLY BAR
# ─────────────────────────────────────────────────────────────
def plotly_hbar(labels, values, colors, title=""):
    import plotly.graph_objects as go
    total=sum(values) or 1
    fig=go.Figure(go.Bar(
        x=values, y=labels, orientation="h",
        marker_color=colors,
        text=[f"{v}  ({v/total*100:.0f}%)" for v in values],
        textposition="outside",
        textfont=dict(color="#8b949e",size=11,family="JetBrains Mono"),
    ))
    fig.update_layout(
        title=dict(text=title,font=dict(color="#e6edf3",size=13)),
        paper_bgcolor=PLOTLY_BG, plot_bgcolor="#161b22",
        font=dict(color="#e6edf3",family="JetBrains Mono"),
        xaxis=dict(gridcolor=PLOTLY_GRID,zerolinecolor=PLOTLY_GRID,
                   tickfont=dict(color="#8b949e",size=10)),
        yaxis=dict(tickfont=dict(color="#e6edf3",size=11)),
        margin=dict(l=0,r=80,t=40 if title else 10,b=10),
        height=max(240,len(labels)*34), showlegend=False,
    )
    return fig

# ─────────────────────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────────────────────
for k,v in [("tokens",[]),("symbols",[]),("ast",[]),
            ("source",""),("filename",""),("analyzed",False)]:
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:16px 0 10px 0">
      <span style="font-size:26px">⟨/⟩</span>
      <span style="font-family:'Inter',sans-serif;font-size:17px;font-weight:700;
                   color:#e6edf3;margin-left:8px">C++ Pipeline</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("<span style='font-size:11px;color:#8b949e;font-weight:600'>TOOLCHAIN STATUS</span>",
                unsafe_allow_html=True)
    for label, cmds in [("flex / win_flex",["flex","win_flex"]),
                         ("bison / win_bison",["bison","win_bison"]),
                         ("gcc",["gcc"])]:
        ok   = any(tool_ok(c) for c in cmds)
        pill = "ok" if ok else "err"
        sym  = "✓" if ok else "✗"
        st.markdown(f'<span class="pill pill-{pill}">{sym} {label}</span>', unsafe_allow_html=True)

    st.markdown("")
    if binary_ok():
        st.markdown('<span class="pill pill-ok">✓ binary ready</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="pill pill-warn">⚠ not compiled</span>', unsafe_allow_html=True)

    st.markdown("---")
    if st.button("⚙  Compile Toolchain", use_container_width=True):
        with st.spinner("Compiling …"):
            steps = compile_all()
        for label, ok, msg in steps:
            if ok: st.success(f"✓ {label}")
            else:  st.error(f"✗ {label}\n```\n{msg}\n```")
        if all(ok for _,ok,_ in steps):
            st.balloons()

    st.markdown("---")
    st.markdown("""
    <div style="font-size:11px;color:#484f58;line-height:1.8">
      <b style="color:#8b949e">Steps</b><br>
      1. Compile Toolchain (once)<br>
      2. Upload a .cpp file<br>
      3. Click ▶ Analyse<br><br>
      lexer.l + parser.y must be<br>in the same folder as app.py
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────────────────────
st.markdown("""
<div style="border-bottom:1px solid #30363d;padding-bottom:14px;margin-bottom:22px">
  <div style="font-family:'Inter',sans-serif;font-size:24px;font-weight:700;color:#e6edf3">
    C++ Compiler Pipeline
  </div>
  <div style="font-size:12px;color:#8b949e;margin-top:4px">
    Upload a C++ source file to see each compiler phase in action
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  UPLOAD + ANALYSE
# ─────────────────────────────────────────────────────────────
col_up, col_btn = st.columns([5, 1.5])
with col_up:
    cpp_file = st.file_uploader(
        "Upload C++ source", type=["cpp","cxx","cc","h","hpp","c"],
        label_visibility="collapsed", key="cpp_upload",
    )
with col_btn:
    st.write("")
    analyse_btn = st.button("▶  Analyse", type="primary",
                            use_container_width=True, disabled=(cpp_file is None))

# ── run analysis ──────────────────────────────────────────────
if analyse_btn and cpp_file:
    if not binary_ok():
        st.error("Binary not found — click **⚙ Compile Toolchain** in the sidebar first.")
    else:
        with tempfile.NamedTemporaryFile(suffix=".cpp", delete=False, mode="wb") as tmp:
            tmp.write(cpp_file.getvalue())
            tmp_path = tmp.name

        prog = st.empty()

        def show_pipeline(s1, s2, s3):
            prog.markdown(f"""
            <div class="pipeline">
              <div class="pipe-step {s1}">{"✓" if s1=="done" else "⏳"} Lexical Analysis</div>
              <div class="pipe-arrow">→</div>
              <div class="pipe-step {s2}">{"✓" if s2=="done" else ("⏳" if s2=="active" else "")} Syntax Analysis</div>
              <div class="pipe-arrow">→</div>
              <div class="pipe-step {s3}">{"✓" if s3=="done" else ("⏳" if s3=="active" else "")} Symbol Table</div>
            </div>""", unsafe_allow_html=True)

        show_pipeline("active", "", "")
        ok, err = run_analyzer(tmp_path)
        os.unlink(tmp_path)

        show_pipeline("done", "active", "")
        raw_tokens = parse_log(LOG_FILE)

        show_pipeline("done", "done", "active")
        symbols   = build_symbol_table(raw_tokens)
        ast_nodes = build_ast(raw_tokens)
        show_pipeline("done", "done", "done")

        st.session_state.tokens   = raw_tokens
        st.session_state.symbols  = symbols
        st.session_state.ast      = ast_nodes
        st.session_state.source   = cpp_file.getvalue().decode("utf-8", errors="replace")
        st.session_state.filename = cpp_file.name
        st.session_state.analyzed = True

        st.success(f"✓  {cpp_file.name}  —  {len(raw_tokens)} tokens · {len(symbols)} symbols · {len(ast_nodes)} AST nodes")

# ─────────────────────────────────────────────────────────────
#  RESULTS
# ─────────────────────────────────────────────────────────────
if st.session_state.analyzed and st.session_state.tokens:
    tokens  = st.session_state.tokens
    symbols = st.session_state.symbols
    ast     = st.session_state.ast
    source  = st.session_state.source
    fname   = st.session_state.filename

    # summary metrics
    base_counts = Counter(base_cat(t["category"]) for t in tokens)
    m1,m2,m3,m4,m5 = st.columns(5)
    m1.metric("Total Tokens",   len(tokens))
    m2.metric("Keywords",       base_counts.get("KEYWORD",0))
    m3.metric("Identifiers",    base_counts.get("IDENTIFIER",0))
    m4.metric("Unique Symbols", len(symbols))
    m5.metric("Source Lines",   source.count("\n")+1)

    st.markdown("<br>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════
    #  PHASE 1 — LEXICAL ANALYSIS
    # ══════════════════════════════════════════════════════════
    st.markdown("""
    <div class="phase-card">
      <div class="phase-header">
        <span class="phase-num">1</span>
        <span class="phase-title">Lexical Analysis</span>
      </div>
      <div class="phase-desc">
        The <b>lexer</b> (lexer.l) scans source code character by character and groups
        characters into <b>tokens</b> — the smallest meaningful units of a program.
        Each token has a <b>type</b> (keyword, identifier, operator…) and a <b>value</b>.
      </div>
    </div>
    """, unsafe_allow_html=True)

    non_comment = [t for t in tokens
                   if "COMMENT" not in t["category"] and "PREPROCESSOR" not in t["category"]]

    tf1, tf2 = st.columns([3, 1])
    with tf1:
        tok_search = st.text_input("", placeholder="🔍  Search tokens…",
                                   label_visibility="collapsed", key="tok_q")
    with tf2:
        all_cats = ["All Types"] + sorted(set(base_cat(t["category"]) for t in non_comment))
        tok_cat  = st.selectbox("", all_cats, label_visibility="collapsed", key="tok_cat")

    filtered = [
        t for t in non_comment
        if (tok_cat == "All Types" or base_cat(t["category"]) == tok_cat)
        and (not tok_search or tok_search.lower() in t["value"].lower()
             or tok_search.lower() in t["category"].lower())
    ]

    simple_rows = [{"Token Type": base_cat(t["category"]),
                    "Value":      t["value"],
                    "Line":       t["line"]} for t in filtered]
    df_simple = pd.DataFrame(simple_rows)

    def style_simple(col):
        if col.name == "Token Type":
            return [f"color:{TOKEN_COLOR.get(v,'#e6edf3')};font-family:JetBrains Mono,monospace;"
                    "font-size:11px;font-weight:600" for v in col]
        if col.name == "Value":
            return ["font-family:JetBrains Mono,monospace;font-size:12px"] * len(col)
        return ["color:#8b949e;font-size:12px"] * len(col)

    if not df_simple.empty:
        st.dataframe(df_simple.style.apply(style_simple, axis=0),
                     use_container_width=True, height=320)
        st.caption(f"Showing {len(filtered)} / {len(non_comment)} tokens  (comments & preprocessor hidden)")

    with st.expander("🔍  Detailed token table  (with column numbers & category variants)"):
        det_rows = [{"#":i+1, "Line":t["line"], "Col":t["col"],
                     "Category":t["category"], "Value":t["value"]}
                    for i,t in enumerate(filtered)]
        st.dataframe(pd.DataFrame(det_rows), use_container_width=True, height=300)

    with st.expander("📊  Token distribution chart"):
        bc_items  = sorted(base_counts.items(), key=lambda x: x[1])
        bc_labels = [i[0] for i in bc_items]
        bc_values = [i[1] for i in bc_items]
        bc_colors = [TOKEN_COLOR.get(l,"#8b949e") for l in bc_labels]
        st.plotly_chart(plotly_hbar(bc_labels, bc_values, bc_colors, "Token Distribution"),
                        use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════
    #  PHASE 2 — SYNTAX ANALYSIS (AST)
    # ══════════════════════════════════════════════════════════
    st.markdown("""
    <div class="phase-card">
      <div class="phase-header">
        <span class="phase-num">2</span>
        <span class="phase-title">Syntax Analysis</span>
      </div>
      <div class="phase-desc">
        The <b>parser</b> (parser.y) takes the token stream and checks it against C++ grammar rules.
        If the grammar is valid it produces an <b>Abstract Syntax Tree (AST)</b> — a hierarchical
        representation of the program's structure showing functions, variables, and statements.
      </div>
    </div>
    """, unsafe_allow_html=True)

    if not ast:
        st.info("No AST nodes found. Make sure the file has recognisable declarations.")
    else:
        tree_text = "\n".join(ast_lines(ast))
        st.code(tree_text, language=None)

        with st.expander("📄  Raw AST — JSON  (advanced view)"):
            st.json(ast, expanded=2)

    st.markdown("<br>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════
    #  PHASE 3 — SYMBOL TABLE
    # ══════════════════════════════════════════════════════════
    st.markdown("""
    <div class="phase-card">
      <div class="phase-header">
        <span class="phase-num">3</span>
        <span class="phase-title">Symbol Table</span>
      </div>
      <div class="phase-desc">
        The compiler collects every <b>identifier</b> (variable, function, namespace) and
        records its name, category, where it first appeared, and how many times it is used.
        This is used later for type-checking and code generation.
      </div>
    </div>
    """, unsafe_allow_html=True)

    sc1, sc2 = st.columns([3, 1])
    with sc1:
        sym_q = st.text_input("", placeholder="🔍  Search by name…",
                              label_visibility="collapsed", key="sym_q")
    with sc2:
        all_scats = ["All"] + sorted(set(s["category"] for s in symbols))
        sym_cat   = st.selectbox("", all_scats, label_visibility="collapsed", key="sym_cat")

    filtered_s = [
        s for s in symbols
        if (sym_cat == "All" or s["category"] == sym_cat)
        and (not sym_q or sym_q.lower() in s["name"].lower())
    ]

    sym_rows = [{"Name":       s["name"],
                 "Category":   s["category"],
                 "First Line": s["first_line"],
                 "Used":       s["occurrences"],
                 "All Lines":  ", ".join(str(l) for l in s["lines"])}
                for s in filtered_s]
    sdf = pd.DataFrame(sym_rows)

    def style_sym(col):
        if col.name == "Category":
            return [f"color:{CAT_COLOR.get(v,'#8b949e')};font-family:JetBrains Mono,monospace;"
                    "font-size:11px;font-weight:600" for v in col]
        if col.name == "Name":
            return ["color:#e6edf3;font-family:JetBrains Mono,monospace;"
                    "font-size:12px;font-weight:600"] * len(col)
        return ["font-size:12px"] * len(col)

    if not sdf.empty:
        st.dataframe(sdf.style.apply(style_sym, axis=0),
                     use_container_width=True, height=400)
        st.caption(f"Showing {len(filtered_s)} / {len(symbols)} symbols")

    st.markdown("<br>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════
    #  SOURCE VIEW (collapsed by default)
    # ══════════════════════════════════════════════════════════
    with st.expander(f"📄  Source code — {fname}"):
        st.code(source, language="cpp", line_numbers=True)

# ─────────────────────────────────────────────────────────────
#  EMPTY STATE
# ─────────────────────────────────────────────────────────────
else:
    st.markdown("""
    <div style="text-align:center;padding:70px 0">
      <div style="font-size:48px;margin-bottom:16px">⟨/⟩</div>
      <div style="font-family:'Inter',sans-serif;font-size:16px;color:#8b949e;margin-bottom:6px">
        Upload a C++ file and click
        <span style="color:#3fb950;font-weight:600">▶ Analyse</span>
      </div>
      <div style="font-size:12px;color:#484f58">
        Compile the toolchain first via the sidebar if needed
      </div>
    </div>
    """, unsafe_allow_html=True)
