from flask import Flask, jsonify, request, send_from_directory
from pathlib import Path
import database as db

app = Flask(__name__, static_folder=str(Path(__file__).parent / "frontend"))

FRONTEND = Path(__file__).parent / "frontend"


@app.get("/")
def root():
    return send_from_directory(FRONTEND, "index.html")


@app.get("/api/items")
def list_items():
    category = request.args.get("category")
    done = request.args.get("done")
    done_bool = None if done is None else bool(int(done))
    return jsonify(db.get_items(category=category, done=done_bool))


@app.get("/api/stats")
def stats():
    return jsonify(db.get_stats())


@app.get("/api/expenses/summary")
def expense_summary():
    return jsonify(db.get_expense_summary())


@app.post("/api/items")
def create_item():
    data = request.json
    item_id = db.insert_item(
        category=data["category"],
        title=data["title"],
        details=data.get("details"),
        amount=data.get("amount"),
        currency=data.get("currency", "EGP"),
        remind_at=data.get("remind_at"),
        expense_category=data.get("expense_category"),
    )
    return jsonify({"id": item_id})


@app.patch("/api/items/<int:item_id>")
def edit_item(item_id):
    data = request.json
    db.update_item(
        item_id,
        title=data.get("title"),
        details=data.get("details"),
        remind_at=data.get("remind_at"),
        amount=data.get("amount"),
        currency=data.get("currency", "EGP"),
        category=data.get("category"),
    )
    return jsonify({"ok": True})


@app.patch("/api/items/<int:item_id>/done")
def complete_item(item_id):
    db.mark_done(item_id)
    return jsonify({"ok": True})


@app.delete("/api/items/<int:item_id>")
def remove_item(item_id):
    db.delete_item(item_id)
    return jsonify({"ok": True})
