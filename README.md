# grumpydog.co

Marketing site for Grumpy Dog Software — websites, apps & honest tech help for rural Nova Scotia.

## Structure

The site is static HTML with no dependencies. The pages are generated from one source file:

- `_src/site.html` — the source. It holds the shared head, nav, footer and each page's content as named `@part` blocks. Edit this file.
- `_src/build.py` — assembles the parts into the published pages and writes `sitemap.xml`.
- `index.html`, `services.html`, `pricing.html`, `work.html`, `about.html`, `contact.html`, `404.html` — generated. Do not edit them directly.
- `privacy/broodi/index.html` — hand-written, not generated.
- `assets/` — logo and app artwork. `logo.png` (1024px) and `favicon.png` (256px) are derived from `logo.jpg`.
- `CNAME` — custom domain for GitHub Pages.

GitHub Pages serves `services.html` at `/services`, so the real URLs are `/`, `/services`, `/pricing`, `/work`, `/about` and `/contact`. The app pages (`/#broodi`, `/#nutriroots`, `/#pethealth`) are still views on the home page. Old hash links such as `/#services` and `/#contact` redirect to the real URLs.

## Making a change

1. Edit `_src/site.html` (or the page list at the top of `_src/build.py` to add a page or change a title).
2. Run `python3 _src/build.py`.
3. Run `python3 _src/build.py --check`. It fails if a generated page is stale or an internal link does not resolve.
4. Commit the source and the generated pages together.

`sitemap.xml` dates come from `_src/lastmod.json`, which the build updates whenever a page's content changes.

## Contact form

The Get in Touch form posts to [Web3Forms](https://web3forms.com) (account: hello@grumpydog.co) and falls back to a `mailto:` link if the request fails. The access key in `index.html` is public by design.

## Deploying

Hosted on GitHub Pages from the `main` branch root. Pushing to `main` deploys.
