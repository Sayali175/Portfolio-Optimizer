// The four asset classes returned by the backend in `target_weights`.
// The keys must match the backend response exactly.
export const ASSETS = [
  { key: 'equity', label: 'Equity', color: '#2457d6', blurb: 'Stocks and equity funds. Higher growth potential, larger swings.' },
  { key: 'debt', label: 'Debt', color: '#1f8a8a', blurb: 'Bonds and debt funds. Steadier returns, lower volatility.' },
  { key: 'hybrid', label: 'Hybrid', color: '#c9921f', blurb: 'A built-in mix of equity and debt in a single fund.' },
  { key: 'liquid', label: 'Liquid', color: '#7b8aa3', blurb: 'Short-term, easy-to-withdraw funds. Lowest risk, lowest return.' },
]