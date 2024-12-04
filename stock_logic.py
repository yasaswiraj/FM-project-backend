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
    risk_scores.append(
        "High" if answers["age"] == "20-40" else "Medium" if answers["age"] == "41-60" else "Low"
    )

    # Income
    risk_scores.append(
        "Low" if answers["income"] == "5000-15000 USD"
        else "Medium" if answers["income"] == "15000-50000 USD"
        else "High"
    )

    # Investment Horizon
    risk_scores.append(
        "Low" if answers["horizon"] == "0-1 year"
        else "Medium" if answers["horizon"] == "1-5 years"
        else "High"
    )

    # Investment Amount
    risk_scores.append(
        "Low" if answers["amount"] == "0-10K USD"
        else "Medium" if answers["amount"] == "10K-50K USD"
        else "High"
    )

    # Determine overall risk level
    high = risk_scores.count("High")
    medium = risk_scores.count("Medium")
    low = risk_scores.count("Low")

    return "High" if high > medium and high > low else "Medium" if medium > low else "Low"


# Buy Rating Evaluation
def evaluate_buy_rating(row, sector_summary):
    """
    Evaluates whether a stock is a 'Good' or 'Bad' buy based on sector averages.
    """
    try:
        sector_avg = sector_summary.loc[row["Sector"]]
    except KeyError:
        return "Bad"

    good_count = 0

    # Evaluate metrics
    metrics = [
        ("P/E Ratio", lambda x, avg: x < 1.1 * avg),
        ("P/B Ratio", lambda x, avg: x < 1.1 * avg),
        ("Debt-to-Equity", lambda x, avg: x < 1.1 * avg),
        ("Std Deviation", lambda x, avg: x < avg),
        ("CAGR", lambda x, avg: x > avg),
    ]

    for metric, condition in metrics:
        if pd.notna(row[metric]) and condition(row[metric], sector_avg[metric]):
            good_count += 1

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

            # Calculate CAGR and Standard Deviation
            start_price = hist["Close"].iloc[0]
            end_price = hist["Close"].iloc[-1]
            cagr = ((end_price / start_price) ** (1 / 2)) - 1
            hist["Daily Returns"] = hist["Close"].pct_change().dropna()
            std_dev = hist["Daily Returns"].std() * np.sqrt(252)

            # Fetch fundamental data
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
    # Filter stocks with a "Good" buy rating
    good_stocks = df[df["Buy Rating"] == "Good"].sort_values(by="CAGR", ascending=False)

    # Risk filtering
    if risk_level == "Low":
        recommended_stocks = good_stocks[good_stocks["Std Deviation"] <= 0.20]
    elif risk_level == "Medium":
        recommended_stocks = good_stocks[good_stocks["Std Deviation"] <= 0.28]
    else:  # High risk
        recommended_stocks = good_stocks

    if diversify:
        # Group by Sector and pick the top stock from each sector
        diversified_stocks = recommended_stocks.groupby("Sector").head(1)

        # If there aren't enough diverse stocks, fill with the next best options
        if len(diversified_stocks) < 5:
            remaining_stocks = recommended_stocks[
                ~recommended_stocks.index.isin(diversified_stocks.index)
            ]
            diversified_stocks = pd.concat([diversified_stocks, remaining_stocks]).head(5)

        return diversified_stocks
    else:
        # Simply return the top 5 stocks
        return recommended_stocks.head(5)


# Portfolio Metrics
def calculate_portfolio_metrics(recommended_stocks):
    """
    Calculate the expected return and standard deviation of the recommended portfolio.
    """
    if recommended_stocks.empty:
        return None, None

    # Extract CAGR and Std Deviation
    cagr = recommended_stocks["CAGR"].values
    std_dev = recommended_stocks["Std Deviation"].values

    # Equal weights for each stock
    n_stocks = len(cagr)
    weights = np.full(n_stocks, 1 / n_stocks)

    # Placeholder correlation matrix (can be replaced with actual correlations)
    correlation_matrix = np.eye(n_stocks) + 0.25 * (np.ones((n_stocks, n_stocks)) - np.eye(n_stocks))

    # Portfolio expected return
    expected_return = np.dot(weights, cagr)

    # Portfolio variance and standard deviation
    portfolio_variance = np.dot(weights, np.dot(correlation_matrix * np.outer(std_dev, std_dev), weights))
    portfolio_std_dev = np.sqrt(portfolio_variance)

    return expected_return, portfolio_std_dev
