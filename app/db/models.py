from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base
from pgvector.sqlalchemy import Vector

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class ParentChunk(Base):
    __tablename__ = 'parent_chunks'
    
    id = Column(String, primary_key=True)
    session_id = Column(String, index=True, nullable=False)
    file_name = Column(String, nullable=False)
    chunk_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class ChildChunk(Base):
    __tablename__ = 'child_chunks'
    
    id = Column(String, primary_key=True)
    parent_id = Column(String, ForeignKey('parent_chunks.id'), nullable=False)
    session_id = Column(String, index=True, nullable=False)
    file_name = Column(String, nullable=False)
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    embedding = Column(Vector(384), nullable=False) 

class Question(Base):
    __tablename__ = 'questions'
    
    id = Column(String, primary_key=True)
    session_id = Column(String, index=True, nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)