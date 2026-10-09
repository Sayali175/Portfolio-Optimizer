export default function HeroSection() {
  return (
    <div className="hero__text">
      <h1>AI-powered portfolio optimization</h1>
      <p className="hero__lead">
        Build a portfolio based on your investment amount and risk profile.
      </p>
      <p>
        A reinforcement learning agent (PPO) was trained on historical mutual fund and NIFTY 50
        data. It replays the market day by day and decides how to split your money across equity,
        debt, hybrid and liquid funds.
      </p>
      <p className="hero__note">
        Set your amount and risk level, then run the simulation to see the allocation and how it
        would have performed.
      </p>
    </div>
  )
}