from core.planner import plan_task
from core.executor import execute_plan

query = "open chrome"
plan = plan_task(query)
print("Plan:", plan)
results = execute_plan(plan)
print("Results:", results)
