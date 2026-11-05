import { useState } from 'react'
import {
  Plus,
  Trash2,
  Upload,
  FileSpreadsheet,
  Wallet,
} from 'lucide-react'

import {
  optimizePortfolio,
  uploadPortfolio,
} from '../services/portfolioApi'
import PortfolioInsightsDashboard from './PortfolioInsightsDashboard'

const ASSET_CLASSES = [
  'equity',
  'debt',
  'hybrid',
  'liquid',
]

const STARTER_HOLDINGS = [
  {
    name: 'Nifty 50 Index Fund',
    asset_class: 'equity',
    current_value: 40000,
  },
  {
    name: 'Debt Mutual Fund',
    asset_class: 'debt',
    current_value: 30000,
  },
  {
    name: 'Hybrid Mutual Fund',
    asset_class: 'hybrid',
    current_value: 20000,
  },
  {
    name: 'Liquid Fund',
    asset_class: 'liquid',
    current_value: 10000,
  },
]

const currency = value =>
  new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 2,
  }).format(value)

const inputStyle = {
  width: '100%',
  padding: '11px 12px',
  borderRadius: '10px',
  border: '1px solid #cbd5e1',
  background: '#fff',
  color: '#0f172a',
  fontSize: '14px',
}

const labelStyle = {
  display: 'block',
  marginBottom: '7px',
  color: '#334155',
  fontSize: '13px',
  fontWeight: 600,
}

const cardStyle = {
  background: '#fff',
  border: '1px solid #e2e8f0',
  borderRadius: '12px',
  padding: '22px',
}

export default function PortfolioOnboarding() {
const [holdings, setHoldings] = useState([])

  const [risk, setRisk] = useState('moderate')
  const [horizon, setHorizon] = useState(3)
  const [goalAmount, setGoalAmount] = useState(200000)
  const [monthlySip, setMonthlySip] = useState(2000)

  const [uploading, setUploading] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [result, setResult] = useState(null)

  const total = holdings.reduce(
    (sum, holding) =>
      sum + (Number(holding.current_value) || 0),
    0
  )

  const updateHolding = (index, field, value) => {
    setHoldings(previous =>
      previous.map((holding, i) =>
        i === index
          ? { ...holding, [field]: value }
          : holding
      )
    )

    setResult(null)
    setMessage('')
  }

  const addHolding = () => {
    setHoldings(previous => [
      ...previous,
      {
        name: '',
        asset_class: 'equity',
        current_value: '',
      },
    ])

    setResult(null)
  }

  const removeHolding = index => {
    setHoldings(previous =>
      previous.filter((_, i) => i !== index)
    )

    setResult(null)
  }

  const handleFileUpload = async event => {
    const file = event.target.files?.[0]
    if (!file) return

    setError('')
    setMessage('')
    setResult(null)

    const extension = file.name.split('.').pop()?.toLowerCase()

    if (!['csv', 'xlsx'].includes(extension)) {
      setError('Please upload a CSV or XLSX file.')
      event.target.value = ''
      return
    }

    setUploading(true)

    try {
      const data = await uploadPortfolio(file)

      setHoldings(data.holdings)
      setMessage(
        `${data.holdings_count} holdings imported successfully from ${file.name}.`
      )
    } catch (err) {
      setError(err.message || 'Unable to upload portfolio.')
    } finally {
      setUploading(false)
      event.target.value = ''
    }
  }

  const handleAnalyze = async event => {
    event.preventDefault()

    setError('')
    setMessage('')
    setResult(null)

    if (holdings.length === 0) {
      setError('Add at least one holding.')
      return
    }

    if (
      holdings.some(
        holding =>
          !holding.name.trim() ||
          holding.current_value === '' ||
          !Number.isFinite(Number(holding.current_value)) ||
          Number(holding.current_value) < 0
      )
    ) {
      setError('Enter a valid name and amount for every holding.')
      return
    }

    if (total <= 0) {
      setError('Portfolio value must be greater than zero.')
      return
    }

    if (!Number.isFinite(Number(goalAmount)) || Number(goalAmount) <= 0 || !Number.isFinite(Number(monthlySip)) || Number(monthlySip) < 0) {
      setError('Enter a positive target amount and a non-negative monthly SIP.')
      return
    }

    setAnalyzing(true)

    try {
      const payload = {
        goal_amount: Number(goalAmount),
        monthly_sip: Number(monthlySip),
        risk_tolerance: risk,
        investment_horizon_years: Number(horizon),
        holdings: holdings.map(holding => ({
          name: holding.name.trim(),
          asset_class: holding.asset_class,
          current_value: Number(holding.current_value),
        })),
      }

      const data = await optimizePortfolio(payload)
      setResult(data)
    } catch (err) {
      setError(err.message || 'Unable to analyze portfolio.')
    } finally {
      setAnalyzing(false)
    }
  }

  const downloadTemplate = () => {
    const rows = [
      ['name', 'asset_class', 'current_value'],
      ...STARTER_HOLDINGS.map(item => [
        item.name,
        item.asset_class,
        item.current_value,
      ]),
    ]

    const csv = rows
      .map(row => row.join(','))
      .join('\r\n')

    const blob = new Blob([csv], {
      type: 'text/csv;charset=utf-8',
    })

    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')

    link.href = url
    link.download = 'portfolio_holdings_template.csv'
    link.click()

    URL.revokeObjectURL(url)
  }

  return (
    <section
      className="container portfolio-onboarding"
      style={{ paddingTop: '0px', paddingBottom: '28px' }}
    >
      <div className="portfolio-onboarding__intro" style={{ marginBottom: '24px' }}>
        <h1
          style={{
            fontSize: 'clamp(26px, 4vw, 36px)',
            fontWeight: 800,
            color: '#0f172a',
          }}
        >
          Your Investment Portfolio
        </h1>

        <p style={{ color: '#64748b', marginTop: '8px' }}>
          Add your investments manually or import them from a spreadsheet.
        </p>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 320px), 1fr))',
          gap: '20px',
          marginBottom: '24px',
        }}
      >
        <div className="portfolio-panel" style={cardStyle}>
          <h2 style={{ fontSize: '18px', fontWeight: 700 }}>
            <Wallet size={20} style={{ display: 'inline', marginRight: 8 }} />
            Portfolio summary
          </h2>

          <p style={{ color: '#64748b', marginTop: 12 }}>
            Current portfolio value
          </p>

          <h3
            style={{
              fontSize: '30px',
              fontWeight: 800,
              marginTop: 4,
              color: '#0f172a',
            }}
          >
            {currency(total)}
          </h3>

          <p style={{ color: '#64748b', marginTop: 10 }}>
            {holdings.length} investments
          </p>
        </div>

        <div className="portfolio-panel" style={cardStyle}>
          <h2 style={{ fontSize: '18px', fontWeight: 700 }}>
            <FileSpreadsheet
              size={20}
              style={{ display: 'inline', marginRight: 8 }}
            />
            Import investments
          </h2>

          <p
            style={{
              color: '#64748b',
              fontSize: 14,
              margin: '12px 0',
            }}
          >
            Upload a CSV or Excel file with your holdings.
          </p>

          <label
            style={{
              ...inputStyle,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 8,
              cursor: uploading ? 'wait' : 'pointer',
              background: '#eff6ff',
              color: '#1d4ed8',
              fontWeight: 600,
            }}
          >
            <Upload size={17} />
            {uploading ? 'Uploading...' : 'Choose CSV / Excel'}
            <input
              type="file"
              accept=".csv,.xlsx"
              disabled={uploading}
              onChange={handleFileUpload}
              style={{ display: 'none' }}
            />
          </label>

          <button
            type="button"
            onClick={downloadTemplate}
            style={{
              marginTop: 12,
              color: '#2563eb',
              fontSize: 13,
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Download sample CSV template
          </button>
        </div>
      </div>

      {error && (
        <div
          role="alert"
          style={{
            padding: 14,
            background: '#fef2f2',
            color: '#b91c1c',
            borderRadius: 10,
            marginBottom: 16,
          }}
        >
          {error}
        </div>
      )}

      {message && (
        <div
          role="status"
          style={{
            padding: 14,
            background: '#f0fdf4',
            color: '#166534',
            borderRadius: 10,
            marginBottom: 16,
          }}
        >
          {message}
        </div>
      )}

      <form onSubmit={handleAnalyze}>
        <div className="portfolio-panel" style={{ ...cardStyle, marginBottom: 24 }}>
          <h2
            style={{
              fontSize: 20,
              fontWeight: 700,
              marginBottom: 20,
            }}
          >
            Investment preferences
          </h2>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns:
                'repeat(auto-fit, minmax(min(100%, 200px), 1fr))',
              gap: 16,
            }}
          >
            <div>
              <label style={labelStyle}>Risk tolerance</label>
              <select
                style={inputStyle}
                value={risk}
                onChange={e => {
                  setRisk(e.target.value)
                  setResult(null)
                }}
              >
                <option value="conservative">Conservative</option>
                <option value="moderate">Moderate</option>
                <option value="aggressive">Aggressive</option>
              </select>
            </div>

            <div>
              <label style={labelStyle}>Investment horizon (years)</label>
              <input
                style={inputStyle}
                type="number"
                min="1"
                max="50"
                required
                value={horizon}
                onChange={e => {
                  setHorizon(e.target.value)
                  setResult(null)
                }}
              />
            </div>
            <div>
              <label style={labelStyle}>Financial target (₹)</label>
              <input style={inputStyle} type="number" min="1" step="0.01" required value={goalAmount} onChange={e => { setGoalAmount(e.target.value); setResult(null) }} />
            </div>
            <div>
              <label style={labelStyle}>Monthly SIP (₹)</label>
              <input style={inputStyle} type="number" min="0" step="0.01" required value={monthlySip} onChange={e => { setMonthlySip(e.target.value); setResult(null) }} />
            </div>
          </div>
        </div>

        <div className="portfolio-panel" style={cardStyle}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              gap: 12,
              flexWrap: 'wrap',
              marginBottom: 20,
            }}
          >
            <h2 style={{ fontSize: 20, fontWeight: 700 }}>
              Current holdings
            </h2>

            <button
              type="button"
              onClick={addHolding}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                color: '#2563eb',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              <Plus size={18} />
              Add investment
            </button>
          </div>

          <div style={{ display: 'grid', gap: 16 }}>
            {holdings.map((holding, index) => (
              <div
                key={index}
                style={{
                  padding: 16,
                  background: '#f8fafc',
                  border: '1px solid #e2e8f0',
                  borderRadius: 12,
                }}
              >
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns:
                      'repeat(auto-fit, minmax(min(100%, 160px), 1fr))',
                    gap: 12,
                    alignItems: 'end',
                  }}
                >
                  <div>
                    <label style={labelStyle}>Investment name</label>
                    <input
                      style={inputStyle}
                      value={holding.name}
                      required
                      onChange={e =>
                        updateHolding(index, 'name', e.target.value)
                      }
                      placeholder="Fund or stock name"
                    />
                  </div>

                  <div>
                    <label style={labelStyle}>Asset class</label>
                    <select
                      style={inputStyle}
                      value={holding.asset_class}
                      onChange={e =>
                        updateHolding(
                          index,
                          'asset_class',
                          e.target.value
                        )
                      }
                    >
                      {ASSET_CLASSES.map(asset => (
                        <option key={asset} value={asset}>
                          {asset.charAt(0).toUpperCase() + asset.slice(1)}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label style={labelStyle}>Current value (₹)</label>
                    <input
                      style={inputStyle}
                      type="number"
                      min="0"
                      step="0.01"
                      required
                      value={holding.current_value}
                      onChange={e =>
                        updateHolding(
                          index,
                          'current_value',
                          e.target.value
                        )
                      }
                    />
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => removeHolding(index)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                    marginTop: 12,
                    color: '#dc2626',
                    fontSize: 13,
                    cursor: 'pointer',
                  }}
                >
                  <Trash2 size={15} />
                  Remove
                </button>
              </div>
            ))}
          </div>

          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              marginTop: 24,
              paddingTop: 16,
              borderTop: '1px solid #e2e8f0',
              fontWeight: 700,
              color: '#0f172a',
            }}
          >
            <span>Total portfolio value</span>
            <span>{currency(total)}</span>
          </div>

          <button
            type="submit"
            disabled={analyzing || uploading}
            style={{
              marginTop: 24,
              width: '100%',
              padding: 14,
              borderRadius: 10,
              background: '#2563eb',
              color: '#fff',
              fontWeight: 700,
              cursor: 'pointer',
              opacity: analyzing || uploading ? 0.6 : 1,
            }}
          >
            {analyzing ? 'Running PPO optimization...' : 'Optimize My Portfolio'}
          </button>
        </div>
      </form>

      {result && <PortfolioInsightsDashboard data={result} />}
    </section>
  )
}

