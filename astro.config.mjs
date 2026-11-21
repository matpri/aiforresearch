// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://aiforresearch.eu',
  trailingSlash: 'always',
  build: {
    // Keep all CSS in external files so the Content-Security-Policy needs no 'unsafe-inline' for styles.
    inlineStylesheets: 'never',
    format: 'directory',
  },
  vite: {
    build: { assetsInlineLimit: 0 },
  },
  integrations: [
    sitemap({
      filter: (page) => !page.includes('/contact/thanks/'),
    }),
  ],
});
