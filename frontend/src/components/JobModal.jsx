import { useEffect } from 'react'
import {
  XIcon,
  BuildingIcon,
  MapPinIcon,
  CalendarIcon,
  BriefcaseIcon,
  ExternalLinkIcon,
  SparklesIcon,
  CheckIcon
} from './Icons'

function getScoreTier(score) {
  if (score >= 60) return { label: 'Strong Match', class: 'score-high' }
  if (score >= 35) return { label: 'Moderate Match', class: 'score-mid' }
  return { label: 'Base Match', class: 'score-low' }
}

function getRemoteType(status) {
  const s = (status || '').toLowerCase()
  if (s.includes('remote')) return { label: 'Remote Role', class: 'badge-remote' }
  if (s.includes('hybrid')) return { label: 'Hybrid Role', class: 'badge-hybrid' }
  return { label: 'Onsite Role', class: 'badge-onsite' }
}

function getSourceMeta(source) {
  const s = (source || '').toLowerCase()
  if (s.includes('linkedin')) return { label: 'LinkedIn', class: 'source-linkedin' }
  if (s.includes('remotive')) return { label: 'Remotive', class: 'source-remotive' }
  if (s.includes('jobicy')) return { label: 'Jobicy', class: 'source-jobicy' }
  if (s.includes('remoteok')) return { label: 'RemoteOK', class: 'source-remoteok' }
  if (s.includes('arbeitnow')) return { label: 'Arbeitnow', class: 'source-arbeitnow' }
  return { label: source || 'External', class: 'source-default' }
}

function formatJobLink(link, jobId) {
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

export default function JobModal({ job, onClose }) {
  // ESC key handler
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [onClose])

  if (!job) return null

  const scoreTier = getScoreTier(job.score || 0)
  const remoteMeta = getRemoteType(job.remote_status)
  const sourceMeta = getSourceMeta(job.source)

  return (
    <div className="modal-backdrop" onClick={onClose} id="job-modal-overlay">
      <div className="modal-container" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="modal-header">
          <div className="modal-header-text">
            <div className="modal-badges-row">
              <span className={`badge-pill ${sourceMeta.class}`}>
                {sourceMeta.label}
              </span>
              <span className={`badge-pill ${remoteMeta.class}`}>
                {remoteMeta.label}
              </span>
              <span className={`modal-score-badge ${scoreTier.class}`}>
                {job.score}/100 · {scoreTier.label}
              </span>
            </div>
            <h2 className="modal-title">{job.title}</h2>
            <div className="modal-company-line">
              <BuildingIcon size={16} className="text-muted" />
              <span>{job.company || 'Confidential Company'}</span>
            </div>
          </div>

          <button
            type="button"
            className="modal-close-btn"
            onClick={onClose}
            id="modal-close-btn"
            title="Close dialog (Esc)"
          >
            <XIcon size={18} />
          </button>
        </div>

        {/* Content Body */}
        <div className="modal-body">
          {/* Quick info chips grid */}
          <div className="modal-info-grid">
            <div className="modal-info-item">
              <span className="info-item-label">
                <MapPinIcon size={13} className="text-muted" />
                <span>Location</span>
              </span>
              <span className="info-item-val">{job.location || 'Not Specified'}</span>
            </div>

            <div className="modal-info-item">
              <span className="info-item-label">
                <CalendarIcon size={13} className="text-muted" />
                <span>Date Posted</span>
              </span>
              <span className="info-item-val">{job.date_posted || 'Recently'}</span>
            </div>

            <div className="modal-info-item">
              <span className="info-item-label">
                <BriefcaseIcon size={13} className="text-muted" />
                <span>Experience Level</span>
              </span>
              <span className="info-item-val">{job.experience || 'Flexible / Mid-Senior'}</span>
            </div>
          </div>

          {/* AI Match Analysis */}
          <div className="modal-section-card">
            <div className="section-card-heading">
              <SparklesIcon size={16} className="text-indigo" />
              <span>AI Fit &amp; Skill Alignment Analysis</span>
            </div>
            <div className="section-card-body">
              <p className="modal-reason-text">{job.reason || 'Strong candidate alignment with role requirements.'}</p>
            </div>
          </div>

          {/* Verification / Security note */}
          <div className="modal-trust-note">
            <CheckIcon size={13} className="text-emerald" />
            <span>Listing verified from public feed via {sourceMeta.label}. Direct application link provided below.</span>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="modal-footer">
          <button
            type="button"
            className="btn-ghost"
            onClick={onClose}
          >
            Close
          </button>

          {(job.link || job.job_id) && (
            <a
              href={formatJobLink(job.link, job.job_id)}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-primary modal-apply-cta"
            >
              <span>Apply on LinkedIn</span>
              <ExternalLinkIcon size={15} />
            </a>
          )}
        </div>
      </div>
    </div>
  )
}
