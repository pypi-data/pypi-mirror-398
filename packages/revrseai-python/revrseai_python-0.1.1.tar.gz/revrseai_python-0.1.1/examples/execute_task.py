from revrseai import RevrseAI

client = RevrseAI("YOUR_API_KEY")
result = client.execute(
    task_id="<task id>",
    endpoint="<endpoint name, e.g. 'login'>",
    data={"username": "<your username>", "password": "<your password>"},
)
print(result.status)
print(result.data)

auth_token = result.data.get("<field name, e.g. 'auth_token'>")

result = client.execute(
    endpoint_id="<task id>",
    endpoint="<endpoint name, e.g. 'jobs-feed'>",
    data={"auth_token": auth_token},
)
print(result.status)
print(result.data)
