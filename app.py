from flask import Flask, request, jsonify, send_from_directory
import os
from src.main import process_query
from src.agent_graph import run_agentic_pipeline

app = Flask(__name__, static_folder="frontend")

# Serve the frontend
@app.route("/")
def index():
    return app.send_static_file("index.html")

@app.route("/<path:path>")
def static_proxy(path):
    return app.send_static_file(path)

# API endpoint for analysis
@app.route("/analyze", methods=["POST"])
def analyze():
    user_query = request.json["query"]
    observed, forecast, insights = process_query(user_query)
    return jsonify({
        "observed": observed,
        "forecast": forecast,
        "insights": insights
    })

@app.route("/analyze_agent", methods=["POST"])
def analyze_agent():
    user_query = request.json["query"]
    try:
        result = run_agentic_pipeline(user_query)
        return jsonify(result)
    except Exception as e:
        # Log the error for debugging
        import traceback
        print("Agentic pipeline error:", e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# Serve graph images
@app.route("/graphs/<filename>")
def get_graph(filename):
    # Adjust this path if your graphs are stored elsewhere
    return send_from_directory("data/graphs", filename)

if __name__ == "__main__":
    app.run(debug=True)
