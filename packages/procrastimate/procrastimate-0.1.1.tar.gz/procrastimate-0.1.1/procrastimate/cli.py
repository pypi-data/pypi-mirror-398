import argparse
from procrastimate.core.models import TaskInput
from procrastimate.wordList.vaguenessCalculator import vagueChecker
from procrastimate.core.excuses import generate_excuse
from procrastimate.core.scheduler import suggest_new_date

def main():
    parser = argparse.ArgumentParser(
        description="ProcrastiMate — professional-grade procrastination"
    )
    parser.add_argument("task", help="Task to procrastinate on")
    parser.add_argument("--severity", choices=["low", "medium", "high"], default="medium")
    parser.add_argument("--audience", choices=["manager", "client", "self"], default="manager")


    args = parser.parse_args()

    task_input = TaskInput(
        task=args.task,
        severity=args.severity,
        audience=args.audience
    )

    vague = vagueChecker(task_input.task)
    excuse = generate_excuse(task_input)
    new_date = suggest_new_date(task_input, vague)

    print("\n🕒 ProcrastiMate Decision\n")
    print(f"Task      : {task_input.task}")
    print(f"Vague     : {'Yes' if vague else 'No'}")
    print(f"Excuse    : {excuse}")
    print(f"New Date  : {new_date.strftime('%Y-%m-%d')}")

    return 0
