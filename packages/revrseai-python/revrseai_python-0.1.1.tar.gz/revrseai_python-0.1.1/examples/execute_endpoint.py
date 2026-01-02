from revrseai import RevrseAI

client = RevrseAI("YOUR_API_KEY")
result = client.execute(
    endpoint_id="<endpoint id>",
    data={"username": "<your username>", "password": "<your password>"},
)
print(result.status)
print(result.data)
