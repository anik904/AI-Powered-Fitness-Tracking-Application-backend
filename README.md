# AI Fitness Tracker — Backend API

## 1. Prerequisites

- **Python 3.10+**
- **MySQL 8.0+** (`brew install mysql`)


## 2. Start MySQL Server

Control your local MySQL service:

```bash
# Start MySQL
brew services start mysql

# Stop MySQL
brew services stop mysql
```

---

## 3. Database Setup

Log into MySQL:

```bash
mysql -u root -p
```

Run:

```sql
CREATE DATABASE IF NOT EXISTS fitness_tracker CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;
```

---

## 4. Environment Configuration

Copy the sample environment file:

```bash
cp .env.example .env
```

Ensure your database connection string in `.env` is correct:

```env
DATABASE_URL=mysql+aiomysql://root:123456@localhost:3306/fitness_tracker
```

---

## 5. Installation & Setup

1. **Create and activate virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## 6. Run the Service

Start the backend server:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

> Tables are created automatically in the database upon startup.

---

## 7. Access Swagger API Docs

Once the server is running, open your browser:

- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)


