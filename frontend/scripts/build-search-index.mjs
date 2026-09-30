#!/usr/bin/env node
/**
 * Builds static/search-index.json — the retrieval index behind the in-browser
 * textbook assistant.
 *
 * Every .mdx under docs/ is split into section-sized chunks (by H2/H3), with
 * frontmatter, imports and JSX stripped, and each chunk keeps the exact URL +
 * heading anchor Docusaurus will generate, so answers can cite a clickable
 * section. Runs automatically before `npm run build` / `npm start`.
 *
 * The same chunks also feed the FastAPI backend's vector ingestion when it is
 * deployed; this file is the zero-cost path that needs no server at all.
 */
import { readdirSync, readFileSync, statSync, writeFileSync, mkdirSync } from 'node:fs';
import { join, relative, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import GithubSlugger from 'github-slugger';

const ROOT = fileURLToPath(new URL('..', import.meta.url));
const DOCS = join(ROOT, 'docs');
const OUT = join(ROOT, 'static', 'search-index.json');
const MAX_CHARS = 1400;

function walk(dir) {
  return readdirSync(dir).flatMap((name) => {
    const full = join(dir, name);
    if (statSync(full).isDirectory()) return walk(full);
    return /\.mdx?$/.test(name) ? [full] : [];
  });
}

/** Docusaurus doc id → route: strip numeric prefixes; `x/index` → `x/`. */
export function docRoute(file) {
  const rel = relative(DOCS, file).split(sep).join('/').replace(/\.mdx?$/, '');
  const parts = rel.split('/').map((p) => p.replace(/^\d+-/, ''));
  if (parts[parts.length - 1] === 'index') parts[parts.length - 1] = '';
  return parts.join('/');
}

export function parseFrontmatter(src) {
  const m = src.match(/^---\n([\s\S]*?)\n---\n?/);
  if (!m) return { data: {}, body: src };
  const data = {};
  for (const line of m[1].split('\n')) {
    const kv = line.match(/^(\w[\w-]*):\s*(.+)$/);
    if (kv) data[kv[1]] = kv[2].replace(/^['"]|['"]$/g, '').trim();
  }
  return { data, body: src.slice(m[0].length) };
}

/** Turn MDX into readable plain text while keeping code (it is useful to retrieve). */
export function cleanMdx(body) {
  return body
    .replace(/^import .*$/gm, '')
    .replace(/^export .*$/gm, '')
    .replace(/\{\/\*[\s\S]*?\*\/\}/g, '')
    .replace(/^:::\w*.*$/gm, '')
    .replace(/<\/?(Tabs|TabItem|details|summary)[^>]*>/g, '')
    // <Exercise title="..." ...> — keep the human-readable attribute values.
    .replace(/<Exercise([\s\S]*?)>/g, (_, attrs) => {
      const vals = [...attrs.matchAll(/(title|hint)="([^"]*)"/g)].map((v) => v[2]);
      return vals.length ? `Exercise: ${vals.join('. ')}\n` : '';
    })
    .replace(/<\/Exercise>/g, '')
    .replace(/!\[[^\]]*\]\([^)]*\)/g, '')
    .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/(^|\s)\*([^*\n]+)\*/g, '$1$2')
    .replace(/\n{3,}/g, '\n\n');
}

export function chunkDoc(file, src) {
  const { data, body } = parseFrontmatter(src);
  const route = docRoute(file);
  const module = route.split('/')[0] || 'intro';
  const slugger = new GithubSlugger();
  const text = cleanMdx(body);
  const lines = text.split('\n');

  let pageTitle = data.title || route;
  const sections = [];
  let current = { heading: pageTitle, anchor: '', lines: [] };
  let inCode = false;
  for (const line of lines) {
    if (/^```/.test(line.trim())) inCode = !inCode;
    const h = !inCode && line.match(/^(#{1,3})\s+(.+?)\s*$/);
    if (h) {
      const heading = h[2].replace(/`/g, '');
      if (h[1] === '#') {
        pageTitle = heading;
        current.heading = heading;
        continue;
      }
      if (current.lines.join('').trim()) sections.push(current);
      current = { heading, anchor: slugger.slug(heading), lines: [] };
      continue;
    }
    current.lines.push(line);
  }
  if (current.lines.join('').trim()) sections.push(current);

  const chunks = [];
  for (const s of sections) {
    if (/^(learning objectives|exercises|summary)$/i.test(s.heading) && s.lines.join(' ').length < 80) continue;
    const body = s.lines.join('\n').trim();
    // Split long sections on paragraph boundaries.
    const paras = body.split(/\n\s*\n/);
    let buf = '';
    for (const p of paras) {
      if (buf && buf.length + p.length > MAX_CHARS) {
        chunks.push(buf);
        buf = '';
      }
      buf += (buf ? '\n\n' : '') + p;
    }
    if (buf.trim()) chunks.push(buf);
    // Attach metadata to every chunk produced for this section.
    for (let i = chunks.length - 1; i >= 0 && typeof chunks[i] === 'string'; i--) {
      chunks[i] = {
        module,
        route,
        page: pageTitle,
        section: s.heading,
        anchor: s.anchor,
        text: chunks[i].replace(/```\w*\n?/g, '').trim(),
      };
    }
  }
  return chunks.filter((c) => c.text.length > 40);
}

function main() {
  const files = walk(DOCS).sort();
  const chunks = files.flatMap((f) => chunkDoc(f, readFileSync(f, 'utf8')));
  chunks.forEach((c, i) => (c.id = i));
  mkdirSync(join(ROOT, 'static'), { recursive: true });
  writeFileSync(OUT, JSON.stringify({ version: 1, generated: new Date().toISOString(), chunks }));
  const pages = new Set(chunks.map((c) => c.route)).size;
  console.log(`[search-index] ${chunks.length} chunks from ${pages} pages -> static/search-index.json`);
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) main();
