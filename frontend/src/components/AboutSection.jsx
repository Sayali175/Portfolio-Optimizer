export default function AboutSection() {
  return (
    <section id="about" className="about" aria-labelledby="about-title">
      <h2 id="about-title">About this project</h2>
      <p>
        Portfolio Optimizer is an academic project. A Proximal Policy Optimization (PPO) agent,
        built with Stable-Baselines3, learns how to spread money across four fund categories using
        daily returns, volatility and NIFTY 50 indicators. This page sends your inputs to a FastAPI
        service that runs the trained model over historical data and returns the results shown
        above.
      </p>
    </section>
  )
}
