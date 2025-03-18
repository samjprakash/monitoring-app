import psutil
from flask import Flask, render_template, jsonify

app = Flask(__name__)

@app.route("/")
def index():
    cpu_metric = psutil.cpu_percent(interval=1)
    mem_metric = psutil.virtual_memory().percent
    message = None

    if cpu_metric > 80 or mem_metric > 80:
        message = "⚠️ High CPU or Memory Usage Detected! Consider Scaling Up."

    return render_template("index.html", cpu_metric=cpu_metric, mem_metric=mem_metric, message=message)

@app.route("/metrics")
def get_metrics():
    return jsonify({
        "cpu": psutil.cpu_percent(interval=1),
        "memory": psutil.virtual_memory().percent
    })

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
