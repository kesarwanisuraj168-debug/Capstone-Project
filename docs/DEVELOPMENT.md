# Developer & Operations Manual (DEVELOPMENT.md)

**Project Name:** Smart Campus Occupancy Forecasting with Spatiotemporal Analytics & Capacity Optimization  
**Document Version:** 1.0.0  
**Target Environment:** Python 3.11 / 3.13 (Windows PowerShell / Linux Bash)  
**Status:** Active / Code-Verified  

---

## 1. Development Environment

### 1.1 Verified Platform Specifications
- **Operating System:** Microsoft Windows 10/11 (64-bit), Linux (Ubuntu 20.04+ LTS), macOS (Darwin 21+).
- **Python Version:** **Python 3.11+** (Tested and verified on Python 3.11.8 and Python 3.13.6).
- **Primary Package Manager:** `pip` ($\ge 24.0$).
- **Shell:** Windows PowerShell 5.1 / PowerShell 7+ or POSIX Bash.
- **Recommended IDE:** Visual Studio Code, Cursor, Antigravity IDE, or PyCharm with Python and Pydantic plugins.

### 1.2 Core Dependency Manifest (`requirements.txt`)
```text
fastapi>=0.110
uvicorn[standard]>=0.29
sqlalchemy>=2.0
pydantic>=2.6
python-multipart>=0.0.9
PyJWT>=2.8
numpy>=1.26
pandas>=2.2
scikit-learn>=1.4
xgboost>=2.0
lightgbm>=4.3
pulp>=2.8
pymysql>=1.1
joblib>=1.3
openpyxl>=3.1
requests>=2.31
pytest>=8.0
```

---

## 2. Comprehensive Codebase Structure

```
c:/Capstone-Project-main/
│
├── backend/                        # FastAPI Application Core
│   ├── __init__.py                 # Package marker
│   ├── config.py                   # Central paths, database URL, JWT secrets, operating hours
│   ├── database.py                 # SQLAlchemy engine, session maker, get_db dependency
│   ├── deps.py                     # Auth dependency guards (optional_user, require_user, require_admin)
│   ├── main.py                     # FastAPI entrypoint, lifespan startup, CORS, static mounting
│   ├── models.py                   # SQLAlchemy ORM models (User, Building, Room, Occupancy, etc.)
│   ├── schemas.py                  # Pydantic v2 request/response schemas and validation
│   ├── security.py                 # PBKDF2-HMAC-SHA256 password hashing & JWT token encoder
│   ├── seed.py                     # Database auto-seeder (structures, 69,290 records, demo users)
│   ├── routes/                     # REST API Route Controllers
│   │   ├── __init__.py             # Route package marker
│   │   ├── auth.py                 # Registration, login, profile (/api/auth)
│   │   ├── buildings.py / ...      # Mounted inside occupancy.py
│   │   ├── occupancy.py            # Building & room CRUD, historical slices (/api/buildings, /api/rooms)
│   │   ├── prediction.py           # Forecasting, day curves, model compare, retrain (/api/predict)
│   │   ├── optimization.py         # PuLP MILP capacity engine & recommendations (/api/optimize)
│   │   ├── dashboard.py            # Aggregated campus KPIs, trend lines, free rooms (/api/dashboard)
│   │   ├── dataset.py              # Ingestion, CSV/Excel upload, simulation, synthesis (/api/dataset)
│   │   └── analytics.py            # DOW/Building heatmaps, 2D spatial layout, tracking (/api/analytics)
│   └── services/                   # Business Logic & Computational Engines
│       ├── __init__.py             # Services package marker
│       ├── forecasting.py          # ML inference, lag chaining, confidence intervals, model cache
│       ├── optimizer.py            # PuLP MILP formulation, CBC solver, timetable conflict checks
│       └── synthetic_generator.py  # Diurnal Poisson arrival generator by room type & scenario
│
├── frontend/                       # Client Single Page Application (SPA)
│   ├── index.html                  # Main SPA container hosting 10 modular views & auth modal
│   └── static/
│       ├── css/
│       │   └── app.css             # Design system styling, tokens, badges, cards, responsive layout
│       └── js/
│           └── app.js              # Client state controller, auth handler, Plotly renderer, CSV export
│
├── ml/                             # Data Science & Machine Learning Pipeline
│   ├── academic_calendar.json      # Calendar metadata (semester, events, holidays, weather, temperature)
│   ├── rooms.json                  # Campus layout, building coordinates, room capacity & type catalog
│   ├── dataset.csv                 # Raw historical dataset (69,290 hourly records across campus)
│   ├── dataset_features.csv        # Engineered feature matrix (14 features + occupancy target)
│   ├── generate_dataset.py         # Standalone synthetic dataset generator
│   ├── preprocessing.py            # Feature engineering pipeline (lags, calendar joins, weather encoding)
│   ├── train_model.py              # Baseline trainer & evaluator (LR, RF, LightGBM, XGBoost)
│   ├── evaluate.py                 # Hold-out evaluation script reporting MAE, RMSE, MAPE, R2
│   ├── train_lstm.py               # (Optional) 2-layer Keras LSTM neural network training script
│   └── models/                     # Serialized Model Artifacts Directory
│       ├── meta.json               # Model metadata, feature lists, and benchmark scores
│       ├── occupancy_model.pkl     # Active production model (XGBoost Regressor)
│       ├── occupancy_model_lgbm.pkl# Evaluated LightGBM Regressor artifact
│       ├── occupancy_model_rf.pkl  # Evaluated Random Forest Regressor artifact
│       ├── occupancy_model_lr.pkl  # Evaluated Linear Regression baseline artifact
│       └── occupancy_model_eval_xgb.pkl # Evaluation hold-out XGBoost artifact
│
├── database/                       # Database DDL References
│   └── schema.sql                  # Reference MySQL 8 DDL schema
│
├── tests/                          # Automated Pytest Test Suite
│   ├── __init__.py                 # Test package marker
│   ├── test_auth.py                # Registration, login, token verification tests
│   ├── test_dataset.py             # File upload, validation, template, synthesis tests
│   ├── test_forecasting.py         # Point forecast, day curves, model compare tests
│   ├── test_optimizer.py           # PuLP MILP allocation & feasibility robustness tests
│   └── test_analytics.py           # DOW heatmap, building heatmap, spatial node tests
│
├── docs/                           # Professional Project Documentation
│   ├── PRD.md                      # Product Requirements Document
│   ├── SRS.md                      # Software Requirements Specification
│   ├── ARCHITECTURE.md             # System Architecture Document
│   ├── UI_UX.md                    # UI/UX Design Specification
│   ├── DEVELOPMENT.md               # Developer & Operations Manual
│   └── DOCUMENTATION_AUDIT.md       # Final Verification Audit Matrix
│
├── campus.db                       # Local SQLite Database (auto-generated & auto-seeded)
├── requirements.txt                # Production Python dependencies
└── README.md                       # Project overview and quick start guide
```

---

## 3. Installation & Setup (Step-by-Step)

### 3.1 Prerequisites
Ensure Python 3.11+ is installed on your Windows workstation. Check the version in PowerShell:
```powershell
python --version
```

### 3.2 Automated 1-Click Setup (Recommended for Windows)
Simply double-click [`setup.bat`](file:///c:/Capstone-Project-main/setup.bat) in the project root directory.

The batch script automatically:
1. Validates Python 3.11+ installation.
2. Creates the `venv` virtual environment if not already present.
3. Activates `venv` and upgrades `pip`.
4. Installs all packages from `requirements.txt`.
5. Checks ML models in `ml/models/` (trains baseline models if absent).
6. Initializes and verifies the SQLite database.
7. Executes all 18 automated tests to verify system readiness.

---

### 3.3 Manual Setup via PowerShell
If you prefer configuring the environment manually:
```powershell
# 1. Create a clean virtual environment
python -m venv venv

# 2. Activate the virtual environment in PowerShell
.\venv\Scripts\Activate.ps1

# 3. Upgrade pip and install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
```
*(Note: If PowerShell execution policy restricts script execution, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first).*

---

## 4. Environment Configuration

Configuration is managed via `backend/config.py`. You can customize behavior using environment variables:

| Environment Variable | Default Value | Description |
| :--- | :--- | :--- |
| `CAMPUS_DATABASE_URL` | `sqlite:///{ROOT}/campus.db` | SQLAlchemy connection URI. Change to `mysql+pymysql://user:pass@localhost/campus` for MySQL 8. |
| `CAMPUS_SECRET` | `campus-demo-secret-change-me-please-2026` | Cryptographic secret key used to sign and verify JWT tokens. |
| `CAMPUS_TOKEN_TTL_HOURS`| `24` | Token expiration duration in hours. |

*Production Notice: In production environments, set `CAMPUS_SECRET` to a high-entropy string generated with `python -c "import secrets; print(secrets.token_hex(32))"`.*

---

## 5. Database Initialization & Seeding

### 5.1 Automatic Seeding on Startup
When the FastAPI backend boots up, the `lifespan` handler in `backend/main.py` automatically creates all database tables via `Base.metadata.create_all(bind=engine)` and invokes `backend/seed.py:seed_all()`.

If the database is unpopulated, it automatically seeds:
1. **5 Campus Buildings:** Academic Block 1 (A), Central Library (B), Cafeteria & Dining (C), Engineering Block (D), Admin & Sports Complex (E).
2. **26 Campus Rooms:** Complete with capacity, room type, and coordinates from `ml/rooms.json`.
3. **69,290 Historical Records:** Seeded from `ml/dataset.csv` in chunks of 4,000 records.
4. **Academic Calendar Events:** Seeded from `ml/academic_calendar.json`.
5. **Academic Timetable Slots:** 20 baseline weekly course sessions across computer science, electronics, and AI.
6. **Demo Accounts:**
   - **Administrator:** `admin` / `admin123` (`role="admin"`)
   - **Standard User:** `user` / `user123` (`role="user"`)

### 5.2 Manual Standalone Seeding
To manually re-seed the SQLite database at any time, run:
```powershell
python -m backend.seed
```

---

## 6. Running the Application

### 6.1 Option A: 1-Click Launch (Recommended for Windows)
Double-click [`run.bat`](file:///c:/Capstone-Project-main/run.bat) in the root directory.

It will:
1. Activate the `venv` virtual environment automatically.
2. Display connection URLs and demo account credentials.
3. Automatically launch your default web browser to [http://localhost:8000/](http://localhost:8000/).
4. Start the FastAPI server on port 8000.

---

### 6.2 Option B: Terminal Command (PowerShell)
Execute Uvicorn from the project root directory:
```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

### 6.3 Service Access Endpoints
- **Interactive Web SPA Dashboard:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Swagger Interactive API Documentation:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc API Specifications:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Backend Health Check:** [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

---

## 7. Machine Learning Engineering Workflow

```mermaid
flowchart LR
    A["Raw Dataset<br>(ml/dataset.csv)"] -->|preprocessing.py| B["Engineered Features<br>(ml/dataset_features.csv)"]
    B -->|train_model.py| C["Trained Models<br>(ml/models/*.pkl)"]
    C -->|evaluate.py| D["Evaluation Metrics<br>(ml/models/meta.json)"]
    D -->|forecasting.py| E["Runtime API Inference<br>(POST /api/predict)"]
```

### 7.1 Feature Engineering (`ml/preprocessing.py`)
To regenerate `ml/dataset_features.csv` from raw observations:
```powershell
python ml/preprocessing.py
```
This script computes 14 engineered features, maps weather categories, generates previous-hour and previous-day occupancy lags, and eliminates cross-day leakage by clearing morning boundary values.

### 7.2 Model Training (`ml/train_model.py`)
To retrain baseline regressors on the chronological 85/15 split:
```powershell
python ml/train_model.py
```
This trains Linear Regression, Random Forest, LightGBM, and XGBoost, evaluates scores on the 10,394 test samples, fits the final production XGBoost model on all data, serializes `occupancy_model.pkl`, and updates `ml/models/meta.json`.

### 7.3 Model Evaluation (`ml/evaluate.py`)
To inspect performance scores of any serialized model against the test set:
```powershell
python ml/evaluate.py ml/models/occupancy_model.pkl
```

---

## 8. Automated Testing Strategy

The project includes an automated test suite implemented with `pytest` and `fastapi.testclient.TestClient`.

### 8.1 Execute Automated Tests
Run the test suite in PowerShell:
```powershell
python -m pytest tests/ -v
```

### 8.2 Test Suite Coverage Matrix (18 Tests)
| Test Module | Test Name | Target Functionality Tested | Status |
| :--- | :--- | :--- | :---: |
| `test_auth.py` | `test_login_success` | Login verification & JWT token return | **PASS** |
| `test_auth.py` | `test_login_invalid_password` | HTTP 401 on incorrect credentials | **PASS** |
| `test_auth.py` | `test_user_me_authenticated` | Authenticated profile retrieval via token | **PASS** |
| `test_auth.py` | `test_user_me_unauthorized` | HTTP 401 on missing auth header | **PASS** |
| `test_dataset.py` | `test_dataset_summary` | Summary breakdown by `synthetic`, `imported`, `measured` | **PASS** |
| `test_dataset.py` | `test_dataset_template` | CSV template download streaming | **PASS** |
| `test_dataset.py` | `test_dataset_empty_file_rejection` | HTTP 400 on empty file upload | **PASS** |
| `test_dataset.py` | `test_dataset_valid_upload` | Ingestion, column mapping & duplicate upsert | **PASS** |
| `test_dataset.py` | `test_synthetic_generation_endpoint` | Custom date & scenario synthesis | **PASS** |
| `test_dataset.py` | `test_synthetic_download_endpoint` | Synthetic CSV streaming attachment | **PASS** |
| `test_forecasting.py` | `test_predict_building` | Point prediction & room details | **PASS** |
| `test_forecasting.py` | `test_predict_day_curve` | 13-hour operating curve with lag chaining | **PASS** |
| `test_forecasting.py` | `test_model_compare` | Multi-algorithm hold-out comparison table | **PASS** |
| `test_optimizer.py` | `test_optimize_single_request` | PuLP MILP single request accommodation | **PASS** |
| `test_optimizer.py` | `test_optimize_exceeding_rooms_robustness`| Slack variable feasibility when requests exceed rooms | **PASS** |
| `test_analytics.py` | `test_heatmap_dow_hour` | 7x13 Day-of-Week matrix dimensions | **PASS** |
| `test_analytics.py` | `test_heatmap_building_time` | Building vs. Time utilization matrix | **PASS** |
| `test_analytics.py` | `test_spatial_campus` | 2D coordinates `(x, y)` and room inventories | **PASS** |

---

## 9. Troubleshooting & Debugging Guide

### Issue 1: `RuntimeError: Model not found at ml/models/occupancy_model.pkl`
- **Cause:** Pre-trained weights have not been generated or were deleted.
- **Solution:** Run `python ml/train_model.py` to regenerate all model binaries and `meta.json`.

### Issue 2: `sqlite3.OperationalError: database is locked`
- **Cause:** Multiple concurrent write processes accessing SQLite in debug mode.
- **Solution:** The database engine is configured with `connect_args={"check_same_thread": False}`. For high-concurrency multi-user environments, switch to MySQL 8 by configuring `CAMPUS_DATABASE_URL`.

### Issue 3: `DeprecationWarning: PULP_CBC_CMD is deprecated`
- **Context:** Warning observed from `pulp` library regarding upcoming PuLP 4.0 API transition.
- **Impact:** Non-breaking warning. CBC solver continues to execute successfully with full mathematical guarantees.

### Issue 4: `PydanticDeprecatedSince20: Support for class-based config is deprecated`
- **Context:** `backend/schemas.py:27` uses `class Config: from_attributes = True`.
- **Solution:** In future refactoring, replace with `model_config = ConfigDict(from_attributes=True)`. Currently functions as expected in Pydantic 2.6+.

### Issue 5: `Address already in use` (Port 8000)
- **Cause:** Another Uvicorn or web server instance is already running on port 8000.
- **Solution:** Kill the lingering process or launch on an alternate port:
  ```powershell
  python -m uvicorn backend.main:app --host 127.0.0.1 --port 8080
  ```

---

## 10. Maintenance & Operational Procedures

### 10.1 Periodic Model Retraining
As campus operations accumulate real-world attendance records (tagged as `imported` or `measured`), administrators should periodically retrain models to minimize concept drift:
- Via Web UI: Click **⚡ Retrain Models (Admin)** in the Model Performance view.
- Via CLI: Run `python ml/train_model.py`.

### 10.2 Database Backups
- **SQLite:** Simply archive or copy `campus.db` while the server is idle.
- **MySQL 8:** Execute standard dump utilities:
  ```powershell
  mysqldump -u campus_user -p campus > campus_backup.sql
  ```

### 10.3 Code Quality & Formatting
Ensure consistent code formatting using `ruff` or `flake8`:
```powershell
python -m pip install ruff
ruff check backend/ ml/ tests/
```
