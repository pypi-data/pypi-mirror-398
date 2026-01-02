# SQL LogFire 🔥

A lightweight, self-hosted logging system built on top of **your existing SQL database**.

**SQL LogFire** is a drop-in alternative to tools like Graylog or Datadog for small teams and startups.
It stores logs using **SQLAlchemy (sync engine only)** and provides an **embedded FastAPI dashboard** to view and search logs in real time.

---

## ✨ Features

* ✅ Uses **your existing SQL database** (PostgreSQL, MySQL, SQLite)
* ✅ **Non-blocking logging** via background worker thread
* ✅ Zero external services (no Elasticsearch, Kafka, agents)
* ✅ Embedded **FastAPI dashboard**
* ✅ Simple API: `logfire.log("message")`
* ✅ Automatic table creation
* ✅ Search & time-based filtering
* ❌ No async engine (by design, for stability)

---

## 📦 Installation

```bash
pip install sql-logfire
```

### Optional (PostgreSQL support)

```bash
pip install sql-logfire[postgres]
```

---

## ⚠️ Important Design Note

> **SQL LogFire supports ONLY synchronous SQLAlchemy engines**

Async engines (`asyncpg`, `create_async_engine`) are **not supported** and will raise errors.

This is intentional:

* Logging happens in a **background thread**
* Sync engines are **thread-safe and stable**
* No `greenlet` / async context issues

---

## 🚀 Quick Start (FastAPI)

### 1️⃣ Create the Database Engine (SYNC)

```python
from sqlalchemy import create_engine

DATABASE_URL = "postgresql+psycopg2://postgres:password@localhost:5432/postgres"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    future=True
)
```

---

### 2️⃣ Initialize LogFire

```python
from sql_logfire.core import LogFire

logfire = LogFire(engine)
```

This will:

* Automatically create required tables
* Start a background worker thread
* Prepare the dashboard

---

### 3️⃣ Mount the Dashboard in FastAPI

```python
from fastapi import FastAPI
from sql_logfire.integrations.fastapi import create_logfire_router

app = FastAPI()

app.include_router(
    create_logfire_router(logfire),
    prefix="/logfire",
    tags=["LogFire"]
)
```

📍 Dashboard available at:

```
http://localhost:8000/logfire
```

---

### 4️⃣ Start Logging 🎉

```python
@app.get("/")
def root():
    logfire.log("User accessed root endpoint", level="INFO")
    return {"status": "ok"}

@app.get("/error")
def error():
    logfire.log("Critical payment failure detected!", level="ERROR")
    return {"status": "error"}
```

---

## 🔍 Dashboard Features

* View latest logs
* Filter by:

  * Log level
  * Time window (last N minutes)
  * Search query
* Auto-refresh
* Clean, minimal UI

*No Swagger. No setup. Just `/logfire`.*

---

## 🗄️ Supported Databases

| Database   | Supported |
| ---------- | --------- |
| SQLite     | ✅         |
| PostgreSQL | ✅         |
| MySQL      | ✅         |
| Async DBs  | ❌         |

---

## 🧠 Why Sync Only?

Logging systems must be:

* **Reliable**
* **Non-blocking**
* **Thread-safe**

Async engines require an event loop and break in:

* Background threads
* WSGI / hybrid environments
* Sync frameworks

SQL LogFire chooses **correctness over complexity**.

---

## 🧹 Graceful Shutdown (Optional)

```python
@app.on_event("shutdown")
def shutdown():
    logfire.shutdown()
```

This ensures all queued logs are flushed before exit.

---

## 📚 Example Database URLS

### SQLite

```text
sqlite:///./logfire.db
```

### PostgreSQL

```text
postgresql+psycopg2://user:password@localhost:5432/db
```

### MySQL

```text
mysql+pymysql://user:password@localhost:3306/db
```

---

## 🧪 When Should You Use SQL LogFire?

✅ Internal tools
✅ MVPs & startups
✅ Self-hosted environments
✅ Compliance-sensitive data
✅ Teams avoiding SaaS logging costs

❌ Massive distributed tracing
❌ Billions of logs/day
❌ Fully async logging pipelines

---

## 🛣️ Roadmap

* [ ] Log retention policies
* [ ] Export logs (CSV / JSON)
* [ ] Auth for dashboard
* [ ] Metrics aggregation
* [ ] Alert rules

---

## 🧑‍💻 Author

**Bittu Singh**
📧 [bittusinghtech@gmail.com](mailto:bittusinghtech@gmail.com)
🔗 [https://github.com/Bittu2903](https://github.com/Bittu2903)

---
