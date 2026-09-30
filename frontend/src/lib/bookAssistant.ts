/**
 * In-browser textbook assistant: retrieval over a build-time index of the
 * whole book (static/search-index.json, produced by
 * scripts/build-search-index.mjs), BM25 ranking, and an extractive answer
 * made only of sentences that appear in the book, each cited to its section.
 *
 * It is the zero-cost path: no server, no API key, nothing leaves the
 * browser. When the FastAPI + Gemini + Qdrant backend is healthy, the chat
 * uses that instead (see ChatContext); this module is also the fallback when
 * the backend fails mid-conversation.
 *
 * Everything below `loadIndex` is pure and unit-tested.
 */

export interface IndexChunk {
  id: number;
  module: string;
  route: string; // doc route, e.g. "module-2-ros2/ros2-architecture"
  page: string; // page title
  section: string; // H2/H3 heading
  anchor: string; // Docusaurus heading id
  text: string;
}

export interface SearchIndex {
  version: number;
  chunks: IndexChunk[];
}

export interface RankedChunk {
  chunk: IndexChunk;
  score: number;
  /** Share of the query's information (IDF mass) this chunk actually contains, 0..1. */
  coverage: number;
}

/** Navigation and self-assessment sections repeat keywords without explaining them. */
const META_SECTION = /^(exercises|learning objectives|summary|chapters|what's next\??|prerequisites|topics covered|common pitfalls)$/i;

function sectionWeight(c: IndexChunk): number {
  let w = 1;
  if (META_SECTION.test(c.section.trim())) w *= 0.45;
  if (c.route.endsWith('/') || c.route.startsWith('instructor-guide')) w *= 0.6;
  return w;
}

export interface LocalAnswer {
  answer: string;
  sources: { moduleId: string; chapterId: string; section: string; score: number; url: string; chunkId: number }[];
  grounded: boolean;
}

const STOPWORDS = new Set(
  (
    'a an the and or but if then else of to in on at by for with from into onto over under ' +
    'is are was were be been being am do does did doing have has had having it its this that ' +
    'these those there here what which who whom whose when where why how can could should would ' +
    'will shall may might must i me my we our you your he she they them their his her as about ' +
    'than so such not no nor too very just also any all each some more most other only own same ' +
    'explain tell describe give show please mean means meaning define definition does work works use used using ' +
    'difference differences between compare comparison versus vs'
  ).split(' '),
);

/** Lowercase, split on non-alphanumerics, drop stopwords, light suffix stemming. */
export function tokenize(text: string): string[] {
  return (text.toLowerCase().match(/[a-z0-9]+(?:[-_][a-z0-9]+)*/g) ?? [])
    .flatMap((t) => (t.includes('-') || t.includes('_') ? [t.replace(/[-_]/g, ''), ...t.split(/[-_]/)] : [t]))
    .filter((t) => t.length > 1 && !STOPWORDS.has(t))
    .map(stem);
}

export function stem(t: string): string {
  if (t.length > 5 && t.endsWith('ing')) return t.slice(0, -3);
  if (t.length > 4 && t.endsWith('ies')) return t.slice(0, -3) + 'y';
  if (t.length > 4 && t.endsWith('es') && /(ss|x|ch|sh)es$/.test(t)) return t.slice(0, -2);
  if (t.length > 3 && t.endsWith('s') && !t.endsWith('ss')) return t.slice(0, -1);
  if (t.length > 5 && t.endsWith('ed')) return t.slice(0, -2);
  return t;
}

/** BM25 over chunks. Headings count three times: a matching section title is strong evidence. */
export class Bm25 {
  private docs: { tf: Map<string, number>; len: number }[];
  private df = new Map<string, number>();
  private avgLen: number;

  constructor(private chunks: IndexChunk[], private k1 = 1.4, private b = 0.72) {
    this.docs = chunks.map((c) => {
      const heading = `${c.page} ${c.section}`;
      const tokens = [...tokenize(heading), ...tokenize(heading), ...tokenize(heading), ...tokenize(c.text)];
      const tf = new Map<string, number>();
      for (const t of tokens) tf.set(t, (tf.get(t) ?? 0) + 1);
      for (const t of tf.keys()) this.df.set(t, (this.df.get(t) ?? 0) + 1);
      return { tf, len: tokens.length };
    });
    this.avgLen = this.docs.reduce((a, d) => a + d.len, 0) / Math.max(1, this.docs.length);
  }

  idf(term: string): number {
    const n = this.docs.length;
    const df = this.df.get(term) ?? 0;
    return Math.log(1 + (n - df + 0.5) / (df + 0.5));
  }

  search(query: string, { limit = 5, route }: { limit?: number; route?: string } = {}): RankedChunk[] {
    const terms = [...new Set(tokenize(query))];
    if (!terms.length) return [];
    const totalIdf = terms.reduce((a, t) => a + this.idf(t), 0);
    const scored: RankedChunk[] = [];
    this.docs.forEach((d, i) => {
      let score = 0;
      let matchedIdf = 0;
      for (const t of terms) {
        const f = d.tf.get(t);
        if (!f) continue;
        matchedIdf += this.idf(t);
        score += this.idf(t) * ((f * (this.k1 + 1)) / (f + this.k1 * (1 - this.b + (this.b * d.len) / this.avgLen)));
      }
      if (score > 0) {
        score *= sectionWeight(this.chunks[i]);
        // Mild boost for the chapter the reader is on.
        if (route && this.chunks[i].route === route) score *= 1.15;
        scored.push({ chunk: this.chunks[i], score, coverage: matchedIdf / totalIdf });
      }
    });
    return scored.sort((a, b) => b.score - a.score).slice(0, limit);
  }
}

/** Split prose into sentences, skipping code lines and list noise. */
export function sentences(text: string): string[] {
  const prose = text
    .split('\n')
    .filter((l) => !/^\s{2,}|^\s*[#$>|]|[;{}]\s*$|^\s*(def|class|import|from|return|ros2|colcon|<)\b/.test(l))
    .map((l) => l.replace(/^\s*(?:[-*]|\d+\.)\s+/, ''))
    .map((l) => (/[.!?:]$/.test(l.trim()) || !l.trim() ? l : `${l.trim()}.`))
    .join(' ')
    // Abbreviations are not sentence ends.
    .replace(/\b(et al|e\.g|i\.e|etc|vs|approx|Fig|Eq)\./g, (m) => m.replace(/\./g, '\u2024'))
    .replace(/\s+/g, ' ');
  return (prose.match(/[^.!?]+[.!?]+(?=\s|$)/g) ?? [])
    .map((s) => s.trim().replace(/\u2024/g, '.').replace(/`/g, '')).filter((s) => s.length > 30 && s.length < 400);
}

/**
 * Compose an extractive answer: the best-matching sentences from the top
 * chunks, in book order within each chunk, with numbered citations.
 */
export function answerFromBook(index: Bm25, query: string, opts: { route?: string; selectedText?: string } = {}): LocalAnswer {
  const q = opts.selectedText ? `${query} ${opts.selectedText}` : query;
  const hits = index.search(q, { limit: 8, route: opts.route });
  // Refuse rather than guess: the best passage must carry most of the query's meaning.
  if (!hits.length || hits[0].coverage < 0.5 || hits[0].score < 1.5) {
    return {
      answer:
        "I couldn't find that in the textbook. Try naming the concept directly, for example 'ROS 2 QoS', " +
        "'URDF joints', 'domain randomization' or 'VLA action tokens'.",
      sources: [],
      grounded: false,
    };
  }
  const qTerms = new Set(tokenize(q));
  // Up to three passages, at most two from the same section, so citations add breadth.
  const perSection = new Map<string, number>();
  const top = hits
    .filter((h) => h.score >= hits[0].score * 0.45)
    .filter((h) => {
      const key = `${h.chunk.route}#${h.chunk.anchor}`;
      perSection.set(key, (perSection.get(key) ?? 0) + 1);
      return (perSection.get(key) ?? 0) <= 2;
    })
    .slice(0, 3);
  const parts: string[] = [];
  const used = new Set<string>();
  top.forEach((h, i) => {
    const ranked = sentences(h.chunk.text)
      .map((s, pos) => ({ s, pos, overlap: tokenize(s).filter((t) => qTerms.has(t)).length }))
      .filter((x) => x.overlap > 0 && !used.has(x.s))
      .sort((a, b) => b.overlap - a.overlap || a.pos - b.pos)
      .slice(0, i === 0 ? 3 : 2)
      .sort((a, b) => a.pos - b.pos);
    const picked = ranked.length ? ranked : sentences(h.chunk.text).slice(0, 1).map((s, pos) => ({ s, pos, overlap: 0 }));
    picked.forEach((x) => used.add(x.s));
    if (picked.length) parts.push(`${picked.map((x) => x.s).join(' ')} [${i + 1}]`);
  });
  const lead = `From the textbook${opts.selectedText ? ' (about your highlighted passage)' : ''}:`;
  return {
    answer: parts.length ? `${lead}\n\n${parts.join('\n\n')}` : `${lead}\n\nSee the sections below.`,
    sources: top.map((h) => ({
      moduleId: h.chunk.module,
      chapterId: h.chunk.route,
      section: `${h.chunk.page} › ${h.chunk.section}`,
      score: Math.round(h.score * 100) / 100,
      url: `docs/${h.chunk.route}${h.chunk.anchor ? `#${h.chunk.anchor}` : ''}`,
      chunkId: h.chunk.id,
    })),
    grounded: true,
  };
}

let cached: Promise<Bm25> | null = null;

/** Fetch the index once per page load. `baseUrl` is the Docusaurus baseUrl. */
export function loadIndex(baseUrl: string): Promise<Bm25> {
  if (!cached) {
    cached = fetch(`${baseUrl}search-index.json`)
      .then((r) => {
        if (!r.ok) throw new Error(`search index ${r.status}`);
        return r.json() as Promise<SearchIndex>;
      })
      .then((idx) => new Bm25(idx.chunks))
      .catch((e) => {
        cached = null;
        throw e;
      });
  }
  return cached;
}
