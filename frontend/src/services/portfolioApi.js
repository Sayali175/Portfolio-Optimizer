const API_BASE = 'http://127.0.0.1:8000'

async function parseResponse(response) {
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    const detail = data?.detail
    const message = Array.isArray(detail)
      ? detail.map(item => `${item.loc?.join('.') || 'Input'}: ${item.msg}`).join('; ')
      : typeof detail === 'string' ? detail : `Request failed (${response.status})`
    throw new Error(message)
  }
  return data
}

export async function uploadPortfolio(file) {
  const form = new FormData()
  form.append('file', file)
  return parseResponse(await fetch(`${API_BASE}/portfolio/upload`, { method: 'POST', body: form }))
}

export async function analyzePortfolio(payload) {
  return parseResponse(await fetch(`${API_BASE}/portfolio/analyze`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }))
}

export async function optimizePortfolio(payload) {
  return parseResponse(await fetch(`${API_BASE}/portfolio/optimize`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }))
}
