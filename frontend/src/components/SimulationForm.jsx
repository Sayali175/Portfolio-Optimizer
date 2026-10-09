import { useState } from 'react'
import { Loader2 } from 'lucide-react'
import { formatCurrency, formatNumber, getRiskLabel } from '../utils/format'

const MAX_AMOUNT = 100000000000 // ₹10,000 crore, just a sanity limit

export default function SimulationForm({ onSubmit, loading }) {
  const [amount, setAmount] = useState('100000') // digits only
  const [risk, setRisk] = useState(0.5)
  const [errors, setErrors] = useState({})

  const amountNumber = Number(amount)

  function handleAmountChange(event) {
    // keep digits only, so "₹1,00,000" typed or pasted still works
    setAmount(event.target.value.replace(/\D/g, '').slice(0, 12))
  }

  function handleSubmit(event) {
    event.preventDefault()
    const nextErrors = {}

    if (!amount || !(amountNumber > 0)) {
      nextErrors.amount = 'Enter an investment amount greater than ₹0.'
    } else if (amountNumber > MAX_AMOUNT) {
      nextErrors.amount = `Enter an amount up to ${formatCurrency(MAX_AMOUNT)}.`
    }
    if (!Number.isFinite(risk) || risk < 0 || risk > 1) {
      nextErrors.risk = 'Risk profile must be between 0 and 1.'
    }

    setErrors(nextErrors)
    if (Object.keys(nextErrors).length === 0) {
      onSubmit(risk, amountNumber)
    }
  }

  return (
    <form className="card form" onSubmit={handleSubmit} noValidate>
      <h2>Simulation inputs</h2>

      <div className="field">
        <label htmlFor="amount">Initial investment</label>
        <div className={`input-wrap ${errors.amount ? 'is-invalid' : ''}`}>
          <span className="input-prefix" aria-hidden="true">₹</span>
          <input
            id="amount"
            type="text"
            inputMode="numeric"
            autoComplete="off"
            value={amount ? formatNumber(amountNumber) : ''}
            onChange={handleAmountChange}
            aria-invalid={Boolean(errors.amount)}
            aria-describedby={errors.amount ? 'amount-error' : undefined}
            disabled={loading}
          />
        </div>
        {errors.amount && (
          <p id="amount-error" className="field-error" role="alert">{errors.amount}</p>
        )}
      </div>

      <div className="field">
        <div className="field__row">
          <label htmlFor="risk">Risk profile</label>
          <span className="risk-value" aria-live="polite">
            {risk.toFixed(2)} · {getRiskLabel(risk)}
          </span>
        </div>
        <input
          id="risk"
          type="range"
          min="0"
          max="1"
          step="0.05"
          value={risk}
          onChange={(e) => setRisk(Number(e.target.value))}
          aria-valuetext={`${risk.toFixed(2)}, ${getRiskLabel(risk)}`}
          disabled={loading}
        />
        <div className="range-scale" aria-hidden="true">
          <span>Conservative</span>
          <span>Low</span>
          <span>Moderate</span>
          <span>Growth</span>
          <span>Aggressive</span>
        </div>
        {errors.risk && <p className="field-error" role="alert">{errors.risk}</p>}
        <p className="field-help">
          The label is only a guide. The model does not guarantee any outcome for a given setting.
        </p>
      </div>

      <button className="btn" type="submit" disabled={loading}>
        {loading ? (
          <>
            <Loader2 className="spin" size={18} aria-hidden="true" /> Optimizing…
          </>
        ) : (
          'Optimize Portfolio'
        )}
      </button>
    </form>
  )
}