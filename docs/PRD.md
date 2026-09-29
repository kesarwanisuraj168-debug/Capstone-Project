# Product Requirements Document (PRD)

**Project Name:** Smart Campus Occupancy Forecasting with Spatiotemporal Analytics & Capacity Optimization  
**Document Version:** 1.0.0  
**Status:** Active / Production-Ready Baseline  
**Target Environment:** Python 3.11+, FastAPI, SQLAlchemy, SQLite/MySQL, Scikit-Learn/XGBoost/LightGBM, PuLP MILP, Vanilla JS + Plotly SPA  

---

## 1. Product Overview

### 1.1 What the Product Is
The **Smart Campus Occupancy Forecasting & Capacity Optimization Platform** (branded as **CampusPulse**) is an enterprise-grade AIML and Data Science solution designed for higher education campuses and institutional facilities. It provides end-to-end spatiotemporal visibility into campus physical asset utilization, forecasts future hourly occupancy using machine learning, identifies spatial overcrowding and idle spaces, and computes mathematically optimal room allocations using Mixed-Integer Linear Programming (MILP).

### 1.2 Why It Exists
Universities and colleges operate large physical footprints comprising multi-building campuses with lecture halls, computer laboratories, seminar rooms, libraries, dining halls, and recreational centers. Historically, institutional administrators have relied on static timetables and periodic headcounts, resulting in blind spots regarding how facilities are actually occupied across the operating day (08:00 to 20:00). CampusPulse bridges the gap between static scheduling and dynamic utilization using predictive analytics and optimization.

### 1.3 What Problem It Solves
- **Visibility Deficit:** Administrators cannot observe real-time or historical hourly utilization across rooms and buildings.
- **Suboptimal Room Allocation:** Class rescheduling or event planning often creates room-capacity mismatches (e.g., placing 30 students in a 300-seat auditorium while a 70-person lecture is squeezed into a 60-seat classroom).
- **Peak Hour Congestion:** Midday spikes (11:00–14:00) cause bottlenecks in libraries and cafeterias without advance warning.
- **Resource Inefficiency:** HVAC, lighting, and custodial services are expended on virtually empty rooms while adjacent areas face severe overcrowding.

### 1.4 Target Audience
Campus facility managers, university registrars, departmental scheduling officers, academic deans, and campus executive leadership.

### 1.5 Real-World Problem Addressed
Higher education institutions spend millions annually on capital expenditures and facilities management. Inefficient space utilization leads either to unnecessary new construction or chronic classroom shortages. CampusPulse extracts operational intelligence from historical schedules, calendar events, weather context, and sensor logs to maximize the capacity yield of existing campus infrastructure.

---

## 2. Problem Statement

### 2.1 Lack of Occupancy Visibility
Campus administrators lack unified dashboards reflecting actual space occupancy. Administrative blocks, engineering wings, and central libraries exist as information silos. Decision-makers lack granular hourly data to ascertain whether a building is operating at 20% or 95% capacity at any given hour of the day.

### 2.2 Inefficient Room Allocation & Mismatch
Classroom scheduling is frequently performed months in advance based on hypothetical course enrollments. Fluctuations in student attendance, elective choices, and timetable overlaps result in high vacancy in large rooms while smaller rooms exceed safety thresholds.

### 2.3 Overcrowding vs. Underutilization Paradox
A hallmark of unmanaged campuses is the simultaneous occurrence of severe overcrowding in select facilities (e.g., Central Library during midterm exam blocks or ground-floor engineering classrooms) alongside complete underutilization in adjacent buildings or upper-floor labs.

### 2.4 Inability to Forecast Temporal Spikes
Conventional management reacts to congestion only after it occurs. Without machine-learning-based temporal forecasting that accounts for academic calendar phases (normal semester, exam periods, campus fests, vacations), day of week, time of day, and weather variations, proactive load balancing is impossible.

### 2.5 Complexity of Rescheduling Constraints
When an ad-hoc class, seminar, or makeup lecture requires assignment, human coordinators struggle to evaluate all concurrent constraints simultaneously: room capacity, forecast attendance, required specialized equipment (e.g., computers, projectors, sound systems), spatial walking distance between buildings, and existing scheduled timetable slots.

---

## 3. Product Vision

To establish an autonomous, intelligent campus operating system that harmonizes academic schedules, spatial footprints, and dynamic human occupancy. In the long term, CampusPulse will evolve from human-in-the-loop decision support into a self-optimizing physical campus platform that dynamically schedules rooms, regulates HVAC/energy systems based on predicted occupancy, and provides real-time wayfinding for students and staff.

---

## 4. Goals and Measurable Objectives

| Objective Area | Baseline Condition | Target / Measurable Metric | Implementation Status |
| :--- | :--- | :--- | :--- |
| **Occupancy Monitoring** | Fragmented manual attendance logs or zero tracking. | Unified campus overview dashboard with KPIs across all campus buildings and rooms for 08:00–20:00 operating hours. | **Implemented** |
| **Forecasting Accuracy** | No forecasting capability (pure guesswork). | Model accuracy achieving $R^2 \ge 0.94$, MAE $\le 8.0$ persons on chronological test hold-outs across all campus rooms. | **Implemented** (LightGBM: $R^2=0.9604$, MAE=6.84; XGBoost: $R^2=0.9598$, MAE=7.01) |
| **Spatiotemporal Analytics** | Static spreadsheets with no temporal or spatial context. | Interactive 2D spatial coordinate mapping (100x100 grid) and 7x13 Day-of-Week vs. Hour density heatmaps. | **Implemented** |
| **Capacity Utilization** | Imbalanced space usage with unknown free seat counts. | Identification of available rooms with $\ge 15$ free seats and room-by-room utilization percentage ranking. | **Implemented** |
| **Overcrowding Detection** | Unnoticed fire/safety hazards until physical complaints arise. | Automated identification of rooms and buildings exceeding configurable thresholds (default $\ge 80\%$). | **Implemented** |
| **Alternative Room Allocation** | Manual, slow, and error-prone reassignment. | PuLP Mixed-Integer Linear Programming (MILP) solver optimizing multi-request room assignments in $\le 1.0$ second. | **Implemented** |

---

## 5. Target Users & Role Boundaries

### 5.1 Currently Supported Roles (Implemented)

#### 1. Administrator (`role="admin"`)
- **Profile:** System administrators, institutional IT leads, and Chief Facilities Officers.
- **Capabilities:**
  - Full access to all analytics, forecasting, optimization, and dataset views.
  - Role & privilege management viewing demo credentials (`admin/admin123`, `user/user123`).
  - Full CRUD operations on Campus Buildings (`POST/PUT/DELETE /api/buildings`) and Rooms (`POST/PUT/DELETE /api/rooms`).
  - Data ingestion management: uploading CSV/Excel datasets (`POST /api/dataset/upload`) with duplicate handling and data origin tagging.
  - Model retraining trigger: executing server-side chronological feature pipeline and model retraining (`POST /api/model/retrain`).
  - Generating and seeding synthetic scenario datasets into SQLite/MySQL.

#### 2. Campus Management / Standard User (`role="user"`)
- **Profile:** Academic department coordinators, scheduling officers, registrars, and faculty event organizers.
- **Capabilities:**
  - Interactive overview dashboard with KPI cards and actual vs. predicted trend lines.
  - 2D Spatial campus map exploration with building and room detail drawers.
  - Ad-hoc single-hour building forecasts and 13-hour operating day curve projections.
  - Spatiotemporal heatmaps (Day-of-Week vs. Hour, Building vs. Time, 14-day historical tracking).
  - Room-by-room capacity stress analysis.
  - Multi-request capacity optimization engine solver (submitting class requests, student counts, equipment constraints, and preferred buildings).
  - Exporting analytics tables and optimization outputs to CSV format.
  - Saving optimization recommendation records to database.

#### 3. Guest / Demo Mode (Unauthenticated)
- **Profile:** Casual evaluators, students, visitors, or stakeholders reviewing system capabilities without an account.
- **Capabilities:**
  - Read-only access to dashboard KPIs, 2D campus spatial explorer, forecasting query tools, spatiotemporal analytics, capacity rankings, and dataset preview.
  - Optimization solver evaluation (runs PuLP solver in memory; saving recommendations to user account is disabled).

### 5.2 Future User Roles (Planned / Future Scope)
- **Student Role:** Personalized mobile-responsive portal displaying real-time study space availability in the library and cafeteria queue forecasts.
- **Faculty / Instructor Role:** Self-service portal to request room swaps or report equipment defects.
- **IoT Hardware Service Account:** Dedicated API token service accounts for physical edge devices pushing telemetry.

---

## 6. User Personas

### Persona 1: Dr. Aris Thorne — Dean of Academic Affairs & Space Planning
- **Role:** Administrator / Senior Executive
- **Goals:** Ensure 100% of academic class schedules are accommodated without overcrowding; justify capital expenditures for campus building renovation.
- **Pain Points:** Lack of verifiable occupancy data; departmental complaints about small classrooms; fear of underutilizing expensive specialized facilities.
- **How System Helps:** Provides campus-wide KPI summaries, building utilization rankings, historical tracking trends, and mathematical verification that space allocation is optimized.

### Persona 2: Elena Vance — University Registrar & Timetable Coordinator
- **Role:** Standard User / Timetable Manager
- **Goals:** Allocate 20+ conflicting departmental makeup lecture requests during peak midday hours without double-booking rooms or violating equipment needs.
- **Pain Points:** Timetable conflicts take hours of manual checking; manual assignments often violate projector or computer lab requirements.
- **How System Helps:** Uses the PuLP Capacity Optimizer view: inputs student headcount, equipment criteria, and building preferences; receives guaranteed conflict-free assignments in under half a second.

### Persona 3: Marcus Chen — Campus Energy & Facilities Engineer
- **Role:** Operations & Sustainability Lead
- **Goals:** Reduce HVAC and electrical consumption by shutting down unoccupied zones during low-density operating hours.
- **Pain Points:** No advance notice of when buildings are effectively deserted; static 8am–8pm HVAC schedules waste power.
- **How System Helps:** Inspects 13-hour forecast curves and Building vs. Time heatmaps to identify low-density slots (e.g., upper floors of Academic Block 1 on Friday afternoons) and schedules plant operations accordingly.

---

## 7. Core Feature Inventory & Implementation Status

| Feature ID | Feature Name | Target User | Input | Processing Logic | Output | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **FEAT-01** | **User Authentication & RBAC** | All | Username, password | PBKDF2-HMAC-SHA256 (120k iterations) hashing; JWT HS256 token issuance (24h TTL); role checks. | Auth token, user badge, role-restricted UI elements. | **Implemented** |
| **FEAT-02** | **Executive KPI Dashboard** | All | Selected date/hour | Queries database for latest recorded actuals; computes campus forecast; calculates free rooms ($\ge 15$ seats) and peak hour. | 7 KPI cards, Canvas utilization bar chart, Plotly actual vs. predicted curve. | **Implemented** |
| **FEAT-03** | **2D Spatial Campus Explorer** | All | Target date, operating hour | Coordinates $(x, y)$ mapped on $100 \times 100$ canvas; joins building room inventories with actual & forecast occupancy. | Interactive spatial node map; colored utilization badges; slide-out room inventory drawer. | **Implemented** |
| **FEAT-04** | **Point-in-Time Occupancy Forecast** | All | Building code, date, hour, model selector | Pulls academic calendar context, lags from DB; passes 14-feature vector into ML regressor; computes 95% CI. | Predicted headcount, utilization %, status badge, room-level table, 95% confidence bounds. | **Implemented** |
| **FEAT-05** | **13-Hour Operating Day Projection** | All | Building code, date | Iterates hours 08:00–20:00; autoregressively chains previous-hour prediction into lag feature for subsequent hours. | Full-day continuous forecast curve; peak occupancy callout; room-level matrix. | **Implemented** |
| **FEAT-06** | **Spatiotemporal Density Heatmaps** | All | Building filter, target date | Aggregates DB occupancy across (Day-of-Week, Hour) and (Building, Hour); normalizes against capacity. | Viridis 7x13 DOW heatmap; Plasma Building vs. Time heatmap; 14-day tracking trend line. | **Implemented** |
| **FEAT-07** | **Capacity & Stress Analysis** | All | Building filter, date | Aggregates average and peak occupancy per room; computes utilization ratio and status category. | Sortable room ranking table; overcapacity warnings; CSV export. | **Implemented** |
| **FEAT-08** | **PuLP MILP Capacity Optimizer** | User, Admin | List of class requests (course, students, equipment, preferred building) | Solves Mixed-Integer Linear Program; usable capacity = capacity - forecast; enforces timetable conflict checks and equipment match; dummy penalty for slack. | Per-request room assignments, movement indicators (new/kept/moved/unmet), solve metrics, hourly analysis. | **Implemented** |
| **FEAT-09** | **Dataset Ingestion & Validation** | Admin | CSV / Excel file, data origin tag, duplicate flag | Parses file; validates column aliases; verifies non-negative counts; warns on capacity exceedance; bulk upserts. | Ingestion summary (inserted, updated, skipped, errors), origin tracking (`synthetic`, `imported`, `measured`). | **Implemented** |
| **FEAT-10** | **Synthetic Data Generator** | Admin | Date range, scenario (normal/exam/fest/vacation), noise level | Generates diurnal Poisson/sine arrival curves by room type; injects academic schedules and student/staff split; seeds DB. | Bulk database records seeded; synthetic CSV export file streaming. | **Implemented** |
| **FEAT-11** | **Live IoT Stream Simulation** | All | Room code, observed count | Simulates turnstile/camera payload; marks record with `data_origin="measured"`; commits to database. | Stream acknowledgment packet with simulation notice; real-time dashboard update. | **Implemented** |
| **FEAT-12** | **Model Comparison & Retraining** | Admin | Retrain button click | Spawns `ml/train_model.py` subprocess; fits LR, RF, LightGBM, XGBoost on chronological split; updates `meta.json`. | Multi-model benchmark table (MAE, RMSE, MAPE, R², time); live model reload. | **Implemented** |
| **FEAT-13** | **Campus Structure CRUD** | Admin | Building/Room schemas | RESTful endpoints verifying unique codes, non-negative capacity, and cascade deletions. | Updated building/room inventories across map, optimizer, and forecaster. | **Implemented** |
| **FEAT-14** | **Hardware IoT Turnstile Gateway** | System | Physical MQTT/RTSP streams | Network-level hardware integration. | Physical hardware edge ingestion. | **Not Implemented / Future Scope** |
| **FEAT-15** | **Two-Way ERP Sync** | System | SIS / Banner / Canvas API | Bi-directional API connectors for course schedules. | Automated write-back of room reassignments. | **Planned / Future Scope** |

---

## 8. User Stories with Acceptance Criteria

### User Story 1: Executive Space Monitoring
- **Story:** *As an institutional administrator, I want to view a real-time consolidated dashboard of campus occupancy so that I can immediately identify overcapacity buildings.*
- **Acceptance Criteria:**
  1. System displays 7 high-level KPI cards summarizing total recorded headcount, predicted occupancy, campus capacity, overall utilization %, overcapacity building count, free room count, and peak forecast hour.
  2. A building bar chart visually color-codes facilities: Green ($<50\%$), Amber ($50\%–79\%$), Red ($\ge 80\%$).
  3. A Plotly trend chart plots campus-wide actual vs. predicted occupancy across all 13 operating hours (08:00–20:00).
  4. Available rooms with at least 15 free seats are tabulated with a 1-click CSV export option.

### User Story 2: Hour-by-Hour Building Forecasting
- **Story:** *As a facilities scheduling officer, I want to forecast occupancy for a specific building and future date so that I can anticipate overcrowding before classes commence.*
- **Acceptance Criteria:**
  1. User can select building, date, operating hour (slider 08:00–20:00), and ML algorithm (XGBoost, LightGBM, Random Forest, Linear Regression).
  2. System returns predicted headcount, 95% confidence interval ($\pm$ margin of error), capacity, utilization %, academic calendar context (weather, temperature, semester), and room breakdown.
  3. Clicking "Full Day Curve" renders an interactive Plotly continuous projection curve across 08:00 to 20:00 using autoregressive lag chaining.

### User Story 3: Multi-Request Room Optimization
- **Story:** *As a department timetable manager, I want to submit multiple class requests with student counts and equipment needs to an optimization engine so that all classes are assigned suitable rooms without timetable clashes.*
- **Acceptance Criteria:**
  1. User can add arbitrary class requests specifying course name, student headcount, equipment checklist (computers, projector, whiteboard, sound system, lab equipment), and preferred building.
  2. PuLP MILP solver evaluates candidate rooms based on usable capacity (`capacity - predicted occupancy`), required equipment compatibility, and hard conflict checking against the database `timetable`.
  3. If requests exceed campus capacity, dummy slack variables guarantee mathematical feasibility and flag unaccommodated requests with clear explanations rather than failing.
  4. Execution completes and renders room assignments, movement tags (`new`, `kept`, `moved`, `no feasible room`), and empty seat counts in $\le 2.0$ seconds.

### User Story 4: Data Ingestion with Provenance Tracking
- **Story:** *As an administrator, I want to upload CSV or Excel attendance files with automatic column mapping so that historical data is ingested without strict column header formatting requirements.*
- **Acceptance Criteria:**
  1. System accepts `.csv`, `.xlsx`, and `.xls` files up to 15MB.
  2. System recognizes case-insensitive column aliases for date, hour, room, occupancy, capacity, room type, and floor.
  3. System validates against negative counts, flags capacity overflows as non-fatal warnings, and allows duplicate slot replacement.
  4. Ingested records are explicitly tagged with `data_origin` (`synthetic`, `imported`, or `measured`) to maintain complete audit transparency.

---

## 9. Functional Scope Breakdown

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            CAMPUSPULSE SCOPE                                │
├──────────────────────────────────────┬──────────────────────────────────────┤
│ CURRENT IMPLEMENTED SCOPE            │ PLANNED / FUTURE SCOPE               │
├──────────────────────────────────────┼──────────────────────────────────────┤
│ • FastAPI async REST API backend     │ • Physical IoT optical sensor wiring │
│ • SQLite/MySQL SQLAlchemy ORM        │ • Distributed MQTT broker gateway    │
│ • PBKDF2 + JWT Auth & RBAC           │ • Native mobile apps (iOS / Android) │
│ • 10-view Vanilla JS + Plotly SPA    │ • Automated 2-way SIS/ERP sync      │
│ • XGBoost/LightGBM/RF/LR forecasting │ • Automated HVAC BACnet integration  │
│ • PuLP MILP capacity optimizer       │ • Active student wayfinding portal   │
│ • 2D spatial coordinate campus map   │ • Facial recognition / turnstile HW  │
│ • CSV/Excel upload pipeline          │ • Real-time edge camera inference    │
│ • Synthetic generator with scenarios │ • Distributed Kubernetes deployment  │
│ • Simulated live sensor stream       │ • Keras LSTM default packaged model  │
└──────────────────────────────────────┴──────────────────────────────────────┘
```

---

## 10. Non-Goals (What the System is NOT Designed to Do)
- **Not a Personal Surveillance System:** CampusPulse tracks aggregate room headcounts and anonymized tallies; it does not perform individual biometric identification, student tracking, or facial surveillance.
- **Not a Replacement for University SIS:** The system is an analytics and optimization decision-support layer; it does not store grades, transcripts, or financial tuition records.
- **Not an Out-of-the-Box Hardware Appliance:** The software does not include physical camera hardware, infrared sensors, or turnstile turnstiles; it provides ingestion APIs and data standards for external hardware feeds.
- **Not an Off-Hours Night Tracker:** The primary operating schedule is restricted to campus operating hours (08:00 to 20:00). Requests outside these hours are flagged as "campus closed".

---

## 11. Operational & Business Benefits

1. **Capital Expenditure Optimization:** By exposing real spatial utilization, university boards can avoid multimillion-dollar construction of new lecture halls by reallocating underutilized blocks.
2. **Timetable Conflict Elimination:** Mathematical optimization eliminates human scheduling errors, room double-booking, and equipment mismatches.
3. **Enhanced Campus Safety:** Real-time overcapacity detection ensures fire code compliance and prevents hazardous hallway crowding.
4. **Energy Sustainability:** Predicted occupancy curves enable campus facility managers to optimize HVAC pre-cooling and lighting schedules, directly reducing carbon emissions and utility costs.
5. **Academic Continuity:** Flexible scenario synthesis (normal, exam, fest, vacation) prepares institutions for demand shocks and academic calendar fluctuations.

---

## 12. Success Criteria & KPIs

- **Functional Test Suite:** 100% pass rate on all automated unit and integration tests (`pytest tests/`).
- **Forecasting Performance:** Active models must maintain $R^2 \ge 0.94$ and $MAE \le 8.0$ persons on chronological test sets.
- **Optimizer Latency:** PuLP MILP allocation of up to 40 requests must solve and return within $1.5$ seconds.
- **API Response Latency:** Midday dashboard queries must respond in $\le 250\text{ ms}$ under local conditions.
- **Data Ingestion Robustness:** File parser must successfully ingest CSV/Excel files with standard alias variations without unhandled exceptions.

---

## 13. Risks and Assumptions

### Risks
- **Data Reality Gap:** Default demonstration data is synthetically structured; deploying to a physical campus without calibrating against real turnstile counts will lead to initial model bias.
- **Single Point of Hardware Failure:** External physical IoT streams may experience network dropout or sensor drift, requiring robust imputation strategies.
- **User Adoption Friction:** Academic department coordinators may resist algorithmic room reallocation due to territorial building preferences.

### Assumptions
- Campus operating hours are standardized between 08:00 and 20:00.
- Campus buildings can be logically represented within a 2D coordinate space for spatial distance penalties.
- Room capacities and room types remain static unless updated via administrator CRUD interfaces.
