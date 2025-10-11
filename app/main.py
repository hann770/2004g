# from fastapi import FastAPI, Depends, HTTPException, status, APIRouter
# from sqlalchemy.orm import Session
# from fastapi.security import OAuth2PasswordRequestForm
# from typing import Annotated, List, Dict, Set, Optional
# from . import models
# from datetime import date, timedelta
# from jose import jwt, JWTError

# from . import schemas, crud, auth, dependencies, database, models
# from .database import engine, Base, get_db
# from .dependencies import get_current_user, verify_group_admin, get_current_group_member
# from .auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, ALGORITHM
# from .schemas import GroupBalance
# LAST_UPDATE_20250926_A
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated, List
from datetime import timedelta

from . import schemas, crud, auth, models
from .database import get_db
from .dependencies import get_current_user, get_current_group_member, verify_group_admin, get_group_with_access_check, verify_group_owner
from .auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

app = FastAPI()

@app.get("/test")
def test_endpoint():
    return {"message": "API is working"}

# --- Auth Routes ---
@app.post("/users/signup", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    return crud.create_user(db=db, user=user)


# @app.post("/token", response_model=schemas.Token)
# async def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
#     """Authenticate user and return an access token."""
#     user = crud.get_user_by_email(db, email=form_data.username)
#     if not user or not auth.verify_password(form_data.password, user.hashed_password):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect username or password",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     access_token = auth.create_access_token(data={"sub": user.email})
#     return {"access_token": access_token, "token_type": "bearer"}

@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], 
    db: Session = Depends(get_db)
):
    user = crud.authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    auth.verify_password(form_data.password, user.hashed_password)

    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Then add your logout route
@app.post("/auth/logout")
def logout_user(current_user: models.User = Depends(get_current_user)):
    return {"message": f"Logout successful for user {current_user.email}"}

# @app.post("/users/logout")
# def logout_user(current_user: models.User = Depends(get_current_user)):
#     """
#     Logs out the user by confirming the token is valid, then instructing the client 
#     to discard the token (since JWTs are stateless).
#     """
#     return {"message": f"Logout successful for user {current_user.email}. Please discard the access token."}

@app.get("/me", response_model=schemas.User)
def read_current_user_profile(current_user: models.User = Depends(get_current_user)):
    """Get the current authenticated user's profile details."""
    return current_user 

# Get all users
@app.get("/users/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    """Get a specific user by ID."""
    db_user = crud.get_user_by_id(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return db_user

# # --- Group Routes ---  

@app.post("/groups/", response_model=schemas.Group, status_code=status.HTTP_201_CREATED)
def create_group_route(group: schemas.GroupCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Create a new expense group, making the creator the admin."""
    return crud.create_group(db=db, group=group, admin_id=current_user.id)

@app.get("/groups/{group_id}", response_model=schemas.Group)
def read_group(group_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Get a specific group by ID (requires membership in a real app)."""
    db_group = crud.get_group_by_id(db, group_id=group_id)
    if db_group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    # In a real app, you would check if current_user is a member before returning
    return db_group
# --- Group Routes ---  

# @app.post("/groups/", response_model=schemas.Group, status_code=status.HTTP_201_CREATED)
# def create_group_route(
#     group: schemas.GroupCreate, 
#     db: Session = Depends(get_db), 
#     current_user: models.User = Depends(get_current_user)
# ):
#     """Create a new expense group, making the creator the admin."""
#     return crud.create_group(db=db, group=group, admin_id=current_user.id)

# @app.get("/groups/{group_id}", response_model=schemas.Group)
# def read_group(
#     group: models.Group = Depends(get_group_with_access_check)
# ):
#     """Get a specific group by ID (requires membership)."""
#     return group

# # --- Group Member Routes ---

# # @app.post("/groups/{group_id}/members/{user_id}", response_model=schemas.GroupMember, status_code=status.HTTP_201_CREATED)
# # def add_member_to_group(group_id: int, user_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
# #     """Add a new member to a group (requires membership or admin in a real app)."""
# #     group = crud.get_group_by_id(db, group_id)
# #     if not group:
# #         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
        
# #     user_to_add = crud.get_user_by_id(db, user_id)
# #     if not user_to_add:
# #         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User to add not found")
        
# #     db_member = crud.add_group_member(db, group_id=group_id, user_id=user_id, inviter_id=current_user.id)
# #     if db_member is None:
# #         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already a member of this group")
    
# #     return schemas.GroupMember(user_id=user_id, is_admin=db_member.is_admin)

# @app.post("/groups/{group_id}/members/{user_id}", response_model=schemas.GroupMember, status_code=status.HTTP_201_CREATED)
# def add_member_to_group(group_id: int, user_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
                                                                                                  
#     """Add a new member to a group (requires the inviting user to be authenticated)."""
#     group = crud.get_group_by_id(db, group_id)
#     if not group:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
        
#     if current_user.id != group.admin_id:
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the group admin can add members.")
 
#     user_to_add = crud.get_user_by_id(db, user_id)
#     if not user_to_add:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User to add not found")
        
#     db_member = crud.add_group_member(db, group_id=group_id, user_id=user_id, inviter_id=current_user.id)
#     if db_member is None:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already a member of this group")
    
#     return schemas.GroupMember(user_id=user_id, is_admin=db_member.is_admin)

# --- Group Member Routes ---
@app.post("/groups/{group_id}/members", response_model=schemas.GroupMember, status_code=status.HTTP_201_CREATED)
def add_member_to_group(
    group_id: int, 
    user_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    """Add a new member to a group (requires only authentication)."""
    user_to_add = crud.get_user_by_id(db, user_id)
    if not user_to_add:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User to add not found")
        
    db_member = crud.add_group_member(db, group_id=group_id, user_id=user_id, inviter_id=current_user.id)
    if db_member is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already a member of this group")
    
    return schemas.GroupMember(user_id=user_id, is_admin=db_member.is_admin)

@app.get("/groups/{group_id}/members", response_model=list[schemas.GroupMember])
def get_group_members(
    group: models.Group = Depends(get_group_with_access_check),
    db: Session = Depends(get_db)
):
    """Get all members of a group (requires membership)."""
    return crud.get_group_members(db, group_id=group.id)

@app.delete("/groups/{group_id}/members/{user_id}")
def remove_member_from_group(
    group_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    group: models.Group = Depends(verify_group_owner)
):
    """Remove a member from a group (requires group admin)."""
    if user_id == group.admin_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove the group admin"
        )
    
    success = crud.remove_group_member(db, group_id=group_id, user_id=user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not a member of this group"
        )
    
    return {"message": "Member removed successfully"}

# --- Expense Routes ---

@app.post("/expenses/", response_model=schemas.Expense, status_code=status.HTTP_201_CREATED)
def create_expense_route(
    expense: schemas.ExpenseCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    """Create a new expense in a group."""
    group = crud.get_group_by_id(db, expense.group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    
    return crud.create_expense(db=db, expense=expense, current_user_id=current_user.id)


@app.put("/expenses/{expense_id}", response_model=schemas.Expense)
def update_expense_route(
    expense_id: int,
    expense_update: schemas.ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update an expense (requires user to be payer or group admin)."""
    db_expense = crud.get_expense_by_id(db, expense_id)
    if not db_expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    if db_expense.payer_id != current_user.id:
        group = crud.get_group_by_id(db, db_expense.group_id)
        if not (group and group.admin_id == current_user.id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this expense")

    return crud.update_expense(db=db, expense_id=expense_id, expense_update=expense_update, current_user_id=current_user.id)


@app.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense_route(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete an expense (requires user to be payer or group admin)."""
    db_expense = crud.get_expense_by_id(db, expense_id)
    if not db_expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    if db_expense.payer_id != current_user.id:
        group = crud.get_group_by_id(db, db_expense.group_id)
        if not (group and group.admin_id == current_user.id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this expense")
            
    crud.delete_expense(db=db, expense_id=expense_id, current_user_id=current_user.id)
    return

# --- Balance Routes ---

@app.get("/groups/{group_id}/balances", response_model=schemas.GroupBalance)
def get_group_balances(group_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Calculate the simplified net balances for a group (who owes whom)."""
    db_group = crud.get_group_by_id(db, group_id)
    if db_group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
        
    balances = crud.simplify_balances(db, group_id)
    
    return schemas.GroupBalance(group_id=group_id, balances=balances)


# --- Recurring Expense Routes ---

@app.post("/groups/{group_id}/recurring-expenses", response_model=schemas.RecurringExpense, status_code=status.HTTP_201_CREATED)
def create_recurring_expense_route(
    group_id: int,
    recurring_expense: schemas.RecurringExpenseCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_group_member) 
):
    """Sets up a new recurring expense for the group."""
    if recurring_expense.group_id != group_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Group ID in path and request body must match"
        )
        
    group = crud.get_group_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    if recurring_expense.payer_id not in recurring_expense.member_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payer must be one of the members involved in the recurring expense split."
        )
    if len(set(recurring_expense.member_ids)) != len(recurring_expense.member_ids) or not recurring_expense.member_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Member list must be unique and non-empty."
        )

    return crud.create_recurring_expense(db=db, recurring_expense=recurring_expense, creator_id=current_user.id)

@app.get("/groups/{group_id}/recurring-expenses", response_model=List[schemas.RecurringExpense])
def read_recurring_expenses(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """View all recurring expenses for a group."""
    group = crud.get_group_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    return crud.get_recurring_expenses_for_group(db, group_id=group_id)


# --- Audit Trail Route ---

@app.get("/groups/{group_id}/audit-trail", response_model=List[schemas.AuditTrail])
def view_audit_trail(
    group_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(verify_group_admin) # Ensures only the group admin can access
):
    """As a group admin, view a detailed audit trail of all changes."""
    return crud.get_audit_trail_for_group(db, group_id=group_id, skip=skip, limit=limit)

