import { SITE } from '../config';

const abs = (path: string) => new URL(path, SITE.url).toString();

export const organizationId = `${SITE.url}/#organization`;
export const personId = `${SITE.url}/#matteo-prina`;
export const websiteId = `${SITE.url}/#website`;

export const organization = {
  '@type': 'Organization',
  '@id': organizationId,
  name: SITE.name,
  url: SITE.url,
  logo: { '@type': 'ImageObject', url: abs('/brand/icon.png'), width: 1024, height: 1024 },
  email: SITE.email,
  founder: { '@id': personId },
  description: SITE.description,
};

export const person = {
  '@type': 'Person',
  '@id': personId,
  name: SITE.owner.name,
  jobTitle: SITE.owner.jobTitle,
  url: SITE.owner.url,
  sameAs: [SITE.owner.url],
  knowsAbout: [
    'Energy system modelling',
    'Artificial intelligence',
    'Machine learning for research',
    'Horizon Europe proposals',
    'Research funding',
  ],
  address: { '@type': 'PostalAddress', addressLocality: SITE.owner.city, addressCountry: 'IT' },
};

export const website = {
  '@type': 'WebSite',
  '@id': websiteId,
  url: SITE.url,
  name: SITE.name,
  description: SITE.description,
  inLanguage: 'en',
  publisher: { '@id': organizationId },
};

export function breadcrumbs(items: { name: string; path: string }[]) {
  return {
    '@type': 'BreadcrumbList',
    itemListElement: items.map((item, i) => ({
      '@type': 'ListItem',
      position: i + 1,
      name: item.name,
      item: abs(item.path),
    })),
  };
}

export function graph(...nodes: Record<string, unknown>[]) {
  return { '@context': 'https://schema.org', '@graph': nodes };
}

export { abs };
