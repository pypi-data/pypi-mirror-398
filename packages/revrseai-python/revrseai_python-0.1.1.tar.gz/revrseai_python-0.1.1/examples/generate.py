from revrseai import RevrseAI

client = RevrseAI("YOUR_API_KEY")
task = client.generate(
    "Log into Job Today using my username and password and get the jobs on my feed",
    secrets={"username": "<your username>", "password": "<your password>"},
)
result = task.wait_till_done()
result.print_markdown_documentation()

result.export_markdown_documentation("job_today_documentation.md")
print("Documentation exported to job_today_documentation.md")
