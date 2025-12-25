# Cosmos Auth Package

Azure Cosmos DB authentication and user verification package for Python. Provides easy-to-use authentication decorators and user management for Flask and FastAPI applications.

## 🎯 Features

- ✅ **User Verification**: Check if users exist in Cosmos DB
- ✅ **Auto-Create Users**: Automatically create users if they don't exist
- ✅ **Role-Based Access Control**: Support for user roles (admin, user, moderator, etc.)
- ✅ **Framework Support**: Works with Flask and FastAPI
- ✅ **Header-Based Auth**: Supports `x-user-email`, `x-user-id` headers
- ✅ **Flexible**: Accepts existing Cosmos DB connection (no connection management needed)

## 📦 Installation

```bash
pip install cosmos-auth-package

# With Flask support
pip install cosmos-auth-package[flask]

# With FastAPI support
pip install cosmos-auth-package[fastapi]

# With both
pip install cosmos-auth-package[all]
```

## 🚀 Quick Start

### 1. Setup Cosmos DB Connection

```python
from azure.cosmos import CosmosClient

# Create your Cosmos DB connection (in your project)
COSMOS_ENDPOINT = "https://your-account.documents.azure.com:443/"
COSMOS_KEY = "your-key"
COSMOS_DATABASE = "your-database"
COSMOS_CONTAINER = "User"

client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
database = client.get_database_client(COSMOS_DATABASE)
user_container = database.get_container_client(COSMOS_CONTAINER)
```

### 2. Initialize Package

```python
from cosmos_auth_package import UserVerifier

# Pass your existing connection
verifier = UserVerifier(user_container)
```

### 3. Use in Flask

```python
from flask import Flask, jsonify, g
from cosmos_auth_package import require_auth

app = Flask(__name__)

@app.route('/protected')
@require_auth(verifier, required_roles=['admin'])
def protected_route():
    user = g.current_user
    return jsonify({
        "message": "Access granted",
        "user": user.email,
        "role": user.role
    })
```

### 4. Use in FastAPI

```python
from fastapi import FastAPI, Depends
from cosmos_auth_package import get_current_user_fastapi, User

app = FastAPI()

@app.get("/protected")
async def protected_route(
    current_user: User = Depends(get_current_user_fastapi(verifier))
):
    return {
        "message": "Access granted",
        "user": current_user.email,
        "role": current_user.role
    }
```

## 📚 API Reference

### UserVerifier

#### Methods

- `verify_user_exists(user_id: str) -> bool` - Check if user exists
- `get_user(user_id: str) -> Optional[User]` - Get user by ID
- `get_user_by_email(email: str) -> Optional[User]` - Get user by email
- `get_user_by_username(username: str) -> Optional[User]` - Get user by username
- `create_user(email, username, role, display_name) -> User` - Create new user
- `get_or_create_user(email, username, role, display_name) -> User` - Get or create user
- `verify_user_role(user_id, required_roles) -> bool` - Check user role
- `update_user_role(user_id, new_role) -> bool` - Update user role

### Decorators

#### Flask

```python
@require_auth(
    verifier,
    required_roles=['admin'],  # Optional
    header_name='x-user-email',  # Default
    auto_create=False  # Auto-create user if doesn't exist
)
```

#### FastAPI

```python
# Basic auth
current_user: User = Depends(get_current_user_fastapi(verifier))

# With role check
current_user: User = Depends(require_role_fastapi(verifier, ['admin']))
```

## 💡 Use Cases

- API authentication with Cosmos DB
- User verification in microservices
- Role-based access control
- Auto-user creation for new users
- Header-based authentication (API Gateway integration)

## 🔧 Requirements

- Python 3.8+
- Azure Cosmos DB account
- `azure-cosmos` package

## 📄 License

MIT License

## 👤 Author

Your Company Name

