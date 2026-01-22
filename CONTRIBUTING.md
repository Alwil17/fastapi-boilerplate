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
   pip install -r requirements.txt
   ```

5. **Make your changes**
   - Add features, fix bugs, or improve documentation.
   - Follow the project's Clean/Hexagonal Architecture principles.
   - Ensure changes align with mental wellness tracking objectives.

6. **Test your changes**
   ```bash
   pytest
   ```

7. **Commit and push**
   ```bash
   git add .
   git commit -m "Describe your change"
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
    git checkout -b feat/mood-analytics-endpoint
    git checkout -b bugfix/fix-jwt-validation
    git checkout -b feat/nlp-sentiment-analysis
    ```

- **Pull Request Guidelines:**
  - Use a clear and descriptive title (e.g. `feat: add mood trend analysis endpoint`)
  - In the PR description, explain **what** you changed and **why**
  - Reference related issues by number if applicable (e.g. `Closes #42`)
  - Make sure your branch is up to date with the target branch (usually `main`)
  - Ensure all tests pass before requesting a review
  - Assign reviewers if possible

---

## 🧑‍💻 Code Style

- Use [PEP8](https://www.python.org/dev/peps/pep-0008/) conventions.
- Use type hints and docstrings for all functions and classes.
- Follow FastAPI standards (async/await, Depends, response_model).
- Keep functions and classes small and focused.
- Use Pydantic models for data validation in schemas/.

---

## 🏗️ Project Structure

When adding new features, follow the established architecture:

- `app/api/routes/` - REST endpoints (auth, mood, chat, recommendations)
- `app/core/` - Security, configuration, logging
- `app/repositories/` - Business logic and database access
- `app/db/models/` - SQLAlchemy models
- `app/schemas/` - Pydantic models for I/O validation
- `app/services/` - NLP, recommendation engine, external services
- `tests/` - Test files with Pytest

---

## 🧪 Testing

- Add or update tests for your changes in the `tests/` directory.
- Make sure all tests pass with `pytest`.
- For new API endpoints, add corresponding integration tests.
- Test edge cases, especially for mental health data handling.
- Mock external services (Hugging Face API calls, etc.).

---

## 📚 Documentation

- Update the `README.md` if your change affects setup or usage.
- Add docstrings to new functions, especially in services/ and repositories/.
- Document new API endpoints with FastAPI's automatic documentation.
- Add comments to clarify complex NLP or recommendation logic.

---

## 🔒 Security & Privacy Considerations

- Follow GDPR compliance requirements for user data.
- Ensure proper JWT token handling and validation.
- Be mindful of sensitive mental health data in logs and error messages.
- Use proper database migrations with Alembic for schema changes.

---

## 💡 Suggestions & Issues

- For feature requests or bug reports, please [open an issue](https://github.com/YOUR_USERNAME/fastapi-boilerplate/issues).
- Be clear and provide context.
- Consider user privacy and data sensitivity in all suggestions.

---

## 🛡️ Code of Conduct

Be respectful and constructive applications.  
See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) if available.

---

Thank you for helping make this a better starting point! 🚀💚