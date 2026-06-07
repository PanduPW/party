import os
from functools import wraps

import MySQLdb.cursors
from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from flask_mysqldb import MySQL
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY", "super-secret-key-1234")
app.config["MYSQL_HOST"] = os.getenv("MYSQL_HOST", "localhost")
app.config["MYSQL_USER"] = os.getenv("MYSQL_USER", "root")
app.config["MYSQL_PASSWORD"] = os.getenv("MYSQL_PASSWORD", "")

mysql = MySQL(app)

# Initialize the database schema and seed data
def init_db():
    schema_path = os.path.join("database", "schema.sql")
    seed_path = os.path.join("database", "seed.sql")

    with app.app_context():
        conn = mysql.connection
        cursor = conn.cursor()
        try:
            print("Ensuring railway_system container exists...")
            cursor.execute("CREATE DATABASE IF NOT EXISTS railway_system")
            cursor.execute("USE railway_system")

            app.config["MYSQL_DB"] = "railway_system"

            cursor.execute("SHOW TABLES LIKE 'Users'")
            tables_exist = cursor.fetchone()

            if not tables_exist and os.path.exists(schema_path):
                print("Running schema migration...")
                with open(schema_path, "r") as f:
                    schema_commands = [
                        cmd.strip()
                        for cmd in f.read().split(";")
                        if cmd.strip() and not cmd.strip().lower().startswith("use ")
                    ]

                for command in schema_commands:
                    cursor.execute(command)
                conn.commit()
            else:
                print("Schema already exists. Skipping structural execution.")

            cursor.execute("SHOW TABLES LIKE 'Station'")
            station_table_exists = cursor.fetchone()

            if station_table_exists:
                cursor.execute("SELECT COUNT(*) FROM Station")
                has_data = cursor.fetchone()[0] > 0

                if not has_data and os.path.exists(seed_path):
                    print("Seeding baseline application data...")
                    with open(seed_path, "r") as f:
                        seed_commands = [
                            cmd.strip() for cmd in f.read().split(";") if cmd.strip()
                        ]

                    for command in seed_commands:
                        cursor.execute(command)
                    conn.commit()
                    print("Database initialized and seeded successfully.")
                else:
                    print("Database initialization check complete. Seeding skipped.")

        except Exception as e:
            conn.rollback()
            print(f"Database Initialization Error: {e}")
        finally:
            cursor.close()


# --- Security/Role Helpers ---
def login_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "role" not in session or session["role"] not in ["admin", "superadmin"]:
            if request.is_json or request.path.startswith("/api/"):
                return jsonify({"error": "Unauthorized Access"}), 403
            return "Unauthorized Access", 403
        return f(*args, **kwargs)

    return decorated_function

def superadmin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "role" not in session or session["role"] != "superadmin":
            if request.is_json or request.path.startswith("/api/"):
                return jsonify({"error": "Strict Super-Admin Authority Required"}), 403
            return "Unauthorized Access", 403
        return f(*args, **kwargs)

    return decorated_function


# --- Auth Routes ---
@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        if request.is_json:
            data = request.json
        else:
            data = request.form

        email = data.get("email", "").strip()
        password = data.get("password", "")

        if not email or not password:
            error_msg = "Please fill in all fields."
            if request.is_json:
                return jsonify({"error": error_msg}), 400
            return render_template("login.html", error=error_msg)

        with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as c:
            query = (
                "SELECT user_id, email, password_hash, role FROM Users WHERE email = %s"
            )
            c.execute(query, (email,))
            user = c.fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["user_id"]
            session["email"] = user["email"]
            session["role"] = user["role"]

            if request.is_json:
                return jsonify(
                    {"ok": True, "role": user["role"], "redirect": url_for("index")}
                )
            return redirect(url_for("index"))

        invalid_msg = "Invalid email or password."
        if request.is_json:
            return jsonify({"error": invalid_msg}), 401
        return render_template("login.html", error=invalid_msg)

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        if request.is_json:
            data = request.json
        else:
            data = request.form

        email = data.get("email", "").strip()
        password = data.get("password", "")
        first_name = data.get("first_name", "").strip()
        last_name = data.get("last_name", "").strip()
        phone_no = data.get("phone_no", None)

        if not email or not password or not first_name or not last_name:
            error_msg = "All required fields must be completed."
            if request.is_json:
                return jsonify({"error": error_msg}), 400
            return render_template("register.html", error=error_msg)

        conn = mysql.connection
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)

        try:
            cursor.execute("SELECT user_id FROM Users WHERE email = %s", (email,))
            if cursor.fetchone():
                error_msg = "This email is already registered."
                if request.is_json:
                    return jsonify({"error": error_msg}), 400
                return render_template("register.html", error=error_msg)

            hashed_password = generate_password_hash(password)

            user_query = (
                "INSERT INTO Users (email, password_hash, role) VALUES (%s, %s, 'user')"
            )
            cursor.execute(user_query, (email, hashed_password))
            new_user_id = cursor.lastrowid

            passenger_query = """
                INSERT INTO Passenger (user_id, first_name, last_name, phone_no)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(
                passenger_query, (new_user_id, first_name, last_name, phone_no)
            )
            conn.commit()

            session.clear()
            session["user_id"] = new_user_id
            session["email"] = email
            session["role"] = "user"

            if request.is_json:
                return jsonify({"ok": True, "redirect": url_for("index")})
            return redirect(url_for("index"))

        except Exception as e:
            conn.rollback()
            print(f"Registration Error Transaction Failure: {e}")
            error_msg = "An unexpected error occurred. Please try again later."
            if request.is_json:
                return jsonify({"error": error_msg}), 500
            return render_template("register.html", error=error_msg)
        finally:
            cursor.close()

    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# --- UI Pages Route Layer ---
@app.route("/")
@app.route("/dashboard")
@login_required
def index():
    return render_template("index.html")


@app.route("/stations")
@login_required
def stations():
    return render_template("stations.html")


@app.route("/routes")
@login_required
def routes():
    return render_template("routes.html")


@app.route("/purchases")
@login_required
def purchases():
    return render_template("purchases.html")


@app.route("/book")
@login_required
def book():
    return render_template("book.html")


@app.route("/trains")
@admin_required
def train_management_page():
    return render_template("trains.html")


@app.route("/manage-users")
@superadmin_required
def user_management_page():
    return render_template("manage_users.html")


# --- API layer: Stations ---
@app.route("/api/stations", methods=["GET"])
@login_required
def api_stations():
    with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as c:
        c.execute("SELECT * FROM Station")
        rows = c.fetchall()
    return jsonify(rows)


@app.route("/api/stations", methods=["POST"])
@admin_required
def api_station_create():
    d = request.json
    with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as c:
        c.execute(
            "INSERT INTO Station (station_name, city) VALUES (%s, %s)",
            (d["station_name"], d["city"]),
        )
        mysql.connection.commit()
    return jsonify({"ok": True})


@app.route("/api/stations/<int:sid>", methods=["PUT"])
@admin_required
def api_station_update(sid):
    d = request.json
    with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as c:
        c.execute(
            "UPDATE Station SET station_name=%s, city=%s WHERE station_id=%s",
            (d["station_name"], d["city"], sid),
        )
        mysql.connection.commit()
    return jsonify({"ok": True})


@app.route("/api/stations/<int:sid>", methods=["DELETE"])
@admin_required
def api_station_delete(sid):
    with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as c:
        c.execute("DELETE FROM Station WHERE station_id=%s", (sid,))
        mysql.connection.commit()
    return jsonify({"ok": True})


# --- API Layer: Routes ---
@app.route("/api/routes")
def api_routes():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized Access"}), 401

    conn = mysql.connection
    cursor = conn.cursor(MySQLdb.cursors.DictCursor)

    try:
        query = """
            SELECT
                r.route_id, r.departure_station_id, r.arrival_station_id, r.train_id, r.ticket_price,
                s1.station_name AS dep_name, s1.city AS dep_city,
                s2.station_name AS arr_name, s2.city AS arr_city,
                t.train_name,
                CAST(r.departure_time AS CHAR) AS departure_time,
                CAST(r.arrival_time AS CHAR) AS arrival_time
            FROM Route r
            JOIN Station s1 ON r.departure_station_id = s1.station_id
            JOIN Station s2 ON r.arrival_station_id = s2.station_id
            LEFT JOIN Train t ON r.train_id = t.train_id
            ORDER BY r.departure_time ASC
        """
        cursor.execute(query)
        routes_data = cursor.fetchall()
        return jsonify(routes_data), 200
    except Exception as e:
        print(f"Database Schedule Read Crash: {e}")
        return jsonify({"error": "Internal ledger read error"}), 500
    finally:
        cursor.close()


@app.route("/api/routes", methods=["POST"])
def api_create_route():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized Access"}), 401

    if session.get("role") not in ["admin", "superadmin"]:
        return jsonify(
            {"error": "Forbidden: Administrative clear privileges required"}
        ), 403

    data = request.get_json() or {}

    train_id = data.get("train_id")
    departure_station_id = data.get("departure_station_id")
    arrival_station_id = data.get("arrival_station_id")
    departure_time = data.get("departure_time")
    arrival_time = data.get("arrival_time")
    ticket_price = data.get("ticket_price")

    if (
        not all(
            [
                train_id,
                departure_station_id,
                arrival_station_id,
                departure_time,
                arrival_time,
            ]
        )
        or ticket_price is None
    ):
        return jsonify({"error": "Missing mandatory scheduling parameters"}), 400

    if int(departure_station_id) == int(arrival_station_id):
        return jsonify(
            {
                "error": "Mutation Error: Departure and arrival node assignments cannot be identical"
            }
        ), 400

    conn = mysql.connection
    cursor = conn.cursor()

    try:
        # 5. Database Transaction Ingestion
        insert_query = """
            INSERT INTO Route (
                train_id,
                departure_station_id,
                arrival_station_id,
                departure_time,
                arrival_time,
                ticket_price
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """
        params = (
            int(train_id),
            int(departure_station_id),
            int(arrival_station_id),
            str(departure_time),
            str(arrival_time),
            float(ticket_price),
        )

        cursor.execute(insert_query, params)
        conn.commit()

        return jsonify(
            {
                "ok": True,
                "message": "Transit route schedule dynamically generated and appended to global ledger.",
                "route_id": cursor.lastrowid,
            }
        ), 201

    except MySQLdb.Error as db_err:
        conn.rollback()
        if db_err.args[0] == 1452:
            return jsonify(
                {
                    "error": "Foreign Key violation: Specified station nodes or locomotive asset references do not exist."
                }
            ), 422

        print(f"Database Schedule Write Crash: {db_err}")
        return jsonify({"error": "Database write handling failure occurred."}), 500

    except Exception as e:
        conn.rollback()
        print(f"Runtime Mutation Process Exception: {e}")
        return jsonify({"error": "Internal ledger mutation system error"}), 500

    finally:
        cursor.close()


@app.route("/api/routes/<int:route_id>", methods=["PUT"])
def api_update_route(route_id):
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized Access"}), 401

    if session.get("role") not in ["admin", "superadmin"]:
        return jsonify({"error": "Forbidden: Administrative privileges required"}), 403

    data = request.get_json() or {}

    train_id = data.get("train_id")
    departure_station_id = data.get("departure_station_id")
    arrival_station_id = data.get("arrival_station_id")
    departure_time = data.get("departure_time")
    arrival_time = data.get("arrival_time")
    ticket_price = data.get("ticket_price")

    if (
        not all(
            [
                train_id,
                departure_station_id,
                arrival_station_id,
                departure_time,
                arrival_time,
            ]
        )
        or ticket_price is None
    ):
        return jsonify({"error": "Missing mandatory scheduling parameters"}), 400

    if int(departure_station_id) == int(arrival_station_id):
        return jsonify(
            {
                "error": "Mutation Error: Departure and arrival node assignments cannot be identical"
            }
        ), 400

    conn = mysql.connection
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT route_id FROM Route WHERE route_id = %s", (route_id,))
        if not cursor.fetchone():
            return jsonify(
                {"error": f"Target route ID #{route_id} not found in tracking indexes."}
            ), 404

        update_query = """
            UPDATE Route
            SET
                train_id = %s,
                departure_station_id = %s,
                arrival_station_id = %s,
                departure_time = %s,
                arrival_time = %s,
                ticket_price = %s
            WHERE route_id = %s
        """
        params = (
            int(train_id),
            int(departure_station_id),
            int(arrival_station_id),
            str(departure_time),
            str(arrival_time),
            float(ticket_price),
            int(route_id),
        )

        cursor.execute(update_query, params)
        conn.commit()

        return jsonify(
            {
                "ok": True,
                "message": f"Transit route #{route_id} configuration adjustments committed successfully.",
            }
        ), 200

    except MySQLdb.Error as db_err:
        conn.rollback()
        if db_err.args[0] == 1452:
            return jsonify(
                {
                    "error": "Foreign Key violation: Specified station nodes or locomotive asset references do not exist."
                }
            ), 422

        print(f"Database Schedule Update Crash [ID {route_id}]: {db_err}")
        return jsonify(
            {"error": "Database write modification handling failure occurred."}
        ), 500

    except Exception as e:
        conn.rollback()
        print(f"Runtime Update Modification Process Exception: {e}")
        return jsonify({"error": "Internal ledger mutation system error"}), 500

    finally:
        cursor.close()


# --- API Layer: Purchases / Tickets ---
@app.route("/api/purchases", methods=["GET"])
@login_required
def api_purchases():
    conn = mysql.connection
    cursor = conn.cursor(MySQLdb.cursors.DictCursor)

    try:
        if session["role"] == "user":
            query = """
                SELECT t.ticket_id, t.status, t.purchase_date,
                       pa.first_name, pa.last_name, u.email,
                       s1.station_name as dep_name, s2.station_name as arr_name,
                       CAST(r.departure_time AS CHAR) as departure_time,
                       CAST(r.arrival_time AS CHAR) as arrival_time,
                       r.ticket_price, tr.train_name
                FROM Ticket t
                JOIN Passenger pa ON t.passenger_id = pa.passenger_id
                JOIN Users u ON pa.user_id = u.user_id
                JOIN Route r ON t.route_id = r.route_id
                JOIN Station s1 ON r.departure_station_id = s1.station_id
                JOIN Station s2 ON r.arrival_station_id = s2.station_id
                LEFT JOIN Train tr ON r.train_id = tr.train_id
                WHERE pa.user_id = %s
                ORDER BY t.ticket_id DESC
            """
            cursor.execute(query, (session["user_id"],))
        else:
            query = """
                SELECT t.ticket_id, t.status, t.purchase_date,
                       pa.first_name, pa.last_name, u.email,
                       s1.station_name as dep_name, s2.station_name as arr_name,
                       CAST(r.departure_time AS CHAR) as departure_time,
                       CAST(r.arrival_time AS CHAR) as arrival_time,
                       r.ticket_price, tr.train_name
                FROM Ticket t
                JOIN Passenger pa ON t.passenger_id = pa.passenger_id
                JOIN Users u ON pa.user_id = u.user_id
                JOIN Route r ON t.route_id = r.route_id
                JOIN Station s1 ON r.departure_station_id = s1.station_id
                JOIN Station s2 ON r.arrival_station_id = s2.station_id
                LEFT JOIN Train tr ON r.train_id = tr.train_id
                ORDER BY t.ticket_id DESC
            """
            cursor.execute(query)

        rows = cursor.fetchall()

        for row in rows:
            if row.get("purchase_date"):
                row["purchase_date"] = str(row["purchase_date"])
            row["ticket_price"] = (
                float(row["ticket_price"]) if row.get("ticket_price") else 0.0
            )
            if not row.get("train_name"):
                row["train_name"] = "Commuter Shuttle Line"

        return jsonify(rows), 200

    except Exception as e:
        print(f"DATABASE DESCRIPTOR FAULT LOG: {e}")
        return jsonify({"error": "Failed to sync structural schema data values."}), 500
    finally:
        cursor.close()


@app.route("/api/purchases/<int:tid>/status", methods=["PUT"])
@login_required
def api_update_purchase_status(tid):
    data = request.json or {}
    new_status = data.get("status")

    if new_status not in ["pending", "paid", "canceled"]:
        return jsonify({"error": "Invalid status option submitted."}), 400

    conn = mysql.connection
    cursor = conn.cursor(MySQLdb.cursors.DictCursor)

    try:
        if session["role"] == "user":
            check_query = """
                SELECT t.status, pa.user_id
                FROM Ticket t
                JOIN Passenger pa ON t.passenger_id = pa.passenger_id
                WHERE t.ticket_id = %s
            """
            cursor.execute(check_query, (tid,))
            ticket = cursor.fetchone()

            if not ticket or ticket["user_id"] != session["user_id"]:
                return jsonify(
                    {"error": "Unauthorized record request modification denied."}
                ), 403

            if ticket["status"] != "pending":
                return jsonify(
                    {"error": "Only pending tickets can be modified by passengers."}
                ), 400

        update_query = "UPDATE Ticket SET status = %s WHERE ticket_id = %s"
        cursor.execute(update_query, (new_status, tid))
        conn.commit()

        return jsonify(
            {"ok": True, "message": "Ticket status updated successfully."}
        ), 200
    except Exception as e:
        conn.rollback()
        print(f"Status Alteration Error: {e}")
        return jsonify({"error": "Database write execution error."}), 500
    finally:
        cursor.close()


@app.route("/api/purchases/<int:tid>", methods=["DELETE"])
@admin_required
def api_delete_purchase(tid):
    conn = mysql.connection
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Ticket WHERE ticket_id = %s", (tid,))
        conn.commit()
        return jsonify({"ok": True, "message": "Ticket successfully deleted."}), 200
    except Exception as e:
        conn.rollback()
        print(f"Error purging record context: {e}")
        return jsonify({"error": "Database deletion error"}), 500
    finally:
        cursor.close()


@app.route("/api/book", methods=["POST"])
@login_required
def api_book():
    if "user_id" not in session:
        return jsonify(
            {"error": "Authentication required. Please re-authenticate."}
        ), 401

    data = request.json or {}
    route_id = data.get("route_id")

    if not route_id:
        return jsonify({"error": "Missing valid route payload parameter."}), 400

    conn = mysql.connection
    cursor = conn.cursor(MySQLdb.cursors.DictCursor)

    try:
        cursor.execute(
            "SELECT passenger_id FROM Passenger WHERE user_id = %s",
            (session["user_id"],),
        )
        passenger = cursor.fetchone()

        if not passenger:
            return jsonify(
                {"error": "Passenger ledger profile not found for this account."}
            ), 404

        cursor.execute("SELECT route_id FROM Route WHERE route_id = %s", (route_id,))
        route_exists = cursor.fetchone()

        if not route_exists:
            return jsonify(
                {"error": "The selected transit route line could not be verified."}
            ), 404

        booking_query = "INSERT INTO Ticket (passenger_id, route_id) VALUES (%s, %s)"
        cursor.execute(booking_query, (passenger["passenger_id"], route_id))
        conn.commit()

        return jsonify({"ok": True, "message": "Ticket successfully provisioned."}), 200
    except Exception as e:
        conn.rollback()
        print(f"CRITICAL SYSTEM BOOKING CRASH: {e}")
        return jsonify({"error": "Internal ledger commit transaction failure."}), 500
    finally:
        cursor.close()

# --- API Layer: Trains ---
@app.route("/api/trains", methods=["GET"])
@admin_required
def api_trains_get():
    with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as c:
        c.execute("SELECT * FROM Train ORDER BY train_id DESC")
        rows = c.fetchall()
    return jsonify(rows), 200

@app.route("/api/trains", methods=["POST"])
@admin_required
def api_train_create():
    d = request.json or {}
    name = d.get("train_name", "").strip()
    ttype = d.get("train_type", "").strip()
    seats = d.get("total_seats")

    if not name or not ttype or not seats:
        return jsonify(
            {"error": "Required fields: train_name, train_type, total_seats."}
        ), 400

    with mysql.connection.cursor() as c:
        c.execute(
            "INSERT INTO Train (train_name, train_type, total_seats) VALUES (%s, %s, %s)",
            (name, ttype, int(seats)),
        )
        mysql.connection.commit()
    return jsonify({"ok": True, "message": "Train engine added to matrix layout."}), 201

@app.route("/api/trains/<int:tid>", methods=["PUT"])
@admin_required
def api_train_update(tid):
    d = request.json or {}
    name = d.get("train_name", "").strip()
    ttype = d.get("train_type", "").strip()
    seats = d.get("total_seats")

    if not name or not ttype or not seats:
        return jsonify({"error": "All updated fields must remain complete."}), 400

    with mysql.connection.cursor() as c:
        c.execute(
            "UPDATE Train SET train_name=%s, train_type=%s, total_seats=%s WHERE train_id=%s",
            (name, ttype, int(seats), tid),
        )
        mysql.connection.commit()
    return jsonify({"ok": True, "message": "Train records adjusted successfully."}), 200

@app.route("/api/trains/<int:tid>", methods=["DELETE"])
@admin_required
def api_train_delete(tid):
    with mysql.connection.cursor() as c:
        c.execute("DELETE FROM Train WHERE train_id = %s", (tid,))
        mysql.connection.commit()
    return jsonify({"ok": True, "message": "Train fleet allocation cleared."}), 200


# --- API layer: User (Superadmin Only) ---
@app.route("/api/users", methods=["GET"])
@superadmin_required
def api_users_get():
    query = """
        SELECT u.user_id, u.email, u.role, p.first_name, p.last_name, p.phone_no
        FROM Users u
        LEFT JOIN Passenger p ON u.user_id = p.user_id
        ORDER BY u.user_id ASC
    """
    with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as c:
        c.execute(query)
        rows = c.fetchall()
    return jsonify(rows), 200


@app.route("/api/users", methods=["POST"])
@superadmin_required
def api_user_create():
    d = request.json or {}
    email = d.get("email", "").strip()
    password = d.get("password", "")
    role = d.get("role", "user")
    first_name = d.get("first_name", "").strip()
    last_name = d.get("last_name", "").strip()
    phone_no = d.get("phone_no", None)

    if not email or not password or not first_name or not last_name:
        return jsonify({"error": "Missing essential profile values."}), 400
    if role not in ["superadmin", "admin", "user"]:
        return jsonify({"error": "Invalid role validation parameter."}), 400

    conn = mysql.connection
    cursor = conn.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute("SELECT user_id FROM Users WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({"error": "Identity collision error. Email exists."}), 400

        hashed_password = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO Users (email, password_hash, role) VALUES (%s, %s, %s)",
            (email, hashed_password, role),
        )
        new_uid = cursor.lastrowid

        cursor.execute(
            "INSERT INTO Passenger (user_id, first_name, last_name, phone_no) VALUES (%s, %s, %s, %s)",
            (new_uid, first_name, last_name, phone_no),
        )
        conn.commit()
        return jsonify({"ok": True, "message": "System user account initialized."}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error": f"Transaction aborted: {e}"}), 500
    finally:
        cursor.close()


@app.route("/api/users/<int:uid>", methods=["PUT"])
@superadmin_required
def api_user_update(uid):
    d = request.json or {}
    email = d.get("email", "").strip()
    role = d.get("role")
    first_name = d.get("first_name", "").strip()
    last_name = d.get("last_name", "").strip()
    phone_no = d.get("phone_no", None)
    password = d.get("password", "")  # Optional field update check

    if not email or not role or not first_name or not last_name:
        return jsonify({"error": "Identity fields cannot remain blank."}), 400
    if role not in ["superadmin", "admin", "user"]:
        return jsonify({"error": "Unsupported permission tier assigned."}), 400

    conn = mysql.connection
    cursor = conn.cursor()
    try:
        if uid == session.get("user_id") and role != "superadmin":
            return jsonify(
                {"error": "Security lock error: Self-demotion is restricted."}
            ), 400

        if password:
            hashed_p = generate_password_hash(password)
            cursor.execute(
                "UPDATE Users SET email=%s, password_hash=%s, role=%s WHERE user_id=%s",
                (email, hashed_p, role, uid),
            )
        else:
            cursor.execute(
                "UPDATE Users SET email=%s, role=%s WHERE user_id=%s",
                (email, role, uid),
            )

        cursor.execute(
            "UPDATE Passenger SET first_name=%s, last_name=%s, phone_no=%s WHERE user_id=%s",
            (first_name, last_name, phone_no, uid),
        )
        conn.commit()
        return jsonify(
            {"ok": True, "message": "Account metrics saved modifications."}
        ), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": f"Write modifications failed: {e}"}), 500
    finally:
        cursor.close()


@app.route("/api/users/<int:uid>", methods=["DELETE"])
@superadmin_required
def api_user_delete(uid):
    if uid == session.get("user_id"):
        return jsonify(
            {"error": "Security violation: Deletion of own active session is blocked."}
        ), 400

    conn = mysql.connection
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Users WHERE user_id = %s", (uid,))
        conn.commit()
        return jsonify({"ok": True, "message": "Identity dropped from registry."}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": f"Purging routine failed: {e}"}), 500
    finally:
        cursor.close()


if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(debug=True, port=5000)
