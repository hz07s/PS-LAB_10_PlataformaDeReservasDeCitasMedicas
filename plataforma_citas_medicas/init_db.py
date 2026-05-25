from app import create_app
from models import db
from utils import seed_demo_data, seed_doctors


def init_db() -> None:
    """Inicializa la base de datos y precarga datos de demostracion."""
    app = create_app({"SEED_DEMO_DATA": True})
    with app.app_context():
        db.create_all()
        seed_doctors(db.session)
        seed_demo_data(db.session)


if __name__ == "__main__":
    init_db()
    print("Base de datos inicializada y médicos precargados.")
