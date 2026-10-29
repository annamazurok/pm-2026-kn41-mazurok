import csv
import math
import random
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
N = 10_000
SEED = 2026
SPRINT_DAYS = 14


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


velocity_rows = read_csv(ROOT / "lr09_forecast" / "velocity.csv")
estimate_rows = read_csv(ROOT / "lr08_poker" / "estimates.csv")
backlog_rows = read_csv(ROOT / "lr06_backlog" / "backlog.csv")

velocity = [int(float(row["points_done"])) for row in velocity_rows]
closed_points = sum(velocity)
end_first = date.fromisoformat(velocity_rows[0]["end_date"])
end_last = date.fromisoformat(velocity_rows[-1]["end_date"])

rel1_stories = {
    row["story_id"] for row in backlog_rows if row["release"] == "REL-1"
}
estimates = {
    row["story_id"]: int(float(row["final_estimate"]))
    for row in estimate_rows
}
total_rel1 = sum(estimates[story] for story in rel1_stories)
remaining_rel1 = total_rel1 - closed_points
if remaining_rel1 < 0:
    raise ValueError("Закритих points більше, ніж оцінений обсяг REL-1")


def simulate(points, rng):
    results = []
    for _ in range(N):
        remaining = points
        sprints = 0
        while remaining > 0:
            remaining -= rng.choice(velocity)
            sprints += 1
            if sprints > 10_000:
                raise RuntimeError("Симуляція не просувається; перевірте velocity")
        results.append(sprints)
    results.sort()
    return results[math.ceil(N * 0.50) - 1], results[math.ceil(N * 0.85) - 1]


def forecast_row(name, points, baseline, date_offset, rng):
    p50, p85 = simulate(points, rng)
    return [
        name,
        points,
        N,
        p50,
        p85,
        (baseline + timedelta(days=p50 * SPRINT_DAYS + date_offset)).isoformat(),
        (baseline + timedelta(days=p85 * SPRINT_DAYS + date_offset)).isoformat(),
    ]


rng = random.Random(SEED)
rows = [
    forecast_row("Весь перший реліз", total_rel1, end_first, -SPRINT_DAYS, rng),
    forecast_row(
        "Залишок після двох спринтів",
        remaining_rel1,
        end_last,
        0,
        rng,
    ),
]

with (ROOT / "lr09_forecast" / "forecast.csv").open(
    "w", encoding="utf-8", newline=""
) as file:
    writer = csv.writer(file, lineterminator="\n")
    writer.writerow(
        [
            "scenario",
            "remaining_points",
            "simulations",
            "p50_sprints",
            "p85_sprints",
            "p50_date",
            "p85_date",
        ]
    )
    writer.writerows(rows)
