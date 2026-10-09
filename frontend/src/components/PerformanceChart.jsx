import { useMemo } from 'react'
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { formatCompactCurrency, formatCurrency, formatNumber } from '../utils/format'

export default function PerformanceChart({ values, initialBalance }) {
  const data = useMemo(() => values.map((value, day) => ({ day, value })), [values])

  return (
    <section className="card" aria-labelledby="performance-title">
      <h2 id="performance-title">Portfolio performance</h2>
      <p className="card__sub">Portfolio value over the simulated period.</p>

      <div
        className="performance__chart"
        role="img"
        aria-label={`Line chart of portfolio value over ${formatNumber(values.length - 1)} simulation days, from ${formatCurrency(values[0])} to ${formatCurrency(values[values.length - 1])}`}
      >
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
            <CartesianGrid stroke="#e2e8f0" vertical={false} />
            <XAxis
              dataKey="day"
              type="number"
              domain={[0, 'dataMax']}
              tick={{ fill: '#64748b', fontSize: 12 }}
              tickLine={false}
              axisLine={{ stroke: '#cbd5e1' }}
              tickFormatter={formatNumber}
              label={{ value: 'Simulation day', position: 'insideBottom', offset: -4, fill: '#64748b', fontSize: 12 }}
              height={44}
            />
            <YAxis
              domain={['auto', 'auto']}
              tick={{ fill: '#64748b', fontSize: 12 }}
              tickLine={false}
              axisLine={false}
              tickFormatter={formatCompactCurrency}
              width={64}
            />
            <Tooltip
              formatter={(value) => [formatCurrency(value), 'Portfolio value']}
              labelFormatter={(day) => `Day ${formatNumber(day)}`}
            />
            <ReferenceLine
              y={initialBalance}
              stroke="#94a3b8"
              strokeDasharray="4 4"
              label={{ value: 'Initial investment', position: 'insideTopLeft', fill: '#64748b', fontSize: 12 }}
            />
            <Line
              type="monotone"
              dataKey="value"
              stroke="#2457d6"
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  )
}