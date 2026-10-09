import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import { ASSETS } from '../utils/assets'
import { formatCurrency, formatPercent } from '../utils/format'

export default function AllocationChart({ weights, initialBalance }) {
  const rows = ASSETS.map((asset) => ({
    ...asset,
    weight: weights[asset.key],
    amount: weights[asset.key] * initialBalance,
  }))

  const largest = rows.reduce((a, b) => (b.weight > a.weight ? b : a))
  const smallest = rows.reduce((a, b) => (b.weight < a.weight ? b : a))
  const summary = rows.map((r) => `${r.label} ${formatPercent(r.weight)}`).join(', ')

  return (
    <section className="card" aria-labelledby="allocation-title">
      <h2 id="allocation-title">Recommended allocation</h2>
      <p className="card__sub">Portfolio mix at the end of the simulation.</p>

      <div className="allocation">
        <div className="allocation__chart" role="img" aria-label={`Allocation donut chart: ${summary}`}>
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={rows}
                dataKey="weight"
                nameKey="label"
                innerRadius="62%"
                outerRadius="92%"
                paddingAngle={2}
                stroke="none"
                isAnimationActive={false}
              >
                {rows.map((row) => (
                  <Cell key={row.key} fill={row.color} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => formatPercent(value)} />
            </PieChart>
          </ResponsiveContainer>
          <div className="allocation__center" aria-hidden="true">
            <strong>{formatPercent(largest.weight, 1)}</strong>
            <span>{largest.label}</span>
          </div>
        </div>

        <ul className="breakdown">
          {rows.map((row) => (
            <li key={row.key} className="breakdown__item">
              <span className="swatch" style={{ background: row.color }} aria-hidden="true" />
              <div className="breakdown__main">
                <div className="breakdown__head">
                  <span className="breakdown__name">{row.label}</span>
                  <span className="breakdown__pct">{formatPercent(row.weight)}</span>
                </div>
                <div className="breakdown__bar" aria-hidden="true">
                  <span style={{ width: `${row.weight * 100}%`, background: row.color }} />
                </div>
                <div className="breakdown__meta">
                  {formatCurrency(row.amount)} of your investment · {row.blurb}
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>

      <p className="explain">
        <strong>What this means:</strong> the model put the most weight on {largest.label}{' '}
        ({formatPercent(largest.weight)}) and the least on {smallest.label}{' '}
        ({formatPercent(smallest.weight)}). It re-balances every day during the simulation, so these
        are the weights it ended with, not a fixed split held throughout.
      </p>
    </section>
  )
}