#!/usr/bin/env python3
"""Write sitemap.xml and robots.txt for www.dfchomeimprovement.com.

Re-run after adding or removing pages (build_html.py / build_blog.py, or a new
hand-written page). Each page is listed under its own <link rel="canonical">
URL, so the sitemap always agrees with the canonical tags. Pages marked
noindex and ad-only landing pages are left out.
"""
import os, re, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = "https://www.dfchomeimprovement.com"
# Ad / funnel pages that should not be offered to search engines
EXCLUDE = {"summer/index.html", "summer/thanks/index.html"}


def html_files():
    out = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for fn in filenames:
            if fn.endswith(".html"):
                out.append(os.path.relpath(os.path.join(dirpath, fn), ROOT))
    return sorted(out)


def lastmod(rel):
    try:
        d = subprocess.check_output(["git", "log", "-1", "--format=%cs", "--", rel],
                                    cwd=ROOT, text=True).strip()
        if d:
            return d
    except Exception:
        pass
    return None


def main():
    urls = []
    for rel in html_files():
        if rel in EXCLUDE:
            continue
        src = open(os.path.join(ROOT, rel), encoding="utf-8").read()
        if re.search(r'<meta name="robots" content="[^"]*noindex', src):
            continue
        m = re.search(r'<link rel="canonical" href="([^"]+)"', src)
        if m:
            loc = m.group(1)
        else:
            path = rel[:-len("index.html")] if rel.endswith("index.html") else rel
            loc = f"{SITE}/{path}"
        if not loc.startswith(SITE):
            continue
        urls.append((loc, lastmod(rel)))

    # one entry per URL, homepage first
    seen, rows = set(), []
    for loc, mod in sorted(urls, key=lambda u: (u[0] != SITE + "/", u[0])):
        if loc in seen:
            continue
        seen.add(loc)
        mod_tag = f"<lastmod>{mod}</lastmod>" if mod else ""
        rows.append(f"  <url><loc>{loc}</loc>{mod_tag}</url>")

    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                + "\n".join(rows) + "\n</urlset>\n")
    with open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8") as f:
        f.write("User-agent: *\n"
                "Disallow: /employee/\n\n"
                f"Sitemap: {SITE}/sitemap.xml\n")
    print(f"wrote sitemap.xml ({len(rows)} urls) and robots.txt")


if __name__ == "__main__":
    main()
