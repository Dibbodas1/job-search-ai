import { useState, useMemo } from 'react'
import {
  SparklesIcon,
  SearchIcon,
  DownloadIcon,
  RefreshCwIcon,
  BuildingIcon,
  MapPinIcon,
  CalendarIcon,
  ExternalLinkIcon,
  GridIcon,
  ListIcon,
  BriefcaseIcon,
  FilterIcon,
  XIcon,
} from './Icons'

function getScoreTier(score) {
  if (score >= 60) return { label: 'High Match', class: 'score-high' }
  if (score >= 35) return { label: 'Good Match', class: 'score-mid' }
  return { label: 'Base Match', class: 'score-low' }
}

function getRemoteType(status) {
  const s = (status || '').toLowerCase()
  if (s.includes('remote')) return { label: 'Remote', class: 'badge-remote' }
  if (s.includes('hybrid')) return { label: 'Hybrid', class: 'badge-hybrid' }
  return { label: 'Onsite', class: 'badge-onsite' }
}

function getSourceMeta(source) {
  const s = (source || '').toLowerCase()
  if (s.includes('remote')) return { label: 'LinkedIn Remote', class: 'source-linkedin' }
  if (source && source.startsWith('LinkedIn')) return { label: source, class: 'source-linkedin' }
  return { label: source || 'LinkedIn', class: 'source-linkedin' }
}

export function formatJobLink(link, jobId) {
  if (jobId && /^\d+$/.test(String(jobId).trim())) {
    return `https://www.linkedin.com/jobs/view/${String(jobId).trim()}/`
  }
  if (!link) return 'https://www.linkedin.com/jobs/'
  const s = String(link).trim()
  const m = s.match(/(\d{7,})/)
  if (m) return `https://www.linkedin.com/jobs/view/${m[1]}/`
  if (s.startsWith('http://') || s.startsWith('https://')) return s
  if (s.startsWith('/')) return `https://www.linkedin.com${s}`
  return `https://${s}`
}


export default function ResultsDashboard({
  results,
  stats,
  aiSummary,
  timeframe,
  onSelectJob,
  onExport,
  exporting,
  onNewSearch
}) {
  const [activeTab, setActiveTab] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState('score')
  const [sortDir, setSortDir] = useState('desc')
  const [filterRemote, setFilterRemote] = useState('all')
  const [filterSource, setFilterSource] = useState('all')
  const [filterMinScore, setFilterMinScore] = useState('all')
  const [viewMode, setViewMode] = useState('grid') // 'grid' | 'table'
  const [isAiExpanded, setIsAiExpanded] = useState(false)

  const allJobs = results?.all_jobs || [...(results?.bangladesh_jobs || []), ...(results?.remote_jobs || [])]
  const locationTargets = results?.location_targets || []
  const jobsByLocation = results?.jobs_by_location || {}

  // ─── Filtered + Sorted Jobs ───────────────────────────────────
  const displayedJobs = useMemo(() => {
    let jobs = []
    if (activeTab === 'all') {
      jobs = [...allJobs]
    } else {
      const normTab = (activeTab || '').trim().toLowerCase()
      // 1. Direct match in jobsByLocation
      if (jobsByLocation[activeTab]) {
        jobs = [...jobsByLocation[activeTab]]
      } else {
        // 2. Case-insensitive and trimmed match in jobsByLocation
        const matchingKey = Object.keys(jobsByLocation).find(
          k => k.trim().toLowerCase() === normTab
        )
        if (matchingKey && jobsByLocation[matchingKey]) {
          jobs = [...jobsByLocation[matchingKey]]
        } else if (normTab.includes('world') || normTab.includes('remote') || normTab.includes('global')) {
          // Worldwide / Remote tab fallback: match jobs where target or remote status indicates remote/worldwide
          jobs = allJobs.filter(j => {
            const tj = (j.target_location || '').toLowerCase()
            const sj = (j.source || '').toLowerCase()
            return tj.includes('world') || tj.includes('remote') || tj.includes('global') ||
                   sj.includes('world') || sj.includes('remote') || (j.remote_status || '').toLowerCase() === 'remote'
          })
          if (jobs.length === 0 && results?.remote_jobs) {
            jobs = [...results.remote_jobs]
          }
        } else if (normTab.includes('bangladesh') || normTab.includes('local') || normTab.includes('dhaka')) {
          // Bangladesh tab fallback
          jobs = allJobs.filter(j => {
            const tj = (j.target_location || '').toLowerCase()
            const lj = (j.location || '').toLowerCase()
            return tj.includes('bangladesh') || tj.includes('dhaka') || lj.includes('bangladesh') || lj.includes('dhaka')
          })
          if (jobs.length === 0 && results?.bangladesh_jobs) {
            jobs = [...results.bangladesh_jobs]
          }
        } else {
          // Generic target_location match
          jobs = allJobs.filter(j => (j.target_location || '').trim().toLowerCase() === normTab)
        }
      }
    }

    // Search query filter (title, company, reason/skills)
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase()
      jobs = jobs.filter(j =>
        (j.title || '').toLowerCase().includes(q) ||
        (j.company || '').toLowerCase().includes(q) ||
        (j.reason || '').toLowerCase().includes(q) ||
        (j.location || '').toLowerCase().includes(q)
      )
    }

    // Remote status filter
    if (filterRemote !== 'all') {
      jobs = jobs.filter(j => (j.remote_status || '').toLowerCase() === filterRemote.toLowerCase())
    }

    // Source filter
    if (filterSource !== 'all') {
      jobs = jobs.filter(j => (j.source || '').toLowerCase().includes(filterSource))
    }

    // Min Score filter
    if (filterMinScore !== 'all') {
      const min = parseInt(filterMinScore, 10)
      jobs = jobs.filter(j => (j.score || 0) >= min)
    }

    // Sorting
    jobs.sort((a, b) => {
      let cmp = 0
      if (sortBy === 'score') cmp = (a.score || 0) - (b.score || 0)
      else if (sortBy === 'date') cmp = String(a.date_posted || '').localeCompare(String(b.date_posted || ''))
      else if (sortBy === 'company') cmp = String(a.company || '').localeCompare(String(b.company || ''))
      else if (sortBy === 'title') cmp = String(a.title || '').localeCompare(String(b.title || ''))
      return sortDir === 'desc' ? -cmp : cmp
    })

    return jobs
  }, [allJobs, jobsByLocation, activeTab, searchQuery, filterRemote, filterSource, filterMinScore, sortBy, sortDir])

  const handleSort = (column) => {
    if (sortBy === column) {
      setSortDir(d => d === 'desc' ? 'asc' : 'desc')
    } else {
      setSortBy(column)
      setSortDir('desc')
    }
  }

  // Extract unique sources for filter dropdown
  const sources = useMemo(() => {
    return [...new Set(allJobs.map(j => j.source).filter(Boolean))]
  }, [allJobs])

  const totalSelected = allJobs.length || (stats?.total_selected || 0)
  const totalScraped = stats?.total_scraped || ((stats?.total_bd_scraped || 0) + (stats?.total_remote_scraped || 0))

  return (
    <section className="results-container" id="results">
      {/* ─── AI Career Insight Banner ───────────────────────────────── */}
      {aiSummary && (
        <div className="ai-insight-panel">
          <div className="ai-insight-header">
            <div className="ai-insight-title">
              <SparklesIcon size={16} className="text-indigo" />
              <span>Gemini 3.6 Career Intelligence &amp; Market Fit</span>
            </div>
            <button
              type="button"
              className="btn-link"
              onClick={() => setIsAiExpanded(!isAiExpanded)}
            >
              {isAiExpanded ? 'Show Less' : 'Read Full Analysis'}
            </button>
          </div>
          <div className={`ai-insight-content ${isAiExpanded ? 'expanded' : 'collapsed'}`}>
            <p>{aiSummary}</p>
          </div>
        </div>
      )}

      {/* ─── Metric Stat Cards ──────────────────────────────────────── */}
      {stats && (
        <div className="metrics-grid">
          <div className="metric-card">
            <div className="metric-icon-wrap bg-indigo-subtle">
              <BriefcaseIcon size={18} className="text-indigo" />
            </div>
            <div>
              <div className="metric-val">{totalSelected}</div>
              <div className="metric-lbl">Curated Matches</div>
            </div>
          </div>

          {locationTargets.length > 0 ? (
            locationTargets.slice(0, 2).map((target, tIdx) => {
              const count = target.count ?? (jobsByLocation[target.location]?.length || 0)
              const iconClass = tIdx % 2 === 0 ? "text-emerald" : "text-sky"
              const wrapClass = tIdx % 2 === 0 ? "bg-emerald-subtle" : "bg-sky-subtle"
              const isWorldwide = (target.location || '').toLowerCase() in { worldwide: 1, global: 1, remote: 1 }
              return (
                <div className="metric-card" key={target.location}>
                  <div className={`metric-icon-wrap ${wrapClass}`}>
                    {isWorldwide ? (
                      <BuildingIcon size={18} className={iconClass} />
                    ) : (
                      <MapPinIcon size={18} className={iconClass} />
                    )}
                  </div>
                  <div>
                    <div className="metric-val">{count}</div>
                    <div className="metric-lbl">{target.location} ({target.workplace})</div>
                  </div>
                </div>
              )
            })
          ) : (
            <>
              <div className="metric-card">
                <div className="metric-icon-wrap bg-emerald-subtle">
                  <MapPinIcon size={18} className="text-emerald" />
                </div>
                <div>
                  <div className="metric-val">{stats.total_bd_selected || 0}</div>
                  <div className="metric-lbl">Local Roles</div>
                </div>
              </div>

              <div className="metric-card">
                <div className="metric-icon-wrap bg-sky-subtle">
                  <BuildingIcon size={18} className="text-sky" />
                </div>
                <div>
                  <div className="metric-val">{stats.total_remote_selected || 0}</div>
                  <div className="metric-lbl">Remote Roles</div>
                </div>
              </div>
            </>
          )}

          <div className="metric-card">
            <div className="metric-icon-wrap bg-purple-subtle">
              <SparklesIcon size={18} className="text-purple" />
            </div>
            <div>
              <div className="metric-val">{Math.round(stats.avg_score || 0)}%</div>
              <div className="metric-lbl">Avg Match Quality</div>
            </div>
          </div>

          <div className="metric-card">
            <div className="metric-icon-wrap bg-amber-subtle">
              <FilterIcon size={18} className="text-amber" />
            </div>
            <div>
              <div className="metric-val">{stats.high_matches || 0}</div>
              <div className="metric-lbl">High Match (≥60)</div>
            </div>
          </div>
        </div>
      )}

      {/* ─── Workspace Filter & Control Bar ─────────────────────────── */}
      <div className="workspace-toolbar">
        {/* Row 1: Search input + View Switcher + Primary Actions */}
        <div className="toolbar-primary-row">
          {/* Real-time search query box */}
          <div className="search-input-wrapper">
            <SearchIcon size={15} className="search-input-icon" />
            <input
              type="text"
              className="search-input"
              placeholder="Search by title, company, or skills..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
            />
            {searchQuery && (
              <button
                type="button"
                className="search-clear-btn"
                onClick={() => setSearchQuery('')}
                title="Clear query"
              >
                <XIcon size={13} />
              </button>
            )}
          </div>

          {/* View switcher: Grid vs Table */}
          <div className="view-mode-toggle">
            <button
              type="button"
              className={`view-btn ${viewMode === 'grid' ? 'view-btn-active' : ''}`}
              onClick={() => setViewMode('grid')}
              title="Card View"
            >
              <GridIcon size={15} />
              <span className="view-btn-label">Cards</span>
            </button>
            <button
              type="button"
              className={`view-btn ${viewMode === 'table' ? 'view-btn-active' : ''}`}
              onClick={() => setViewMode('table')}
              title="Table View"
            >
              <ListIcon size={15} />
              <span className="view-btn-label">Table</span>
            </button>
          </div>

          {/* Action buttons */}
          <div className="toolbar-actions">
            <button
              className="btn-export"
              onClick={onExport}
              disabled={exporting || displayedJobs.length === 0}
              id="export-btn"
              title="Export filtered results to Excel"
            >
              <DownloadIcon size={14} />
              <span>{exporting ? 'Generating Excel...' : 'Export Excel'}</span>
            </button>

            <button
              className="btn-ghost btn-sm"
              onClick={onNewSearch}
              id="new-search-btn"
              title="Re-run search with new settings"
            >
              <RefreshCwIcon size={13} />
              <span>New Search</span>
            </button>
          </div>
        </div>

        {/* Row 2: Location Tabs & Dropdown Filters */}
        <div className="toolbar-filters-row">
          {/* Location tab pills */}
          <div className="location-tabs">
            <button
              className={`loc-tab ${activeTab === 'all' ? 'loc-tab-active' : ''}`}
              onClick={() => setActiveTab('all')}
            >
              All Matches <span className="tab-badge">{allJobs.length}</span>
            </button>
            {locationTargets.length > 0 ? (
              locationTargets.map(target => {
                const targetKey = target.location || ''
                const normalizedKey = targetKey.trim().toLowerCase()
                const foundKey = Object.keys(jobsByLocation).find(k => k.trim().toLowerCase() === normalizedKey)
                const count = target.count ?? (
                  jobsByLocation[targetKey]?.length ||
                  (foundKey ? jobsByLocation[foundKey]?.length : 0) ||
                  allJobs.filter(j => (j.target_location || '').trim().toLowerCase() === normalizedKey).length
                )
                const wpBadge = target.workplace && target.workplace !== 'all' ? ` · ${target.workplace.toUpperCase()}` : ''
                const isSelected = activeTab === targetKey || activeTab.trim().toLowerCase() === normalizedKey
                return (
                  <button
                    key={target.location}
                    className={`loc-tab ${isSelected ? 'loc-tab-active' : ''}`}
                    onClick={() => setActiveTab(target.location)}
                  >
                    <span>{target.location}{wpBadge}</span>
                    <span className="tab-badge">{count}</span>
                  </button>
                )
              })
            ) : (
              <>
                <button
                  className={`loc-tab ${activeTab === 'bangladesh' ? 'loc-tab-active' : ''}`}
                  onClick={() => setActiveTab('bangladesh')}
                >
                  Local Roles <span className="tab-badge">{(results?.bangladesh_jobs || []).length}</span>
                </button>
                <button
                  className={`loc-tab ${activeTab === 'remote' ? 'loc-tab-active' : ''}`}
                  onClick={() => setActiveTab('remote')}
                >
                  Remote Global <span className="tab-badge">{(results?.remote_jobs || []).length}</span>
                </button>
              </>
            )}
          </div>

          {/* Select filters */}
          <div className="filter-dropdowns">
            {/* Workplace type */}
            <select
              className="select-control"
              value={filterRemote}
              onChange={e => setFilterRemote(e.target.value)}
              id="filter-remote"
            >
              <option value="all">All Workplaces</option>
              <option value="remote">Remote Only</option>
              <option value="hybrid">Hybrid</option>
              <option value="onsite">Onsite</option>
            </select>

            {/* Platform source */}
            <select
              className="select-control"
              value={filterSource}
              onChange={e => setFilterSource(e.target.value)}
              id="filter-source"
            >
              <option value="all">All Sources</option>
              {sources.map(s => (
                <option key={s} value={s.toLowerCase()}>{s}</option>
              ))}
            </select>

            {/* Min score */}
            <select
              className="select-control"
              value={filterMinScore}
              onChange={e => setFilterMinScore(e.target.value)}
            >
              <option value="all">Any Match Score</option>
              <option value="60">High Match (≥60)</option>
              <option value="40">Good Match (≥40)</option>
            </select>

            {/* Reset filters button if active */}
            {(searchQuery || filterRemote !== 'all' || filterSource !== 'all' || filterMinScore !== 'all' || activeTab !== 'all') && (
              <button
                type="button"
                className="btn-filter-reset"
                onClick={() => {
                  setSearchQuery('')
                  setFilterRemote('all')
                  setFilterSource('all')
                  setFilterMinScore('all')
                  setActiveTab('all')
                }}
                title="Reset all filters"
              >
                Reset
              </button>
            )}
          </div>
        </div>
      </div>

      {/* ─── Results Content (Grid or Table) ────────────────────────── */}
      {displayedJobs.length > 0 ? (
        viewMode === 'grid' ? (
          /* CARD GRID VIEW */
          <div className="jobs-cards-grid">
            {displayedJobs.map((job, idx) => {
              const scoreTier = getScoreTier(job.score)
              const remoteMeta = getRemoteType(job.remote_status)
              const sourceMeta = getSourceMeta(job.source)

              return (
                <div
                  className="job-card"
                  key={`${job.title}-${job.company}-${idx}`}
                  onClick={() => onSelectJob(job)}
                >
                  {/* Card Header */}
                  <div className="job-card-header">
                    <div className="job-card-meta-top">
                      <span className={`badge-pill ${sourceMeta.class}`}>
                        {sourceMeta.label}
                      </span>
                      <span className={`badge-pill ${remoteMeta.class}`}>
                        {remoteMeta.label}
                      </span>
                    </div>

                    {/* Match Score Indicator */}
                    <div className={`score-ring-badge ${scoreTier.class}`} title={`Fit Score: ${job.score}/100`}>
                      <span className="score-num">{job.score}</span>
                      <span className="score-denom">/100</span>
                    </div>
                  </div>

                  {/* Job Title & Company */}
                  <div className="job-card-body">
                    <h4 className="job-card-title" title={job.title}>{job.title}</h4>
                    <div className="job-card-company">
                      <BuildingIcon size={14} className="text-muted" />
                      <span>{job.company || 'Confidential'}</span>
                    </div>

                    <div className="job-card-details-row">
                      <span className="job-detail-item">
                        <MapPinIcon size={13} className="text-muted" />
                        <span className="text-truncate">{job.location || 'Not Specified'}</span>
                      </span>
                      {job.date_posted && (
                        <span className="job-detail-item">
                          <CalendarIcon size={13} className="text-muted" />
                          <span>{job.date_posted}</span>
                        </span>
                      )}
                      {job.experience && (
                        <span className="job-detail-item">
                          <BriefcaseIcon size={13} className="text-muted" />
                          <span>{job.experience}</span>
                        </span>
                      )}
                    </div>

                    {/* Match reasoning / matched skills preview */}
                    {job.reason && (
                      <div className="job-card-reason">
                        <span className="reason-label">Matched:</span>
                        <p className="reason-summary">{job.reason}</p>
                      </div>
                    )}
                  </div>

                  {/* Card Footer Actions */}
                  <div className="job-card-footer">
                    <button
                      type="button"
                      className="btn-card-details"
                      onClick={(e) => {
                        e.stopPropagation()
                        onSelectJob(job)
                      }}
                    >
                      View Analysis
                    </button>

                    {(job.link || job.job_id) && (
                      <a
                        href={formatJobLink(job.link, job.job_id)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn-card-apply"
                        onClick={e => e.stopPropagation()}
                      >
                        <span>Apply</span>
                        <ExternalLinkIcon size={12} />
                      </a>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        ) : (
          /* TABLE VIEW */
          <div className="jobs-table-outer">
            <table className="modern-table">
              <thead>
                <tr>
                  <th style={{ width: '40px' }}>#</th>
                  <th
                    className={sortBy === 'title' ? 'sorted' : ''}
                    onClick={() => handleSort('title')}
                  >
                    Role Title {sortBy === 'title' && (sortDir === 'desc' ? '↓' : '↑')}
                  </th>
                  <th
                    className={sortBy === 'company' ? 'sorted' : ''}
                    onClick={() => handleSort('company')}
                  >
                    Company {sortBy === 'company' && (sortDir === 'desc' ? '↓' : '↑')}
                  </th>
                  <th>Location</th>
                  <th
                    className={sortBy === 'date' ? 'sorted' : ''}
                    onClick={() => handleSort('date')}
                  >
                    Posted {sortBy === 'date' && (sortDir === 'desc' ? '↓' : '↑')}
                  </th>
                  <th
                    className={sortBy === 'score' ? 'sorted' : ''}
                    onClick={() => handleSort('score')}
                  >
                    Score {sortBy === 'score' && (sortDir === 'desc' ? '↓' : '↑')}
                  </th>
                  <th>Skills Analysis</th>
                  <th>Workplace</th>
                  <th>Source</th>
                  <th style={{ textAlign: 'right' }}>Apply</th>
                </tr>
              </thead>
              <tbody>
                {displayedJobs.map((job, idx) => {
                  const scoreTier = getScoreTier(job.score)
                  const remoteMeta = getRemoteType(job.remote_status)
                  const sourceMeta = getSourceMeta(job.source)

                  return (
                    <tr
                      key={`${job.title}-${job.company}-${idx}`}
                      onClick={() => onSelectJob(job)}
                      className="table-row-interactive"
                    >
                      <td className="text-muted text-center">{idx + 1}</td>
                      <td>
                        <div className="table-job-title">{job.title}</div>
                      </td>
                      <td>
                        <span className="table-company">{job.company}</span>
                      </td>
                      <td>
                        <span className="table-location">{job.location}</span>
                      </td>
                      <td>
                        <span className="table-date">{job.date_posted}</span>
                      </td>
                      <td>
                        <span className={`table-score-pill ${scoreTier.class}`}>
                          {job.score}/100
                        </span>
                      </td>
                      <td>
                        <div className="table-reason-snippet">{job.reason}</div>
                      </td>
                      <td>
                        <span className={`badge-pill ${remoteMeta.class}`}>
                          {remoteMeta.label}
                        </span>
                      </td>
                      <td>
                        <span className={`badge-pill ${sourceMeta.class}`}>
                          {sourceMeta.label}
                        </span>
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        {(job.link || job.job_id) && (
                          <a
                            href={formatJobLink(job.link, job.job_id)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="table-apply-btn"
                            onClick={e => e.stopPropagation()}
                          >
                            <span>Apply</span>
                            <ExternalLinkIcon size={11} />
                          </a>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )
      ) : (
        /* Empty State */
        <div className="empty-results-box">
          <div className="empty-icon-wrap">
            <SearchIcon size={28} className="text-muted" />
          </div>
          <h4 className="empty-title">No matching jobs found</h4>
          <p className="empty-desc">
            No listings matched your active filter criteria. Try adjusting your query or resetting filters.
          </p>
          <button
            type="button"
            className="btn-ghost btn-sm"
            onClick={() => {
              setSearchQuery('')
              setFilterRemote('all')
              setFilterSource('all')
              setFilterMinScore('all')
              setActiveTab('all')
            }}
          >
            Clear All Filters
          </button>
        </div>
      )}

      {/* ─── Footer Details ─────────────────────────────────────────── */}
      <div className="results-footer-info">
        <span>Timeframe: <strong>{timeframe}</strong></span>
        <span className="meta-bullet">·</span>
        <span>Showing <strong>{displayedJobs.length}</strong> of <strong>{totalSelected}</strong> curated candidates</span>
        <span className="meta-bullet">·</span>
        <span>Aggregated from <strong>{totalScraped}</strong> raw listings</span>
      </div>
    </section>
  )
}
