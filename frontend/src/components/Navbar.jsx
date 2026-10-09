import { Landmark } from 'lucide-react'

export default function Navbar() {
  return (
    <header className="navbar">
      <div className="container navbar__inner">
        <a className="brand" href="#top">
          <span className="brand__mark" aria-hidden="true">
            <Landmark size={20} />
          </span>
          <span>
            <span className="brand__name">Portfolio Optimizer</span>
            <span className="brand__tag">AI-powered portfolio allocation</span>
          </span>
        </a>
        <nav aria-label="Primary">
          <ul className="nav-links">
            <li><a href="#top">Dashboard</a></li>
            <li><a href="#simulation">Simulation</a></li>
            <li><a href="#about">About</a></li>
          </ul>
        </nav>
      </div>
    </header>
  )
}