import { getCollection, type CollectionEntry } from 'astro:content';

export function formatDate(date: Date): string {
  return date.toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'Europe/Rome' });
}

export async function getSortedNews(): Promise<CollectionEntry<'news'>[]> {
  const posts = await getCollection('news');
  return posts.sort((a, b) => b.data.pubDate.valueOf() - a.data.pubDate.valueOf());
}

export function readingTime(text: string): number {
  return Math.max(1, Math.round(text.split(/\s+/).length / 220));
}
