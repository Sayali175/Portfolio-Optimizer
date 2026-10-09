import { CircleAlert } from 'lucide-react'

export default function ErrorBanner({ message }) {
  return (
    <div className="error-banner" role="alert">
      <CircleAlert size={20} aria-hidden="true" />
      <div>
        <strong>Simulation failed</strong>
        <p>{message}</p>
      </div>
    </div>
  )
}