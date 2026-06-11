import json
import logging
import os
from datetime import datetime
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, jsonify, render_template

from config import DATA_FILE, REFRESH_TIMES
from agents.orchestrator_agent import OrchestratorAgent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
Path("data").mkdir(exist_ok=True)


def refresh_headlines() -> dict:
    headlines = OrchestratorAgent().run()
    payload = {
        "updated_at": datetime.now().isoformat(),
        "headlines":  headlines,
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return payload


def load_headlines() -> dict:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"updated_at": None, "headlines": []}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/headlines")
def api_headlines():
    return jsonify(load_headlines())


@app.route("/api/refresh", methods=["POST"])
def api_refresh():
    try:
        data = refresh_headlines()
        return jsonify({"status": "ok", **data})
    except Exception as exc:
        logger.error("Refresh error: %s", exc)
        return jsonify({"status": "error", "message": str(exc)}), 500


def _start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(daemon=True)
    for time_str in REFRESH_TIMES:
        hour, minute = map(int, time_str.split(":"))
        scheduler.add_job(
            refresh_headlines,
            "cron",
            hour=hour,
            minute=minute,
            id=f"refresh_{time_str}",
        )
    scheduler.start()
    logger.info("Scheduler running. Auto-refresh at: %s", ", ".join(REFRESH_TIMES))
    return scheduler


if __name__ == "__main__":
    _start_scheduler()

    if not os.path.exists(DATA_FILE):
        logger.info("No cached headlines — fetching now...")
        try:
            refresh_headlines()
        except Exception as exc:
            logger.warning("Initial fetch failed (%s). Click Refresh Now in the UI.", exc)

    app.run(host="0.0.0.0", port=5678, debug=False, use_reloader=False)
