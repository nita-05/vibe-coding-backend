from __future__ import annotations

import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union, cast

from app.services.security import hash_password, verify_password
from app.settings import settings


def _is_mongo_url(url: str) -> bool:
    u = (url or "").strip().lower()
    return u.startswith("mongodb://") or u.startswith("mongodb+srv://")


def _mongo_db():
    # Lazy import to avoid requiring pymongo when using SQLite.
    from pymongo import MongoClient

    client = MongoClient(settings.database_url)
    try:
        db = client.get_default_database()
    except Exception:
        db = None
    if db is None:
        db = client["vibe_coding"]
    return client, db


_MONGO: Optional[Tuple[Any, Any]] = None


def _get_mongo():
    global _MONGO
    if _MONGO is None:
        _MONGO = _mongo_db()
    return _MONGO


# --- SQLite (SQLAlchemy) fallback ---
from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text, create_engine  # noqa: E402
from sqlalchemy.ext.declarative import declarative_base  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

Base = declarative_base()


class Draft(Base):
    __tablename__ = "drafts"

    id = Column(Integer, primary_key=True, index=True)
    prompt = Column(Text, nullable=False)
    blueprint_id = Column(String, nullable=True)
    settings = Column(JSON, nullable=True)
    result = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=True)
    password_hash = Column(String, nullable=True)  # nullable for Google OAuth users
    google_id = Column(String, nullable=True, unique=True, index=True)  # Google OAuth ID
    avatar_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    id = Column(String, primary_key=True, index=True)  # stored in cookie
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_seen_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False, index=True)


engine = None
SessionLocal = None
if not _is_mongo_url(settings.database_url):
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables / indexes."""
    if _is_mongo_url(settings.database_url):
        _client, db = _get_mongo()
        # Users: unique email, unique google_id (sparse)
        db["users"].create_index("email", unique=True)
        db["users"].create_index("google_id", unique=True, sparse=True)
        # Sessions: TTL cleanup
        db["auth_sessions"].create_index("expires_at", expireAfterSeconds=0)
        db["auth_sessions"].create_index("user_id")
        # Projects: user_id index
        db["projects"].create_index("user_id")
        db["projects"].create_index("updated_at")
        return

    assert engine is not None
    Base.metadata.create_all(bind=engine)
    _sqlite_maybe_migrate(engine)
    # Create projects table if missing
    from sqlalchemy import Table, MetaData, Column, Integer, String, Text, JSON, DateTime
    metadata = MetaData()
    try:
        projects_table = Table("projects", metadata, autoload_with=engine)
    except Exception:
        projects_table = Table(
            "projects",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("user_id", String, nullable=False, index=True),
            Column("name", String, nullable=False),
            Column("description", Text, nullable=True),
            Column("files", JSON, nullable=False),
            Column("created_at", DateTime, default=datetime.utcnow),
            Column("updated_at", DateTime, default=datetime.utcnow),
        )
        projects_table.create(engine, checkfirst=True)


def _sqlite_maybe_migrate(engine: Any) -> None:
    """Best-effort SQLite migrations for local dev (no Alembic)."""
    try:
        with engine.connect() as conn:
            rows = conn.exec_driver_sql("PRAGMA table_info(users)").fetchall()
            cols = {r[1] for r in rows}  # (cid, name, type, notnull, dflt_value, pk)

            # Add google_id if missing (introduced for Google OAuth)
            if "google_id" not in cols:
                conn.exec_driver_sql("ALTER TABLE users ADD COLUMN google_id VARCHAR")
            if "avatar_url" not in cols:
                conn.exec_driver_sql("ALTER TABLE users ADD COLUMN avatar_url VARCHAR")

            # Ensure an index exists for google_id lookups (unique where possible)
            # SQLite can't create a UNIQUE constraint retroactively, but a unique index works.
            conn.exec_driver_sql("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_google_id ON users(google_id)")
    except Exception:
        # Don't crash startup on best-effort migration.
        return


def get_db():
    """Dependency: yield MongoDB database or SQLAlchemy session."""
    if _is_mongo_url(settings.database_url):
        _client, db = _get_mongo()
        yield db
        return

    assert SessionLocal is not None
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def save_draft(db, draft_data: Dict[str, Any]) -> str:
    """Save a draft to the database."""
    if _is_mongo_db(db):
        doc = {
            "prompt": draft_data["prompt"],
            "blueprint_id": draft_data.get("blueprint_id"),
            "settings": draft_data.get("settings"),
            "result": draft_data["result"],
            "created_at": _as_dt(draft_data.get("created_at")),
        }
        res = db["drafts"].insert_one(doc)
        return str(res.inserted_id)

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
    return str(draft.id)


def get_draft(db, draft_id: str) -> Optional[Dict[str, Any]]:
    """Get a draft by ID."""
    if _is_mongo_db(db):
        oid = _maybe_object_id(draft_id)
        if oid is None:
            return None
        doc = db["drafts"].find_one({"_id": oid})
        if not doc:
            return None
        return {
            "id": str(doc["_id"]),
            "prompt": doc.get("prompt"),
            "blueprint_id": doc.get("blueprint_id"),
            "settings": doc.get("settings"),
            "result": doc.get("result"),
            "created_at": _iso(doc.get("created_at")),
        }

    draft = db.query(Draft).filter(Draft.id == draft_id).first()
    if not draft:
        return None
    
    return {
        "id": str(draft.id),
        "prompt": draft.prompt,
        "blueprint_id": draft.blueprint_id,
        "settings": draft.settings,
        "result": draft.result,
        "created_at": draft.created_at.isoformat()
    }


def get_all_drafts(db, limit: int = 20) -> List[Dict[str, Any]]:
    """Get all drafts, limited by count."""
    if _is_mongo_db(db):
        docs = db["drafts"].find({}).sort("created_at", -1).limit(int(limit))
        out: List[Dict[str, Any]] = []
        for d in docs:
            out.append(
                {
                    "id": str(d["_id"]),
                    "prompt": d.get("prompt"),
                    "blueprint_id": d.get("blueprint_id"),
                    "settings": d.get("settings"),
                    "result": d.get("result"),
                    "created_at": _iso(d.get("created_at")),
                }
            )
        return out

    drafts = db.query(Draft).order_by(Draft.created_at.desc()).limit(limit).all()
    
    return [
        {
            "id": str(draft.id),
            "prompt": draft.prompt,
            "blueprint_id": draft.blueprint_id,
            "settings": draft.settings,
            "result": draft.result,
            "created_at": draft.created_at.isoformat()
        }
        for draft in drafts
    ]


def create_user(*, db, email: str, password: str, name: Optional[str] = None) -> Dict[str, Any]:
    email_norm = email.lower().strip()
    if _is_mongo_db(db):
        doc = {
            "email": email_norm,
            "name": name,
            "password_hash": hash_password(password),
            "google_id": None,
            "avatar_url": None,
            "created_at": datetime.utcnow(),
        }
        res = db["users"].insert_one(doc)
        return {"id": str(res.inserted_id), "email": email_norm, "name": name, "avatar_url": None}

    user = User(email=email_norm, name=name, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": str(user.id), "email": user.email, "name": user.name, "avatar_url": getattr(user, "avatar_url", None)}


def create_or_get_google_user(
    *, db, google_id: str, email: str, name: Optional[str] = None, avatar_url: Optional[str] = None
) -> Dict[str, Any]:
    """Create or get user by Google ID. If email exists but no google_id, link them."""
    email_norm = email.lower().strip()
    if _is_mongo_db(db):
        users = db["users"]
        doc = users.find_one({"google_id": google_id})
        if doc:
            updates: Dict[str, Any] = {}
            if name and doc.get("name") != name:
                updates["name"] = name
            if email_norm and doc.get("email") != email_norm:
                updates["email"] = email_norm
            if avatar_url and doc.get("avatar_url") != avatar_url:
                updates["avatar_url"] = avatar_url
            if updates:
                users.update_one({"_id": doc["_id"]}, {"$set": updates})
                doc.update(updates)
            return {
                "id": str(doc["_id"]),
                "email": doc.get("email", email_norm),
                "name": doc.get("name"),
                "avatar_url": doc.get("avatar_url"),
            }

        # Link by email if exists
        existing = users.find_one({"email": email_norm})
        if existing:
            updates = {"google_id": google_id}
            if name:
                updates["name"] = name
            if avatar_url:
                updates["avatar_url"] = avatar_url
            users.update_one({"_id": existing["_id"]}, {"$set": updates})
            existing.update(updates)
            return {
                "id": str(existing["_id"]),
                "email": existing.get("email"),
                "name": existing.get("name"),
                "avatar_url": existing.get("avatar_url"),
            }

        # Create new
        new_doc = {
            "email": email_norm,
            "name": name,
            "password_hash": None,
            "google_id": google_id,
            "avatar_url": avatar_url,
            "created_at": datetime.utcnow(),
        }
        res = users.insert_one(new_doc)
        return {"id": str(res.inserted_id), "email": email_norm, "name": name, "avatar_url": avatar_url}

    # SQLite fallback
    user = db.query(User).filter(User.google_id == google_id).first()
    if user:
        if name and user.name != name:
            user.name = name
        if email_norm != user.email:
            user.email = email_norm
        if avatar_url and getattr(user, "avatar_url", None) != avatar_url:
            user.avatar_url = avatar_url
        db.commit()
        db.refresh(user)
        return {"id": str(user.id), "email": user.email, "name": user.name, "avatar_url": getattr(user, "avatar_url", None)}

    existing = db.query(User).filter(User.email == email_norm).first()
    if existing:
        existing.google_id = google_id
        if name:
            existing.name = name
        if avatar_url:
            existing.avatar_url = avatar_url
        db.commit()
        db.refresh(existing)
        return {
            "id": str(existing.id),
            "email": existing.email,
            "name": existing.name,
            "avatar_url": getattr(existing, "avatar_url", None),
        }

    user = User(email=email_norm, name=name, google_id=google_id, password_hash=None, avatar_url=avatar_url)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": str(user.id), "email": user.email, "name": user.name, "avatar_url": getattr(user, "avatar_url", None)}


def authenticate_user(*, db, email: str, password: str) -> Optional[Dict[str, Any]]:
    email_norm = email.lower().strip()
    if _is_mongo_db(db):
        doc = db["users"].find_one({"email": email_norm})
        if not doc:
            return None
        ph = doc.get("password_hash")
        if not ph:
            return None
        if not verify_password(password, ph):
            return None
        return {
            "id": str(doc["_id"]),
            "email": doc.get("email"),
            "name": doc.get("name"),
            "avatar_url": doc.get("avatar_url"),
        }

    user = db.query(User).filter(User.email == email_norm).first()
    if not user:
        return None
    if not user.password_hash:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return {"id": str(user.id), "email": user.email, "name": user.name, "avatar_url": getattr(user, "avatar_url", None)}


def create_session(*, db, user_id: str, ttl_seconds: int) -> Dict[str, Any]:
    sid = secrets.token_urlsafe(32)
    now = datetime.utcnow()
    expires_at = now + timedelta(seconds=int(ttl_seconds))

    if _is_mongo_db(db):
        db["auth_sessions"].insert_one(
            {
                "_id": sid,
                "user_id": user_id,
                "created_at": now,
                "last_seen_at": now,
                "expires_at": expires_at,
            }
        )
        return {"id": sid, "user_id": user_id, "expires_at": expires_at}

    # SQLite: user_id is int FK
    sess = AuthSession(
        id=sid,
        user_id=int(user_id),
        created_at=now,
        last_seen_at=now,
        expires_at=expires_at,
    )
    db.add(sess)
    db.commit()
    db.refresh(sess)
    return {"id": sess.id, "user_id": str(sess.user_id), "expires_at": sess.expires_at}


def get_session(*, db, sid: str) -> Optional[Dict[str, Any]]:
    if not sid:
        return None

    now = datetime.utcnow()
    if _is_mongo_db(db):
        doc = db["auth_sessions"].find_one({"_id": sid})
        if not doc:
            return None
        expires_at = doc.get("expires_at")
        if isinstance(expires_at, datetime) and expires_at < now:
            db["auth_sessions"].delete_one({"_id": sid})
            return None
        db["auth_sessions"].update_one({"_id": sid}, {"$set": {"last_seen_at": now}})
        return {"id": sid, "user_id": cast(str, doc.get("user_id")), "expires_at": expires_at}

    sess = db.query(AuthSession).filter(AuthSession.id == sid).first()
    if not sess:
        return None
    if sess.expires_at < now:
        db.delete(sess)
        db.commit()
        return None
    sess.last_seen_at = now
    db.add(sess)
    db.commit()
    return {"id": sess.id, "user_id": str(sess.user_id), "expires_at": sess.expires_at}


def delete_session(*, db, sid: str) -> None:
    if not sid:
        return
    if _is_mongo_db(db):
        db["auth_sessions"].delete_one({"_id": sid})
        return

    sess = db.query(AuthSession).filter(AuthSession.id == sid).first()
    if sess:
        db.delete(sess)
        db.commit()


def get_user_by_id(*, db, user_id: str) -> Optional[Dict[str, Any]]:
    if not user_id:
        return None
    if _is_mongo_db(db):
        oid = _maybe_object_id(user_id)
        if oid is None:
            return None
        doc = db["users"].find_one({"_id": oid})
        if not doc:
            return None
        return {
            "id": str(doc["_id"]),
            "email": doc.get("email"),
            "name": doc.get("name"),
            "avatar_url": doc.get("avatar_url"),
        }

    try:
        iid = int(user_id)
    except Exception:
        return None
    user = db.query(User).filter(User.id == iid).first()
    if not user:
        return None
    return {"id": str(user.id), "email": user.email, "name": user.name, "avatar_url": getattr(user, "avatar_url", None)}


def get_user_by_email(*, db, email: str) -> Optional[Dict[str, Any]]:
    email_norm = (email or "").lower().strip()
    if not email_norm:
        return None
    if _is_mongo_db(db):
        doc = db["users"].find_one({"email": email_norm})
        if not doc:
            return None
        return {
            "id": str(doc["_id"]),
            "email": doc.get("email"),
            "name": doc.get("name"),
            "avatar_url": doc.get("avatar_url"),
        }

    user = db.query(User).filter(User.email == email_norm).first()
    if not user:
        return None
    return {"id": str(user.id), "email": user.email, "name": user.name, "avatar_url": getattr(user, "avatar_url", None)}


def _is_mongo_db(db: Any) -> bool:
    # pymongo.database.Database has get_collection/list_collection_names
    return hasattr(db, "get_collection") and hasattr(db, "list_collection_names")


def _maybe_object_id(v: str):
    try:
        from bson import ObjectId

        return ObjectId(v)
    except Exception:
        return None


def _as_dt(v: Any) -> datetime:
    if isinstance(v, datetime):
        return v
    if isinstance(v, str) and v:
        try:
            return datetime.fromisoformat(v)
        except Exception:
            pass
    return datetime.utcnow()


def _iso(v: Any) -> str:
    if isinstance(v, datetime):
        return v.isoformat()
    return datetime.utcnow().isoformat()


def save_project(*, db, user_id: str, name: str, files: List[Dict[str, Any]], description: Optional[str] = None) -> str:
    """Save a project (all files) for a user."""
    now = datetime.utcnow()
    if _is_mongo_db(db):
        doc = {
            "user_id": user_id,
            "name": name,
            "description": description,
            "files": files,
            "created_at": now,
            "updated_at": now,
        }
        res = db["projects"].insert_one(doc)
        return str(res.inserted_id)

    # SQLite: would need a Project table, but for now just use JSON in a simple table
    # For simplicity, we'll use MongoDB-style storage even in SQLite
    from sqlalchemy import Table, MetaData
    metadata = MetaData()
    projects_table = Table(
        "projects",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("user_id", String, nullable=False, index=True),
        Column("name", String, nullable=False),
        Column("description", Text, nullable=True),
        Column("files", JSON, nullable=False),
        Column("created_at", DateTime, default=datetime.utcnow),
        Column("updated_at", DateTime, default=datetime.utcnow),
    )
    metadata.create_all(engine)
    # Insert via raw SQL for simplicity
    with engine.connect() as conn:
        result = conn.execute(
            projects_table.insert().values(
                user_id=user_id,
                name=name,
                description=description,
                files=files,
                created_at=now,
                updated_at=now,
            )
        )
        conn.commit()
        return str(result.lastrowid)


def get_project(*, db, project_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    """Get a project by ID (user must own it)."""
    if _is_mongo_db(db):
        oid = _maybe_object_id(project_id)
        if oid is None:
            return None
        doc = db["projects"].find_one({"_id": oid, "user_id": user_id})
        if not doc:
            return None
        return {
            "id": str(doc["_id"]),
            "name": doc.get("name"),
            "description": doc.get("description"),
            "files": doc.get("files", []),
            "created_at": _iso(doc.get("created_at")),
            "updated_at": _iso(doc.get("updated_at")),
        }

    try:
        iid = int(project_id)
    except Exception:
        return None
    # SQLite: query projects table
    from sqlalchemy import Table, MetaData, select
    metadata = MetaData()
    projects_table = Table("projects", metadata, autoload_with=engine)
    with engine.connect() as conn:
        result = conn.execute(
            select(projects_table).where(
                projects_table.c.id == iid,
                projects_table.c.user_id == user_id,
            )
        ).first()
        if not result:
            return None
        return {
            "id": str(result.id),
            "name": result.name,
            "description": result.description,
            "files": result.files or [],
            "created_at": result.created_at.isoformat() if result.created_at else datetime.utcnow().isoformat(),
            "updated_at": result.updated_at.isoformat() if result.updated_at else datetime.utcnow().isoformat(),
        }


def list_projects(*, db, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """List all projects for a user."""
    if _is_mongo_db(db):
        docs = db["projects"].find({"user_id": user_id}).sort("updated_at", -1).limit(int(limit))
        out: List[Dict[str, Any]] = []
        for d in docs:
            out.append(
                {
                    "id": str(d["_id"]),
                    "name": d.get("name"),
                    "description": d.get("description"),
                    "files": d.get("files", []),
                    "created_at": _iso(d.get("created_at")),
                    "updated_at": _iso(d.get("updated_at")),
                }
            )
        return out

    # SQLite
    from sqlalchemy import Table, MetaData, select
    metadata = MetaData()
    projects_table = Table("projects", metadata, autoload_with=engine)
    with engine.connect() as conn:
        results = conn.execute(
            select(projects_table)
            .where(projects_table.c.user_id == user_id)
            .order_by(projects_table.c.updated_at.desc())
            .limit(limit)
        ).fetchall()
        return [
            {
                "id": str(r.id),
                "name": r.name,
                "description": r.description,
                "files": r.files or [],
                "created_at": r.created_at.isoformat() if r.created_at else datetime.utcnow().isoformat(),
                "updated_at": r.updated_at.isoformat() if r.updated_at else datetime.utcnow().isoformat(),
            }
            for r in results
        ]


def update_project(
    *,
    db,
    project_id: str,
    user_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Update project metadata (name/description). Returns updated project or None if not found/owned."""
    now = datetime.utcnow()
    if _is_mongo_db(db):
        oid = _maybe_object_id(project_id)
        if oid is None:
            return None
        update: Dict[str, Any] = {"updated_at": now}
        if name is not None:
            update["name"] = name
        if description is not None:
            update["description"] = description
        res = db["projects"].update_one({"_id": oid, "user_id": user_id}, {"$set": update})
        if res.matched_count == 0:
            return None
        return get_project(db=db, project_id=project_id, user_id=user_id)

    try:
        iid = int(project_id)
    except Exception:
        return None
    from sqlalchemy import Table, MetaData, select, update as sql_update

    metadata = MetaData()
    projects_table = Table("projects", metadata, autoload_with=engine)
    values: Dict[str, Any] = {"updated_at": now}
    if name is not None:
        values["name"] = name
    if description is not None:
        values["description"] = description
    with engine.connect() as conn:
        res = conn.execute(
            sql_update(projects_table)
            .where(projects_table.c.id == iid, projects_table.c.user_id == user_id)
            .values(**values)
        )
        conn.commit()
        if res.rowcount == 0:
            return None
        result = conn.execute(
            select(projects_table).where(projects_table.c.id == iid, projects_table.c.user_id == user_id)
        ).first()
        if not result:
            return None
        return {
            "id": str(result.id),
            "name": result.name,
            "description": result.description,
            "files": result.files or [],
            "created_at": result.created_at.isoformat() if result.created_at else datetime.utcnow().isoformat(),
            "updated_at": result.updated_at.isoformat() if result.updated_at else datetime.utcnow().isoformat(),
        }


def delete_project(*, db, project_id: str, user_id: str) -> bool:
    """Delete a project. Returns True if deleted, False if not found/owned."""
    if _is_mongo_db(db):
        oid = _maybe_object_id(project_id)
        if oid is None:
            return False
        res = db["projects"].delete_one({"_id": oid, "user_id": user_id})
        return bool(res.deleted_count)

    try:
        iid = int(project_id)
    except Exception:
        return False
    from sqlalchemy import Table, MetaData, delete as sql_delete

    metadata = MetaData()
    projects_table = Table("projects", metadata, autoload_with=engine)
    with engine.connect() as conn:
        res = conn.execute(sql_delete(projects_table).where(projects_table.c.id == iid, projects_table.c.user_id == user_id))
        conn.commit()
        return bool(res.rowcount)


def replace_project(
    *,
    db,
    project_id: str,
    user_id: str,
    name: str,
    files: List[Dict[str, Any]],
    description: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Replace a project's files + metadata. Returns updated project or None if not found/owned."""
    now = datetime.utcnow()
    if _is_mongo_db(db):
        oid = _maybe_object_id(project_id)
        if oid is None:
            return None
        res = db["projects"].update_one(
            {"_id": oid, "user_id": user_id},
            {
                "$set": {
                    "name": name,
                    "description": description,
                    "files": files,
                    "updated_at": now,
                }
            },
        )
        if res.matched_count == 0:
            return None
        return get_project(db=db, project_id=project_id, user_id=user_id)

    try:
        iid = int(project_id)
    except Exception:
        return None
    from sqlalchemy import Table, MetaData, select, update as sql_update

    metadata = MetaData()
    projects_table = Table("projects", metadata, autoload_with=engine)
    with engine.connect() as conn:
        res = conn.execute(
            sql_update(projects_table)
            .where(projects_table.c.id == iid, projects_table.c.user_id == user_id)
            .values(
                name=name,
                description=description,
                files=files,
                updated_at=now,
            )
        )
        conn.commit()
        if res.rowcount == 0:
            return None
        result = conn.execute(
            select(projects_table).where(projects_table.c.id == iid, projects_table.c.user_id == user_id)
        ).first()
        if not result:
            return None
        return {
            "id": str(result.id),
            "name": result.name,
            "description": result.description,
            "files": result.files or [],
            "created_at": result.created_at.isoformat() if result.created_at else datetime.utcnow().isoformat(),
            "updated_at": result.updated_at.isoformat() if result.updated_at else datetime.utcnow().isoformat(),
        }

