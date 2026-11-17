
from conexion import ObtenerConexion
from solicitudes import (
    ModificarSolicitud,
    EliminarSolicitud,
    BuscarSolicitudes
)


CORREO_ESTUDIANTE = "estudiante@sgfdu.com"
CORREO_ADMIN = "admin@sgfdu.com"


# Revisar las solicitudes almacenadas en SQL Server
def revisar_solicitudes_bd():

    conexion = ObtenerConexion()
    cursor = conexion.cursor()

    try:
        cursor.execute("""
            SELECT
                IdSolicitud,
                usuario_id,
                NombreSolicitante,
                CorreoElectronico,
                estado_id
            FROM Solicitudes
            ORDER BY IdSolicitud DESC
        """)

        solicitudes = cursor.fetchall()

        print("\n========== SOLICITUDES EN SQL SERVER ==========")

        if not solicitudes:
            print("La tabla Solicitudes está vacía.")
            return

        for s in solicitudes:
            print(
                f"ID: {s.IdSolicitud} | "
                f"Usuario ID: {s.usuario_id} | "
                f"Nombre: {s.NombreSolicitante} | "
                f"Correo: {s.CorreoElectronico} | "
                f"Estado: {s.estado_id}"
            )

    finally:
        cursor.close()
        conexion.close()


# Obtener solicitudes de un usuario mediante su correo
def obtener_solicitud(correo):

    conexion = ObtenerConexion()
    cursor = conexion.cursor()

    try:
        cursor.execute("""
            SELECT IdSolicitud
            FROM Solicitudes
            WHERE CorreoElectronico = ?
              AND estado_id <> 3
            ORDER BY IdSolicitud DESC
        """, (correo,))

        fila = cursor.fetchone()

        if fila is None:
            print(f"No hay solicitudes activas para {correo}.")
            return None

        id_solicitud = fila[0]

    finally:
        cursor.close()
        conexion.close()

    # Buscar el detalle utilizando la función del módulo
    resultado, respuesta = BuscarSolicitudes(
        str(id_solicitud),
        CORREO_ADMIN
    )

    if not resultado:
        print("\nError en la búsqueda:", respuesta)
        return None

    return respuesta[0]


# PRUEBAS MODIFICAR
def probar_modificar():

    print("\n========== PRUEBAS MODIFICAR SOLICITUD ==========")

    solicitud = obtener_solicitud(CORREO_ESTUDIANTE)

    if solicitud is None:
        print("No se encontró una solicitud del estudiante.")
        return

    usuario_id = solicitud["usuario_id"]
    id_solicitud = solicitud["IdSolicitud"]

    # TEST 1 - Modificar nombre de actividad
    print("\nTEST 1 - Modificar actividad")

    print(ModificarSolicitud(
        id_solicitud,
        usuario_id,
        {"NombreActividad": "Actividad modificada"},
        CORREO_ESTUDIANTE
    ))

    # TEST 2 - Modificar justificación
    print("\nTEST 2 - Modificar justificación")

    print(ModificarSolicitud(
        id_solicitud,
        usuario_id,
        {"Justificacion": "Justificación actualizada para la prueba."},
        CORREO_ESTUDIANTE
    ))

    # TEST 3 - Modificar varios campos
    print("\nTEST 3 - Modificar varios campos")

    print(ModificarSolicitud(
        id_solicitud,
        usuario_id,
        {
            "NombreActividad": "Actividad actualizada",
            "InformacionBancaria": "Banco Nacional - Cuenta actualizada"
        },
        CORREO_ESTUDIANTE
    ))

    # TEST 4 - Intentar modificar sin cambios
    print("\nTEST 4 - Sin campos para modificar")

    print(ModificarSolicitud(
        id_solicitud,
        usuario_id,
        {},
        CORREO_ESTUDIANTE
    ))

    # TEST 5 - Intentar modificar un campo no permitido
    print("\nTEST 5 - Campo no editable")

    print(ModificarSolicitud(
        id_solicitud,
        usuario_id,
        {"estado_id": 3},
        CORREO_ESTUDIANTE
    ))

    # TEST 6 - Intentar modificar una solicitud ajena
    print("\nTEST 6 - Usuario sin permisos")

    print(ModificarSolicitud(
        id_solicitud,
        999,
        {"NombreActividad": "Cambio no autorizado"},
        CORREO_ESTUDIANTE
    ))

    # TEST 7 - Intentar registrar un monto negativo
    print("\nTEST 7 - Monto inválido")

    print(ModificarSolicitud(
        id_solicitud,
        usuario_id,
        {"MontoSolicitado": -5000},
        CORREO_ESTUDIANTE
    ))


# PRUEBAS ELIMINAR
def probar_eliminar():

    print("\n========== PRUEBAS ELIMINAR SOLICITUD ==========")

    solicitud = obtener_solicitud(CORREO_ADMIN)

    if solicitud is None:
        print("No se encontró una solicitud del administrador.")
        return

    id_solicitud = solicitud["IdSolicitud"]
    usuario_id = solicitud["usuario_id"]

    # TEST 1 - Eliminar solicitud propia
    print("\nTEST 1 - Eliminar solicitud propia")

    print(EliminarSolicitud(
        id_solicitud,
        usuario_id,
        CORREO_ADMIN
    ))

    # TEST 2 - Intentar eliminarla nuevamente
    print("\nTEST 2 - Eliminar solicitud ya eliminada")

    print(EliminarSolicitud(
        id_solicitud,
        usuario_id,
        CORREO_ADMIN
    ))

    # TEST 3 - Usuario sin permisos
    print("\nTEST 3 - Intentar eliminar solicitud ajena")

    solicitud_estudiante = obtener_solicitud(CORREO_ESTUDIANTE)

    if solicitud_estudiante:

        print(EliminarSolicitud(
            solicitud_estudiante["IdSolicitud"],
            999,
            CORREO_ESTUDIANTE
        ))


if __name__ == "__main__":

    revisar_solicitudes_bd()

    probar_modificar()
    probar_eliminar()
