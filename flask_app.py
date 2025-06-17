from flask import Flask, render_template, request, redirect
from datetime import datetime
import json
import os
import uuid

app = Flask(__name__)

DATA_FOLDER = "data"
LEDGER_FILE = os.path.join(DATA_FOLDER, "ledger.json")
REWARDS_FILE = os.path.join(DATA_FOLDER, "rewards.json")
GROUPS_FILE = os.path.join(DATA_FOLDER, "groups.json")

# Ensure data folder and files exist
os.makedirs(DATA_FOLDER, exist_ok=True)

for file in [LEDGER_FILE, REWARDS_FILE, GROUPS_FILE]:
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump({} if "groups" in file else [] if "ledger" in file else {}, f)

# Utility functions
def load_chain():
    with open(LEDGER_FILE, "r") as f:
        return json.load(f)

def save_chain(chain):
    with open(LEDGER_FILE, "w") as f:
        json.dump(chain, f, indent=4)

def load_rewards():
    with open(REWARDS_FILE, "r") as f:
        return json.load(f)

def save_rewards(rewards):
    with open(REWARDS_FILE, "w") as f:
        json.dump(rewards, f, indent=4)

def load_groups():
    with open(GROUPS_FILE, "r") as f:
        return json.load(f)

def save_groups(groups):
    with open(GROUPS_FILE, "w") as f:
        json.dump(groups, f, indent=4)

# Routes
@app.route("/")
def home():
    groups = load_groups()
    return render_template("index.html", groups=groups)

@app.route("/add_group", methods=["GET", "POST"])
def add_group():
    if request.method == "POST":
        group_name = request.form["group_name"]
        members = request.form["members"].split(",")
        members = [m.strip() for m in members if m.strip()]
        group_id = str(uuid.uuid4())

        groups = load_groups()
        groups[group_id] = {
            "name": group_name,
            "members": members
        }
        save_groups(groups)

        return redirect("/")
    
    return render_template("add_group.html")

@app.route("/add_transaction", methods=["GET", "POST"])
def add_transaction():
    groups = load_groups()
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

        chain = load_chain()
        if not chain or len(chain[-1]["transactions"]) >= 5:
            block = {
                "index": len(chain) + 1,
                "timestamp": timestamp,
                "transactions": [new_transaction]
            }
            chain.append(block)
        else:
            chain[-1]["transactions"].append(new_transaction)

        save_chain(chain)
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

        chain = load_chain()
        new_block = {
            "index": len(chain) + 1,
            "timestamp": timestamp,
            "transactions": [reward_transaction]
        }
        chain.append(new_block)
        save_chain(chain)

        rewards = load_rewards()
        rewards[miner] = rewards.get(miner, 0) + 10
        save_rewards(rewards)

        return redirect("/rewards")
    
    return render_template("mine.html")

@app.route("/rewards")
def rewards():
    rewards = load_rewards()
    return render_template("rewards.html", rewards=rewards)

@app.route("/group_ledger/<group_id>")
def group_ledger(group_id):
    chain = load_chain()
    groups = load_groups()

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
