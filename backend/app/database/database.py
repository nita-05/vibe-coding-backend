from sqlalchemy import create_engine, Column, Integer, String, Text, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings
from datetime import datetime
from typing import Dict, Any, List

Base = declarative_base()


class Draft(Base):
    __tablename__ = "drafts"
    
    id = Column(Integer, primary_key=True, index=True)
    prompt = Column(Text, nullable=False)
    blueprint_id = Column(String, nullable=True)
    settings = Column(JSON, nullable=True)
    result = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# Database setup
engine = create_engine(settings.database_url, connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def save_draft(db, draft_data: Dict[str, Any]) -> int:
    """Save a draft to the database."""
    draft = Draft(
        prompt=draft_data["prompt"],
        blueprint_id=draft_data.get("blueprint_id"),
        settings=draft_data.get("settings"),
        result=draft_data["result"],
        created_at=datetime.fromisoformat(draft_data["created_at"]) if isinstance(draft_data["created_at"], str) else draft_data["created_at"]
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft.id


def get_draft(db, draft_id: int) -> Dict[str, Any]:
    """Get a draft by ID."""
    draft = db.query(Draft).filter(Draft.id == draft_id).first()
    if not draft:
        return None
    
    return {
        "id": draft.id,
        "prompt": draft.prompt,
        "blueprint_id": draft.blueprint_id,
        "settings": draft.settings,
        "result": draft.result,
        "created_at": draft.created_at.isoformat()
    }


def get_all_drafts(db, limit: int = 20) -> List[Dict[str, Any]]:
    """Get all drafts, limited by count."""
    drafts = db.query(Draft).order_by(Draft.created_at.desc()).limit(limit).all()
    
    return [
        {
            "id": draft.id,
            "prompt": draft.prompt,
            "blueprint_id": draft.blueprint_id,
            "settings": draft.settings,
            "result": draft.result,
            "created_at": draft.created_at.isoformat()
        }
        for draft in drafts
    ]

