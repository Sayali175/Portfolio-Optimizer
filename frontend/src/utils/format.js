// Indian-style number formatting helpers (e.g. ₹1,00,000).

const inrCurrency = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 0,
})
const inrNumber = new Intl.NumberFormat('en-IN')
const inrCompact = new Intl.NumberFormat('en-IN', {
  notation: 'compact',
  maximumFractionDigits: 1,
})

export const formatCurrency = (value) => inrCurrency.format(value)
export const formatNumber = (value) => inrNumber.format(value)
export const formatCompactCurrency = (value) => `₹${inrCompact.format(value)}`

// 0.2458 -> "24.58%"
export const formatPercent = (fraction, digits = 2) => `${(fraction * 100).toFixed(digits)}%`

// 0.25 -> "+25.00%", -0.0483 -> "-4.83%"
export function formatSignedPercent(fraction, digits = 2) {
  const sign = fraction > 0 ? '+' : ''
  return `${sign}${(fraction * 100).toFixed(digits)}%`
}

// Friendly label for the risk slider (0 to 1).
export function getRiskLabel(value) {
  if (value < 0.125) return 'Conservative'
  if (value < 0.375) return 'Low'
  if (value < 0.625) return 'Moderate'
  if (value < 0.875) return 'Growth'
  return 'Aggressive'
}