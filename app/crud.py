from sqlalchemy.orm import Session
from sqlalchemy import insert, delete
from . import models, schemas
from passlib.context import CryptContext
from .auth import get_password_hash
from typing import Optional, List, Dict, Set, Any
from collections import defaultdict
from sqlalchemy import func
from fastapi import HTTPException, status
import logging
import json # Used for serializing audit trail data
from datetime import date

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ----------- User CRUD -----------
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# ----------- Group CRUD -----------  
def get_group_by_id(db: Session, group_id: int):
    return db.query(models.Group).filter(models.Group.id == group_id).first()

def get_user_groups(db: Session, user_id: int):
    # return db.query(models.Group).filter(models.Group.admin_id == user_id).all()
    return db.query(models.Group).join(models.GroupMember).filter(models.GroupMember.user_id == user_id).all()

def create_group(db: Session, group: schemas.GroupCreate, admin_id: int):
    """
    Creates a new group and automatically adds the creator as the admin member.
    """
#    # 1. Create the new group
#     db_group = models.Group(name=group.name, admin_id=admin_id)
#     db.add(db_group)
#     db.commit()
#     db.refresh(db_group)

#     # 2. Find the admin user
#     admin_user = db.query(models.User).filter(models.User.id == admin_id).first()

#     # 3. Add the admin user to the group's members list
#     if admin_user:
#         db_group.members.append(admin_user)
#         db.commit()

#     return db_group

    # 1. Create the new group
    db_group = models.Group(
        name=group.name,
        admin_id=admin_id
    )
    db.add(db_group)
    db.flush() # Flush to get the group_id before commit

    # 2. Add the creator as the admin member
    db_member = models.GroupMember(
        group_id=db_group.id,
        user_id=admin_id,
        is_admin=True
    )
    db.add(db_member)
    db.flush()

    # 3. Add Audit Log for group creation
    create_audit_log(
        db=db,
        group_id=db_group.id,
        user_id=admin_id,
        action="GROUP_CREATED",
        new_value={"group_name": db_group.name}
    )

    db.commit()
    db.refresh(db_group)
    return db_group


# def update_group(db: Session, group_id: int, group_update: schemas.GroupUpdate):
#     db_group = get_group_by_id(db, group_id)
#     if db_group:
#         db_group.name = group_update.name
#         db.commit()
#         db.refresh(db_group)
#     return db_group
def update_group(db: Session, group_id: int, group_in: schemas.GroupUpdate):
    """Updates the details of an existing group."""
    db_group = get_group_by_id(db, group_id)
    if not db_group:
        return None

    # Update only fields that are provided
    update_data = group_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_group, key, value)

    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group

# def delete_group(db: Session, group_id: int):
#     db_group = get_group_by_id(db, group_id)
#     if db_group:
#         db.delete(db_group)
#         db.commit()
#     return db_group
def delete_group(db: Session, group_id: int):
    """Deletes a group and all associated members and expenses."""
    db_group = get_group_by_id(db, group_id)
    if not db_group:
        return None

    db.delete(db_group)
    db.commit()
    return db_group

# ----------- Group Member CRUD -----------
# def get_group_members(db: Session, group_id: int) -> List[models.User]:
#     """Retrieves all users that are members of a given group."""
#     # Assuming the models.Group has a 'members' relationship loaded via a many-to-many table
#     db_group = db.query(models.Group).filter(models.Group.id == group_id).first()
#     if db_group:
#         return db_group.members
#     return []
def get_group_members(db: Session, group_id: int):
    """Get all group members for a specific group."""
    return db.query(models.GroupMember).filter(models.GroupMember.group_id == group_id).all()

def get_group_member_record(db: Session, group_id: int, user_id: int):
    """Get a specific group member record."""
    return db.query(models.GroupMember).filter(
        models.GroupMember.group_id == group_id,
        models.GroupMember.user_id == user_id
    ).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    """Get all users with pagination."""
    return db.query(models.User).offset(skip).limit(limit).all()

def get_group_member_by_ids(db: Session, group_id: int, user_id: int) -> Optional[models.GroupMember]:
    """Retrieves a specific group member relationship."""
    return db.query(models.GroupMember).filter(
        models.GroupMember.group_id == group_id,
        models.GroupMember.user_id == user_id
    ).first()

# def is_user_a_member_of_group(db: Session, user_id: int, group_id: int):
#     # Check if the user is the group admin
#     group = db.query(models.Group).filter(models.Group.id == group_id, models.Group.admin_id == user_id).first()
#     if group:
#         return True
    
#     group_member = db.query(models.group_members_table).filter_by(group_id=group_id, user_id=user_id).first()
#     return group_member is not None

def is_user_in_group(db: Session, group_id: int, user_id: int) -> bool:
    """Checks if a user is a member of a group."""
    return get_group_member_by_ids(db, group_id, user_id) is not None

# def is_user_member_of_group(db: Session, user_id: int, group_id: int) -> bool:
#     # Check if the user is the admin of the group
#     query = db.query(models.group_members_table).filter(
#         models.group_members_table.c.user_id == user_id,
#         models.group_members_table.c.group_id == group_id
#     )
#     return db.execute(query).fetchone() is not None

def is_user_group_admin(db: Session, group_id: int, user_id: int) -> bool:
    """Checks if a user is an admin of a group."""
    member = get_group_member_by_ids(db, group_id, user_id)
    return member is not None and member.is_admin

# def add_group_member(db: Session, group_id: int, user_id: int):
#     stmt = insert(models.group_members_table).values(group_id=group_id, user_id=user_id)
#     db.execute(stmt)
#     db.commit()

# def get_group_members(db: Session, group_id: int):
#     group = db.query(models.Group).filter(models.Group.id == group_id).first()
#     if not group:
#         return None
#     return group.members
# def add_group_member(db: Session, group_id: int, user_id: int, is_admin: bool = False):
#     """Adds a user to a group if they are not already a member."""
#     if get_group_member_by_ids(db, group_id, user_id):
#         # User is already a member
#         return get_group_member_by_ids(db, group_id, user_id)

#     db_member = models.GroupMember(
#         group_id=group_id,
#         user_id=user_id,
#         is_admin=is_admin
#     )
#     db.add(db_member)
#     db.commit()
#     db.refresh(db_member)
#     return db_member

def add_group_member(db: Session, group_id: int, user_id: int, inviter_id: int, is_admin: bool = False):
    """Adds a member to a group if they are not already a member."""
    exists = db.query(models.GroupMember).filter(
        models.GroupMember.group_id == group_id, 
        models.GroupMember.user_id == user_id
    ).first()
    if exists:
        return None 

    db_group_member = models.GroupMember(
        group_id=group_id, 
        user_id=user_id, 
        is_admin=is_admin
    )
    db.add(db_group_member)
    db.flush()

    # Add Audit Log
    create_audit_log(
        db=db,
        group_id=group_id,
        user_id=inviter_id,
        action="GROUP_MEMBER_ADDED",
        new_value={"member_id": user_id, "is_admin": is_admin}
    )
    db.commit()
    return db_group_member

# def remove_group_member(db: Session, group_id: int, user_id: int):
#     stmt = delete(models.group_members_table).where(
#         models.group_members_table.c.group_id == group_id,
#         models.group_members_table.c.user_id == user_id
#     )
#     db.execute(stmt)
#     db.commit()
def remove_group_member(db: Session, group_id: int, user_id: int):
    """Removes a user from a group."""
    db_member = get_group_member_by_ids(db, group_id, user_id)
    if db_member:
        db.delete(db_member)
        db.commit()
        return True
    return False

# ----------- Expense CRUD -----------

# def create_expense(db: Session, expense: schemas.ExpenseCreate, payer_id: int):
#     db_expense = models.Expense(
#         description=expense.description,
#         amount=expense.amount,
#         group_id=expense.group_id,
#         payer_id=payer_id
#     )
#     db.add(db_expense)
#     db.commit()
#     db.refresh(db_expense)

#     audit_entry = models.AuditTrail(
#         user_id=payer_id,
#         expense_id=db_expense.id,
#         action="created",
#         new_value=f"description: {db_expense.description}, amount: {db_expense.amount}"
#     )
#     db.add(audit_entry)
#     db.commit()

#     return db_expense
def create_expense(db: Session, expense: schemas.ExpenseCreate, payer_id: int):
    """Creates a new expense in a group."""
    db_expense = models.Expense(
        payer_id=payer_id,
        **expense.model_dump()
    )
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)

    # Log the creation action
    audit_entry = models.AuditTrail(
        user_id=payer_id,
        expense_id=db_expense.id,
        action="created",
        new_value=f"description: {db_expense.description}, amount: {db_expense.amount}"
    )
    db.add(audit_entry)
    db.commit()

    return db_expense

def get_expense_by_id(db: Session, expense_id: int):
    """Retrieves a single expense by its ID."""
    return db.query(models.Expense).filter(models.Expense.id == expense_id).first()

def get_group_expenses(db: Session, group_id: int):
    """Retrieves all expenses for a specific group."""
    return db.query(models.Expense).filter(models.Expense.group_id == group_id).all()

# def update_expense(db: Session, db_expense: models.Expense, expense_update: schemas.ExpenseUpdate):
#     old_value = f"description: {db_expense.description}, amount: {db_expense.amount}"
    
#     update_data = expense_update.dict(exclude_unset=True)
#     for key, value in update_data.items():
#         setattr(db_expense, key, value)
    
#     db.add(db_expense)
#     db.commit()
#     db.refresh(db_expense)
    
#     new_value = f"description: {db_expense.description}, amount: {db_expense.amount}"


#     audit_entry = models.AuditTrail(
#         user_id=db_expense.payer_id,
#         expense_id=db_expense.id,
#         action="updated",
#         old_value=old_value,
#         new_value=new_value
#     )
#     db.add(audit_entry)
#     db.commit()
    
#     return db_expense
def update_expense(db: Session, expense_id: int, expense_in: schemas.ExpenseUpdate):
    """Updates the details of an existing expense."""
    db_expense = get_expense_by_id(db, expense_id)
    if not db_expense:
        return None

    # Update only fields that are provided
    update_data = expense_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_expense, key, value)

    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)

    return db_expense

# def delete_expense(db: Session, expense_id: int):
#     db_expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
#     if db_expense:
#         # Log the deletion action before the object is deleted
#         old_value = f"description: {db_expense.description}, amount: {db_expense.amount}"
#         audit_entry = models.AuditTrail(
#             user_id=db_expense.payer_id,
#             expense_id=db_expense.id,
#             action="deleted",
#             old_value=old_value,
#             new_value="None"
#         )
#         db.add(audit_entry)

#         db.delete(db_expense)
#         db.commit()
#         return True
#     return False
def delete_expense(db: Session, expense_id: int):
    """Deletes an expense."""
    db_expense = get_expense_by_id(db, expense_id)
    if not db_expense:
        return None
    
    db.delete(db_expense)
    db.commit()
    return db_expense

def get_group_expenses(db: Session, group_id: int):
    return db.query(models.Expense).filter(models.Expense.group_id == group_id).all()

# ----------- Audit Trail CRUD -----------
def create_audit_trail_entry(
    db: Session, 
    user_id: int, 
    expense_id: int, 
    action: str, 
    old_value: Optional[str], 
    new_value: Optional[str]
):
    """Creates an audit trail entry for an expense action."""
    db_audit = models.AuditTrail(
        user_id=user_id,
        expense_id=expense_id,
        action=action,
        old_value=old_value,
        new_value=new_value
    )
    db.add(db_audit)

def get_group_audit_trail(db: Session, group_id: int):

    # get audit trail entries for all expenses in the specified group
    return db.query(models.AuditTrail).join(models.Expense).filter(
        models.Expense.group_id == group_id
    ).order_by(models.AuditTrail.timestamp.desc()).all()

# ----------- Recurring Expense CRUD -----------
# def create_recurring_expense(db: Session, recurring_expense: schemas.RecurringExpenseCreate, payer_id: int):
   
#     db_recurring_expense = models.RecurringExpense(
#         description=recurring_expense.description,
#         amount=recurring_expense.amount,
#         group_id=recurring_expense.group_id,
#         frequency=recurring_expense.frequency,
#         start_date=recurring_expense.start_date,
#         end_date=recurring_expense.end_date,
#         payer_id=payer_id
#     )
#     db.add(db_recurring_expense)
#     db.commit()
#     db.refresh(db_recurring_expense)
#     return db_recurring_expense
def create_recurring_expense(
    db: Session, 
    recurring_expense: schemas.RecurringExpenseCreate, 
    creator_id: int
):
    """Creates a new recurring expense entry and logs the action."""
    
    # Prepare split details JSON (simple format for this iteration)
    split_details = {
        "split_type": recurring_expense.split_type,
        "member_ids": recurring_expense.member_ids
    }

    db_recurring = models.RecurringExpense(
        description=recurring_expense.description,
        amount=recurring_expense.amount,
        group_id=recurring_expense.group_id,
        payer_id=recurring_expense.payer_id,
        creator_id=creator_id,
        frequency=recurring_expense.frequency,
        start_date=recurring_expense.start_date,
        end_date=recurring_expense.end_date,
        split_details_json=json.dumps(split_details)
    )
    
    db.add(db_recurring)
    db.flush()
    
    # Log the creation of the recurring expense
    create_audit_log(
        db=db,
        group_id=db_recurring.group_id,
        user_id=creator_id,
        action="RECURRING_EXPENSE_CREATED",
        new_value=schemas.RecurringExpense.model_validate(db_recurring).model_dump(mode='json')
    )
    db.commit()
    db.refresh(db_recurring)

    return db_recurring

# def get_recurring_expenses_for_group(db: Session, group_id: int):
#     """Retrieves all recurring expenses for a group."""
#     return db.query(models.RecurringExpense)\
#              .filter(models.RecurringExpense.group_id == group_id)\
#              .all()
def get_recurring_expense_by_id(db: Session, recurring_expense_id: int):
    """Retrieves a single recurring expense by its ID."""
    return db.query(models.RecurringExpense).filter(models.RecurringExpense.id == recurring_expense_id).first()

# --- Balance Simplification ---

def simplify_balances(db: Session, group_id: int) -> List[schemas.BalanceDetail]:
    """
    Calculates and simplifies balances for a group using the Greedy algorithm.
    """
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        return []

    # 1. Calculate net balance for each member
    net_balances: Dict[int, float] = defaultdict(float)
    member_ids = {m.id for m in group.members}

    for expense in group.expenses:
        if not member_ids: continue 

        # Simple equal split logic:
        share_per_member = round(expense.amount / len(member_ids), 2)
        
        net_balances[expense.payer_id] += expense.amount
   
        for member_id in member_ids:
            net_balances[member_id] -= share_per_member

    filtered_balances = {user_id: balance for user_id, balance in net_balances.items() if abs(balance) > 0.01}

    # 2. Separate debtors and creditors
    debtors = [] # [(debt_amount, user_id)] - stored as negative for sorting
    creditors = [] # [(credit_amount, user_id)] - stored as negative for sorting
    
    for user_id, balance in filtered_balances.items():
        if balance < 0:
            debtors.append((balance, user_id))
        elif balance > 0:
            creditors.append((-balance, user_id)) 

    debtors.sort() 
    creditors.sort() 

    balances_to_settle: List[schemas.BalanceDetail] = []
    
    # 3. Simplify balances (Greedy algorithm)
    while debtors and creditors:
        debt_amount_neg, debtor_id = debtors.pop(0) 
        credit_amount_neg, creditor_id = creditors.pop(0)

        debt_abs = abs(debt_amount_neg)
        credit_abs = abs(credit_amount_neg)
        
        settlement_amount = round(min(debt_abs, credit_abs), 2)
        
        if settlement_amount > 0:
            balances_to_settle.append(schemas.BalanceDetail(
                payer_id=debtor_id, 
                payee_id=creditor_id, 
                amount=settlement_amount
            ))

        remaining_debt = round(debt_abs - settlement_amount, 2)
        remaining_credit = round(credit_abs - settlement_amount, 2)
        
        if remaining_debt > 0.01:
            debtors.append((-remaining_debt, debtor_id))
        
        if remaining_credit > 0.01:
            creditors.append((-remaining_credit, creditor_id)) 
            
        debtors.sort()
        creditors.sort()
        
    return balances_to_settle

# Default calculate_group_balances function (US10)
# def calculate_group_balances(db: Session, group_id: int) -> schemas.GroupBalance:
    
#     # get group info
#     group = get_group_by_id(db, group_id)
#     if not group:
#         return schemas.GroupBalance(group_id=group_id, balances=[])
        
#     # get all member ids
#     member_ids = [member.id for member in group.members]
    
#     # get all expenses for the group
#     expenses = get_group_expenses(db, group_id)

#     # net balance = total paid - total owed
#     # positive = amount to receive (Payee)
#     # negative = amount to pay (Payer)
#     net_balances = {member_id: 0.0 for member_id in member_ids}
    
#     num_members = len(member_ids)
    
#     for expense in expenses:
#         if num_members == 0:
#             continue
            
#         share = expense.amount / num_members
        
#         # payer: net balance increases (is owed)
#         net_balances[expense.payer_id] += expense.amount
        
#         # payee: net balance decreases (is owed)
#         for member_id in member_ids:
#             net_balances[member_id] -= share

#     # settle debts
#     debtors = []  # negative balance
#     creditors = [] # positive balance
    
#     for user_id, balance in net_balances.items():
      
#         # ignore balances close to zero
#         if abs(balance) < 0.01:
#             continue
        
#         if balance > 0:
#             # positive balance: creditor (receives)
#             creditors.append((-balance, user_id))
#         else:
#             # negative balance: debtor (pays)
#             debtors.append((balance, user_id))

#     # list of transactions to settle balances
#     balances_to_settle = []
    
#     debtors.sort() 
#     creditors.sort() 

#     # greedily match debtors and creditors
#     while debtors and creditors:
#         debt_amount, debtor_id = debtors.pop(0) 
#         credit_amount, creditor_id = creditors.pop(0)

#         # awaiting settlement amounts
#         debt_abs = abs(debt_amount)
#         credit_abs = abs(credit_amount)
        
#         # transaction amount is the minimum of the two
#         settlement_amount = round(min(debt_abs, credit_abs), 2)
        
#         if settlement_amount > 0:
#             # transaction: debtor_id pays settlement_amount to creditor_id
#             balances_to_settle.append(schemas.BalanceDetail(
#                 payer_id=debtor_id, 
#                 payee_id=creditor_id, 
#                 amount=settlement_amount
#             ))

#         # update remaining balances
#         remaining_debt = debt_abs - settlement_amount
#         remaining_credit = credit_abs - settlement_amount
        
#         # put back remaining balances if any
#         if remaining_debt > 0.01:
#             debtors.append((-remaining_debt, debtor_id)) 
#             debtors.sort()
        
#         if remaining_credit > 0.01:
#             creditors.append((-remaining_credit, creditor_id)) 
#             creditors.sort()


#     return schemas.GroupBalance(group_id=group_id, balances=balances_to_settle)


# def calculate_group_balances(db: Session, group_id: int) -> List[schemas.BalanceDetail]:
#     # Get all members of the group     
#     members = get_group_members(db, group_id)
#     member_ids: Set[int] = {member.id for member in members}
#     num_members = len(member_ids)
    
#     if num_members == 0:
#         return []

#     expenses = db.query(models.Expense).filter(models.Expense.group_id == group_id).all()
    
#     # 1. Calculate the net balance for each member
#     balances: Dict[int, float] = defaultdict(float) 

#     for expense in expenses:
#         payer_id = expense.payer_id
#         amount = expense.amount
        
#         share_per_member = amount / num_members
        
#         # Payer is credited the full amount they paid
#         balances[payer_id] += amount
        
#         # Every member is debited their equal share
#         for member_id in member_ids:
#             balances[member_id] -= share_per_member
            
#     # 2. Separate into debtors and creditors (for transaction optimization)
#     creditors = [] #Is owed money
#     debtors = []  #Owes money

#     for user_id, balance in balances.items():
#         balance = round(balance, 2)
        
#         if balance > 0.01:
            
#             creditors.append((-balance, user_id)) 
#         elif balance < -0.01: 
#             debtors.append((balance, user_id)) 

#     # 3. Settle debts using a greedy algorithm
#     balances_to_settle: List[schemas.BalanceDetail] = []
    
#     # Sort: debtors (smallest debt first, e.g., -10.0, -5.0)
#     # Sort: creditors (largest credit first, e.g., -10.0, -5.0)
#     debtors.sort() 
#     creditors.sort() 

#     while debtors and creditors:
#         # Get the largest debt and the largest credit
#         debt_amount_neg, debtor_id = debtors.pop(0) 
#         credit_amount_neg, creditor_id = creditors.pop(0)

#         debt_abs = abs(debt_amount_neg)
#         credit_abs = abs(credit_amount_neg)
        
#         # Transaction amount: the minimum of the two
#         settlement_amount = round(min(debt_abs, credit_abs), 2)
        
#         if settlement_amount > 0:
#             # Record transaction: debtor_id pays settlement_amount to creditor_id
#             balances_to_settle.append(schemas.BalanceDetail(
#                 payer_id=debtor_id, 
#                 payee_id=creditor_id, 
#                 amount=settlement_amount
#             ))

#         # Update remaining balances
#         remaining_debt = round(debt_abs - settlement_amount, 2)
#         remaining_credit = round(credit_abs - settlement_amount, 2)
        
#         # Push back the remaining balance to the list
#         if remaining_debt > 0.01:
#             # The debtor still owes money, store as negative amount
#             debtors.append((-remaining_debt, debtor_id))
        
#         if remaining_credit > 0.01:
#             # The creditor is still owed money, store as negative of positive amount
#             creditors.append((-remaining_credit, creditor_id)) 
            
#         # Re-sort to maintain the greedy principle
#         debtors.sort()
#         creditors.sort()

#     return balances_to_settle

# --- Balance Calculation (Greedy Algorithm for Simplification) ---
def get_group_balances(db: Session, group_id: int) -> List[schemas.BalanceDetail]:
    """
    Calculates the simplified net balances for a specific group.
    
    This function sums up all expenses within the group to find the net amount
    each member owes or is owed, and then simplifies the debts into a minimal
    set of direct payments.
    """
    
    # 1. Aggregate total expenses paid by each user
    expense_data = db.query(
        models.Expense.payer_id,
        func.sum(models.Expense.amount).label('total_paid')
    ).filter(models.Expense.group_id == group_id).group_by(models.Expense.payer_id).all()

    # 2. Get all members in the group
    members = db.query(models.GroupMember.user_id).filter(models.GroupMember.group_id == group_id).all()
    member_ids = {m.user_id for m in members}
    num_members = len(member_ids)
    
    if num_members == 0:
        return []

    # 3. Calculate equal share and net balance for each member
    total_group_expense = sum(d.total_paid for d in expense_data)
    equal_share = round(total_group_expense / num_members, 2) if num_members > 0 else 0

    net_balances: Dict[int, float] = defaultdict(lambda: -equal_share) # Everyone initially owes their share
    
    # Update balances with paid amounts
    for payer_id, total_paid in expense_data:
        # Net balance = Total Paid - Equal Share. 
        # A positive balance means they are a creditor (are owed money).
        # A negative balance means they are a debtor (owe money).
        net_balances[payer_id] = round(total_paid - equal_share, 2)
    
    # Ensure all members (even those who paid nothing) are included
    for user_id in member_ids:
        if user_id not in net_balances:
            net_balances[user_id] = round(-equal_share, 2)
            
    # 4. Separate debtors and creditors
    debtors = [] # (debt_amount, user_id) where debt_amount is POSITIVE
    creditors = [] # (credit_amount, user_id) where credit_amount is POSITIVE

    for user_id, balance in net_balances.items():
        # Only consider users who are part of the group
        if user_id not in member_ids:
            continue
            
        if balance < -0.01: # Owes money
            debtors.append((-balance, user_id)) 
        elif balance > 0.01: # Is owed money
            creditors.append((balance, user_id))

    # Sort: Greedy algorithm works best when pairing the largest debt with the largest credit
    # Debtors: sort by debt amount descending
    debtors.sort(key=lambda x: x[0], reverse=True) 
    # Creditors: sort by credit amount descending
    creditors.sort(key=lambda x: x[0], reverse=True) 

    balances_to_settle: List[schemas.BalanceDetail] = []
    
    # 5. Simplify balances (Greedy approach)
    while debtors and creditors:
        # Get the largest debt and the largest credit
        debt_amount, debtor_id = debtors.pop(0) 
        credit_amount, creditor_id = creditors.pop(0)

        # Transaction amount: the minimum of the two
        settlement_amount = round(min(debt_amount, credit_amount), 2)
        
        if settlement_amount > 0.01:
            # Record transaction: debtor_id pays settlement_amount to creditor_id
            balances_to_settle.append(schemas.BalanceDetail(
                payer_id=debtor_id, 
                payee_id=creditor_id, 
                amount=settlement_amount
            ))

        # Update remaining balances
        remaining_debt = round(debt_amount - settlement_amount, 2)
        remaining_credit = round(credit_amount - settlement_amount, 2)
        
        # Push back the remaining balance to the list
        if remaining_debt > 0.01:
            # The debtor still owes money
            debtors.append((remaining_debt, debtor_id))
        
        if remaining_credit > 0.01:
            # The creditor is still owed money
            creditors.append((remaining_credit, creditor_id)) 
            
        # Re-sort to maintain the greedy principle
        debtors.sort(key=lambda x: x[0], reverse=True)
        creditors.sort(key=lambda x: x[0], reverse=True) 

    return balances_to_settle
    return schemas.GroupBalance(group_id=group_id, balances=balances_to_settle)

# --- Audit Trail Helpers ---

def create_audit_log(
    db: Session, 
    group_id: int, 
    user_id: int, 
    action: str, 
    expense_id: Optional[int] = None, 
    old_value: Optional[Dict[str, Any]] = None, 
    new_value: Optional[Dict[str, Any]] = None
):
    """Logs an action to the audit trail. Uses json.dumps for old/new values."""
    db_log = models.AuditTrail(
        group_id=group_id,
        user_id=user_id,
        expense_id=expense_id,
        action=action,
        old_value=json.dumps(old_value) if old_value is not None else None,
        new_value=json.dumps(new_value) if new_value is not None else None,
    )
    db.add(db_log)
    db.flush() # Use flush so the log ID is generated before commit

def get_audit_trail_for_group(db: Session, group_id: int, skip: int = 0, limit: int = 50):
    """Retrieves the audit trail for a specific group, ordered by timestamp descending."""
    return db.query(models.AuditTrail)\
             .filter(models.AuditTrail.group_id == group_id)\
             .order_by(models.AuditTrail.timestamp.desc())\
             .offset(skip).limit(limit).all()
