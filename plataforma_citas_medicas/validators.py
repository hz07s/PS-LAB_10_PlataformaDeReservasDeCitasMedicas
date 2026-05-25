import re
from datetime import datetime, timedelta, date as date_type, time as time_type


NAME_RE = re.compile(r"^[A-Za-z ]+$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^\d{9,15}$")
PASSWORD_SPECIALS = "!@#$%^&*"


def validate_name(value: str) -> str:
    """Valida nombre: solo letras/espacios, longitud 2-50."""
    if value is None:
        raise ValueError("El nombre es obligatorio.")
    cleaned = value.strip()
    if len(cleaned) < 2 or len(cleaned) > 50:
        raise ValueError("El nombre debe tener entre 2 y 50 caracteres.")
    if not NAME_RE.fullmatch(cleaned):
        raise ValueError("El nombre solo puede contener letras y espacios.")
    return cleaned


def validate_email(value: str) -> str:
    """Valida email con formato estandar y longitud maxima."""
    if value is None:
        raise ValueError("El email es obligatorio.")
    cleaned = value.strip().lower()
    if len(cleaned) > 100:
        raise ValueError("El email no puede exceder 100 caracteres.")
    if not EMAIL_RE.fullmatch(cleaned):
        raise ValueError("El email no tiene un formato válido.")
    return cleaned


def validate_age(value: str) -> int:
    """Valida edad como entero entre 18 y 100."""
    if value is None:
        raise ValueError("La edad es obligatoria.")
    cleaned = str(value).strip()
    if not re.fullmatch(r"\d+", cleaned):
        raise ValueError("La edad debe ser un número entero.")
    age = int(cleaned)
    if age < 18 or age > 100:
        raise ValueError("La edad debe estar entre 18 y 100.")
    return age


def validate_phone(value: str) -> str:
    """Valida telefono solo con digitos y longitud 9-15."""
    if value is None:
        raise ValueError("El teléfono es obligatorio.")
    cleaned = str(value).strip()
    if not PHONE_RE.fullmatch(cleaned):
        raise ValueError("El teléfono debe tener entre 9 y 15 dígitos.")
    return cleaned


def validate_password(value: str) -> str:
    """Valida contraseña fuerte con requisitos de complejidad."""
    if value is None:
        raise ValueError("La contraseña es obligatoria.")
    if len(value) < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres.")
    if not re.search(r"[A-Z]", value):
        raise ValueError("La contraseña debe incluir al menos una mayúscula.")
    if not re.search(r"[a-z]", value):
        raise ValueError("La contraseña debe incluir al menos una minúscula.")
    if not re.search(r"\d", value):
        raise ValueError("La contraseña debe incluir al menos un dígito.")
    if not re.search(rf"[{re.escape(PASSWORD_SPECIALS)}]", value):
        raise ValueError(
            "La contraseña debe incluir al menos un carácter especial: !@#$%^&*."
        )
    return value


def validate_confirm_password(password: str, confirm: str) -> None:
    """Valida que la confirmacion coincida con la contraseña."""
    if password != confirm:
        raise ValueError("La confirmación de contraseña no coincide.")


def validate_doctor_id(value: str, valid_ids: set[int]) -> int:
    """Valida que el ID del medico exista en el conjunto permitido."""
    if value is None:
        raise ValueError("Debe seleccionar un médico válido.")
    cleaned = str(value).strip()
    if not cleaned.isdigit():
        raise ValueError("Debe seleccionar un médico válido.")
    doctor_id = int(cleaned)
    if doctor_id not in valid_ids:
        raise ValueError("El médico seleccionado no existe.")
    return doctor_id


def validate_date(value: str, today: date_type | None = None) -> date_type:
    """Valida fecha futura (>= hoy+1) y dia habil."""
    if value is None:
        raise ValueError("La fecha es obligatoria.")
    cleaned = value.strip()
    try:
        selected = datetime.strptime(cleaned, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError("La fecha debe tener formato YYYY-MM-DD.") from exc

    base = today or date_type.today()
    min_date = base + timedelta(days=1)
    max_date = base + timedelta(days=120)
    if selected < min_date:
        raise ValueError("La fecha debe ser al menos un día después de hoy.")
    if selected > max_date:
        raise ValueError("La cita no puede exceder los 120 dias.")
    if selected.weekday() >= 5:
        raise ValueError("La fecha debe ser un día hábil (lunes a viernes).")
    return selected


def validate_time(
    value: str, start: time_type, end: time_type, duration_min: int = 30
) -> time_type:
    """Valida hora con formato, bloque de 30 minutos y horario del medico."""
    if value is None:
        raise ValueError("La hora es obligatoria.")
    cleaned = value.strip()
    try:
        parsed = datetime.strptime(cleaned, "%H:%M").time()
    except ValueError as exc:
        raise ValueError("La hora debe tener formato HH:MM.") from exc

    if parsed.minute not in (0, 30) or parsed.second != 0:
        raise ValueError(
            "La hora debe ser cada 30 minutos (ej. 09:00, 09:30)."
        )

    start_dt = datetime.combine(date_type.today(), start)
    end_dt = datetime.combine(date_type.today(), end)
    candidate = datetime.combine(date_type.today(), parsed)
    if candidate < start_dt:
        raise ValueError("El médico no atiende a esa hora.")
    if candidate + timedelta(minutes=duration_min) > end_dt:
        raise ValueError("El médico no atiende a esa hora.")
    return parsed


def validate_availability(exists: bool) -> None:
    """Valida disponibilidad en base a existencia de cita previa."""
    if exists:
        raise ValueError("Ya existe una cita en ese horario.")


def validate_cancellation(cita_dt: datetime, now: datetime) -> None:
    """Valida la regla de cancelacion con 2 horas de anticipacion."""
    if cita_dt <= now:
        raise ValueError("La cita ya ha pasado y no puede cancelarse.")
    if cita_dt - now < timedelta(hours=2):
        raise ValueError("Solo puedes cancelar con al menos 2 horas de anticipación.")
