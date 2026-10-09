import { formatSignedPercent, getRiskLabel } from '../utils/format'

export default function RiskAnalysis({ result }) {
  const items = [
    {
      title: 'Sharpe ratio',
      value: result.sharpe_ratio.toFixed(2),
      text: 'Measures risk-adjusted performance. Higher values generally mean better returns relative to how much the portfolio value moved.',
    },
    {
      title: 'Maximum drawdown',
      value: formatSignedPercent(result.max_drawdown),
      text: 'The largest fall from a previous peak during the simulation. Smaller drops mean a smoother ride.',
    },
    {
      title: 'Total return',
      value: formatSignedPercent(result.total_return),
      text: 'How much the portfolio grew or shrank over the whole simulated period, compared with the starting amount.',
    },
    {
      title: 'Risk profile',
      value: `${result.risk_profile.toFixed(2)} · ${getRiskLabel(result.risk_profile)}`,
      text: 'The risk setting you chose (0 to 1). It is passed to the model as an input and does not guarantee a particular result.',
    },
  ]

  return (
    <section className="card" aria-labelledby="analysis-title">
      <h2 id="analysis-title">Risk and performance analysis</h2>
      <dl className="analysis">
        {items.map((item) => (
          <div key={item.title} className="analysis__item">
            <dt>
              {item.title}
              <span className="analysis__value">{item.value}</span>
            </dt>
            <dd>{item.text}</dd>
          </div>
        ))}
      </dl>
      {result.sharpe_ratio > 3 && (
        <p className="caution" role="note">
          A Sharpe ratio this high is unusual for real portfolios. Simulated results on historical
          data often look better than what is achievable in live markets, so treat the numbers as a
          demonstration.
        </p>
      )}
    </section>
  )
}