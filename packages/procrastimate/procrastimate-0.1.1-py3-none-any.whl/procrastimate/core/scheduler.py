from datetime import datetime, timedelta
import random
from procrastimate.core.models import TaskInput

BASE_DELAY = {
    "low": 1,
    "medium": 3,
    "high": 5,
}
VAGUE_MULTIPLIER = 1.5

# Scheduling is about plausibility, not efficiency.

task_input = TaskInput(
    task="enable QR for subs flow",
    severity="high",
    audience="manager"
)


def suggest_new_date(task: TaskInput, is_vague: bool) -> datetime:
    base_days = BASE_DELAY.get(task.severity, 2)

    if is_vague:
        base_days = int(base_days * VAGUE_MULTIPLIER)

    # Small randomness for realism
    jitter = random.choice([0, 1])

    return datetime.now() + timedelta(days=base_days + jitter)

