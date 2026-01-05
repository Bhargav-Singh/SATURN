import os

os.environ.setdefault("SATURN_DB_URL", "sqlite+pysqlite:///:memory:")

from db.session import init_db, session_scope
from models.core import (
    Agent,
    AgentTool,
    ApiKey,
    AuditLog,
    ChatSession,
    Company,
    Invoice,
    KbChunk,
    KbDocument,
    Message,
    Role,
    Tool,
    UsageEvent,
    User,
    UserRole,
)


def pytest_configure():
    init_db()


def _truncate_all():
    with session_scope() as session:
        session.query(Message).delete()
        session.query(ChatSession).delete()
        session.query(UsageEvent).delete()
        session.query(AgentTool).delete()
        session.query(Tool).delete()
        session.query(KbChunk).delete()
        session.query(KbDocument).delete()
        session.query(Agent).delete()
        session.query(Invoice).delete()
        session.query(AuditLog).delete()
        session.query(ApiKey).delete()
        session.query(UserRole).delete()
        session.query(Role).delete()
        session.query(User).delete()
        session.query(Company).delete()


def pytest_runtest_setup():
    _truncate_all()
