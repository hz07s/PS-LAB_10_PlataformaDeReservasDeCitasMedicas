# Documento tecnico - MediResist

**Integrantes:** Equipo X  
**Sistema:** Plataforma de Reserva de Citas Medicas (MediResist)

## 1. Arquitectura
- **Backend:** Flask (Python)
- **ORM:** SQLAlchemy
- **BD:** SQLite
- **Seguridad:** Hash de contrasenas (Werkzeug), CSRF (Flask-WTF), autoescaping de Jinja2

## 2. Tablas de particion de equivalencia (PE)

| Campo | Clases validas | Clases invalidas |
| --- | --- | --- |
| Nombre | Letras y espacios, 2-50 caracteres | Longitud <2, >50; contiene numeros; contiene simbolos |
| Email | Formato local@dominio.tld, longitud <=100 | Sin @; sin punto en dominio; longitud >100; espacios |
| Edad | Entero 18-100 | <18; >100; decimal; letras |
| Telefono | Digitos 9-15 | Longitud <9 o >15; contiene no digitos |
| Contrasena | >=8 con mayuscula, minuscula, digito y !@#$%^&* | Falta uno de los requisitos; longitud <8 |
| Confirmacion | Igual a contrasena | Distinta a contrasena |
| Medico | ID existente | ID inexistente; ID no numerico |
| Fecha | YYYY-MM-DD; >= hoy+1; lunes a viernes | Formato invalido; fecha pasada; fin de semana |
| Hora | HH:MM; minutos 00/30; dentro de horario | Minutos distintos de 00/30; fuera de horario; hora >= fin |
| Disponibilidad | Sin cita previa mismo medico/fecha/hora | Ya existe cita en ese horario |
| Cancelacion | Cita futura con >= 2 horas de anticipacion | Cita pasada; diferencia < 2 horas |

## 3. Analisis de valores limite (AVL)

| Campo | Justo antes | Limite | Justo despues |
| --- | --- | --- | --- |
| Nombre (longitud) | 1 char | 2 chars | 3 chars |
| Nombre (max) | 49 chars | 50 chars | 51 chars |
| Email (longitud) | 99 chars | 100 chars | 101 chars |
| Edad | 17 | 18 | 19 |
| Edad (max) | 99 | 100 | 101 |
| Telefono (min) | 8 digitos | 9 digitos | 10 digitos |
| Telefono (max) | 14 digitos | 15 digitos | 16 digitos |
| Fecha (min) | hoy | hoy+1 | hoy+2 |
| Hora (inicio) | 08:59 | 09:00 | 09:01 |
| Hora (bloques) | 09:29 | 09:30 | 09:31 |
| Hora (fin) | 16:30 | 17:00 | 17:01 |
| Cancelacion | 1h59 | 2h00 | 2h01 |

## 4. Casos de prueba (PE + AVL)

| ID | Descripcion | Entrada | Resultado esperado |
| --- | --- | --- | --- |
| TC-01 | Nombre valido minimo | "Ana" | Aceptado |
| TC-02 | Nombre invalido muy corto | "A" | Error |
| TC-03 | Nombre invalido con numero | "Juan1" | Error |
| TC-04 | Nombre valido maximo | 50 letras | Aceptado |
| TC-05 | Nombre invalido maximo+1 | 51 letras | Error |
| TC-06 | Email valido | test@example.com | Aceptado |
| TC-07 | Email sin arroba | testexample.com | Error |
| TC-08 | Email sin punto en dominio | test@domain | Error |
| TC-09 | Email longitud 100 | 100 chars | Aceptado |
| TC-10 | Email longitud 101 | 101 chars | Error |
| TC-11 | Edad limite inferior | 18 | Aceptado |
| TC-12 | Edad menor al limite | 17 | Error |
| TC-13 | Edad limite superior | 100 | Aceptado |
| TC-14 | Edad mayor al limite | 101 | Error |
| TC-15 | Telefono minimo | 9 digitos | Aceptado |
| TC-16 | Telefono menor a minimo | 8 digitos | Error |
| TC-17 | Telefono maximo | 15 digitos | Aceptado |
| TC-18 | Telefono mayor a maximo | 16 digitos | Error |
| TC-19 | Password valida | Test123! | Aceptado |
| TC-20 | Password sin mayuscula | test123! | Error |
| TC-21 | Password sin minuscula | TEST123! | Error |
| TC-22 | Password sin digito | Test!!! | Error |
| TC-23 | Password sin especial | Test1234 | Error |
| TC-24 | Confirmacion distinta | Test123! / Test123 | Error |
| TC-25 | Fecha hoy | hoy | Error |
| TC-26 | Fecha hoy+1 habil | hoy+1 (habil) | Aceptado |
| TC-27 | Fecha fin de semana | sabado o domingo | Error |
| TC-28 | Hora antes de inicio | 08:59 | Error |
| TC-29 | Hora inicio exacta | 09:00 | Aceptado |
| TC-30 | Hora no en bloque | 09:01 | Error |
| TC-31 | Hora en bloque | 09:30 | Aceptado |
| TC-32 | Hora ultima valida | 16:30 | Aceptado |
| TC-33 | Hora fin exacta | 17:00 | Error |
| TC-34 | Disponibilidad ocupada | cita duplicada | Error |
| TC-35 | Cancelacion 2h exactas | now+2h | Aceptado |
| TC-36 | Cancelacion 1h59 | now+1h59 | Error |
| TC-37 | Cancelacion pasada | now-1m | Error |

## 5. Cobertura de pruebas
Las pruebas unitarias y de integracion implementadas con pytest cubren el 100% de las particiones de equivalencia y los valores limite listados en este documento.

## 6. Decisiones de implementacion
- **Concurrencia:** Se uso una restriccion unica (medico_id, fecha, hora) y manejo de IntegrityError para evitar doble reserva.
- **Seguridad:** Hash de contrasenas con Werkzeug y CSRF en formularios.
- **Fechas y horas:** Comparaciones con datetime.now() consistente en toda la aplicacion.
- **Disponibilidad:** API interna `/api/availability` devuelve horarios libres/ocupados para actualizar el selector de horas.
- **Errores inesperados:** Captura global con mensaje generico y registro en logs.
