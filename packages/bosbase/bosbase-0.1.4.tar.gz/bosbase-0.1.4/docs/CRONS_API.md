# Crons API - Python SDK

Cron jobs in BosBase can be triggered on demand through the SDK.

## List Cron Jobs

```python
jobs = pb.crons.get_full_list()
for job in jobs:
    print(job["name"], job["schedule"], job["status"])
```

## Trigger a Job

```python
pb.crons.run("rebuild-search-index")
```

The job ID is the slug shown in the dashboard. The call returns immediately; execution is handled asynchronously by the server.

## Use Cases

- Kick off expensive maintenance tasks from CI.
- Build CLI tooling for support engineers to run administrative actions safely.
- Integrate scheduled jobs with Git-based release pipelines.

## Tips

1. Cron endpoints require superuser authentication.
2. Inspect the request logs (filter by `collection = '_crons'`) to verify status and duration.
3. Combine with the Logs API or custom notifications to surface job results back to operators.
