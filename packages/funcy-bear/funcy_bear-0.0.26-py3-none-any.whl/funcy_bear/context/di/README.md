# funcy_bear.context.di

Dependency-injection primitives that keep Bear Dereth’s services modular and
testable. The module provides a declarative container, provider markers, and
resource helpers that wrap context managers or singletons.

> Note: `__experimental_provider.py` is intentionally excluded until it lands in
> production.

## Core Pieces
- `DeclarativeContainer` (`__container.py`): Metaclass-driven registry that
  captures `Resource`/`Singleton` declarations, starts them automatically, and
  exposes registered services.
- `Provide` / `Provider` (`__wiring.py`): Marker used in function signatures to
  request services by name. Plays nicely with the `inject` decorator.
- `inject` / `parse_params` (`__wiring.py`): Runtime wiring that inspects
  callables, resolves `Provide[...]` parameters, and overrides the container
  cache with concrete instances.
- `Resource` / `Singleton` (`_resources.py`): Wrappers for context managers,
  generator-based factories, and eager/lazy singletons.

Importing `funcy_bear.context.di` re-exports the public surface so call sites can do:

```python
from funcy_bear.context.di import DeclarativeContainer, Provide, inject, Resource, Singleton
```

---

## Declarative Containers

Containers use a metaclass to index attributes declared on subclasses. Resource
attributes are removed from the class body, registered under normalized keys,
and eagerly started when the container class is created.

```python
from funcy_bear.context.di import DeclarativeContainer, Resource, Singleton

def build_console() -> Console:
    return Console(highlight=False)

class AppContainer(DeclarativeContainer):
    console = Resource(build_console)
    secrets = Singleton(dict)
```

Key behaviors:
- `start()` instantiates every resource/singleton and caches the result.
- `services` holds live instances; `service_types` tracks annotated types for
  non-resource attributes.
- `register_teardown(name, callback, priority=float("inf"))` enqueues cleanup.
- `shutdown()` consumes the teardown queue and clears registrations.
- Containers are context managers; use `with AppContainer:` to ensure startup +
  cleanup wrap a block.

Overrides can be supplied with `AppContainer.override("console", fake_console)`
which is useful for tests.

---

## Provider Markers & Injection

`Provide` is both a class and a marker. Using it as a default value signals the
injector to fetch that service from the container.

```python
from funcy_bear.context.di import Provide, inject
from .container import AppContainer

@inject
def report(message: str, console = Provide[AppContainer.console]):
    console.print(f"🚀 {message}")

Provide.set_container(AppContainer)  # usually done during app bootstrap
report("Hello DI!")
```

What happens under the hood:
1. `inject` calls `parse_params`, binding provided arguments.
2. Parameters whose default is a `Provide` marker are inspected via `Parser`.
3. The parser resolves the desired type (from annotations, string hints, or
   existing cached instances).
4. Instances are looked up or created, inserted into the container with
   `override`, and the function is invoked with the resolved dependency.
5. Any failures populate `Provide.default.result` with an exception so callers
   can inspect why wiring failed.

You can also call `Provide[...]` directly to get a provider instance for manual
wiring, or set `Provide.set_container(AppContainer)` once during startup to
avoid passing the container each time.

---

## Resources vs. Singletons

### `Singleton`
- Wraps a class or factory that should only run once.
- Thread-safe through an `RLock`; `instance` is a cached property.
- `reset_instance()` clears the cached value (used during teardown).
- `from_instance(existing)` builds a singleton around an already constructed
  object—handy for plugging in mocks.

### `Resource`
- Accepts callables, context managers, or `@contextmanager` generators.
- Detects objects implementing `__enter__/__exit__` and preserves the exit
  handler for shutdown.
- If the factory returns other `Resource`/`Singleton` instances as arguments,
  `_resolve_args` ensures those dependencies are resolved before invocation.
- Works both lazily (via `get()`) and eagerly (container startup).

Both types expose `.service_name` which is auto-filled from the factory/class
name when not set explicitly.

---

## Wiring Tips
- Always annotate parameters when possible; the parser leans on annotations to
  discover concrete types.
- If you need conditional construction, override the service after startup
  rather than mutating container internals.
- Use teardown callbacks to close DB connections, stop background workers, etc.,
  and give critical cleanup a lower priority value so it runs earlier.
- Reset singletons between tests via `Singleton.reset_instance()` or
  `AppContainer.shutdown()` to avoid cross-test leakage.

Stay wired, stay cozy, Bear! 🐻🔌✨
