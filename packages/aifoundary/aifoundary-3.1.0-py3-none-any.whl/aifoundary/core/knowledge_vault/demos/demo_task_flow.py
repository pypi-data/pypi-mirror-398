import requests

BOSS_AI_URL = "http://localhost:9000/task"

task = {
    "id": "task-001",
    "intent": "What knowledge exists in the system?"
}

response = requests.post(BOSS_AI_URL, json=task)

print("STATUS:", response.status_code)
print("RAW RESPONSE:")
print(response.text)
