from pydantic import BaseModel, EmailStr
from typing import Optional, List
import datetime
from enum import Enum
from datetime import date 
from . import models as model

# --- US1: User Schemas ---
class UserBase(BaseModel):
    email: EmailStr
    username: Optional[str] = None

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime.datetime
    
    class Config:
        from_attributes = True

# --- US2: Group Schemas ---
class GroupBase(BaseModel):
    #name: str
    name: Optional[str] = None 
    description: Optional[str] = None

class GroupCreate(GroupBase):
    pass

class GroupUpdate(GroupBase):
        name: Optional[str] = None
        description: Optional[str] = None

class GroupMember(BaseModel):
    user_id: int
    is_admin: bool 
    group_id: Optional[int] = None
    remark: Optional[str] = None
    
    class Config:
        from_attributes = True
class GroupMemberRecord(BaseModel):
    user_id: int
    nickname: Optional[str] = None
    is_admin: bool = False
    
    class Config:
        from_attributes = True

class Group(GroupBase):
    # id: int
    # admin_id: int
    # expenses: List["Expense"] = []
    # members: List["User"] = [] 

    # recurring_expenses: List["RecurringExpense"] = []

    # class Config:
    #     from_attributes = True
    
    id: int
    admin_id: int
    members: List[GroupMemberRecord] = [] # List of members in the group
    expenses: List["Expense"] = []


    recurring_expenses: List["RecurringExpense"] = []

    class Config:
        from_attributes = True

# --- US3 & US4: Group Member Management Schemas ---

# class GroupMemberCreate(BaseModel):
#     member_id: int
class GroupMemberAdd(BaseModel):
    member_id: int
    remark: Optional[str] = None

class GroupMemberUpdate(BaseModel):
    remark: Optional[str] = None
    is_admin: Optional[bool] = None

# --- US5 & US6: Expense Schemas ---

# class ExpenseBase(BaseModel):
#     description: str
#     amount: float
#     group_id: int

# class ExpenseCreate(ExpenseBase):
#     pass

# class ExpenseUpdate(BaseModel):
#     description: Optional[str] = None
#     amount: Optional[float] = None
#     group_id: Optional[int] = None

# class Expense(ExpenseBase):
#     id: int
#     payer_id: int
#     timestamp: datetime.datetime
    
#     class Config:
#         from_attributes = True
# Cost-sharing breakdown for a single member
class ShareBase(BaseModel):
    member_id: int
    amount: float # The amount this member owes

class Share(ShareBase):
    id: int
    expense_id: int
    
    class Config:
        from_attributes = True

# class RecurringFrequency(str, Enum):
#     daily = "DAILY"
#     weekly = "WEEKLY"
#     monthly = "MONTHLY"
#     yearly = "YEARLY"
class ExpenseBase(BaseModel):
    description: str
    amount: float
    expense_date: date
    group_id: int
    payer_id: int
    shares: List[ShareBase] # The cost-sharing breakdown
    # For recurring expenses
    frequency: Optional[model.RecurringFrequency] = None 
    
class ExpenseCreate(ExpenseBase):
    pass
    
class ExpenseUpdate(BaseModel):
    description: Optional[str] = None
    amount: Optional[float] = None
    expense_date: Optional[date] = None
    payer_id: Optional[int] = None
    shares: Optional[List[ShareBase]] = None
    # Cannot update frequency/recurrence of a created expense

class Expense(ExpenseBase):
    id: int
    creator_id: int # The user who recorded the expense (for US6 ownership check)
    timestamp: datetime.datetime
    
    class Config:
        from_attributes = True

# --- US8: Recurring Expense Schemas ---
# US: As a group member, I can set up recurring expenses ---
# class RecurringExpenseBase(BaseModel):
#     description: str
#     amount: float
#     group_id: int
#     payer_id: int
#     frequency: RecurringFrequency
#     expense_date: date # Start date (when the first one is due)
#     shares: List[ShareBase]
    
# class RecurringExpenseCreate(RecurringExpenseBase):
#     pass

# class RecurringExpense(RecurringExpenseBase):
#     id: int
#     creator_id: int # The user who recorded the recurring expense
#     created_at: datetime.datetime
    
#     class Config:
#         from_attributes = True

# class RecurringFrequency(str, Enum):
#     daily = "daily"
#     weekly = "weekly"
#     monthly = "monthly"
#     yearly = "yearly"
class RecurringExpenseBase(BaseModel):
    description: str
    amount: float
    group_id: int
    frequency: model.RecurringFrequency
    start_date: date
    end_date: Optional[date] = None
    payer_id: int
class RecurringExpenseCreate(RecurringExpenseBase):
    # equal split
    member_ids: List[int]
    payer_id: int
    split_type: str = "equal"
class RecurringExpense(RecurringExpenseBase):
    id: int
    payer_id: int
    creator_id: int
    created_at: datetime.datetime
    split_details_json: str # The serialized split details

    class Config:
        from_attributes = True
        # For date objects, allow serialization to ISO format strings
        json_encoders = {
            date: lambda v: v.isoformat()
        }

# --- Audit Trail Schemas ---
class AuditTrailBase(BaseModel):
    user_id: int # The user who performed the action
    group_id: int
    action: str # e.g., 'EXPENSE_CREATED', 'MEMBER_REMOVED'
    details: Optional[str] # Change details or description
    expense_id: Optional[int] = None # Associated expense, if applicable
    old_value: Optional[str] 
    new_value: Optional[str] 

class AuditTrail(AuditTrailBase):
    id: int
    timestamp: datetime.datetime
    
    class Config:
        from_attributes = True


# --- US10: Balance Schemas ---

# class BalanceDetail(BaseModel):
#     # Details of a single balance transaction between two users
#     payer_id: int
#     payee_id: int
#     amount: float

#     class Config:
#         from_attributes = True

# class GroupBalance(BaseModel):
#     # Represents the balance details for a group
#     group_id: int
#     balances: List[BalanceDetail]

#     class Config:
#         from_attributes = True
class BalanceDetail(BaseModel):

    payer_id: int
    payee_id: int
    amount: float

    class Config:
        from_attributes = True

class UserBalance(BaseModel):
    
    user_id: int
    net_balance: float # Positive means owed to user, negative means user owes

class GroupBalance(BaseModel):
    
    group_id: int
    balances: List[BalanceDetail]

    class Config:
        from_attributes = True

# JWT Token
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
 

# Rebuild models at the end of the file after all classes are defined
Group.model_rebuild()
GroupMemberRecord.model_rebuild()
Share.model_rebuild()
User.model_rebuild()
Expense.model_rebuild()
RecurringExpense.model_rebuild()
AuditTrail.model_rebuild()
GroupMember.model_rebuild()
GroupBalance.model_rebuild()
BalanceDetail.model_rebuild()
UserBalance.model_rebuild()




# Group.model_rebuild()
# User.model_rebuild()
# Expense.model_rebuild()
# AuditTrail.model_rebuild()
# GroupMember.model_rebuild()
# GroupBalance.model_rebuild()
# BalanceDetail.model_rebuild()
# RecurringExpense.model_rebuild()

