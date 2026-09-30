# Mutual Fund Portfolio Optimizer using Reinforcement Learning

An AI-powered system that learns optimal mutual fund allocation strategies using Reinforcement Learning (PPO), and provides personalized, dynamic portfolio recommendations through an interactive web dashboard.

## Overview

Retail investors in India often lack access to intelligent, adaptive portfolio tools. This project uses a Reinforcement Learning agent to allocate funds across Equity, Debt, Hybrid, and Liquid categories based on market conditions and an investor's risk profile, and simulates portfolio performance over time.

## Team

| Name | Role |
|---|---|
| Sayali | Research & literature review, Frontend |
| Rajdeep | RL model development |
| Joel | Backend & Zerodha API integration |

## Tech Stack

- **Language:** Python
- **RL Algorithm:** PPO (Proximal Policy Optimization)
- **RL Library:** Stable-Baselines3
- **Deep Learning Framework:** PyTorch
- **RL Environment:** Gymnasium
- **Backend:** FastAPI
- **Database:** PostgreSQL
- **Frontend:** React
- **Visualization:** Plotly / Matplotlib
- **Market Data:** AMFI NAV data, NSE historical data, Zerodha Kite Connect API (live data)
- **Deployment:** Docker

## Project Structure

```
├── data/               # Raw and processed datasets, data dictionary
├── rl/                 # Gym environment, PPO training, evaluation scripts
│   ├── env.py
│   ├── train.py
│   └── evaluate.py
├── app/
│   ├── backend/        # FastAPI app, API routes, Zerodha integration
│   └── frontend/       # React app, dashboard, charts
├── docs/               # Architecture diagrams, report, interfaces doc
├── requirements.txt
├── docker-compose.yml
└── README.md
```

## Architecture

1. **Data Layer** – AMFI NAV data + NSE market indicators, plus live data via Zerodha Kite Connect
2. **Preprocessing** – Cleaning, normalization, feature engineering (returns, volatility, RSI, MACD)
3. **RL Environment** – State: market conditions + portfolio; Action: allocation weights; Reward: risk-adjusted return
4. **RL Agent** – PPO model trained on historical data
5. **Portfolio Simulator** – Simulates performance and rebalancing over time
6. **Web Interface** – User inputs (risk profile, amount), dashboard, scenario comparison, reports

## Setup Instructions

### Prerequisites
- Python 3.10+
- Node.js 18+ (for the React frontend)
- PostgreSQL installed locally, or Docker
- A Zerodha Kite Connect developer account and API key (for live data)

### 1. Clone the repository
```bash
git clone <repository-url>
cd <repository-folder>
```

### 2. Set up the Python environment
```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment variables
Create a `.env` file in the project root:
```
DATABASE_URL=postgresql://user:password@localhost:5432/portfolio_db
KITE_API_KEY=your_zerodha_api_key
KITE_API_SECRET=your_zerodha_api_secret
```

### 4. Set up the database
```bash
# Using Docker
docker run --name portfolio-db -e POSTGRES_PASSWORD=password -p 5432:5432 -d postgres
```

### 5. Download and prepare data
```bash
python data/download_data.py
python data/preprocess.py
```

### 6. Train the RL model
```bash
python rl/train.py
```

### 7. Run the backend
```bash
cd app/backend
uvicorn main:app --reload
```
API docs available at `http://localhost:8000/docs`

### 8. Run the frontend
```bash
cd app/frontend
npm install
npm start
```
App available at `http://localhost:3000`

### 9. (Optional) Run everything with Docker
```bash
docker-compose up --build
```

## Usage

1. Open the web app and enter your risk appetite (low/medium/high), investment amount, and horizon
2. View the recommended allocation and simulated portfolio performance
3. Compare against baseline strategies (equal-weight, 60/40, buy-and-hold)
4. Download a PDF/CSV/Excel report of the results

## Disclaimer

This project is for academic and research purposes only. Recommendations are based on historical simulations and do not constitute financial advice.

## Future Scope

- Live market API integration (Zerodha Kite Connect)
- SIP (Systematic Investment Plan) strategy support
- Multi-objective optimization (tax, liquidity, risk)
- Mobile application
- AI-based financial advisory chatbot
