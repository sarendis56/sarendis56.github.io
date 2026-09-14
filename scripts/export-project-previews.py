#!/usr/bin/env python3
"""Export a local project directory and self-contained HTML previews; never deploys."""
import argparse
import base64
import html
import json
import re
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('built_site', type=Path)
parser.add_argument('output_directory', type=Path)
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
built = args.built_site.resolve()
out = args.output_directory.resolve()
if out == root or root in out.parents:
    parser.error('Choose an output directory outside the website repository.')
out.mkdir(parents=True, exist_ok=True)
projects = json.loads((root / '_data/projects.json').read_text())
css = (built / 'assets/css/project.css').read_text()
cards = []
urls = []
for slug, project in projects.items():
    text = (built / 'papers' / slug / 'index.html').read_text()
    canonical = re.search(r'<link rel="canonical" href="([^"]+)"', text).group(1)
    base = canonical.split('/papers/')[0]
    media = [project] + project.get('related_publications', [])
    figure = next(f for m in media for f in m.get('figures', []))
    thumbnail = ''
    for m in media:
        for f in m.get('figures', []):
            data = 'data:image/png;base64,' + base64.b64encode((built / f['src'].lstrip('/')).read_bytes()).decode()
            text = text.replace('"' + f['src'] + '"', '"' + data + '"')
            if f is figure:
                thumbnail = data
    text = text.replace('<link rel="stylesheet" href="/assets/css/project.css">', '<style>' + css + '</style>')
    text = re.sub(r'(href|src)="(/[^\"]*)"', lambda m: m[1] + '="' + base + m[2] + '"', text)
    # Local exports never become a second indexable copy if shared elsewhere.
    text = re.sub(r'<meta name="robots" content="[^"]*">', '<meta name="robots" content="noindex, nofollow">', text)
    banner = '<aside style="font:14px/1.6 system-ui;padding:12px 20px;background:var(--soft);border-bottom:1px solid var(--line)"><a href="index.html">← All project previews</a> · Local preview · Public URL after deployment: <a href="' + canonical + '">' + canonical + '</a></aside>'
    text = text.replace('<body>', '<body>' + banner)
    (out / (slug + '.html')).write_text(text)
    name = html.escape(project['name'])
    cards.append(f'<article class="card"><a class="picture" href="{slug}.html"><img src="{thumbnail}" alt="{html.escape(figure["alt"],quote=True)}" loading="lazy"></a><div class="content"><p class="status">{html.escape(project["status"])}</p><h2><a href="{slug}.html">{name}</a></h2><p>{html.escape(project["summary"])}</p><p><a class="button" href="{slug}.html">Open local preview →</a></p><label>Public URL after deployment<input readonly aria-label="Public URL for {name}" value="{canonical}" onclick="this.select()"></label><a class="live" href="{canonical}">Open public URL ↗</a></div></article>')
    urls.append(f'- {project["name"]}: {canonical}')
style = '''*{box-sizing:border-box}body{margin:0;background:#f4f6f8;color:#202830;font:16px/1.65 system-ui,sans-serif}main{max-width:1180px;margin:auto;padding:48px 24px}header{max-width:800px;margin-bottom:32px}h1{font:44px/1.1 Georgia,serif;letter-spacing:-.03em;margin:12px 0 22px}h2{font:27px/1.2 Georgia,serif;margin:12px 0}a{color:#175a83;text-underline-offset:3px}.eyebrow,.status{font-size:13px;font-weight:600;color:#175a83}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(310px,1fr));gap:24px}.card{background:white;border:1px solid #dae2e9;border-radius:12px;overflow:hidden}.picture{display:flex;align-items:center;height:190px;padding:20px;border-bottom:1px solid #e2e8ed;background:white}.picture img{width:100%;max-height:155px;object-fit:contain}.content{padding:24px}.content>p{font-size:15px}.button{display:inline-block;font-weight:600}label{display:block;font-size:12px;color:#536271}input{display:block;width:100%;padding:10px;margin:6px 0;border:1px solid #dae2e9;border-radius:4px;font:12px system-ui;background:#f4f6f8;color:#202830}.live{font-size:12px}footer{margin-top:32px;color:#536271;font-size:14px}@media(max-width:400px){main{padding:28px 16px}.grid{grid-template-columns:1fr}h1{font-size:36px}}'''
index = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>Project previews and URLs</title><style>' + style + '</style></head><body><main><header><p class="eyebrow">PEICHUN HUA · LOCAL PROJECT DIRECTORY</p><h1>Nine projects, one bookmark.</h1><p>Every project includes a research summary, a source figure, and a results table. Open a local preview below or select its public URL to copy it. The ACSAC full paper and ISCAS demo share one page.</p><p>This directory stays on your computer and is absent from your public website navigation. The public URLs become available after deploying the updated repository.</p><p>Crawler discovery: <a href="https://peichun.xyz/robots.txt">robots.txt</a> → <a href="https://peichun.xyz/sitemap.xml">sitemap.xml</a> → project pages → papers. The sitemap lists the exact page addresses, so crawlers do not need to guess their names. Discovery does not guarantee indexing.</p></header><div class="grid">' + ''.join(cards) + '</div><footer>Preview images are embedded. Source-paper links open their public URLs. Generated from the built website; no publishing action was performed.</footer></main></body></html>'
(out / 'index.html').write_text(index)
(out / 'project-urls.txt').write_text('Project URLs after deployment\n\n'+'\n'.join(urls)+'\n')
print(f'Exported {len(projects)} self-contained previews and a local directory to {out}')
