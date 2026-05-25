# MediResist - Plataforma de Reserva de Citas Médicas

**Curso:** Laboratorio de Pruebas de Software  
**Integrantes:** Choquehuanca Zapana Hernan Andy, Flores Choquehuanca Joe Daniel, Larico Rodriguez Bryan Fernando, Maldonado Vilca Victor Gonzalo

## Descripción
MediResist es un sistema web minimalista y robusto para reservar citas médicas. Implementa validaciones estrictas, seguridad básica (hashing, CSRF) y reglas de negocio específicas para evitar fallos en pruebas adversarias.

## Requisitos previos
- Python 3.10+
- pip

## Instalación y ejecución
```bash
cd plataforma_citas_medicas
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python init_db.py
python app.py
```

La aplicación quedará disponible en `http://127.0.0.1:5000`.

## Médicos precargados
- Dr. Juan Perez - Cardiologia - 09:00-17:00 (Almuerzo 12:30-13:30)
- Dra. Maria Gomez - Dermatologia - 08:00-14:00 (Almuerzo 12:30-13:30)
- Dr. Luis Fernandez - Pediatria - 10:00-18:00 (Almuerzo 12:30-13:30)

## Usuario tester
- Email: tester@medireserve.com
- Contraseña: Test123!

## Pruebas unitarias
```bash
pytest
```
Las pruebas cubren el 100% de las particiones de equivalencia y los valores límite definidos.

## Documentación técnica
Consulte `documento_tecnico.md` para la especificación de pruebas PE/AVL y decisiones de implementación.

## Manual rápido
Consulte `manual_rapido.md` para un flujo de prueba breve para testers.
