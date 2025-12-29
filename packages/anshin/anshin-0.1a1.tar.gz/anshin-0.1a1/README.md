# anshin

anshin is an early-stage Python/TOML tool for describing and building a system in a reproducible way
(inspired by declarative OS configuration workflows).

This package is a minimal functional seed:
- `anshin init` creates starter TOML config files
- `anshin validate` validates an `anshin.system.toml`
- `anshin --version` prints the version

## Usage:

```bash
anshin init --dir .
anshin validate anshin.system.toml
```

---

## Status:

Pre-alpha. Expect changes.
