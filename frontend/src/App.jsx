
import { useEffect, useRef, useState } from 'react'
import {
  Activity,
  ArrowDownRight,
  Gauge,
  TrendingDown,
  TrendingUp,
  Wallet,
  LayoutDashboard,
  ChartNoAxesCombined,
  CircleHelp,
  Menu,
  X,
} from 'lucide-react'

import HeroSection from './components/HeroSection'
import SimulationForm from './components/SimulationForm'
import LoadingPanel from './components/LoadingPanel'
import ErrorBanner from './components/ErrorBanner'
import MetricCard from './components/MetricCard'
import AllocationChart from './components/AllocationChart'
import PerformanceChart from './components/PerformanceChart'
import RiskAnalysis from './components/RiskAnalysis'
import SimulationDetails from './components/SimulationDetails'
import AboutSection from './components/AboutSection'
import Disclaimer from './components/Disclaimer'
import PortfolioOnboarding from './components/PortfolioOnboarding'

import { simulatePortfolio } from './services/api'
import { formatCurrency, formatSignedPercent } from './utils/format'

export default function App() {
  const [activePage, setActivePage] = useState('portfolio')
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const resultsRef = useRef(null)

  async function handleOptimize(riskProfile, initialBalance) {
    setLoading(true)
    setError('')

    try {
      const data = await simulatePortfolio(
        riskProfile,
        initialBalance
      )

      setResult(data)
    } catch (err) {
      setError(
        err.message || 'Something went wrong. Please try again.'
      )
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!result || activePage !== 'simulation') return

    const reduceMotion = window.matchMedia(
      '(prefers-reduced-motion: reduce)'
    ).matches

    resultsRef.current?.scrollIntoView({
      behavior: reduceMotion ? 'auto' : 'smooth',
      block: 'start',
    })
  }, [result, activePage])

  const isGain = result ? result.total_return >= 0 : true

  const switchPage = page => {
    setActivePage(page)
    setMobileMenuOpen(false)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <div className="app-layout">
      <aside className={`app-sidebar ${mobileMenuOpen ? 'app-sidebar--open' : ''}`} aria-label="Main navigation">
        <div className="app-sidebar__brand">
          <div className="app-brand-mark"><ChartNoAxesCombined size={21} strokeWidth={2.2} /></div>
          <div><strong>Portfolio Optimizer</strong><span>Investment analytics</span></div>
          <button type="button" className="app-menu-close" aria-label="Close menu" onClick={() => setMobileMenuOpen(false)}><X size={19} /></button>
        </div>
        <div className="app-sidebar__section-label">WORKSPACE</div>
        <nav className="app-sidebar__nav" aria-label="Portfolio sections">
          <button type="button" className={`app-nav-item ${activePage === 'portfolio' ? 'is-active' : ''}`} aria-current={activePage === 'portfolio' ? 'page' : undefined} onClick={() => switchPage('portfolio')}>
            <LayoutDashboard size={18} /> <span>My Portfolio</span>
          </button>
          <button type="button" className={`app-nav-item ${activePage === 'simulation' ? 'is-active' : ''}`} aria-current={activePage === 'simulation' ? 'page' : undefined} onClick={() => switchPage('simulation')}>
            <ChartNoAxesCombined size={18} /> <span>Historical Simulation</span>
          </button>
        </nav>
        <div className="app-sidebar__bottom">
          <div className="app-sidebar__info"><CircleHelp size={17}/><span>Research and educational use</span></div>
          <div className="app-sidebar__version">PPO V2 · Academic project</div>
        </div>
      </aside>
      {mobileMenuOpen && <button type="button" className="app-mobile-overlay" aria-label="Close navigation" onClick={() => setMobileMenuOpen(false)} />}
      <div className="app-main-column">
        <header className="app-topbar">
          <div className="app-topbar__left">
            <button type="button" className="app-menu-toggle" aria-label="Open menu" onClick={() => setMobileMenuOpen(true)}><Menu size={21}/></button>
            <span className="app-breadcrumb">Workspace</span><span className="app-breadcrumb-separator">/</span>
            <span className="app-breadcrumb-current">{activePage === 'portfolio' ? 'My Portfolio' : 'Historical Simulation'}</span>
          </div>
          <div className="app-topbar__right"><span className="app-status-dot"/><span>Local analytics</span></div>
        </header>
        <main id="top" className="app-content">
          <div className="app-page-heading">
            <div>
              <p className="app-page-eyebrow">INVESTMENT WORKSPACE</p>
              <h1>{activePage === 'portfolio' ? 'My Portfolio' : 'Historical Simulation'}</h1>
              <p>{activePage === 'portfolio' ? 'Manage your holdings and review personalized AI allocation insights.' : 'Explore historical PPO performance and portfolio risk.'}</p>
            </div>
            <span className="app-page-chip">PPO V2 · Historical data</span>
          </div>
        {activePage === 'portfolio' ? (
          <PortfolioOnboarding />
        ) : (
          <>
            <section id="simulation" className="hero">
              <div className="container hero__grid">
                <HeroSection />

                <SimulationForm
                  onSubmit={handleOptimize}
                  loading={loading}
                />
              </div>
            </section>

            <div className="container stack">
              {error && <ErrorBanner message={error} />}
              {loading && <LoadingPanel />}

              {result && !loading && (
                <section
                  ref={resultsRef}
                  className="results stack"
                  aria-labelledby="results-title"
                >
                  <h2
                    id="results-title"
                    className="results__title"
                  >
                    Portfolio overview
                  </h2>

                  <div className="metrics">
                    <MetricCard
                      icon={Wallet}
                      label="Final value"
                      value={formatCurrency(
                        result.final_portfolio_value
                      )}
                      hint={`from ${formatCurrency(
                        result.initial_balance
                      )}`}
                    />

                    <MetricCard
                      icon={isGain ? TrendingUp : TrendingDown}
                      label="Total return"
                      value={formatSignedPercent(
                        result.total_return
                      )}
                      tone={isGain ? 'positive' : 'negative'}
                    />

                    <MetricCard
                      icon={Gauge}
                      label="Sharpe ratio"
                      value={result.sharpe_ratio.toFixed(2)}
                      hint="Risk-adjusted return"
                    />

                    <MetricCard
                      icon={ArrowDownRight}
                      label="Max drawdown"
                      value={formatSignedPercent(
                        result.max_drawdown
                      )}
                      tone="negative"
                      hint="Largest fall from a peak"
                    />
                  </div>

                  <AllocationChart
                    weights={result.target_weights}
                    initialBalance={result.initial_balance}
                  />

                  <PerformanceChart
                    values={result.portfolio_values}
                    initialBalance={result.initial_balance}
                  />

                  <div className="two-col">
                    <RiskAnalysis result={result} />
                    <SimulationDetails result={result} />
                  </div>
                </section>
              )}

              {!result && !loading && !error && (
                <p className="empty">
                  <Activity
                    size={18}
                    aria-hidden="true"
                  />
                  Results will appear here after you run a simulation.
                </p>
              )}

              <AboutSection />
              <Disclaimer />
            </div>
          </>
        )}
        </main>
        <footer className="footer app-footer">Portfolio Optimizer · Experimental research platform · Not investment advice</footer>
      </div>
    </div>
  )
}
