import { useEffect, useRef, useState } from 'react'
import { Activity, ArrowDownRight, Gauge, TrendingDown, TrendingUp, Wallet } from 'lucide-react'

import Navbar from './components/Navbar'
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

import { simulatePortfolio } from './services/api'
import { formatCurrency, formatSignedPercent } from './utils/format'

export default function App() {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const resultsRef = useRef(null)

  async function handleOptimize(riskProfile, initialBalance) {
    setLoading(true)
    setError('')
    try {
      const data = await simulatePortfolio(riskProfile, initialBalance)
      setResult(data)
    } catch (err) {
      setError(err.message || 'Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  // Bring the results into view when a new simulation finishes.
  useEffect(() => {
    if (!result) return
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    resultsRef.current?.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'start' })
  }, [result])

  const isGain = result ? result.total_return >= 0 : true

  return (
    <>
      <Navbar />
      <main id="top">
        <section id="simulation" className="hero">
          <div className="container hero__grid">
            <HeroSection />
            <SimulationForm onSubmit={handleOptimize} loading={loading} />
          </div>
        </section>

        <div className="container stack">
          {error && <ErrorBanner message={error} />}
          {loading && <LoadingPanel />}

          {result && !loading && (
            <section ref={resultsRef} className="results stack" aria-labelledby="results-title">
              <h2 id="results-title" className="results__title">Portfolio overview</h2>

              <div className="metrics">
                <MetricCard
                  icon={Wallet}
                  label="Final value"
                  value={formatCurrency(result.final_portfolio_value)}
                  hint={`from ${formatCurrency(result.initial_balance)}`}
                />
                <MetricCard
                  icon={isGain ? TrendingUp : TrendingDown}
                  label="Total return"
                  value={formatSignedPercent(result.total_return)}
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
                  value={formatSignedPercent(result.max_drawdown)}
                  tone="negative"
                  hint="Largest fall from a peak"
                />
              </div>

              <AllocationChart weights={result.target_weights} initialBalance={result.initial_balance} />
              <PerformanceChart values={result.portfolio_values} initialBalance={result.initial_balance} />

              <div className="two-col">
                <RiskAnalysis result={result} />
                <SimulationDetails result={result} />
              </div>
            </section>
          )}

          {!result && !loading && !error && (
            <p className="empty">
              <Activity size={18} aria-hidden="true" /> Results will appear here after you run a
              simulation.
            </p>
          )}

          <AboutSection />
          <Disclaimer />
        </div>
      </main>
      <footer className="footer">Portfolio Optimizer · Academic project</footer>
    </>
  )
}