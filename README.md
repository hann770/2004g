A backend system for shared expense management

```bash
PROJECT-PG12/(tbf)
├── app/
│   ├── main.py             # FastAPI app entry point and all routes
│   ├── database.py         # Database connection and session management
│   ├── models.py           # SQLAlchemy ORM models
│   ├── schemas.py          # Pydantic Schemas for request and response models
│   ├── crud.py             # CRUD operations for database models
│   ├── auth.py             # User authentication and JWT handling
│   └── dependencies.py     # Common dependencies, e.g.,get current user DB session
├── Dockerfile              # Docker image build file
├── docker-compose.yml      # Docker container orchestration file
├── requirements.txt        # Python dependencies
└── README.md               # Project documentation

```bash
# Project PG12 - Documentation

## 1. System Architecture and Object-Oriented Modelling

1.1 Architecture Overview
**Technology Stack:**
- **Backend**: FastAPI (Python) with SQLAlchemy ORM
- **Database**: PostgreSQL with relational modelling
- **Authentication**: JWT tokens with OAuth2
- **Deployment**: Docker containerization

1.2 Architecture Diagrams
#### Layered Architecture Diagram
┌─────────────────┐
│   API Layer     │ ← FastAPI Routes & Dependencies
├─────────────────┤
│  Service Layer  │ ← Business Logic & Validation
├─────────────────┤
│   Data Layer    │ ← SQLAlchemy Models & Repositories
├─────────────────┤
│ Database Layer  │ ← PostgreSQL with proper indexing
└─────────────────┘

**Core Class Diagram**
```mermaid
classDiagram
    class User {
        +int id
        +str email
        +str username
        +str hashed_password
        +create_group()
    }
    
    class Group {
        +int id
        +str name
        +str description
        +int admin_id
        +add_member()
    }
    
    class GroupMember {
        +int group_id
        +int user_id
        +bool is_admin
        +str nickname
        +update_nickname()
    }
    
    class Expense {
        +int id
        +str description
        +float amount
        +int payer_id
        +str split_type
        +calculate_balances()
    }
    
    User "1" -- "*" GroupMember
    Group "1" -- "*" GroupMember
    Group "1" -- "*" Expense
    User "1" -- "*" Expense : as payer

1.3 Sequence Diagrams
## 1.3 Sequence Diagrams
```mermaid
**User Registration and Authentication Flow**
sequenceDiagram
    participant U as User
    participant F as FastAPI
    participant A as AuthService
    participant D as Database
    participant C as CRUD

    U->>F: POST /users/signup
    F->>A: validate_email_format()
    A->>C: get_user_by_email()
    C->>D: SELECT users WHERE email
    D-->>C: user_exists?
    C-->>A: null (new user)
    A->>A: hash_password()
    A->>C: create_user()
    C->>D: INSERT INTO users
    D-->>C: user_created
    C-->>A: user_object
    A-->>F: user_created
    F-->>U: 201 Created + user_data

    U->>F: POST /token
    F->>A: authenticate_user()
    A->>C: get_user_by_email()
    C->>D: SELECT users WHERE email
    D-->>C: user_data
    C-->>A: user_with_hash
    A->>A: verify_password()
    A->>A: create_access_token()
    A-->>F: JWT_token
    F-->>U: 200 OK + access_token


**Expense Creation and Splitting Flow**
```mermaid
sequenceDiagram
    participant U as User
    participant F as FastAPI
    participant D as Dependencies
    participant ES as ExpenseService
    participant BS as BalanceService
    participant DB as Database

    U->>F: POST /groups/{id}/expenses
    F->>D: get_group_with_access_check()
    D-->>F: group_access_verified
    F->>ES: create_expense(expense_data)
    ES->>ES: validate_splits()
    ES->>ES: calculate_individual_shares()
    ES->>DB: INSERT INTO expenses
    DB-->>ES: expense_created
    ES->>DB: INSERT INTO expense_splits
    DB-->>ES: splits_created
    ES->>BS: initialize_balances()
    BS->>DB: UPDATE balances
    DB-->>BS: balances_updated
    BS-->>ES: balances_set
    ES-->>F: expense_with_splits
    F-->>U: 201 Created + expense_data

**Payment Processing and Balance Update Flow**
```mermaid
sequenceDiagram
    participant U as User
    participant F as FastAPI
    participant D as Dependencies
    participant PS as PaymentService
    participant BS as BalanceService
    participant DB as Database

    U->>F: POST /expenses/{id}/payments
    F->>D: get_current_user()
    D-->>F: current_user_verified
    F->>D: verify_expense_access()
    D-->>F: expense_access_verified
    F->>PS: create_payment(payment_data)
    PS->>PS: validate_payment_amount()
    PS->>DB: INSERT INTO payments
    DB-->>PS: payment_created
    PS->>BS: update_balances_after_payment()
    BS->>BS: recalculate_balances()
    BS->>DB: UPDATE user_balances
    DB-->>BS: balances_updated
    BS-->>PS: new_balances
    PS-->>F: payment_data
    F-->>U: 201 Created + payment_data

**Audit Trail and Logging Flow**
```mermaid
sequenceDiagram
    participant U as User
    participant F as FastAPI
    participant D as Dependencies
    participant AS as AuditService
    participant DB as Database

    U->>F: POST /groups/{id}/expenses
    Note over F: Business logic executes
    F->>AS: log_audit_event()
    AS->>AS: create_audit_entry()
    AS->>DB: INSERT INTO audit_logs
    DB-->>AS: log_created
    AS-->>F: audit_logged

    U->>F: GET /groups/{id}/audit-trail
    F->>D: verify_group_admin()
    D-->>F: admin_verified
    F->>AS: get_audit_logs(group_id)
    AS->>DB: SELECT audit_logs WHERE group_id
    DB-->>AS: audit_entries
    AS-->>F: audit_data
    F-->>U: 200 OK + audit_trail

Invitation Management Flow
```mermaid
sequenceDiagram
    participant I as Inviter
    participant F as FastAPI
    participant Inv as Invitee
    participant IS as InvitationService
    participant GS as GroupService
    participant DB as Database

    I->>F: POST /groups/{id}/invite
    F->>D: verify_group_membership()
    D-->>F: member_verified
    F->>IS: create_invitation(inviter_id, invitee_email)
    IS->>DB: SELECT users WHERE email
    DB-->>IS: invitee_user
    IS->>DB: INSERT INTO invitations
    DB-->>IS: invitation_created
    IS-->>F: invitation_data
    F-->>I: 201 Created + invitation_data

    Inv->>F: GET /invitations/me
    F->>D: get_current_user()
    D-->>F: current_user_verified
    F->>IS: get_pending_invitations()
    IS->>DB: SELECT invitations WHERE invitee_id
    DB-->>IS: pending_invitations
    IS-->>F: invitations_list
    F-->>Inv: 200 OK + invitations

    Inv->>F: POST /invitations/{id}/respond
    F->>D: get_pending_invitation_as_invitee()
    D-->>F: invitation_verified
    F->>IS: process_invitation_response()
    IS->>IS: validate_invitation_status()
    alt Accept Invitation
        IS->>GS: add_group_member()
        GS->>DB: INSERT INTO group_members
        DB-->>GS: member_added
        IS->>DB: UPDATE invitations SET status=accepted
    else Reject Invitation
        IS->>DB: UPDATE invitations SET status=rejected
    end
    DB-->>IS: invitation_updated
    IS-->>F: updated_invitation
    F-->>Inv: 200 OK + invitation_status

