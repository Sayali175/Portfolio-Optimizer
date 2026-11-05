import { useState } from 'react'

const ASSETS = ['equity', 'debt', 'hybrid', 'liquid']
const NAMES = { equity: 'Equity', debt: 'Debt', hybrid: 'Hybrid', liquid: 'Liquid' }
const COLORS = { equity: '#2563eb', debt: '#8b5cf6', hybrid: '#0d9488', liquid: '#f59e0b' }
const RISK_NAMES = { conservative: 'Conservative', moderate: 'Moderate', aggressive: 'Aggressive' }
const money = n => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(Number(n) || 0)
const pct = n => `${((Number(n) || 0) * 100).toFixed(1)}%`
const pp = n => `${Number(n || 0) > 0 ? '+' : ''}${Number(n || 0).toFixed(2)} pp`
const panel = { background: '#fff', border: '1px solid #e2e8f0', borderRadius: 16, padding: 22 }
const small = { color: '#64748b', fontSize: 13, lineHeight: 1.6 }
const title = { fontSize: 19, fontWeight: 750, color: '#0f172a', marginBottom: 14 }
const cell = { padding: '12px 8px', borderBottom: '1px solid #f1f5f9' }
const headerCell = { padding: '10px 8px', borderBottom: '1px solid #e2e8f0', color: '#334155', fontSize: 13 }

function Explanation({ value, mode }) {
  if (!value) return null
  return <p style={{ ...small, marginTop: 10 }}>{value[mode] || 'Explanation unavailable.'}</p>
}

function WeightBar({ value, color }) {
  return <div style={{ height: 9, borderRadius: 9, background: '#e2e8f0', overflow: 'hidden' }}>
    <div style={{ width: `${Math.max(0, Math.min(100, Number(value || 0) * 100))}%`, background: color, height: '100%', borderRadius: 9 }} />
  </div>
}

function AllocationMix({ weights }) {
  return <div style={{ display: 'grid', gap: 11 }}>
    {ASSETS.map(asset => <div key={asset}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, marginBottom: 5 }}>
        <span style={{ ...small, color: '#334155' }}>{NAMES[asset]}</span>
        <strong style={{ fontSize: 13 }}>{pct(weights?.[asset])}</strong>
      </div>
      <WeightBar value={weights?.[asset]} color={COLORS[asset]} />
    </div>)}
  </div>
}

function SensitivitySection({ sensitivity, mode, riskTolerance }) {
  const [selectedRisk, setSelectedRisk] = useState('moderate')
  if (!sensitivity) return null

  const baseline = sensitivity.baseline_weights || {}
  const riskTests = sensitivity.risk_profile_tests || {}
  const riskDifferences = sensitivity.risk_test_differences_from_baseline_percentage_points || {}
  const ranges = sensitivity.risk_response_range_percentage_points || {}
  const weightTests = sensitivity.current_weight_tests || {}
  const weightDetails = sensitivity.current_weight_test_details || {}
  const riskKeys = ['conservative', 'moderate', 'aggressive'].filter(key => riskTests[key])
  const activeRisk = riskTests[selectedRisk] ? selectedRisk : riskKeys[0]
  const selectedWeights = riskTests[activeRisk] || baseline
  const riskRows = ASSETS.map(asset => ({ asset, range: Number(ranges[asset] || 0) }))
  const mostSensitive = riskRows.reduce((best, row) => row.range > best.range ? row : best, riskRows[0])
  const conservativeEquity = Number(riskTests.conservative?.equity)
  const aggressiveEquity = Number(riskTests.aggressive?.equity)
  const conservativeLiquid = Number(riskTests.conservative?.liquid)
  const aggressiveLiquid = Number(riskTests.aggressive?.liquid)
  const counterintuitive = [conservativeEquity, aggressiveEquity, conservativeLiquid, aggressiveLiquid].every(Number.isFinite)
    && aggressiveEquity < conservativeEquity - 0.0001
    && aggressiveLiquid > conservativeLiquid + 0.0001

  return <div style={panel}>
    <h3 style={title}>6. How sensitive is the AI recommendation?</h3>
    <p style={small}>We ran the same PPO model again with different risk settings while keeping the market snapshot and your original holdings fixed. This tests model behavior; it does not prove which portfolio is best.</p>

    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(175px, 1fr))', gap: 12, marginTop: 18 }}>
      <div style={{ background: '#eff6ff', borderRadius: 12, padding: 15 }}>
        <div style={small}>Most sensitive category</div>
        <strong style={{ fontSize: 19, color: '#1d4ed8' }}>{NAMES[mostSensitive.asset]}</strong>
        <div style={small}>Across risk settings</div>
      </div>
      <div style={{ background: '#f8fafc', borderRadius: 12, padding: 15 }}>
        <div style={small}>Largest allocation range</div>
        <strong style={{ fontSize: 19 }}>{mostSensitive.range.toFixed(2)} pp</strong>
        <div style={small}>Percentage points, not percent return</div>
      </div>
      <div style={{ background: '#f8fafc', borderRadius: 12, padding: 15 }}>
        <div style={small}>Observation features</div>
        <strong style={{ fontSize: 19 }}>{sensitivity.observation_feature_count ?? 18}</strong>
        <div style={small}>Used by the PPO model</div>
      </div>
    </div>

    <h4 style={{ margin: '24px 0 10px', fontSize: 16, color: '#0f172a' }}>Risk profile comparison</h4>
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', minWidth: 490, borderCollapse: 'collapse', textAlign: 'left' }}>
        <thead><tr>
          <th style={headerCell}>Asset</th>
          {riskKeys.map(key => <th key={key} style={headerCell}>{RISK_NAMES[key]}</th>)}
          <th style={headerCell}>Range</th>
        </tr></thead>
        <tbody>{ASSETS.map(asset => <tr key={asset}>
          <td style={cell}><strong>{NAMES[asset]}</strong></td>
          {riskKeys.map(key => <td key={key} style={cell}>{pct(riskTests[key]?.[asset])}</td>)}
          <td style={cell}>{Number(ranges[asset] || 0).toFixed(2)} pp</td>
        </tr>)}</tbody>
      </table>
    </div>

    <div style={{ marginTop: 20 }}>
      <p style={{ ...small, marginBottom: 10 }}>Select a risk setting to inspect the allocation returned by the model:</p>
      <div role="group" aria-label="Inspect risk sensitivity" style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
        {riskKeys.map(key => <button key={key} type="button" aria-pressed={activeRisk === key} onClick={() => setSelectedRisk(key)} style={{ borderRadius: 9, padding: '9px 13px', cursor: 'pointer', fontWeight: 650, border: '1px solid #bfdbfe', background: activeRisk === key ? '#2563eb' : '#fff', color: activeRisk === key ? '#fff' : '#334155' }}>{RISK_NAMES[key]}</button>)}
      </div>
      {activeRisk && <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))', gap: 22, marginTop: 16 }}>
        <div><strong style={{ display: 'block', marginBottom: 14 }}>Original recommendation</strong><AllocationMix weights={baseline} /></div>
        <div><strong style={{ display: 'block', marginBottom: 14 }}>{RISK_NAMES[activeRisk]} setting</strong><AllocationMix weights={selectedWeights} /></div>
      </div>}
      {activeRisk && <p style={{ ...small, marginTop: 14 }}>
        Change from the original recommendation: {ASSETS.map(asset => `${NAMES[asset]} ${pp(riskDifferences[activeRisk]?.[asset] ?? (Number(selectedWeights?.[asset] || 0) - Number(baseline[asset] || 0)) * 100)}`).join(' · ')}.
      </p>}
    </div>

    {counterintuitive && <div role="note" style={{ marginTop: 20, padding: 15, background: '#fffbeb', border: '1px solid #fde68a', borderRadius: 12 }}>
      <strong style={{ color: '#92400e' }}>Risk behavior needs validation</strong>
      <p style={{ ...small, marginTop: 6, color: '#92400e' }}>In this test, the aggressive setting reduces Equity and increases Liquid compared with the conservative setting. This may indicate the PPO model is not responding to risk preferences as intended. Check the training reward and risk-profile handling before using these outputs as investment recommendations.</p>
    </div>}

    <h4 style={{ margin: '26px 0 10px', fontSize: 16, color: '#0f172a' }}>What happens if your starting holdings change?</h4>
    <p style={small}>These tests change the input portfolio by moving 5 percentage points between Equity and Liquid, while holding the other inputs fixed. They do not execute any trades.</p>
    {Object.keys(weightTests).length > 0 ? <div style={{ overflowX: 'auto', marginTop: 12 }}>
      <table style={{ width: '100%', minWidth: 540, borderCollapse: 'collapse', textAlign: 'left' }}>
        <thead><tr><th style={headerCell}>AI output</th><th style={headerCell}>Baseline</th>
          {Object.keys(weightTests).map(key => <th key={key} style={headerCell}>{key === 'more_equity' ? '+5 pp Equity input' : key === 'less_equity' ? '-5 pp Equity input' : key.replaceAll('_', ' ')}</th>)}
        </tr></thead>
        <tbody>{ASSETS.map(asset => <tr key={asset}>
          <td style={cell}><strong>{NAMES[asset]}</strong></td>
          <td style={cell}>{pct(baseline[asset])}</td>
          {Object.keys(weightTests).map(key => <td key={key} style={cell}>{pct(weightTests[key]?.[asset])}<div style={{ ...small, fontSize: 11 }}>{pp(weightDetails[key]?.output_difference_from_baseline_percentage_points?.[asset] ?? (Number(weightTests[key]?.[asset] || 0) - Number(baseline[asset] || 0)) * 100)}</div></td>)}
        </tr>)}</tbody>
      </table>
    </div> : <p style={{ ...small, marginTop: 10 }}>No feasible ±5 percentage-point Equity/Liquid input tests were returned for these holdings.</p>}

    <Explanation value={sensitivity.explanation} mode={mode} />
    <p style={{ ...small, marginTop: 12, fontSize: 12 }}>{sensitivity.caveat || 'Sensitivity tests are not causal explanations or predictions of future performance.'}</p>
  </div>
}

export default function PortfolioInsightsDashboard({ data }) {
  const [mode, setMode] = useState('simple')
  if (!data) return null

  const insights = data.insights || {}
  const explanations = data.explanations || {}
  const current = data.current_weights || {}
  const proposed = data.proposed_weights || {}
  const rebalance = insights.rebalancing || {}
  const goal = insights.goal_planning || {}
  const future = insights.future_scenarios || {}
  const targetFuture = insights.target_future_scenarios || {}
  const stress = insights.stress_test || {}
  const stressExplanations = explanations.stress_tests || {}
  const allocationExplanations = Object.fromEntries((explanations.allocations || []).map(item => [item.asset_class, item]))
  const scenarioNames = { equity_crash: 'Stock-market crash', broad_market_downturn: 'Broad market downturn', interest_rate_shock: 'Interest-rate shock' }
  const scenarioKeys = ['downside_p10', 'median_p50', 'upside_p90']
  const scenarioLabels = { downside_p10: 'Weaker outcome (10th percentile)', median_p50: 'Middle outcome (median)', upside_p90: 'Stronger outcome (90th percentile)' }

  return <section aria-label="Personalized portfolio insights" style={{ display: 'grid', gap: 20, marginTop: 28 }}>
    <div style={{ ...panel, borderColor: '#93c5fd', background: '#eff6ff' }}>
      <h2 style={{ ...title, marginBottom: 6 }}>Your personalized portfolio results</h2>
      <p style={small}>PPO V2 · Historical market snapshot: {data.market_data_reference ? new Date(data.market_data_reference).toLocaleDateString('en-IN') : 'Not specified'} · Not live market data</p>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 16 }} role="group" aria-label="Explanation level">
        {[['simple', 'Explain simply'], ['technical', 'Technical explanation']].map(([key, label]) => <button key={key} type="button" aria-pressed={mode === key} onClick={() => setMode(key)} style={{ borderRadius: 9, padding: '10px 15px', fontWeight: 700, cursor: 'pointer', background: mode === key ? '#2563eb' : '#fff', color: mode === key ? '#fff' : '#334155', border: '1px solid #bfdbfe' }}>{label}</button>)}
      </div>
      <Explanation value={explanations.overall} mode={mode} />
    </div>

    <div style={panel}>
      <h3 style={title}>1. Your allocation vs the AI proposal</h3>
      <p style={small}>Compare the percentage of your money assigned to each investment category.</p>
      <div style={{ display: 'grid', gap: 22, marginTop: 18 }}>
        {ASSETS.map(asset => <div key={asset}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8, gap: 10, flexWrap: 'wrap' }}><strong>{NAMES[asset]}</strong><span style={small}>Current {pct(current[asset])} → AI {pct(proposed[asset])}</span></div>
          <div style={{ display: 'grid', gap: 7 }}>
            <div style={{ display: 'grid', gridTemplateColumns: '58px 1fr', alignItems: 'center', gap: 8 }}><span style={small}>Current</span><WeightBar value={current[asset]} color="#94a3b8" /></div>
            <div style={{ display: 'grid', gridTemplateColumns: '58px 1fr', alignItems: 'center', gap: 8 }}><span style={small}>AI</span><WeightBar value={proposed[asset]} color={COLORS[asset]} /></div>
          </div>
          <Explanation value={allocationExplanations[asset]} mode={mode} />
        </div>)}
      </div>
    </div>

    <div style={panel}>
      <h3 style={title}>2. How to rebalance</h3>
      <p style={small}>Illustrative amounts to move between categories to match the proposed allocation.</p>
      <div style={{ overflowX: 'auto', marginTop: 14 }}><table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 430, textAlign: 'left' }}><thead><tr>{['Asset', 'Action', 'Amount', 'Proposed value'].map(x => <th key={x} style={{ padding: '10px 8px', borderBottom: '1px solid #e2e8f0' }}>{x}</th>)}</tr></thead><tbody>
        {ASSETS.map(asset => { const change = rebalance.changes?.[asset]; return <tr key={asset}><td style={{ padding: '12px 8px' }}>{NAMES[asset]}</td><td style={{ padding: '12px 8px', textTransform: 'capitalize' }}>{change?.action || '—'}</td><td style={{ padding: '12px 8px', color: (change?.adjustment || 0) < 0 ? '#b91c1c' : '#047857' }}>{change ? money(Math.abs(change.adjustment)) : '—'}</td><td style={{ padding: '12px 8px' }}>{change ? money(change.target_amount) : '—'}</td></tr> })}
      </tbody></table></div>
      <p style={{ ...small, marginTop: 12 }}>Estimated transaction fees: {money(rebalance.estimated_transaction_fees)}. {rebalance.estimated_tax == null ? (rebalance.tax_note || 'Taxes are not estimated.') : `Estimated taxes: ${money(rebalance.estimated_tax)}.`}</p>
    </div>

    <div style={panel}>
      <h3 style={title}>3. Possible future outcomes</h3>
      <p style={small}>Illustrative Monte Carlo results over {future.horizon_years ?? 'your selected'} years, including the monthly SIP.</p>
      <div style={{ overflowX: 'auto', marginTop: 14 }}><table style={{ width: '100%', minWidth: 440, borderCollapse: 'collapse', textAlign: 'left' }}><thead><tr>{['Scenario', 'Your portfolio', 'AI proposal'].map(x => <th key={x} style={{ padding: '10px 8px', borderBottom: '1px solid #e2e8f0' }}>{x}</th>)}</tr></thead><tbody>
        {scenarioKeys.map(key => <tr key={key}><td style={{ padding: '12px 8px' }}>{scenarioLabels[key]}</td><td style={{ padding: '12px 8px' }}>{money(future[key])}</td><td style={{ padding: '12px 8px' }}>{money(targetFuture[key])}</td></tr>)}
      </tbody></table></div>
      <Explanation value={explanations.growth} mode={mode} />
      <Explanation value={explanations.downside} mode={mode} />
    </div>

    <div style={panel}>
      <h3 style={title}>4. Your investment goal</h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 12 }}>
        {[['Target', goal.target_amount], ['Projected value', goal.projected_value], ['Your monthly SIP', goal.monthly_sip], ['Estimated required SIP', goal.required_monthly_sip]].map(([label, value]) => <div key={label} style={{ background: '#f8fafc', padding: 14, borderRadius: 10 }}><div style={small}>{label}</div><strong style={{ fontSize: 19 }}>{money(value)}</strong></div>)}
      </div>
      <Explanation value={explanations.goal} mode={mode} />
      <p style={small}>Goal projection currently uses your existing allocation, not the AI proposal.</p>
    </div>

    <div style={panel}>
      <h3 style={title}>5. What if markets fall?</h3>
      <p style={small}>Hypothetical shocks, not predictions. Compare what might remain from your current portfolio value.</p>
      {Object.entries(scenarioNames).map(([key, label]) => <div key={key} style={{ padding: '15px 0', borderBottom: '1px solid #e2e8f0' }}><strong>{label}</strong><div style={{ display: 'flex', flexWrap: 'wrap', gap: 18, marginTop: 8 }}><span style={small}>Current: <strong>{money(stress.current?.[key]?.estimated_value)}</strong> ({pct(stress.current?.[key]?.portfolio_change)})</span><span style={small}>AI: <strong>{money(stress.target?.[key]?.estimated_value)}</strong> ({pct(stress.target?.[key]?.portfolio_change)})</span></div><Explanation value={stressExplanations[key]} mode={mode} /></div>)}
    </div>

    <SensitivitySection sensitivity={data.model_sensitivity} mode={mode} riskTolerance={data.risk_tolerance} />

    <div style={{ ...panel, background: '#f8fafc' }}><h3 style={title}>What the model cannot tell you</h3><Explanation value={explanations.model_limitations} mode={mode} /><p style={{ ...small, marginTop: 10 }}>{data.disclaimer || 'This is an experimental educational tool, not investment advice.'}</p></div>
  </section>
}
