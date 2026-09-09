import { useState } from 'react'
import {
  SearchIcon,
  CalendarIcon,
  SlidersIcon,
  GlobeIcon,
  CheckIcon,
  MapPinIcon,
  BriefcaseIcon,
  XIcon,
  PlusIcon,
} from './Icons'

const WORKPLACE_OPTIONS = [
  { id: 'onsite', label: 'Onsite', hint: 'In-Office' },
  { id: 'hybrid', label: 'Hybrid', hint: 'Office + WFH' },
  { id: 'remote', label: 'Remote', hint: '100% WFH' },
  { id: 'all', label: 'All Modes', hint: 'Any Workplace' },
]

const QUICK_ADD_PRESETS = [
  { location: 'Bangladesh', workplace: 'onsite', label: 'Bangladesh (Onsite)' },
  { location: 'Worldwide', workplace: 'remote', label: 'Worldwide (Remote)' },
  { location: 'Dhaka', workplace: 'hybrid', label: 'Dhaka (Hybrid)' },
  { location: 'United States', workplace: 'remote', label: 'US (Remote)' },
  { location: 'Germany', workplace: 'hybrid', label: 'Germany (Hybrid)' },
  { location: 'United Kingdom', workplace: 'remote', label: 'UK (Remote)' },
  { location: 'India', workplace: 'onsite', label: 'India (Onsite)' },
]

export default function SearchPanel({ config, onChange, onSearch }) {
  const locations = config.locations || [
    { id: 'loc-1', location: 'Bangladesh', workplace: 'onsite' },
    { id: 'loc-2', location: 'Worldwide', workplace: 'remote' },
  ]

  const timeframes = [
    { label: 'Past 24h', value: 'day', days: 1, hint: 'Freshest' },
    { label: 'Past Week', value: 'week', days: 7, hint: 'Recommended' },
    { label: '2 Weeks', value: 'biweek', days: 14, hint: 'Broader' },
    { label: '30 Days', value: 'month', days: 30, hint: 'All Recent' },
  ]

  const topCounts = [10, 15, 20, 25]

  const activeTf = timeframes.find(t => t.days === config.days) || timeframes[1]

  // ─── Multi-Location Handlers ────────────────────────────────────────
  const handleUpdateLocationName = (id, newName) => {
    const updated = locations.map(item =>
      item.id === id ? { ...item, location: newName } : item
    )
    onChange({ ...config, locations: updated })
  }

  const handleUpdateLocationWorkplace = (id, newWorkplace) => {
    const updated = locations.map(item =>
      item.id === id ? { ...item, workplace: newWorkplace } : item
    )
    onChange({ ...config, locations: updated })
  }

  const handleAddEmptyLocation = () => {
    const newId = `loc-${Date.now()}`
    const updated = [
      ...locations,
      { id: newId, location: '', workplace: 'all' },
    ]
    onChange({ ...config, locations: updated })
  }

  const handleQuickAdd = (preset) => {
    // If an identical location already exists, just update its workplace
    const existing = locations.find(
      l => (l.location || '').toLowerCase() === preset.location.toLowerCase()
    )
    if (existing) {
      handleUpdateLocationWorkplace(existing.id, preset.workplace)
      return
    }
    const newId = `loc-${Date.now()}`
    const updated = [
      ...locations,
      { id: newId, location: preset.location, workplace: preset.workplace },
    ]
    onChange({ ...config, locations: updated })
  }

  const handleRemoveLocation = (id) => {
    if (locations.length <= 1) return
    const updated = locations.filter(item => item.id !== id)
    onChange({ ...config, locations: updated })
  }

  return (
    <div className="search-panel-container" id="search-panel">
      <div className="card search-control-card">
        {/* Header */}
        <div className="search-card-header">
          <div className="search-card-title-group">
            <h3 className="search-card-title">Multi-Location Search &amp; Workplace Modes</h3>
            <p className="search-card-desc">
              Search multiple locations simultaneously (e.g. Bangladesh onsite + Global remote) with dedicated workplace filters for each.
            </p>
          </div>
          <span className="search-badge">
            <GlobeIcon size={13} />
            Live LinkedIn Feeds
          </span>
        </div>

        {/* ─── Multi-Location Target Builder ───────────────────────────── */}
        <div className="multi-loc-container">
          <div className="multi-loc-header">
            <label className="control-label">
              <MapPinIcon size={14} className="control-label-icon" />
              <span>Target Locations ({locations.length})</span>
            </label>
            <span className="multi-loc-hint">Set Remote, Hybrid, or Onsite for each location</span>
          </div>

          <div className="multi-loc-list">
            {locations.map((locItem, idx) => {
              const isWorldwide = (locItem.location || '').toLowerCase() in { worldwide: 1, global: 1, remote: 1 }
              return (
                <div className="multi-loc-card" key={locItem.id || idx}>
                  <div className="multi-loc-card-header">
                    <div className="multi-loc-index-pill">
                      <span className="multi-loc-num">{idx + 1}</span>
                      <span className="multi-loc-label">Target #{idx + 1}</span>
                    </div>

                    {locations.length > 1 && (
                      <button
                        type="button"
                        className="multi-loc-remove-btn"
                        onClick={() => handleRemoveLocation(locItem.id)}
                        title="Remove location"
                      >
                        <XIcon size={13} />
                        <span>Remove</span>
                      </button>
                    )}
                  </div>

                  {/* Location input row */}
                  <div className="multi-loc-inputs-row">
                    <div className="multi-loc-text-wrapper">
                      {isWorldwide ? (
                        <GlobeIcon size={15} className="multi-loc-pin-icon" />
                      ) : (
                        <MapPinIcon size={15} className="multi-loc-pin-icon" />
                      )}
                      <input
                        type="text"
                        className="multi-loc-text-input"
                        placeholder="e.g. Bangladesh, Dhaka, Berlin, United States..."
                        value={locItem.location}
                        onChange={e => handleUpdateLocationName(locItem.id, e.target.value)}
                      />
                      {locItem.location && (
                        <button
                          type="button"
                          className="multi-loc-clear-btn"
                          onClick={() => handleUpdateLocationName(locItem.id, '')}
                          title="Clear text"
                        >
                          <XIcon size={12} />
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Workplace selector for this specific location */}
                  <div className="multi-loc-workplace-row">
                    <span className="multi-loc-wp-label">Workplace Arrangement:</span>
                    <div className="multi-loc-segmented">
                      {WORKPLACE_OPTIONS.map(opt => {
                        const isSelected = (locItem.workplace || 'all') === opt.id
                        return (
                          <button
                            key={opt.id}
                            type="button"
                            className={`multi-loc-segment-btn ${isSelected ? 'multi-loc-segment-active' : ''}`}
                            onClick={() => handleUpdateLocationWorkplace(locItem.id, opt.id)}
                          >
                            <span className="wp-btn-label">{opt.label}</span>
                            <span className="wp-btn-hint">{opt.hint}</span>
                          </button>
                        )
                      })}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>

          {/* Add location and quick presets */}
          <div className="multi-loc-actions-bar">
            <button
              type="button"
              className="btn-add-location"
              onClick={handleAddEmptyLocation}
            >
              <PlusIcon size={14} />
              <span>Add Another Location</span>
            </button>

            <div className="quick-add-wrap">
              <span className="quick-add-label">Quick Add:</span>
              <div className="quick-add-list">
                {QUICK_ADD_PRESETS.map(preset => (
                  <button
                    key={preset.label}
                    type="button"
                    className="quick-add-pill"
                    onClick={() => handleQuickAdd(preset)}
                  >
                    + {preset.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* ─── Posting Timeframe & Max Matches ─────────────────────────── */}
        <div className="search-controls-grid">
          {/* Timeframe selector */}
          <div className="control-block">
            <label className="control-label">
              <CalendarIcon size={14} className="control-label-icon" />
              <span>Posting Timeframe</span>
            </label>
            <div className="segmented-control">
              {timeframes.map(tf => {
                const isSelected = config.days === tf.days
                return (
                  <button
                    key={tf.value}
                    type="button"
                    className={`segment-btn ${isSelected ? 'segment-active' : ''}`}
                    onClick={() => onChange({
                      ...config,
                      timeframe: tf.value === 'day' ? '24h' : 'week',
                      days: tf.days
                    })}
                  >
                    <span className="segment-main">{tf.label}</span>
                    {tf.hint && <span className="segment-hint">{tf.hint}</span>}
                  </button>
                )
              })}
            </div>
          </div>

          {/* Top count selector */}
          <div className="control-block">
            <label className="control-label">
              <SlidersIcon size={14} className="control-label-icon" />
              <span>Max Matches per Feed</span>
            </label>
            <div className="segmented-control pill-control">
              {topCounts.map(n => {
                const isSelected = config.topCount === n
                return (
                  <button
                    key={n}
                    type="button"
                    className={`segment-btn ${isSelected ? 'segment-active' : ''}`}
                    onClick={() => onChange({ ...config, topCount: n })}
                  >
                    <span>{n} jobs</span>
                  </button>
                )
              })}
            </div>
          </div>
        </div>

        {/* ─── Target Channels Indicator ───────────────────────────────── */}
        <div className="sources-ready-bar">
          <span className="sources-ready-title">Target Channels ({locations.length}):</span>
          <div className="sources-ready-list">
            {locations.map((locItem, i) => {
              const loc = locItem.location || 'Location'
              const wp = locItem.workplace || 'all'
              const wpName = wp === 'all' ? 'All Workplace Modes' : wp.toUpperCase()
              return (
                <span className="source-ready-tag" key={locItem.id || i}>
                  <CheckIcon size={11} className="source-check-icon" />
                  LinkedIn ({loc} · {wpName})
                </span>
              )
            })}
          </div>
        </div>

        {/* ─── Search CTA Button ───────────────────────────────────────── */}
        <div className="search-action-row">
          <button
            className="btn-primary btn-lg search-submit-btn"
            onClick={onSearch}
            id="search-btn"
          >
            <SearchIcon size={18} />
            <span>Scan LinkedIn Jobs ({locations.length} Locations)</span>
          </button>
          <span className="search-time-note">
            Crawling live LinkedIn feeds for {locations.map(l => `${l.location || 'Location'} (${l.workplace})`).join(', ')} · Crawlee &amp; Playwright
          </span>
        </div>
      </div>
    </div>
  )
}


