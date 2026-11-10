"""把演练手册 Markdown 转成可交互的单文件 HTML。

零外部依赖（不引 CDN），双击即可离线打开。特性：
- 左侧目录自动生成，滚动高亮
- 每条命令一键复制
- 每一幕可勾选"已完成"，进度存 localStorage
- 打印样式：自动隐藏按钮，适合直接打印成纸质手册

用法：python tools/build_manual_html.py
"""

from __future__ import annotations

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "docs" / "onboarding" / "企业级开发流程演练手册.md"
OUT = ROOT / "docs" / "onboarding" / "企业级开发流程演练手册.html"

SCENE_RE = re.compile(r"^幕\s*\d+")


def inline(text: str) -> str:
    """处理行内格式。text 已做过 HTML 转义。"""
    codes: list[str] = []

    def stash(match: re.Match) -> str:
        codes.append(match.group(1))
        return f"\x00{len(codes) - 1}\x00"

    text = re.sub(r"`([^`]+)`", stash, text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(
        r"\[([^\]]+)\]\((https?://[^)]+)\)",
        r'<a href="\2" target="_blank" rel="noopener">\1</a>',
        text,
    )
    text = re.sub(
        r"(?<![\"'>=])(https?://[^\s<」）]+)",
        r'<a href="\1" target="_blank" rel="noopener">\1</a>',
        text,
    )

    def restore(match: re.Match) -> str:
        return f"<code>{codes[int(match.group(1))]}</code>"

    return re.sub(r"\x00(\d+)\x00", restore, text)


def is_table_sep(line: str) -> bool:
    return bool(re.match(r"^\|[\s:\-|]+\|$", line.strip()))


def render_table(rows: list[str]) -> str:
    cells = [[c.strip() for c in row.strip().strip("|").split("|")] for row in rows]
    header, body = cells[0], cells[2:]
    out = ['<div class="table-wrap"><table><thead><tr>']
    out += [f"<th>{inline(c)}</th>" for c in header]
    out.append("</tr></thead><tbody>")
    for row in body:
        out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in row) + "</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def convert(md: str) -> tuple[str, list[tuple[str, str, bool]]]:
    lines = md.splitlines()
    body: list[str] = []
    toc: list[tuple[str, str, bool]] = []
    i, n = 0, 0
    open_section = False

    def close_section() -> None:
        nonlocal open_section
        if open_section:
            body.append("</section>")
            open_section = False

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # 代码块
        if stripped.startswith("```"):
            lang = stripped[3:].strip()
            i += 1
            buf: list[str] = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            code = html.escape("\n".join(buf))
            body.append(
                '<div class="codebox">'
                f'<div class="codebar"><span>{lang or "shell"}</span>'
                '<button class="copy" type="button">复制</button></div>'
                f'<pre><code>{code}</code></pre></div>'
            )
            continue

        # 标题
        if stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            text = stripped[level:].strip()
            text = re.sub(r"^\d+\.\s*", "", text) if level == 3 else text
            n += 1
            sid = f"sec-{n}"
            text = re.sub(r"^幕\s*", "幕 ", text)
            if level == 1:
                body.append(f'<h1 id="{sid}">{inline(html.escape(text))}</h1>')
                toc.append((sid, text, False))
            elif level == 2:
                close_section()
                is_scene = bool(SCENE_RE.match(text))
                body.append(f'<section class="{"scene" if is_scene else "plain"}" id="{sid}">')
                open_section = True
                title_html = inline(html.escape(text))
                if is_scene:
                    body.append(
                        '<div class="scene-head">'
                        f'<h2 id="{sid}">{title_html}</h2>'
                        f'<label class="done"><input type="checkbox" data-scene="{sid}">'
                        '<span>已完成</span></label>'
                        "</div>"
                    )
                else:
                    body.append(f'<h2 id="{sid}">{title_html}</h2>')
                toc.append((sid, text, is_scene))
            else:
                body.append(f'<h{level} id="{sid}">{inline(html.escape(text))}</h{level}>')
            i += 1
            continue

        # 表格
        if stripped.startswith("|") and i + 1 < len(lines) and is_table_sep(lines[i + 1]):
            rows: list[str] = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(lines[i])
                i += 1
            body.append(render_table(rows))
            continue

        # 引用块
        if stripped.startswith(">"):
            buf = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                buf.append(inline(html.escape(lines[i].strip().lstrip(">" ).strip())))
                i += 1
            body.append('<blockquote><p>' + "<br>".join(buf) + "</p></blockquote>")
            continue

        # 无序 / 有序列表
        if re.match(r"^[-*]\s+", stripped):
            items = []
            while i < len(lines) and re.match(r"^[-*]\s+", lines[i].strip()):
                items.append(inline(html.escape(re.sub(r"^[-*]\s+", "", lines[i].strip()))))
                i += 1
            body.append("<ul>" + "".join(f"<li>{it}</li>" for it in items) + "</ul>")
            continue

        if re.match(r"^\d+\.\s+", stripped):
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s+", lines[i].strip()):
                items.append(inline(html.escape(re.sub(r"^\d+\.\s+", "", lines[i].strip()))))
                i += 1
            body.append("<ol>" + "".join(f"<li>{it}</li>" for it in items) + "</ol>")
            continue

        # 分隔线
        if re.fullmatch(r"-{3,}", stripped):
            body.append('<hr class="divider">')
            i += 1
            continue

        # 空行
        if not stripped:
            i += 1
            continue

        # 段落（连续非空行合并）
        buf = [stripped]
        i += 1
        while i < len(lines):
            nxt = lines[i].strip()
            if (not nxt or nxt.startswith(("#", "|", ">", "```"))
                    or re.match(r"^[-*]\s+", nxt) or re.match(r"^\d+\.\s+", nxt)
                    or re.fullmatch(r"-{3,}", nxt)):
                break
            buf.append(nxt)
            i += 1
        body.append("<p>" + inline(html.escape("".join(buf))) + "</p>")

    close_section()
    return "".join(body), toc


def build_html(body: str, toc: list) -> str:
    nav = ['<nav class="toc"><div class="toc-title">目录</div><ul>']
    for sid, text, is_scene in toc:
        cls = " class=\"toc-scene\"" if is_scene else ""
        nav.append(f'<li><a href="#{sid}"{cls} data-target="{sid}">{html.escape(text)}</a></li>')
    nav.append("</ul></nav>")
    nav_html = "".join(nav)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>企业级开发流程 · 12 幕实操演练手册</title>
<style>
:root {{
  --bg: #f7f7f5; --paper: #ffffff; --ink: #1f1f1f; --muted: #6b6b6b;
  --line: #e3e2dd; --accent: #1d9e75; --accent-soft: #e1f5ee;
  --code-bg: #f6f6f4; --warn-bg: #fdf6e3; --warn-line: #e8d9a8;
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0; background: var(--bg); color: var(--ink);
  font-family: -apple-system, "Segoe UI", "Microsoft YaHei", Roboto, sans-serif;
  font-size: 15px; line-height: 1.75;
}}
header.top {{
  position: sticky; top: 0; z-index: 20; background: rgba(255,255,255,.96);
  border-bottom: 1px solid var(--line); padding: 10px 24px;
  display: flex; align-items: center; gap: 16px; flex-wrap: wrap;
}}
header.top .brand {{ font-weight: 500; font-size: 15px; }}
header.top .brand small {{ color: var(--muted); font-weight: 400; margin-left: 8px; }}
.progress-wrap {{ display: flex; align-items: center; gap: 10px; margin-left: auto; }}
.progress {{ width: 220px; height: 6px; background: var(--line); border-radius: 4px; overflow: hidden; }}
.progress > i {{ display: block; height: 100%; width: 0; background: var(--accent); transition: width .25s; }}
#progress-text {{ font-size: 13px; color: var(--muted); font-variant-numeric: tabular-nums; }}
button.reset {{ font-size: 12px; padding: 4px 10px; border: 1px solid var(--line); background: #fff;
  border-radius: 6px; cursor: pointer; color: var(--muted); }}
button.reset:hover {{ color: var(--ink); border-color: #bbb; }}
.layout {{ display: flex; align-items: flex-start; gap: 0; }}
nav.toc {{
  position: sticky; top: 57px; flex: 0 0 268px; max-height: calc(100vh - 57px);
  overflow-y: auto; padding: 20px 12px 40px 24px; font-size: 13px;
}}
nav.toc .toc-title {{ font-size: 12px; color: var(--muted); letter-spacing: .08em; margin-bottom: 10px; }}
nav.toc ul {{ list-style: none; margin: 0; padding: 0; }}
nav.toc li {{ margin: 1px 0; }}
nav.toc a {{ display: block; padding: 4px 8px; border-radius: 6px; color: #4a4a4a; text-decoration: none;
  border-left: 2px solid transparent; }}
nav.toc a:hover {{ background: #eeece6; color: #111; }}
nav.toc a.active {{ background: var(--accent-soft); color: #0f6e56; border-left-color: var(--accent); }}
nav.toc a.toc-scene {{ font-weight: 500; color: #222; }}
nav.toc li.sub a {{ padding-left: 20px; color: var(--muted); font-weight: 400; }}
main {{ flex: 1 1 auto; min-width: 0; max-width: 860px; margin: 0 auto; padding: 28px 40px 120px; }}
h1 {{ font-size: 26px; font-weight: 500; margin: 8px 0 4px; letter-spacing: -.01em; }}
h2 {{ font-size: 20px; font-weight: 500; margin: 0; }}
h3 {{ font-size: 16px; font-weight: 500; margin: 26px 0 8px; }}
h4 {{ font-size: 15px; font-weight: 500; margin: 18px 0 6px; }}
section.scene {{ background: var(--paper); border: 1px solid var(--line); border-radius: 12px;
  padding: 22px 26px; margin: 20px 0; }}
section.scene.done {{ border-color: #bfe3d4; background: #fcfefd; }}
section.plain {{ margin: 20px 0; }}
.scene-head {{ display: flex; align-items: center; justify-content: space-between; gap: 12px;
  padding-bottom: 12px; border-bottom: 1px dashed var(--line); margin-bottom: 6px; }}
label.done {{ display: inline-flex; align-items: center; gap: 6px; font-size: 13px; color: var(--muted);
  cursor: pointer; user-select: none; white-space: nowrap; padding: 3px 10px; border: 1px solid var(--line);
  border-radius: 20px; background: #fff; }}
label.done input {{ margin: 0; accent-color: var(--accent); }}
label.done:has(input:checked) {{ color: #0f6e56; border-color: #9fe1cb; background: var(--accent-soft); }}
p {{ margin: 8px 0; }}
ul, ol {{ margin: 8px 0; padding-left: 22px; }}
li {{ margin: 3px 0; }}
strong {{ font-weight: 500; }}
code {{ font-family: "Cascadia Code", Consolas, Menlo, monospace; font-size: 13px;
  background: #efeee9; padding: 1px 5px; border-radius: 4px; }}
.codebox {{ margin: 12px 0; border: 1px solid var(--line); border-radius: 10px; overflow: hidden;
  background: var(--code-bg); }}
.codebar {{ display: flex; align-items: center; justify-content: space-between;
  padding: 5px 12px; background: #efeee9; border-bottom: 1px solid var(--line);
  font-size: 11px; color: var(--muted); letter-spacing: .06em; }}
.codebar .copy {{ font-size: 11px; padding: 2px 10px; border: 1px solid var(--line); background: #fff;
  border-radius: 5px; cursor: pointer; color: #555; }}
.codebar .copy:hover {{ border-color: #bbb; color: #111; }}
.codebar .copy.ok {{ background: var(--accent); color: #fff; border-color: var(--accent); }}
pre {{ margin: 0; padding: 14px 16px; overflow-x: auto; }}
pre code {{ background: none; padding: 0; font-size: 13px; line-height: 1.7; }}
blockquote {{ margin: 12px 0; padding: 10px 14px; background: var(--warn-bg);
  border-left: 3px solid var(--warn-line); border-radius: 0 8px 8px 0; color: #4a3f1e; }}
blockquote p {{ margin: 0; font-size: 14px; }}
.table-wrap {{ overflow-x: auto; margin: 12px 0; }}
table {{ border-collapse: collapse; width: 100%; font-size: 14px; background: #fff; }}
th, td {{ border: 1px solid var(--line); padding: 7px 12px; text-align: left; vertical-align: top; }}
th {{ background: #f2f1ec; font-weight: 500; }}
hr.divider {{ border: 0; border-top: 1px solid var(--line); margin: 28px 0; }}
a {{ color: #0f6e56; }}
footer.end {{ margin-top: 40px; color: var(--muted); font-size: 13px; text-align: center; }}
@media (max-width: 900px) {{
  nav.toc {{ display: none; }}
  main {{ padding: 20px 18px 80px; }}
  header.top {{ padding: 8px 16px; }}
  .progress {{ width: 120px; }}
}}
@media print {{
  header.top, nav.toc, .codebar .copy, label.done {{ display: none !important; }}
  body {{ background: #fff; }}
  main {{ max-width: none; padding: 0; }}
  section.scene {{ break-inside: avoid; border-color: #ddd; }}
}}
</style>
</head>
<body>
<header class="top">
  <div class="brand">企业级开发流程 · 12 幕实操演练<small>ecom-ai-cs</small></div>
  <div class="progress-wrap">
    <div class="progress"><i id="progress-bar"></i></div>
    <span id="progress-text">0 / 0</span>
    <button class="reset" id="print" type="button">打印 / 存 PDF</button>
    <button class="reset" id="reset" type="button">重置进度</button>
  </div>
</header>
<div class="layout">
{nav_html}
<main>
{body}
<footer class="end">本页由 tools/build_manual_html.py 从 Markdown 生成，修改内容请改 .md 后重新生成。</footer>
</main>
</div>
<script>
(function () {{
  var KEY = 'ecomcs-manual-progress-v1';
  var boxes = Array.prototype.slice.call(document.querySelectorAll('input[data-scene]'));
  var bar = document.getElementById('progress-bar');
  var text = document.getElementById('progress-text');

  function load() {{
    try {{ return JSON.parse(localStorage.getItem(KEY) || '{{}}'); }} catch (e) {{ return {{}}; }}
  }}
  function save(state) {{
    try {{ localStorage.setItem(KEY, JSON.stringify(state)); }} catch (e) {{}}
  }}
  function refresh() {{
    var done = boxes.filter(function (b) {{ return b.checked; }}).length;
    bar.style.width = boxes.length ? (done / boxes.length * 100) + '%' : '0';
    text.textContent = done + ' / ' + boxes.length;
  }}
  var state = load();
  boxes.forEach(function (box) {{
    var id = box.getAttribute('data-scene');
    if (state[id]) {{ box.checked = true; box.closest('section').classList.add('done'); }}
    box.addEventListener('change', function () {{
      state[id] = box.checked;
      box.closest('section').classList.toggle('done', box.checked);
      save(state);
      refresh();
    }});
  }});
  refresh();

  document.getElementById('print').addEventListener('click', function () {{ window.print(); }});

  document.getElementById('reset').addEventListener('click', function () {{
    if (!confirm('确定清空全部完成记录？')) return;
    state = {{}}; save(state);
    boxes.forEach(function (b) {{ b.checked = false; b.closest('section').classList.remove('done'); }});
    refresh();
  }});

  document.querySelectorAll('.codebar .copy').forEach(function (btn) {{
    btn.addEventListener('click', function () {{
      var code = btn.closest('.codebox').querySelector('code').innerText;
      var done = function () {{
        btn.textContent = '已复制'; btn.classList.add('ok');
        setTimeout(function () {{ btn.textContent = '复制'; btn.classList.remove('ok'); }}, 1400);
      }};
      if (navigator.clipboard && window.isSecureContext) {{
        navigator.clipboard.writeText(code).then(done, fallback);
      }} else {{ fallback(); }}
      function fallback() {{
        var ta = document.createElement('textarea');
        ta.value = code; ta.style.position = 'fixed'; ta.style.opacity = '0';
        document.body.appendChild(ta); ta.select();
        try {{ document.execCommand('copy'); done(); }} catch (e) {{ alert('复制失败，请手动选中'); }}
        document.body.removeChild(ta);
      }}
    }});
  }});

  var links = Array.prototype.slice.call(document.querySelectorAll('nav.toc a'));
  var targets = links.map(function (a) {{ return document.getElementById(a.getAttribute('data-target')); }});
  function onScroll() {{
    var pos = window.scrollY + 90, current = 0;
    targets.forEach(function (t, i) {{ if (t && t.getBoundingClientRect().top + window.scrollY <= pos) current = i; }});
    links.forEach(function (a, i) {{ a.classList.toggle('active', i === current); }});
  }}
  window.addEventListener('scroll', onScroll, {{ passive: true }});
  onScroll();
}})();
</script>
</body>
</html>
"""


def main() -> int:
    md = SRC.read_text(encoding="utf-8")
    body, toc = convert(md)
    OUT.write_text(build_html(body, toc), encoding="utf-8")
    print(f"已生成 {OUT.name}")
    print(f"体积 {OUT.stat().st_size / 1024:.1f} KB | 目录项 {len(toc)} | 幕 {sum(1 for _, _, s in toc if s)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
