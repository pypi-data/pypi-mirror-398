This `README.md` is designed to be the definitive guide for your team. It explains the "Why" and the "How," shifting the focus from manual configuration to a **Foundation-first** approach.

---

# GuardianHub SDK (Foundation)

Welcome to the core backbone of the GuardianHub ecosystem. This SDK is designed to provide **Zero-Config** capabilities for all microservices. By using this library, your service automatically inherits our standards for configuration, logging, and observability.

## 🚀 The "One-Minute" Setup

The goal of this SDK is to allow you to focus on business logic. You no longer need to manage `config.json` files or manually set up OpenTelemetry.

### 1. Installation

```bash
pip install guardianhub-sdk

```

### 2. Implementation

In your microservice's `main.py`, simply call the initialization utility:

```python
from fastapi import FastAPI
from guardianhub.utils.fastapi_utils import initialize_guardian_service
from guardianhub import settings

app = FastAPI(title="My Service")

# This single call configures:
# - Environment-aware settings (K8s vs Local)
# - JSON Logging
# - Prometheus Metrics (/metrics)
# - Health Checks (/health)
# - OpenTelemetry Tracing (to Langfuse & OTEL Collector)
initialize_guardian_service(app)

@app.get("/task")
async def do_work():
    # Use the pre-configured LLM client
    # It already knows the Aura-LLM endpoint based on the environment
    from guardianhub.clients import LLMClient
    client = LLMClient()
    return await client.generate("Hello world")

```

---

## 🛠 Configuration Philosophy

We have moved away from local `config.json` files in every repository. The SDK now uses a **Hierarchical Provider** system:

1. **SDK Defaults:** Hardcoded "safe" fallbacks (usually `localhost`).
2. **Bundled Profiles:** The SDK contains `config_dev.json` and `config_kubernetes-dev.json`. It detects your `ENVIRONMENT` variable and loads the correct infrastructure URLs automatically.
3. **Environment Overrides:** Any setting can be overridden using the `GH_` prefix.
* Example: To change the LLM temperature without code changes, set `GH_LLM__TEMPERATURE=0.7`.
* Example: To point to a specific Vector DB, set `GH_ENDPOINTS__VECTOR_SERVICE_URL=http://my-db:8005`.



### Standard Endpoints

Every service using `initialize_guardian_service(app)` exposes:

* `GET /health`: Returns uptime, version, environment, and active request count.
* `GET /metrics`: Prometheus-compatible metrics.

---

## 📊 Observability & Tracing

The SDK automatically instruments both **incoming FastAPI requests** and **outgoing HTTPX calls**.

* **Trace Propagation:** Traces automatically flow from Service A to Service B via W3C headers.
* **Langfuse Integration:** Traces are sent to the centralized Langfuse instance for LLM monitoring.
* **Excluded URLs:** Health checks and metrics endpoints are automatically filtered out of your traces to keep them clean.

---

## 🛡️ Best Practices for the Team

* **No Local Configs:** Do not create `config.json` in your service repo. If an endpoint is missing, update it in the SDK and bump the version.
* **Use the `settings` object:** Never use `os.getenv` directly for shared infra. Use `from guardianhub import settings`.
* **Secrets:** Sensitive keys (Postgres passwords, API keys) should be injected via K8s Secrets into environment variables following the `GH_` pattern.

---

To explain this to the team, you need to highlight that we’ve moved from **"Hardcoded Configuration"** to **"Dynamic Parameters."** The SDK now acts as a smart proxy. It doesn't just hold values; it resolves them based on where the code is running. Here is the detailed breakdown of how we manage parameters in the `CoreSettings` system.

---

## 1. The Parameter Hierarchy (The "Resolution Chain")

When a developer calls `settings.endpoints.VECTOR_SERVICE_URL`, the SDK looks for the value in this specific order. **The first one it finds wins.**

| Priority | Source | Use Case |
| --- | --- | --- |
| **1 (Highest)** | **Environment Variables** | Injecting Secrets (DB Passwords) or emergency overrides. |
| **2** | **Direct Code Initialization** | Used mostly in unit tests to mock behavior. |
| **3** | **Bundled JSON Profiles** | **The Backbone.** Defines where internal services live in K8s. |
| **4 (Lowest)** | **Python Class Defaults** | The safety net. Usually points to `localhost`. |

---

## 2. Parameter Grouping (The "Pillars")

We don't have a flat list of 50 variables. We group parameters into **Pillars** so the team can find what they need via autocompletion.

### A. The `service` Pillar

Defines "Who am I?"

* `settings.service.name`: Used for Logging and Jaeger/OTEL traces.
* `settings.service.port`: The port the internal server listens on.

### B. The `endpoints` Pillar

Defines "Where is everyone else?"

* These are strictly URL strings.
* **Note:** We use `extra="allow"` here. If you add `NEW_AI_SERVICE_URL` to the JSON, it is immediately available via `settings.endpoints.get("NEW_AI_SERVICE_URL")` without needing an SDK code update.

### C. The `llm` Pillar

Defines "How do I think?"

* Standardizes AI behavior across the fleet. If we decide `temperature` should be `0.2` instead of `0.1` for the whole company, we change it here once.

---

## 3. Naming Convention for Overrides

To override a nested parameter via the environment (e.g., in a Dockerfile or K8s Manifest), we use the **Double Underscore (`__`)** convention.

**Pattern:** `GH_[PILLAR]__[PARAMETER]`

* **To change the LLM model:** `export GH_LLM__MODEL_NAME="gpt-4o"`
* **To change the Vector URL:** `export GH_ENDPOINTS__VECTOR_SERVICE_URL="http://custom-vector-db:8005"`
* **To change Logging Level:** `export GH_LOGGING__LEVEL="DEBUG"`

---

## 4. How We Manage Secrets

**Rule:** No passwords or API Keys are ever stored in the `config_*.json` files.

The SDK defines the *field* in the `LLMSettings` or `ServiceEndpoints` class, but we leave the value as a placeholder. The team must map K8s Secrets to the corresponding `GH_` environment variable:

```yaml
# Kubernetes Deployment Example
env:
  - name: GH_LLM__API_KEY
    valueFrom:
      secretKeyRef:
        name: llm-secrets
        key: api_key

```

---

## 5. Maintenance: Adding a New Parameter

If a service needs a new configuration parameter (e.g., `RETRY_COUNT`):

1. **Does it apply to everyone?** Add it to `src/guardianhub/config/config_dev.json` and `config_kubernetes-dev.json`.
2. **Is it a new "Pillar"?** Add a new `BaseModel` class in `settings.py`.
3. **Is it just a URL?** Just add it to the `endpoints` section of the JSON files.

---

## 🛡️ Summary for the Team

> "The SDK is the **Backbone**. The JSON files are the **Maps**. The Environment Variables are the **Keys**."

By following this, we ensure that if we move our entire infrastructure from AWS to Azure, or from one K8s namespace to another, we only update the JSON files in the SDK, and every microservice "teleports" to the new location on its next restart.

**Would you like me to create a "Configuration Cheat Sheet" table that lists all current standard parameters and their default values for the team to print out?**

## 🏗️ Contributing to the SDK

If you need to add a new shared client (e.g., Redis, S3) or a new endpoint:

1. Add the endpoint to `src/guardianhub/config/config_*.json`.
2. (Optional) Add a Pydantic model in `settings.py` if you want strict typing.
3. Bump the version using `./scripts/bump_version.sh`.
4. Publish the new wheel.

---

**Would you like me to generate a `bootstrap_service.py` script now, which your team can run to instantly generate a folder with this exact structure for a new microservice?**