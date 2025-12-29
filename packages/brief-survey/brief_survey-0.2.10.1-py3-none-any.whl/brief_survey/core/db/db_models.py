import datetime
import pytz
from sqlalchemy import (
    Column, Enum, Integer, String, DateTime, Boolean, BigInteger,
    ForeignKey, TEXT, Text, Float, UniqueConstraint, Date
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

def utcnow():
    return datetime.datetime.now(pytz.UTC)

Base = declarative_base()


