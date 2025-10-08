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