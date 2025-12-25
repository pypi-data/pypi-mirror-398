# FastAPI Project Generator CLI

A lightweight, beginner-friendly CLI tool that creates a clean, ready-to-use FastAPI project structure instantly.

## 🚀 Features

- ✅ **One-command bootstrapping:** Start a FastAPI project in seconds.
- ✅ **Opinionated structure:** Follows best practices for organized code.
- ✅ **Pre-configured:** Generates `main.py`, routes, config, tests, `.env`, and more.
- ✅ **Beginner Friendly:** No complex configuration needed.

## 📦 Installation

```bash
# Clone the repository
git clone <repository-url>
cd fastapi-starter

# Install locally
pip install .
```

## 🛠️ Usage

Creating a new project is as simple as:

```bash
fastapi-starter my_awesome_app
```

This will create a `my_awesome_app/` directory with the following structure:

```text
my_awesome_app/
├── app/
│   ├── main.py          # Entry point
│   ├── api/             # API routes
│   ├── core/            # Configuration
│   ├── models/          # Database models
│   ├── schemas/         # Pydantic models
│   └── services/        # Business logic
├── tests/               # Unit tests
├── .env                 # Environment variables
├── .gitignore          
├── requirements.txt
└── README.md
```

## 🚀 Getting Started with the Generated Project

1. Navigate to your new project:
   ```bash
   cd my_awesome_app
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the development server:
   ```bash
   fastapi dev app/main.py
   ```
4. Explore your API:
   - Interactive docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
