export default function MetricCard({ icon: Icon, label, value, hint, tone = 'neutral' }) {
  return (
    <div className="card metric">
      <div className="metric__label">
        {Icon && <Icon size={16} aria-hidden="true" />}
        <span>{label}</span>
      </div>
      <div className={`metric__value metric__value--${tone}`}>{value}</div>
      {hint && <div className="metric__hint">{hint}</div>}
    </div>
  )
}