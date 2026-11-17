
from datetime import date, timedelta
from decimal import Decimal

from conexion import ObtenerConexion
from sesion import RegistrarSesion
from agenda import RegistrarAgendaSesion


# --------------------------------------------------
# USUARIOS
# --------------------------------------------------

CORREO_ASISTENTE = "asistente@sgfdu.com"
CORREO_COMITE = "comite@sgfdu.com"
CORREO_ADMIN = "admin@sgfdu.com"
CORREO_ESTUDIANTE = "estudiante@sgfdu.com"


def ObtenerIdUsuario(correo):

    conexion = ObtenerConexion()
    cursor = conexion.cursor()

    try:
        cursor.execute("""
            SELECT id
            FROM Usuario
            WHERE correo = ?
              AND estado_id = 1
              AND bloqueado = 0
        """, (correo,))

        fila = cursor.fetchone()

        return fila[0] if fila else None

    finally:
        cursor.close()
        conexion.close()


# --------------------------------------------------
# CREAR LÍNEA DE ACCIÓN
# --------------------------------------------------

def CrearLineaAccion():

    conexion = ObtenerConexion()
    cursor = conexion.cursor()

    try:

        cursor.execute("""
            SELECT TOP 1 IdLineaAccion
            FROM LineaAccion
            WHERE Estado = 'ACTIVA'
            ORDER BY IdLineaAccion
        """)

        fila = cursor.fetchone()

        if fila:
            return fila[0]

        cursor.execute("""
            INSERT INTO LineaAccion (
                TextoLinea,
                MontoMaximo,
                Porcentaje,
                Estado,
                FechaModificacion
            )
            OUTPUT INSERTED.IdLineaAccion
            VALUES (?, ?, ?, ?, SYSDATETIME())
        """, (
            "Línea de acción para pruebas",
            Decimal("1000000.00"),
            Decimal("100.00"),
            "ACTIVA"
        ))

        id_linea = cursor.fetchone()[0]

        conexion.commit()

        print(f"Línea de acción creada: {id_linea}")

        return id_linea

    except Exception:
        conexion.rollback()
        raise

    finally:
        cursor.close()
        conexion.close()


# --------------------------------------------------
# CREAR SOLICITUDES
# --------------------------------------------------

def CrearSolicitudes(usuario_id, linea_id):

    conexion = ObtenerConexion()
    cursor = conexion.cursor()

    solicitudes = []

    try:

        for numero in range(1, 4):

            cursor.execute("""
                INSERT INTO Solicitudes (
                    usuario_id,
                    NombreSolicitante,
                    Carne,
                    CorreoElectronico,
                    NumeroCelular,
                    rol_id,
                    MontoSolicitado,
                    InformacionBancaria,
                    NombreActividad,
                    Justificacion,
                    LineaAccion,
                    estado_id,
                    observaciones,
                    fecha_creacion
                )
                OUTPUT INSERTED.IdSolicitud
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, NULL, SYSDATETIME())
            """, (
                usuario_id,
                f"Solicitante Prueba {numero}",
                f"202600000{numero}",
                f"solicitante{numero}@pruebas.com",
                "88888888",
                1,
                Decimal("50000.00"),
                "Cuenta bancaria de prueba",
                f"Actividad de evaluación {numero}",
                "Justificación creada automáticamente para probar el módulo de evaluación.",
                linea_id
            ))

            id_solicitud = cursor.fetchone()[0]

            solicitudes.append(id_solicitud)

        conexion.commit()

        print(f"Solicitudes creadas: {solicitudes}")

        return solicitudes

    except Exception:
        conexion.rollback()
        raise

    finally:
        cursor.close()
        conexion.close()


# --------------------------------------------------
# CREAR SESIÓN Y AGENDA
# --------------------------------------------------

def CrearSesionYAgenda(asistente_id, comite_id, solicitudes):

    fecha = (date.today() + timedelta(days=20)).isoformat()

    resultado = RegistrarSesion(
        usuario_id=asistente_id,
        fecha=fecha,
        hora_inicio="09:00",
        hora_fin="10:00",
        participantes=[comite_id]
    )

    if not resultado[0]:
        raise Exception(resultado[1])

    conexion = ObtenerConexion()
    cursor = conexion.cursor()

    try:

        cursor.execute("""
            SELECT TOP 1 IdSesion
            FROM Sesion
            WHERE UsuarioCreador = ?
              AND Fecha = ?
              AND HoraInicio = '09:00'
            ORDER BY IdSesion DESC
        """, (asistente_id, fecha))

        fila = cursor.fetchone()

        if not fila:
            raise Exception("No se pudo recuperar la sesión creada.")

        id_sesion = fila[0]

    finally:
        cursor.close()
        conexion.close()

    # Agregar las tres solicitudes a la agenda.
    for orden, id_solicitud in enumerate(solicitudes, start=1):

        resultado = RegistrarAgendaSesion(
            id_sesion=id_sesion,
            id_solicitud=id_solicitud,
            orden=orden,
            usuario_id=asistente_id,
            observaciones=f"Solicitud de prueba número {orden}."
        )

        if not resultado[0]:
            raise Exception(resultado[1])

    # Agregar un tema general.
    resultado = RegistrarAgendaSesion(
        id_sesion=id_sesion,
        id_solicitud=None,
        orden=4,
        usuario_id=asistente_id,
        tema="Asuntos generales de la sesión",
        observaciones="Tema general para pruebas."
    )

    if not resultado[0]:
        raise Exception(resultado[1])

    print(f"Sesión creada: {id_sesion}")
    print("Agenda creada con 3 solicitudes y 1 tema general.")

    return id_sesion


# --------------------------------------------------
# PREPARACIÓN COMPLETA
# --------------------------------------------------

def PrepararDatos():

    asistente = ObtenerIdUsuario(CORREO_ASISTENTE)
    comite = ObtenerIdUsuario(CORREO_COMITE)
    admin = ObtenerIdUsuario(CORREO_ADMIN)
    estudiante = ObtenerIdUsuario(CORREO_ESTUDIANTE)

    usuarios = {
        "asistente": asistente,
        "comite": comite,
        "admin": admin,
        "estudiante": estudiante
    }

    faltantes = [
        nombre
        for nombre, usuario in usuarios.items()
        if usuario is None
    ]

    if faltantes:
        raise Exception(f"Faltan usuarios de prueba: {faltantes}")

    linea_id = CrearLineaAccion()

    solicitudes = CrearSolicitudes(
        estudiante,
        linea_id
    )

    id_sesion = CrearSesionYAgenda(
        asistente,
        comite,
        solicitudes
    )

    return {
        **usuarios,
        "linea": linea_id,
        "solicitudes": solicitudes,
        "id_sesion": id_sesion
    }


if __name__ == "__main__":

    try:

        datos = PrepararDatos()

        print("\n===================================")
        print("DATOS DE PRUEBA PREPARADOS")
        print("===================================")

        for clave, valor in datos.items():
            print(f"{clave}: {valor}")

    except Exception as error:

        print(f"\nERROR AL PREPARAR LOS DATOS: {error}")
