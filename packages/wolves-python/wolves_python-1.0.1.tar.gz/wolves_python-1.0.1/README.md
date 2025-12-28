# Wolves Python SDK

This package is the Python counterpart of `sdk/js-client`, implementing the limited scope defined in:
`spec/wolves-python-sdk/wolves_python_sdk_feature_spec.md`.

## Usage

```python
from wolves_python import WolvesClient, WolvesUser

client = WolvesClient("YOUR_SDK_KEY")
user = WolvesUser(user_id="user_123", email="user@example.com")

client.initialize(user).wait()

exp = client.get_experiment(user, "my-experiment")
variant = exp.get_string("variant", "control")

client.log_event(user, "purchase", value=9.99, metadata={"currency": "USD"})
client.shutdown().wait()
```

## API surface (scope)

This SDK intentionally implements a limited subset:

- `WolvesClient.initialize(user) -> WolvesFuture[bool]`
- `WolvesClient.get_experiment(user, experiment_name) -> Experiment` (logs `exposure` every call)
- `WolvesClient.get_experiment_for_test(experiment_name, group_name, user=None) -> Experiment`
- `WolvesClient.log_event(user, event_name, value=None, metadata=None) -> None`
- `WolvesClient.shutdown() -> WolvesFuture[None]`

Non-goals (by design): feature gates, dynamic config helpers, persistence beyond process memory, multi-environment/options object.

## Testing

Run unit tests:

```bash
cd sdk/python
python -m pytest -q
```

Run integration tests (requires network):

```bash
cd sdk/python
WOLVES_RUN_INTEGRATION=1 python -m pytest -q -k integration
```

Run coverage (100% line + branch enforced):

```bash
cd sdk/python
python -m pytest --cov=wolves_python --cov-branch --cov-fail-under=100
```

## Examples

Run the basic example (requires network):

```bash
cd sdk/python
WOLVES_API_KEY=... python examples/basic.py
```
