import { useState, useRef, useCallback } from 'react'
import {
  UploadCloudIcon,
  FileTextIcon,
  UserIcon,
  RefreshCwIcon,
  SparklesIcon,
  PlusIcon,
  XIcon,
} from './Icons'

export default function CVUpload({
  onUpload,
  isUploading,
  profile,
  compact,
  onStartManual,
  onRemoveSkill,
  onAddSkill,
  onResetDefaults,
}) {
  const [dragOver, setDragOver] = useState(false)
  const [newSkillInputs, setNewSkillInputs] = useState({})
  const fileInputRef = useRef(null)

  const handleFile = useCallback((file) => {
    if (file && (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf'))) {
      onUpload(file)
    }
  }, [onUpload])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    handleFile(file)
  }, [handleFile])

  const handleDragOver = useCallback((e) => {
    e.preventDefault()
    setDragOver(true)
  }, [])

  const handleDragLeave = useCallback(() => setDragOver(false), [])

  const handleInputChange = useCallback((e) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0])
    }
  }, [handleFile])

  const handleSkillInputChange = (category, value) => {
    setNewSkillInputs(prev => ({ ...prev, [category]: value }))
  }

  const handleAddSkillSubmit = (e, category) => {
    e.preventDefault()
    const value = (newSkillInputs[category] || '').trim()
    if (value && onAddSkill) {
      onAddSkill(category, value)
      setNewSkillInputs(prev => ({ ...prev, [category]: '' }))
    }
  }

  // Quick suggestion chips for rapid customization
  const SUGGESTED_EXTRAS = [
    { name: 'Node.js', category: 'backend' },
    { name: 'TypeScript', category: 'core' },
    { name: 'Next.js', category: 'frontend' },
    { name: 'Tailwind CSS', category: 'frontend' },
    { name: 'Redux', category: 'frontend' },
    { name: 'Docker', category: 'tools' },
    { name: 'PostgreSQL', category: 'backend' },
    { name: 'GraphQL', category: 'backend' },
    { name: 'Python', category: 'languages' },
  ]

  // ─── 1. Uploading State ──────────────────────────────────────────
  if (isUploading) {
    return (
      <div className="upload-container">
        <div className="card uploading-card">
          <div className="upload-pulse-hub">
            <div className="pulse-ring" />
            <div className="pulse-core">
              <SparklesIcon size={24} className="pulse-icon" />
            </div>
          </div>
          <h3 className="uploading-title">Analyzing Your Resume</h3>
          <p className="uploading-subtitle">
            Gemini 3.6 is parsing your experience, core skills, and technical specialization...
          </p>

          <div className="uploading-steps">
            <div className="uploading-step active">
              <span className="step-dot" />
              <span>Extracting PDF text and document structure</span>
            </div>
            <div className="uploading-step active">
              <span className="step-dot" />
              <span>Identifying technical skills and stack depth</span>
            </div>
            <div className="uploading-step active">
              <span className="step-dot" />
              <span>Synthesizing candidate profile summary</span>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // ─── 2. Compact Skills Display (Post-upload or Manual Skills Mode) ────────────────
  if (profile && compact) {
    const skills = profile.skills || {}
    // Ensure all standard categories exist so the user can easily add to any bucket
    const standardCategories = ['core', 'frontend', 'backend', 'tools']
    const allCategoryKeys = Array.from(new Set([...standardCategories, ...Object.keys(skills)]))

    const initials = (profile.name || 'U')
      .split(' ')
      .map(w => w[0])
      .join('')
      .slice(0, 2)
      .toUpperCase()

    const totalSkillCount = Object.values(skills).reduce(
      (acc, items) => acc + (Array.isArray(items) ? items.length : 0),
      0
    )

    // Collect all existing skills in lowercase to hide already added suggestions
    const existingSkillsFlat = new Set(
      Object.values(skills)
        .flat()
        .filter(Boolean)
        .map(s => String(s).toLowerCase())
    )

    return (
      <div className="profile-summary-container" id="profile-summary">
        <input
          type="file"
          ref={fileInputRef}
          accept=".pdf"
          onChange={handleInputChange}
          style={{ display: 'none' }}
          id="cv-reupload-input"
        />

        <div className="card profile-card">
          {/* Header */}
          <div className="profile-header">
            <div className="profile-identity">
              <div className="profile-avatar">
                {initials || <UserIcon size={18} />}
              </div>
              <div>
                <div className="profile-name-row">
                  <h3 className="profile-name">{profile.name || 'Candidate Profile'}</h3>
                  <span className={`profile-badge ${profile.source === 'manual' ? 'profile-badge-manual' : ''}`}>
                    {profile.source === 'manual' ? 'Skills Search Mode' : 'CV Extracted'}
                  </span>
                </div>
                <p className="profile-role">{profile.title || 'Full Stack JavaScript Developer'}</p>
              </div>
            </div>

            <div className="profile-header-actions">
              <button
                type="button"
                className="btn-ghost btn-xs"
                onClick={() => fileInputRef.current?.click()}
                title="Upload a new PDF resume"
              >
                <UploadCloudIcon size={13} />
                <span>Upload CV</span>
              </button>

              {onResetDefaults && (
                <button
                  type="button"
                  className="btn-ghost btn-xs"
                  onClick={onResetDefaults}
                  title="Reset to MERN defaults (React, MongoDB, Express, JavaScript)"
                >
                  <RefreshCwIcon size={13} />
                  <span>MERN Defaults</span>
                </button>
              )}
            </div>
          </div>

          {/* Experience / Profile Summary */}
          {profile.experience_summary && (
            <div className="profile-summary-box">
              <p>{profile.experience_summary}</p>
            </div>
          )}

          {/* Skill Groups with Interactive Add / Remove */}
          <div className="profile-skills-wrapper">
            <div className="skills-section-heading">
              <div className="skills-heading-left">
                <span>Technical Skills Profile</span>
                <span className="skills-tip-text">· Click &times; to remove, or type to add</span>
              </div>
              <span className="skills-total-count">
                {totalSkillCount} active skills
              </span>
            </div>

            <div className="skills-categories-grid">
              {allCategoryKeys.map(category => {
                const items = Array.isArray(skills[category]) ? skills[category] : []
                return (
                  <div className="skill-group-card" key={category}>
                    <div className="skill-group-header">
                      <span className="skill-group-title">{category}</span>
                      <span className="skill-group-count">{items.length}</span>
                    </div>

                    {/* Skill Badges */}
                    <div className="skill-tags-list">
                      {items.map((skill, i) => (
                        <span className="skill-tag skill-tag-editable" key={i}>
                          <span className="skill-tag-text">{skill}</span>
                          {onRemoveSkill && (
                            <button
                              type="button"
                              className="skill-remove-btn"
                              onClick={(e) => {
                                e.stopPropagation()
                                onRemoveSkill(category, skill)
                              }}
                              title={`Remove ${skill}`}
                              aria-label={`Remove ${skill}`}
                            >
                              &times;
                            </button>
                          )}
                        </span>
                      ))}

                      {items.length === 0 && (
                        <span className="skill-empty-hint">No skills in this group</span>
                      )}
                    </div>

                    {/* Inline Add Skill Input */}
                    {onAddSkill && (
                      <form
                        className="skill-add-form"
                        onSubmit={(e) => handleAddSkillSubmit(e, category)}
                      >
                        <input
                          type="text"
                          className="skill-add-input"
                          placeholder={`+ Add to ${category}...`}
                          value={newSkillInputs[category] || ''}
                          onChange={(e) => handleSkillInputChange(category, e.target.value)}
                        />
                        {(newSkillInputs[category] || '').trim() && (
                          <button type="submit" className="skill-add-btn">
                            <PlusIcon size={12} />
                            <span>Add</span>
                          </button>
                        )}
                      </form>
                    )}
                  </div>
                )
              })}
            </div>

            {/* Quick Add Suggestions Bar */}
            {onAddSkill && (
              <div className="quick-suggestions-block">
                <span className="quick-suggestions-label">Quick Add Popular Tech:</span>
                <div className="quick-suggestions-chips">
                  {SUGGESTED_EXTRAS.filter(s => !existingSkillsFlat.has(s.name.toLowerCase())).map(s => (
                    <button
                      key={s.name}
                      type="button"
                      className="suggested-chip"
                      onClick={() => onAddSkill(s.category, s.name)}
                      title={`Add ${s.name} to ${s.category}`}
                    >
                      <PlusIcon size={11} />
                      <span>{s.name}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    )
  }

  // ─── 3. Initial Upload Dropzone + Manual Start Option ─────────────
  return (
    <div className="upload-container" id="cv-upload-hub">
      <input
        type="file"
        ref={fileInputRef}
        accept=".pdf"
        onChange={handleInputChange}
        style={{ display: 'none' }}
        id="cv-upload-input"
      />

      {/* Primary Dropzone */}
      <div
        className={`dropzone ${dragOver ? 'dropzone-active' : ''}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => fileInputRef.current?.click()}
        id="cv-upload-zone"
      >
        <div className="dropzone-icon-wrap">
          <UploadCloudIcon size={26} className="dropzone-icon" />
        </div>

        <div className="dropzone-body">
          <h3 className="dropzone-title">Upload your resume to begin</h3>
          <p className="dropzone-description">
            Drag and drop your PDF resume here, or <span className="text-primary-link">browse files</span>
          </p>
        </div>

        <div className="dropzone-meta">
          <span className="meta-badge">
            <FileTextIcon size={12} />
            PDF format only
          </span>
          <span className="meta-bullet">·</span>
          <span className="meta-badge">Up to 10MB</span>
          <span className="meta-bullet">·</span>
          <span className="meta-badge">Protected &amp; confidential</span>
        </div>

        <button className="btn-primary dropzone-cta" type="button">
          <FileTextIcon size={15} />
          <span>Select PDF File</span>
        </button>
      </div>

      {/* Or: Search by Tech Stack without CV */}
      {onStartManual && (
        <div className="manual-skills-prompt">
          <div className="manual-prompt-divider">
            <span className="manual-divider-line" />
            <span className="manual-divider-text">OR SEARCH BY TECH STACK</span>
            <span className="manual-divider-line" />
          </div>

          <div className="manual-prompt-card">
            <div className="manual-prompt-info">
              <div className="manual-prompt-heading">
                <SparklesIcon size={16} className="text-primary" />
                <h4 className="manual-prompt-title">Search without uploading a resume</h4>
              </div>
              <p className="manual-prompt-desc">
                Quick-start with default developer skills:{' '}
                <strong className="text-highlight">React</strong>,{' '}
                <strong className="text-highlight">MongoDB</strong>,{' '}
                <strong className="text-highlight">Express.js</strong>, and{' '}
                <strong className="text-highlight">JavaScript</strong>.
                You can add or remove skills as needed.
              </p>
            </div>

            <button
              type="button"
              className="btn-secondary btn-manual-start"
              onClick={onStartManual}
              id="btn-manual-skills"
            >
              <SparklesIcon size={15} />
              <span>Search with Skills (No CV)</span>
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

