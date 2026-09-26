# Astro Intelligence OS

A professional-grade, research-oriented Astrology Intelligence Platform.

## Architecture

- **Python**: Deterministic astronomy/astrology calculation engine, AstroState, methods, evaluation, ML research.
- **TypeScript/Node.js**: Web UI, API, orchestration, agent runtime, research cockpit.
- **PostgreSQL**: Primary database.
- **Redis**: Caching, queues, job coordination.
- **Docker**: Reproducible environments.

## Repository Structure

```
/engine          — Python calculation engine (astronomy, astro-state, methods, evaluation)
/apps            — TypeScript applications (web, api, research-cockpit)
/packages        — Shared TypeScript packages
/services        — Microservices (method-runner, ensemble, agents)
/contracts       — Versioned API schemas shared between Python ↔ TypeScript
/tests           — Cross-cutting integration & regression tests
/docs            — Architecture, specs, decisions
/scripts         — Fixtures, benchmarks, migrations
/docker          — Docker configurations
```

## Getting Started

```bash
# Python engine
cd engine && pip install -e ".[dev]"

# TypeScript apps
cd apps/api && npm install && npm run dev
```

## Development Philosophy

See [MASTER_ARCHITECTURE.md](docs/MASTER_ARCHITECTURE.md) and [IMPLEMENTATION_ROADMAP.md](docs/IMPLEMENTATION_ROADMAP.md).
