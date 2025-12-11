from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from stock_logic import (
    get_risk_level,
    fetch_stock_data,
    recommend_stocks,
    calculate_portfolio_metrics,
    forecast_and_plot,
    download_price_data_for_recommended_stocks,
)
import pandas as pd
import os

app = Flask(__name__)

# Enable CORS
CORS(app)

# Sample tickers for testing
tickers = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "BRK-B", "TSLA", "V", "JNJ",
    "WMT", "PG", "MA", "PYPL", "UNH", "DIS", "HD", "INTC", "CSCO", "MRK",
    "XOM", "PFE", "VZ", "KO", "PEP", "ABT", "CRM", "NKE", "AVGO", "WFC",
    "T", "LLY", "ORCL", "MDT", "GE", "NEE", "CVX", "COST", "QCOM", "ABNB", "DUK", "NEE", 
    "SO", "EXC", "XEL", "AEP", "CAT", "HON", "MMM", "RTX", "UPS", "DE", "GE", "COP", "EOG", "SLB"
]

# In-memory storage for preferences
user_preferences = {}
price_data_dict = {}

@app.route('/')
def home():
    return "Welcome to the Stock Recommendation API!"

@app.route('/risk', methods=['POST'])
def risk():
    try:
        data = request.json
        answers = data['answers']
        risk_level = get_risk_level(answers)
        return jsonify({"risk_level": risk_level})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/fetch', methods=['GET'])
def fetch():
    try:
        global tickers
        stock_data = fetch_stock_data(tickers)
        stock_data.to_csv("stock_data.csv", index=False)  # Save for reuse
        return jsonify({"message": "Stock data fetched and saved."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/recommend', methods=['POST'])
def recommend():
    try:
        data = request.json
        risk_level = data['risk_level']
        diversify = data['diversify']

        # Load stock data
        stock_data = pd.read_csv("stock_data.csv")
        print("Loaded Stock DataFrame:")
        print(stock_data.head())  # Debugging print

        # Check if required columns exist
        required_columns = ["Ticker", "Buy Rating", "CAGR", "Std Deviation", "Sector"]
        for col in required_columns:
            if col not in stock_data.columns:
                raise KeyError(f"Missing required column: {col}")

        # Get recommendations
        recommendations = recommend_stocks(risk_level, diversify, stock_data)

        # Download price data for the recommended stocks
        global price_data_dict
        price_data_dict = download_price_data_for_recommended_stocks(recommendations)

        # Calculate portfolio metrics if there are recommendations
        if not recommendations.empty:
            expected_return, portfolio_std_dev = calculate_portfolio_metrics(recommendations)
        else:
            expected_return, portfolio_std_dev = None, None

        # Convert recommendations to JSON
        recommendations_json = recommendations.to_dict(orient="records")

        # Return recommendations and metrics
        return jsonify({
            "recommendations": recommendations_json,
            "expected_return": expected_return,
            "portfolio_std_dev": portfolio_std_dev
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/portfolio-preference', methods=['POST'])
def portfolio_preference():
    try:
        data = request.json
        user_preferences["diversify"] = data.get("diversify", True)
        return jsonify({"message": "Preference saved successfully", "preference": user_preferences["diversify"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get-preference', methods=['GET'])
def get_preference():
    try:
        diversify = user_preferences.get("diversify", True)  # Default to True
        return jsonify({"preference": diversify})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/forecast/<ticker>', methods=['GET'])
def forecast(ticker):
    try:
        if ticker not in price_data_dict:
            return jsonify({"error": f"No price data found for ticker {ticker}"}), 404

        # Generate and save the forecast plot
        file_path = f"{ticker}_forecast.png"
        forecast_and_plot(ticker, price_data_dict[ticker], file_path)

        # Send the file as a response
        return send_file(file_path, mimetype="image/png", as_attachment=False)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # Cleanup: Remove the generated file after sending
        if os.path.exists(file_path):
            os.remove(file_path)

if __name__ == "__main__":
    app.run(debug=True)
