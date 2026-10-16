## What and why

<!-- What changes, and the problem it solves. Link the issue: Fixes #123 -->

## How it was tested

<!-- Commands run, endpoints exercised, tests added. -->

## Checklist

- [ ] `make test` passes (coverage gate included)
- [ ] `make lint` and `make format` are clean
- [ ] `make security` is clean
- [ ] Models changed: Alembic migration added and `alembic check` shows no drift
- [ ] `requirements*.in` changed: `make lock` re-run and both `.txt` files committed
- [ ] New or changed settings are in `.env.example` and the README
- [ ] `CHANGELOG.md` updated under *Unreleased*
