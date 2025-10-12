# 2004g
A backend system for shared expense management

2004g/
├── app/
│   ├── main.py             # FastAPI app entry point and all routes
│   ├── database.py         # Database connection and session management
│   ├── models.py           # SQLAlchemy ORM models
│   ├── schemas.py          # Pydantic Schemas for request and response models
│   ├── crud.py             # CRUD operations for database models
│   ├── auth.py             # User authentication and JWT handling
│   └── dependencies.py     # Common dependencies, e.g., current user and DB session
├── Dockerfile              # Docker image build file
├── docker-compose.yml      # Docker container orchestration file
├── requirements.txt        # Python dependencies
└── README.md               # Project documentation

[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/_63RRTUw)

# 2004g
A backend system for shared expense management

A modern backend system for managing shared expenses among groups, built with FastAPI and PostgreSQL.

## Features

- **User Authentication** - Secure JWT-based authentication
- **Expense Management** - Create, track, and manage shared expenses
- **Group Management** - Organize expenses by groups
- **Balance Calculation** - Automated balance calculations between users
- **RESTful API** - Clean, documented API endpoints
- **Docker Support** - Easy deployment with Docker and Docker Compose

## 🏗️ Project Structure
