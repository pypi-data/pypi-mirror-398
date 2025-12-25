---

## 🚀 Quick Start

Create FastAPI App for more visit https://fastapi.tiangolo.com/

## ⚙️ Installation

```bash

pip install fast-mu-builder
```

### 🚀 Setting Up a Custom User Model in FastAPI with Tortoise ORM + FastAPI-Builder

This guide explains how to create a package module for your **User model**, extend it from `AbstractUser`, configure it in Tortoise ORM, and generate GraphQL + migrations.

---

## 📂 Project Structure

```bash

myapp
  ├── mymodel_package
  │   ├── __init__.py
  │   └── models
  │       └── ..
  ├── config
  │   ├── __init__.py
  │   └── tortoise.py
  ├── main.py
  └── ...
```



🗄️ 3. Create Tortoise ORM Config

Inside config/tortoise.py:
```python
from decouple import config

db_url = f"postgres://{config('DB_USER')}:{config('DB_PASSWORD')}@{config('DB_HOST')}:{config('DB_PORT')}/{config('DB_NAME')}"

TORTOISE_ORM = {
    "connections": {"default": db_url},
    "apps": {
        "models": {
            "models": [
                "fast_mu_builder.models",   # built-in models
                "mymodel_package.models",    # your custom models
                "aerich.models",             # migration tracking
            ],
            "default_connection": "default",
        },
    },
    "use_tz": True,  # Enable timezone-aware datetimes
    "timezone": "Africa/Dar_es_Salaam",  # Set to EAT (Dar es Salaam)
}
```

🔧 4. Generate CRUD APIs via GraphQL

Run the following to scaffold GraphQL CRUD APIs:
```bash
# For your custom User model
graphql gen:crud-api user_management --module-package=mymodel_package.models --model User

# For fast_mu_builder built-in models
graphql gen:crud-api user_management --module-package=fast_mu_builder.models --model Group,Permission,Headship
graphql gen:crud-api workflow --module-package=fast_mu_builder.models --model Workflow,WorkflowStep,Transition,Evaluation
```
For your Models
```bash
# 
graphql gen:crud-api <module-name> --model Model1,Model2,Model3

# generating graphql schemas with attachments

graphql gen:crud-api <module-name> --model ModelName --with-attachment

# generating graphql schemas with transition
graphql gen:crud-api <module-name> --model ModelName --with-transition
```

📦 5. Initialize Aerich (DB migrations)
```bash
# Initialize Aerich with your Tortoise ORM config
aerich init -t config.tortoise.TORTOISE_ORM

# Create initial migration & database tables
aerich init-db
```

## 📖 Documentation
Coming soon...

---

## 🤝 Contributing
Contributions, issues, and feature requests are welcome!  
Feel free to check the [issues page](https://github.com/jay-ludanga/fast-backend-builder/issues).

---

## 📜 License
This project is licensed under the **MIT License**.


# Thanks

Thanks for all the contributors that made this library possible,
also a special mention to Japhary Juma, Shija Ntula and Juma Nassoro.