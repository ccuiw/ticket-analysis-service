# CLAUDE.md

## Project Overview

This repository contains a full-stack ticket text analysis service.

Users submit ticket text through a React frontend. A FastAPI backend will eventually call a large language model, validate its structured output, repair invalid output when appropriate, and return a stable JSON response.

The initial version uses mock analysis results. Real LLM integration will be added incrementally.

## Technology Stack

### Backend

* Python 3.12+
* FastAPI
* Pydantic
* httpx
* pytest

### Frontend

* React
* TypeScript
* Vite
* Native fetch API
* Plain CSS or CSS Modules

### Infrastructure

* Git and GitHub
* Docker and Docker Compose
* GitHub Actions in a later phase

## Architecture Rules

Maintain clear boundaries between:

* API/interface layer
* Application orchestration
* Domain models and exceptions
* LLM provider adapters
* Prompt loading and rendering
* Output parsing
* Structural validation
* Business validation
* Repair and retry logic
* Evaluation scripts

The domain layer must not import FastAPI, model-provider SDKs, or frontend code.

The application service coordinates the analysis flow. It must not contain provider-specific HTTP or SDK logic.

Model-provider integrations must implement a shared abstraction so that providers can be replaced without rewriting the application service.

Model output must always be treated as untrusted external data until it has been parsed and validated.

## Prompt Rules

* Prompt text must be stored outside Python source files.
* Keep Zero-shot and Few-shot versions in separate files.
* Prompt versions must be identifiable in logs and evaluation results.
* Missing information must produce `null` or `"不确定"` according to the data contract.
* Prompts must prohibit fabrication.
* User ticket text must be clearly separated from instructions.
* Do not place API keys or secrets in prompts.

## API Rules

* Use the `/api/v1` prefix for versioned application endpoints.
* Use Pydantic models for request and response bodies.
* Maintain one explicit data contract between frontend and backend.
* Return clear validation and application errors.
* Do not expose raw stack traces to API clients.
* All future outbound HTTP calls must have an explicit timeout.
* All future retries must have a strict maximum attempt count.

## Frontend Rules

* Use TypeScript types corresponding to backend response models.
* Keep API calls outside React presentation components.
* Handle loading, success, validation error, and network error states.
* Do not introduce Redux, Next.js, or large UI frameworks without explicit approval.
* Prefer simple, readable components over premature abstraction.

## Testing Rules

* Backend tests must not call real LLM APIs.
* Use fake or mock LLM clients in unit and integration tests.
* Test parsing and validation separately from model quality evaluation.
* Never delete or weaken tests merely to make a build pass.
* Run relevant tests after every implementation change.

## Security Rules

* Never commit `.env`.
* Never commit API keys, tokens, passwords, private URLs, or user secrets.
* Keep `.env.example` limited to variable names and safe example values.
* Do not log secrets or full sensitive ticket content.
* Do not execute destructive Git commands.
* Do not use `git push --force`.
* Do not modify the `.git` directory.

## Git Rules

* Do not commit or push unless the user explicitly requests it.
* Do not work directly on `main` for feature implementation.
* Keep changes focused on the requested task.
* Before finishing a task, show:

  * changed files;
  * tests and checks executed;
  * command results;
  * remaining issues;
  * `git status`.

## Scope Rules

Do not add the following without explicit approval:

* databases;
* Redis;
* message queues;
* Kubernetes;
* LangChain;
* LangGraph;
* Dify;
* authentication systems;
* microservices;
* cloud deployment;
* analytics platforms;
* large UI frameworks.

Prefer the smallest implementation that is correct, testable, and extensible.

## Working Method

Before significant changes:

1. Inspect the relevant files.
2. Explain the intended changes.
3. Identify affected modules.
4. Implement only the current requested scope.
5. Run relevant tests and checks.
6. Report results accurately.

When requirements are ambiguous, preserve the existing architecture and choose the smallest reasonable implementation. Do not silently invent major product requirements.
