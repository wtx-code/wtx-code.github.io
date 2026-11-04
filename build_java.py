# -*- coding: utf-8 -*-
"""
Java 教程构建脚本
把 java-mds/ 下的 Markdown 文章转换成 java/ 下的 HTML 页面（含左侧目录）。
用法：在项目根目录运行  python build_java.py
"""
import glob
import html
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(ROOT, "java-mds")
OUT_DIR = os.path.join(ROOT, "java")

HEADER = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} - Java 教程 - 吴腾鑫的官方网站</title>
<link rel="icon" type="image/png" href="../3.png">
<link rel="stylesheet" href="../css/style.css">
</head>
<body>
<header class="site-header">
  <div class="container">
    <a class="logo" href="../index.html">
      <img class="logo-img" src="../3.png" alt="一二头像 logo">
      <span>吴腾鑫的官方网站<span class="dot"></span></span>
    </a>
    <nav>
      <a href="../index.html">首页</a>
      <a href="index.html" style="color:#3b82f6">Java教程</a>
      <a href="../index.html#about">C语言教程</a>
      <a href="../index.html#about">Python教程</a>
    </nav>
  </div>
</header>

<div class="tutorial-wrap">
  <aside class="tutorial-nav">
    <h4>Java 教程</h4>
{nav}
  </aside>
  <article class="tutorial-main">
    <div class="crumb">Java 教程 / {crumb}</div>
    <h1>{title}</h1>
{body}
    <div class="pager">
{pager}
    </div>
  </article>
</div>

<footer class="site-footer">
  <div class="container">© 2026 wutenxin.com · 用热爱驱动</div>
</footer>
</body>
</html>
"""


def inline(text):
    s = html.escape(text, quote=False)
    s = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r'<img src="\2" alt="\1">', s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2" target="_blank">\1</a>', s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    return s


def md_to_html(md):
    lines = md.split("\n")
    out, para, i = [], [], 0

    def flush():
        if para:
            out.append("<p>" + inline(" ".join(para)) + "</p>")
            para.clear()

    while i < len(lines):
        line = lines[i]
        s = line.strip()

        # 代码块
        if s.startswith("```"):
            flush()
            code = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1
            out.append("<pre><code>" + html.escape("\n".join(code)) + "</code></pre>")
            continue

        if not s:
            flush()
            i += 1
            continue

        if s == "plaintext":          # 代码块前的语言标记，忽略
            i += 1
            continue

        # 标题
        m = re.match(r"^(#{1,4})\s+(.*)$", s)
        if m:
            flush()
            level = len(m.group(1))
            tag = "h2" if level <= 2 else "h3"
            out.append("<%s>%s</%s>" % (tag, inline(m.group(2)), tag))
            i += 1
            continue

        # 引用
        if s.startswith(">"):
            flush()
            quote = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip()[1:].strip())
                i += 1
            out.append("<blockquote>" + inline(" ".join(quote)) + "</blockquote>")
            continue

        # 表格
        if s.startswith("|"):
            flush()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                rows.append(cells)
                i += 1
            rows = [r for r in rows if not all(re.fullmatch(r":?-{2,}:?", c) for c in r)]
            if rows:
                t = ["<table>", "<tr>" + "".join("<th>" + inline(c) + "</th>" for c in rows[0]) + "</tr>"]
                for r in rows[1:]:
                    t.append("<tr>" + "".join("<td>" + inline(c) + "</td>" for c in r) + "</tr>")
                t.append("</table>")
                out.append("".join(t))
            continue

        # 列表
        if re.match(r"^[-*]\s+", s):
            flush()
            items = []
            while i < len(lines) and re.match(r"^[-*]\s+", lines[i].strip()):
                items.append(re.sub(r"^[-*]\s+", "", lines[i].strip()))
                i += 1
            out.append("<ul>" + "".join("<li>" + inline(it) + "</li>" for it in items) + "</ul>")
            continue

        if re.match(r"^\d+\.\s+", s):
            flush()
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s+", lines[i].strip()):
                items.append(re.sub(r"^\d+\.\s+", "", lines[i].strip()))
                i += 1
            out.append("<ol>" + "".join("<li>" + inline(it) + "</li>" for it in items) + "</ol>")
            continue

        para.append(s)
        i += 1

    flush()
    return "\n".join(out)


def parse(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    title = os.path.splitext(os.path.basename(path))[0]
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.S)
    body_md = text
    if m:
        for line in m.group(1).split("\n"):
            if line.strip().startswith("title:"):
                title = line.split(":", 1)[1].strip()
        body_md = m.group(2)
    slug = re.sub(r"^\d+[-_]", "", os.path.splitext(os.path.basename(path))[0])
    body_md = re.sub(r"^#{1,2}\s+.*\n+", "", body_md, count=1)   # 去掉与标题重复的一级标题
    return title, slug, md_to_html(body_md)


def main():
    files = sorted(glob.glob(os.path.join(SRC_DIR, "*.md")))
    if not files:
        print("java-mds/ 目录下没有 .md 文件")
        return
    pages = [parse(p) for p in files]

    nav_items = []
    for idx, (title, slug, _) in enumerate(pages):
        href = "index.html" if idx == 0 else slug + ".html"
        nav_items.append((title, href))

    for idx, (title, slug, body) in enumerate(pages):
        nav = "\n".join(
            '    <a href="%s"%s>%s</a>' % (href, ' class="active"' if k == idx else "", t)
            for k, (t, href) in enumerate(nav_items)
        )
        pager = []
        if idx > 0:
            pager.append('<a href="%s">← 上一篇：%s</a>' % (nav_items[idx - 1][1], nav_items[idx - 1][0]))
        else:
            pager.append("<span></span>")
        if idx < len(pages) - 1:
            pager.append('<a href="%s">下一篇：%s →</a>' % (nav_items[idx + 1][1], nav_items[idx + 1][0]))
        else:
            pager.append("<span></span>")

        page = HEADER.format(title=title, nav=nav, crumb=title, body=body, pager="\n".join(pager))
        out_name = "index.html" if idx == 0 else slug + ".html"
        with open(os.path.join(OUT_DIR, out_name), "w", encoding="utf-8") as f:
            f.write(page)
        print("生成 java/%s  (%s)" % (out_name, title))

    print("完成：共 %d 篇" % len(pages))


if __name__ == "__main__":
    main()
