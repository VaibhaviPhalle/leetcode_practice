"""
FastAPI app — serves the dashboard UI and JSON API.
Background scheduler runs scraper every 5 hours independently of page refreshes.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .database import get_jobs, get_stats, get_tiers, init_db, log_scrape
from .scraper import run_scrape

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def _scheduled_scrape():
    logger.info("Scheduled scrape starting...")
    try:
        summary = await run_scrape()
        log_scrape(summary)
        logger.info("Scheduled scrape done: %s", summary)
    except Exception as e:
        logger.error("Scheduled scrape failed: %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()

    # Run an initial scrape immediately on startup in the background
    asyncio.create_task(_scheduled_scrape())

    # Then repeat every 5 hours
    scheduler.add_job(_scheduled_scrape, "interval", hours=5, id="scrape_job")
    scheduler.start()
    logger.info("Scheduler started — scraping every 5 hours")

    yield

    scheduler.shutdown(wait=False)


app = FastAPI(title="Job Discovery Dashboard", lifespan=lifespan)


# ── API Routes ────────────────────────────────────────────────────────────────

@app.get("/api/jobs")
def api_jobs(
    tier: str = Query(default="All"),
    location: str = Query(default="All"),
    days: int = Query(default=30, ge=1, le=90),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    """
    Returns jobs from local SQLite — no external API calls.
    Safe to call on every dashboard refresh.
    """
    loc_filter = None if location == "All" else location
    jobs = get_jobs(tier=tier, location_filter=loc_filter, days=days, limit=limit, offset=offset)
    return {"jobs": jobs, "count": len(jobs)}


@app.get("/api/stats")
def api_stats():
    return get_stats()


@app.get("/api/tiers")
def api_tiers():
    return {"tiers": ["All"] + get_tiers()}


@app.post("/api/scrape")
async def api_scrape():
    """Manually trigger a scrape (with a simple in-memory cooldown of 30 min)."""
    now = datetime.utcnow()
    last = getattr(app.state, "last_manual_scrape", None)
    if last and (now - last).total_seconds() < 1800:
        remaining = int(1800 - (now - last).total_seconds())
        return {"status": "cooldown", "retry_in_seconds": remaining}

    app.state.last_manual_scrape = now
    asyncio.create_task(_scheduled_scrape())
    return {"status": "started"}


# ── Dashboard HTML ─────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def dashboard():
    return HTMLResponse(content=_DASHBOARD_HTML)


_DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Job Discovery Dashboard</title>
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js" defer></script>
<style>
  [x-cloak] { display: none !important; }
  .tier-badge { @apply text-xs font-semibold px-2 py-0.5 rounded-full; }
  .fresh { background:#dcfce7; color:#166534; }
  .day1  { background:#fef9c3; color:#854d0e; }
  .older { background:#fee2e2; color:#991b1b; }
  tr:hover td { background: #f8fafc; }
</style>
</head>
<body class="bg-gray-50 text-gray-800 font-sans" x-data="dashboard()" x-init="init()">

<!-- Header -->
<header class="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
  <div>
    <h1 class="text-xl font-bold text-gray-900">Job Discovery</h1>
    <p class="text-xs text-gray-500 mt-0.5">Silicon Valley · Bay Area · Remote US</p>
  </div>
  <div class="flex items-center gap-4">
    <!-- Stats chips -->
    <div class="flex gap-3">
      <div class="bg-blue-50 rounded-lg px-3 py-1.5 text-center">
        <div class="text-lg font-bold text-blue-700" x-text="stats.total_jobs ?? '—'"></div>
        <div class="text-xs text-blue-500">Total Jobs</div>
      </div>
      <div class="bg-green-50 rounded-lg px-3 py-1.5 text-center">
        <div class="text-lg font-bold text-green-700" x-text="stats.new_today ?? '—'"></div>
        <div class="text-xs text-green-500">New Today</div>
      </div>
    </div>
    <!-- Manual refresh -->
    <button
      @click="triggerScrape()"
      :disabled="scraping || cooldown > 0"
      class="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg transition"
    >
      <svg x-show="!scraping" xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
      <svg x-show="scraping" class="w-4 h-4 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path></svg>
      <span x-text="scraping ? 'Scraping…' : (cooldown > 0 ? `Wait ${cooldown}s` : 'Refresh Jobs')"></span>
    </button>
  </div>
</header>

<!-- Last scrape info -->
<div class="px-6 py-2 bg-gray-100 border-b border-gray-200 text-xs text-gray-500 flex gap-4">
  <span>Last scrape: <strong x-text="lastScrapeTime"></strong></span>
  <span x-show="stats.last_scrape">New jobs found: <strong x-text="stats.last_scrape?.new_jobs ?? 0"></strong></span>
  <span x-show="stats.last_scrape?.errors > 0" class="text-red-500">Errors: <strong x-text="stats.last_scrape?.errors"></strong></span>
</div>

<!-- Filters -->
<div class="px-6 py-3 bg-white border-b border-gray-200 flex flex-wrap gap-3 items-center">
  <div class="flex items-center gap-2">
    <label class="text-sm font-medium text-gray-600">Tier</label>
    <select x-model="filters.tier" @change="loadJobs()" class="text-sm border border-gray-300 rounded-md px-2 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500">
      <template x-for="t in tiers" :key="t">
        <option :value="t" x-text="t"></option>
      </template>
    </select>
  </div>

  <div class="flex items-center gap-2">
    <label class="text-sm font-medium text-gray-600">Location</label>
    <select x-model="filters.location" @change="loadJobs()" class="text-sm border border-gray-300 rounded-md px-2 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500">
      <option value="All">All</option>
      <option value="Bay Area">Bay Area</option>
      <option value="Remote">Remote</option>
    </select>
  </div>

  <div class="flex items-center gap-2">
    <label class="text-sm font-medium text-gray-600">Posted within</label>
    <select x-model="filters.days" @change="loadJobs()" class="text-sm border border-gray-300 rounded-md px-2 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500">
      <option value="1">24 hours</option>
      <option value="3">3 days</option>
      <option value="7" selected>7 days</option>
      <option value="14">14 days</option>
      <option value="30">30 days</option>
    </select>
  </div>

  <div class="flex items-center gap-2">
    <label class="text-sm font-medium text-gray-600">Search</label>
    <input
      x-model="filters.search"
      @input.debounce.300ms="applySearch()"
      type="text"
      placeholder="title, company…"
      class="text-sm border border-gray-300 rounded-md px-2 py-1.5 w-48 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
    />
  </div>

  <div class="ml-auto text-sm text-gray-500">
    Showing <strong x-text="filteredJobs.length"></strong> of <strong x-text="jobs.length"></strong> jobs
  </div>
</div>

<!-- Table -->
<div class="px-6 py-4">
  <div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
    <div x-show="loading" class="flex justify-center items-center py-20">
      <svg class="w-8 h-8 animate-spin text-indigo-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path></svg>
    </div>

    <div x-show="!loading && filteredJobs.length === 0" class="py-20 text-center text-gray-400">
      <svg xmlns="http://www.w3.org/2000/svg" class="mx-auto w-12 h-12 mb-3 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M21 21l-4.35-4.35m0 0A7.5 7.5 0 104.65 16.65 7.5 7.5 0 0016.65 16.65z"/></svg>
      <p class="text-sm">No jobs found. Try refreshing or changing filters.</p>
    </div>

    <table x-show="!loading && filteredJobs.length > 0" class="w-full text-sm">
      <thead class="bg-gray-50 border-b border-gray-200">
        <tr>
          <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide w-24">Age</th>
          <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Company</th>
          <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Tier</th>
          <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Role</th>
          <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Location</th>
          <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Source</th>
          <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide w-20">Apply</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-gray-100">
        <template x-for="job in filteredJobs" :key="job.job_id">
          <tr class="transition-colors">
            <td class="px-4 py-3">
              <span :class="ageClass(job)" class="text-xs font-medium px-2 py-0.5 rounded-full" x-text="ageLabel(job)"></span>
            </td>
            <td class="px-4 py-3 font-medium text-gray-900" x-text="job.company_name"></td>
            <td class="px-4 py-3">
              <span :class="tierColor(job.company_tier)" class="tier-badge" x-text="job.company_tier"></span>
            </td>
            <td class="px-4 py-3 text-gray-700 max-w-xs truncate" x-text="job.title"></td>
            <td class="px-4 py-3 text-gray-500 max-w-xs truncate" x-text="job.location || '—'"></td>
            <td class="px-4 py-3 text-gray-400 text-xs capitalize" x-text="job.source"></td>
            <td class="px-4 py-3">
              <a
                :href="job.job_url || '#'"
                target="_blank"
                rel="noopener"
                :class="job.job_url ? 'bg-indigo-600 hover:bg-indigo-700 text-white' : 'bg-gray-200 text-gray-400 cursor-not-allowed pointer-events-none'"
                class="inline-block text-xs font-semibold px-3 py-1.5 rounded-lg transition"
                x-text="job.job_url ? 'Apply →' : 'No URL'"
              ></a>
            </td>
          </tr>
        </template>
      </tbody>
    </table>
  </div>
</div>

<script>
function dashboard() {
  return {
    jobs: [],
    filteredJobs: [],
    stats: {},
    tiers: ['All'],
    loading: false,
    scraping: false,
    cooldown: 0,
    filters: { tier: 'All', location: 'Bay Area', days: 7, search: '' },

    get lastScrapeTime() {
      const s = this.stats.last_scrape;
      if (!s) return 'Never';
      const d = new Date(s.scraped_at);
      return d.toLocaleString();
    },

    async init() {
      await Promise.all([this.loadTiers(), this.loadStats()]);
      await this.loadJobs();
      // Auto-refresh stats every 60s without re-fetching jobs
      setInterval(() => this.loadStats(), 60_000);
    },

    async loadTiers() {
      const r = await fetch('/api/tiers');
      const d = await r.json();
      this.tiers = d.tiers;
    },

    async loadStats() {
      const r = await fetch('/api/stats');
      this.stats = await r.json();
    },

    async loadJobs() {
      this.loading = true;
      const params = new URLSearchParams({
        tier: this.filters.tier,
        location: this.filters.location,
        days: this.filters.days,
        limit: 500,
      });
      const r = await fetch(`/api/jobs?${params}`);
      const d = await r.json();
      this.jobs = d.jobs;
      this.applySearch();
      this.loading = false;
    },

    applySearch() {
      const q = this.filters.search.toLowerCase().trim();
      if (!q) {
        this.filteredJobs = this.jobs;
        return;
      }
      this.filteredJobs = this.jobs.filter(j =>
        j.title.toLowerCase().includes(q) ||
        j.company_name.toLowerCase().includes(q) ||
        (j.location || '').toLowerCase().includes(q)
      );
    },

    async triggerScrape() {
      if (this.scraping || this.cooldown > 0) return;
      this.scraping = true;
      const r = await fetch('/api/scrape', { method: 'POST' });
      const d = await r.json();
      this.scraping = false;
      if (d.status === 'cooldown') {
        this.cooldown = d.retry_in_seconds;
        const t = setInterval(() => {
          this.cooldown--;
          if (this.cooldown <= 0) { this.cooldown = 0; clearInterval(t); }
        }, 1000);
      } else {
        // Poll stats every 5s until scrape is likely done (~90s max)
        let polls = 0;
        const poll = setInterval(async () => {
          polls++;
          await this.loadStats();
          if (polls >= 18) { clearInterval(poll); await this.loadJobs(); }
        }, 5000);
      }
    },

    ageLabel(job) {
      const date = job.posted_at || job.first_seen;
      if (!date) return '?';
      const diff = (Date.now() - new Date(date)) / 3600000;
      if (diff < 6)  return `${Math.round(diff)}h ago`;
      if (diff < 24) return `${Math.round(diff)}h ago`;
      const days = Math.floor(diff / 24);
      return `${days}d ago`;
    },

    ageClass(job) {
      const date = job.posted_at || job.first_seen;
      if (!date) return 'bg-gray-100 text-gray-500';
      const hours = (Date.now() - new Date(date)) / 3600000;
      if (hours < 24)  return 'fresh';
      if (hours < 48)  return 'day1';
      return 'older';
    },

    tierColor(tier) {
      const map = {
        'FAANG':        'bg-purple-100 text-purple-800',
        'AI-First':     'bg-blue-100 text-blue-800',
        'Large Tech':   'bg-indigo-100 text-indigo-800',
        'Consumer':     'bg-pink-100 text-pink-800',
        'Enterprise':   'bg-orange-100 text-orange-800',
        'Fintech':      'bg-yellow-100 text-yellow-800',
        'Dev Tools':    'bg-teal-100 text-teal-800',
        'Unicorn':      'bg-rose-100 text-rose-800',
        'Cybersecurity':'bg-red-100 text-red-800',
        'Semiconductor':'bg-gray-100 text-gray-700',
        'Robotics':     'bg-cyan-100 text-cyan-800',
      };
      return map[tier] || 'bg-gray-100 text-gray-600';
    },
  };
}
</script>
</body>
</html>
"""
