import enum
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float, Table, Enum, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column # ... and other imports

Base = declarative_base()

# Many-to-many relationship table for Group and User
group_members_table = Table(
    'group_members',
    Base.metadata,
    Column('group_id', Integer, ForeignKey('groups.id')),
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('is_admin', Boolean, default=False)
)

class RecurringFrequency(enum.Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    yearly = "yearly"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    expenses_created = relationship("Expense", back_populates="payer")
    groups_administered = relationship("Group", back_populates="admin")
    groups_joined = relationship("Group", secondary=group_members_table, back_populates="members")
    audit_trails = relationship("AuditTrail", back_populates="user") 
         
    recurring_expenses_created = relationship("RecurringExpense", back_populates="payer") 

class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    admin_id = Column(Integer, ForeignKey("users.id"))
    
    admin = relationship("User", back_populates="groups_administered")
    expenses = relationship("Expense", back_populates="group")
    members = relationship("User", secondary=group_members_table, back_populates="groups_joined")

    audit_trails = relationship("AuditTrail", back_populates="group")
    recurring_expenses = relationship("RecurringExpense", back_populates="group")

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String)
    amount = Column(Float)
    timestamp = Column(DateTime, server_default=func.now())
    
    payer_id = Column(Integer, ForeignKey("users.id"))
    group_id = Column(Integer, ForeignKey("groups.id"))

    payer = relationship("User", back_populates="expenses_created")
    group = relationship("Group", back_populates="expenses")

class AuditTrail(Base):
    __tablename__ = "audit_trail"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    group_id = Column(Integer, ForeignKey('groups.id')) 
    expense_id = Column(Integer, ForeignKey("expenses.id", ondelete="CASCADE"))
    recurring_expense_id = Column(Integer, ForeignKey("recurring_expenses.id", ondelete="CASCADE"), nullable=True) # Added

    action = Column(String)  # e.g., "created", "updated", "deleted"
    old_value = Column(String, nullable=True) # Storing as a string for simplicity
    new_value = Column(String, nullable=True) # Storing as a string for simplicity
    timestamp = Column(DateTime, server_default=func.now())

    user = relationship("User")
    expense = relationship("Expense")
    group = relationship("Group", back_populates="audit_trails") 
    recurring_expense = relationship("RecurringExpense", back_populates="audit_trails") # Added

class RecurringExpense(Base):
    __tablename__ = "recurring_expenses"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String)
    amount = Column(Float)
    
    #frequency = Column(SqlEnum(RecurringFrequency), default=RecurringFrequency.monthly)
    frequency = Column(Enum(RecurringFrequency), default=RecurringFrequency.monthly)

    start_date = Column(Date)
    end_date = Column(Date, nullable=True) # Optional end date
    
    payer_id = Column(Integer, ForeignKey("users.id"))
    group_id = Column(Integer, ForeignKey("groups.id"))
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    payer = relationship("User", back_populates="recurring_expenses_created")
    group = relationship("Group", back_populates="recurring_expenses")
    audit_trails = relationship("AuditTrail", back_populates="recurring_expense")
