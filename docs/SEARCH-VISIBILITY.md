# Search visibility

## Current setup

Public research pages live under `/papers/`. They are intentionally absent from
homepage navigation but appear in `/sitemap.xml`. People and crawlers receive the
same content. These are public URLs, not private or agent-only pages.

Five arXiv PDFs have local copies. Original arXiv records and PDFs remain linked
from the paper pages. `_data/paper_mirrors.json` records source URLs, retrieval
dates, and SHA-256 checksums. These snapshots do not automatically track revisions.

## Maintain the blacklist

Edit `_data/indexing.json`. `excluded_paths` initially contains:

- `/assets/docs/CV.pdf`
- `/assets/docs/TODAES.pdf`

Jekyll generates robots.txt from this list. An excluded local PDF suppresses its
publication entry on the homepage and also suppresses
its project page from the sitemap and adds `noindex, nofollow` to that HTML page.
For an excluded project, also blacklist `/papers/slug/`, or set `indexable: false`
in its front matter. An HTML page's noindex does not cover its linked PDF.
Keep excluded manuscripts out of publication data and public summaries.

The two original PDF links remain accessible, with unchanged PDF bytes.
The blacklist prevents cooperative crawling; it does not guarantee Google or
Google Scholar will never list the URL. It does not control copies on public
GitHub repositories, publishers, arXiv, or other domains. Agents acting on a direct
user request may still retrieve public URLs.

## Required hosting step: PDF noindex

GitHub Pages cannot set per-file HTTP response headers through this repository.
A `_headers` file, `.htaccess`, an HTML wrapper, or a noindex line in robots.txt
will not add the required PDF header on GitHub Pages.

Use a response-header rule on a proxy in front of peichun.xyz, or a host that
supports per-file headers. Match the exact blacklisted paths, including requests
with query strings, and set:

    X-Robots-Tag: noindex, nofollow

Run `ruby scripts/indexing-headers.rb` to print a Cloudflare response-header
Transform Rule generated from the same blacklist. This only prints configuration;
it does not change DNS, enable a proxy, or deploy anything.

Once the header rule is active, verify HTTP 200 and the noindex header:

    curl -I https://peichun.xyz/assets/docs/CV.pdf
    curl -I 'https://peichun.xyz/assets/docs/TODAES.pdf?download=1'

Only then set `header_noindex_enabled` to true. This allows Googlebot and Bingbot
to retrieve the PDFs to read the header while OAI-SearchBot remains excluded.
Other crawlers retain the blacklist. Verify the deployed robots.txt afterward.

If already indexed, use Search Console's removal tool for temporary suppression
while persistent noindex is processed. Confirm the github.io alias redirects to
the canonical domain. Alternate public copies require separate handling.
For genuinely private access, use authentication rather than crawler instructions.

## Add a public paper

1. Add a record to `_data/publications.yml` with a unique `id`.
2. Add its summary, method, evaluation, authors, year, topics, and accurate status
   to `_data/projects.json`. Preserve preprint versus accepted/published status.
3. Add `_projects/<id>.md` with `layout: project`, `project_id: <id>`, and
   `permalink: /papers/<id>/`. Do not add the publication `page` field unless you
   want a visible homepage Project Page button.
4. For mirrored PDFs, set `pdf` to the local asset path, retain `source_pdf`, and
   update `_data/paper_mirrors.json` with a verified checksum and retrieval date.
5. Run `bundle exec jekyll build` and `python3 scripts/check-indexing.py _site`.

Submit https://peichun.xyz/sitemap.xml in Google Search Console after deployment.
Sitemaps and metadata support discovery; indexing and ranking remain engine decisions.

## References

- https://developers.google.com/search/docs/crawling-indexing/block-indexing
- https://developers.google.com/search/docs/crawling-indexing/robots-meta-tag
- https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview
- https://developers.openai.com/api/docs/bots

## Figures, tables, and related publications

The ACSAC 2025 full paper and ISCAS 2026 live demo share the project page
`/papers/puf-transformer-protection/`. Their publication-list entries and citations
remain separate. The earlier OWL-ViT project URL redirects to the demo section and
is excluded from the sitemap.

All nine projects now include a source figure and a results table. The eight
individual project pages show their own method figure and evaluation table; the
merged hardware-protection page shows the ISCAS demonstration figure and table.
Each project in `_data/projects.json` supports `figures` and `tables` arrays. The shared template renders them with no JavaScript dependency. Figures
have alt text, captions, source links, stable dimensions, and full-size links.
Tables are selectable HTML with column and row headings and horizontal scrolling
on small screens. Prefer SVG for original vector figures and PNG for extracted
paper figures; use HTML tables instead of screenshots whenever the values matter.

Save images under `assets/img/projects/<project-id>/`. An example figure entry is:

```json
{
  "src": "/assets/img/projects/example/architecture.png",
  "width": 1200,
  "height": 600,
  "alt": "Describe the diagram's components and their relationship.",
  "caption": "Architecture of the proposed method.",
  "source_url": "/assets/docs/example.pdf#page=3",
  "source_label": "Paper, Figure 2"
}
```

An example table entry is:

```json
{
  "caption": "Measured latency in the evaluated configuration",
  "columns": ["Method", "Latency (ms)"],
  "rows": [["Baseline", "12.5"], ["Proposed", "8.1"]],
  "note": "Replace these illustrative values with verified paper results and state the experimental conditions.",
  "source_url": "/assets/docs/example.pdf#page=5",
  "source_label": "Paper, Table 2"
}
```

These are documentation examples, not published experimental results. The merged
hardware-protection page contains an actual example: Figure 1 extracted from the
ISCAS demo PDF and its embedded table transcribed as HTML. Accuracy without the
correct key is distinguished from the authorized inference timing measurements.

For a demo or follow-up belonging to an existing project, add a
`related_publications` entry using its publication `id`, `section_id`, `role`,
`summary`, `method`, and `results`; it may have its own `figures` and `tables`.
The publication data remains the source for authors, PDF links, and BibTeX.
Optional custom Markdown can also be placed after a project's front matter.

## Finding project URLs and exporting previews

The stable addresses are listed in `docs/PROJECT-URLS.md`. This reference is
excluded from the public site. The actual public discovery list is `/sitemap.xml`,
which is advertised in `/robots.txt` and generated from the Jekyll project
collection. Crawlers receive each exact URL there; they do not infer slugs from
paper titles. Keep existing permalinks stable when changing display names.

After building, export a local, bookmarkable directory and self-contained previews:

    python3 scripts/export-project-previews.py _site /absolute/path/outside/repository/project-previews

Open the exported `index.html` for the gallery with links to local previews.
The exported `project-urls.txt` lists public project URLs. Exports stay outside
the repository and are marked noindex. Public project pages remain indexable.

The website also serves the gallery at `/projects/`. It has no homepage link or
sitemap entry and uses `noindex, follow`, so it is intended for direct-link
access. It uses the same project data and blacklist as the individual pages.
Anyone with its URL can view it; this is not an access restriction.

Figure extraction provenance is recorded in `docs/figure-sources.json`. The eight
method figures are 300-dpi crops from the source PDFs; source-linked HTML tables
transcribe the selected values and state their experimental scope.
