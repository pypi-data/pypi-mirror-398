from procrastimate.core.models import TaskInput
import random
from procrastimate.wordList import vaguenessCalculator

EXCUSES = {
    "vague": {
        "manager": {
            "low": [
                "Taking a moment to align on the scope before proceeding.",
            ],
            "medium": [
                "The task requires further clarification across dependent areas before execution.",
            ],
            "high": [
                "We need to ensure cross-functional alignment and clarify ownership before moving forward.",
            ],
        }
    },
    "clear": {
        "manager": {
            "low": [
                "Scheduling this for tomorrow to ensure proper focus.",
            ],
            "medium": [
                "Pushing this to the next cycle to avoid rushed implementation.",
            ],
            "high": [
                "Deferring to ensure stability and avoid unintended side effects.",
            ],
        }
    }
}


def generate_excuse(task: TaskInput) -> str:
    vague = vaguenessCalculator.vagueChecker(task.task)

    clarity_key = "vague" if vague else "clear"
    audience = task.audience
    severity = task.severity

    try:
        templates = EXCUSES[clarity_key][audience][severity]
    except KeyError:
        # fallback safety net
        return "Re-evaluating priorities before proceeding."

    return random.choice(templates)


task_input = TaskInput(
    task="enable QR for subs flow",
    severity="high",
    audience="manager"
)
