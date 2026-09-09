import { useState, useEffect } from 'react'
import { SparklesIcon, CheckIcon, RefreshCwIcon, GlobeIcon } from './Icons'

const COLOR_PALETTE = ['#0a66c2', '#38bdf8', '#8b5cf6', '#10b981', '#f59e0b', '#ec4899']

export default function SearchProgress({ timeframe, config, locations: propLocations }) {
  const currentConfig = config || timeframe || {}
  const locations = propLocations || currentConfig.locations || [
    { location: currentConfig.location || 'Bangladesh', workplace: currentConfig.workplaceType || 'all' }
  ]

  const sources = []
  locations.forEach((locItem, idx) => {
    const loc = locItem.location || 'Target Location'
    const wp = locItem.workplace || 'all'
    const wpDesc = wp === 'all' ? 'All Workplace Modes' : `${wp.toUpperCase()} Roles`
    sources.push({
      id: `li-target-${idx}`,
      name: `LinkedIn (${loc})`,
      location: wpDesc,
      color: COLOR_PALETTE[idx % COLOR_PALETTE.length],
    })
  })

  sources.push(
    { id: 'li-enrich', name: 'JD Enrichment & Parsing', location: 'Full Description & Tech Stack', color: '#10b981' },
    { id: 'li-ai', name: 'Gemini 3.6 Scoring Engine', location: 'Stack Alignment & Ranking', color: '#8b5cf6' }
  )

  const [activeIndex, setActiveIndex] = useState(0)
  const [progress, setProgress] = useState(0)
  const [secondsElapsed, setSecondsElapsed] = useState(0)

  // Step ticker
  useEffect(() => {
    const stepDuration = 6000
    const totalSteps = sources.length

    const interval = setInterval(() => {
      setActiveIndex(prev => {
        const next = prev + 1
        if (next >= totalSteps) {
          clearInterval(interval)
          return totalSteps - 1
        }
        return next
      })
    }, stepDuration)

    // Progress bar
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 94) return 94
        return prev + 0.5
      })
    }, 200)

    // Second counter
    const secInterval = setInterval(() => {
      setSecondsElapsed(s => s + 1)
    }, 1000)

    return () => {
      clearInterval(interval)
      clearInterval(progressInterval)
      clearInterval(secInterval)
    }
  }, [sources.length])

  const daysCount = currentConfig.days || 7
  const tfLabel = daysCount <= 1 ? 'Past 24 Hours' : `Past ${daysCount} Days`
  const locListStr = locations.map(l => `${l.location || 'Location'} (${l.workplace})`).join(', ')

  return (
    <div className="progress-hub-container">
      <div className="card progress-hub-card">
        {/* Scanner radar visual */}
        <div className="scanner-radar">
          <div className="radar-circle radar-c1" />
          <div className="radar-circle radar-c2" />
          <div className="radar-circle radar-c3" />
          <div className="radar-sweep" />
          <div className="radar-core">
            <GlobeIcon size={24} className="radar-icon" />
          </div>
        </div>

        <div className="progress-header">
          <div className="progress-status-pill">
            <span className="live-pulse-dot" />
            <span>Scanning LinkedIn Feeds · {secondsElapsed}s elapsed</span>
          </div>
          <h2 className="progress-headline">Querying {locations.length} Target Location Feeds ({tfLabel})</h2>
          <p className="progress-subtext">
            Crawling {locListStr} with Crawlee &amp; Playwright, enriching tech stack requirements, and ranking with Gemini AI.
          </p>
        </div>

        {/* Linear Progress Bar */}
        <div className="progress-track-wrapper">
          <div className="progress-track-header">
            <span className="track-label">Search Aggregation Progress</span>
            <span className="track-percentage">{Math.round(progress)}%</span>
          </div>
          <div className="progress-track">
            <div className="progress-fill" style={{ width: `${progress}%` }} />
          </div>
        </div>

        {/* Source cards grid */}
        <div className="sources-scanning-grid">
          {sources.map((source, i) => {
            const isDone = i < activeIndex
            const isActive = i === activeIndex
            const isPending = i > activeIndex

            return (
              <div
                key={source.id}
                className={`source-scan-card ${isDone ? 'scan-done' : ''} ${isActive ? 'scan-active' : ''} ${isPending ? 'scan-pending' : ''}`}
              >
                <div className="scan-card-left">
                  <div
                    className="scan-avatar"
                    style={{ borderColor: source.color, color: source.color }}
                  >
                    <span className="scan-color-indicator" style={{ backgroundColor: source.color }} />
                  </div>
                  <div>
                    <div className="scan-source-name">{source.name}</div>
                    <div className="scan-source-loc">{source.location}</div>
                  </div>
                </div>

                <div className="scan-status-badge">
                  {isDone && (
                    <span className="badge-done">
                      <CheckIcon size={12} />
                      Scanned
                    </span>
                  )}
                  {isActive && (
                    <span className="badge-scanning">
                      <RefreshCwIcon size={12} className="spin-icon" />
                      Scanning...
                    </span>
                  )}
                  {isPending && (
                    <span className="badge-queued">Queued</span>
                  )}
                </div>
              </div>
            )
          })}
        </div>

        {/* AI post-processing note */}
        <div className="progress-ai-note">
          <SparklesIcon size={14} className="text-indigo" />
          <span>Gemini AI will score and synthesize personalized match rationale once feeds resolve.</span>
        </div>
      </div>
    </div>
  )
}


