# Manual de Usuario - MediResist

## 1. Introducción
MediResist es una plataforma web para registrar pacientes y reservar citas médicas en horarios predefinidos. Está diseñada para evitar errores por entradas inválidas o límites extremos.

## 2. Cómo ejecutar la aplicación
1. Abrir una terminal en la carpeta `plataforma_citas_medicas`.
2. Ejecutar:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt
   python init_db.py
   python app.py
   ```
3. Abrir el navegador en `http://127.0.0.1:5000`.

## 3. Pantallas del sistema

### 3.1 Registro (/register)
Permite crear una cuenta de paciente.

**Campos y reglas principales:**
- **Nombre:** Solo letras y espacios, de 2 a 50 caracteres.
- **Email:** Formato valido (ej. usuario@dominio.com).
- **Edad:** Entero entre 18 y 100.
- **Telefono:** Solo digitos, 9 a 15 caracteres.
- **Contraseña:** Minimo 8 caracteres, con mayuscula, minuscula, digito y caracter especial !@#$%^&*.

**Ejemplo valido:**
- Nombre: Ana Lopez
- Email: ana.lopez@example.com
- Edad: 29
- Telefono: 987654321
- Contraseña: Ana1234!

**Ejemplo invalido:**
- Nombre: Ana1
- Email: ana@dominio
- Edad: 17
- Telefono: 123-456
- Contraseña: ana1234

**Captura simulada:**
> [Registro: formulario con campos y un boton "Registrarme"]

### 3.2 Inicio de sesión (/login)
Ingresar con email y contraseña.

**Reglas:**
- Mensaje generico si email o contraseña son incorrectos.
- Despues de 3 intentos fallidos consecutivos, se bloquea por 5 minutos.

**Captura simulada:**
> [Login: formulario de email y contraseña con boton "Ingresar"]

### 3.3 Panel principal (/dashboard)
Muestra:
- Lista de medicos precargados.
- Formulario de reserva de citas con selector dinamico de horas disponibles.
- Tabla de citas futuras y pasadas con indicador de cancelacion.
- Tabla de disponibilidad con horarios libres (verde) y ocupados (rojo).

**Captura simulada:**
> [Dashboard: card de "Reservar cita" a la izquierda y "Mis citas" a la derecha]

### 3.4 Cerrar sesión (/logout)
Finaliza la sesion y vuelve al login.

## 4. Reservar una cita
1. Seleccionar un medico.
2. Elegir fecha en formato YYYY-MM-DD (el sistema bloquea fines de semana).
3. Elegir hora en bloques de 30 minutos desde el selector.

**Restricciones clave:**
- Solo fechas habiles (lunes a viernes).
- La fecha debe ser al menos un dia despues de hoy.
- La cita no puede exceder los 120 dias a partir de hoy.
- Horas validas dentro del horario del medico (inicio inclusive, fin exclusivo).
- No se permite doble reserva para el mismo medico, fecha y hora.

**Ejemplo valido:**
- Medico: Dr. Juan Perez
- Fecha: 2026-05-19 (martes)
- Hora: 09:30

**Ejemplo invalido:**
- Fecha: sabado o domingo.
- Hora: 17:00 si el medico termina a las 17:00.

## 5. Cancelar una cita
Una cita solo se puede cancelar si faltan 2 horas o mas para la hora agendada.

**Ejemplo valido:**
- Cita a las 16:00, hora actual 13:59 -> OK

**Ejemplo invalido:**
- Cita a las 16:00, hora actual 14:30 -> Rechazada

## 6. Consejos para evitar errores
- Verifique el formato de fecha y hora.
- Use solo numeros en telefono.
- No intente reservar el mismo horario dos veces.
- Mantenga una contraseña fuerte.

## 7. Datos precargados
Usuario tester:
- Email: tester@medireserve.com
- Contrasena: Test123!

Medicos disponibles:
- Dr. Juan Perez - Cardiologia - 09:00 a 17:00
- Dra. Maria Gomez - Dermatologia - 08:00 a 14:00
- Dr. Luis Fernandez - Pediatria - 10:00 a 18:00
