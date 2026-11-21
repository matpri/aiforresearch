import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

const news = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/news' }),
  schema: z.object({
    title: z.string(),
    description: z.string().max(200),
    pubDate: z.coerce.date(),
    issue: z.number().int().positive(),
    tags: z.array(z.string()).default([]),
    sources: z.number().int().nonnegative().default(0),
    aiGenerated: z.boolean().default(true),
    model: z.string().optional(),
  }),
});

export const collections = { news };
