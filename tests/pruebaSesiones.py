# pruebas_sesiones_agenda.py
from datetime import date, timedelta

from conexion import ObtenerConexion
from sesion import RegistrarSesion, ConsultarSesion, ModificarSesion, EliminarSesion
from agenda import (
    RegistrarAgendaSesion,
    ConsultarAgendaSesion,
    ModificarAgendaSesion,
    EliminarAgendaSesion,
)

# Usuarios de prueba
CORREO_ASISTENTE = "asistente@sgfdu.com"    # rol 4
CORREO_COMITE = "comite@sgfdu.com"          # rol 3
CORREO_ADMIN = "admin@sgfdu.com"            # rol 5
CORREO_ESTUDIANTE = "estudiante@sgfdu.com"  # rol 1

resultados = []


# --------------------------------------------------
# AUXILIARES DE BASE DE DATOS
# --------------------------------------------------

def _consultar_id(sql, params=()):
    conexion = ObtenerConexion()
    cursor = conexion.cursor()
    try:
        cursor.execute(sql, params)
        fila = cursor.fetchone()
        return fila[0] if fila else None
    finally:
        cursor.close()
        conexion.close()


def ObtenerIdUsuario(correo):
    return _consultar_id(
        """
        SELECT id FROM Usuario
        WHERE correo = ? AND estado_id = 1 AND bloqueado = 0
        """,
        (correo,),
    )


def ObtenerIdSolicitud():
    return _consultar_id(
        """
        SELECT TOP 1 IdSolicitud FROM Solicitudes
        WHERE estado_id IN (1, 2)
        ORDER BY IdSolicitud DESC
        """
    )


def ObtenerIdSesion(usuario_id, fecha, hora):
    return _consultar_id(
        """
        SELECT TOP 1 IdSesion FROM Sesion
        WHERE UsuarioCreador = ? AND Fecha = ? AND HoraInicio = ?
        ORDER BY IdSesion DESC
        """,
        (usuario_id, fecha, hora),
    )


def ObtenerIdAgenda(id_sesion, id_solicitud):
    return _consultar_id(
        """
        SELECT IdAgenda FROM AgendaSesion
        WHERE IdSesion = ? AND IdSolicitud = ?
        """,
        (id_sesion, id_solicitud),
    )

def ObtenerIdAgendaTema(id_sesion, tema):
    return _consultar_id(
        """
        SELECT TOP 1 IdAgenda
        FROM AgendaSesion
        WHERE IdSesion = ? AND Tema = ?
        ORDER BY IdAgenda DESC
        """,
        (id_sesion, tema),
    )
# --------------------------------------------------
# REGISTRO DE RESULTADOS
# --------------------------------------------------

def Verificar(nombre, resultado, esperado=True):
    exito, mensaje = resultado
    correcto = exito == esperado
    resultados.append((nombre, correcto))

    print(f"\n{nombre}")
    print(f"Resultado: {mensaje}")
    print("PRUEBA CORRECTA" if correcto else "PRUEBA FALLIDA")


# --------------------------------------------------
# PREPARACIÓN
# --------------------------------------------------

def Preparar():
    """Obtiene los datos necesarios. Devuelve None si falta alguno."""
    ctx = {
        "asistente": ObtenerIdUsuario(CORREO_ASISTENTE),
        "comite": ObtenerIdUsuario(CORREO_COMITE),
        "admin": ObtenerIdUsuario(CORREO_ADMIN),
        "estudiante": ObtenerIdUsuario(CORREO_ESTUDIANTE),
        "solicitud": ObtenerIdSolicitud(),
        "fecha": (date.today() + timedelta(days=7)).isoformat(),
    }

    faltantes = [clave for clave, valor in ctx.items() if not valor]
    if faltantes:
        print(f"No se encontraron los datos necesarios: {faltantes}")
        return None

    return ctx


# --------------------------------------------------
# PRUEBAS DE SESIÓN
# --------------------------------------------------

def PruebasSesion(ctx):
    print("\n===================================")
    print("PRUEBAS DEL MODULO DE SESIONES")
    print("===================================")

    fecha = ctx["fecha"]

    # Registro por asistente (paso base para el resto)
    resultado = RegistrarSesion(
        usuario_id=ctx["asistente"],
        fecha=fecha,
        hora_inicio="09:00",
        hora_fin="10:00",
        participantes=[ctx["comite"]],
    )
    Verificar("Registrar sesión por asistente", resultado)

    id_sesion = ObtenerIdSesion(ctx["asistente"], fecha, "09:00")
    if not id_sesion:
        print("No se pudo recuperar la sesión registrada. Se detienen las pruebas de sesión.")
        return None
    ctx["id_sesion"] = id_sesion

    Verificar(
        "Permisos: administrador no puede registrar sesión",
        RegistrarSesion(ctx["admin"], fecha, "11:00", [ctx["comite"]]),
        esperado=False,
    )

    Verificar(
        "Consultar sesión por comité",
        ConsultarSesion(usuario_id=ctx["comite"], id_sesion=id_sesion),
    )

    Verificar(
        "Permisos: estudiante no puede consultar sesión",
        ConsultarSesion(ctx["estudiante"], id_sesion),
        esperado=False,
    )

    cambios = {
        "Fecha": (date.today() + timedelta(days=8)).isoformat(),
        "HoraInicio": "10:00",
        "HoraFin": "11:00",
        "Estado": "PROGRAMADA",
    }
    Verificar(
        "Modificar sesión por asistente",
        ModificarSesion(id_sesion, cambios, ctx["asistente"]),
    )

    return id_sesion


# --------------------------------------------------
# PRUEBAS DE AGENDA
# --------------------------------------------------

def PruebasAgenda(ctx):
    print("\n===================================")
    print("PRUEBAS DEL MODULO DE AGENDA")
    print("===================================")

    id_sesion = ctx["id_sesion"]
    id_solicitud = ctx["solicitud"]

    Verificar(
        "Registrar punto de agenda por asistente",
        RegistrarAgendaSesion(
            id_sesion=id_sesion,
            id_solicitud=id_solicitud,
            orden=1,
            usuario_id=ctx["asistente"],
            observaciones="Revisión de solicitud.",
        ),
    )

    id_agenda = ObtenerIdAgenda(id_sesion, id_solicitud)
    if not id_agenda:
        print("No se pudo recuperar el punto de agenda. Se detienen las pruebas de agenda.")
        return

    Verificar(
        "Permisos: estudiante no puede registrar agenda",
        RegistrarAgendaSesion(
            id_sesion=id_sesion,
            id_solicitud=id_solicitud,
            orden=2,
            usuario_id=ctx["estudiante"],
        ),
        esperado=False,
    )

    Verificar(
        "Consultar agenda por comité",
        ConsultarAgendaSesion(id_sesion, ctx["comite"]),
    )

        # Registrar un punto de agenda de tipo tema general.
    tema_original = "Revisión de acuerdos anteriores"

    Verificar(
        "Registrar punto de agenda general",
        RegistrarAgendaSesion(
            id_sesion=id_sesion,
            id_solicitud=None,
            orden=2,
            usuario_id=ctx["asistente"],
            tema=tema_original,
            observaciones="Tema pendiente de revisión."
        ),
    )

    id_agenda_tema = ObtenerIdAgendaTema(id_sesion, tema_original)

    if not id_agenda_tema:
        print("No se pudo recuperar el punto de agenda general.")
        return

    # Modificar tema, orden y observaciones.
    cambios_tema = {
        "Tema": "Revisión de acuerdos y nuevos compromisos",
        "Orden": 3,
        "Observaciones": "Se revisarán los acuerdos y compromisos pendientes."
    }

    Verificar(
        "Modificar tema, orden y observaciones del punto general",
        ModificarAgendaSesion(
            id_agenda_tema,
            cambios_tema,
            ctx["admin"]
        ),
    )

    # Consultar nuevamente para comprobar los cambios.
    Verificar(
        "Consultar agenda después de modificar el tema",
        ConsultarAgendaSesion(id_sesion, ctx["comite"]),
    )

    Verificar(
        "Permisos: estudiante no puede consultar agenda",
        ConsultarAgendaSesion(id_sesion, ctx["estudiante"]),
        esperado=False,
    )

    cambios = {
        "IdSolicitud": id_solicitud,
        "Orden": 2,
        "Observaciones": "Solicitud revisada y actualizada.",
    }
    Verificar(
        "Modificar punto de agenda por administrativo",
        ModificarAgendaSesion(id_agenda, cambios, ctx["admin"]),
    )

    Verificar(
        "Permisos: estudiante no puede modificar agenda",
        ModificarAgendaSesion(id_agenda, {"Orden": 3}, ctx["estudiante"]),
        esperado=False,
    )

    Verificar(
        "Cancelar punto de agenda por administrativo",
        EliminarAgendaSesion(id_agenda, ctx["admin"]),
    )

    Verificar(
        "Cancelar punto de agenda por segunda vez (debe fallar)",
        EliminarAgendaSesion(id_agenda, ctx["admin"]),
        esperado=False,
    )


# --------------------------------------------------
# CANCELACIÓN DE SESIÓN (va al final)
# --------------------------------------------------

def PruebasCancelarSesion(ctx):
    print("\n===================================")
    print("PRUEBAS DE CANCELACIÓN DE SESIÓN")
    print("===================================")

    id_sesion = ctx["id_sesion"]

    Verificar(
        "Cancelar sesión por asistente",
        EliminarSesion(id_sesion, ctx["asistente"]),
    )

    Verificar(
        "Cancelar sesión por segunda vez (debe fallar)",
        EliminarSesion(id_sesion, ctx["asistente"]),
        esperado=False,
    )


# --------------------------------------------------
# EJECUCIÓN
# --------------------------------------------------

def Main():
    ctx = Preparar()
    if ctx is None:
        return

    if PruebasSesion(ctx) is not None:
        PruebasAgenda(ctx)
        PruebasCancelarSesion(ctx)

    print("\n===================================")
    print("RESUMEN")
    print("===================================")
    correctas = sum(1 for _, ok in resultados if ok)
    for nombre, ok in resultados:
        print(f"{'OK    ' if ok else 'FALLA '} {nombre}")
    print(f"\n{correctas} de {len(resultados)} pruebas correctas")


if __name__ == "__main__":
    Main()