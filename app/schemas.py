from pydantic import BaseModel, EmailStr
from typing import Optional, List
import datetime
from enum import Enum
from datetime import date 

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime.datetime
    
    class Config:
        from_attributes = True

class GroupBase(BaseModel):
    #name: str
    name: Optional[str] = None 

class GroupCreate(GroupBase):
    pass

class GroupUpdate(GroupBase):
    name: Optional[str] = None

class GroupMember(BaseModel):
    user_id: int
    is_admin: bool

class Group(GroupBase):
    id: int
    admin_id: int
    expenses: List["Expense"] = []
    members: List["User"] = [] 

    recurring_expenses: List["RecurringExpense"] = []

    class Config:
        from_attributes = True

class ExpenseBase(BaseModel):
    description: str
    amount: float
    group_id: int

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseUpdate(BaseModel):
    description: Optional[str] = None
    amount: Optional[float] = None
    group_id: Optional[int] = None

class Expense(ExpenseBase):
    id: int
    payer_id: int
    timestamp: datetime.datetime
    
    class Config:
        from_attributes = True

class TokenData(BaseModel):
    email: Optional[str] = None

class GroupMemberCreate(BaseModel):
    member_id: int

class AuditTrailBase(BaseModel):
    user_id: int
    expense_id: int
    action: str
    old_value: Optional[str]
    new_value: Optional[str]

class AuditTrail(AuditTrailBase):
    id: int
    timestamp: datetime.datetime
    
    class Config:
        from_attributes = True

class RecurringFrequency(str, Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    yearly = "yearly"

class RecurringExpenseBase(BaseModel):
    description: str
    amount: float
    group_id: int
    frequency: RecurringFrequency
    start_date: date
    end_date: Optional[date] = None

class RecurringExpenseCreate(RecurringExpenseBase):
    pass

class RecurringExpense(RecurringExpenseBase):
    id: int
    payer_id: int
    created_at: datetime.datetime
    
    class Config:
        from_attributes = True

#US10
class BalanceDetail(BaseModel):
    # Details of a single balance transaction between two users
    payer_id: int
    payee_id: int
    amount: float

    class Config:
        from_attributes = True

class GroupBalance(BaseModel):
    # Represents the balance details for a group
    group_id: int
    balances: List[BalanceDetail]

    class Config:
        from_attributes = True

# Rebuild models at the end of the file after all classes are defined
Group.model_rebuild()
User.model_rebuild()
Expense.model_rebuild()
AuditTrail.model_rebuild()
GroupMember.model_rebuild()
GroupBalance.model_rebuild()
BalanceDetail.model_rebuild()
RecurringExpense.model_rebuild()

