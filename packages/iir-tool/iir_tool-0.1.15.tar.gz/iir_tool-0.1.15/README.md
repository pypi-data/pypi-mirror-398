# iir — Internal Info Replacement

**iir (Internal Info Replacement)** is a lightweight system for safely replacing
internal identifiers (hosts, domains, service names, user names, etc.) before
sharing logs, documents, or prompts with external parties or AI systems.

It is designed as a **structural safety layer**:
a tool that helps humans safely sanitize (replace) internal identifiers
before sharing information outside a trusted boundary.

---

## Intended usage note

iir is designed to be used **inside a local or private environment**
such as a developer machine, LAN, or internal network,
as a preprocessing tool **before** sharing text with external services
(including public or hosted LLMs).

iir itself is **not intended to be exposed as a public service**.
How and where it is operated is the responsibility of the user.

Please note that the dictionary used by iir should be treated as
**your private internal data**.

iir is a utility to assist safe replacement workflows.
It does not claim to provide complete security guarantees.

---

## About MCP integration

MCP support is planned as an **optional execution mode** for iir.
It is primarily intended for **on-premise or self-hosted LLM setups**.

MCP integration does not change the core concept of iir.
Replacement logic and safety assumptions remain the same,
and MCP is **not required** for using iir effectively.

---

## Installation (CLI)

Install iir from PyPI:

```sh
pip install iir-tool
```

> Note: The PyPI package name is `iir-tool`, but the CLI command is `iir`.

---

## Two usage modes

### 1. Local / personal mode (CLI-first)

This mode assumes **direct CLI usage after installing iir via PyPI**.

Typical use cases:

- Preparing logs or text before sharing
- Sanitizing prompts before sending to AI tools
- Ad-hoc replacement in pipelines or scripts

Characteristics:

- CLI-first design (stdin → stdout)
- Local execution
- No container runtime required

---

### 2. Shared / boundary mode (API / Web / MCP)

Intended to be deployed **inside a LAN or private environment**
and act as a boundary **before** data is shared externally.

Examples:

- HTTP-based replacement service (internal use)
- Web-based replacement form for inspection
- MCP adapter as an optional LLM safety layer

This mode is **not designed for public exposure**.

---

### 3. Container-based evaluation (Docker)

iir can also be evaluated using the official Docker image.
This mode is intended for **local or private evaluation**, not public exposure.

Docker usage differs from direct CLI usage in that:

- Commands are executed via `python -m iir`
- State is stored in a volume-mounted directory
- Django lifecycle operations are **explicit and manual**

For a verified, step-by-step evaluation flow using Docker, see:

- `docs/quickstart-docker.md`

This Docker-based setup is **not a replacement** for
Local / Personal Mode workflows and should not be exposed publicly.

---

## Basic usage (CLI)

This section describes **local CLI usage after installing iir via PyPI**.
It assumes a **direct CLI environment**, not Docker.

Before using iir for the first time, initialize the local working directory:

```sh
iir dev-init
```

This command only prepares local state files (such as `.env.secret`).
It does **not** run database migrations.

After initialization, you must explicitly run database migrations:

```sh
iir admin migrate
```

Then register entries and run replacement:

```sh
echo "my.domain" | iir add-entry DOMAIN
echo "connect to my.domain" | iir replace
```

> Note:
> When running iir via Docker, the initialization and migration steps
> are different. Refer to `docs/quickstart.md` for Docker-specific instructions.

---

## Maintenance and administration

iir intentionally keeps its CLI minimal.
Maintenance tasks such as inspection, correction, or cleanup
are performed via Django Admin.

For details, see:

- [Maintenance guide](docs/maintenance.md)

> Note:
> iir can store its local state in a directory specified by the `DATA_DIR`
> environment variable. This is required for container-based workflows and
> optional for direct CLI usage.

---

## Documentation

- [Quickstart](docs/quickstart.md)
- [Maintenance guide](docs/maintenance.md)
- [Container / Shared mode](docs/container-mode.md)
- [API](docs/api.md)

---

## License

This project is licensed under the [MIT License](LICENSE).

