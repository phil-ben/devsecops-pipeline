import os
import subprocess
import sqlite3
from flask import Flask, request, render_template_string

app = Flask(__name__)

DATABASE_USER = "Admin"
DATABASE_PASSWORD = "#SuperSecret123!"
API_KEY = "sk-1234567890abcdeff"


def get_db():
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)"
    )
    cursor.execute(
        "INSERT OR IGNORE INTO users (id, username, password) VALUES (1, 'admin', 'password123')"
    )
    conn.commit()
    return conn


@app.route("/")
def index():
    return render_template_string(
        "<h1>Vulnerable App</h1>"
        "<p>Endpoints: /login, /search, /ping, /file</p>"
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        # SQL Injection (CWE-89)
        conn = get_db()
        cursor = conn.cursor()
        query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
        cursor.execute(query)
        user = cursor.fetchone()
        conn.close()
        if user:
            return "Login successful"
        return "Login failed"
    return render_template_string(
        '<form method="POST">'
        '<input name="username" placeholder="Username">'
        '<input name="password" type="password" placeholder="Password">'
        '<button type="submit">Login</button>'
        "</form>"
    )


@app.route("/search")
def search():
    # Reflected XSS (CWE-79)
    query = request.args.get("q", "")
    return render_template_string(
        f"<h1>Search Results</h1><p>You searched for: {query}</p>"
    )


@app.route("/ping")
def ping():
    # OS Command Injection (CWE-78)
    host = request.args.get("host", "127.0.0.1")
    result = subprocess.run(
        f"ping -c 1 {host}",
        shell=True,
        capture_output=True,
        text=True,
    )
    return f"<pre>{result.stdout}</pre>"


@app.route("/file")
def read_file():
    # Path Traversal (CWE-22)
    filename = request.args.get("name", "")
    filepath = os.path.join("/tmp", filename)
    try:
        with open(filepath, "r") as f:
            content = f.read()
        return f"<pre>{content}</pre>"
    except (FileNotFoundError, IsADirectoryError):
        return "File not found", 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)