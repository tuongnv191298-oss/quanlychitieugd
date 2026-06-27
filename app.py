from flask import Flask, render_template, request, jsonify, session, redirect
import sqlite3

app = Flask(__name__)
app.secret_key = "ai_bank_pro_final"

DB = "data.db"


# ================= INIT DB =================
def init():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # USERS
    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    # TRANSACTIONS
    c.execute("""
    CREATE TABLE IF NOT EXISTS transactions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        date TEXT,
        type TEXT,
        category TEXT,
        amount REAL,
        note TEXT
    )
    """)

    conn.commit()
    conn.close()

init()


# ================= AUTH PAGE =================
@app.route("/auth")
def auth():
    return render_template("login.html")


# ================= REGISTER =================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        u = request.form["user"]
        p = request.form["pass"]

        conn = sqlite3.connect(DB)
        c = conn.cursor()

        try:
            c.execute("INSERT INTO users(username,password) VALUES(?,?)", (u, p))
            conn.commit()
        except:
            return "❌ User đã tồn tại"

        return redirect("/auth")

    return render_template("register.html")


# ================= LOGIN =================
@app.route("/login", methods=["POST"])
def login():
    u = request.form["user"]
    p = request.form["pass"]

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p))
    user = c.fetchone()

    if user:
        session["user"] = u
        return redirect("/")
    return "❌ Sai tài khoản"


# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/auth")


# ================= HOME =================
@app.route("/")
def home():
    if "user" not in session:
        return redirect("/auth")
    return render_template("app.html", user=session["user"])


# ================= GET DATA =================
@app.route("/data")
def data():
    if "user" not in session:
        return jsonify({"error": "not logged in"})

    user = session["user"]

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT * FROM transactions WHERE user=? ORDER BY id DESC", (user,))
    rows = c.fetchall()
    conn.close()

    income = 0
    expense = 0
    data = []

    for r in rows:
        data.append({
            "id": r[0],
            "date": r[2],
            "type": r[3],
            "category": r[4],
            "amount": r[5],
            "note": r[6]
        })

        if r[3] == "Thu":
            income += r[5]
        else:
            expense += r[5]

    return jsonify({
        "data": data,
        "income": income,
        "expense": expense,
        "balance": income - expense
    })


# ================= ADD =================
@app.route("/add", methods=["POST"])
def add():
    user = session.get("user")
    d = request.json

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    INSERT INTO transactions(user,date,type,category,amount,note)
    VALUES (?,?,?,?,?,?)
    """, (user, d["date"], d["type"], d["category"], d["amount"], d["note"]))

    conn.commit()
    conn.close()
    return jsonify({"ok": True})


# ================= UPDATE =================
@app.route("/update/<int:id>", methods=["POST"])
def update(id):
    d = request.json

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    UPDATE transactions
    SET date=?, type=?, category=?, amount=?, note=?
    WHERE id=?
    """, (d["date"], d["type"], d["category"], d["amount"], d["note"], id))

    conn.commit()
    conn.close()
    return jsonify({"ok": True})


# ================= DELETE =================
@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("DELETE FROM transactions WHERE id=?", (id,))

    conn.commit()
    conn.close()
    return jsonify({"ok": True})


# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)