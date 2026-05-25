import logging
import os
from datetime import date as date_type, datetime, timedelta
from functools import wraps

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import inspect as sqlalchemy_inspect
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException
from werkzeug.security import check_password_hash, generate_password_hash

from models import Cita, Medico, User, db
from utils import combine_date_time, get_availability, seed_demo_data, seed_doctors
from validators import (
    validate_age,
    validate_availability,
    validate_cancellation,
    validate_confirm_password,
    validate_date,
    validate_doctor_id,
    validate_email,
    validate_name,
    validate_password,
    validate_phone,
    validate_time,
)


FAILED_LOGINS: dict[str, dict[str, datetime | int | None]] = {}


def _get_client_key() -> str:
    """Obtiene un identificador simple por IP para bloqueo temporal."""
    return request.headers.get("X-Forwarded-For", request.remote_addr) or "unknown"


def _is_blocked(key: str) -> bool:
    """Verifica si el email/IP esta bloqueado por intentos fallidos."""
    entry = FAILED_LOGINS.get(key)
    if not entry:
        return False
    blocked_until = entry.get("blocked_until")
    if blocked_until and datetime.now() >= blocked_until:
        FAILED_LOGINS.pop(key, None)
        return False
    return bool(blocked_until)


def _register_failure(key: str) -> None:
    """Registra un intento fallido y aplica bloqueo si corresponde."""
    entry = FAILED_LOGINS.get(key, {"count": 0, "blocked_until": None})
    blocked_until = entry.get("blocked_until")
    if blocked_until and datetime.now() >= blocked_until:
        entry = {"count": 0, "blocked_until": None}
    entry["count"] = int(entry.get("count", 0)) + 1
    if entry["count"] >= 3:
        entry["blocked_until"] = datetime.now() + timedelta(minutes=5)
    FAILED_LOGINS[key] = entry


def _clear_failures(key: str) -> None:
    """Limpia los intentos fallidos luego de un login exitoso."""
    FAILED_LOGINS.pop(key, None)


def login_required(view):
    """Decorador para proteger rutas autenticadas."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Debe iniciar sesión para continuar.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


def create_app(test_config: dict | None = None) -> Flask:
    """Crea y configura la aplicacion Flask."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "sqlite:///mediresist.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config.setdefault("SEED_DEMO_DATA", True)
    if test_config:
        app.config.update(test_config)

    # Proteccion CSRF obligatoria.
    CSRFProtect(app)
    db.init_app(app)

    with app.app_context():
        db.create_all()
        inspector = sqlalchemy_inspect(db.engine)
        tables = set(inspector.get_table_names())
        needs_reset = False
        if not {"usuarios", "medicos", "citas"}.issubset(tables):
            needs_reset = True
        else:
            cita_cols = {col["name"] for col in inspector.get_columns("citas")}
            if "usuario_id" not in cita_cols:
                needs_reset = True

        if needs_reset:
            logging.warning("Schema desactualizado detectado. Recreando base de datos.")
            db.drop_all()
            db.create_all()

        seed_doctors(db.session)
        if app.config.get("SEED_DEMO_DATA", True):
            seed_demo_data(db.session)

    logging.basicConfig(level=logging.INFO)

    @app.errorhandler(Exception)
    def handle_exception(error):
        """Maneja errores inesperados sin exponer detalles al usuario."""
        if isinstance(error, HTTPException):
            return error
        app.logger.exception("Unexpected error: %s", error)
        flash("Ha ocurrido un error interno.", "error")
        return redirect(url_for("login")), 500

    @app.route("/")
    def home():
        """Redirecciona segun estado de autenticacion."""
        if "user_id" in session:
            return redirect(url_for("dashboard"))
        return redirect(url_for("login"))

    @app.route("/register", methods=["GET", "POST"])
    def register():
        """Registro de nuevos usuarios con validaciones estrictas."""
        if request.method == "POST":
            try:
                nombre = validate_name(request.form.get("nombre", ""))
                email = validate_email(request.form.get("email", ""))
                edad = validate_age(request.form.get("edad", ""))
                telefono = validate_phone(request.form.get("telefono", ""))
                password = validate_password(request.form.get("password", ""))
                confirm = request.form.get("confirm_password", "")
                validate_confirm_password(password, confirm)
            except ValueError as exc:
                flash(str(exc), "error")
                return render_template("register.html", form=request.form)

            if User.query.filter_by(email=email).first():
                flash("El email ya está registrado.", "error")
                return render_template("register.html", form=request.form)

            user = User(
                nombre=nombre,
                email=email,
                edad=edad,
                telefono=telefono,
                password_hash=generate_password_hash(password),
            )
            db.session.add(user)
            db.session.commit()
            flash("Registro exitoso. Ahora puede iniciar sesión.", "success")
            return redirect(url_for("login"))

        return render_template("register.html", form={})

    @app.route("/login", methods=["GET", "POST"])
    def login():
        """Inicio de sesion con bloqueo temporal por intentos fallidos."""
        if request.method == "POST":
            email_input = request.form.get("email", "")
            email = email_input.strip().lower()
            client_key = _get_client_key()
            if _is_blocked(email) or _is_blocked(client_key):
                flash("Demasiados intentos. Espere 5 minutos.", "error")
                return render_template("login.html", form=request.form)

            user = User.query.filter_by(email=email).first()
            password = request.form.get("password", "")
            if not user or not check_password_hash(user.password_hash, password):
                _register_failure(email)
                _register_failure(client_key)
                flash("Email o contraseña incorrectos.", "error")
                return render_template("login.html", form=request.form)

            _clear_failures(email)
            _clear_failures(client_key)
            session["user_id"] = user.id
            session["user_name"] = user.nombre
            flash("Inicio de sesión exitoso.", "success")
            return redirect(url_for("dashboard"))

        return render_template("login.html", form={})

    @app.route("/dashboard", methods=["GET"])
    @login_required
    def dashboard():
        """Panel principal con reservas y listado de citas."""
        doctors = Medico.query.all()
        now = datetime.now()
        citas = (
            Cita.query.filter_by(usuario_id=session["user_id"])
            .filter(Cita.estado == "programada")
            .order_by(Cita.fecha.asc(), Cita.hora.asc())
            .all()
        )
        citas_view = []
        for cita in citas:
            cita_dt = combine_date_time(cita.fecha, cita.hora)
            status = "Pasada" if cita_dt < now else "Programada"
            can_cancel = cita_dt - now >= timedelta(hours=2)
            citas_view.append(
                {
                    "cita": cita,
                    "estado": status,
                    "cancelable": can_cancel,
                }
            )

        min_date = (date_type.today() + timedelta(days=1)).strftime("%Y-%m-%d")

        return render_template(
            "dashboard.html",
            doctors=doctors,
            citas=citas_view,
            min_date=min_date,
            user_name=session.get("user_name", ""),
        )

    @app.route("/reserve", methods=["POST"])
    @login_required
    def reserve():
        """Reserva de cita con validaciones y transaccion segura."""
        doctors = Medico.query.all()
        valid_ids = {doctor.id for doctor in doctors}
        try:
            doctor_id = validate_doctor_id(request.form.get("medico_id", ""), valid_ids)
            doctor = db.session.get(Medico, doctor_id)
            if not doctor:
                raise ValueError("El médico seleccionado no existe.")

            fecha = validate_date(request.form.get("fecha", ""))
            hora = validate_time(
                request.form.get("hora", ""),
                doctor.hora_inicio,
                doctor.hora_fin,
                doctor.duracion_min,
            )
        except ValueError as exc:
            flash(str(exc), "error")
            return redirect(url_for("dashboard"))

        try:
            with db.session.begin_nested():
                exists = (
                    Cita.query.filter_by(
                        medico_id=doctor_id,
                        fecha=fecha,
                        hora=hora,
                        estado="programada",
                    ).first()
                    is not None
                )
                validate_availability(exists)
                cita = Cita(
                    usuario_id=session["user_id"],
                    medico_id=doctor_id,
                    fecha=fecha,
                    hora=hora,
                    estado="programada",
                )
                db.session.add(cita)
            db.session.commit()
            flash("Cita reservada correctamente.", "success")
        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), "error")
        except IntegrityError:
            db.session.rollback()
            flash("Ya existe una cita en ese horario.", "error")

        return redirect(url_for("dashboard"))

    @app.route("/cancel/<int:cita_id>", methods=["POST"])
    @login_required
    def cancel(cita_id: int):
        """Cancela una cita si cumple la regla de 2 horas de anticipacion."""
        cita = Cita.query.filter_by(
            id=cita_id, usuario_id=session["user_id"], estado="programada"
        ).first()
        if not cita:
            flash("La cita no existe o ya fue cancelada.", "error")
            return redirect(url_for("dashboard"))

        try:
            cita_dt = combine_date_time(cita.fecha, cita.hora)
            validate_cancellation(cita_dt, datetime.now())
        except ValueError as exc:
            flash(str(exc), "error")
            return redirect(url_for("dashboard"))

        cita.estado = "cancelada"
        db.session.commit()
        flash("Cita cancelada correctamente.", "success")
        return redirect(url_for("dashboard"))

    @app.route("/api/availability", methods=["GET"])
    @login_required
    def api_availability():
        """API interna para obtener disponibilidad por medico y fecha."""
        doctors = Medico.query.all()
        valid_ids = {doctor.id for doctor in doctors}
        medico_id = request.args.get("medico_id", "")
        fecha_input = request.args.get("fecha", "")
        try:
            doctor_id = validate_doctor_id(medico_id, valid_ids)
            doctor = db.session.get(Medico, doctor_id)
            if not doctor:
                raise ValueError("El médico seleccionado no existe.")
            fecha = validate_date(fecha_input)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        slots = get_availability(db.session, doctor, fecha)
        return jsonify({"slots": slots})

    @app.route("/logout")
    def logout():
        """Cierra sesion y limpia la informacion temporal."""
        session.clear()
        flash("Sesión cerrada.", "success")
        return redirect(url_for("login"))

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=False)
