# 🚀 Raystack: Where Starlette Speed Meets Django Elegance

![PyPI Version](https://img.shields.io/pypi/v/raystack)
![Python Versions](https://img.shields.io/pypi/pyversions/raystack) ![Python 3.6+](https://img.shields.io/badge/Python-3.6%2B-blue)
![License](https://img.shields.io/pypi/l/raystack)
![Downloads](https://img.shields.io/pypi/dm/raystack)

**Raystack** is a modern, lightweight Python web framework that merges the asynchronous power of Starlette with the battle-tested structure and development convenience inspired by Django. A clean, minimal framework that gives you the best of both worlds!

## ⚡ Quick Start

Get your project up and running in minutes!

### 1. Install Raystack

```bash
pip install raystack
```

### 2. Create a New Project

```bash
raystack startproject myproject
cd myproject
```

### 3. Run the Development Server

```bash
raystack runserver
```

Open your browser and navigate to: [http://127.0.0.1:8000](http://127.0.0.1:8000/)

## 🌐 URL-Based Async/Sync Mode Detection

Raystack introduces a unique approach to database interaction, allowing you to explicitly control whether to use synchronous or asynchronous operations by simply specifying the appropriate driver in your database URL.

### How It Works:

The mode is determined by the presence of async drivers in your database URL within your `config/settings.py` file.

```python
# Synchronous mode (default)
DATABASES = {
    'default': {
        'ENGINE': 'raystack.core.database.sqlalchemy',
        'URL': 'sqlite:///db.sqlite3',  # Sync mode
    }
}

# Asynchronous mode
DATABASES = {
    'default': {
        'ENGINE': 'raystack.core.database.sqlalchemy',
        'URL': 'sqlite+aiosqlite:///' + str(BASE_DIR / 'db.sqlite3'),  # Async mode
    }
}
```

### Supported Drivers:

**Synchronous:**
*   **SQLite**: `sqlite:///db.sqlite3`
*   **PostgreSQL**: `postgresql://user:pass@localhost/dbname`
*   **MySQL**: `mysql://user:pass@localhost/dbname`

**Asynchronous:**
*   **SQLite**: `sqlite+aiosqlite:///db.sqlite3` (requires `aiosqlite`)
*   **PostgreSQL**: `postgresql+asyncpg://user:pass@localhost/dbname` (requires `asyncpg`)
*   **MySQL**: `mysql+aiomysql://user:pass@localhost/dbname` (requires `aiomysql`)

## 🛠️ ORM Usage Examples

Raystack's ORM automatically detects the mode based on your database configuration and adapts accordingly. No need for separate sync/async methods!

### Basic CRUD Operations

```python
# Create
article = await Article.objects.create(title="Hello", content="World", author_id=1)

# Get a single object
user = await UserModel.objects.get(id=1)

# Filter
users = await UserModel.objects.filter(age__gte=25).execute()

# Update
user.name = "Jane Doe"
await user.save()

# Delete
await user.delete()

# Count
count = await UserModel.objects.count()

# Check existence
exists = await UserModel.objects.filter(email="john@example.com").exists()
```

## 🔌 Admin Panel & Authentication

Raystack core framework is minimal and doesn't include an admin panel by default. However, we provide a complete example project with admin interface and authentication:

**👉 [raystack-admin](https://github.com/ForceFledgling/raystack-admin)** - A full-featured example project with:
*   Administrative interface
*   User authentication and authorization
*   User and group management
*   Session and JWT authentication
*   Ready-to-use templates and static files

You can use `raystack-admin` as a reference implementation or starting point for your own admin interface.

## 📚 Documentation

*   [Technical Documentation](.docs/index.md)
*   [ORM Reference](.docs/orm.md)
*   [Template Reference](.docs/templates.md)
*   [Command Reference](.docs/commands.md)
*   [Middleware Reference](.docs/middleware.md)
*   [Extending Raystack](.docs/extending.md)
*   [FAQ](.docs/faq.md)

## 🔗 Related Projects

*   **[raystack-admin](https://github.com/ForceFledgling/raystack-admin)** - Example project with admin interface and authentication

## 🤝 Contributing

Pull requests and issues are welcome! See [GitHub](https://github.com/ForceFledgling/raystack).

## 📜 License

MIT License. See [LICENSE](LICENSE) for details.
