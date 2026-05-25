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

def test_dashboard_requires_login(client):
    response = client.get("/dashboard", follow_redirects=True)

    assert b"Debe iniciar sesi" in response.data


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

def test_reserve_requires_login(client):
    response = client.post(
        "/reserve",
        data={
            "medico_id": "1",
            "fecha": "2026-06-01",
            "hora": "09:00",
        },
        follow_redirects=True,
    )

    assert b"Debe iniciar sesi" in response.data

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

def test_api_requires_login(client):
    response = client.get(
        "/api/availability?medico_id=1&fecha=2026-06-01"
    )
    assert response.status_code in (302, 401)

def test_reserve_invalid_doctor(client):
    register_client(client)
    login_client(client)

    fecha = get_next_weekday().strftime("%Y-%m-%d")

    response = client.post(
        "/reserve",
        data={
            "medico_id": "999",
            "fecha": fecha,
            "hora": "09:00",
        },
        follow_redirects=True,
    )

    assert b"medico" in response.data.lower()

def test_reserve_past_date(client):
    register_client(client)
    login_client(client)

    with client.application.app_context():
        doctor = Medico.query.first()

    yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    response = client.post(
            "/reserve",
        data={
            "medico_id": str(doctor.id),
            "fecha": yesterday,
            "hora": "09:00",
        },
        follow_redirects=True,
    )

    assert b"fecha" in response.data.lower()

def test_reserve_invalid_time(client):
    register_client(client)
    login_client(client)

    with client.application.app_context():
        doctor = Medico.query.first()

    fecha = get_next_weekday().strftime("%Y-%m-%d")

    response = client.post(
        "/reserve",
        data={
            "medico_id": str(doctor.id),
            "fecha": fecha,
            "hora": "09:01",
        },
        follow_redirects=True,
    )

    assert b"hora" in response.data.lower()

def test_user_cannot_cancel_other_user_appointment(client):
    register_client(client, "user1@test.com")
    login_client(client, "user1@test.com")

    with client.application.app_context():
        patient = User.query.filter_by(email="user1@test.com").first()
        doctor = Medico.query.first()

        cita = Cita(
            usuario_id=patient.id,
            medico_id=doctor.id,
            fecha=get_next_weekday(),
            hora=datetime.strptime("09:00", "%H:%M").time(),
            estado="programada",
        )

        db.session.add(cita)
        db.session.commit()
        cita_id = cita.id

    client.get("/logout")

    register_client(client, "user2@test.com")
    login_client(client, "user2@test.com")

    response = client.post(
        f"/cancel/{cita_id}",
        follow_redirects=True,
    )

    assert b"no existe" in response.data.lower()

def test_cannot_cancel_twice(client):
    register_client(client)
    login_client(client)

    with client.application.app_context():
        patient = User.query.filter_by(email="test@example.com").first()
        doctor = Medico.query.first()

        cita = Cita(                
            usuario_id=patient.id,
            medico_id=doctor.id,
            fecha=get_next_weekday(),
            hora=datetime.strptime("09:00", "%H:%M").time(),
            estado="programada",
        )

        db.session.add(cita)
        db.session.commit()
        cita_id = cita.id

    response = client.post(
        f"/cancel/{cita_id}",
        follow_redirects=True,
    )

    assert b"cancelada correctamente" in response.data

    response = client.post(
        f"/cancel/{cita_id}",
        follow_redirects=True,
    )

    assert b"ya fue cancelada" in response.data.lower()

def test_same_time_different_doctors(client):
    register_client(client)
    login_client(client)

    with client.application.app_context():
        doctors = Medico.query.limit(2).all()

    fecha = get_next_weekday().strftime("%Y-%m-%d")

    response1 = client.post(
        "/reserve",
        data={
            "medico_id": str(doctors[0].id),
            "fecha": fecha,
            "hora": "09:00",
        },
        follow_redirects=True,
    )

    response2 = client.post(
        "/reserve",
        data={
            "medico_id": str(doctors[1].id),
            "fecha": fecha,
            "hora": "09:00",
        },
        follow_redirects=True,
    )

    assert b"Cita reservada" in response1.data
    assert b"Cita reservada" in response2.data