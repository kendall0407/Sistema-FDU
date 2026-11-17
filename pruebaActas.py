
from conexion import ObtenerConexion
from sesion import RegistrarSesion

from actas import (
    CrearActa,
    ConsultarActa,
    ModificarActa,
    EliminarActa
)

from datetime import date, time, timedelta
import re


# ==========================================
# CONFIGURACION DE PRUEBAS
# ==========================================

pruebas_exitosas = 0
pruebas_fallidas = 0


def Probar(nombre, resultado):
    global pruebas_exitosas, pruebas_fallidas

    if resultado:
        print(f"[OK] {nombre}")
        pruebas_exitosas += 1
    else:
        print(f"[ERROR] {nombre}")
        pruebas_fallidas += 1


# ==========================================
# OBTENER USUARIOS PARA LAS PRUEBAS
# ==========================================

conexion = ObtenerConexion()
cursor = conexion.cursor()

cursor.execute("""
    SELECT TOP 1 id
    FROM Usuario
    WHERE rol_id = 4
      AND estado_id = 1
      AND bloqueado = 0
    ORDER BY id
""")

fila_asistente = cursor.fetchone()

cursor.execute("""
    SELECT TOP 1 id
    FROM Usuario
    WHERE rol_id = 3
      AND estado_id = 1
      AND bloqueado = 0
    ORDER BY id
""")

fila_comite = cursor.fetchone()

conexion.close()

if not fila_asistente:
    raise Exception("No existe un usuario activo con rol Asistente del CIC.")

if not fila_comite:
    raise Exception("No existe un usuario activo con rol Miembro del Comité.")

usuario_asistente = fila_asistente[0]
usuario_comite = fila_comite[0]

print("\n==========================================")
print("       PRUEBAS DEL MODULO DE ACTAS")
print("==========================================")

print(f"Asistente de prueba: {usuario_asistente}")
print(f"Usuario sin permisos: {usuario_comite}")


# ==========================================
# CREAR UNA SESION EXCLUSIVA PARA LAS PRUEBAS
# ==========================================

fecha_prueba = (date.today() + timedelta(days=30)).isoformat()
hora_inicio = "09:00:00"
hora_fin = "10:00:00"

resultado, mensaje = RegistrarSesion(
    usuario_id=usuario_asistente,
    fecha=fecha_prueba,
    hora_inicio=hora_inicio,
    hora_fin=hora_fin,
    participantes=[usuario_comite]
)

if not resultado:
    raise Exception(f"No se pudo crear la sesión de prueba: {mensaje}")

coincidencia = re.search(r"ID:\s*(\d+)", mensaje)

if not coincidencia:
    raise Exception("No se pudo obtener el ID de la sesión.")

id_sesion = int(coincidencia.group(1))

print(f"\nSesión de prueba creada. ID: {id_sesion}")


# ==========================================
# 1. PRUEBAS DE CREAR ACTA
# ==========================================

print("\n--- CREAR ACTA ---")

contenido_original = "ACTA DE PRUEBA DEL SISTEMA FDU"

resultado, mensaje = CrearActa(
    id_sesion,
    contenido_original,
    usuario_asistente
)

Probar("Crear acta correctamente", resultado)

if not resultado:
    raise Exception(f"No se pudo crear el acta: {mensaje}")

coincidencia = re.search(r"ID:\s*(\d+)", mensaje)

if not coincidencia:
    raise Exception("No se pudo obtener el ID del acta.")

id_acta = int(coincidencia.group(1))

print(f"Acta de prueba creada. ID: {id_acta}")


# Crear acta duplicada
resultado, mensaje = CrearActa(
    id_sesion,
    "ACTA DUPLICADA",
    usuario_asistente
)

Probar("Rechazar acta duplicada para la misma sesión", not resultado)


# Contenido vacío
resultado, mensaje = CrearActa(
    id_sesion,
    "",
    usuario_asistente
)

Probar("Rechazar contenido vacío", not resultado)


# ID inválido
resultado, mensaje = CrearActa(
    -1,
    "Contenido de prueba",
    usuario_asistente
)

Probar("Rechazar identificador de sesión inválido", not resultado)


# Usuario sin permisos
resultado, mensaje = CrearActa(
    id_sesion,
    "Acta no autorizada",
    usuario_comite
)

Probar("Rechazar creación sin permisos", not resultado)


# ==========================================
# 2. PRUEBAS DE CONSULTAR ACTA
# ==========================================

print("\n--- CONSULTAR ACTA ---")

# Consultar acta específica
resultado, datos = ConsultarActa(
    id_acta=id_acta,
    usuario_id=usuario_asistente
)

Probar(
    "Consultar acta por identificador",
    resultado and datos["IdActa"] == id_acta
)


# Consultar todas las actas
resultado, datos = ConsultarActa(
    usuario_id=usuario_asistente
)

Probar(
    "Consultar todas las actas",
    resultado and isinstance(datos, list)
)


# Consultar acta inexistente
resultado, datos = ConsultarActa(
    id_acta=2147483647,
    usuario_id=usuario_asistente
)

Probar("Rechazar consulta de acta inexistente", not resultado)


# Consultar con identificador inválido
resultado, datos = ConsultarActa(
    id_acta=-1,
    usuario_id=usuario_asistente
)

Probar("Rechazar identificador inválido", not resultado)


# Usuario sin permisos
resultado, datos = ConsultarActa(
    id_acta=id_acta,
    usuario_id=usuario_comite
)

Probar("Rechazar consulta sin permisos", not resultado)


# ==========================================
# 3. PRUEBAS DE MODIFICAR ACTA
# ==========================================

print("\n--- MODIFICAR ACTA ---")

contenido_modificado = "ACTA DE PRUEBA MODIFICADA"

resultado, mensaje = ModificarActa(
    id_acta,
    contenido_modificado,
    usuario_asistente
)

Probar("Modificar acta correctamente", resultado)


# Verificar contenido y fecha de modificación
conexion = ObtenerConexion()
cursor = conexion.cursor()

cursor.execute("""
    SELECT Contenido, FechaModificacion
    FROM Acta
    WHERE IdActa = ?
""", (id_acta,))

fila = cursor.fetchone()

conexion.close()

Probar(
    "Verificar contenido modificado",
    fila is not None and fila[0] == contenido_modificado
)

Probar(
    "Verificar actualización de FechaModificacion",
    fila is not None and fila[1] is not None
)


# Contenido vacío
resultado, mensaje = ModificarActa(
    id_acta,
    "",
    usuario_asistente
)

Probar("Rechazar modificación con contenido vacío", not resultado)


# ID inválido
resultado, mensaje = ModificarActa(
    -1,
    "Contenido inválido",
    usuario_asistente
)

Probar("Rechazar modificación con ID inválido", not resultado)


# Acta inexistente
resultado, mensaje = ModificarActa(
    2147483647,
    "Contenido de prueba",
    usuario_asistente
)

Probar("Rechazar modificación de acta inexistente", not resultado)


# Usuario sin permisos
resultado, mensaje = ModificarActa(
    id_acta,
    "Modificación no autorizada",
    usuario_comite
)

Probar("Rechazar modificación sin permisos", not resultado)


# ==========================================
# 4. PRUEBAS DE ELIMINAR ACTA
# ==========================================

print("\n--- ELIMINAR ACTA ---")

# Usuario sin permisos
resultado, mensaje = EliminarActa(
    id_acta,
    usuario_comite
)

Probar("Rechazar eliminación sin permisos", not resultado)


# ID inválido
resultado, mensaje = EliminarActa(
    -1,
    usuario_asistente
)

Probar("Rechazar eliminación con ID inválido", not resultado)


# Eliminar acta de prueba
resultado, mensaje = EliminarActa(
    id_acta,
    usuario_asistente
)

Probar("Cancelar acta correctamente", resultado)


# Verificar estado y fecha de modificación
conexion = ObtenerConexion()
cursor = conexion.cursor()

cursor.execute("""
    SELECT Estado, FechaModificacion
    FROM Acta
    WHERE IdActa = ?
""", (id_acta,))

fila = cursor.fetchone()

conexion.close()

Probar(
    "Verificar que el estado sea CANCELADA",
    fila is not None and fila[0] == "CANCELADA"
)

Probar(
    "Verificar fecha de modificación al cancelar",
    fila is not None and fila[1] is not None
)


# Intentar cancelar nuevamente
resultado, mensaje = EliminarActa(
    id_acta,
    usuario_asistente
)

Probar("Rechazar cancelación de un acta ya cancelada", not resultado)


# Verificar que el registro siga existiendo
conexion = ObtenerConexion()
cursor = conexion.cursor()

cursor.execute("""
    SELECT COUNT(*)
    FROM Acta
    WHERE IdActa = ?
""", (id_acta,))

cantidad = cursor.fetchone()[0]

conexion.close()

Probar(
    "Verificar que el acta no fue eliminada físicamente",
    cantidad == 1
)


# ==========================================
# RESULTADOS FINALES
# ==========================================

print("\n==========================================")
print("           RESULTADOS FINALES")
print("==========================================")

print(f"Pruebas exitosas: {pruebas_exitosas}")
print(f"Pruebas fallidas: {pruebas_fallidas}")

total = pruebas_exitosas + pruebas_fallidas

print(f"Total de pruebas: {total}")

if pruebas_fallidas == 0:
    print("\nTODAS LAS PRUEBAS FUERON EXITOSAS.")
else:
    print("\nHAY PRUEBAS QUE NECESITAN REVISION.")

print("\n==========================================")
print(f"ID de sesión de prueba: {id_sesion}")
print(f"ID de acta de prueba: {id_acta}")
print("La sesión y el acta de prueba permanecen en la BD.")
print("==========================================")
