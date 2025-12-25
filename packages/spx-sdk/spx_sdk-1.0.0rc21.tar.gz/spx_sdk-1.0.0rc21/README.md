

# SPX SDK

SPX SDK is the Python toolkit that powers Hammerheads' SPX simulation and automation platform. It provides the runtime building blocks for composing digital twins, orchestrating their lifecycle, validating configuration, and wiring custom logic into larger simulation pipelines.

## Why SPX SDK?

- **Composable component tree** – Build rich hierarchies by combining `SpxComponent` subclasses, containers, and reusable hooks.
- **Registry-driven configuration** – Register classes once and instantiate them from Python dicts, YAML, or JSON without hand-written factories.
- **Lifecycle orchestration** – Consistent `prepare → start → run → pause → stop → reset → destroy` transitions that propagate through the component tree.
- **Actions & attributes** – Model device behaviour declaratively and bind to inputs/outputs via the `actions` and `attributes` subsystems.
- **Diagnostics & validation** – Guard hooks, structured tracing, and JSON Schema validation help catch configuration issues early.
- **Extensibility first** – Override only what you need; compose existing mixins or build your own domains on top.

The repository also contains utilities for loading Python modules dynamically, registering simulation hooks, and integrating with CI pipelines.

## Installation

Install from PyPI:

```bash
pip install spx-sdk
```

Using Poetry inside a project:

```bash
poetry add spx-sdk
```

## Quickstart

```python
from spx_sdk.components import SpxComponent, SpxContainer
from spx_sdk.registry import register_class


@register_class(name="info")
class InfoComponent(SpxComponent):
    message: str = ""

    def run(self, *args, **kwargs):
        self.logger.info("InfoComponent → %s", self.message)


# Definition could be loaded from YAML/JSON; here we inline a dict for brevity.
definition = {
    "info": {
        "description": "Simple hello-world component",
        "message": "Hello from SPX!",
    }
}

# Build the component tree and execute a lifecycle step.
root = SpxContainer(definition, name="root")
root.prepare()
root.run()
```

### Configuration-driven

The same hierarchy can be produced from JSON, TOML, or any dict-like structure. `SpxContainer` walks the configuration tree, looks up registered classes (here `info`), and instantiates them with their definitions. Components can override `_populate` for custom parsing or rely on field assignment when attributes already exist.

### Hierarchy & Lifecycle Propagation

`SpxContainer` builds a component tree and propagates lifecycle calls to every descendant. Parent components call `prepare()`, `start()`, `run()`, `pause()`, and `stop()` on each child in insertion order—no extra wiring required.

```python
from spx_sdk.components import SpxComponent, SpxContainer


class Motor(SpxComponent):
    def prepare(self, *args, **kwargs):
        super().prepare(*args, **kwargs)
        self.logger.info("Motor prepared")

    def run(self, *args, **kwargs):
        super().run(*args, **kwargs)
        self.logger.info("Motor running")

    def pause(self, *args, **kwargs):
        super().pause(*args, **kwargs)
        self.logger.info("Motor paused")


class Gearbox(SpxComponent):
    def start(self, *args, **kwargs):
        super().start(*args, **kwargs)
        self.logger.info("Gearbox engaged")

    def stop(self, *args, **kwargs):
        super().stop(*args, **kwargs)
        self.logger.info("Gearbox stopped")


plant_definition = {
    "motor": {"class": "Motor"},
    "gearbox": {"class": "Gearbox"},
}

root = SpxContainer(plant_definition, name="line")
root.prepare()  # prepare() cascades to motor and gearbox
root.start()    # start() cascades, invoking Gearbox.start()
root.run()      # run() cascades, invoking Motor.run()
root.pause()    # pause() cascades, invoking Motor.pause()
root.stop()     # stop() cascades, invoking Gearbox.stop()
```

This pattern supports deep hierarchies: subcontainers receive the same lifecycle calls, so complex assemblies stay synchronised. Combine it with hooks or actions to react to specific transitions without modifying the core lifecycle methods.

## Diagnostics & Observability

SPX SDK collects structured diagnostics for every lifecycle operation. Two helper decorators keep insights consistent:

- `spx_sdk.diagnostics.guard` wraps public APIs and converts raised exceptions into rich diagnostic payloads. You decide whether errors bubble up or are translated to HTTP-compatible responses.
- `spx_sdk.diagnostics.trace` captures timing, context, and metadata for nested operations. Traces can be streamed to logs or aggregated by observability backends.

Example:

```python
from spx_sdk.diagnostics import guard, trace


class Sensor(SpxComponent):
    @guard("sensor.collect", bubble=False, http_status=500)
    def run(self):
        with trace(self, action="sensor.readout", extra={"units": "celsius"}):
            value = self._read_hardware()
            self.logger.debug("Sensor value=%s", value)
            self._publish(value)
```

Guards guard the outer API (`run`), while traces describe nested steps. All diagnostics include the component path, so log aggregation tools can correlate entries across the hierarchy.

## Validation Pipeline

Configuration validation is handled by a JSON Schema backend (`spx_sdk.validation._jsonschema_backend`). Key features:

- Load schemas directly from package resources or custom paths.
- Validate component definitions, actions, and attributes before runtime.
- Receive enumerated error messages with pointers to invalid data.

You can trigger validation programmatically:

```python
from spx_sdk.validation import JSONSchemaValidator

validator = JSONSchemaValidator(schema="schemas/component.json")
problems = validator.validate(definition)
if problems:
    for issue in problems:
        print(f"[{issue.path}] {issue.message}")
    raise ValueError("Invalid definition")
```

When using `SpxContainer`, validation hooks can run automatically: failed checks raise guarded diagnostics so CI pipelines fail fast with meaningful feedback. For CLI or automation use, wire the validator into your release tooling to block deployments when definitions drift from the contract.

### Defining Schemas

Schemas live alongside your components and describe allowed keys, required attributes, and value types. A minimal JSON Schema for the `InfoComponent` from the quickstart could look like this:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "InfoComponent",
  "type": "object",
  "properties": {
    "description": {
      "type": ["string", "null"],
      "description": "Optional human-readable summary."
    },
    "message": {
      "type": "string",
      "minLength": 1,
      "description": "Message emitted during run()."
    }
  },
  "required": ["message"],
  "additionalProperties": false
}
```

Store the schema under `schemas/info_component.json` (or similar) and point the validator to it:

```python
validator = JSONSchemaValidator(schema="schemas/info_component.json")
validator.raise_for_errors(definition)  # convenience helper that raises on failure
```

Complex hierarchies can compose schemas—refer to shared fragments with `$ref` or register multiple schemas per component type. Validation runs before lifecycle execution, so your system fails fast when configuration drifts from the contract.

## Key Concepts

- **SpxComponent** – Base class for every node. Handles child management, lifecycle, and configuration population. Each component exposes an optional `description` derived from its definition.
- **SpxContainer** – Specialised component that reads a configuration tree and instantiates registered children automatically.
- **Registry** – `@register_class` decorator exposes classes under stable names so definitions stay declarative.
- **Actions & attributes** – Pluggable behaviours that let components exchange data or invoke business logic during lifecycles.
- **Diagnostics** – Guard and trace helpers wrap operations with structured error handling and instrumentation.
- **Validation** – JSON Schema backend keeps definitions consistent and provides actionable error messages.

Explore the `spx_sdk` package to see how these pieces come together.

## Examples & Documentation

- Browse the [`examples/`](examples/) directory for end-to-end demonstrations.
- Review unit tests under [`tests/`](tests/) to understand expected behaviour and extension points.
- API docs are under active development; for now, inline docstrings and tests are the canonical reference.

## Contributing

1. Clone the repository and install dependencies:

   ```bash
   poetry install
   ```

2. Run the test suite before submitting changes:

   ```bash
   poetry run pytest
   ```

3. Follow the existing coding style and ensure new public APIs are covered by tests.

Bug reports and feature suggestions are welcome via GitHub issues or pull requests.

## License

SPX SDK is released under the MIT License. See [LICENSE](LICENSE) for details.
