from patterns.planner_executor.graph import build_graph
import json

##def run_task(task: str):
app = build_graph()
    ##return app.invoke({"task": task})

task = "Create a simple 3-step plan for launching an AI chatbot product."
result = run_task(task)
print(json.dumps(result, indent=2, ensure_ascii=False))

"""
Create a simple 3-step plan for launching an AI chatbot product.
"""