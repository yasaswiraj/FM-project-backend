import yfinance as yf
import pandas as pd
import numpy as np

# Risk Assessment Logic
def get_risk_level(answers):
    """
    Determines the user's risk level based on their answers.
    """
    risk_scores = []

    # Age
    if answers['age'] == "20-40":
        risk_scores.append("High")
    elif answers['age'] == "41-60":
        risk_scores.append("Medium")
    else:
        risk_scores.append("Low")

    # Income
    if answers['income'] == "5000-15000 USD":
        risk_scores.append("Low")
    elif answers['income'] == "15000-50000 USD":
        risk_scores.append("Medium")
    else:
        risk_scores.append("High")

    # Investment Horizon
    if answers['horizon'] == "0-1 year":
        risk_scores.append("Low")
    elif answers['horizon'] == "1-5 years":
        risk_scores.append("Medium")
    else:
        risk_scores.append("High")

    # Investment Amount
    if answers['amount'] == "0-10K USD":
        risk_scores.append("Low")
    elif answers['amount'] == "10K-50K USD":
        risk_scores.append("Medium")
    else:
        risk_scores.append("High")

    # Determine overall risk level
    high = risk_scores.count("High")
    medium = risk_scores.count("Medium")
    low = risk_scores.count("Low")

    if high > medium and high > low:
        return "High"
    elif medium > low:
        return "Medium"
    else:
        return "Low"


# Buy Rating Evaluation
def evaluate_buy_rating(row, sector_summary):
    """
    Evaluates whether a stock is a 'Good' or 'Bad' buy based on sector averages.
    """
    try:
        # Get the sector average values for the stock's sector
        sector_avg = sector_summary.loc[row["Sector"]]
    except KeyError:
        # If sector is missing in sector summary, return 'Bad'
        return "Bad"

    good_count = 0

    # P/E Ratio: Good if the company's P/E is less than 110% of the sector average
    if row["P/E Ratio"] and row["P/E Ratio"] < 1.1 * sector_avg["P/E Ratio"]:
        good_count += 1

    # P/B Ratio: Good if the company's P/B is less than 110% of the sector average
    if row["P/B Ratio"] and row["P/B Ratio"] < 1.1 * sector_avg["P/B Ratio"]:
        good_count += 1

    # Debt-to-Equity: Good if the company's debt-to-equity is less than 110% of the sector average
    if row["Debt-to-Equity"] and row["Debt-to-Equity"] < 1.1 * sector_avg["Debt-to-Equity"]:
        good_count += 1

    # Standard Deviation: Good if the company's standard deviation is below the sector average
    if row["Std Deviation"] and row["Std Deviation"] < sector_avg["Std Deviation"]:
        good_count += 1

    # CAGR: Good if the company's CAGR is above the sector average
    if row["CAGR"] and row["CAGR"] > sector_avg["CAGR"]:
        good_count += 1

    # If 3 or more metrics are good, the stock is rated 'Good'; otherwise, 'Bad'
    return "Good" if good_count >= 3 else "Bad"


# Fetch Stock Data
def fetch_stock_data(tickers):
    """
    Fetch stock data for the provided tickers, calculate metrics, and add 'Buy Rating'.
    """
    data = []

    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="2y")
            if hist.empty or "Close" not in hist.columns:
                continue

            start_price = hist["Close"].iloc[0]
            end_price = hist["Close"].iloc[-1]
            cagr = ((end_price / start_price) ** (1 / 2)) - 1

            hist["Daily Returns"] = hist["Close"].pct_change().dropna()
            std_dev = hist["Daily Returns"].std() * np.sqrt(252)

            info = stock.info
            data.append({
                "Ticker": ticker,
                "Company Name": info.get("longName", "N/A"),
                "Sector": info.get("sector", "N/A"),
                "P/E Ratio": info.get("trailingPE"),
                "P/B Ratio": info.get("priceToBook"),
                "Debt-to-Equity": info.get("debtToEquity"),
                "Std Deviation": std_dev,
                "CAGR": cagr,
            })
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            continue

    # Convert collected data into a DataFrame
    df = pd.DataFrame(data)

    if not df.empty:
        # Convert numeric columns for calculations
        numeric_columns = ["P/E Ratio", "P/B Ratio", "Debt-to-Equity", "Std Deviation", "CAGR"]
        df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric, errors="coerce")

        # Group by sector and calculate averages
        sector_summary = df.groupby("Sector")[numeric_columns].mean()

        # Add 'Buy Rating' column
        df["Buy Rating"] = df.apply(lambda row: evaluate_buy_rating(row, sector_summary), axis=1)

    return df


# Recommend Stocks
def recommend_stocks(risk_level, diversify, df):
    """
    Recommend stocks based on the user's risk level and diversification preference.
    """
    good_stocks = df[df["Buy Rating"] == "Good"]
    good_stocks = good_stocks.sort_values(by="CAGR", ascending=False)

    if risk_level == "Low":
        recommended_stocks = good_stocks[good_stocks["Std Deviation"] <= 0.20]
    elif risk_level == "Medium":
        recommended_stocks = good_stocks[good_stocks["Std Deviation"] <= 0.28]
    else:
        recommended_stocks = good_stocks

    if diversify:
        return recommended_stocks.groupby("Sector").head(1).head(5)
    else:
        return recommended_stocks.head(5)
