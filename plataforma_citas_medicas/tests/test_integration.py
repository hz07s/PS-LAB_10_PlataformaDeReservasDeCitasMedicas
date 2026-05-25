from datetime import date, datetime, timedelta

import pytest

import app as app_module
from models import Cita, Medico, User, db


def register_client(client, email="test@example.com"):
    return client.post(
        "/register",
        data={
            "nombre": "Juan Perez",
            "email": email,
            "edad": "30",
            "telefono": "123456789",
            "password": "Test123!",
            "confirm_password": "Test123!",
        },
        follow_redirects=True,
    )


def login_client(client, email="test@example.com", password="Test123!"):
    return client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=True,
    )


def get_next_weekday():
    target = date.today() + timedelta(days=1)
    while target.weekday() >= 5:
        target += timedelta(days=1)
    return target


def test_register_and_login_success(client):
    response = register_client(client)
    assert b"Registro exitoso" in response.data

    response = login_client(client)
    assert b"Inicio de sesi" in response.data


def test_duplicate_email_registration(client):
    register_client(client)
    response = register_client(client)
    assert b"El email ya est" in response.data


def test_reservation_and_conflict(client):
    register_client(client)
    login_client(client)

    with client.application.app_context():
        doctor = Medico.query.first()
        assert doctor is not None

    fecha = get_next_weekday().strftime("%Y-%m-%d")
    data = {"medico_id": str(doctor.id), "fecha": fecha, "hora": "09:00"}
    response = client.post("/reserve", data=data, follow_redirects=True)
    assert b"Cita reservada" in response.data

    response = client.post("/reserve", data=data, follow_redirects=True)
    assert b"Ya existe una cita" in response.data


def test_cancel_time_rules(client, monkeypatch):
    register_client(client)
    login_client(client)

    fixed_now = datetime(2026, 5, 18, 12, 0, 0)

    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_now

    monkeypatch.setattr(app_module, "datetime", FixedDateTime)

    with client.application.app_context():
        patient = User.query.filter_by(email="test@example.com").first()
        doctor = Medico.query.first()
        assert patient is not None
        assert doctor is not None

        def create_cita(offset):
            target = fixed_now + offset
            cita = Cita(
                usuario_id=patient.id,
                medico_id=doctor.id,
                fecha=target.date(),
                hora=target.time(),
                estado="programada",
            )
            db.session.add(cita)
            db.session.commit()
            return cita.id

        cita_ok = create_cita(timedelta(hours=2))
        cita_close = create_cita(timedelta(hours=1, minutes=59))
        cita_past = create_cita(timedelta(hours=-1))

    response = client.post(f"/cancel/{cita_ok}", follow_redirects=True)
    assert b"cancelada correctamente" in response.data

    response = client.post(f"/cancel/{cita_close}", follow_redirects=True)
    assert b"Solo puedes cancelar" in response.data

    response = client.post(f"/cancel/{cita_past}", follow_redirects=True)
    assert b"ya ha pasado" in response.data


def test_api_availability(client):
    register_client(client)
    login_client(client)

    with client.application.app_context():
        doctor = Medico.query.first()
        assert doctor is not None

    fecha = get_next_weekday().strftime("%Y-%m-%d")
    response = client.get(f"/api/availability?medico_id={doctor.id}&fecha={fecha}")
    assert response.status_code == 200
    data = response.get_json()
    assert "slots" in data
    assert any(slot["status"] == "Libre" for slot in data["slots"])
