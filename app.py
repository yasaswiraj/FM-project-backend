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
        # Receive input data
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
        print("Recommendations:")
        print(recommendations)  # Debugging print

        # Return recommendations as JSON
        return recommendations.to_json(orient='records')
    except KeyError as e:
        print(f"KeyError: {e}")
        return jsonify({"error": f"KeyError: {e}"}), 400
    except Exception as e:
        print(f"Exception: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)