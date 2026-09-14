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
    urls.append(f'- {project["name"]}: {canonical}')
index = (built / 'projects/index.html').read_text()
index = index.replace('<link rel="stylesheet" href="/assets/css/project-gallery.css">', '<style>' + (built / 'assets/css/project-gallery.css').read_text() + '</style>')
for slug in projects:
    index = index.replace('href="/papers/' + slug + '/"', 'href="' + slug + '.html"')
for project in projects.values():
    for media in [project] + project.get('related_publications', []):
        for figure in media.get('figures', []):
            data = 'data:image/png;base64,' + base64.b64encode((built / figure['src'].lstrip('/')).read_bytes()).decode()
            index = index.replace('src="' + figure['src'] + '"', 'src="' + data + '"')
index = re.sub(r'(href|src)="(/[^\"]*)"', lambda m: m[1] + '="' + base + m[2] + '"', index)
(out / 'index.html').write_text(index)
(out / 'project-urls.txt').write_text('Project URLs after deployment\n\n'+'\n'.join(urls)+'\n')
print(f'Exported {len(projects)} self-contained previews and a local directory to {out}')
