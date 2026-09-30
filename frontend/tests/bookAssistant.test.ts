/**
 * The in-browser assistant is tested against the REAL generated index of the
 * book (static/search-index.json), not a toy fixture, so these tests fail if
 * a chapter disappears or retrieval quality regresses.
 */
import { readFileSync } from 'fs';
import { join } from 'path';
import { Bm25, answerFromBook, sentences, stem, tokenize, type SearchIndex } from '../src/lib/bookAssistant';

const index: SearchIndex = JSON.parse(readFileSync(join(__dirname, '..', 'static', 'search-index.json'), 'utf8'));
const bm25 = new Bm25(index.chunks);
const topRoute = (q: string) => bm25.search(q, { limit: 1 })[0]?.chunk.route;

describe('tokenize', () => {
  it('drops stopwords, splits hyphens and stems plurals', () => {
    expect(tokenize('What are the ROS-2 topics?')).toEqual(expect.arrayContaining(['ros2', 'ros', 'topic']));
    expect(tokenize('What are the')).toEqual([]);
    expect(stem('sensors')).toBe('sensor');
    expect(stem('policies')).toBe('policy');
    expect(stem('class')).toBe('class');
  });
});

describe('retrieval over the whole book', () => {
  it('indexes every module', () => {
    const modules = new Set(index.chunks.map((c) => c.module));
    for (const m of ['module-1-intro', 'module-2-ros2', 'module-3-simulation', 'module-4-isaac', 'module-5-vla']) {
      expect(modules.has(m)).toBe(true);
    }
  });

  it.each([
    ['difference between a ROS 2 service and an action', 'module-2-ros2/services-actions-parameters'],
    ['URDF joint types and links', 'module-2-ros2/urdf-tf2-launch'],
    ['domain randomization for sim-to-real', 'module-3-simulation/sim-to-real'],
    ['ros_gz_bridge configuration for a simulated lidar', 'module-3-simulation/sensor-simulation'],
    ['USD prims layers and references', 'module-4-isaac/isaac-sim-and-usd'],
    ['cuVSLAM visual SLAM', 'module-4-isaac/isaac-ros-perception'],
    ['Nav2 costmaps and behavior trees', 'module-4-isaac/navigation-and-locomotion'],
    ['action tokenization in VLA models', 'module-5-vla/vla-architecture'],
    ['Whisper speech recognition', 'module-5-vla/voice-to-action'],
    ['SayCan task planning with a skill library', 'module-5-vla/llm-task-planning'],
    ['IMU drift complementary filter', 'module-1-intro/sensor-systems'],
  ])('"%s" finds %s', (query, route) => {
    expect(topRoute(query)).toBe(route);
  });
});

describe('answerFromBook', () => {
  it('answers only with sentences that exist in the cited chunks', () => {
    const res = answerFromBook(bm25, 'What is Quality of Service in ROS 2?');
    expect(res.grounded).toBe(true);
    expect(res.sources.length).toBeGreaterThan(0);
    const cited = res.sources.map((s) => index.chunks.find((c) => c.id === s.chunkId)!);
    expect(cited.every(Boolean)).toBe(true);
    const body = res.answer.split('\n\n').slice(1).map((p) => p.replace(/ \[\d\]$/, ''));
    const corpus = cited.map((c) => sentences(c.text).join(' ')).join(' ');
    for (const para of body) for (const s of sentences(para)) expect(corpus).toContain(s);
  });

  it('builds links that point at real section anchors', () => {
    const res = answerFromBook(bm25, 'domain randomization');
    expect(res.sources[0].url).toMatch(/^docs\/module-3-simulation\/sim-to-real#[a-z0-9-]+$/);
  });

  it('says so instead of guessing when the book has nothing', () => {
    const res = answerFromBook(bm25, 'best biryani recipe in Karachi');
    expect(res.grounded).toBe(false);
    expect(res.sources).toEqual([]);
    expect(res.answer).toMatch(/couldn't find/);
  });

  it('uses highlighted text as context', () => {
    const res = answerFromBook(bm25, 'explain this', { selectedText: 'zero moment point balance for bipedal walking' });
    expect(res.grounded).toBe(true);
    expect(res.answer).toMatch(/highlighted passage/);
  });
});
