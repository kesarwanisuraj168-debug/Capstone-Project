# Software Requirements Specification (SRS)

**Standard:** IEEE 830-1998 Aligned Specification  
**Project Name:** Smart Campus Occupancy Forecasting with Spatiotemporal Analytics & Capacity Optimization  
**Document Version:** 1.0.0  
**Status:** Approved / Code-Verified  

---

## 1. Introduction

### 1.1 Purpose
This Software Requirements Specification (SRS) provides a formal, comprehensive specification of the functional, non-functional, data, interface, and algorithmic requirements for the Smart Campus Occupancy Forecasting & Capacity Optimization system. It serves as the definitive technical contract for developers, quality assurance engineers, system architects, and university stakeholders.

### 1.2 Scope of the Software
The software comprises a high-performance Python FastAPI backend, an asynchronous SQLAlchemy ORM database layer (supporting SQLite and MySQL 8), a machine learning inference engine executing gradient-boosted decision trees (XGBoost, LightGBM, Random Forest), a Mixed-Integer Linear Programming (MILP) capacity optimizer powered by PuLP and the CBC solver, and a responsive single-page web dashboard with interactive Plotly.js spatiotemporal visualizations.

The system ingests historical and streaming occupancy records, computes spatial and temporal utilization heatmaps, forecasts occupancy across operating hours (08:00 to 20:00), and outputs conflict-free room allocation recommendations under physical, academic, and equipment constraints.

### 1.3 Definitions, Acronyms, and Abbreviations
- **API:** Application Programming Interface
- **CBC:** Coin-or Branch and Cut (Open-source MILP solver bundled with PuLP)
- **CI:** Confidence Interval (Prediction interval reflecting model variance)
- **CSV:** Comma-Separated Values
- **DOW:** Day of Week (0 = Monday, 6 = Sunday)
- **ERP:** Enterprise Resource Planning
- **HMAC:** Hash-based Message Authentication Code
- **JWT:** JSON Web Token (RFC 7519)
- **LightGBM:** Light Gradient Boosting Machine
- **MAE:** Mean Absolute Error
- **MAPE:** Mean Absolute Percentage Error
- **MILP:** Mixed-Integer Linear Programming
- **ORM:** Object-Relational Mapping (SQLAlchemy)
- **PBKDF2:** Password-Based Key Derivation Function 2 (RFC 2898)
- **$R^2$:** Coefficient of Determination
- **RBAC:** Role-Based Access Control
- **RMSE:** Root Mean Squared Error
- **SIS:** Student Information System
- **SPA:** Single Page Application
- **XGBoost:** eXtreme Gradient Boosting

### 1.4 References
- IEEE Std 830-1998: IEEE Recommended Practice for Software Requirements Specifications.
- RFC 7519: JSON Web Token (JWT) Architecture and Claims.
- NIST Special Publication 800-132: Recommendation for Password-Based Key Derivation.
- PuLP Modeling Documentation: Optimization with PuLP and CBC Solver.
- FastAPI Specification: ASGI Framework Documentation (v0.110+).

---

## 2. Overall Description

### 2.1 Product Perspective
CampusPulse operates as a centralized web-based operational intelligence portal. It interfaces with institutional databases, processes incoming attendance/sensor feeds via REST endpoints, runs server-side ML models, and delivers data visualizations to web browsers over HTTP/JSON without requiring client-side plugins.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        INSTITUTIONAL ECOSYSTEM                         │
├─────────────────┬──────────────────────┬───────────────────────────────┤
│ Campus Users    │ Browser SPA Client   │ Desktop & Mobile Web Browsers │
├─────────────────┼──────────────────────┼───────────────────────────────┤
│ REST API Engine │ FastAPI (Uvicorn)    │ Centralized Business Logic    │
├─────────────────┼──────────────────────┼───────────────────────────────┤
│ Data Layer      │ SQLAlchemy Engine    │ SQLite (default) / MySQL 8    │
├─────────────────┼──────────────────────┼───────────────────────────────┤
│ ML Engine       │ Scikit-Learn/XGBoost │ Serialized Model Artifacts    │
├─────────────────┼──────────────────────┼───────────────────────────────┤
│ Solver Engine   │ PuLP / CBC Solver    │ Mathematical MILP Optimizer  │
└─────────────────┴──────────────────────┴───────────────────────────────┘
```

### 2.2 Product Functions
1. **User Authentication & Session Management:** Token-based authentication with role verification (`admin`, `user`).
2. **Campus Asset Inventory Management:** CRUD operations for physical campus structures (buildings, coordinates, rooms, capacities, floors, types).
3. **Data Ingestion & Integrity Validation:** Ingesting CSV/Excel records, alias header normalization, duplicate handling, and data origin labeling (`synthetic`, `imported`, `measured`).
4. **Occupancy Forecasting:** Point-in-time predictions and 13-hour day curves across 08:00–20:00 operating days with confidence bands.
5. **Spatiotemporal Analytics:** DOW vs. Hour heatmaps, Building vs. Time heatmaps, 2D campus spatial maps, and 14-day tracking.
6. **Capacity Optimization:** PuLP-based MILP room allocation resolving course requests, student headcounts, equipment needs, timetable clashes, and distance penalties.
7. **Synthetic Data Synthesis:** High-fidelity simulation of campus diurnal cycles under various academic scenarios (normal, exam, fest, vacation).

### 2.3 User Classes and Characteristics
- **Administrator (`admin`):** High technical and operational competence. Manages campus structures, triggers model retraining, uploads datasets, seeds test data, and manages privileges.
- **Academic / Department User (`user`):** Focuses on course scheduling, space availability, running optimizations, reviewing forecasts, and exporting analytical reports.
- **Guest / Evaluator:** Evaluates public dashboards, spatial layout maps, and forecasting visualizations without authentication credentials.

### 2.4 Operating Environment
- **Server OS:** Cross-platform (Windows 10/11, Windows Server, Linux Ubuntu 20.04+, macOS).
- **Runtime Environment:** Python 3.11 or Python 3.13.
- **Client Environment:** Modern web browser supporting ECMAScript 6+ and HTML5 Canvas (Google Chrome 100+, Mozilla Firefox 100+, Microsoft Edge 100+, Safari 15+).
- **Network Protocol:** HTTP/1.1 or HTTP/2 over TLS (HTTPS). Default development port: `8000`.

### 2.5 Design and Implementation Constraints
- **Operating Hours:** Forecast and optimization algorithms are constrained to the standard operating window (08:00 to 20:00; hours 8 through 20).
- **Single-Threaded Solver Execution:** PuLP CBC execution runs as a synchronous process bounded by a 30-second execution timeout.
- **Model Storage:** ML artifacts are serialized using `joblib` into `ml/models/` and loaded into RAM on server startup.
- **File Upload Bounding:** Maximum file upload size is strictly limited to 15 megabytes (`15 * 1024 * 1024` bytes).

### 2.6 Assumptions and Dependencies
- Static campus metadata (room codes, room types, baseline capacities) exists in `ml/rooms.json` or database tables.
- System clocks are synchronized in UTC / local timezone for consistent hourly bucket indexing.
- SQLite is utilized for single-node deployments; multi-instance deployment requires configuring `CAMPUS_DATABASE_URL` to point to MySQL 8.

---

## 3. Functional Requirements

### 3.1 Module 1: Authentication & Access Control

| Requirement ID | Description | Implementation Status |
| :--- | :--- | :--- |
| **FR-AUTH-001** | The system shall provide a registration endpoint `POST /api/auth/register` accepting `username` (3–50 chars), `full_name`, and `password` (4–128 chars). | **Implemented** |
| **FR-AUTH-002** | Passwords shall be cryptographically hashed using PBKDF2-HMAC-SHA256 with 120,000 iterations and a cryptographically secure 16-byte random salt. Plaintext passwords shall never be persisted. | **Implemented** |
| **FR-AUTH-003** | The system shall authenticate users via `POST /api/auth/login` and issue an RFC 7519 compliant JSON Web Token (JWT) signed with HS256 algorithm with a default TTL of 24 hours. | **Implemented** |
| **FR-AUTH-004** | The system shall expose `GET /api/auth/me` requiring a valid Bearer token and returning the authenticated user profile. | **Implemented** |
| **FR-AUTH-005** | The system shall enforce Role-Based Access Control (RBAC): endpoints modifying campus structures or triggering model retraining shall require `role="admin"` (HTTP 403 Forbidden on violation). | **Implemented** |

### 3.2 Module 2: Campus Infrastructure & Inventory Management

| Requirement ID | Description | Implementation Status |
| :--- | :--- | :--- |
| **FR-CAMP-001** | The system shall list all registered buildings via `GET /api/buildings` including building code, name, 2D coordinates `(x, y)`, total room count, and cumulative seating capacity. | **Implemented** |
| **FR-CAMP-002** | The system shall allow administrators to create (`POST /api/buildings`), update (`PUT /api/buildings/{id}`), and delete (`DELETE /api/buildings/{id}`) building records. Deleting a building shall cascade delete all associated rooms and historical occupancy records. | **Implemented** |
| **FR-CAMP-003** | The system shall list rooms filtered optionally by building code via `GET /api/rooms` returning room code, type, capacity, and floor. | **Implemented** |
| **FR-CAMP-004** | The system shall allow administrators to create (`POST /api/rooms`), update (`PUT /api/rooms/{id}`), and delete (`DELETE /api/rooms/{id}`) room records with unique code verification. | **Implemented** |

### 3.3 Module 3: Occupancy Data Ingestion & Validation Pipeline

| Requirement ID | Description | Implementation Status |
| :--- | :--- | :--- |
| **FR-DATA-001** | The system shall accept CSV, XLSX, and XLS file uploads via `POST /api/dataset/upload` up to a maximum size of 15MB. | **Implemented** |
| **FR-DATA-002** | The ingestion parser shall support case-insensitive column alias mapping for `date`, `timestamp`, `hour`, `room`, `building`, `occupancy`, `capacity`, `room_type`, `floor`, `students_count`, `staff_count`, `is_exam`, and `scheduled_class`. | **Implemented** |
| **FR-DATA-003** | The parser shall reject negative occupancy values and out-of-range hours ($<0$ or $>23$). Exceedances of room capacity shall generate non-fatal warning messages. | **Implemented** |
| **FR-DATA-004** | The system shall support a `replace_duplicates` flag to either update existing `(room_id, date, hour)` slots or skip duplicates. | **Implemented** |
| **FR-DATA-005** | Every ingested record shall be explicitly tagged with a provenance marker `data_origin` (`synthetic`, `imported`, or `measured`). | **Implemented** |
| **FR-DATA-006** | The system shall provide database summary statistics via `GET /api/dataset/summary` detailing total record counts partitioned by origin, date coverage span, and room/building coverage. | **Implemented** |
| **FR-DATA-007** | The system shall expose a downloadable standard CSV template via `GET /api/dataset/template`. | **Implemented** |
| **FR-DATA-008** | The system shall provide a simulated live sensor stream endpoint `POST /api/dataset/simulate-stream` updating current room counts with `data_origin="measured"`. | **Implemented** |
| **FR-DATA-009** | The system shall generate realistic synthetic datasets across custom date spans and scenarios (`normal`, `exam`, `fest`, `vacation`) via `POST /api/dataset/generate-synthetic` and stream downloadable CSV files via `GET /api/dataset/download-synthetic`. | **Implemented** |

### 3.4 Module 4: Machine Learning Forecasting Engine

| Requirement ID | Description | Implementation Status |
| :--- | :--- | :--- |
| **FR-ML-001** | The system shall generate point forecasts via `POST /api/predict` for a specified building, date, and hour (restricted to 08:00–20:00). | **Implemented** |
| **FR-ML-002** | The forecasting feature vector shall comprise 14 features: `hour`, `day_of_week`, `month`, `is_weekend`, `semester`, `event`, `holiday`, `weather_code`, `temperature`, `building_num`, `room_num`, `capacity`, `prev_hour_occ`, and `prev_day_occ`. | **Implemented** |
| **FR-ML-003** | The system shall compute a 95% Confidence Interval for each forecast based on the empirical error distribution of the active model. | **Implemented** |
| **FR-ML-004** | The system shall project a 13-hour continuous operating day curve via `GET /api/predict/day` from 08:00 to 20:00 utilizing autoregressive lag chaining (the predicted value of hour $h$ feeds into `prev_hour_occ` for hour $h+1$). | **Implemented** |
| **FR-ML-005** | The system shall support algorithm selection among XGBoost (default), LightGBM, Random Forest, Linear Regression, and optional Keras LSTM. | **Implemented** |
| **FR-ML-006** | The system shall expose benchmark metrics (MAE, RMSE, MAPE, $R^2$) via `GET /api/model/compare` calculated strictly on a chronological 15% hold-out test set. | **Implemented** |
| **FR-ML-007** | The system shall allow administrators to trigger background model retraining via `POST /api/model/retrain` executing `ml/train_model.py` and refreshing in-memory weights. | **Implemented** |
| **FR-ML-008** | All prediction queries shall be logged to the `predictions` database table and retrievable via `GET /api/predictions`. | **Implemented** |

### 3.5 Module 5: Spatiotemporal Analytics & Spatial Visualization

| Requirement ID | Description | Implementation Status |
| :--- | :--- | :--- |
| **FR-ANLY-001** | The system shall compute a $7 \times 13$ Day-of-Week (Monday–Sunday) vs. Hour (08:00–20:00) matrix of average occupancy via `GET /api/analytics/heatmap/dow-hour`. | **Implemented** |
| **FR-ANLY-002** | The system shall compute a Building vs. Hour utilization percentage matrix for any specified date via `GET /api/analytics/heatmap/building-time`. | **Implemented** |
| **FR-ANLY-003** | The system shall provide room-by-room utilization, average occupancy, peak occupancy, and stress status via `GET /api/analytics/room-comparison`. | **Implemented** |
| **FR-ANLY-004** | The system shall return campus 2D coordinates `(x, y)` and utilization statuses via `GET /api/analytics/spatial` for rendering on an interactive canvas. | **Implemented** |
| **FR-ANLY-005** | The system shall compare 14-day historical actual vs. predicted person-hours and calculate variance via `GET /api/analytics/historical-vs-predicted`. | **Implemented** |

### 3.6 Module 6: PuLP MILP Capacity Optimization Engine

| Requirement ID | Description | Implementation Status |
| :--- | :--- | :--- |
| **FR-OPT-001** | The system shall accept up to 40 simultaneous room allocation requests via `POST /api/optimize` specifying course name, student headcount, equipment constraints, and preferred building. | **Implemented** |
| **FR-OPT-002** | The solver shall compute each room's usable capacity dynamically as $\text{usable} = \max(0, \text{capacity} - \text{predicted\_occupancy})$ using the ML forecast. | **Implemented** |
| **FR-OPT-003** | The solver shall enforce hard conflict constraints against existing scheduled classes recorded in the `timetable` table for the corresponding weekday and hour slot. | **Implemented** |
| **FR-OPT-004** | The solver shall enforce equipment constraints against `EQUIPMENT_GROUND_TRUTH` (computers, projector, sound system, whiteboard, lab equipment). | **Implemented** |
| **FR-OPT-005** | The objective function shall minimize: $\sum (W_{\text{empty}} \cdot \text{empty\_ratio} + W_{\text{switch}} \cdot \text{switch} + W_{\text{dist}} \cdot \text{dist} + \text{equip\_miss} + \text{pref\_miss}) + \sum (\text{INFEASIBLE\_PENALTY} \cdot \text{dummy}_i)$. | **Implemented** |
| **FR-OPT-006** | Slack dummy variables ($\text{dummy}_i$) with penalty $1,000,000$ shall guarantee that the solver never crashes or raises an infeasibility exception even when requests exceed total campus capacity. | **Implemented** |
| **FR-OPT-007** | Solved recommendations shall be logged to the `recommendations` table and retrievable via `GET /api/recommendations`. | **Implemented** |

---

## 4. Non-Functional Requirements (NFR)

### 4.1 Performance Requirements
- **NFR-PERF-001 (API Latency):** 95% of read-only REST API requests (`/api/buildings`, `/api/dashboard`, `/api/analytics/*`) shall respond within $\le 200\text{ ms}$ under nominal single-host load.
- **NFR-PERF-002 (Forecasting Latency):** Point prediction for an entire building across all constituent rooms shall execute in $\le 80\text{ ms}$ using in-memory tree models.
- **NFR-PERF-003 (Optimization Solve Time):** The PuLP MILP solver shall solve a 25-request allocation problem against the 26-room campus in $\le 1.0\text{ second}$ (timeout threshold: 30 seconds).

### 4.2 Security Requirements
- **NFR-SEC-001 (Password Security):** Passwords shall never be logged or returned via API responses. Hashes must use PBKDF2-HMAC-SHA256 with at least 120,000 iterations.
- **NFR-SEC-002 (Token Integrity):** JWT tokens shall be cryptographically verified on every protected route. Expired or forged tokens shall be rejected with HTTP 401 Unauthorized.
- **NFR-SEC-003 (Injection Mitigation):** All database operations shall use parameterized queries through SQLAlchemy ORM; direct string concatenation in SQL statements is strictly prohibited.
- **NFR-SEC-004 (Upload Sanitization):** Uploaded files shall be validated in memory; execution of uploaded scripts or saving files directly to server executable paths is prohibited.

### 4.3 Availability & Reliability
- **NFR-REL-001 (Fault Tolerance):** Database connection errors shall trigger pool pre-ping reconnects (`pool_pre_ping=True`).
- **NFR-REL-002 (Solver Feasibility Guarantee):** The capacity optimization engine shall have a mathematical guarantee of feasibility through bounded slack variables, ensuring zero 500 Internal Server Errors due to solver infeasibility.

### 4.4 Maintainability & Extensibility
- **NFR-MNT-001 (Modular Decoupling):** Routes, schemas, database models, and ML services shall be segregated into distinct directories (`backend/routes/`, `backend/services/`, `ml/`).
- **NFR-MNT-002 (Database Portability):** Switching between SQLite and MySQL 8 shall require altering only the `CAMPUS_DATABASE_URL` environment variable without codebase modifications.

### 4.5 Usability & Accessibility
- **NFR-USE-001 (Responsive Viewport):** Frontend layouts shall adapt fluidly from 360px mobile viewports to 2560px 4K desktop screens.
- **NFR-USE-002 (Color Contrast & Semantic Badges):** All status badges (High, Medium, Low, Overcrowded) shall pair distinct color codes with explicit text labels.

---

## 5. Data Requirements & Schema Specification

### 5.1 Input Datasets
- **`ml/dataset.csv`:** 69,290 historical hourly occupancy observations.
- **`ml/rooms.json`:** Campus spatial structure, building coordinates, room capacity, and room types.
- **`ml/academic_calendar.json`:** Date-indexed academic calendar metadata (semester, exam, fest, holiday, weather, temperature).

### 5.2 Database Entity-Relationship Definitions

#### 1. Table: `users`
| Field | Type | Modifiers | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer | PK, Auto-increment | Unique user identifier |
| `username` | String(50) | Unique, Index, Not Null | Login account username |
| `full_name` | String(100) | Default: `""` | User's full name |
| `password_hash` | String(200) | Not Null | PBKDF2 hash string |
| `role` | String(20) | Default: `"user"` | Authorization role (`admin` or `user`) |
| `created_at` | DateTime | Default: `utcnow` | User creation timestamp |

#### 2. Table: `buildings`
| Field | Type | Modifiers | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer | PK, Auto-increment | Unique building identifier |
| `code` | String(10) | Unique, Index, Not Null | Short building code (e.g., `A`, `B`, `C`) |
| `name` | String(100) | Not Null | Descriptive building name |
| `x` | Integer | Default: `0` | Coordinate $x$ on 0–100 grid |
| `y` | Integer | Default: `0` | Coordinate $y$ on 0–100 grid |

#### 3. Table: `rooms`
| Field | Type | Modifiers | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer | PK, Auto-increment | Unique room identifier |
| `code` | String(20) | Unique, Index, Not Null | Unique room code (e.g., `A-101`) |
| `building_id` | Integer | FK (`buildings.id`), Not Null | Parent building foreign key |
| `room_type` | String(30) | Default: `"classroom"` | Type: classroom, lab, library, cafeteria, etc. |
| `capacity` | Integer | Not Null | Maximum seated capacity |
| `floor` | Integer | Default: `1` | Building floor level |

#### 4. Table: `occupancy`
| Field | Type | Modifiers | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer | PK, Auto-increment | Unique record identifier |
| `room_id` | Integer | FK (`rooms.id`), Index, Not Null | Target room foreign key |
| `date` | String(10) | Index, Not Null | Date formatted as `YYYY-MM-DD` |
| `hour` | Integer | Index, Not Null | Operating hour (0–23) |
| `occupancy_count` | Integer | Not Null | Observed head count |
| `data_origin` | String(20) | Default: `"synthetic"`, Not Null | Provenance: `synthetic`, `imported`, `measured` |
| `students_count` | Integer | Nullable | Breakdown: student headcount |
| `staff_count` | Integer | Nullable | Breakdown: faculty/staff headcount |
| `is_exam` | Integer | Default: `0` | Flag: 1 if exam session, 0 otherwise |
| `scheduled_class` | String(100) | Nullable | Course or class code scheduled |

#### 5. Table: `timetable`
| Field | Type | Modifiers | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer | PK, Auto-increment | Unique timetable entry |
| `course` | String(80) | Not Null | Course name/code |
| `room_id` | Integer | FK (`rooms.id`), Not Null | Room where class is scheduled |
| `day_of_week` | Integer | Not Null | 0 = Monday .. 6 = Sunday |
| `hour` | Integer | Not Null | Operating hour slot |
| `semester` | Integer | Default: `1` | Academic semester indicator |

#### 6. Table: `events`
| Field | Type | Modifiers | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer | PK, Auto-increment | Unique event identifier |
| `date` | String(10) | Unique, Index, Not Null | Date of event (`YYYY-MM-DD`) |
| `name` | String(100) | Not Null | Event title (e.g., TechFest, Final Exams) |

#### 7. Table: `predictions`
| Field | Type | Modifiers | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer | PK, Auto-increment | Unique log identifier |
| `user_id` | Integer | FK (`users.id`), Nullable | Requesting user identifier |
| `building_id` | Integer | FK (`buildings.id`), Nullable | Predicted building foreign key |
| `date` | String(10) | Not Null | Target prediction date |
| `hour` | Integer | Not Null | Target prediction hour |
| `predicted_occupancy`| Integer | Not Null | Predicted headcount value |
| `model` | String(30) | Default: `"xgb"` | Algorithm used (`xgb`, `lgbm`, `rf`, `lr`) |
| `created_at` | DateTime | Default: `utcnow` | Prediction timestamp |

#### 8. Table: `recommendations`
| Field | Type | Modifiers | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer | PK, Auto-increment | Unique recommendation log ID |
| `user_id` | Integer | FK (`users.id`), Nullable | User who executed the solver |
| `date` | String(10) | Not Null | Target schedule date |
| `hour` | Integer | Not Null | Target schedule hour |
| `payload` | Text | Default: `"{}"` | Serialized JSON results and summary |
| `created_at` | DateTime | Default: `utcnow` | Recommendation timestamp |

---

## 6. Comprehensive API Requirements & Endpoint Matrix

| Method | Endpoint | Auth Level | Request Body / Query Params | Success Response (200/201) | Error Codes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **POST** | `/api/auth/register` | Public | JSON: `username`, `full_name`, `password` | `{ token, user: { id, username, role } }` | 409 (Username taken), 422 |
| **POST** | `/api/auth/login` | Public | JSON: `username`, `password` | `{ token, user: { id, username, role } }` | 401 (Invalid creds), 422 |
| **GET** | `/api/auth/me` | User / Admin | Header: `Authorization: Bearer <token>` | `{ id, username, full_name, role }` | 401 (Unauthorized) |
| **GET** | `/api/buildings` | Public | None | Array of Building objects with `room_count`, `capacity` | 500 |
| **POST** | `/api/buildings` | Admin | JSON: `code`, `name`, `x`, `y` | `{ status, message, building }` | 400 (Duplicate), 401, 403 |
| **PUT** | `/api/buildings/{id}`| Admin | JSON: `name`, `x`, `y` | `{ status, message, building }` | 404 (Not found), 401, 403 |
| **DELETE**| `/api/buildings/{id}`| Admin | Path: `id` | `{ status, message }` | 404, 401, 403 |
| **GET** | `/api/rooms` | Public | Query: `building` (optional) | Array of Room objects with building metadata | 500 |
| **POST** | `/api/rooms` | Admin | JSON: `code`, `building_code`, `room_type`, `capacity`, `floor` | `{ status, message, room }` | 400, 404 (Building missing), 403 |
| **PUT** | `/api/rooms/{id}` | Admin | JSON: `room_type`, `capacity`, `floor` | `{ status, message, room }` | 404, 403 |
| **DELETE**| `/api/rooms/{id}` | Admin | Path: `id` | `{ status, message }` | 404, 403 |
| **GET** | `/api/occupancy/current` | Public | None | Snapshot of latest recorded date & hour with totals | 500 |
| **GET** | `/api/occupancy/history` | Public | Query: `days` (default 30, max 365) | Daily sum series `[{ date, total }]` | 500 |
| **GET** | `/api/occupancy/date` | Public | Query: `date`, `hour` | Building-level occupancy sums for slot | 500 |
| **GET** | `/api/occupancy/detail`| Public | Query: `building`, `date` | 13-hour occupancy matrix for each room in building | 500 |
| **POST** | `/api/predict` | Optional Auth | JSON: `building`, `date`, `hour`, `model` | `{ predicted_occupancy, capacity, utilization, rooms, context }` | 404 (Building), 422, 503 |
| **GET** | `/api/predict/day` | Public | Query: `building`, `date` | Continuous 13-hour curve `[{ hour, predicted }]` | 404, 503 |
| **GET** | `/api/predict/campus` | Public | Query: `date`, `hour` | Campus total and per-building forecast | 503 |
| **GET** | `/api/predict/overcapacity` | Public | Query: `date`, `hour`, `threshold` | Buildings with utilization $\ge \text{threshold}$ | 503 |
| **GET** | `/api/predict/peak` | Public | Query: `building`, `date` | Peak hour object with predicted headcount | 404, 503 |
| **GET** | `/api/model/metrics` | Public | None | Active model name, feature columns, metrics dict | 503 |
| **GET** | `/api/model/compare` | Public | None | Comparison table across LR, RF, LightGBM, XGBoost | 503 |
| **POST** | `/api/model/retrain` | Admin | Header: Bearer Token | `{ status, message, metrics, output }` | 401, 403, 500 |
| **GET** | `/api/predictions` | Public | Query: `limit` (1–200, default 30) | Historical prediction log array | 500 |
| **POST** | `/api/optimize` | Optional Auth | JSON: `date`, `hour`, `requests[]`, `save` | `{ status, summary, results[], hourly_analysis }` | 422 ($>40$ requests), 500 |
| **GET** | `/api/recommendations` | Public | Query: `limit` (1–200, default 30) | Past optimization recommendation records | 500 |
| **GET** | `/api/optimize/courses`| Public | None | Distinct list of courses from timetable | 500 |
| **GET** | `/api/optimize/options`| Public | Query: `students`, `equipment` | Filtered rooms meeting capacity and equipment | 500 |
| **GET** | `/api/dashboard` | Public | Query: `date`, `hour` (optional) | Aggregated KPIs, trend series, free rooms, alerts | 500 |
| **POST** | `/api/dataset/upload` | Public / Admin | Multipart: `file`, `origin`, `replace_duplicates` | `{ status, filename, total_rows, inserted, updated, skipped }` | 400 (Empty/Corrupt), 413, 422 |
| **GET** | `/api/dataset/summary`| Public | None | Record counts by origin, date span, coverage | 500 |
| **GET** | `/api/dataset/preview`| Public | Query: `limit`, `origin` | Sample records with room and building joins | 500 |
| **GET** | `/api/dataset/template`| Public | None | CSV template attachment stream | 500 |
| **POST** | `/api/dataset/simulate-stream` | Public | Query: `room_code`, `occupancy_count` | Packet acknowledgment with simulation mode tag | 404 (Room missing) |
| **POST** | `/api/dataset/generate-synthetic` | Public | Query: `start_date`, `end_date`, `scenario`, `noise_level`, `seed_db` | Summary of synthesized records & seeding status | 400, 422 |
| **GET** | `/api/dataset/download-synthetic` | Public | Query: `start_date`, `end_date`, `scenario`, `noise_level` | Downloadable CSV file attachment stream | 400 |
| **GET** | `/api/analytics/heatmap/dow-hour` | Public | Query: `building` (optional) | $7 \times 13$ matrix of average occupancy | 500 |
| **GET** | `/api/analytics/heatmap/building-time` | Public | Query: `date` (optional) | Matrix of utilization % across buildings and hours | 500 |
| **GET** | `/api/analytics/room-comparison` | Public | Query: `building`, `date` | Room ranking array with avg, peak, util %, status | 500 |
| **GET** | `/api/analytics/spatial` | Public | Query: `date`, `hour` | 2D coordinates `(x, y)`, occupancy, utilization, status | 500 |
| **GET** | `/api/analytics/historical-vs-predicted` | Public | Query: `building`, `days` (1–30) | Daily person-hour actual vs predicted series | 500 |
| **GET** | `/api/health` | Public | None | `{ status: "ok", model_loaded: bool, model: str }` | 500 |

---

## 7. Machine Learning Requirements Specification

### 7.1 Data Corpus & Feature Formulation
- **Corpus File:** `ml/dataset_features.csv` (derived from 69,290 hourly observations in `ml/dataset.csv`).
- **Target Variable:** `occupancy` (continuous non-negative integer representing headcount in a specific room at a specific hour).
- **Engineered Feature Set (14 features):**
  1. `hour`: Operating hour ($8 \le h \le 20$).
  2. `day_of_week`: Integer weekday ($0 = \text{Monday}, 6 = \text{Sunday}$).
  3. `month`: Calendar month ($1 \le m \le 12$).
  4. `is_weekend`: Binary flag ($1$ if Saturday/Sunday, $0$ otherwise).
  5. `semester`: Academic term ($1$ during active term months, $0$ during breaks).
  6. `event`: Binary indicator ($1$ if institutional campus event scheduled).
  7. `holiday`: Binary indicator ($1$ if academic/national holiday).
  8. `weather_code`: Categorical encoding (0: Normal, 1: Hot, 2: Cold, 3: Rainy, 4: Stormy).
  9. `temperature`: Ambient temperature in Celsius (float).
  10. `building_num`: Ordinal building identifier.
  11. `room_num`: Ordinal room identifier.
  12. `capacity`: Static room seating capacity.
  13. `prev_hour_occ`: Lagged occupancy from the immediately preceding hour (cleared to $0.0$ at 08:00 boundary).
  14. `prev_day_occ`: Lagged occupancy from the identical room and hour slot on the previous calendar day.

### 7.2 Validation Strategy
- **Temporal Hold-Out Split:** Strictly chronological 85/15 split.
  - Training Partition: First 58,896 samples (85%).
  - Test Hold-Out Partition: Last 10,394 unseen samples (15%).
  - Zero target leakage: Lags across midnight are cleared to prevent cross-day information bleed.

### 7.3 Model Implementations & Evaluated Benchmarks

```
   Algorithm Benchmarks (Evaluated on Chronological 15% Hold-Out Set):
   ┌──────────────────────┬───────┬───────┬─────────┬──────────┬────────────────────────┐
   │ Algorithm            │  MAE  │  RMSE │  MAPE % │ R² Score │ Deployment Status      │
   ├──────────────────────┼───────┼───────┼─────────┼──────────┼────────────────────────┤
   │ LightGBM Regressor   │  6.84 │ 12.13 │  67.42% │  0.9604  │ ⭐ Primary Recomm.     │
   │ XGBoost Regressor    │  7.01 │ 12.23 │  64.89% │  0.9598  │ ⭐ Default Active      │
   │ Random Forest        │  7.72 │ 14.74 │  64.23% │  0.9415  │ Production Ready       │
   │ Linear Regression    │ 12.63 │ 21.24 │ 178.81% │  0.8787  │ Statistical Baseline   │
   │ Keras LSTM (2-Layer) │  —    │  —    │   —     │  —       │ Optional Lazy-Loaded   │
   └──────────────────────┴───────┴───────┴─────────┴──────────┴────────────────────────┘
```

---

## 8. Error Handling Specification

The system implements structured HTTP exception handling mapped to standard RFC error codes:

| HTTP Status | Trigger Condition | System Response JSON Format |
| :--- | :--- | :--- |
| **400 Bad Request** | Empty file upload, invalid date format, start date > end date, generation span $>365$ days. | `{"detail": "start_date must be before or equal to end_date."}` |
| **401 Unauthorized**| Missing Bearer token on protected route (`/api/auth/me`), invalid password on login. | `{"detail": "Invalid username or password."}` |
| **403 Forbidden** | Standard user attempting admin-restricted action (`/api/model/retrain`, `/api/buildings`). | `{"detail": "Administrator privileges required."}` |
| **404 Not Found** | Querying a non-existent building (`KeyError`), room code, or database ID. | `{"detail": "Unknown building 'Z'"}` |
| **413 Payload Too Large** | Ingestion file exceeds 15 megabytes (`15 * 1024 * 1024` bytes). | `{"detail": "File too large (max 15MB)."}` |
| **422 Unprocessable** | Forecasting query for hour $<8$ or $>20$, optimizer request count $>40$, missing room column. | `{"detail": "Forecasts are valid for 08:00-20:00."}` |
| **503 Service Unavailable** | Forecasting model artifact missing from disk (`occupancy_model.pkl`). | `{"detail": "Model not found at ... Run: py -3.11 ml/train_model.py"}` |

---

## 9. Acceptance Criteria & Test Verification Matrix

Every module must meet the following automated criteria verified by the Pytest test suite (`tests/`):

1. **Authentication Suite (`tests/test_auth.py`):**
   - Verification of successful login and JWT token issuance.
   - Verification of HTTP 401 on incorrect credentials.
   - Verification of authenticated user profile retrieval and 401 rejection on unauthenticated requests.
2. **Dataset & Ingestion Suite (`tests/test_dataset.py`):**
   - Verification of summary statistics and origin counting (`synthetic`, `imported`, `measured`).
   - Verification of template CSV generation.
   - Verification of 400 rejection on empty file uploads.
   - Verification of successful ingestion, row parsing, and duplicate handling on valid CSVs.
   - Verification of synthetic generation and CSV download streaming.
3. **Forecasting Suite (`tests/test_forecasting.py`):**
   - Verification of point building prediction and confidence interval bounds.
   - Verification of 13-hour day curve generation with lag chaining.
   - Verification of model comparison metrics across all benchmark algorithms.
4. **Capacity Optimization Suite (`tests/test_optimizer.py`):**
   - Verification of single-request MILP assignment satisfying capacity and equipment.
   - Verification of robustness when 25 requests exceed room capacity (slack dummy variables absorb excess without failure).
5. **Analytics Suite (`tests/test_analytics.py`):**
   - Verification of $7 \times 13$ Day-of-Week heatmap matrix dimensions.
   - Verification of Building vs. Time heatmap matrix structure.
   - Verification of 2D spatial coordinate output for all campus buildings.
