#!/usr/bin/env python3
"""Build grumpydog.co from _src/site.html.

    python3 _src/build.py           write the pages and sitemap.xml
    python3 _src/build.py --check   verify the committed pages are up to date and links resolve

No dependencies. GitHub Pages serves services.html at /services with HTTP 200,
so each page is written as a root-level .html file.
"""
import datetime
import hashlib
import json
import re
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent
REPO = SRC.parent
ORIGIN = "https://grumpydog.co"

HOME_TITLE = "Grumpy Dog Software — Websites, Apps &amp; Tech Help in Rural Nova Scotia"
HOME_DESC = ("Female-owned software company in the Annapolis Valley building websites, mobile apps, and practical "
             "tools for farms, shops, trades, and local businesses across rural Nova Scotia.")

# file -> page definition. `nav` is the data-page value of the nav link to mark active.
PAGES = {
    "index.html": dict(
        path="/", key="home", nav="home", parts=["home", "apps"], scripts=["script-common", "script-home"],
        title=HOME_TITLE, description=HOME_DESC,
        social_title="Grumpy Dog Software — Practical Tech for Rural Nova Scotia",
        social_description="Female-owned, farm-rooted software company building websites, apps, and practical tools in the Annapolis Valley.",
        priority="1.0"),
    "services.html": dict(
        path="/services", key="services", nav="services", parts=["services"],
        title="Our Services — Grumpy Dog Software",
        description="Websites, custom tools, managed hosting, and plain-spoken technology guidance for rural businesses.",
        priority="0.9"),
    "pricing.html": dict(
        path="/pricing", key="pricing", nav="services", parts=["pricing"],
        title="Pricing — Grumpy Dog Software",
        description="Plain pricing for websites, managed hosting, and technology guidance from Grumpy Dog Software in rural Nova Scotia.",
        priority="0.8"),
    "work.html": dict(
        path="/work", key="work", nav="work", parts=["work"],
        title="Our Work — Grumpy Dog Software",
        description="See customer websites built by Grumpy Dog Software for rural businesses and working farms.",
        priority="0.8"),
    "about.html": dict(
        path="/about", key="about", nav="staff", parts=["staff"],
        title="About Grumpy Dog Software — Our Staff",
        description="Meet Celina and the canine leadership team behind Grumpy Dog Software.",
        priority="0.7"),
    "contact.html": dict(
        path="/contact", key="contact", nav="contact", parts=["contact"], scripts=["script-common", "script-contact"],
        title="Contact Grumpy Dog Software",
        description="Talk with Grumpy Dog Software about your website, app, custom tool, hosting, or technology project.",
        priority="0.9"),
    "web-design-annapolis-valley.html": dict(
        path="/web-design-annapolis-valley", key="valley", nav=None, parts=["valley"],
        title="Web Design and Tech Help in the Annapolis Valley, Nova Scotia | Grumpy Dog Software",
        description=("Websites, apps and plain-English tech help for farms, shops, restaurants, inns and makers "
                     "across the Annapolis Valley, from Windsor to Digby."),
        priority="0.8"),
    "404.html": dict(
        path="/404", key="notfound", nav=None, parts=["notfound"], robots="noindex, follow", sitemap=False,
        title="Page Not Found — Grumpy Dog Software",
        description="That page isn't here. Head back to the Grumpy Dog Software home page or get in touch."),
}

# Old hash routes -> real URLs. Hash links inside the source are rewritten with this map,
# and the home page redirects old bookmarks (a fragment never reaches the server, so this has to be script).
ROUTES = {
    "home": "/", "services": "/services", "work": "/work", "staff": "/about", "contact": "/contact",
    "pricing": "/pricing", "about": "/about",
    "services-websites": "/services#services-websites", "services-guidance": "/services#services-guidance",
    "websites": "/services#services-websites", "consulting": "/services#services-guidance",
}
HOME_HASHES = ["apps", "broodi", "nutriroots", "pethealth"]  # still live as hash views on the home page

# Pages not built from site.html. lastmod is the date of the file's last commit.
STATIC_SITEMAP = [("/privacy/broodi/", "2026-07-19", "0.3")]


def load_parts():
    text = (SRC / "site.html").read_text(encoding="utf-8")
    parts = dict(re.findall(r"<!-- @part ([\w-]+) -->\n(.*?)\n<!-- @endpart -->", text, flags=re.S))
    if "head" not in parts:
        sys.exit("site.html: no @part head found")
    return parts


def expand(body, parts, depth=0):
    if depth > 5:
        sys.exit("site.html: @include nested too deep")
    def repl(m):
        name = m.group(1)
        if name not in parts:
            sys.exit(f"site.html: @include of unknown part '{name}'")
        return expand(parts[name], parts, depth + 1)
    return re.sub(r"<!-- @include ([\w-]+) -->", repl, body)


def rewrite_links(html, page):
    def repl(m):
        target = m.group(1)
        if target in ROUTES:
            url = ROUTES[target]
            base, _, frag = url.partition("#")
            if base == page["path"] and frag:
                url = "#" + frag  # same page: plain in-page anchor
            return f'href="{url}"'
        if target in HOME_HASHES:
            return m.group(0) if page["key"] == "home" else f'href="/#{target}"'
        return m.group(0)
    return re.sub(r'href="#([\w-]+)"', repl, html)


def mark_nav(nav, key):
    if not key:
        return nav
    def repl(m):
        tag = m.group(0)
        if 'class="' in tag:
            tag = tag.replace('class="', 'class="active ', 1)
        else:
            tag = tag.replace("<a ", '<a class="active" ', 1)
        return tag.replace("<a ", '<a aria-current="page" ', 1)
    out, n = re.subn(rf'<a [^>]*data-page="{key}"[^>]*>', repl, nav)
    if n != 1:
        sys.exit(f"nav: expected one link with data-page={key}, found {n}")
    return out


def render(page, parts):
    head = parts["head"]
    is_home = page["key"] == "home"
    head = re.sub(r"<!-- @if home -->\n(.*?)\n<!-- @endif -->\n?", (lambda m: m.group(1) + "\n") if is_home else "", head, flags=re.S)
    redirects = {k: v for k, v in ROUTES.items() if k != "home"}
    redirect_script = ("window.GD_REDIRECTS=" + json.dumps(redirects, separators=(",", ":"))
                       + ";(function(){var t=window.GD_REDIRECTS[location.hash.slice(1)];if(t)location.replace(t)})();")
    values = {
        "title": page["title"],
        "description": page["description"],
        "robots": page.get("robots", "index, follow, max-image-preview:large"),
        "canonical": ORIGIN + page["path"],
        "social_title": page.get("social_title", page["title"]),
        "social_description": page.get("social_description", page["description"]),
        "redirect_script": redirect_script,
    }
    for k, v in values.items():
        head = head.replace("{{" + k + "}}", v)
    if page["key"] == "notfound":  # the 404 is served at every unknown URL, so it has no canonical address
        head = re.sub(r'<link rel="canonical"[^>]*>\n|<meta property="og:url"[^>]*>\n', "", head)
    left = re.findall(r"\{\{\w+\}\}", head)
    if left:
        sys.exit(f"head: unfilled placeholders {left}")

    body = "\n\n".join(expand(parts[p], parts) for p in page["parts"])
    # exactly one .page is visible on load, so the content is there without script
    body = body.replace('<div class="page" id="page-', '<div class="page active" id="page-', 1) \
        if 'class="page active"' not in body else body
    scripts = "\n\n".join(parts[s] for s in page.get("scripts", ["script-common"]))
    html = "\n".join([
        head, "<body>", mark_nav(parts["nav"], page["nav"]), "", body, "", parts["footer"], "",
        "<script>", scripts, "</script>", "</body></html>", ""])
    html = rewrite_links(html, page)
    note = "<!-- Generated by _src/build.py from _src/site.html. Do not edit this file directly. -->"
    return html.replace("<head>", "<head>\n" + note, 1)


def build_all():
    parts = load_parts()
    return {name: render(page, parts) for name, page in PAGES.items()}


def lastmods(outputs, update):
    """Date each page last changed, tracked by content hash so the sitemap never drifts."""
    path = SRC / "lastmod.json"
    state = json.loads(path.read_text()) if path.exists() else {}
    today = datetime.date.today().isoformat()
    for name, html in outputs.items():
        digest = hashlib.sha256(html.encode("utf-8")).hexdigest()[:16]
        if state.get(name, {}).get("hash") != digest:
            state[name] = {"hash": digest, "date": today}
    if update:
        path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
    return state


def sitemap(state):
    rows = [(PAGES[n]["path"], state[n]["date"], PAGES[n]["priority"]) for n in PAGES if PAGES[n].get("sitemap", True)]
    rows += STATIC_SITEMAP
    out = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path, date, prio in rows:
        out += ["  <url>", f"    <loc>{ORIGIN}{path}</loc>", f"    <lastmod>{date}</lastmod>", f"    <priority>{prio}</priority>", "  </url>"]
    return "\n".join(out + ["</urlset>", ""])


def resolves(url):
    path = url.split("#")[0].split("?")[0]
    if path in ("", "/"):
        return (REPO / "index.html").exists()
    p = REPO / path.lstrip("/")
    return p.is_file() or p.with_suffix(".html").is_file() or (p / "index.html").is_file()


def check(outputs, state):
    problems = []
    for name, html in outputs.items():
        f = REPO / name
        if not f.exists() or f.read_text(encoding="utf-8") != html:
            problems.append(f"{name} is out of date - run python3 _src/build.py")
        for url in sorted(set(re.findall(r'(?:href|src)="(/[^"/][^"]*|/)"', html))):
            if not resolves(url):
                problems.append(f"{name}: {url} does not resolve to a file")
        for frag in sorted(set(re.findall(r'href="#([\w-]+)"', html))):
            if f'id="{frag}"' not in html and not (PAGES[name]["key"] == "home" and frag in HOME_HASHES):
                problems.append(f"{name}: #{frag} has no matching id on the page")
        if html.count('class="page active"') != 1:
            problems.append(f"{name}: expected exactly one visible page")
        if PAGES[name]["key"] != "home" and "application/ld+json" in html:
            problems.append(f"{name}: home-only structured data leaked")
    titles = [p["title"] for p in PAGES.values()]
    if len(set(titles)) != len(titles):
        problems.append("page titles are not unique")
    sm = REPO / "sitemap.xml"
    if not sm.exists() or sm.read_text() != sitemap(state):
        problems.append("sitemap.xml is out of date - run python3 _src/build.py")
    return problems


def main():
    checking = "--check" in sys.argv
    outputs = build_all()
    state = lastmods(outputs, update=not checking)
    if checking:
        problems = check(outputs, state)
        for p in problems:
            print("FAIL ", p)
        print(f"{len(outputs)} pages checked, {len(problems)} problems")
        sys.exit(1 if problems else 0)
    for name, html in outputs.items():
        (REPO / name).write_text(html, encoding="utf-8")
        print(f"wrote {name:14s} {len(html) // 1024} KB")
    (REPO / "sitemap.xml").write_text(sitemap(state))
    print("wrote sitemap.xml")


if __name__ == "__main__":
    main()
