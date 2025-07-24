print("Starting Flask app...")
from flask import Flask, request, jsonify
from fredapi import Fred
from datetime import datetime
import pytz
import yfinance as yf
from utility import translate_text, list_languages
import os

print("ENV AT START:", os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))

app = Flask(__name__)

# Your existing recommendation and explanation dictionaries here:
def get_recommendation(cpi, age, risk, horizon, goal):
    if cpi > 6:
        options = {
            (25, "high", "long", "growth"): "Gold ETF, Equity - Energy/Commodities, International ETFs",
            (40, "medium", "medium", "inflation hedge"): "Inflation-Protected Bonds, REITs",
            (55, "low", "short", "regular income"): "Short Duration Debt + Gold Savings Fund",
            (65, "low", "medium", "capital protection"): "SCSS, PMVVY, Hybrid Funds (low equity)"
        }
    elif 3 <= cpi <= 6:
        options = {
            (30, "high", "long", "growth"): "Flexi-cap Equity Funds, Global Tech Funds",
            (45, "medium", "medium", "hedge + growth"): "Balanced Advantage Funds, Multi-Asset Allocation",
            (60, "low", "short", "income"): "Short Duration Debt + Conservative Hybrid Fund",
            (35, "high", "medium", "growth"): "Thematic Funds (infra, consumption) + SIP in Equity"
        }
    else:
        options = {
            (28, "high", "long", "wealth building"): "Mid-Cap & Small-Cap Equity Funds",
            (50, "medium", "medium", "hedge/deflation"): "Long-Term G-Secs, PPF, Index Funds",
            (65, "low", "short", "preserve capital"): "Liquid Funds, Bank FDs, Floating Rate Bonds",
            (38, "medium", "long", "growth"): "Large & Mid Cap Funds, Tax Saver ELSS"
        }
    for (opt_age, opt_risk, opt_horizon, opt_goal), rec in options.items():
        if abs(age - opt_age) <= 5 and risk == opt_risk and horizon == opt_horizon and goal in opt_goal:
            return rec
    return "No exact match found for your profile. Consider consulting a financial advisor."


RECOMMENDATION_EXPLANATIONS = {
    # (same as your original dictionary)
    "Gold ETF, Equity - Energy/Commodities, International ETFs":
        "These funds invest in gold and commodities or international stocks to protect your investment from inflation and grow wealth over time.",
    "Inflation-Protected Bonds, REITs":
        "These are government-backed bonds that adjust for inflation and real estate funds that provide stable income and inflation protection.",
    "Short Duration Debt + Gold Savings Fund":
        "These funds invest in short-term safe bonds and gold savings to offer regular income with low risk.",
    "SCSS, PMVVY, Hybrid Funds (low equity)":
        "Safe government savings schemes and funds with a mix of stocks and debt to protect capital with modest growth.",
    "Flexi-cap Equity Funds, Global Tech Funds":
        "Funds investing in companies of all sizes globally with focus on technology for strong growth potential.",
    "Balanced Advantage Funds, Multi-Asset Allocation":
        "Funds that balance stocks and bonds automatically to manage risk and provide steady growth.",
    "Short Duration Debt + Conservative Hybrid Fund":
        "Low-risk funds investing mostly in bonds and some stocks to preserve capital and generate income.",
    "Thematic Funds (infra, consumption) + SIP in Equity":
        "Funds investing in specific sectors like infrastructure or consumer goods for targeted growth with regular investments.",
    "Mid-Cap & Small-Cap Equity Funds":
        "Funds that invest in medium and small companies with higher growth potential but more risk.",
    "Long-Term G-Secs, PPF, Index Funds":
        "Safe government securities, tax-saving accounts, and low-cost stock index funds for long-term stability.",
    "Liquid Funds, Bank FDs, Floating Rate Bonds":
        "Very safe funds and fixed deposits that preserve capital and provide liquidity.",
    "Large & Mid Cap Funds, Tax Saver ELSS":
        "Funds investing in large and medium companies with tax-saving benefits and growth potential."
}


def get_top5_stocks():
    nifty_50_tickers = [
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", "KOTAKBANK.NS",
        "LT.NS", "AXISBANK.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "HINDUNILVR.NS",
        "BAJFINANCE.NS", "ASIANPAINT.NS", "MARUTI.NS", "SUNPHARMA.NS", "TITAN.NS", "ONGC.NS",
        "ULTRACEMCO.NS", "INDUSINDBK.NS", "NTPC.NS", "POWERGRID.NS", "DIVISLAB.NS", "DRREDDY.NS",
        "HCLTECH.NS", "COALINDIA.NS", "SHREECEM.NS", "BAJAJFINSV.NS", "TATAMOTORS.NS", "GRASIM.NS",
    ]
    data = yf.download(nifty_50_tickers, period="3mo", interval="1d")['Close']
    data = data.dropna(axis=1, how='all')
    returns = (data.iloc[-1] - data.iloc[0]) / data.iloc[0] * 100
    top5 = returns.sort_values(ascending=False).head(5)
    return top5


def get_latest_cpi_info(fred):
    cpi_series_id = "CPIAUCSL"
    cpi_data = fred.get_series(cpi_series_id)
    cpi_yoy = cpi_data.pct_change(12) * 100
    latest_cpi = cpi_data.iloc[-1]
    latest_cpi_date = cpi_data.index[-1]
    latest_cpi_yoy = cpi_yoy.dropna().iloc[-1]

    india_tz = pytz.timezone("Asia/Kolkata")
    current_datetime_ist = datetime.now(india_tz)
    current_date_str = current_datetime_ist.strftime("%A, %B %d, %Y, %I:%M %p IST")

    return {
        "latest_cpi_value": round(latest_cpi, 2),
        "latest_cpi_date": str(latest_cpi_date.date()),
        "latest_cpi_yoy": round(latest_cpi_yoy, 2),
        "current_date_str": current_date_str,
    }


# Initialize Fred client once with API key
FRED_API_KEY = "03b729d2659c2674f4e2f593e0b84be6"
fred_client = Fred(api_key=FRED_API_KEY)

# Use your Google Translate project ID from previous code
TRANSLATE_PROJECT_ID = "gmail-automation-463517"


@app.route('/recommendation', methods=['POST'])
def recommendation():
    data = request.json
    print("recommendation")
    # Print environment info for debugging
    print("GOOGLE_APPLICATION_CREDENTIALS:", os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))
    print("Received data:", data)

    # Extract inputs
    try:
        age = int(data.get("age"))
        risk = data.get("risk").lower()
        horizon = data.get("horizon").lower()
        goal = data.get("goal").lower()
        invested_amount = float(data.get("invested_amount"))
        preferred_language = data.get("language", "en").lower()
    except Exception as e:
        return jsonify({"error": "Invalid or missing input parameters", "details": str(e)}), 400

    print("Preferred language:", preferred_language)

    # Get CPI info
    cpi_info = get_latest_cpi_info(fred_client)
    latest_cpi_yoy = cpi_info["latest_cpi_yoy"]

    # Get recommendation and explanation
    recommendation_text = get_recommendation(latest_cpi_yoy, age, risk, horizon, goal)
    explanation_eng = RECOMMENDATION_EXPLANATIONS.get(
        recommendation_text,
        "Please consult a financial advisor for more details about this investment."
    )

    # Get top performing stocks
    top5_stock_returns = get_top5_stocks()
    top5_stocks = []
    for ticker, ret in top5_stock_returns.items():
        top5_stocks.append({
            "ticker": ticker,
            "return_percent": round(ret, 2)
        })

    # Allocation calculation based on risk profile
    if risk == "high":
        stock_alloc = 0.7
        fund_alloc = 0.3
    elif risk == "medium":
        stock_alloc = 0.5
        fund_alloc = 0.5
    else:  # low risk
        stock_alloc = 0.3
        fund_alloc = 0.7

    stock_amount = invested_amount * stock_alloc
    fund_amount = invested_amount * fund_alloc
    per_stock_amount = stock_amount / len(top5_stocks) if top5_stocks else 0

    # Translate recommendation and explanation if needed
    if preferred_language != "en":
        try:
            recommendation_translated = translate_text(recommendation_text, preferred_language, TRANSLATE_PROJECT_ID)
            explanation_translated = translate_text(explanation_eng, preferred_language, TRANSLATE_PROJECT_ID)
        except Exception as e:
            print("Translation error:", e)
            recommendation_translated = recommendation_text
            explanation_translated = explanation_eng
    else:
        recommendation_translated = recommendation_text
        explanation_translated = explanation_eng

    response = {
        #"cpi_info": cpi_info,
        "recommendation": recommendation_translated,
        #"env_google_credentials": os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"),
        "recommendation_explanation": explanation_translated,
        "top5_stocks": top5_stocks,
        "allocation": {
            "stock_percent": round(stock_alloc * 100, 1),
            "fund_percent": round(fund_alloc * 100, 1),
            "stock_amount": round(stock_amount, 2),
            "fund_amount": round(fund_amount, 2),
            "per_stock_amount": round(per_stock_amount, 2),
        },
    }

    return jsonify(response)


if __name__ == "__main__":
    app.run(debug=True)
