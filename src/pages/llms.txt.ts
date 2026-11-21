import type { APIContext } from 'astro';
import { SITE } from '../config';
import { getSortedNews } from '../lib/format';
import { FEED_COUNT } from '../lib/sources';

// llms.txt: a plain-text map of the site for AI search engines and assistants (https://llmstxt.org).
export async function GET(_context: APIContext) {
  const posts = await getSortedNews();
  const lines = [
    `# ${SITE.name}`,
    '',
    `> ${SITE.description}`,
    '',
    `AI for Research publishes a free weekly digest every Monday. Each issue is written by Claude Haiku (Anthropic) from ${FEED_COUNT} public sources, published without human review, labelled as AI-generated, and links every story to its original source. The site is run by ${SITE.owner.name} (${SITE.owner.jobTitle}, ${SITE.owner.city}, ${SITE.owner.country}).`,
    '',
    '## Main pages',
    `- [Weekly AI News](${SITE.url}/news/): archive of all issues`,
    `- [Services](${SITE.url}/services/): research proposal support (call analysis, first drafts, draft review), coming soon and not yet for sale`,
    `- [About](${SITE.url}/about/): who runs the site`,
    `- [AI transparency](${SITE.url}/ai-transparency/): how the digest is made, model, rules and full source list`,
    `- [Contact](${SITE.url}/contact/)`,
    '',
    '## Issues',
    ...posts.map((p) => `- [Issue #${p.data.issue}: ${p.data.title}](${SITE.url}/news/${p.id}/): ${p.data.description}`),
    '',
    '## Optional',
    `- [RSS feed](${SITE.url}/rss.xml)`,
    `- [Privacy policy](${SITE.url}/privacy/)`,
    `- [Legal notice](${SITE.url}/legal-notice/)`,
    '',
  ];
  return new Response(lines.join('\n'), { headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
}
