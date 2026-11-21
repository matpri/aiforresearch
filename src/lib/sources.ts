import sources from '../../scripts/sources.json';

export interface Source { name: string; url: string; category: string; keywords?: boolean }
export const SOURCES = sources as Source[];
export const FEED_COUNT = SOURCES.length;
export const SOURCE_CATEGORIES = [...new Set(SOURCES.map((s) => s.category))];
