import rss from '@astrojs/rss';
import type { APIContext } from 'astro';
import { SITE } from '../config';
import { getSortedNews } from '../lib/format';

export async function GET(context: APIContext) {
  const posts = await getSortedNews();
  return rss({
    title: `${SITE.name}: weekly AI news for researchers`,
    description: SITE.description,
    site: context.site ?? SITE.url,
    trailingSlash: true,
    customData: '<language>en</language>',
    items: posts.map((post) => ({
      title: post.data.title,
      description: post.data.description,
      pubDate: post.data.pubDate,
      link: `/news/${post.id}/`,
      categories: post.data.tags,
    })),
  });
}
