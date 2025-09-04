from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Index, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import pytz
import uuid

# Create the base class for declarative models
Base = declarative_base()

class Product(Base):
    """Product model for the products table"""
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    productUrl = Column(Text, nullable=False, unique=True)
    shortCode = Column(String(50), nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Kolkata')))
    
    # Add index for better query performance
    __table_args__ = (
        Index('idx_product_url', 'productUrl'),
        Index('idx_short_code', 'shortCode'),
    )
    
    def __repr__(self):
        return f"<Product(id={self.id}, shortCode='{self.shortCode}', timestamp='{self.timestamp}')>"

class Job(Base):
    """Job model for tracking background tasks"""
    __tablename__ = 'jobs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(36), nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    product_url = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default='pending')  # pending, processing, completed, failed
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    page_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Kolkata')))
    completed_at = Column(DateTime, nullable=True)
    
    # Add index for better query performance
    __table_args__ = (
        Index('idx_job_id', 'job_id'),
        Index('idx_status', 'status'),
        Index('idx_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Job(id={self.id}, job_id='{self.job_id}', status='{self.status}')>"

# Database configuration
DATABASE_URL = "sqlite:///products.db"

# Create engine
engine = create_engine(DATABASE_URL, echo=False)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize the database"""
    create_tables()
    print("Database initialized successfully!")

if __name__ == "__main__":
    init_db()
