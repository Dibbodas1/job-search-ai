import { SparklesIcon } from './Icons'

export default function Hero({ children }) {
  const sources = [
    { name: 'BDjobs', color: '#f59e0b', tag: 'Bangladesh Local', icon: '🇧🇩' },
    { name: 'Indeed', color: '#003a9b', tag: 'BD & Worldwide', icon: '🔍' },
    { name: 'LinkedIn', color: '#0a66c2', tag: 'Local & Global', icon: '💼' },
    { name: 'WeWorkRemotely', color: '#14b8a6', tag: 'Top Remote Tech', icon: '🏠' },
    { name: 'Remotive', color: '#10b981', tag: 'Vetted Remote', icon: '🌐' },
    { name: 'RemoteOK', color: '#ec4899', tag: 'Developer Roles', icon: '🟢' },
    { name: 'Jobicy', color: '#f97316', tag: 'Global Tech', icon: '📋' },
    { name: 'Arbeitnow', color: '#8b5cf6', tag: 'EU & Worldwide', icon: '⚡' },
  ]

  return (
    <section className="hero" id="hero">
      <div className="hero-atmosphere" />

      <div className="hero-badge">
        <SparklesIcon size={14} className="hero-badge-icon" />
        <span>Multi-Platform AI Engine · BDjobs · Indeed · LinkedIn · WeWorkRemotely & More</span>
      </div>

      <h1 className="hero-title">
        Target Developer Jobs <br />
        <span className="hero-title-gradient">Across 8+ Premier Platforms</span>
      </h1>

      <p className="hero-subtitle">
        Upload your resume or specify your custom skills. We scan BDjobs, Indeed, LinkedIn,
        WeWorkRemotely, Remotive, RemoteOK, Jobicy &amp; Arbeitnow simultaneously across Bangladesh and Worldwide Remote,
        eliminate duplicates, and score every role against your qualifications.
      </p>

      <div className="hero-sources-strip">
        <span className="sources-label">Supported Job Networks:</span>
        <div className="hero-sources-list">
          {sources.map(s => (
            <div className="source-pill" key={s.name}>
              <span className="source-pill-icon">{s.icon}</span>
              <span className="source-indicator" style={{ backgroundColor: s.color }} />
              <span className="source-name">{s.name}</span>
              <span className="source-tag">{s.tag}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="hero-upload-container">
        {children}
      </div>
    </section>
  )
}

