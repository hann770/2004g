from fastapi import FastAPI, Depends, HTTPException, status, APIRouter
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated, List, Dict, Set
from . import models
from datetime import date

from . import schemas, crud, auth, dependencies, database, models
from .auth import get_current_user
from .schemas import GroupBalance
# LAST_UPDATE_20250926_A

app = FastAPI()

@app.on_event("startup")
def startup_event():
    models.Base.metadata.create_all(bind=database.engine)

# As a new user, I can sign up, log in, and log out...
@app.post("/users/signup", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def signup(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

# Get user by ID
@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(database.get_db)):
    db_user = crud.get_user_by_id(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

# Log in
@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = crud.get_user_by_email(db, email=form_data.username)
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

# As a registered user, I can create, view, update, and delete expense groups...
@app.post("/groups", response_model=schemas.Group, status_code=status.HTTP_201_CREATED)
def create_group(group: schemas.GroupCreate, current_user: schemas.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    return crud.create_group(db=db, group=group, admin_id=current_user.id)

@app.get("/groups", response_model=List[schemas.Group])
def get_user_groups(current_user: schemas.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    return crud.get_user_groups(db=db, user_id=current_user.id)

@app.patch("/groups/{group_id}", response_model=schemas.Group)
def update_group(group_id: int, group_update: schemas.GroupUpdate, current_user: schemas.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    db_group = crud.get_group_by_id(db, group_id=group_id)
    if not db_group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    if db_group.admin_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this group")
    return crud.update_group(db=db, group_id=group_id, group_update=group_update)

@app.delete("/groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(group_id: int, current_user: schemas.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    db_group = crud.get_group_by_id(db, group_id=group_id)
    if not db_group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    if db_group.admin_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this group")
    crud.delete_group(db=db, group_id=group_id)
    return

@app.post("/groups/{group_id}/members", status_code=status.HTTP_201_CREATED)
def add_member_to_group(group_id: int, member: schemas.GroupMemberCreate, current_user: schemas.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    db_group = crud.get_group_by_id(db, group_id=group_id)
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
    if db_group.admin_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to manage this group's members")
    
    # Check if user to be added exists
    db_user_to_add = crud.get_user_by_id(db, user_id=member.member_id)
    if not db_user_to_add:
        raise HTTPException(status_code=404, detail="User to add not found")
        
    crud.add_group_member(db=db, group_id=group_id, user_id=member.member_id)
    return {"message": "Member added successfully"}

@app.get("/groups/{group_id}/members", response_model=List[schemas.User])
def get_group_members(
    group_id: int, 
    current_user: schemas.User = Depends(auth.get_current_user), 
    db: Session = Depends(database.get_db)
):
    # Verify if the current user is a member of the group
    is_member = crud.is_user_a_member_of_group(db, user_id=current_user.id, group_id=group_id)
    if not is_member:
        raise HTTPException(status_code=403, detail="Not authorized to view this group's members")

    # Get the members of the group
    members = crud.get_group_members(db, group_id=group_id)
    return members

@app.delete("/groups/{group_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member_from_group(group_id: int, user_id: int, current_user: schemas.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    db_group = crud.get_group_by_id(db, group_id=group_id)
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
    if db_group.admin_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to manage this group's members")
        
    # Check if the user is in the group
    group_member = db.query(models.group_members_table).filter_by(group_id=group_id, user_id=user_id).first()
    if not group_member:
        raise HTTPException(status_code=404, detail="User is not a member of this group")
        
    crud.remove_group_member(db=db, group_id=group_id, user_id=user_id)
    return {"message": "Member removed successfully"}

@app.post("/expenses", response_model=schemas.Expense, status_code=status.HTTP_201_CREATED)
def create_expense(expense: schemas.ExpenseCreate, current_user: schemas.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    # 验证用户是否是该群组成员
    is_member = crud.is_user_a_member_of_group(db, user_id=current_user.id, group_id=expense.group_id)
    if not is_member:
        raise HTTPException(status_code=403, detail="User is not a member of this group")
    return crud.create_expense(db=db, expense=expense, payer_id=current_user.id)


@app.patch("/expenses/{expense_id}", response_model=schemas.Expense)
def update_expense(expense_id: int, expense_update: schemas.ExpenseUpdate, current_user: schemas.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    db_expense = crud.get_expense(db, expense_id=expense_id)
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
        
    # get group info to check admin rights
    db_group = crud.get_group_by_id(db, db_expense.group_id)
    admin_id = db_group.admin_id if db_group else None
    
    # user must be either the payer or the admin
    is_payer = db_expense.payer_id == current_user.id
    is_admin = current_user.id == admin_id
    
    if not (is_payer or is_admin):
        raise HTTPException(status_code=403, detail="Not authorized to update this expense. Must be the payer or the group admin.")
        
    return crud.update_expense(db=db, db_expense=db_expense, expense_update=expense_update)

@app.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(expense_id: int, current_user: schemas.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    db_expense = crud.get_expense(db, expense_id=expense_id)
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
        
    # 获取群组信息以检查管理员权限
    db_group = crud.get_group_by_id(db, db_expense.group_id)
    admin_id = db_group.admin_id if db_group else None
    
    # 联合权限检查：当前用户必须是 Payer 或 Admin
    is_payer = db_expense.payer_id == current_user.id
    is_admin = current_user.id == admin_id
    
    if not (is_payer or is_admin):
        raise HTTPException(status_code=403, detail="Not authorized to delete this expense. Must be the payer or the group admin.")
        
    crud.delete_expense(db=db, expense_id=expense_id)
    return {"message": "Expense deleted successfully"}

@app.get("/groups/{group_id}/audit-trail", response_model=List[schemas.AuditTrail])
def get_group_audit_trail(
    group_id: int, 
    current_user: schemas.User = Depends(auth.get_current_user), 
    db: Session = Depends(database.get_db)
):
    # 授权检查: 检查当前用户是否是该群组的管理员
    db_group = crud.get_group_by_id(db, group_id=group_id)
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
        
    if db_group.admin_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this group's audit trail")
    
    # 调用 crud 函数
    return crud.get_group_audit_trail(db, group_id=group_id)

@app.get("/groups/{group_id}/expenses", response_model=List[schemas.Expense])
def get_expenses_by_group(
    group_id: int, 
    current_user: schemas.User = Depends(auth.get_current_user), 
    db: Session = Depends(database.get_db)
):
    """
    作为群组成员，查看该群组的所有费用。
    """
    # 1. 检查群组是否存在
    db_group = crud.get_group_by_id(db, group_id=group_id)
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
        
    # 2. 授权检查：确保当前用户是该群组的成员
    is_member = crud.is_user_member_of_group(db, user_id=current_user.id, group_id=group_id)
    if not is_member:
        raise HTTPException(status_code=403, detail="Not authorized. You must be a member of the group to view its expenses.")

    # 3. 获取并返回费用列表
    return crud.get_group_expenses(db, group_id=group_id)

def get_expense_group_admin_id(expense_id: int, db: Session = Depends(database.get_db)):
    db_expense = crud.get_expense(db, expense_id)
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    db_group = crud.get_group_by_id(db, db_expense.group_id)
    if not db_group:
        # 这不应该发生，除非数据库关系损坏
        raise HTTPException(status_code=500, detail="Expense's group not found")
        
    return db_group.admin_id

@app.post("/recurring-expenses", response_model=schemas.RecurringExpense, status_code=status.HTTP_201_CREATED)
def create_recurring_expense_route(
    recurring_expense: schemas.RecurringExpenseCreate,
    current_user: schemas.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    # 1. 检查群组是否存在
    group = crud.get_group_by_id(db, group_id=recurring_expense.group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
        
    # 2. 授权检查: 用户必须是群组管理员或成员
    group_members = crud.get_group_members(db, group_id=recurring_expense.group_id)
    
    # 检查当前用户是否是管理员或在成员列表中
    is_member = current_user.id == group.admin_id or any(member.id == current_user.id for member in group_members)
    
    if not is_member:
        raise HTTPException(
            status_code=403, 
            detail="Not authorized. You must be a member of the group to set up a recurring expense for it."
        )

    # 3. 验证: 确保开始日期不在过去
    if recurring_expense.start_date < date.today():
        raise HTTPException(status_code=400, detail="Start date cannot be in the past.")

    # 4. 验证: 确保结束日期在开始日期之后 (如果提供了结束日期)
    if (recurring_expense.end_date and 
        recurring_expense.end_date <= recurring_expense.start_date):
        raise HTTPException(status_code=400, detail="End date must be after the start date.")
        
    # 5. 创建周期性费用记录
    return crud.create_recurring_expense(
        db=db, 
        recurring_expense=recurring_expense, 
        payer_id=current_user.id
    )

@app.get(
    "/groups/{group_id}/balances", response_model=schemas.GroupBalance)
def get_group_balances(
    group_id: int, 
    current_user: schemas.User = Depends(auth.get_current_user), 
    db: Session = Depends(database.get_db)
):
    # check if group exists
    db_group = crud.get_group_by_id(db, group_id=group_id)
    
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
        
    # check if current user is a member or admin
    is_member = crud.is_user_member_of_group(db, user_id=current_user.id, group_id=group_id)
    is_admin = current_user.id == db_group.admin_id
    
    if not (is_member or is_admin):
        raise HTTPException(status_code=403, detail="Not authorized to view balances for this group.")
    
    # Assuming crud.calculate_group_balances returns the List[schemas.BalanceDetail]
    balances_to_settle: List[schemas.BalanceDetail] = crud.calculate_group_balances(db, group_id=group_id)
    
    # crud.calculate_group_balances returns List[BalanceDetail]
    #return crud.calculate_group_balances(db, group_id=group_id)
    return schemas.GroupBalance(
        group_id=group_id,
        balances=balances_to_settle
    )