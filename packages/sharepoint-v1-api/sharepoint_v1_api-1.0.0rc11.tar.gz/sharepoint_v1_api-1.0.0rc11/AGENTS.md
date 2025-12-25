# AGENTS.md

This file provides guidance to agents when working with code in this repository.

### Project stack (non‑obvious)
- **Language**: Python ≥ 3.6 (type‑annotated, uses f‑strings).
- **Package manager**: `pip` (editable install via `pip install -e .`). No `requirements.txt`; dependencies are declared in `setup.py` (`requests`, `requests‑ntlm`).
- **Entry point**: Import `SharePointAPI` from `sharepoint_api.SharePointAPI`. The class method `SharePointAPI._compact_init(creds)` is the *canonical* way to create an instance – it bypasses the normal constructor and injects credentials directly.

### Build / install / lint / test commands (non‑obvious)
- **Install editable**: `pip install -e .` (required to pick up the `sharepoint_api` package in the workspace).
- **Run a single test**: The project does **not** include a test framework; there are no `pytest` or `unittest` configurations. If tests are added later, the conventional command would be `pytest path/to/test_file.py::test_name`. Until such a framework exists, there are no built‑in test commands.
- **Linting**: No lint configuration files (`.flake8`, `pyproject.toml` lint section, etc.) are present. Use standard tools (`flake8`, `black`, `isort`) manually if desired.

### Code style conventions (non‑obvious)
- **Naming**:
  - Classes use **PascalCase** (e.g., `SharePointAPI`, `SharePointList`).
  - Methods and functions use **snake_case**.
  - Private/internal helpers are prefixed with an underscore (e.g., `_api_get_call`).
- **Type hints**: Most public methods are annotated with return types; follow this pattern for new code.
- **Docstrings**: Triple‑quoted strings are used for public APIs; keep this style.
- **Imports**: All imports are absolute (e.g., `from sharepoint_api.SharePointAPI import SharePointAPI`). Do not use relative imports inside the package.
- **Error handling**: Network errors raise `ConnectionError` after printing status and response; replicate this pattern for new API calls.

### Project‑specific utilities & hidden patterns
- **HTTP authentication**: All requests use `HttpNtlmAuth(self.username, self.password)` – the library expects NTLM credentials; do **not** replace with plain `requests` auth.
- **Header manipulation**:
  - For **merge** operations, the header `X-HTTP-Method: MERGE` is added.
  - For **overwrite** (PUT) operations, the header `X-HTTP-Method: PUT` is added.
  - These headers are required by SharePoint’s REST API and are not obvious from the README.
- **Form digest handling**: Calls to `/_api/contextinfo` retrieve a `FormDigestValue` that must be passed in subsequent POST/PUT/DELETE calls. Forgetting this causes 403 errors.
- **File upload/download**: The `copyto` endpoint is used for copying files within SharePoint; the method builds the target path manually (`out_path = f"/cases/{sharepoint_site}/{out_folder}/{out_file}"`). Ensure `out_folder` and `out_file` are correctly set; the default filename is `"copy of " + file`.
- **Compact initializer**: `SharePointAPI._compact_init(creds)` constructs an instance without calling `__init__`; it is the recommended shortcut for quick usage (see Quick Start in `README.md`).

### Gotchas & got‑to‑know points
- The repository contains **no test suite**; adding one will require installing a test runner (e.g., `pytest`) and creating a `tests/` directory.
- No linting configuration is provided; enforce your own style guidelines.
- The package is **not** a typical Django/Flask app; it is a thin wrapper around SharePoint’s REST API, so typical web‑framework conventions do not apply.
- The `setup.py` version (`0.1.4`) is the source of truth; the `pyproject.toml` only defines the build system.

---

*Mode‑specific AGENTS files* (create under `.roo/` in the project root)

*.roo/rules-code/AGENTS.md*
``` 
# Code mode rules (non‑obvious)

- Use `SharePointAPI._compact_init(creds)` for quick client creation.
- Always include `X-HTTP-Method` headers for MERGE/PUT operations.
- Preserve NTLM auth via `HttpNtlmAuth`; do not replace with basic auth.
- When uploading files, remember the default `out_file` naming scheme.
- Follow the project’s naming conventions (PascalCase classes, snake_case functions).
- Add type hints to new public methods.
```

*.roo/rules-debug/AGENTS.md*
``` 
# Debug mode rules (non‑obvious)

- Network failures raise `ConnectionError` after printing status and response; catch this in debugging scripts.
- Enable verbose logging by setting `self.proxies = {"http": "http://localhost:8888"}` if using a proxy tool.
- SharePoint API errors often surface as HTTP 400/404; the code prints request URL and body – use these logs to reproduce issues.
- When stepping through `_api_*` methods, watch the `form_digest_value` flow; missing digest leads to 403.
```

*.roo/rules-ask/AGENTS.md*
``` 
# Ask mode rules (non‑obvious)

- The package provides only a SharePoint wrapper; there is no web UI or CLI besides the Python API.
- Documentation in `README.md` is minimal – refer to source code for endpoint details.
- No built‑in test framework; advise adding `pytest` if testing is required.
```

*.roo/rules-architect/AGENTS.md*
``` 
# Architect mode rules (non‑obvious)

- The architecture is a thin client around SharePoint’s REST API; all heavy lifting is delegated to SharePoint.
- Dependency graph: `sharepoint_api` → `requests` + `requests‑ntlm`. No other third‑party libs.
- Future extensions should respect the existing `_api_*` abstraction layer rather than calling `requests` directly.
- Consider adding a configuration layer for base URLs and credentials to avoid hard‑coding in code.