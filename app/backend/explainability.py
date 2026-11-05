
import numpy as np

ASSETS = ("equity", "debt", "hybrid", "liquid")

ASSET_NAMES = {
    "equity": "Equity",
    "debt": "Debt",
    "hybrid": "Hybrid",
    "liquid": "Liquid",
}

ASSET_DESCRIPTIONS = {
    "equity": (
        "shares or stock-market investments",
        "stock-market exposure",
    ),
    "debt": (
        "investments that generally earn income from debt instruments",
        "interest-rate and credit exposure",
    ),
    "hybrid": (
        "funds that combine different investment types",
        "mixed-asset exposure",
    ),
    "liquid": (
        "short-term investments designed for liquidity",
        "short-term investment exposure",
    ),
}

RISK_LEVELS = {
    "conservative": 0.1,
    "moderate": 0.5,
    "aggressive": 0.9,
}


# ---------------------------------------------------------
# FORMATTING HELPERS
# ---------------------------------------------------------

def money(value):
    value = float(value)
    sign = "-" if value < 0 else ""
    return f"{sign}₹{abs(value):,.2f}"


def percent(value):
    return f"{float(value) * 100:.2f}%"


def signed_money(value):
    value = float(value)
    sign = "+" if value > 0 else ""
    return f"{sign}{money(value)}"


def signed_percent_points(value):
    return f"{float(value):+.2f} percentage points"


def comparison_text(difference, threshold=0.01):
    if difference > threshold:
        return f"{money(difference)} higher"
    elif difference < -threshold:
        return f"{money(abs(difference))} lower"
    return "almost unchanged"


# ---------------------------------------------------------
# VALIDATION HELPERS
# ---------------------------------------------------------

def validate_weights(weights):
    values = {}

    for asset in ASSETS:
        if asset not in weights:
            raise ValueError(
                f"Missing allocation for {asset}"
            )

        value = float(weights[asset])

        if not np.isfinite(value):
            raise ValueError(
                f"Invalid allocation for {asset}"
            )

        if value < 0 or value > 1:
            raise ValueError(
                f"{asset} weight must be between 0 and 1"
            )

        values[asset] = value

    if not np.isclose(
        sum(values.values()),
        1.0,
        atol=1e-3,
    ):
        raise ValueError(
            "Portfolio weights must sum to 1"
        )

    return values


# ---------------------------------------------------------
# DYNAMIC PORTFOLIO EXPLANATIONS
# ---------------------------------------------------------

def create_explanations(
    current_weights,
    proposed_weights,
    insights,
):
    """
    Generate dynamic financial explanations.

    Uses actual portfolio values, allocation changes,
    illustrative future scenarios, stress tests and
    goal-planning calculations.

    Returns the existing API response structure so
    the React dashboard remains compatible.
    """

    current_weights = validate_weights(
        current_weights
    )

    proposed_weights = validate_weights(
        proposed_weights
    )

    total = float(
        insights["portfolio_value"]
    )

    if not np.isfinite(total) or total <= 0:
        raise ValueError(
            "Portfolio value must be positive"
        )

    allocation_explanations = []

    # -----------------------------------------------------
    # INDIVIDUAL ASSET EXPLANATIONS
    # -----------------------------------------------------

    for asset in ASSETS:

        current = current_weights[asset]
        proposed = proposed_weights[asset]

        difference = proposed - current
        amount = difference * total

        description, exposure = (
            ASSET_DESCRIPTIONS[asset]
        )

        asset_name = ASSET_NAMES[asset]

        if difference > 0.0001:

            direction = "increase"

            simple = (
                f"The AI proposes increasing your "
                f"{asset_name} allocation from "
                f"{percent(current)} to "
                f"{percent(proposed)}. "
                f"This increases your investment in "
                f"{description}. "
                f"You would move approximately "
                f"{money(abs(amount))} into this category."
            )

        elif difference < -0.0001:

            direction = "decrease"

            simple = (
                f"The AI proposes reducing your "
                f"{asset_name} allocation from "
                f"{percent(current)} to "
                f"{percent(proposed)}. "
                f"This reduces your investment in "
                f"{description}. "
                f"You would move approximately "
                f"{money(abs(amount))} out of this category."
            )

        else:

            direction = "hold"

            simple = (
                f"Your {asset_name} allocation remains "
                f"almost unchanged at approximately "
                f"{percent(proposed)}."
            )

        technical = (
            f"{asset_name} allocation changes from "
            f"{percent(current)} to "
            f"{percent(proposed)}, representing "
            f"{signed_percent_points(difference * 100)}. "
            f"The gross capital adjustment is "
            f"{signed_money(amount)}. "
            f"This changes the portfolio's {exposure}. "
            f"The PPO model produces four continuous "
            f"actions which are transformed into "
            f"allocation weights using softmax. "
            f"This describes the allocation change, "
            f"not the model's internal decision process."
        )

        allocation_explanations.append({
            "asset_class": asset,
            "asset_name": asset_name,
            "direction": direction,
            "current_weight": round(
                current, 6
            ),
            "proposed_weight": round(
                proposed, 6
            ),
            "change_percentage_points": round(
                difference * 100, 2
            ),
            "adjustment_amount": round(
                amount, 2
            ),
            "simple": simple,
            "technical": technical,
        })

    # -----------------------------------------------------
    # FUTURE SCENARIO COMPARISON
    # -----------------------------------------------------

    current_scenarios = (
        insights["future_scenarios"]
    )

    proposed_scenarios = (
        insights["target_future_scenarios"]
    )

    current_median = float(
        current_scenarios["median_p50"]
    )

    proposed_median = float(
        proposed_scenarios["median_p50"]
    )

    current_downside = float(
        current_scenarios["downside_p10"]
    )

    proposed_downside = float(
        proposed_scenarios["downside_p10"]
    )

    current_upside = float(
        current_scenarios["upside_p90"]
    )

    proposed_upside = float(
        proposed_scenarios["upside_p90"]
    )

    median_difference = (
        proposed_median - current_median
    )

    downside_difference = (
        proposed_downside - current_downside
    )

    upside_difference = (
        proposed_upside - current_upside
    )

    # -----------------------------------------------------
    # GROWTH EXPLANATION
    # -----------------------------------------------------

    if median_difference > 0.01:

        growth_simple = (
            f"The AI-proposed portfolio has a higher "
            f"middle outcome in our example simulations. "
            f"Its projected middle value is "
            f"{money(proposed_median)}, compared with "
            f"{money(current_median)} for your current "
            f"portfolio. That is "
            f"{money(median_difference)} more under "
            f"these assumptions, not a guaranteed gain."
        )

    elif median_difference < -0.01:

        growth_simple = (
            f"The AI-proposed portfolio has a lower "
            f"middle outcome in our example simulations. "
            f"Its projected middle value is "
            f"{money(proposed_median)}, compared with "
            f"{money(current_median)} for your current "
            f"portfolio. That is "
            f"{money(abs(median_difference))} less "
            f"under these assumptions."
        )

    else:

        growth_simple = (
            "Both portfolios have almost the same "
            "middle outcome in our example simulations."
        )

    growth_explanation = {
        "simple": growth_simple,
        "technical": (
            f"Simulated median terminal value: "
            f"current={money(current_median)}, "
            f"proposed={money(proposed_median)}, "
            f"difference={signed_money(median_difference)}. "
            f"The simulated 90th-percentile value changes "
            f"from {money(current_upside)} to "
            f"{money(proposed_upside)}, a difference of "
            f"{signed_money(upside_difference)}. "
            f"These results depend on illustrative "
            f"Monte Carlo assumptions and are not "
            f"validated forecasts of future returns."
        ),
    }

    # -----------------------------------------------------
    # DOWNSIDE EXPLANATION
    # -----------------------------------------------------

    if downside_difference > 0.01:

        downside_simple = (
            f"In the weaker outcomes we simulated, "
            f"the AI-proposed portfolio retains "
            f"{money(downside_difference)} more than "
            f"your current portfolio. "
            f"This suggests a better downside result "
            f"under these particular assumptions."
        )

    elif downside_difference < -0.01:

        downside_simple = (
            f"In the weaker outcomes we simulated, "
            f"the AI-proposed portfolio retains "
            f"{money(abs(downside_difference))} less "
            f"than your current portfolio. "
            f"This suggests a worse downside result "
            f"under these particular assumptions."
        )

    else:

        downside_simple = (
            "Both portfolios produce nearly identical "
            "weaker-case outcomes in our simulations."
        )

    downside_explanation = {
        "simple": downside_simple,
        "technical": (
            f"10th-percentile terminal value: "
            f"current={money(current_downside)}, "
            f"proposed={money(proposed_downside)}. "
            f"The difference is "
            f"{signed_money(downside_difference)}. "
            f"The 10th percentile describes a point "
            f"in the simulated outcome distribution. "
            f"It is not a guaranteed minimum value "
            f"or a worst-case loss bound."
        ),
    }

    # -----------------------------------------------------
    # STRESS TEST EXPLANATIONS
    # -----------------------------------------------------

    stress_explanations = {}

    current_stress = (
        insights["stress_test"]["current"]
    )

    proposed_stress = (
        insights["stress_test"]["target"]
    )

    scenario_names = {
        "equity_crash": "Stock-market crash",
        "broad_market_downturn": (
            "Broad market downturn"
        ),
        "interest_rate_shock": (
            "Interest-rate shock"
        ),
    }

    for scenario, title in scenario_names.items():

        current_value = float(
            current_stress[scenario][
                "estimated_value"
            ]
        )

        proposed_value = float(
            proposed_stress[scenario][
                "estimated_value"
            ]
        )

        current_change = float(
            current_stress[scenario][
                "portfolio_change"
            ]
        )

        proposed_change = float(
            proposed_stress[scenario][
                "portfolio_change"
            ]
        )

        difference = (
            proposed_value - current_value
        )

        if difference > 0.01:

            simple = (
                f"In this hypothetical "
                f"{title.lower()}, the AI-proposed "
                f"portfolio would retain approximately "
                f"{money(difference)} more than "
                f"your current portfolio."
            )

        elif difference < -0.01:

            simple = (
                f"In this hypothetical "
                f"{title.lower()}, the AI-proposed "
                f"portfolio would retain approximately "
                f"{money(abs(difference))} less than "
                f"your current portfolio."
            )

        else:

            simple = (
                f"Both portfolios produce nearly "
                f"identical results in this hypothetical "
                f"{title.lower()}."
            )

        technical = (
            f"Under the predefined {title.lower()} "
            f"shock, current allocation change="
            f"{percent(current_change)}, "
            f"proposed allocation change="
            f"{percent(proposed_change)}. "
            f"Estimated values are "
            f"{money(current_value)} and "
            f"{money(proposed_value)}, respectively. "
            f"The proposed-minus-current difference "
            f"is {signed_money(difference)}. "
            f"This is a static scenario calculation, "
            f"not a market forecast."
        )

        stress_explanations[scenario] = {
            "title": title,
            "simple": simple,
            "technical": technical,
        }

    # -----------------------------------------------------
    # FINANCIAL GOAL EXPLANATION
    # -----------------------------------------------------

    goal = insights["goal_planning"]

    target_amount = float(
        goal["target_amount"]
    )

    projected_value = float(
        goal["projected_value"]
    )

    required_sip = float(
        goal["required_monthly_sip"]
    )

    monthly_sip = float(
        goal["monthly_sip"]
    )

    goal_gap = (
        target_amount - projected_value
    )

    assumed_return = float(
        goal["assumed_annual_return"]
    )

    if goal_gap <= 0:

        goal_simple = (
            f"Under our example return assumptions, "
            f"your current portfolio and monthly "
            f"investment of {money(monthly_sip)} "
            f"could reach your goal of "
            f"{money(target_amount)}. "
            f"The estimated value is "
            f"{money(projected_value)}. "
            f"This is not guaranteed."
        )

    else:

        goal_simple = (
            f"Under our example return assumptions, "
            f"your current investment plan may fall "
            f"short of your {money(target_amount)} "
            f"goal by approximately "
            f"{money(goal_gap)}. "
            f"The estimated required total monthly "
            f"investment is {money(required_sip)} "
            f"under the same assumptions."
        )

    goal_explanation = {
        "simple": goal_simple,
        "technical": (
            f"Current-allocation assumed annual "
            f"return={percent(assumed_return)}. "
            f"Monthly contribution={money(monthly_sip)}. "
            f"Projected terminal value="
            f"{money(projected_value)}. "
            f"Target={money(target_amount)}. "
            f"Estimated goal gap="
            f"{signed_money(goal_gap)}. "
            f"Required monthly contribution="
            f"{money(required_sip)}. "
            f"Contributions are modeled at month end. "
            f"These goal calculations use the current "
            f"portfolio allocation, not the PPO "
            f"allocation."
        ),
    }

    # -----------------------------------------------------
    # DYNAMIC OVERALL SUMMARY
    # -----------------------------------------------------

    if (
        downside_difference > 0.01
        and median_difference < -0.01
    ):

        overall_simple = (
            "The AI-proposed portfolio shows a "
            "trade-off between growth and downside "
            "outcomes. In the example simulations, "
            "its weaker-case result is better, "
            "but its middle outcome is lower. "
            "This may be a more defensive mix "
            "under the tested assumptions."
        )

    elif (
        downside_difference > 0.01
        and median_difference > 0.01
    ):

        overall_simple = (
            "Under our example assumptions, "
            "the AI-proposed portfolio has better "
            "weaker-case and middle outcomes. "
            "This does not establish that it "
            "will outperform in real markets."
        )

    elif (
        downside_difference < -0.01
        and median_difference > 0.01
    ):

        overall_simple = (
            "The proposed portfolio has a higher "
            "middle outcome but a weaker downside "
            "result in our simulations. "
            "This illustrates a possible "
            "growth-versus-risk trade-off."
        )

    elif (
        downside_difference < -0.01
        and median_difference < -0.01
    ):

        overall_simple = (
            "The proposed portfolio has both "
            "a lower middle outcome and a weaker "
            "downside result under our assumptions. "
            "The simulation does not show an "
            "advantage on these two measures."
        )

    else:

        overall_simple = (
            "The AI has proposed a different "
            "allocation of your investments. "
            "The simulated outcomes are similar "
            "on at least one measure. "
            "Compare the allocations, risk "
            "and goal assumptions before deciding."
        )

    overall_simple += (
        f" The simulated middle-value difference "
        f"is {signed_money(median_difference)}, "
        f"and the weaker-case difference is "
        f"{signed_money(downside_difference)}."
    )

    overall_technical = (
        "PPO V2 uses four current allocation "
        "weights, 13 market indicators and "
        "one risk-profile scalar to produce "
        "four continuous actions. Softmax "
        "transforms these actions into "
        "portfolio allocation weights. "
        f"Simulated median difference="
        f"{signed_money(median_difference)}; "
        f"10th-percentile difference="
        f"{signed_money(downside_difference)}; "
        f"90th-percentile difference="
        f"{signed_money(upside_difference)}. "
        "These results describe modeled "
        "consequences of the proposed allocation. "
        "They do not identify the internal "
        "causal reasons for the PPO decision."
    )

    # -----------------------------------------------------
    # MODEL LIMITATIONS
    # -----------------------------------------------------

    limitations = {
        "simple": (
            "The AI learned from historical market "
            "data. It cannot know future market "
            "movements. The simulations depend "
            "on assumptions, and the suggested "
            "portfolio is not guaranteed to be "
            "the best choice."
        ),
        "technical": (
            "This explanation is based on "
            "single-observation PPO inference, "
            "allocation comparisons, illustrative "
            "Monte Carlo projections and "
            "predefined stress scenarios. "
            "These are not causal feature "
            "attributions. The model has not "
            "demonstrated consistent benchmark "
            "outperformance. Historical data "
            "and assumed return distributions "
            "may not reflect future markets."
        ),
    }

    # -----------------------------------------------------
    # FINAL EXPLANATION RESPONSE
    # -----------------------------------------------------

    return {
        "overall": {
            "simple": overall_simple,
            "technical": overall_technical,
        },
        "allocations": allocation_explanations,
        "growth": growth_explanation,
        "downside": downside_explanation,
        "stress_tests": stress_explanations,
        "goal": goal_explanation,
        "model_limitations": limitations,
    }


# =========================================================
# LOCAL PPO SENSITIVITY ANALYSIS
# =========================================================

def _allocation(model, observation):
    """
    Run deterministic PPO inference and convert
    four actions into allocation weights.

    This must match the softmax conversion used
    in personalized.py.
    """

    obs = np.asarray(
        observation,
        dtype=np.float32,
    ).reshape(-1)

    action, _ = model.predict(
        obs,
        deterministic=True,
    )

    logits = np.asarray(
        action,
        dtype=np.float64,
    ).reshape(-1)

    if (
        logits.size != 4
        or not np.isfinite(logits).all()
    ):
        raise ValueError(
            "PPO returned invalid actions"
        )

    logits = np.clip(
        logits,
        -5,
        5,
    )

    exp_values = np.exp(
        logits - logits.max()
    )

    weights = (
        exp_values / exp_values.sum()
    )

    return weights


def _weights_dict(weights):
    return {
        asset: round(
            float(weights[index]),
            6,
        )
        for index, asset in enumerate(ASSETS)
    }


def _weight_difference(first, second):
    """
    Return percentage-point differences
    between two allocations.
    """

    return {
        asset: round(
            (
                float(second[index])
                - float(first[index])
            ) * 100,
            2,
        )
        for index, asset in enumerate(ASSETS)
    }


# ---------------------------------------------------------
# PPO MODEL SENSITIVITY
# ---------------------------------------------------------

def analyze_model_sensitivity(
    model,
    observation,
):
    """
    Analyze how PPO allocation changes when
    selected observation inputs are modified.

    Observation format:
    - Features 0-3: current portfolio weights
    - Features 4-16: market indicators
    - Feature 17: risk-profile scalar

    These are controlled input/output experiments,
    NOT causal feature attribution.
    """

    obs = np.asarray(
        observation,
        dtype=np.float32,
    ).reshape(-1)

    if obs.size != 18:
        raise ValueError(
            "Expected exactly 18 observation features"
        )

    if not np.isfinite(obs).all():
        raise ValueError(
            "Observation contains invalid values"
        )

    # -----------------------------------------------------
    # BASELINE ALLOCATION
    # -----------------------------------------------------

    baseline = _allocation(
        model,
        obs,
    )

    baseline_weights = _weights_dict(
        baseline
    )

    # -----------------------------------------------------
    # RISK PROFILE EXPERIMENTS
    # -----------------------------------------------------

    risk_tests = {}
    baseline_differences = {}

    for label, risk in RISK_LEVELS.items():

        modified = obs.copy()

        modified[-1] = risk

        weights = _allocation(
            model,
            modified,
        )

        risk_tests[label] = _weights_dict(
            weights
        )

        baseline_differences[label] = (
            _weight_difference(
                baseline,
                weights,
            )
        )

    # -----------------------------------------------------
    # CURRENT HOLDINGS EXPERIMENTS
    # -----------------------------------------------------

    weight_tests = {}
    weight_test_details = {}

    experiments = [
        ("more_equity", 0.05),
        ("less_equity", -0.05),
    ]

    for label, change in experiments:

        modified = obs.copy()

        new_equity = (
            float(modified[0]) + change
        )

        new_liquid = (
            float(modified[3]) - change
        )

        if not (
            0 <= new_equity <= 1
            and 0 <= new_liquid <= 1
        ):
            continue

        modified[0] = new_equity
        modified[3] = new_liquid

        weights = _allocation(
            model,
            modified,
        )

        weight_tests[label] = (
            _weights_dict(weights)
        )

        weight_test_details[label] = {
            "input_equity_change_percentage_points": (
                round(change * 100, 2)
            ),
            "input_liquid_change_percentage_points": (
                round(-change * 100, 2)
            ),
            "output_difference_from_baseline_percentage_points": (
                _weight_difference(
                    baseline,
                    weights,
                )
            ),
        }

    # -----------------------------------------------------
    # RISK RESPONSE RANGES
    # -----------------------------------------------------

    risk_range = {}

    for asset in ASSETS:

        values = [
            risk_tests[label][asset]
            for label in RISK_LEVELS
        ]

        risk_range[asset] = round(
            (
                max(values) - min(values)
            ) * 100,
            2,
        )

    most_sensitive = max(
        risk_range,
        key=risk_range.get,
    )

    delta = risk_range[
        most_sensitive
    ]

    # -----------------------------------------------------
    # SIMPLE SENSITIVITY EXPLANATION
    # -----------------------------------------------------

    if delta < 0.01:

        simple = (
            "Changing the risk setting barely "
            "changed the model allocation for "
            "this particular portfolio and "
            "market observation."
        )

    else:

        simple = (
            f"When we tested cautious, medium "
            f"and higher risk settings, the "
            f"model changed "
            f"{ASSET_NAMES[most_sensitive]} "
            f"the most. Its allocation varied "
            f"by {delta:.2f} percentage points. "
            f"This shows how the model responds "
            f"to risk settings, not which "
            f"setting is best for you."
        )

    # -----------------------------------------------------
    # TECHNICAL SENSITIVITY EXPLANATION
    # -----------------------------------------------------

    technical = (
        "Deterministic PPO inference was repeated "
        "with risk scalar values 0.1, 0.5 and 0.9, "
        "holding the other 17 observation "
        "features constant. "
        f"The largest output-weight range was "
        f"{ASSET_NAMES[most_sensitive]} at "
        f"{delta:.2f} percentage points. "
        "Where feasible, separate tests shift "
        "5 percentage points between the "
        "current Equity and Liquid inputs. "
        "The resulting output allocations "
        "are compared against the baseline. "
        "These are controlled input/output "
        "perturbations, not SHAP values, "
        "causal explanations, or evidence "
        "of predictive accuracy."
    )

    # -----------------------------------------------------
    # FINAL SENSITIVITY RESPONSE
    # -----------------------------------------------------

    return {
        "baseline_weights": baseline_weights,

        "risk_profile_tests": risk_tests,

        "current_weight_tests": weight_tests,

        "risk_response_range_percentage_points": (
            risk_range
        ),

        "risk_test_differences_from_baseline_percentage_points": (
            baseline_differences
        ),

        "current_weight_test_details": (
            weight_test_details
        ),

        "explanation": {
            "simple": simple,
            "technical": technical,
        },

        "method": (
            "controlled_input_perturbation"
        ),

        "observation_feature_count": 18,

        "caveat": (
            "Single-observation sensitivity test "
            "on historical inputs. Results are "
            "not investment advice or causal "
            "feature attribution."
        ),
    }
