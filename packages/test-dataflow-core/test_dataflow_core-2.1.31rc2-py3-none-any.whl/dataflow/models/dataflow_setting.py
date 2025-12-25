from sqlalchemy import Column, Integer, Boolean
from dataflow.db import Base


class DataflowSetting(Base):
    """
    Table DATAFLOW_SETTING
    Stores application-level configurations such as auto onboarding.
    """

    __tablename__ = "DATAFLOW_SETTING"

    id = Column(Integer, primary_key=True, index=True, unique=True, nullable=False, autoincrement=True)
    allow_auto_org_onboarding = Column(Boolean, nullable=False, default=True, server_default="true")
    new_org_credits = Column(Integer, nullable=False, default=100, server_default="100")
