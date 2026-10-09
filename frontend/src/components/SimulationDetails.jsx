import { formatCurrency, formatNumber, getRiskLabel } from '../utils/format'

export default function SimulationDetails({ result }) {
  const years = result.steps / 252 // approx. trading days per year
  const rows = [
    ['Initial investment', formatCurrency(result.initial_balance)],
    ['Risk profile', `${result.risk_profile.toFixed(2)} (${getRiskLabel(result.risk_profile)})`],
    ['Simulation steps', `${formatNumber(result.steps)} days (about ${years.toFixed(1)} years)`],
    ['Final portfolio value', formatCurrency(result.final_portfolio_value)],
  ]

  return (
    <section className="card" aria-labelledby="details-title">
      <h2 id="details-title">Simulation details</h2>
      <dl className="details">
        {rows.map(([label, value]) => (
          <div key={label} className="details__row">
            <dt>{label}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
    </section>
  )
}