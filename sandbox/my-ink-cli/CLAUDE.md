# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

This is a `create-ink-app` scaffold used as a sandbox for experimenting with Ink (React for CLIs) before integrating patterns into the main portfolio project at `../../`.

## Commands

```bash
npm run build        # babel transpiles source/ → dist/
npm run dev          # babel in watch mode
npm test             # prettier check + xo lint + ava tests
```

Run a single test: `ava test.js` (ava doesn't support `--grep` filtering by default; write focused tests in separate files if needed).

## Architecture

- **`source/cli.js`** — entry point; parses CLI flags with `meow`, renders the Ink app
- **`source/app.js`** — root React component for the Ink UI
- **`test.js`** — ava tests using `ink-testing-library`; JSX loaded via `import-jsx` loader

Babel (not tsc) handles JSX transpilation. ESM throughout (`"type": "module"`). No TypeScript.

## Toolchain Notes

- Linter: **xo** (wraps ESLint with `eslint-config-xo-react` + prettier integration)
- Formatter: **prettier** with `@vdemedes/prettier-config`
- Test runner: **ava** (not Jest) — tests run in parallel by default
- `NODE_NO_WARNINGS=1` is set in ava config to suppress ESM loader warnings
