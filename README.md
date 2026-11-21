# aiforresearch.eu

Source code for [AI for Research](https://aiforresearch.eu), a weekly digest of AI news for researchers.

- **Site:** [Astro](https://astro.build) static site, no server code, no database, no cookies.
- **Hosting:** Render static site, deployed on every push to `main` (`render.yaml`).
- **Weekly issue:** every Monday at 06:00 UTC a GitHub Action runs `scripts/generate_news.py`, which reads the feeds in `scripts/sources.json`, asks Claude Haiku (`claude-haiku-5-5`) to select and summarise the stories, writes `src/content/news/<slug>.md`, checks the build and pushes. Render then deploys it.

## Project layout

```
src/pages/            pages (home, news, services, about, contact, legal)
src/content/news/     one Markdown file per weekly issue (written by the script)
src/components/       header, footer, SEO head, icons, logo
src/styles/global.css all styles (brand colours, dark mode, animations)
public/               favicons, Open Graph image, robots.txt, js/main.js
scripts/              weekly digest generator + source list
.github/workflows/    weekly digest + build check
render.yaml           Render config, including security headers (CSP, HSTS)
```

## Local development

```bash
npm install
npm run dev          # http://localhost:4321
npm run build        # output in dist/
```

Test the feeds without calling the API (no key needed):

```bash
pip install -r scripts/requirements.txt
python scripts/generate_news.py --dry-run
```

## Configuration

| Where | Name | What |
| --- | --- | --- |
| GitHub > Settings > Secrets and variables > Actions | `ANTHROPIC_API_KEY` | **Secret.** Used only by the weekly workflow. Never commit it. |
| Render > Environment | `PUBLIC_WEB3FORMS_KEY` | Web3Forms access key for the contact form. Empty = email link only. |
| Render > Environment | `PUBLIC_CF_ANALYTICS_TOKEN` | Cloudflare Web Analytics token (cookieless). Empty = no statistics. |

The `PUBLIC_*` values end up in the HTML, which is how these services are designed to work. Neither one is a secret.

After changing Render environment variables, trigger a manual deploy. If you enable analytics or the form, the privacy policy updates itself at the next build.

## Run the weekly issue by hand

GitHub > Actions > **Weekly digest** > **Run workflow**.

To change the sources, edit `scripts/sources.json`. The AI transparency page lists them automatically. To change the writing rules, edit `SYSTEM_PROMPT` and `BANNED_WORDS` in `scripts/generate_news.py`.

## Correcting an issue

Edit the Markdown file in `src/content/news/`, add a line at the end such as `*Correction (24 November 2026): the study was published in Nature, not Science.*`, and push.
