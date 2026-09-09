import { useState, useCallback } from 'react'
import Hero from './components/Hero'
import CVUpload from './components/CVUpload'
import SearchPanel from './components/SearchPanel'
import SearchProgress from './components/SearchProgress'
import ResultsDashboard from './components/ResultsDashboard'
import JobModal from './components/JobModal'
import { ZapIcon, RefreshCwIcon, AlertCircleIcon, XIcon, CheckIcon } from './components/Icons'

const API_BASE = import.meta.env.VITE_API_BASE || '/api'

// Default skills requested by user: React, MongoDB, Express.js, and JavaScript
const DEFAULT_MERN_PROFILE = {
  name: 'Candidate (Skills Mode)',
  title: 'Full Stack JavaScript Developer',
  experience_summary: 'Targeting modern web developer roles specializing in React, MongoDB, Express.js, and JavaScript.',
  skills: {
    core: ['React', 'JavaScript', 'Express.js', 'MongoDB'],
    frontend: ['React', 'JavaScript'],
    backend: ['Express.js', 'MongoDB'],
    tools: ['Git', 'REST APIs'],
  },
  years_experience: 2,
  source: 'manual',
}

export default function App() {
  // ─── State ──────────────────────────────────────────────────────
  const [stage, setStage] = useState('landing') // landing | uploading | uploaded | searching | results
  const [cvProfile, setCvProfile] = useState(null)
  const [results, setResults] = useState(null)
  const [searchConfig, setSearchConfig] = useState({
    locations: [
      { id: 'loc-1', location: 'Bangladesh', workplace: 'onsite' },
      { id: 'loc-2', location: 'Worldwide', workplace: 'remote' }
    ],
    timeframe: 'week',
    days: 7,
    topCount: 15,
  })
  const [resultId, setResultId] = useState(null)
  const [stats, setStats] = useState(null)
  const [aiSummary, setAiSummary] = useState(null)
  const [timeframeLabel, setTimeframeLabel] = useState('')
  const [selectedJob, setSelectedJob] = useState(null)
  const [error, setError] = useState(null)
  const [exporting, setExporting] = useState(false)

  // ─── CV Upload ──────────────────────────────────────────────────
  const handleCVUpload = useCallback(async (file) => {
    setStage('uploading')
    setError(null)

    const formData = new FormData()
    formData.append('cv', file)

    try {
      const resp = await fetch(`${API_BASE}/upload-cv`, { method: 'POST', body: formData })
      const text = await resp.text()
      let data
      try {
        data = JSON.parse(text)
      } catch {
        throw new Error(`Server returned an invalid response (${resp.status} ${resp.statusText || 'Error'})`)
      }

      if (!resp.ok || !data.success) {
        throw new Error(data.error || 'Failed to parse CV')
      }

      // Mark source as cv
      const profile = { ...data.profile, source: 'cv' }
      setCvProfile(profile)
      setStage('uploaded')
    } catch (err) {
      setError(err.message)
      setStage('landing')
    }
  }, [])

  // ─── Manual Skills Mode (No CV Needed) ──────────────────────────
  const handleStartManual = useCallback(() => {
    setCvProfile(JSON.parse(JSON.stringify(DEFAULT_MERN_PROFILE)))
    setStage('uploaded')
    setError(null)
  }, [])

  // ─── Interactive Skill Editing: Remove Skill ────────────────────
  const handleRemoveSkill = useCallback((category, skillToRemove) => {
    setCvProfile(prev => {
      if (!prev || !prev.skills) return prev
      const catSkills = prev.skills[category] || []
      const updatedCatSkills = catSkills.filter(
        s => s.toLowerCase() !== skillToRemove.toLowerCase()
      )
      return {
        ...prev,
        skills: {
          ...prev.skills,
          [category]: updatedCatSkills,
        },
      }
    })
  }, [])

  // ─── Interactive Skill Editing: Add Skill ───────────────────────
  const handleAddSkill = useCallback((category, newSkill) => {
    const trimmed = (newSkill || '').trim()
    if (!trimmed) return
    setCvProfile(prev => {
      if (!prev) return prev
      const currentSkills = prev.skills || {}
      const catSkills = currentSkills[category] || []
      if (catSkills.some(s => s.toLowerCase() === trimmed.toLowerCase())) {
        return prev // already exists
      }
      return {
        ...prev,
        skills: {
          ...currentSkills,
          [category]: [...catSkills, trimmed],
        },
      }
    })
  }, [])

  // ─── Reset to Default MERN Skills ───────────────────────────────
  const handleResetDefaults = useCallback(() => {
    setCvProfile(JSON.parse(JSON.stringify(DEFAULT_MERN_PROFILE)))
  }, [])

  // ─── Job Search ─────────────────────────────────────────────────
  const handleSearch = useCallback(async () => {
    if (!cvProfile) return
    setStage('searching')
    setError(null)
    setResults(null)

    const skills = cvProfile.skills || {}

    try {
      const resp = await fetch(`${API_BASE}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          skills,
          locations: searchConfig.locations || [
            { location: 'Bangladesh', workplace: 'onsite' },
            { location: 'Worldwide', workplace: 'remote' }
          ],
          timeframe: searchConfig.timeframe,
          days: searchConfig.days,
          top_count: searchConfig.topCount,
          profile: cvProfile,
        }),
      })
      const text = await resp.text()
      let data
      try {
        data = JSON.parse(text)
      } catch {
        throw new Error(
          resp.status === 504 || resp.status === 502
            ? 'The search request timed out. Please try again with a shorter timeframe.'
            : `Search request error (${resp.status} ${resp.statusText || 'Unknown error'})`
        )
      }

      if (!resp.ok || !data.success) {
        throw new Error(data.error || 'Search failed')
      }

      setResults({
        all_jobs: data.all_jobs || [],
        jobs_by_location: data.jobs_by_location || {},
        location_targets: data.location_targets || searchConfig.locations || [],
        bangladesh_jobs: data.bangladesh_jobs || data.local_jobs || [],
        local_jobs: data.local_jobs || data.bangladesh_jobs || [],
        remote_jobs: data.remote_jobs || [],
        location_label: data.location_label || '',
      })

      setResultId(data.result_id)
      setStats(data.stats)
      setAiSummary(data.ai_summary)
      setTimeframeLabel(data.timeframe)
      setStage('results')
    } catch (err) {
      setError(err.message)
      setStage('uploaded')
    }
  }, [cvProfile, searchConfig])

  // ─── Excel Export ───────────────────────────────────────────────
  const handleExportExcel = useCallback(async () => {
    if (!results) return
    setExporting(true)
    try {
      const resp = await fetch(`${API_BASE}/download-excel`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          result_id: resultId,
          location_label: results.location_label,
          location_targets: results.location_targets,
          jobs_by_location: results.jobs_by_location,
          bangladesh_jobs: results.bangladesh_jobs,
          remote_jobs: results.remote_jobs,
          timeframe: timeframeLabel,
        }),
      })

      if (!resp.ok) {
        const errData = await resp.json().catch(() => ({ error: 'Download failed' }))
        throw new Error(errData.error || 'Download failed')
      }

      const blob = await resp.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `LinkedIn_Job_Matches_${new Date().toISOString().slice(0, 10)}.xlsx`
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
    } catch (err) {
      setError(err.message)
    } finally {
      setExporting(false)
    }
  }, [results, resultId, timeframeLabel])

  // ─── Reset Handlers ─────────────────────────────────────────────
  const handleReset = useCallback(() => {
    setStage('uploaded')
    setResults(null)
    setResultId(null)
    setStats(null)
    setAiSummary(null)
    setError(null)
  }, [])

  const handleFullReset = useCallback(() => {
    setStage('landing')
    setCvProfile(null)
    setResults(null)
    setResultId(null)
    setStats(null)
    setAiSummary(null)
    setError(null)
  }, [])

  // Step indicator state
  const currentStep = (stage === 'landing' || stage === 'uploading') ? 1 : (stage === 'uploaded' || stage === 'searching') ? 2 : 3

  return (
    <div className="app-shell">
      {/* Top Navigation */}
      <header className="navbar" id="navbar">
        <div className="navbar-inner">
          {/* Logo & Brand */}
          <div className="navbar-brand" onClick={handleFullReset} role="button" tabIndex={0}>
            <div className="brand-icon-box">
              <ZapIcon size={18} className="brand-zap-icon" />
            </div>
            <div className="brand-text">
              <span className="brand-name">JobPulse</span>
              <span className="brand-tag">LinkedIn AI</span>
            </div>
          </div>

          {/* Workflow Step Tracker (Desktop / Tablet) */}
          <div className="nav-stepper">
            <div className={`step-item ${currentStep >= 1 ? 'step-item-active' : ''}`}>
              <span className="step-num">{currentStep > 1 ? <CheckIcon size={12} /> : '1'}</span>
              <span className="step-label">Skills / CV</span>
            </div>
            <div className="step-divider" />
            <div className={`step-item ${currentStep >= 2 ? 'step-item-active' : ''}`}>
              <span className="step-num">{currentStep > 2 ? <CheckIcon size={12} /> : '2'}</span>
              <span className="step-label">Configure &amp; Edit</span>
            </div>
            <div className="step-divider" />
            <div className={`step-item ${currentStep === 3 ? 'step-item-active' : ''}`}>
              <span className="step-num">3</span>
              <span className="step-label">LinkedIn Matches</span>
            </div>
          </div>

          {/* Navbar Actions */}
          <div className="navbar-actions">
            {stage === 'results' && stats && (
              <div className="nav-matches-badge">
                <span className="nav-pulse-dot" />
                <span>{stats.total_bd_selected + stats.total_remote_selected} Curated Roles</span>
              </div>
            )}

            {cvProfile && stage !== 'landing' && (
              <button
                type="button"
                className="btn-restart"
                onClick={handleFullReset}
                title="Start over from upload"
              >
                <RefreshCwIcon size={13} />
                <span>Start Over</span>
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Global Error Banner */}
      {error && (
        <div className="error-toast-container">
          <div className="error-toast">
            <AlertCircleIcon size={18} className="error-toast-icon" />
            <span className="error-toast-message">{error}</span>
            <button
              type="button"
              className="error-toast-close"
              onClick={() => setError(null)}
              title="Dismiss error"
            >
              <XIcon size={14} />
            </button>
          </div>
        </div>
      )}

      {/* Main Viewport Container */}
      <main className="main-content">
        {/* Stage 1: Landing & Upload */}
        {(stage === 'landing' || stage === 'uploading') && (
          <Hero>
            <CVUpload
              onUpload={handleCVUpload}
              isUploading={stage === 'uploading'}
              onStartManual={handleStartManual}
            />
          </Hero>
        )}

        {/* Stage 2: Profile Analyzed / Skills Customized & Search Config */}
        {stage === 'uploaded' && (
          <div className="workspace-view">
            <div className="workspace-header">
              <h2 className="workspace-title">Skills Profile Ready for Matching</h2>
              <p className="workspace-subtitle">
                Customize your technical skills and target location below (search any city, state, or country), then launch the live LinkedIn job search.
              </p>
            </div>

            <div className="workspace-columns">
              <div className="workspace-col-profile">
                <CVUpload
                  onUpload={handleCVUpload}
                  isUploading={false}
                  profile={cvProfile}
                  compact
                  onRemoveSkill={handleRemoveSkill}
                  onAddSkill={handleAddSkill}
                  onResetDefaults={handleResetDefaults}
                />
              </div>

              <div className="workspace-col-search">
                <SearchPanel
                  config={searchConfig}
                  onChange={setSearchConfig}
                  onSearch={handleSearch}
                />
              </div>
            </div>
          </div>
        )}

        {/* Stage 2.5: Searching In Progress */}
        {stage === 'searching' && (
          <div className="searching-view">
            <SearchProgress
              timeframe={searchConfig}
              config={searchConfig}
              locations={searchConfig.locations}
            />
          </div>
        )}

        {/* Stage 3: Results Dashboard */}
        {stage === 'results' && results && (
          <div className="results-view">
            <ResultsDashboard
              results={results}
              stats={stats}
              aiSummary={aiSummary}
              timeframe={timeframeLabel}
              onSelectJob={setSelectedJob}
              onExport={handleExportExcel}
              exporting={exporting}
              onNewSearch={handleReset}
            />
          </div>
        )}
      </main>

      {/* Job Detail Modal */}
      {selectedJob && (
        <JobModal job={selectedJob} onClose={() => setSelectedJob(null)} />
      )}

      {/* Global Footer */}
      <footer className="footer">
        <div className="footer-inner">
          <div className="footer-left">
            <span className="footer-brand">JobPulse AI</span>
            <span className="footer-sep">·</span>
            <span>Real-time LinkedIn Developer Job Intelligence</span>
          </div>
          <div className="footer-sources">
            <span>Powered by Gemini 3.6 Flash</span>
            <span className="footer-sep">·</span>
            <span>LinkedIn ({searchConfig.location || 'Selected Location'})</span>
            <span className="footer-sep">·</span>
            <span>LinkedIn (Worldwide Remote)</span>
          </div>
        </div>
      </footer>
    </div>
  )
}

