from sqlalchemy.orm import Session
from sqlalchemy import insert, delete
from . import models, schemas
from passlib.context import CryptContext
from .auth import get_password_hash
from typing import Optional, List, Dict, Set
from collections import defaultdict

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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
    
def get_group_by_id(db: Session, group_id: int):
    return db.query(models.Group).filter(models.Group.id == group_id).first()

def get_user_groups(db: Session, user_id: int):
    return db.query(models.Group).filter(models.Group.admin_id == user_id).all()

def create_group(db: Session, group: schemas.GroupCreate, admin_id: int):
    # 1. Create the new group
    db_group = models.Group(name=group.name, admin_id=admin_id)
    db.add(db_group)
    db.commit()
    db.refresh(db_group)

    # 2. Find the admin user
    admin_user = db.query(models.User).filter(models.User.id == admin_id).first()

    # 3. Add the admin user to the group's members list
    if admin_user:
        db_group.members.append(admin_user)
        db.commit()

    return db_group

def update_group(db: Session, group_id: int, group_update: schemas.GroupUpdate):
    db_group = get_group_by_id(db, group_id)
    if db_group:
        db_group.name = group_update.name
        db.commit()
        db.refresh(db_group)
    return db_group

def delete_group(db: Session, group_id: int):
    db_group = get_group_by_id(db, group_id)
    if db_group:
        db.delete(db_group)
        db.commit()
    return db_group

def add_group_member(db: Session, group_id: int, user_id: int):
    stmt = insert(models.group_members_table).values(group_id=group_id, user_id=user_id)
    db.execute(stmt)
    db.commit()

def remove_group_member(db: Session, group_id: int, user_id: int):
    stmt = delete(models.group_members_table).where(
        models.group_members_table.c.group_id == group_id,
        models.group_members_table.c.user_id == user_id
    )
    db.execute(stmt)
    db.commit()

# In crud.py, add this function to check for group membership
def is_user_a_member_of_group(db: Session, user_id: int, group_id: int):
    # Check if the user is the group admin
    group = db.query(models.Group).filter(models.Group.id == group_id, models.Group.admin_id == user_id).first()
    if group:
        return True
    
    # Check if the user is a member of the group via the association table
    group_member = db.query(models.group_members_table).filter_by(group_id=group_id, user_id=user_id).first()
    return group_member is not None

# In crud.py, add this function to get all members of a group
def get_group_members(db: Session, group_id: int):
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        return None
    return group.members

# Expense CRUD
def get_expense(db: Session, expense_id: int):
    return db.query(models.Expense).filter(models.Expense.id == expense_id).first()

def create_expense(db: Session, expense: schemas.ExpenseCreate, payer_id: int):
    db_expense = models.Expense(
        description=expense.description,
        amount=expense.amount,
        group_id=expense.group_id,
        payer_id=payer_id
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

def update_expense(db: Session, db_expense: models.Expense, expense_update: schemas.ExpenseUpdate):
    old_value = f"description: {db_expense.description}, amount: {db_expense.amount}"
    
    update_data = expense_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_expense, key, value)
    
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    
    new_value = f"description: {db_expense.description}, amount: {db_expense.amount}"

    # Log the update action
    audit_entry = models.AuditTrail(
        user_id=db_expense.payer_id,
        expense_id=db_expense.id,
        action="updated",
        old_value=old_value,
        new_value=new_value
    )
    db.add(audit_entry)
    db.commit()
    
    return db_expense

def delete_expense(db: Session, expense_id: int):
    db_expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    if db_expense:
        # Log the deletion action before the object is deleted
        old_value = f"description: {db_expense.description}, amount: {db_expense.amount}"
        audit_entry = models.AuditTrail(
            user_id=db_expense.payer_id,
            expense_id=db_expense.id,
            action="deleted",
            old_value=old_value,
            new_value="None"
        )
        db.add(audit_entry)

        db.delete(db_expense)
        db.commit()
        return True
    return False

def get_group_expenses(db: Session, group_id: int):
    return db.query(models.Expense).filter(models.Expense.group_id == group_id).all()

# Audit Trail CRUD
def create_audit_trail_entry(
    db: Session, 
    user_id: int, 
    expense_id: int, 
    action: str, 
    old_value: Optional[str], 
    new_value: Optional[str]
):
    """创建一条新的审计记录。"""
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

def get_group_expenses(db: Session, group_id: int):
    # get all expenses for a specific group
    return db.query(models.Expense).filter(models.Expense.group_id == group_id).all()

def create_recurring_expense(db: Session, recurring_expense: schemas.RecurringExpenseCreate, payer_id: int):
   
    db_recurring_expense = models.RecurringExpense(
        description=recurring_expense.description,
        amount=recurring_expense.amount,
        group_id=recurring_expense.group_id,
        frequency=recurring_expense.frequency,
        start_date=recurring_expense.start_date,
        end_date=recurring_expense.end_date,
        payer_id=payer_id
    )
    db.add(db_recurring_expense)
    db.commit()
    db.refresh(db_recurring_expense)
    return db_recurring_expense


def is_user_member_of_group(db: Session, user_id: int, group_id: int) -> bool:
    # Check if the user is the admin of the group
    query = db.query(models.group_members_table).filter(
        models.group_members_table.c.user_id == user_id,
        models.group_members_table.c.group_id == group_id
    )
    return db.execute(query).fetchone() is not None

#US10
def calculate_group_balances(db: Session, group_id: int) -> schemas.GroupBalance:
    
    # get group info
    group = get_group_by_id(db, group_id)
    if not group:
        return schemas.GroupBalance(group_id=group_id, balances=[])
        
    # get all member ids
    member_ids = [member.id for member in group.members]
    
    # get all expenses for the group
    expenses = get_group_expenses(db, group_id)

    # net balance = total paid - total owed
    # positive = amount to receive (Payee)
    # negative = amount to pay (Payer)
    net_balances = {member_id: 0.0 for member_id in member_ids}
    
    num_members = len(member_ids)
    
    for expense in expenses:
        if num_members == 0:
            continue
            
        share = expense.amount / num_members
        
        # payer: net balance increases (is owed)
        net_balances[expense.payer_id] += expense.amount
        
        # payee: net balance decreases (is owed)
        for member_id in member_ids:
            net_balances[member_id] -= share

    # settle debts
    debtors = []  # negative balance
    creditors = [] # positive balance
    
    for user_id, balance in net_balances.items():
      
        # ignore balances close to zero
        if abs(balance) < 0.01:
            continue
        
        if balance > 0:
            # positive balance: creditor (receives)
            creditors.append((-balance, user_id))
        else:
            # negative balance: debtor (pays)
            debtors.append((balance, user_id))

    # list of transactions to settle balances
    balances_to_settle = []
    
    debtors.sort() 
    creditors.sort() 

    # greedily match debtors and creditors
    while debtors and creditors:
        debt_amount, debtor_id = debtors.pop(0) 
        credit_amount, creditor_id = creditors.pop(0)

        # awaiting settlement amounts
        debt_abs = abs(debt_amount)
        credit_abs = abs(credit_amount)
        
        # transaction amount is the minimum of the two
        settlement_amount = round(min(debt_abs, credit_abs), 2)
        
        if settlement_amount > 0:
            # transaction: debtor_id pays settlement_amount to creditor_id
            balances_to_settle.append(schemas.BalanceDetail(
                payer_id=debtor_id, 
                payee_id=creditor_id, 
                amount=settlement_amount
            ))

        # update remaining balances
        remaining_debt = debt_abs - settlement_amount
        remaining_credit = credit_abs - settlement_amount
        
        # put back remaining balances if any
        if remaining_debt > 0.01:
            debtors.append((-remaining_debt, debtor_id)) 
            debtors.sort()
        
        if remaining_credit > 0.01:
            creditors.append((-remaining_credit, creditor_id)) 
            creditors.sort()


    return schemas.GroupBalance(group_id=group_id, balances=balances_to_settle)

def get_group_members(db: Session, group_id: int) -> List[models.User]:
    """Retrieves all users that are members of a given group."""
    # Assuming the models.Group has a 'members' relationship loaded via a many-to-many table
    db_group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if db_group:
        return db_group.members
    return []

def calculate_group_balances(db: Session, group_id: int) -> List[schemas.BalanceDetail]:
    # Get all members of the group     
    members = get_group_members(db, group_id)
    member_ids: Set[int] = {member.id for member in members}
    num_members = len(member_ids)
    
    if num_members == 0:
        return []

    expenses = db.query(models.Expense).filter(models.Expense.group_id == group_id).all()
    
    # 1. Calculate the net balance for each member
    balances: Dict[int, float] = defaultdict(float) 

    for expense in expenses:
        payer_id = expense.payer_id
        amount = expense.amount
        
        share_per_member = amount / num_members
        
        # Payer is credited the full amount they paid
        balances[payer_id] += amount
        
        # Every member is debited their equal share
        for member_id in member_ids:
            balances[member_id] -= share_per_member
            
    # 2. Separate into debtors and creditors (for transaction optimization)
    creditors = [] #Is owed money
    debtors = []  #Owes money

    for user_id, balance in balances.items():
        balance = round(balance, 2)
        
        if balance > 0.01:
            
            creditors.append((-balance, user_id)) 
        elif balance < -0.01: 
            debtors.append((balance, user_id)) 

    # 3. Settle debts using a greedy algorithm
    balances_to_settle: List[schemas.BalanceDetail] = []
    
    # Sort: debtors (smallest debt first, e.g., -10.0, -5.0)
    # Sort: creditors (largest credit first, e.g., -10.0, -5.0)
    debtors.sort() 
    creditors.sort() 

    while debtors and creditors:
        # Get the largest debt and the largest credit
        debt_amount_neg, debtor_id = debtors.pop(0) 
        credit_amount_neg, creditor_id = creditors.pop(0)

        debt_abs = abs(debt_amount_neg)
        credit_abs = abs(credit_amount_neg)
        
        # Transaction amount: the minimum of the two
        settlement_amount = round(min(debt_abs, credit_abs), 2)
        
        if settlement_amount > 0:
            # Record transaction: debtor_id pays settlement_amount to creditor_id
            balances_to_settle.append(schemas.BalanceDetail(
                payer_id=debtor_id, 
                payee_id=creditor_id, 
                amount=settlement_amount
            ))

        # Update remaining balances
        remaining_debt = round(debt_abs - settlement_amount, 2)
        remaining_credit = round(credit_abs - settlement_amount, 2)
        
        # Push back the remaining balance to the list
        if remaining_debt > 0.01:
            # The debtor still owes money, store as negative amount
            debtors.append((-remaining_debt, debtor_id))
        
        if remaining_credit > 0.01:
            # The creditor is still owed money, store as negative of positive amount
            creditors.append((-remaining_credit, creditor_id)) 
            
        # Re-sort to maintain the greedy principle
        debtors.sort()
        creditors.sort()

    return balances_to_settle