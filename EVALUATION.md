# Evaluation

Evaluation runner: [evaluation/evaluate.py](evaluation/evaluate.py)

Task set: [evaluation/tasks.json](evaluation/tasks.json)

Sample repository: [examples/sample-repository](examples/sample-repository)

## Metrics captured

- task success/failure
- duration
- iterations
- changed files
- input/output tokens

## Run

```bash
python evaluation/evaluate.py --api-base-url http://localhost:8080 --api-key dev-local-key --workspace-root .
```

## Expected MVP demo task

- `Fix the authentication timeout bug and update the tests.`

The mock model path is designed to demonstrate edit -> test fail -> analyze -> test update -> pass.
