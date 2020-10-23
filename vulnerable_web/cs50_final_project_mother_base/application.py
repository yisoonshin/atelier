

from flask import Flask, render_template, request, redirect, session, url_for
from flask_session import Session


import sqlite3
import hashlib
from tempfile import mkdtemp
from helpers import login_required, error

# Configure application
app = Flask(__name__, static_folder='static')

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Remove
app.config["SESSION_COOKIE_HTTPONLY"] = False

# Configure session to use filesystem
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

conn = sqlite3.connect('metalgear.db', check_same_thread=False)
# List of dicts format
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

conn.row_factory = dict_factory
cursor = conn.cursor()

@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/robots.txt")
def robots():
    return app.send_static_file('robots.txt')

@app.route("/humans.txt")
def humans():
    return app.send_static_file('humans.txt')

@app.route("/login", methods=["GET", "POST"])
def login():
    # POST method to sign in:
    if request.method == "POST":

        # Server-side input checking
        if not request.form.get("username"):
            return render_template("login.html", error_msg="must provide username")

        if not request.form.get("password"):
            return render_template("login.html", error_msg="must provide password")

        user = request.form.get("username")
        pw_hash = hashlib.md5(request.form.get("password").encode()).hexdigest()

        query = f"""
        SELECT * FROM users
        WHERE username='{user}' AND pw_hash='{pw_hash}';"""
        print(query)

        # Query database for username & hash
        rows = [row for row in cursor.execute(query)]

        # Return error message if no match is found
        if not rows:
            error_msg = "invalid username and/or password"
            return render_template("login.html", error_msg=error_msg)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session["username"] = rows[0]["username"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/pw_reset", methods=["GET", "POST"])
@login_required
def reset():
    if request.method == "GET":
        return render_template("pw_reset.html")
    else:
        new_pass  = request.form.get("new_password")
        pw_confirm = request.form.get("pw_confirm")

        # error checking
        if not new_pass:
            return render_template("pw_reset.html", error_msg="Sorry, please enter a new password.")
        if len(new_pass) < 6:
            return render_template("pw_reset.html", error_msg="Sorry, password must be at least 6 characters.")
        if new_pass != pw_confirm:
            return render_template("pw_reset.html", error_msg="Sorry, passwords don't match.")

        # if all clear, generate password hash and input that in the db.
        pw_hash = hashlib.md5(new_pass.encode()).hexdigest()
        uid = session.get("user_id")
        query = f"""
            UPDATE users
            SET pw_hash='{pw_hash}'
            WHERE id={uid}
        """
        conn.execute(query)
        conn.commit()

        return render_template("pw_reset.html", success="Password successfully reset.")

@app.route("/missions")
@login_required
def missions():
    query = """
    SELECT
        u.username AS requester,
        m.posted_at,
        ROUND(m.payout,2) AS payout,
        m.headline,
        m.details
    FROM missions m LEFT JOIN users u ON m.requested_by=u.id
    ORDER BY m.posted_at DESC;
    """
    missions = conn.execute(query).fetchall()
    if sum(["<script>" in mission["details"] for mission in missions]):
        return render_template("missions.html", missions=missions, flag="THM_{5N4K3_<35_x55}")
    else:
        return render_template("missions.html", missions=missions)


@app.route("/history")
@login_required
def history():
    return render_template("history.html")

@app.route("/message_board", methods=["GET", "POST"])
@login_required
def message_board():
    if request.method == "POST":
        uid = session.get("user_id")
        message = request.form.get("message_form")
        query = """
            INSERT INTO messages (user_id, message)
            VALUES (?, ?)
        """
        conn.execute(query, (uid, message))
        conn.commit()
        message = request.form.get("message_form")
        return render_template("message_board.html")
    else:
        query = """
        SELECT
            u.username,
            m.time_sent,
            m.message
        FROM messages m LEFT JOIN users u ON m.user_id=u.id
        ORDER BY m.time_sent DESC;
        """
        messages = conn.execute(query).fetchall()
        return render_template("message_board.html", messages=messages)

@app.route("/box", methods=["GET", "POST"])
@login_required
def box():
    if request.method == "POST":
        passcode = request.form.get("passcode").strip().lower().replace('_','').replace('-','').replace('?','')
        print(passcode)
        if "lalilulelo" in passcode:
            return redirect("/command_center")
        else:
            return redirect("/logout")
    else:
        return render_template("box.html")

@app.route("/command_center")
@login_required
def command_center():
    return render_template("command_center.html")

@app.route("/headcount", methods=["GET", "POST"])
@login_required
def headcount():
    term = ''
    if request.method == "POST":
        term = request.form.get("search").strip().lower()
    query = f"SELECT * FROM users WHERE role LIKE '%{term}%' OR username LIKE '%{term}%' OR email LIKE '%{term}%' ORDER by role;"
    rows = conn.execute(query)

    if not rows:
        return render_template("headcount.html")
    else:
        return render_template("headcount.html", rows=rows)

@app.route("/provision", methods=["GET", "POST"])
@login_required
def provision():
    if request.method == "POST":
        # Server-side input checking
        if not request.form.get("username"):
            return render_template("provision.html", error_msg="must provide username")

        # check if user already exists
        query = "SELECT DISTINCT username FROM users;"
        usernames = [row["username"].lower() for row in conn.execute(query)]
        if request.form.get("username").strip().lower() in usernames:
            return render_template("provision.html", error_msg="this username is too similar to an existing one")

        if not request.form.get("password"):
            return render_template("provision.html", error_msg="must provide password")

        if not request.form.get("email"):
            return render_template("provision.html", error_msg="must provide email")

        user = request.form.get("username")
        pw_hash = hashlib.md5(request.form.get("password").encode()).hexdigest()
        email = request.form.get("email")
        role = request.form.get("role")

        query = """
            INSERT INTO users (username, pw_hash, email, role)
            VALUES (?, ?, ?, ?)
        """
        conn.execute(query, (user, pw_hash, email, role))
        conn.commit()
        return render_template("provision.html", success=f"successfully added {user}")
    else:
        return render_template("provision.html")

@app.route("/create_missions", methods=["GET", "POST"])
@login_required
def create_missions():
    if request.method == "POST":

        if not request.form.get('mission_headline'):
            return render_template("create_missions.html", error_msg="Please provide a headline.")

        if not request.form.get('mission_details'):
            return render_template("create_missions.html", error_msg="Please provide relevant mission details.")

        requester = session.get("user_id")
        headline = request.form.get("mission_headline")
        payout = request.form.get("mission_payout")
        details = request.form.get("mission_details")
        query = """
            INSERT INTO missions (requested_by, headline, payout, details)
            VALUES (?, ?, ?, ?)
        """
        conn.execute(query, (requester, headline, payout, details))
        conn.commit()
        return render_template("create_missions.html", success="Mission successfully created.")
    else:
        return render_template("create_missions.html")

@app.route("/jukebox")
@login_required
def jukebox():
    user = session.get("username")
    if user in ['bigboss','kaz','ocelot']:
        return render_template("jukebox.html")
    else:
        return render_template("error.html", error_code=403, error_msg="This content is only for commanding officers only.")