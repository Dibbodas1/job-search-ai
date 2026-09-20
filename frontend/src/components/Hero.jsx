import { SparklesIcon } from './Icons'

export default function Hero({ children }) {
  const sources = [
    { name: 'LinkedIn', color: '#0a66c2', tag: 'Local & Global', icon: '💼' },
  ]

  return (
    <section className="hero" id="hero">
      <div className="hero-atmosphere" />

      <div className="hero-badge">
        <SparklesIcon size={14} className="hero-badge-icon" />
        <span>LinkedIn Job Intelligence Engine</span>
      </div>

      <h1 className="hero-title">
        Target Developer Jobs <br />
        <span className="hero-title-gradient">On LinkedIn</span>
      </h1>

      <p className="hero-subtitle">
        Upload your resume or specify your custom skills. We scan LinkedIn for the best matches across your target locations,
        eliminate duplicates, and score every role against your qualifications.
      </p>

      <div className="hero-sources-strip">
        <span className="sources-label">Supported Job Network:</span>
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

