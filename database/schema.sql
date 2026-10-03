-- ============================================================================
-- Smart Campus Occupancy Forecasting — MySQL 8 reference schema
-- The application defaults to SQLite (works out of the box).
-- To use MySQL instead, set the env var:
--   CAMPUS_DATABASE_URL=mysql+pymysql://student:pass@localhost/campus
-- The backend creates these tables automatically via SQLAlchemy.
-- ============================================================================

CREATE DATABASE IF NOT EXISTS campus CHARACTER SET utf8mb4;
USE campus;

CREATE TABLE IF NOT EXISTS users (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(50)  NOT NULL UNIQUE,
    full_name     VARCHAR(100) NOT NULL DEFAULT '',
    password_hash VARCHAR(200) NOT NULL,
    role          VARCHAR(20)  NOT NULL DEFAULT 'user',
    created_at    DATETIME     DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS buildings (
    id   INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(10)  NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    x    INT NOT NULL DEFAULT 0,
    y    INT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS rooms (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    code       VARCHAR(20) NOT NULL UNIQUE,
    building_id INT NOT NULL,
    room_type  VARCHAR(30) NOT NULL DEFAULT 'classroom',
    capacity   INT NOT NULL,
    CONSTRAINT fk_rooms_building FOREIGN KEY (building_id)
        REFERENCES buildings(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS occupancy (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    room_id         INT NOT NULL,
    date            DATE NOT NULL,
    hour            TINYINT NOT NULL,
    occupancy_count INT NOT NULL,
    INDEX idx_occ_room_date (room_id, date, hour),
    CONSTRAINT fk_occ_room FOREIGN KEY (room_id) REFERENCES rooms(id)
);

CREATE TABLE IF NOT EXISTS timetable (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    course      VARCHAR(80) NOT NULL,
    room_id     INT NOT NULL,
    day_of_week TINYINT NOT NULL,          -- 0=Monday .. 6=Sunday
    hour        TINYINT NOT NULL,
    semester    TINYINT NOT NULL DEFAULT 1,
    CONSTRAINT fk_tt_room FOREIGN KEY (room_id) REFERENCES rooms(id)
);

CREATE TABLE IF NOT EXISTS events (
    id   INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS predictions (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    user_id             INT,
    building_id         INT,
    date                DATE NOT NULL,
    hour                TINYINT NOT NULL,
    predicted_occupancy INT NOT NULL,
    model               VARCHAR(30) NOT NULL DEFAULT 'xgb',
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_pred_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT fk_pred_building FOREIGN KEY (building_id) REFERENCES buildings(id)
);

CREATE TABLE IF NOT EXISTS recommendations (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT,
    date       DATE NOT NULL,
    hour       TINYINT NOT NULL,
    payload    JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_rec_user FOREIGN KEY (user_id) REFERENCES users(id)
);