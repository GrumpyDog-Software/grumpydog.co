# grumpydog.co

Marketing site for Grumpy Dog Software — websites, apps & honest tech help for rural Nova Scotia.

## Structure

- `index.html` — the entire site. A single-page app with hash-based routing (`#home`, `#broodi`, `#nutriroots`, `#pethealth`, `#websites`, `#consulting`, `#contact`). No build step, no dependencies.
- `assets/` — logo and app artwork. `logo.png` (1024px) and `favicon.png` (256px) are derived from `logo.jpg`.
- `CNAME` — custom domain for GitHub Pages.

## Contact form

The Get in Touch form posts to [Web3Forms](https://web3forms.com) (account: hello@grumpydog.co) and falls back to a `mailto:` link if the request fails. The access key in `index.html` is public by design.

## Deploying

Hosted on GitHub Pages from the `main` branch root. Pushing to `main` deploys.
