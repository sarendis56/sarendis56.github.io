#!/usr/bin/env python3
"""Validate built discovery policy, metadata, links, and mirror integrity (stdlib only)."""
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit, unquote
from urllib.robotparser import RobotFileParser

root = Path(__file__).resolve().parents[1]
built = Path(sys.argv[1] if len(sys.argv) > 1 else root / '_site').resolve()
policy = json.loads((root / '_data/indexing.json').read_text())
projects = json.loads((root / '_data/projects.json').read_text())
mirrors = json.loads((root / '_data/paper_mirrors.json').read_text())
failures = []

def check(condition, message):
    if not condition:
        failures.append(message)

class Document(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.meta = {}
        self.links = []
        self.canonical = None
        self.ld = []
        self.in_ld = False
        self.feed(text)
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta':
            self.meta.setdefault(attrs.get('name', attrs.get('property', '')), []).append(attrs.get('content', ''))
        if tag == 'link' and attrs.get('rel') == 'canonical':
            self.canonical = attrs.get('href')
        if tag == 'a' and attrs.get('href'):
            self.links.append(attrs['href'])
        if tag == 'script' and attrs.get('type') == 'application/ld+json':
            self.in_ld = True
    def handle_endtag(self, tag):
        if tag == 'script':
            self.in_ld = False
    def handle_data(self, data):
        if self.in_ld:
            self.ld.append(json.loads(data))

home = Document((built / 'index.html').read_text())
base = home.canonical.rstrip('/')
check(base == 'https://peichun.xyz', 'Homepage canonical must use peichun.xyz')
check(not any('/papers/' in x for x in home.links), 'Project pages leaked into homepage navigation')
robots_text = (built / 'robots.txt').read_text()
check('{{' not in robots_text and '{%' not in robots_text, 'Unrendered robots.txt')
robots = RobotFileParser()
robots.parse(robots_text.splitlines())
xml = ET.parse(built / 'sitemap.xml')
urls = [e.text for e in xml.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
check(len(urls) == len(set(urls)), 'Duplicate sitemap URLs')
check(base + '/' in urls, 'Homepage absent from sitemap')
check('Sitemap: ' + base + '/sitemap.xml' in robots_text, 'Missing canonical sitemap declaration')

for path in policy['excluded_paths']:
    check(base + path not in urls, 'Excluded path leaked into sitemap: ' + path)
    for agent in ['OAI-SearchBot', 'Googlebot', 'Bingbot', 'ExampleBot']:
        permitted = policy['header_noindex_enabled'] and agent in ['Googlebot', 'Bingbot']
        for suffix in ['', '?download=1']:
            check(robots.can_fetch(agent, base + path + suffix) == permitted,
                  'Wrong excluded-path crawl policy: ' + agent + ' ' + path + suffix)
    file = root / path.lstrip('/')
    if file.is_file():
        deployed = built / path.lstrip('/')
        check(deployed.is_file() and file.read_bytes() == deployed.read_bytes(),
              'Excluded direct-link file changed or missing: ' + path)

for slug, project in projects.items():
    path = '/papers/' + slug + '/'
    text = (built / path.lstrip('/') / 'index.html').read_text()
    doc = Document(text)
    noindex = 'noindex' in ','.join(doc.meta.get('robots', []))
    check((base + path in urls) != noindex, 'Sitemap/noindex disagreement: ' + slug)
    check(doc.canonical == base + path, 'Wrong project canonical: ' + slug)
    check(doc.meta.get('citation_author') == project['authors'], 'Wrong authors: ' + slug)
    check(bool(doc.meta.get('citation_title', [''])[0]), 'Missing title: ' + slug)
    check(len(doc.ld) == 1 and doc.ld[0].get('@type') == 'ScholarlyArticle', 'Invalid structured data: ' + slug)
    check('{{' not in text and '{%' not in text, 'Unrendered Liquid: ' + slug)
    check('TODAES.pdf' not in text and 'CV.pdf' not in text, 'Excluded document linked from project: ' + slug)
    if project['status'].startswith('arXiv preprint'):
        check('citation_conference_title' not in doc.meta, 'Preprint mislabeled as conference publication: ' + slug)
    media_groups = [project] + project.get('related_publications', [])
    for media in media_groups:
        for figure in media.get('figures', []):
            image = built / figure['src'].lstrip('/')
            check(image.is_file(), 'Missing project figure: ' + figure['src'])
            check(bool(figure.get('alt')) and bool(figure.get('caption')), 'Figure needs alt text and caption: ' + slug)
        for table in media.get('tables', []):
            check(bool(table.get('caption')), 'Table needs caption: ' + slug)
            check(all(len(row) == len(table['columns']) for row in table['rows']), 'Table column count mismatch: ' + slug)
    for related in project.get('related_publications', []):
        old_path = '/papers/' + related['id'] + '/'
        check(base + old_path not in urls, 'Related publication still has separate sitemap entry')
        redirect = Document((built / old_path.lstrip('/') / 'index.html').read_text())
        check('noindex' in ','.join(redirect.meta.get('robots', [])), 'Legacy project redirect must be noindex')
        check(redirect.canonical == base + path, 'Legacy redirect canonical must match merged project')
    for href in doc.links + doc.meta.get('citation_pdf_url', []):
        target = urlsplit(urljoin(base + path, href))
        if target.netloc == urlsplit(base).netloc:
            local = built / unquote(target.path).lstrip('/')
            if target.path.endswith('/'):
                local /= 'index.html'
            check(local.is_file(), 'Broken local link: ' + slug + ' -> ' + href)
    if not noindex:
        for agent in ['Googlebot', 'Bingbot', 'OAI-SearchBot', 'ExampleBot']:
            check(robots.can_fetch(agent, base + path), 'Public project blocked: ' + agent + ' ' + slug)
            check(robots.can_fetch(agent, doc.meta['citation_pdf_url'][0]), 'Public paper blocked: ' + slug)

for mirror in mirrors:
    data = (built / mirror['path'].lstrip('/')).read_bytes()
    check(data.startswith(b'%PDF-'), 'Mirror is not a PDF: ' + mirror['path'])
    check(hashlib.sha256(data).hexdigest() == mirror['sha256'], 'Mirror hash mismatch: ' + mirror['path'])

for private_path in ['docs', 'scripts', 'main.tex', 'vendor', 'html_source_file']:
    check(not (built / private_path).exists(), 'Build exposed maintenance/source files: ' + private_path)
if failures:
    print('\n'.join('FAIL: ' + x for x in failures))
    sys.exit(1)
print(f'PASS: {len(projects)} project pages, {len(mirrors)} PDF mirrors, sitemap, citation metadata, links, and blacklist.')
if not policy['header_noindex_enabled']:
    print('PENDING HOSTING: excluded PDFs are crawl-blocked; HTTP noindex enforcement is not enabled.')
