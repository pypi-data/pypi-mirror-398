from revrseai import RevrseAI

client = RevrseAI("YOUR_API_KEY")
task = client.info("Job Today")
task.print_markdown_documentation()

task.export_markdown_documentation("job_today_documentation.md")
print("Documentation exported to job_today_documentation.md")
