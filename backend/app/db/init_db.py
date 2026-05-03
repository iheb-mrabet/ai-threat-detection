from backend.app.db.database import engine, Base
from backend.app.db.models import SecurityEvent, Alert


def init_db():
    Base.metadata.create_all(bind=engine)
    print("Database initialized.")


if __name__ == "__main__":
    init_db()
