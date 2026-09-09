import { SparklesIcon } from './Icons'

export default function Hero({ children }) {
  const sources = [
    { name: 'LinkedIn (Bangladesh)', color: '#0a66c2', tag: 'Dhaka & Hybrid' },
    { name: 'LinkedIn (Remote)', color: '#38bdf8', tag: 'Global Tech Roles' },
  ]

  return (
    <section className="hero" id="hero">
      <div className="hero-atmosphere" />

      <div className="hero-badge">
        <SparklesIcon size={14} className="hero-badge-icon" />
        <span>Gemini 3.6 AI · Real-time LinkedIn Developer Intelligence</span>
      </div>

      <h1 className="hero-title">
        Target Developer Jobs <br />
        <span className="hero-title-gradient">Matched to Your Exact Stack</span>
      </h1>

      <p className="hero-subtitle">
        Upload your resume or specify your custom skills. We scan live LinkedIn job feeds
        across Bangladesh and Worldwide Remote, filter out the noise, and score every role against your qualifications.
      </p>

      <div className="hero-sources-strip">
        <span className="sources-label">Target Network:</span>
        <div className="hero-sources-list">
          {sources.map(s => (
            <div className="source-pill" key={s.name}>
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

