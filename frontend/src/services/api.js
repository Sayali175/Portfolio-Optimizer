// All communication with the FastAPI backend lives in this file.

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'
const REQUEST_TIMEOUT_MS = 180000 // the simulation can take a while

const REQUIRED_WEIGHTS = ['equity', 'debt', 'hybrid', 'liquid']
const REQUIRED_NUMBERS = [
  'risk_profile',
  'initial_balance',
  'final_portfolio_value',
  'total_return',
  'sharpe_ratio',
  'max_drawdown',
  'steps',
]

// Turns FastAPI's 422 validation errors into readable text.
function describeValidationError(detail) {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        const field = Array.isArray(item.loc) ? item.loc.slice(1).join('.') : ''
        return field ? `${field}: ${item.msg}` : item.msg
      })
      .join('; ')
  }
  return 'The request was rejected by the server.'
}

// Makes sure the response has everything the UI needs, so the UI never crashes.
function validateResponse(data) {
  const malformed = new Error('The server returned an unexpected response. Please try again.')
  if (!data || typeof data !== 'object') throw malformed

  for (const key of REQUIRED_NUMBERS) {
    if (!Number.isFinite(data[key])) throw malformed
  }
  if (!data.target_weights || typeof data.target_weights !== 'object') throw malformed
  for (const key of REQUIRED_WEIGHTS) {
    if (!Number.isFinite(data.target_weights[key])) throw malformed
  }
  if (!Array.isArray(data.portfolio_values) || data.portfolio_values.length < 2) throw malformed

  return data
}

export async function simulatePortfolio(riskProfile, initialBalance) {
  let response
  try {
    response = await fetch(`${API_BASE_URL}/simulate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        risk_profile: riskProfile,
        initial_balance: initialBalance,
      }),
      signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    })
  } catch (error) {
    if (error?.name === 'TimeoutError') {
      throw new Error('The simulation took too long to respond. Please try again.')
    }
    throw new Error(
      'Unable to connect to the portfolio optimization engine. Make sure the FastAPI backend is running on port 8000 and allows requests from this page (CORS).',
    )
  }

  if (!response.ok) {
    if (response.status === 422) {
      const body = await response.json().catch(() => null)
      throw new Error(describeValidationError(body?.detail))
    }
    throw new Error(
      `The optimization engine returned an error (HTTP ${response.status}). Check the backend terminal for details.`,
    )
  }

  let data
  try {
    data = await response.json()
  } catch {
    throw new Error('The server returned an unexpected response. Please try again.')
  }
  return validateResponse(data)
}