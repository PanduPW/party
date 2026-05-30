import os

import MySQLdb
import MySQLdb.cursors
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from flask_mysqldb import MySQL

load_dotenv()

app = Flask(__name__)

app.config["MYSQL_HOST"] = os.getenv("MYSQL_HOST", "localhost")
app.config["MYSQL_USER"] = os.getenv("MYSQL_USER", "root")
app.config["MYSQL_PASSWORD"] = os.getenv("MYSQL_PASSWORD", "")
# app.config["MYSQL_DB"] = os.getenv("MYSQL_DB", "railway_system")


mysql = MySQL(app)


def init_db():
    schema_path = os.path.join("database", "schema.sql")
    seed_path = os.path.join("database", "seed.sql")

    if not os.path.exists(schema_path):
        return

    with app.app_context():
        conn = mysql.connection
        cursor = conn.cursor()
        try:
            with open(schema_path, "r") as f:
                schema_commands = [
                    cmd.strip() for cmd in f.read().split(";") if cmd.strip()
                ]

            for command in schema_commands:
                cursor.execute(command)
            conn.commit()

            conn.select_db("railway_system")

            cursor.execute("SELECT COUNT(*) FROM Station")
            has_data = cursor.fetchone()[0] > 0

            if not has_data and os.path.exists(seed_path):
                with open(seed_path, "r") as f:
                    seed_commands = [
                        cmd.strip() for cmd in f.read().split(";") if cmd.strip()
                    ]

                for command in seed_commands:
                    cursor.execute(command)
                conn.commit()
                print("Database initialized and seeded successfully.")
            else:
                print(
                    "Database initialized. Seeding skipped because data already exists."
                )

        except Exception as e:
            conn.rollback()
            print(f"Database Initialization Error: {e}")
        finally:
            cursor.close()

            app.config["MYSQL_DB"] = "railway_system"


# Pages
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/trains")
def trains():
    return render_template("trains.html")


@app.route("/stations")
def stations():
    return render_template("stations.html")


@app.route("/routes")
def routes():
    return render_template("routes.html")


@app.route("/purchases")
def purchases():
    return render_template("purchases.html")


@app.route("/book")
def book():
    return render_template("book.html")


# API: Trains
@app.route("/api/trains", methods=["GET"])
def api_trains():
    with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as c:
        c.execute("SELECT * FROM train")
        trains = c.fetchall()

    for t in trains:
        t["ticket_price"] = float(t["ticket_price"])

    return jsonify(trains)


@app.route("/api/trains", methods=["POST"])
def api_train_create():
    d = request.json
    with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as c:
        c.execute(
            "INSERT INTO train (train_name,total_seats,train_type,ticket_price) VALUES (%s,%s,%s,%s)",
            (
                d["train_name"],
                d["total_seats"],
                d["train_type"],
                d["ticket_price"],
            ),
        )
        mysql.connection.commit()
    return jsonify({"ok": True})


@app.route("/api/trains/<int:tid>", methods=["PUT"])
def api_train_update(tid):
    d = request.json
    with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as c:
        c.execute(
            "UPDATE train SET train_name=%s,total_seats=%s,train_type=%s,ticket_price=%s WHERE train_id=%s",
            (
                d["train_name"],
                d["total_seats"],
                d["train_type"],
                d["ticket_price"],
                tid,
            ),
        )
        mysql.connection.commit()
    return jsonify({"ok": True})


@app.route("/api/trains/<int:tid>", methods=["DELETE"])
def api_train_delete(tid):
    with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as c:
        c.execute("DELETE FROM train WHERE train_id=%s", (tid,))
        mysql.connection.commit()
    return jsonify({"ok": True})


# API: Stations
@app.route("/api/stations", methods=["GET"])
def api_stations():
    with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as c:
        c.execute("SELECT * FROM station")
        rows = c.fetchall()
    return jsonify(rows)


@app.route("/api/stations", methods=["POST"])
def api_station_create():
    d = request.json
    with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as c:
        c.execute(
            "INSERT INTO station (station_name,city,state_name) VALUES (%s,%s,%s)",
            (d["station_name"], d["city"], d["state_name"]),
        )
        mysql.connection.commit()
    return jsonify({"ok": True})


@app.route("/api/stations/<int:sid>", methods=["PUT"])
def api_station_update(sid):
    d = request.json
    with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as c:
        c.execute(
            "UPDATE station SET station_name=%s,city=%s,state_name=%s WHERE station_id=%s",
            (d["station_name"], d["city"], d["state_name"], sid),
        )
        mysql.connection.commit()
    return jsonify({"ok": True})


@app.route("/api/stations/<int:sid>", methods=["DELETE"])
def api_station_delete(sid):
    with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as c:
        c.execute("DELETE FROM station WHERE station_id=%s", (sid,))
        mysql.connection.commit()
    return jsonify({"ok": True})


# API: Routes
@app.route("/api/routes", methods=["GET"])
def api_routes():
    with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as c:
        c.execute("""
            SELECT r.route_id, r.departure_time, r.arrival_time, r.train_id,
                   s1.station_name as dep_name, s1.city as dep_city,
                   s2.station_name as arr_name, s2.city as arr_city,
                   t.train_name, t.ticket_price,
                   r.departure_station_id, r.arrival_station_id
            FROM route r
            JOIN station s1 ON r.departure_station_id=s1.station_id
            JOIN station s2 ON r.arrival_station_id=s2.station_id
            LEFT JOIN train t ON r.train_id=t.train_id
        """)
        rows = c.fetchall()

    for row in rows:
        if "departure_time" in row and row["departure_time"]:
            row["departure_time"] = str(row["departure_time"])
        if "arrival_time" in row and row["arrival_time"]:
            row["arrival_time"] = str(row["arrival_time"])
        if "ticket_price" in row and row["ticket_price"]:
            row["ticket_price"] = float(row["ticket_price"])

    return jsonify(rows)


@app.route("/api/routes", methods=["POST"])
def api_route_create():
    d = request.json
    with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as c:
        c.execute(
            "INSERT INTO route (departure_station_id,arrival_station_id,departure_time,arrival_time,train_id) VALUES (%s,%s,%s,%s,%s)",
            (
                d["departure_station_id"],
                d["arrival_station_id"],
                d["departure_time"],
                d["arrival_time"],
                d.get("train_id"),
            ),
        )
        mysql.connection.commit()
    return jsonify({"ok": True})


@app.route("/api/routes/<int:rid>", methods=["PUT"])
def api_route_update(rid):
    d = request.json
    with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as c:
        c.execute(
            "UPDATE route SET departure_station_id=%s,arrival_station_id=%s,departure_time=%s,arrival_time=%s,train_id=%s WHERE route_id=%s",
            (
                d["departure_station_id"],
                d["arrival_station_id"],
                d["departure_time"],
                d["arrival_time"],
                d.get("train_id"),
                rid,
            ),
        )
        mysql.connection.commit()
    return jsonify({"ok": True})


@app.route("/api/routes/<int:rid>", methods=["DELETE"])
def api_route_delete(rid):
    with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as c:
        c.execute("DELETE FROM route WHERE route_id=%s", (rid,))
        mysql.connection.commit()
    return jsonify({"ok": True})


# API: Purchases
@app.route("/api/purchases", methods=["GET"])
def api_purchases():
    with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as c:
        c.execute("""
            SELECT p.purchase_id, p.seat_no, p.purchase_date_status, p.status,
                   pa.first_name, pa.last_name, pa.email,
                   s1.station_name as dep_name, s2.station_name as arr_name,
                   r.departure_time, r.arrival_time,
                   t.train_name, t.ticket_price,
                   p.passenger_id, p.route_id
            FROM purchase p
            JOIN passenger pa ON p.passenger_id=pa.passenger_id
            JOIN route r ON p.route_id=r.route_id
            JOIN station s1 ON r.departure_station_id=s1.station_id
            JOIN station s2 ON r.arrival_station_id=s2.station_id
            LEFT JOIN train t ON r.train_id=t.train_id
            ORDER BY p.purchase_id DESC
        """)
        rows = c.fetchall()

    for row in rows:
        if "purchase_date_status" in row and row["purchase_date_status"]:
            row["purchase_date_status"] = str(row["purchase_date_status"])
        if "departure_time" in row and row["departure_time"]:
            row["departure_time"] = str(row["departure_time"])
        if "arrival_time" in row and row["arrival_time"]:
            row["arrival_time"] = str(row["arrival_time"])
        if "ticket_price" in row and row["ticket_price"]:
            row["ticket_price"] = float(row["ticket_price"])

    return jsonify(rows)


@app.route("/api/purchases/<int:pid>/status", methods=["PUT"])
def api_purchase_status(pid):
    d = request.json
    with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as c:
        c.execute(
            "UPDATE purchase SET status=%s WHERE purchase_id=%s",
            (d["status"], pid),
        )
        mysql.connection.commit()
    return jsonify({"ok": True})


@app.route("/api/purchases/<int:pid>", methods=["DELETE"])
def api_purchase_delete(pid):
    with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as c:
        c.execute("DELETE FROM purchase WHERE purchase_id=%s", (pid,))
        mysql.connection.commit()
    return jsonify({"ok": True})


# API: Book ticket
@app.route("/api/book", methods=["POST"])
def api_book():
    d = request.json
    with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as c:
        c.execute("SELECT passenger_id FROM passenger WHERE email=%s", (d["email"],))
        existing = c.fetchone()

        if existing:
            pid = existing["passenger_id"]
            c.execute(
                "UPDATE passenger SET first_name=%s,last_name=%s,phone_no=%s WHERE passenger_id=%s",
                (d["first_name"], d["last_name"], d.get("phone_no"), pid),
            )
        else:
            c.execute(
                "INSERT INTO passenger (first_name,last_name,email,phone_no) VALUES (%s,%s,%s,%s)",
                (
                    d["first_name"],
                    d["last_name"],
                    d["email"],
                    d.get("phone_no"),
                ),
            )
            pid = c.lastrowid

        c.execute(
            "INSERT INTO purchase (passenger_id,route_id,seat_no,purchase_date_status,status) VALUES (%s,%s,%s,CURRENT_DATE,'pending')",
            (pid, d["route_id"], d["seat_no"]),
        )
        mysql.connection.commit()

    return jsonify({"ok": True})


if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(debug=True, port=5000)
