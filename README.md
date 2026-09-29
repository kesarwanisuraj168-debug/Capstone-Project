# Smart Campus Occupancy Forecasting with Spatiotemporal Analytics & Capacity Optimization

CampusPulse is a capstone project for forecasting room occupancy and exploring campus utilization. It combines a FastAPI backend, a browser-based dashboard, scikit-learn/gradient-boosting models, and a PuLP room-allocation optimizer. The included occupancy history is synthetic demonstration data, not measurements from a real campus.

---

## 🌟 Key Platform Capabilities

1. **Machine Learning Forecasting**:
   - Multiple regression architectures: **XGBoost** ($R^2 \approx 0.960$), **LightGBM** ($R^2 \approx 0.960$), **Random Forest** ($R^2 \approx 0.941$), and **Linear Regression** baseline ($R^2 \approx 0.879$), with optional **Keras LSTM**.
   - Chronological 85/15 train-test split preventing target leakage and temporal overlap.
   - Building, room, campus, peak-hour, and full-day forecasts for the 08:00-20:00 operating window.
   - Optional LSTM inference support when its separate model artifacts and TensorFlow dependency are installed.

2. **Spatiotemporal Analytics**:
   - Interactive Day-of-Week vs. Hour campus density heatmaps powered by Plotly.
   - Building vs. Time utilization heatmaps.
   - Interactive 2D Campus Spatial Visualization showing building coordinates, utilization status, and room inventories.
   - 14-day historical recorded vs. forecasted tracking.

3. **Capacity Optimization Engine (PuLP MILP)**:
   - Mixed-Integer Linear Programming solved with CBC solver.
   - Mathematically guaranteed feasibility via slack penalty variables (never crashes even if requests exceed available rooms).
   - Hard constraint checking against active scheduled classes from the campus `timetable` to prevent double-booking.
   - Minimizes empty seats, switching penalties, movement distance, and equipment mismatch.

4. **Real-World Data Ingestion Pipeline**:
   - Drag-and-drop CSV and Excel (`.xlsx`, `.xls`) upload with alias mapping (`timestamp`, `room`, `occupancy`, `capacity`, `floor`, etc.).
   - Explicit origin tracking: `synthetic` (demonstration data), `imported` (attendance/historical files), and `measured` (sensor/turnstile feed).
   - Validation against negative counts, capacity warnings, duplicate detection, and missing-value handling.
   - A clearly labeled simulated sensor-stream endpoint for demonstrations; no physical IoT hardware is included.

5. **Security & Role-Based Authorization**:
   - PBKDF2-HMAC-SHA256 password hashing (120,000 iterations).
   - JWT session management with `require_user` and `require_admin` authorization guards.
   - Administrator-only model retraining; the dashboard also supports guest/demo use.

6. **Automated Testing Suite**:
   - Full automated Pytest suite (`tests/`) covering authentication, forecasting, optimization, dataset ingestion, and analytics.

---

## 🏗️ Project Architecture

```
Capstone-Project-main/
├── backend/
│   ├── main.py             # FastAPI app, static mounting, lifespan setup
│   ├── config.py           # Central settings, paths, JWT secret, operating hours
│   ├── database.py         # SQLAlchemy engine, session maker, get_db dependency
│   ├── deps.py             # Auth dependencies (optional_user, require_user, require_admin)
│   ├── models.py           # ORM models (User, Building, Room, Occupancy, Timetable, etc.)
│   ├── schemas.py          # Pydantic v2 validation models
│   ├── security.py         # PBKDF2 password hashing & JWT encode/decode
│   ├── seed.py             # Database auto-seeder (structures, 69,290 records, demo users)
│   ├── routes/
│   │   ├── auth.py         # User registration, login, profile (/api/auth)
│   │   ├── occupancy.py    # Campus & room inventory, historical slices (/api/occupancy)
│   │   ├── prediction.py   # Forecasts, day curves, model comparison, retrain (/api/predict)
│   │   ├── optimization.py # PuLP MILP room allocation engine (/api/optimize)
│   │   ├── dashboard.py    # Aggregated KPI cards & trend lines (/api/dashboard)
│   │   ├── dataset.py      # CSV/Excel upload, validation, preview, simulation (/api/dataset)
│   │   └── analytics.py    # DOW/Building heatmaps, 2D spatial map, tracking (/api/analytics)
│   └── services/
│       ├── forecasting.py  # Model inference, lag chaining, confidence intervals
│       └── optimizer.py    # PuLP MILP formulation with slack dummy variables & timetable checks
├── frontend/
│   ├── index.html          # SPA dashboard containing 10 interactive views
│   └── static/
│       ├── css/app.css     # Clean modern CSS with cards, badges, and responsive grids
│       └── js/app.js       # Client controller, auth storage, Plotly rendering, CSV export
├── ml/
│   ├── generate_dataset.py # Synthetic campus dataset generator
│   ├── preprocessing.py    # Feature engineering (lags, calendar, weather)
│   ├── train_model.py      # Trains & saves LR, RF, LightGBM, XGBoost models
│   ├── evaluate.py         # Evaluates model performance on test hold-out
│   ├── dataset.csv         # 69,290 hourly raw occupancy records
│   ├── dataset_features.csv# Engineered ML feature matrix
│   └── models/             # Serialized joblib artifacts & metadata
├── database/
│   └── schema.sql          # MySQL 8 reference schema (SQLite used by default)
├── tests/                  # Automated pytest test suites
└── requirements.txt        # Python dependency manifest
```

---

## ⚡ Quick Start (Windows)

### Option A: 1-Click Launch (Recommended)
1. **Initial Setup (one-time):** Run [`setup.bat`](setup.bat) to create the virtual environment, install dependencies, verify model artifacts, seed the database, and run the tests.
2. **Start Application:** Run [`run.bat`](run.bat) to start the server and open the dashboard in your default browser. [`START.bat`](START.bat) combines setup and launch for first-time use.

---

### Option B: Manual Terminal Execution (PowerShell)

### 1. Prerequisites
Install **Python 3.11 or newer** and run the commands from the repository root.

### 2. Install Dependencies
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Run Automated Tests
```powershell
python -m pytest tests/ -v
```
*(All 18 unit & integration tests should pass successfully).*

### 4. Start the Application Server
```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```
On startup, the app creates the SQLite database (`campus.db`) and seeds it with the included buildings, rooms, occupancy history, timetable, events, and demo accounts when those tables are empty.

### 5. Access the Platform
- **Interactive Web Dashboard**: [http://localhost:8000/](http://localhost:8000/)
- **Interactive Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **API Health Check**: [http://localhost:8000/api/health](http://localhost:8000/api/health) (also available at `/health`)

---

## 🔑 Demo Login Accounts

| Role | Username | Password | Permissions |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin` | `admin123` | Administrator-only model retraining |
| **Standard User** | `user` | `user123` | Standard signed-in account for dashboard workflows |

*(You can also use the application in Guest / Demo Mode without signing in).*

---

## 📊 Model Evaluation Results

Models were evaluated on a strictly chronological **15% hold-out test set (10,394 unseen samples)** from `ml/dataset_features.csv`:

| Model Architecture | MAE (Mean Abs Error) | RMSE | MAPE (%) | $R^2$ Score | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **LightGBM Regressor** | **6.84** | **12.13** | 67.42% | **0.9604** | ⭐ Primary Recommendation |
| **XGBoost Regressor** | **7.01** | **12.23** | 64.89% | **0.9598** | ⭐ Default Active Model |
| **Random Forest** | 7.72 | 14.74 | 64.23% | 0.9415 | Production Ready |
| **Linear Regression** | 12.63 | 21.24 | 178.81% | 0.8787 | Baseline |

> [!NOTE]
> **Data Transparency Disclaimer**: The default historical dataset is structured synthetic demonstration data. While statistical metrics confirm high algorithm convergence ($R^2 \approx 0.96$), real-world campus deployment requires sensor calibration and attendance register validation.

---

## 📥 Real-World Data Ingestion & Supported Columns

The platform accepts **CSV** and **Excel (`.xlsx`, `.xls`)** files via the dashboard or `POST /api/dataset/upload`. The upload endpoint defaults the origin to `imported`; callers may explicitly choose `imported`, `measured`, or `synthetic`.

### Supported Columns (Case-insensitive aliases supported):
- **Date / Timestamp**: `date` (`YYYY-MM-DD`) or `timestamp` (`YYYY-MM-DD HH:MM:SS`)
- **Hour**: `hour` (Integer `0`–`23`, valid operating slots `8`–`20`)
- **Room**: `room` or `room_code` (e.g. `A-101`, `B-Ref`, `D-201`)
- **Occupancy Count**: `occupancy` or `count` (Non-negative integer)
- **Capacity (Optional)**: `capacity` or `seats`
- **Room Type (Optional)**: `classroom`, `lab`, `library`, `meeting`, `cafeteria`, `auditorium`
- **Floor (Optional)**: `floor` (Integer)
- **Students / Staff (Optional)**: `students_count`, `staff_count`
- **Course / Scheduled Class (Optional)**: `scheduled_class`

Download the ready-to-use sample template from the dashboard or at `/api/dataset/template`.

---

## Configuration and Data Notes

The database defaults to a SQLite file at the project root. Set these environment variables before starting the server to override the defaults:

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `CAMPUS_DATABASE_URL` | `sqlite:///{project root}/campus.db` | SQLAlchemy database URL; a MySQL URL can be used with the included `pymysql` dependency. |
| `CAMPUS_SECRET` | Demo-only development secret | Secret used to sign JWTs. Set a private, high-entropy value outside local demos. |
| `CAMPUS_TOKEN_TTL_HOURS` | `24` | JWT expiration time in hours. |

`POST /api/dataset/simulate-stream` is explicitly a **simulation** endpoint. It writes a demo observation tagged `measured`, but it does not connect to or verify any sensor hardware. The provided model scores are evaluations on synthetic demonstration data and should not be interpreted as real-campus performance.