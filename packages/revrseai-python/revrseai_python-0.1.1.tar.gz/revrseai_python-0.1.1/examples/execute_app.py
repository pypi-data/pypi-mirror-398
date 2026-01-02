from revrseai import RevrseAI

client = RevrseAI("YOUR_API_KEY")
result = client.execute(
    app="Job Today",
    endpoint="<endpoint name, e.g. 'login'>",
    data={"username": "<your username>", "password": "<your password>"},
)
print(result.status)
print(result.data)
