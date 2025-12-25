from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from dataflow.db import Base
from sqlalchemy.sql import func
import enum

class BillingPeriod(str, enum.Enum):
    """Enum for billing periods"""
    hourly = "hourly"
    daily = "daily"
    monthly = "monthly"
    yearly = "yearly"

class Subscription(Base):

    """TABLE 'SUBSCRIPTION'
    Attributes:
        id (int): Primary key for the subscription entry.
        plan_name (str): Name of the subscription plan.
        max_envs (int): Maximum number of environments allowed under this subscription.
        max_secrets (int): Maximum number of secrets allowed under this subscription.
        max_connections (int): Maximum number of connections allowed under this subscription.

    Relationships:
        servers: Many-to-many relationship with ServerConfig model via SUBSCRIPTION_SERVER association table.
        organizations: Many-to-many relationship with Organization model via ORGANIZATION_SUBSCRIPTION association table.
    """
    
    __tablename__ = "SUBSCRIPTION"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    plan_name       = Column(String, nullable=False)
    display_name    = Column(String, nullable=False)
    description     = Column(String)
    max_users       = Column(Integer, nullable=False)
    max_envs        = Column(Integer, nullable=False)
    max_secrets     = Column(Integer, nullable=False)
    max_connections = Column(Integer, nullable=False)
    amount          = Column(String, nullable=False)  # in usd
    stripe_price_id = Column(String)

    servers         = relationship("ServerConfig", secondary='SUBSCRIPTION_SERVER', back_populates="subscriptions")
    # organizations   = relationship("Organization", secondary='ORGANIZATION_SUBSCRIPTION', back_populates="subscriptions")

class SubscriptionServer(Base):

    """TABLE 'SUBSCRIPTION_SERVER'

    Attributes:
        subscription_id (int): Foreign key referencing the SUBSCRIPTION table, also part of the primary key.
        server_id (int): Foreign key referencing the SERVER_CONFIG table, also part of the primary key.
    """

    __tablename__ = 'SUBSCRIPTION_SERVER'
    
    subscription_id = Column(Integer, ForeignKey('SUBSCRIPTION.id', ondelete="CASCADE"), primary_key=True)
    server_id = Column(Integer, ForeignKey('SERVER_CONFIG.id', ondelete="CASCADE"), primary_key=True)

class Price(Base):
    
    """TABLE 'PRICE'

    Pricing for per item in pay as you go model

    Attributes:
        id (int): Primary key for the price entry.
        item (str): Name of the item (e.g., 'connection', 'secret', 'environment').
        price (int): Price of the item in cents.
        period (BillingPeriod): Billing period (hourly, daily, monthly, yearly).
    """

    __tablename__ = "PRICE"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    item       = Column(String, nullable=False, unique=True)
    price      = Column(Integer, nullable=False)
    period     = Column(Enum(BillingPeriod), nullable=False, default=BillingPeriod.monthly, server_default='monthly')

class OrganizationSubscription(Base):

    """TABLE 'ORGANIZATION_SUBSCRIPTION'

    Association table for many-to-many relationship between Organization and Subscription.

    Attributes:
        organization_id (int): Foreign key referencing the ORGANIZATION table, also part of the primary key.
        subscription_id (int): Foreign key referencing the SUBSCRIPTION table, also part of the primary key.
    """

    __tablename__ = 'ORGANIZATION_SUBSCRIPTION'

    id = Column(Integer, primary_key=True, autoincrement=True)
    org_id = Column(Integer, ForeignKey('ORGANIZATION.id', ondelete="CASCADE"), primary_key=True)
    subscription_id = Column(Integer, ForeignKey('SUBSCRIPTION.id', ondelete="CASCADE"), primary_key=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)
    renewal_date = Column(DateTime, nullable=True)
    price = Column(Integer, nullable=False)
    billing_cycle = Column(Enum(BillingPeriod), nullable=False, default=BillingPeriod.monthly, server_default='monthly')  # e.g., 'monthly', 'yearly'

class OrganizationCreditTransaction(Base):
    __tablename__ = "ORGANIZATION_CREDIT_TRANSACTION"

    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("ORGANIZATION.id"), nullable=False)
    amount = Column(Integer, nullable=False)
    type = Column(String, nullable=True) # 'free' or 'purchase'
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now(), server_default=func.now())