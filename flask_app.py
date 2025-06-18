from flask import Flask, render_template, request, redirect, session
from datetime import datetime
import json
import os
import uuid
import random

app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # Replace this with a secure secret key

DATA_FOLDER = "data"
LEDGER_FILE = os.path.join(DATA_FOLDER, "ledger.json")
REWARDS_FILE = os.path.join(DATA_FOLDER, "rewards.json")
GROUPS_FILE = os.path.join(DATA_FOLDER, "groups.json")
USERS_FILE = os.path.join(DATA_FOLDER, "users.json")

# Ensure data folder and files exist
os.makedirs(DATA_FOLDER, exist_ok=True)

for file, default in [
    (LEDGER_FILE, []),
    (REWARDS_FILE, {}),
    (GROUPS_FILE, {}),
    (USERS_FILE, {})
]:
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump(default, f)

# Utility functions
def load_json(filepath):
    with open(filepath, "r") as f:
        return json.load(f)

def save_json(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)

# Routes
@app.route("/")
def home():
    if "user" not in session:
        return redirect("/login")
    groups = load_json(GROUPS_FILE)
    return render_template("index.html", groups=groups)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        otp = str(random.randint(100000, 999999))
        session["otp"] = otp
        session["email"] = email
        print(f"OTP for {email} is: {otp}")  # Replace with actual email sending
        return redirect("/verify_otp")
    return render_template("register.html")

@app.route("/verify_otp", methods=["GET", "POST"])
def verify_otp():
    if request.method == "POST":
        entered_otp = request.form["otp"]
        if entered_otp == session.get("otp"):
            return redirect("/set_password")
        else:
            return "Invalid OTP"
    return render_template("verify_otp.html")

@app.route("/set_password", methods=["GET", "POST"])
def set_password():
    if request.method == "POST":
        password = request.form["password"]
        email = session.get("email")
        users = load_json(USERS_FILE)
        users[email] = {"password": password}
        save_json(USERS_FILE, users)
        session["user"] = email
        return redirect("/")
    return render_template("set_password.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("new_user") == "yes":
            return redirect("/register")
        email = request.form["email"]
        password = request.form["password"]
        users = load_json(USERS_FILE)
        if email in users and users[email]["password"] == password:
            session["user"] = email
            return redirect("/")
        return "Invalid credentials"
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")

@app.route("/add_group", methods=["GET", "POST"])
def add_group():
    if request.method == "POST":
        group_name = request.form["group_name"]
        members = request.form["members"].split(",")
        members = [m.strip() for m in members if m.strip()]
        group_id = str(uuid.uuid4())

        groups = load_json(GROUPS_FILE)
        groups[group_id] = {
            "name": group_name,
            "members": members
        }
        save_json(GROUPS_FILE, groups)
        return redirect("/")
    return render_template("add_group.html")

@app.route("/add_transaction", methods=["GET", "POST"])
def add_transaction():
    groups = load_json(GROUPS_FILE)
    selected_group = request.form.get("group_id") if request.method == "POST" else request.args.get("group_id")

    if request.method == "POST" and "amount" in request.form:
        sender = request.form["sender"]
        receiver = request.form["receiver"]
        amount = float(request.form["amount"])
        group_id = request.form["group_id"]
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        new_transaction = {
            "sender": sender,
            "receiver": receiver,
            "amount": amount,
            "timestamp": timestamp,
            "group_id": group_id
        }

        chain = load_json(LEDGER_FILE)
        if not chain or len(chain[-1]["transactions"]) >= 5:
            block = {
                "index": len(chain) + 1,
                "timestamp": timestamp,
                "transactions": [new_transaction]
            }
            chain.append(block)
        else:
            chain[-1]["transactions"].append(new_transaction)

        save_json(LEDGER_FILE, chain)
        return redirect(f"/group_ledger/{group_id}")
    return render_template("add_transaction.html", groups=groups, selected_group=selected_group)

@app.route("/mine", methods=["GET", "POST"])
def mine():
    if request.method == "POST":
        miner = request.form["miner"]
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        reward_transaction = {
            "sender": "System",
            "receiver": miner,
            "amount": 10.0,
            "timestamp": timestamp
        }

        chain = load_json(LEDGER_FILE)
        new_block = {
            "index": len(chain) + 1,
            "timestamp": timestamp,
            "transactions": [reward_transaction]
        }
        chain.append(new_block)
        save_json(LEDGER_FILE, chain)

        rewards = load_json(REWARDS_FILE)
        rewards[miner] = rewards.get(miner, 0) + 10
        save_json(REWARDS_FILE, rewards)
        return redirect("/rewards")
    return render_template("mine.html")

@app.route("/rewards")
def rewards():
    rewards = load_json(REWARDS_FILE)
    return render_template("rewards.html", rewards=rewards)

@app.route("/group_ledger/<group_id>")
def group_ledger(group_id):
    chain = load_json(LEDGER_FILE)
    groups = load_json(GROUPS_FILE)

    if group_id not in groups:
        return render_template("404.html"), 404

    group = groups[group_id]
    members = group["members"]

    transactions = []
    for block in chain:
        for tx in block["transactions"]:
            if tx.get("group_id") == group_id:
                transactions.append(tx)

    balances = {member: 0 for member in members}
    for tx in transactions:
        sender = tx["sender"]
        receiver = tx["receiver"]
        amount = tx["amount"]
        if sender in balances:
            balances[sender] -= amount
        if receiver in balances:
            balances[receiver] += amount

    return render_template("group_ledger.html", group=group, group_id=group_id,
                           transactions=transactions, balances=balances)

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

if __name__ == "__main__":
    app.run(debug=True)
