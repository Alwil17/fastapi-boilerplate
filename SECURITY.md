# Security policy

## Reporting a vulnerability

Do not open a public issue. Report it privately through
[GitHub security advisories](https://github.com/Alwil17/fastapi-boilerplate/security/advisories/new)
or by email to willialfred24@gmail.com.

Include what is affected, how to reproduce it, and the impact you see. You will get an
acknowledgement within a few days; a fix and a release follow once the report is
confirmed. Please keep the details private until that release is out.

## Supported versions

Only the latest release receives security fixes.

## Using this boilerplate securely

The application refuses to start with `APP_ENV=production` (or `prod`, `staging`) when:

- `APP_SECRET_KEY` is a known default or shorter than 32 characters
- `APP_DEBUG` is true
- `CORS_ORIGINS` contains `*`
- `DB_PASSWORD` is the default value

Before going live also:

- Set `ALLOWED_HOSTS` to your real hostnames and `FORWARDED_ALLOW_IPS` to your proxy only.
  A wrong `FORWARDED_ALLOW_IPS` lets clients spoof their IP and dodge rate limits.
- Set `METRICS_TOKEN` if `/metrics` is reachable by anything other than your scraper.
- Rate limits are per process with the default `memory://` store. Behind several workers
  or replicas the effective limit is multiplied; use a shared store or limit at the proxy.
- Terminate TLS in front of the app; the app sets HSTS in production.
- Rotate `APP_SECRET_KEY` to invalidate every access token. Refresh tokens are stored
  hashed and can be revoked per user (`/auth/logout-all`).

Dependencies are pinned with hashes. CI runs `pip-audit`, Bandit, CodeQL and a Trivy scan
of the image; Dependabot proposes updates weekly.
