import { useState, useEffect } from 'react'
import { SparklesIcon, CheckIcon, RefreshCwIcon, GlobeIcon } from './Icons'

const COLOR_PALETTE = ['#0a66c2', '#38bdf8', '#8b5cf6', '#10b981', '#f59e0b', '#ec4899']

export default function SearchProgress({ timeframe, config, locations: propLocations }) {
  const currentConfig = config || timeframe || {}
  const locations = propLocations || currentConfig.locations || [
    { location: currentConfig.location || 'Bangladesh', workplace: currentConfig.workplaceType || 'all' }
  ]

  const sources = [
    { id: 'bdjobs-feed', name: 'BDjobs Scraper', location: 'Bangladesh Tech & Software', color: '#f59e0b', icon: '🇧🇩' },
    { id: 'indeed-feed', name: 'Indeed Bangladesh', location: 'Local Tech Feeds', color: '#003a9b', icon: '🔍' },
    { id: 'linkedin-feed', name: 'LinkedIn Live Feeds', location: `${locations.map(l => l.location || 'Target').join(', ')}`, color: '#0a66c2', icon: '💼' },
    { id: 'wwr-feed', name: 'WeWorkRemotely', location: 'Programming & Remote RSS', color: '#14b8a6', icon: '🏠' },
    { id: 'remotive-feed', name: 'Remotive & RemoteOK', location: 'Worldwide Software Roles', color: '#10b981', icon: '🌐' },
    { id: 'jobicy-feed', name: 'Jobicy & Arbeitnow', location: 'Global & EU Tech Boards', color: '#8b5cf6', icon: '📋' },
    { id: 'dedup-enrich', name: 'Deduplication & Parsing', location: 'Cross-platform Match & Clean', color: '#f97316', icon: '⚡' },
    { id: 'gemini-scoring', name: 'Gemini AI Scoring Engine', location: 'Resume Stack Alignment', color: '#ec4899', icon: '🤖' },
  ]

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
            <span>Scanning 8 Job Networks · {secondsElapsed}s elapsed</span>
          </div>
          <h2 className="progress-headline">Querying 8 Platforms across {locations.length} Target Locations ({tfLabel})</h2>
          <p className="progress-subtext">
            Scanning BDjobs, Indeed, LinkedIn, WeWorkRemotely, Remotive, RemoteOK, Jobicy &amp; Arbeitnow simultaneously, eliminating duplicates, and scoring with Gemini AI.
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
                    style={{ borderColor: source.color, color: source.color, fontSize: '15px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                  >
                    {source.icon || <span className="scan-color-indicator" style={{ backgroundColor: source.color }} />}
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


