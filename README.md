# party

---

## usage

```bash
python -m venv .venv
```

## Activate Virtual Environment

### Windows

```bash
.venv\Scripts\activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Setup Environment Variables

Copy the example environment file:

### Windows

```bash
copy .env.example .env
```

Then edit the `.env` file.
```py
MYSQL_HOST=localhost
MYSQL_USER=saki
MYSQL_PASSWORD=saki
MYSQL_DB=railway_system
```

---

# Run the Application

```bash
python app.py
```

The app will run on:

```text
http://127.0.0.1:5000
```

---

Make sure:

* `.env` file exists
* required variables are filled correctly
