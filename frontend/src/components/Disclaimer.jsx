import { TriangleAlert } from 'lucide-react'

export default function Disclaimer() {
  return (
    <aside className="disclaimer" role="note">
      <TriangleAlert size={18} aria-hidden="true" />
      <p>
        Simulation results are based on historical market data and a trained reinforcement learning
        model. They are for educational and demonstration purposes only and do not constitute
        financial advice.
      </p>
    </aside>
  )
}