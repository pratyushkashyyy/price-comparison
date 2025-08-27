from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import pytz

# Create the base class for declarative models
Base = declarative_base()

class Product(Base):
    """Product model for the products table"""
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    productUrl = Column(Text, nullable=False)
    shortCode = Column(String(50), nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Kolkata')))
    
    def __repr__(self):
        return f"<Product(id={self.id}, shortCode='{self.shortCode}', timestamp='{self.timestamp}')>"

# Database configuration
DATABASE_URL = "sqlite:///products.db"

# Create engine
engine = create_engine(DATABASE_URL, echo=True)

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
