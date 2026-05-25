from datetime import date as date_type, datetime, time as time_type, timedelta

from werkzeug.security import generate_password_hash

from models import Cita, Medico, User


def seed_doctors(session) -> None:
    """Crea los medicos base si la tabla esta vacia."""
    if session.query(Medico).count() > 0:
        return
    almuerzo_inicio = time_type(12, 30)
    almuerzo_fin = time_type(13, 30)
    doctors = [
        Medico(
            nombre="Dr. Juan Perez",
            especialidad="Cardiologia",
            hora_inicio=time_type(9, 0),
            hora_fin=time_type(17, 0),
            almuerzo_inicio=almuerzo_inicio,
            almuerzo_fin=almuerzo_fin,
            duracion_min=30,
        ),
        Medico(
            nombre="Dra. Maria Gomez",
            especialidad="Dermatologia",
            hora_inicio=time_type(8, 0),
            hora_fin=time_type(14, 0),
            almuerzo_inicio=almuerzo_inicio,
            almuerzo_fin=almuerzo_fin,
            duracion_min=30,
        ),
        Medico(
            nombre="Dr. Luis Fernandez",
            especialidad="Pediatria",
            hora_inicio=time_type(10, 0),
            hora_fin=time_type(18, 0),
            almuerzo_inicio=almuerzo_inicio,
            almuerzo_fin=almuerzo_fin,
            duracion_min=30,
        ),
    ]
    session.add_all(doctors)
    session.commit()


def _next_weekday(base_date: date_type) -> date_type:
    """Avanza hasta el siguiente dia habil."""
    candidate = base_date
    while candidate.weekday() >= 5:
        candidate += timedelta(days=1)
    return candidate


def _previous_weekday(base_date: date_type) -> date_type:
    """Retrocede hasta el dia habil anterior."""
    candidate = base_date
    while candidate.weekday() >= 5:
        candidate -= timedelta(days=1)
    return candidate


def seed_demo_data(session) -> None:
    """Precarga usuarios de prueba y citas de demostracion."""
    if session.query(User).filter_by(email="tester@medireserve.com").first():
        return

    tester = User(
        nombre="Usuario Tester",
        email="tester@medireserve.com",
        edad=30,
        telefono="999888777",
        password_hash=generate_password_hash("Test123!"),
    )
    ana = User(
        nombre="Ana Lopez",
        email="ana.lopez@example.com",
        edad=28,
        telefono="987654321",
        password_hash=generate_password_hash("Test123!"),
    )
    carlos = User(
        nombre="Carlos Ruiz",
        email="carlos.ruiz@example.com",
        edad=35,
        telefono="998877665",
        password_hash=generate_password_hash("Test123!"),
    )
    session.add_all([tester, ana, carlos])
    session.commit()

    doctors = {doctor.nombre: doctor for doctor in session.query(Medico).all()}
    today = date_type.today()
    future = _next_weekday(today + timedelta(days=1))
    future_alt = _next_weekday(today + timedelta(days=2))
    past = _previous_weekday(today - timedelta(days=1))
    past_alt = _previous_weekday(today - timedelta(days=2))

    citas = [
        # Dr. Juan Perez (09:00-17:00)
        Cita(
            usuario_id=ana.id,
            medico_id=doctors["Dr. Juan Perez"].id,
            fecha=future,
            hora=time_type(10, 0),
            estado="programada",
        ),
        Cita(
            usuario_id=carlos.id,
            medico_id=doctors["Dr. Juan Perez"].id,
            fecha=past,
            hora=time_type(15, 30),
            estado="programada",
        ),
        # Dra. Maria Gomez (08:00-14:00)
        Cita(
            usuario_id=carlos.id,
            medico_id=doctors["Dra. Maria Gomez"].id,
            fecha=future_alt,
            hora=time_type(9, 0),
            estado="programada",
        ),
        Cita(
            usuario_id=ana.id,
            medico_id=doctors["Dra. Maria Gomez"].id,
            fecha=past_alt,
            hora=time_type(13, 0),
            estado="programada",
        ),
        # Dr. Luis Fernandez (10:00-18:00)
        Cita(
            usuario_id=ana.id,
            medico_id=doctors["Dr. Luis Fernandez"].id,
            fecha=future,
            hora=time_type(11, 30),
            estado="programada",
        ),
        Cita(
            usuario_id=carlos.id,
            medico_id=doctors["Dr. Luis Fernandez"].id,
            fecha=past,
            hora=time_type(16, 0),
            estado="programada",
        ),
    ]
    session.add_all(citas)
    session.commit()


def generate_time_slots(
    start: time_type, end: time_type, duration_min: int = 30
) -> list[str]:
    """Genera los bloques de tiempo validos en formato HH:MM."""
    slots = []
    current = datetime.combine(date_type.today(), start)
    end_dt = datetime.combine(date_type.today(), end)
    while current + timedelta(minutes=duration_min) <= end_dt:
        slots.append(current.strftime("%H:%M"))
        current += timedelta(minutes=duration_min)
    return slots


def _overlaps_lunch(
    slot_time: time_type,
    duration_min: int,
    lunch_start: time_type,
    lunch_end: time_type,
) -> bool:
    """Indica si el bloque de la cita se cruza con el almuerzo."""
    slot_start = datetime.combine(date_type.today(), slot_time)
    slot_end = slot_start + timedelta(minutes=duration_min)
    lunch_start_dt = datetime.combine(date_type.today(), lunch_start)
    lunch_end_dt = datetime.combine(date_type.today(), lunch_end)
    return slot_start < lunch_end_dt and slot_end > lunch_start_dt


def get_availability(session, medico: Medico, fecha: date_type) -> list[dict]:
    """Devuelve una lista de horarios con estado libre/ocupado."""
    slots = generate_time_slots(medico.hora_inicio, medico.hora_fin, medico.duracion_min)
    occupied = {
        cita.hora.strftime("%H:%M")
        for cita in session.query(Cita)
        .filter_by(medico_id=medico.id, fecha=fecha, estado="programada")
        .all()
    }
    availability = []
    for slot in slots:
        slot_time = datetime.strptime(slot, "%H:%M").time()
        if _overlaps_lunch(
            slot_time,
            medico.duracion_min,
            medico.almuerzo_inicio,
            medico.almuerzo_fin,
        ):
            status = "Almuerzo"
        elif slot in occupied:
            status = "Ocupada"
        else:
            status = "Libre"
        availability.append({"time": slot, "status": status})
    return availability


def check_disponibilidad(
    session, medico: Medico, fecha: date_type, hora: time_type
) -> bool:
    """Indica si una cita esta libre para medico/fecha/hora."""
    exists = (
        session.query(Cita)
        .filter_by(medico_id=medico.id, fecha=fecha, hora=hora, estado="programada")
        .first()
        is not None
    )
    return not exists


def cancelacion_posible(cita_dt: datetime, now: datetime) -> bool:
    """Evalua si la cancelacion cumple la regla de 2 horas."""
    return cita_dt - now >= timedelta(hours=2)


def precarga_datos(session) -> None:
    """Alias publico para la precarga de datos de demostracion."""
    seed_demo_data(session)


def combine_date_time(fecha: date_type, hora: time_type) -> datetime:
    """Combina fecha y hora en un datetime naive consistente."""
    return datetime.combine(fecha, hora)
