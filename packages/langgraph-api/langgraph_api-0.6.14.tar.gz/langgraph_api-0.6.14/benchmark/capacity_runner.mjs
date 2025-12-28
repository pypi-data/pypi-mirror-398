/*
 * Adaptive capacity benchmark orchestrator.
 * Ramps TARGET from RAMP_START up to RAMP_END by RAMP_MULTIPLIER.
 * For each level N: optional cleanup → run k6 (N users, 1 run each) → wait summary → decide next.
 * No retries anywhere; errors reduce success rate.
 */

import { execFileSync } from 'node:child_process';
import { readdirSync, readFileSync, writeFileSync, createReadStream } from 'node:fs';
import { join } from 'node:path';
import readline from 'node:readline';
import QuickChart from 'quickchart-js';
import { baseUrlToBaseUrlName } from './capacity_urls.mjs';

function envBool(name, def = false) {
  const v = process.env[name];
  if (v === undefined || v === null) return def;
  return String(v).toLowerCase() === 'true';
}

function envInt(name, def) {
  const v = process.env[name];
  if (!v) return def;
  const n = parseInt(v, 10);
  return Number.isFinite(n) ? n : def;
}

function envFloat(name, def) {
  const v = process.env[name];
  if (!v) return def;
  const n = parseFloat(v);
  return Number.isFinite(n) ? n : def;
}

function slugifyTimestamp(ts) {
  const raw = ts ?? new Date().toISOString();
  return raw.replace(/:/g, '-').replace(/\..+/, '');
}

const BASE_URL = process.env.BASE_URL;
const LANGSMITH_API_KEY = process.env.LANGSMITH_API_KEY;

const RAMP_START = envInt('RAMP_START', 10);
const RAMP_END = envInt('RAMP_END', 1000);
const RAMP_MULTIPLIER = envFloat('RAMP_MULTIPLIER', 10);
const WAIT_SECONDS = envInt('WAIT_SECONDS', 60);
const CLEAR_BETWEEN_STEPS = envBool('CLEAR_BETWEEN_STEPS', true);
const CLEAR_DELAY_SECONDS = envInt('CLEAR_DELAY_SECONDS', 5);

// Agent params
const DATA_SIZE = envInt('DATA_SIZE', 1000);
const DELAY = envInt('DELAY', 0);
const EXPAND = envInt('EXPAND', 50);
const STEPS = envInt('STEPS', 10);

if (!BASE_URL) {
  console.error('BASE_URL is required');
  process.exit(1);
}
if (!(RAMP_MULTIPLIER > 1)) {
  console.error('RAMP_MULTIPLIER must be > 1');
  process.exit(1);
}

function headers() {
  const h = { 'Content-Type': 'application/json' };
  if (LANGSMITH_API_KEY) h['x-api-key'] = LANGSMITH_API_KEY;
  return h;
}

async function cleanThreads() {
  if (!CLEAR_BETWEEN_STEPS) return;
  const hdrs = headers();
  const searchUrl = `${BASE_URL}/threads/search`;
  let totalDeleted = 0;
  // Loop until no more threads
  while (true) {
    let threads;
    try {
      const res = await fetch(searchUrl, {
        method: 'POST',
        headers: hdrs,
        // Only request thread_id to minimize response size
        body: JSON.stringify({ limit: 1000, select: ['thread_id'] }),
      });
      if (!res.ok) {
        console.error(`Cleanup search failed: ${res.status} ${res.statusText}`);
        break;
      }
      threads = await res.json();
    } catch (e) {
      // Response too large or other error - skip cleanup
      console.error(`Cleanup search error: ${e?.message || e}`);
      break;
    }
    if (!Array.isArray(threads) || threads.length === 0) break;
    for (const t of threads) {
      try {
        const del = await fetch(`${BASE_URL}/threads/${t.thread_id}`, {
          method: 'DELETE',
          headers: hdrs,
        });
        if (del.ok) totalDeleted++;
      } catch (e) {
        // Ignore delete errors; do not retry
      }
    }
  }
  if (CLEAR_DELAY_SECONDS > 0) {
    await new Promise((r) => setTimeout(r, CLEAR_DELAY_SECONDS * 1000));
  }
  console.log(`Cleanup completed. Deleted ~${totalDeleted} threads.`);
}

const SLOWEST_N = envInt('SLOWEST_N', 2);

function runK6(target) {
  const env = {
    ...process.env,
    BASE_URL,
    LANGSMITH_API_KEY,
    TARGET: String(target),
    WAIT_SECONDS: String(WAIT_SECONDS),
    DATA_SIZE: String(DATA_SIZE),
    DELAY: String(DELAY),
    EXPAND: String(EXPAND),
    STEPS: String(STEPS),
  };
  console.log(`Running k6 with TARGET=${target}`);
  // Also write raw JSON stream for per-stage histograms
  const ts = new Date().toISOString().replace(/:/g, '-').replace(/\..+/, '');
  const rawOut = `capacity_raw_t${target}_${ts}.json`;
  // We rely on handleSummary to write capacity_summary_t${TARGET}_<ts>.json
  execFileSync('k6', ['run', '--out', `json=${rawOut}`, 'capacity_k6.js'], {
    cwd: process.cwd(),
    env,
    stdio: 'inherit',
  });
  return { rawOut, ts };
}

function loadSummaryForTarget(target) {
  const files = readdirSync(process.cwd())
    .filter((f) => f.startsWith(`capacity_summary_t${target}_`) && f.endsWith('.json'))
    .sort();
  if (files.length === 0) {
    throw new Error(`No capacity summary file found for target ${target}`);
  }
  const latest = files[files.length - 1];
  const content = readFileSync(join(process.cwd(), latest), 'utf-8');
  return { filename: latest, data: JSON.parse(content) };
}

function updateSummaryWithSlowestRuns(summaryFilename, summaryData, slowestRuns) {
  summaryData.slowestRuns = slowestRuns;
  writeFileSync(join(process.cwd(), summaryFilename), JSON.stringify(summaryData, null, 2));
  console.log(`Updated ${summaryFilename} with ${slowestRuns.length} slowest runs`);
}

async function main() {
  let n = RAMP_START;

  while (n <= RAMP_END) {
    const currentTarget = n;
    console.log(`\n=== Capacity step: N=${currentTarget} ===`);
    if (CLEAR_BETWEEN_STEPS) {
      console.log('Clearing threads before step...');
      await cleanThreads();
    }

    let stageTimestamp = null;
    let runDurationHistogram = null;
    let histogramSampleCount = 0;
    let slowestRuns = [];
    let rawOut = null;

    try {
      const result = runK6(currentTarget);
      rawOut = result.rawOut;
      stageTimestamp = result.ts;
      try {
        const histogramResult = await generateHistogramsForStage(result.rawOut);
        runDurationHistogram = histogramResult?.runDurationHistogramSeconds ?? null;
        histogramSampleCount = histogramResult?.sampleCount ?? 0;
        slowestRuns = histogramResult?.slowestRuns ?? [];
      } catch (e) {
        console.error(`Failed to generate histograms for N=${currentTarget}:`, e?.message || e);
      }
    } catch (e) {
      console.error(`k6 run failed at N=${currentTarget}:`, e?.message || e);
      // Treat as failure for this step
    }

    let summaryFilename = null;
    let summary = null;
    try {
      const result = loadSummaryForTarget(currentTarget);
      summaryFilename = result.filename;
      summary = result.data;

      // Update summary with slowest runs extracted from raw JSON
      if (slowestRuns.length > 0) {
        updateSummaryWithSlowestRuns(summaryFilename, summary, slowestRuns);
      }
    } catch (e) {
      console.error(`Failed to read summary for N=${currentTarget}:`, e?.message || e);
    }

    const metrics = summary?.metrics ?? {};
    const successRatePercent = metrics?.successRate ?? null;
    const avgDurationSeconds = metrics?.runDuration?.avg ?? null;

    const hasSuccessRate = Number.isFinite(successRatePercent);
    const hasAvgDuration = Number.isFinite(avgDurationSeconds);
    if (hasSuccessRate && hasAvgDuration) {
      console.log(`Step N=${currentTarget} successRate=${successRatePercent.toFixed(2)}% avgDur=${avgDurationSeconds.toFixed(3)}s`);
    } else {
      console.log(`Step N=${currentTarget} summary incomplete`);
    }

    const effectiveTimestamp = summary?.timestamp ?? stageTimestamp ?? slugifyTimestamp(null);

    if (Array.isArray(runDurationHistogram) && runDurationHistogram.length > 0) {
      const histogramLog = {
        timestamp: effectiveTimestamp,
        baseUrl: BASE_URL,
        baseUrlName: baseUrlToBaseUrlName[BASE_URL],
        target: currentTarget,
        waitSeconds: WAIT_SECONDS,
        dataSize: DATA_SIZE,
        delay: DELAY,
        expand: EXPAND,
        steps: STEPS,
        metric: 'run_duration_seconds',
        histogram: {
          unit: 'seconds',
          buckets: runDurationHistogram,
          sampleCount: histogramSampleCount,
        },
      };
      const histogramFile = `capacity_histogram_t${currentTarget}_${slugifyTimestamp(effectiveTimestamp)}.json`;
      writeFileSync(join(process.cwd(), histogramFile), JSON.stringify(histogramLog, null, 2));
      console.log(JSON.stringify(histogramLog));
    }

    if (currentTarget >= RAMP_END) {
      console.log('Reached final ramp target; stopping.');
      break;
    }

    const next = Math.floor(currentTarget * RAMP_MULTIPLIER);
    if (next > RAMP_END) {
      n = RAMP_END;
    } else {
      n = next;
    }

    if (n <= currentTarget) {
      console.log('Next ramp value would not increase; stopping.');
      break;
    }
  }
}

main().catch((e) => {
  console.error('Fatal error in capacity runner:', e?.stack || e?.message || e);
  process.exit(1);
});

function buildHistogramBuckets(valuesSeconds, bucketCount = 12) {
  if (!Array.isArray(valuesSeconds) || valuesSeconds.length === 0) return [];
  const min = Math.min(...valuesSeconds);
  const max = Math.max(...valuesSeconds);
  if (!Number.isFinite(min) || !Number.isFinite(max)) return [];
  if (min === max) {
    return [{
      start: Number(min.toFixed(6)),
      end: Number(max.toFixed(6)),
      count: valuesSeconds.length,
    }];
  }
  const width = (max - min) / bucketCount;
  if (width === 0) {
    return [{
      start: Number(min.toFixed(6)),
      end: Number(max.toFixed(6)),
      count: valuesSeconds.length,
    }];
  }
  const buckets = Array.from({ length: bucketCount }, (_, i) => ({
    start: min + i * width,
    end: i === bucketCount - 1 ? max : min + (i + 1) * width,
    count: 0,
  }));
  for (const v of valuesSeconds) {
    if (!Number.isFinite(v)) continue;
    let idx = Math.floor((v - min) / width);
    if (idx < 0) idx = 0;
    if (idx >= bucketCount) idx = bucketCount - 1;
    buckets[idx].count += 1;
  }
  return buckets.map((b, i) => ({
    start: Number(b.start.toFixed(6)),
    end: Number(b.end.toFixed(6)),
    count: b.count,
  }));
}

// Build and save histogram charts for one stage from raw K6 JSON
// Also extracts slowest runs from run_duration metric tags
async function generateHistogramsForStage(rawFile) {
  // Parse streaming JSONL from k6 --out json
  const metrics = {
    run_duration: [],
    run_pickup_duration: [],
    run_return_duration: [],
    run_insertion_duration: [],
    run_oss_duration: [],
  };
  // Collect run_duration entries with tags for slowest runs
  const runDurationWithTags = [];

  await new Promise((resolve, reject) => {
    const rl = readline.createInterface({ input: createReadStream(join(process.cwd(), rawFile), { encoding: 'utf-8' }), crlfDelay: Infinity });
    rl.on('line', (line) => {
      try {
        const entry = JSON.parse(line);
        if (entry.type === 'Point') {
          const name = entry.metric;
          if (name in metrics) {
            const v = entry?.data?.value;
            if (Number.isFinite(v)) metrics[name].push(v);
          }
          // Capture run_duration entries with runId/threadId tags
          if (name === 'run_duration') {
            const tags = entry?.data?.tags;
            const v = entry?.data?.value;
            if (tags?.runId && tags?.threadId && Number.isFinite(v)) {
              runDurationWithTags.push({
                durationMs: v,
                runId: tags.runId,
                threadId: tags.threadId,
              });
            }
          }
        }
      } catch (_) {
        // ignore parse errors
      }
    });
    rl.on('close', resolve);
    rl.on('error', reject);
  });

  // Get slowest N runs
  const slowestRuns = runDurationWithTags
    .sort((a, b) => b.durationMs - a.durationMs)
    .slice(0, SLOWEST_N)
    .map((r) => ({
      durationSeconds: r.durationMs / 1000,
      runId: r.runId,
      threadId: r.threadId,
    }));

  const runDurationSeconds = metrics.run_duration.map((v) => v / 1000);
  return {
    runDurationHistogramSeconds: buildHistogramBuckets(runDurationSeconds),
    sampleCount: runDurationSeconds.length,
    slowestRuns,
  };
}
