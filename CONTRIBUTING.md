# 🤝 Contributing to Fastapi boilerplate repo

Thank you for your interest in contributing to this repo!  
We welcome all improvements, bug fixes, documentation, and ideas for make this a better starting point backend.

---

## 📝 How to Contribute

1. **Fork the repository**  
   Click the "Fork" button at the top right of this page.

2. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/fastapi-boilerplate.git
   cd fastapi-boilerplate
   ```

3. **Create a new branch**
   ```bash
   git checkout -b my-feature
   ```

4. **Install dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   pip install --require-hashes -r requirements-dev.txt
   ```

5. **Make your changes**
   - Add features, fix bugs, or improve documentation.
   - Follow the layering: routes call services, services call repositories, repositories own the SQL.
   - Keep the boilerplate generic: no domain-specific features.

6. **Test your changes**
   ```bash
   make test       # pytest with the 95% coverage gate CI enforces
   make lint       # ruff + mypy
   make format     # black + isort
   make security   # bandit + pip-audit
   ```
   If you change the models, add an Alembic migration (`make migrate-create msg="..."`);
   CI fails when the models and migrations drift apart. If you change
   `requirements*.in`, run `make lock` and commit the regenerated `.txt` files.

7. **Commit and push**
   ```bash
   git add .
   git commit -m "feat: describe your change"   # Conventional Commits: feat, fix, docs, test, refactor, build, ci
   git push origin my-feature
   ```

8. **Open a Pull Request**
   - Go to your fork on GitHub.
   - Click "Compare & pull request".
   - Describe your changes and submit.

---

## 🌱 Branch Naming & Pull Request Rules

- **Branch naming convention:**
  - For new features: `feat/short-description`
  - For bug fixes: `bugfix/short-description`
  - For maintenance or chores: `chore/short-description`
  - For documentation: `docs/short-description`
  - Example:  
    ```
    git checkout -b feat/password-reset-endpoint
    git checkout -b bugfix/fix-jwt-validation
    ```

- **Pull Request Guidelines:**
  - Use a clear and descriptive title (e.g. `feat: add password reset endpoint`)
  - In the PR description, explain **what** you changed and **why**
  - Reference related issues by number if applicable (e.g. `Closes #42`)
  - Make sure your branch is up to date with the target branch (usually `main`)
  - Ensure all tests pass before requesting a review
  - Assign reviewers if possible

---

## 🧑‍💻 Code Style

- Use [PEP8](https://www.python.org/dev/peps/pep-0008/) conventions.
- Use type hints and docstrings for all functions and classes.
- Follow FastAPI standards (Depends, response_model). Routes that use the synchronous
  database session or bcrypt are plain `def`, not `async def`, so they run in the thread
  pool instead of blocking the event loop.
- Keep functions and classes small and focused.
- Use Pydantic models for data validation in schemas/.

---

## 🏗️ Project Structure

When adding new features, follow the established architecture:

- `app/api/routes/` - REST endpoints (auth, users, health)
- `app/core/` - Security, configuration, logging
- `app/repositories/` - Database access
- `app/db/models/` - SQLAlchemy models
- `app/schemas/` - Pydantic models for I/O validation
- `app/services/` - Business logic
- `tests/` - Test files with Pytest

---

## 🧪 Testing

- Add or update tests for your changes in the `tests/` directory.
- Make sure all tests pass with `pytest`.
- For new API endpoints, add corresponding integration tests.
- Test edge cases: invalid input, expired or revoked tokens, missing or duplicate records.
- Mock external services; tests must not need the network.
- Coverage must stay at or above 95% (`make test`).

---

## 📚 Documentation

- Update the `README.md` if your change affects setup or usage.
- Add docstrings to new functions, especially in services/ and repositories/.
- Document new API endpoints with FastAPI's automatic documentation.
- Add comments that explain why, not what, for anything non-obvious.
- Add a line under *Unreleased* in `CHANGELOG.md`.

---

## 🔒 Security & Privacy Considerations

- Never log or return passwords, tokens or other credentials, including in error messages.
- Ensure proper JWT token handling and validation.
- Use proper database migrations with Alembic for schema changes.
- Report vulnerabilities privately, see [SECURITY.md](SECURITY.md).

---

## 💡 Suggestions & Issues

- For feature requests or bug reports, please [open an issue](https://github.com/Alwil17/fastapi-boilerplate/issues).
- Be clear and provide context.

---

## 🛡️ Code of Conduct

Be respectful and constructive applications.  
See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) if available.

---

Thank you for helping make this a better starting point! 🚀💚