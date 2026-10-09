import { useEffect, useState } from 'react'
import { Loader2 } from 'lucide-react'

const STEPS = [
  'Analyzing market data…',
  'Running portfolio simulation…',
  'Generating optimized allocation…',
]

export default function LoadingPanel() {
  const [index, setIndex] = useState(0)

  // Only rotates the wording while waiting. It does not claim any real progress.
  useEffect(() => {
    const timer = setInterval(() => setIndex((i) => (i + 1) % STEPS.length), 2500)
    return () => clearInterval(timer)
  }, [])

  return (
    <section className="card loading" role="status" aria-live="polite">
      <Loader2 className="spin loading__icon" size={32} aria-hidden="true" />
      <h2>Optimizing your portfolio…</h2>
      <p>{STEPS[index]}</p>
      <ul className="loading__list">
        <li>Analyzing historical market behavior</li>
        <li>Running PPO simulation</li>
        <li>Calculating performance metrics</li>
      </ul>
    </section>
  )
}