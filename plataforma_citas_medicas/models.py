from datetime import datetime, time as time_type

from flask_sqlalchemy import SQLAlchemy

# Instancia central de SQLAlchemy para el proyecto.
db = SQLAlchemy()


class User(db.Model):
    """Modelo de usuario/paciente con datos personales y credenciales."""

    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    edad = db.Column(db.Integer, nullable=False)
    telefono = db.Column(db.String(15), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    citas = db.relationship("Cita", backref="usuario", lazy=True)

    def __init__(self, nombre, email, edad, telefono, password_hash, **kwargs):
        kwargs["nombre"] = nombre
        kwargs["email"] = email
        kwargs["edad"] = edad
        kwargs["telefono"] = telefono
        kwargs["password_hash"] = password_hash
        super().__init__(**kwargs)


class Medico(db.Model):
    """Modelo de medico con horario fijo y duracion de citas."""

    __tablename__ = "medicos"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), nullable=False)
    especialidad = db.Column(db.String(80), nullable=False)
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fin = db.Column(db.Time, nullable=False)
    almuerzo_inicio = db.Column(db.Time, nullable=False, default=time_type(12, 30))
    almuerzo_fin = db.Column(db.Time, nullable=False, default=time_type(13, 30))
    duracion_min = db.Column(db.Integer, nullable=False, default=30)

    citas = db.relationship("Cita", backref="medico", lazy=True)

    def __init__(
        self,
        nombre,
        especialidad,
        hora_inicio,
        hora_fin,
        almuerzo_inicio=time_type(12, 30),
        almuerzo_fin=time_type(13, 30),
        duracion_min=30,
        **kwargs,
    ):
        kwargs["nombre"] = nombre
        kwargs["especialidad"] = especialidad
        kwargs["hora_inicio"] = hora_inicio
        kwargs["hora_fin"] = hora_fin
        kwargs["almuerzo_inicio"] = almuerzo_inicio
        kwargs["almuerzo_fin"] = almuerzo_fin
        kwargs["duracion_min"] = duracion_min
        super().__init__(**kwargs)


class Cita(db.Model):
    """Modelo de cita con restriccion de unicidad por medico/fecha/hora."""

    __tablename__ = "citas"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    medico_id = db.Column(db.Integer, db.ForeignKey("medicos.id"), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    hora = db.Column(db.Time, nullable=False)
    estado = db.Column(db.String(20), nullable=False, default="programada")
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    __table_args__ = (
        db.UniqueConstraint(
            "medico_id", "fecha", "hora", name="uq_cita_medico_fecha_hora"
        ),
    )

    def __init__(self, usuario_id, medico_id, fecha, hora, estado="programada", **kwargs):
        kwargs["usuario_id"] = usuario_id
        kwargs["medico_id"] = medico_id
        kwargs["fecha"] = fecha
        kwargs["hora"] = hora
        kwargs["estado"] = estado
        super().__init__(**kwargs)
