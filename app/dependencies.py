# from fastapi import Depends, HTTPException, status, Path
# from fastapi.security import OAuth2PasswordBearer
# from sqlalchemy.orm import Session
# from jose import JWTError, jwt
# from . import crud, auth, database, schemas
# from .models import User, GroupMember
# from typing import Annotated


# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# # def get_current_user(db: Session = Depends(database.get_db), token: str = Depends(oauth2_scheme)):
# #     credentials_exception = HTTPException(
# #         status_code=status.HTTP_401_UNAUTHORIZED,
# #         detail="Could not validate credentials",
# #         headers={"WWW-Authenticate": "Bearer"},
# #     )
# #     try:
# #         payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
# #         user_email: str = payload.get("sub")
# #         if user_email is None:
# #             raise credentials_exception
# #     except JWTError:
# #         raise credentials_exception
# #     user = crud.get_user_by_email(db, email=user_email)
# #     if user is None:
# #         raise credentials_exception
# #     return user


# # def get_current_user(db: Session = Depends(database.get_db), token: str = Depends(oauth2_scheme)) -> schemas.User:
# #     """
# #     Authenticates the user via the provided JWT token and returns the corresponding User model object.
    
# #     This function is used as a FastAPI dependency for protected routes.
# #     """
# #     credentials_exception = HTTPException(
# #         status_code=status.HTTP_401_UNAUTHORIZED,
# #         detail="Could not validate credentials",
# #         headers={"WWW-Authenticate": "Bearer"},
# #     )
    
# #     try:
# #         payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])    
# #         user_email: str = payload.get("sub")
        
# #         if user_email is None:
# #             raise credentials_exception
            
# #     except JWTError:   
# #         raise credentials_exception
        
# #     user = crud.get_user_by_email(db, email=user_email)  
# #     if user is None:
# #         raise credentials_exception

# #     return user

# def get_current_user(db: Session = Depends(database.get_db), token: str = Depends(oauth2_scheme)) -> User:
#     """
#     Authenticates the user via the provided JWT token and returns the corresponding User model object.
    
#     This function is used as a FastAPI dependency for protected routes.
#     """
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
    
#     try:
#         # Decode the JWT token using the secret key and algorithm from auth module
#         payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])    
#         user_email: str = payload.get("sub")
        
#         if user_email is None:
#             raise credentials_exception
            
#     except JWTError:   
#         raise credentials_exception
        
#     user = crud.get_user_by_email(db, email=user_email)
    
#     if user is None:
#         raise credentials_exception

#     return user


# # Get the user's GroupMember record
# def get_current_group_member(
#     group_id: int = Path(..., description="The ID of the group."),
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(database.get_db)
# ) -> GroupMember:
#     """Checks if the current user is a member of the specified group and returns the membership record."""
#     member_record = crud.get_group_member_record(db, group_id=group_id, user_id=current_user.id)
    
#     if member_record is None:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="User is not a member of this group"
#         )
#     return member_record

# # Check if the current user is a Group Admin
# def verify_group_admin(
#     member_record: GroupMember = Depends(get_current_group_member)
# ) -> GroupMember:
#     """Verifies that the current user is an admin of the specified group."""
#     if not member_record.is_admin:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="User must be a group admin to perform this action"
#         )
#     return member_record

# dependencies.py
from fastapi import Depends, HTTPException, status, Path
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from . import crud, auth, database, schemas
from .models import User, GroupMember
from typing import Annotated

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(db: Session = Depends(database.get_db), token: str = Depends(oauth2_scheme)) -> User:
    """
    Authenticates the user via the provided JWT token and returns the corresponding User model object.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])    
        user_email: str = payload.get("sub")
        
        if user_email is None:
            raise credentials_exception
            
    except JWTError:   
        raise credentials_exception
        
    user = crud.get_user_by_email(db, email=user_email)
    
    if user is None:
        raise credentials_exception

    return user

def get_group_with_access_check(
    group_id: int = Path(..., description="The ID of the group."),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    """Gets a group and verifies the current user has access to it."""
    db_group = crud.get_group_by_id(db, group_id=group_id)
    if db_group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    
    # Check if user is a member of the group
    member_record = crud.get_group_member_record(db, group_id=group_id, user_id=current_user.id)
    if member_record is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a member of this group"
        )
    
    return db_group

def get_current_group_member(
    group_id: int = Path(..., description="The ID of the group."),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
) -> GroupMember:
    """Checks if the current user is a member of the specified group and returns the membership record."""
    member_record = crud.get_group_member_record(db, group_id=group_id, user_id=current_user.id)
    
    if member_record is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a member of this group"
        )
    return member_record

def verify_group_admin(
    member_record: GroupMember = Depends(get_current_group_member)
) -> GroupMember:
    """Verifies that the current user is an admin of the specified group."""
    if not member_record.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be a group admin to perform this action"
        )
    return member_record

def verify_group_owner(
    group_id: int = Path(..., description="The ID of the group."),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    """Verifies that the current user is the owner/admin of the specified group."""
    group = crud.get_group_by_id(db, group_id=group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    
    if current_user.id != group.admin_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the group admin can perform this action"
        )
    
    return group