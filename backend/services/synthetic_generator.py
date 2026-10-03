"""
High-fidelity synthetic occupancy data generator for campus spatiotemporal analytics.

Simulates:
- Room-type specific diurnal profiles (classrooms, labs, libraries, cafeteria, gyms)
- Academic scenarios: Normal Semester, Exam Season, Campus Fest, Summer/Winter Vacation
- Detailed breakdown: student vs. staff count, scheduled courses, exam flags
- Stochastic noise and realistic constraints (non-negative, capped at room capacity)
- Deterministic seeding option for repeatable scientific evaluation
"""
from __future__ import annotations

import math
import random
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple


COURSE_NAMES = [
    "CS101 - Intro to CS",
    "CS201 - Data Structures",
    "CS305 - DBMS",
    "AI401 - Machine Learning",
    "EE201 - Circuit Theory",
    "ME102 - Engineering Mechanics",
    "MATH201 - Linear Algebra",
    "PHY101 - Engineering Physics",
    "HUM105 - Tech Communication",
]


def _get_base_profile(room_type: str, hour: int, scenario: str) -> float:
    """
    Returns baseline expected occupancy percentage (0.0 to 1.0)
    for a given room type, hour of day, and academic scenario.
    """
    if hour < 7 or hour > 21:
        return 0.02  # late night / early morning security / maintenance

    if room_type == "classroom":
        if scenario == "exam":
            # Exam halls: structured 2-hour morning and afternoon shifts, 50% staggered seating
            if hour in (9, 10, 11) or hour in (14, 15, 16):
                return 0.50
            return 0.05
        elif scenario == "vacation":
            return 0.05 if (9 <= hour <= 15) else 0.01
        elif scenario == "fest":
            return 0.10 if (10 <= hour <= 14) else 0.02
        else:
            # Normal academic: Morning peak 9-12, Lunch dip 12-14, Afternoon peak 14-17
            if 9 <= hour <= 12:
                return 0.75 + 0.10 * math.sin((hour - 9) / 3 * math.pi)
            elif 12 < hour < 14:
                return 0.20
            elif 14 <= hour <= 17:
                return 0.65 + 0.10 * math.sin((hour - 14) / 3 * math.pi)
            else:
                return 0.15

    elif room_type == "lab":
        if scenario == "vacation":
            return 0.08
        if scenario == "fest":
            return 0.05
        # Labs are active in 3-hour afternoon blocks
        if 13 <= hour <= 17:
            return 0.70
        elif 9 <= hour <= 12:
            return 0.40
        return 0.10

    elif room_type == "library":
        if scenario == "exam":
            # High demand during exams all day
            if 8 <= hour <= 21:
                return 0.85 + 0.10 * math.sin((hour - 8) / 13 * math.pi)
            return 0.25
        elif scenario == "vacation":
            return 0.20 if (9 <= hour <= 17) else 0.05
        else:
            # Normal library profile: steady climb peaking 11am-5pm
            if 8 <= hour <= 20:
                return 0.55 + 0.25 * math.sin((hour - 8) / 12 * math.pi)
            return 0.10

    elif room_type == "cafeteria":
        if scenario == "fest":
            return 0.80 if (11 <= hour <= 18) else 0.30
        if scenario == "vacation":
            return 0.25 if (12 <= hour <= 14) else 0.05
        # Breakfast peak 8-9, Lunch peak 12-14, Evening snacks 16-18
        if 8 <= hour <= 9:
            return 0.45
        elif 12 <= hour <= 14:
            return 0.88
        elif 16 <= hour <= 18:
            return 0.55
        elif 9 < hour < 12 or 14 < hour < 16:
            return 0.20
        return 0.05

    elif room_type in ("meeting", "admin"):
        if 9 <= hour <= 17:
            return 0.50 if scenario != "vacation" else 0.20
        return 0.05

    elif room_type == "auditorium":
        if scenario == "fest":
            return 0.90 if (10 <= hour <= 19) else 0.20
        # Normal days: mostly quiet unless afternoon seminars
        if hour in (14, 15, 16):
            return 0.40
        return 0.02

    elif room_type == "gym":
        # Morning & evening peaks
        if 6 <= hour <= 8:
            return 0.65
        elif 17 <= hour <= 20:
            return 0.75
        return 0.10

    # Default fallback
    return 0.30 if (9 <= hour <= 17) else 0.05


def generate_synthetic_records(
    rooms: List[dict],
    start_date: date,
    end_date: date,
    scenario: str = "normal",
    noise_level: float = 0.10,
    seed: Optional[int] = 42,
) -> List[dict]:
    """
    Generates a list of dictionaries matching the Occupancy schema.

    rooms: list of dicts with keys {'id', 'code', 'room_type', 'capacity', 'building_code'}
    """
    if seed is not None:
        random.seed(seed)

    records: List[dict] = []
    current_date = start_date

    while current_date <= end_date:
        dow = current_date.weekday()  # 0=Monday, 6=Sunday
        is_weekend = dow >= 5
        date_str = current_date.strftime("%Y-%m-%d")

        # Weekend factor
        weekend_multiplier = 0.15 if dow == 6 else (0.40 if dow == 5 else 1.0)

        for hour in range(8, 21):  # standard campus operational hours 8 AM to 8 PM
            for r in rooms:
                rtype = (r.get("room_type") or "classroom").lower()
                capacity = r.get("capacity", 50)
                room_id = r.get("id")
                room_code = r.get("code")

                base_occ = _get_base_profile(rtype, hour, scenario)
                base_occ *= weekend_multiplier

                # Add Gaussian / Poisson noise
                noise = random.gauss(0, noise_level)
                final_util = max(0.0, min(1.0, base_occ + noise))
                headcount = int(round(final_util * capacity))

                # Scheduled class tag
                scheduled_course = None
                is_exam_flag = 1 if (scenario == "exam" and not is_weekend and 9 <= hour <= 17) else 0

                if rtype in ("classroom", "lab") and not is_weekend and headcount > 5:
                    if is_exam_flag:
                        scheduled_course = "Mid-Term / Final Examination"
                    elif (9 <= hour <= 12) or (14 <= hour <= 17):
                        scheduled_course = random.choice(COURSE_NAMES)

                # Student & Staff breakdown
                if headcount > 0:
                    staff_cnt = 1 if rtype in ("classroom", "lab") and scheduled_course else max(1, int(round(headcount * 0.05)))
                    student_cnt = max(0, headcount - staff_cnt)
                else:
                    staff_cnt = 0
                    student_cnt = 0

                records.append({
                    "room_id": room_id,
                    "room_code": room_code,
                    "date": date_str,
                    "hour": hour,
                    "occupancy_count": headcount,
                    "students_count": student_cnt,
                    "staff_count": staff_cnt,
                    "scheduled_class": scheduled_course,
                    "is_exam": is_exam_flag,
                    "data_origin": "synthetic",
                })

        current_date += timedelta(days=1)

    return records
