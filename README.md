# COLIBI services

This repository manages backend services and utilizes the [PANTSBUILD](https://www.pantsbuild.org/) build system for handling the monorepository. You can find more details about [MONOREPO](https://monorepo.tools/) here.

The main advantage of using a monorepo is maintaining a consistent shared codebase. For instance, it ensures that the code generated from protobuf files remains consistent across all projects, avoiding the need to copy and paste changes in a polyrepo setup.

## How to Create a Virtual Environment for the IDE

The prerequisite for creating a virtual environment (VIRTUALENV) is the lockfile, as described in the section on [Third-party dependencies](https://www.pantsbuild.org/stable/docs/python/overview/third-party-dependencies) configuration. All dependencies must be versioned, for example:

```toml
alembic==1.13.3
asyncpg==0.29.0
cryptography==43.0.1
fastapi==0.115.0
grpcio==1.66.2
```

To enable dependency resolution, the configuration `enable_resolves = true` must be set to `True` under the Python system configuration. Additionally, set `py_generated_sources_in_resolve = ['python-default']` as described [here](https://www.pantsbuild.org/stable/reference/goals/export#py_generated_sources_in_resolve).

Once these configurations are completed, run `pants export --resolve=python-default` to generate the virtual environment.
