# iir — Internal Info Replacement

**iir (Internal Info Replacement)** is a lightweight CLI tool for safely replacing
internal identifiers (hosts, domains, service names, user names, etc.)
before sharing logs, documents, or prompts with external parties or AI systems.

iir is designed as a **structural safety layer**:
it helps prevent accidental leakage of internal information by performing
deterministic, exact-match replacements before data leaves a trusted boundary.

---

## Installation

Install iir from PyPI:

```sh
pip install iir-tool
```

> Note: The PyPI package name is `iir-tool`, but the CLI command is `iir`.

---

## Quickstart (CLI)

Initialize local state in the current directory:

```sh
iir dev-init
```

This command prepares local state files (such as `.env.secret`).
It does **not** run database migrations.

Run database migrations explicitly:

```sh
iir admin migrate
```

Register an internal identifier:

```sh
echo "my.internal.domain" | iir add-entry DOMAIN
```

Perform a replacement:

```sh
echo "connect to my.internal.domain" | iir replace
```

Example output:

```text
connect to Domain1
```

(The exact number depends on your local database.)

---

## Design notes

- Replacements are **exact match only**
- No regular expressions or fuzzy matching
- Replacement order is deterministic
- Output must be treated as external and irreversible

iir does not attempt to automatically detect sensitive data.
Only explicitly registered values are replaced.

---

## Documentation

Complete documentation, including Docker-based evaluation
and shared / container deployment modes, is available on GitHub:

- https://github.com/koich/iir

---

## License

This project is licensed under the MIT License.

