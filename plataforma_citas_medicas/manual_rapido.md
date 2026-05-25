# MediResist - Manual Rápido para Testers

## 1. Inicio rápido
```bash
cd plataforma_citas_medicas
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python init_db.py
python app.py
```
Acceder a: `http://127.0.0.1:5000`

## 2. Credenciales de prueba
**Usuario tester**
- Email: `tester@medireserve.com`
- Contraseña: `Test123!`

## 3. Pruebas unitarias (pytest)
```bash
pytest
```

## 4. Flujo de prueba recomendado
1. Iniciar sesión con el usuario tester.
2. En el dashboard, seleccionar médico y fecha (mínimo mañana).
3. Verificar la **tabla de disponibilidad** (libre/ocupada) y el **selector de horas**.
4. Reservar una cita libre.
5. Intentar reservar el mismo horario (debe fallar con mensaje claro).
6. Probar cancelación:
   - Cita con más de 2 horas de anticipación: **se cancela**.
   - Cita con menos de 2 horas o pasada: **se rechaza**.

## 5. Datos precargados
**Médicos**
- Dr. Juan Perez - Cardiología - 09:00 a 17:00 (Almuerzo 12:30-13:30)  
- Dra. Maria Gomez - Dermatología - 08:00 a 14:00 (Almuerzo 12:30-13:30)  
- Dr. Luis Fernandez - Pediatría - 10:00 a 18:00 (Almuerzo 12:30-13:30)  

**Usuarios adicionales**
- Ana Lopez y Carlos Ruiz con citas distribuidas en distintos médicos (futuras y pasadas).

## 6. Notas de validación crítica
- **Nombre:** solo letras y espacios (2-50).
- **Email:** formato válido y único.
- **Edad:** entero 18-100.
- **Teléfono:** Perú, 9 dígitos iniciando con 9.
- **Contraseña:** 8-64 con mayúscula, minúscula, dígito y especial (!@#$%^&*). Solo letras inglesas y números.
- **Fecha de cita:** >= hoy+1, solo lunes a viernes.
- **Hora:** bloques de 30 min, dentro del horario del médico y fuera del almuerzo.

## 7. Si ves errores de esquema
Si cambió el modelo o aparece un error de columnas, borra `mediresist.db` y ejecuta de nuevo:
```bash
python init_db.py
```
