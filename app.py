from flask import Flask, request, jsonify
from flask_cors import CORS
from stock_logic import get_risk_level, fetch_stock_data, recommend_stocks
import pandas as pd

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
    # Add more tickers as needed...
]

# In-memory storage for preferences
user_preferences = {}

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

        # Calculate portfolio metrics if there are recommendations
        if not recommendations.empty:
            from stock_logic import calculate_portfolio_metrics
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

if __name__ == "__main__":
    app.run(debug=True)
