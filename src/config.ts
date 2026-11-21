export const SITE = {
  name: 'AI for Research',
  url: 'https://aiforresearch.eu',
  tagline: 'AI news, tools and insights for researchers',
  description:
    'A free weekly digest of the AI news that matters for scientists: new models, research tools, AI co-scientists, EU policy and funding.',
  email: 'admin@aiforresearch.eu',
  locale: 'en_GB',
  owner: {
    name: 'Matteo Prina',
    jobTitle: 'Senior Researcher in Energy Modelling and Artificial Intelligence',
    url: 'https://matteoprina.com',
    city: 'Milan',
    country: 'Italy',
  },
  // Public, non-secret build-time values (configure on Render).
  web3formsKey: import.meta.env.PUBLIC_WEB3FORMS_KEY ?? '',
  cfAnalyticsToken: import.meta.env.PUBLIC_CF_ANALYTICS_TOKEN ?? '',
};

export const NAV = [
  { href: '/news/', label: 'Weekly News' },
  { href: '/services/', label: 'Services' },
  { href: '/about/', label: 'About' },
  { href: '/contact/', label: 'Contact' },
];
