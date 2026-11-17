
from datetime import date, timedelta
from decimal import Decimal

from conexion import ObtenerConexion

from sesion import RegistrarSesion

from evaluacion import (
    RegistrarEvaluacion,
    ConsultarEvaluacion,
    SolicitarInformacionAdicional,
    ModificarEvaluacion,
    EliminarEvaluacion
)

from preparacion_evaluacion import PrepararDatos
# --------------------------------------------------
# USUARIOS DE PRUEBA
# --------------------------------------------------

CORREO_ASISTENTE = "asistente@sgfdu.com"
CORREO_COMITE = "comite@sgfdu.com"
CORREO_ADMIN = "admin@sgfdu.com"
CORREO_ESTUDIANTE = "estudiante@sgfdu.com"

resultados = []


# --------------------------------------------------
# AUXILIARES DE BASE DE DATOS
# --------------------------------------------------

def ConsultarSQL(sql, parametros=()):

    conexion = ObtenerConexion()
    cursor = conexion.cursor()

    try:
        cursor.execute(sql, parametros)
        return cursor.fetchall()

    finally:
        cursor.close()
        conexion.close()


def ConsultarUno(sql, parametros=()):

    filas = ConsultarSQL(sql, parametros)

    return filas[0][0] if filas else None


def ObtenerIdUsuario(correo):

    return ConsultarUno("""
        SELECT id
        FROM Usuario
        WHERE correo = ?
          AND estado_id = 1
          AND bloqueado = 0
    """, (correo,))


def ObtenerSolicitudesPrueba():

    return ConsultarSQL("""
        SELECT TOP 3
            S.IdSolicitud,
            S.MontoSolicitado,
            L.MontoMaximo

        FROM Solicitudes S

        INNER JOIN LineaAccion L
            ON S.LineaAccion = L.IdLineaAccion

        WHERE S.estado_id IN (1, 2)
          AND S.MontoSolicitado > 0
          AND L.MontoMaximo > 0

        ORDER BY S.IdSolicitud DESC
    """)


def ObtenerIdSesion(usuario_id, fecha, hora):

    return ConsultarUno("""
        SELECT TOP 1 IdSesion
        FROM Sesion
        WHERE UsuarioCreador = ?
          AND Fecha = ?
          AND HoraInicio = ?
        ORDER BY IdSesion DESC
    """, (usuario_id, fecha, hora))


def ObtenerIdEvaluacion(id_sesion, id_solicitud):

    return ConsultarUno("""
        SELECT TOP 1 IdEvaluacion
        FROM Evaluacion
        WHERE IdSesion = ?
          AND IdSolicitud = ?
        ORDER BY IdEvaluacion DESC
    """, (id_sesion, id_solicitud))


# --------------------------------------------------
# REGISTRO DE RESULTADOS
# --------------------------------------------------

def Verificar(nombre, resultado, esperado=True):

    exito, mensaje = resultado

    correcto = exito == esperado

    resultados.append((nombre, correcto))

    print(f"\n{nombre}")
    print(f"Resultado: {mensaje}")

    print(
        "PRUEBA CORRECTA"
        if correcto
        else "PRUEBA FALLIDA"
    )


# --------------------------------------------------
# PREPARACIÓN
# --------------------------------------------------

def Preparar():

    ctx = {
        "asistente": ObtenerIdUsuario(CORREO_ASISTENTE),
        "comite": ObtenerIdUsuario(CORREO_COMITE),
        "admin": ObtenerIdUsuario(CORREO_ADMIN),
        "estudiante": ObtenerIdUsuario(CORREO_ESTUDIANTE),
    }

    solicitudes = ObtenerSolicitudesPrueba()

    if len(solicitudes) < 3:
        print("Se necesitan al menos 3 solicitudes activas con montos válidos.")
        return None

    faltantes = [
        clave
        for clave, valor in ctx.items()
        if not valor
    ]

    if faltantes:
        print(f"No se encontraron los usuarios: {faltantes}")
        return None

    # Guardar las tres solicitudes de prueba.
    ctx["solicitudes"] = solicitudes

    # Calcular un monto válido para la aprobación.
    for i, solicitud in enumerate(solicitudes):

        id_solicitud = solicitud[0]
        monto_solicitado = Decimal(str(solicitud[1]))
        monto_maximo = Decimal(str(solicitud[2]))

        monto_valido = min(monto_solicitado, monto_maximo)

        ctx[f"solicitud{i + 1}"] = id_solicitud
        ctx[f"monto{i + 1}"] = monto_valido

    ctx["fecha"] = (
        date.today() + timedelta(days=15)
    ).isoformat()

    return ctx


# --------------------------------------------------
# CREAR SESIÓN DE PRUEBA
# --------------------------------------------------

def PrepararSesion(ctx):

    print("\n===================================")
    print("PREPARACIÓN DE SESIÓN")
    print("===================================")

    resultado = RegistrarSesion(
        usuario_id=ctx["asistente"],
        fecha=ctx["fecha"],
        hora_inicio="09:00",
        hora_fin="10:00",
        participantes=[ctx["comite"]]
    )

    Verificar("Registrar sesión para evaluaciones", resultado)

    id_sesion = ObtenerIdSesion(
        ctx["asistente"],
        ctx["fecha"],
        "09:00"
    )

    if not id_sesion:
        print("No se pudo recuperar la sesión.")
        return False

    ctx["id_sesion"] = id_sesion

    return True


# --------------------------------------------------
# PRUEBAS DE REGISTRO
# --------------------------------------------------

def PruebasRegistro(ctx):

    print("\n===================================")
    print("PRUEBAS DE REGISTRO")
    print("===================================")

    id_sesion = ctx["id_sesion"]

    # 1. Registrar evaluación aprobada.
    Verificar(
        "Registrar evaluación APROBADA",
        RegistrarEvaluacion(
            id_sesion=id_sesion,
            id_solicitud=ctx["solicitud1"],
            decision="APROBADA",
            usuario_id=ctx["comite"],
            monto_aprobado=ctx["monto1"],
            observaciones="Solicitud aprobada para pruebas."
        )
    )

    ctx["evaluacion1"] = ObtenerIdEvaluacion(
        id_sesion,
        ctx["solicitud1"]
    )

    if not ctx["evaluacion1"]:
        print("No se pudo recuperar la primera evaluación.")
        return False

    # 2. Evitar evaluación duplicada.
    Verificar(
        "Registrar evaluación duplicada",
        RegistrarEvaluacion(
            id_sesion,
            ctx["solicitud1"],
            "APROBADA",
            ctx["comite"],
            ctx["monto1"]
        ),
        esperado=False
    )

    # 3. Registrar una evaluación rechazada.
    Verificar(
        "Registrar evaluación RECHAZADA",
        RegistrarEvaluacion(
            id_sesion,
            ctx["solicitud3"],
            "RECHAZADA",
            ctx["admin"],
            observaciones="Solicitud rechazada para pruebas."
        )
    )

    ctx["evaluacion3"] = ObtenerIdEvaluacion(
        id_sesion,
        ctx["solicitud3"]
    )

    # 4. Monto superior al solicitado.
    Verificar(
        "Rechazar monto superior al solicitado",
        RegistrarEvaluacion(
            id_sesion,
            ctx["solicitud2"],
            "APROBADA",
            ctx["comite"],
            ctx["monto2"] + Decimal("1.00")
        ),
        esperado=False
    )

    # 5. Decisión inválida.
    Verificar(
        "Rechazar decisión inválida",
        RegistrarEvaluacion(
            id_sesion,
            ctx["solicitud2"],
            "PENDIENTE",
            ctx["comite"]
        ),
        esperado=False
    )

    # 6. Estudiante no puede registrar evaluaciones.
    Verificar(
        "Permisos: estudiante no puede registrar evaluación",
        RegistrarEvaluacion(
            id_sesion,
            ctx["solicitud2"],
            "RECHAZADA",
            ctx["estudiante"]
        ),
        esperado=False
    )

    return True


# --------------------------------------------------
# PRUEBAS DE CONSULTA
# --------------------------------------------------

def PruebasConsulta(ctx):

    print("\n===================================")
    print("PRUEBAS DE CONSULTA")
    print("===================================")

    # Consultar todas las evaluaciones.
    Verificar(
        "Consultar todas las evaluaciones por comité",
        ConsultarEvaluacion(
            usuario_id=ctx["comite"]
        )
    )

    # Consultar una evaluación específica.
    Verificar(
        "Consultar evaluación específica",
        ConsultarEvaluacion(
            usuario_id=ctx["admin"],
            id_evaluacion=ctx["evaluacion1"]
        )
    )

    # Consultar evaluación inexistente.
    Verificar(
        "Consultar evaluación inexistente",
        ConsultarEvaluacion(
            usuario_id=ctx["comite"],
            id_evaluacion=999999
        ),
        esperado=False
    )

    # Estudiante sin permisos.
    Verificar(
        "Permisos: estudiante no puede consultar evaluaciones",
        ConsultarEvaluacion(
            usuario_id=ctx["estudiante"]
        ),
        esperado=False
    )


# --------------------------------------------------
# PRUEBAS DE INFORMACIÓN ADICIONAL
# --------------------------------------------------

def PruebasInformacionAdicional(ctx):

    print("\n===================================")
    print("PRUEBAS DE INFORMACIÓN ADICIONAL")
    print("===================================")

    id_sesion = ctx["id_sesion"]

    # 1. Solicitar información adicional.
    Verificar(
        "Solicitar información adicional",
        SolicitarInformacionAdicional(
            id_sesion=id_sesion,
            id_solicitud=ctx["solicitud2"],
            observaciones="Se requiere ampliar la justificación del presupuesto.",
            usuario_id=ctx["comite"]
        )
    )

    ctx["evaluacion2"] = ObtenerIdEvaluacion(
        id_sesion,
        ctx["solicitud2"]
    )

    # 2. Verificar que no se duplique.
    Verificar(
        "Solicitar información adicional por segunda vez",
        SolicitarInformacionAdicional(
            id_sesion,
            ctx["solicitud2"],
            "Segunda solicitud de información.",
            ctx["comite"]
        ),
        esperado=False
    )

    # 3. Verificar permisos.
    Verificar(
        "Permisos: estudiante no puede solicitar información",
        SolicitarInformacionAdicional(
            id_sesion,
            ctx["solicitud3"],
            "Información adicional de prueba.",
            ctx["estudiante"]
        ),
        esperado=False
    )

    # 4. Verificar que el estado de la solicitud cambió.
    estado = ConsultarUno("""
        SELECT estado_id
        FROM Solicitudes
        WHERE IdSolicitud = ?
    """, (ctx["solicitud2"],))

    Verificar(
        "Verificar estado INFO_ADICIONAL de la solicitud",
        (
            estado == 2,
            f"Estado actual de la solicitud: {estado}"
        )
    )


# --------------------------------------------------
# PRUEBAS DE MODIFICACIÓN
# --------------------------------------------------

def PruebasModificacion(ctx):

    print("\n===================================")
    print("PRUEBAS DE MODIFICACIÓN")
    print("===================================")

    id_evaluacion = ctx["evaluacion1"]

    # 1. Cambiar decisión a RECHAZADA.
    Verificar(
        "Modificar decisión a RECHAZADA",
        ModificarEvaluacion(
            id_evaluacion,
            {
                "Decision": "RECHAZADA",
                "Observaciones": "Decisión modificada durante las pruebas."
            },
            ctx["admin"]
        )
    )

    # 2. Cambiar nuevamente a APROBADA.
    Verificar(
        "Modificar decisión a APROBADA",
        ModificarEvaluacion(
            id_evaluacion,
            {
                "Decision": "APROBADA",
                "MontoAprobado": ctx["monto1"],
                "Observaciones": "Solicitud aprobada después de revisión."
            },
            ctx["comite"]
        )
    )

    # 3. Modificar una evaluación de información adicional.
    Verificar(
        "Modificar evaluación de información adicional",
        ModificarEvaluacion(
            ctx["evaluacion2"],
            {
                "Decision": "RECHAZADA",
                "Observaciones": "La información recibida no cumple los requisitos."
            },
            ctx["admin"]
        )
    )

    # 4. Intentar modificar con un monto superior.
    Verificar(
        "Rechazar modificación con monto superior al solicitado",
        ModificarEvaluacion(
            id_evaluacion,
            {
                "MontoAprobado": ctx["monto1"] + Decimal("1.00")
            },
            ctx["admin"]
        ),
        esperado=False
    )

    # 5. Intentar modificar con un campo no permitido.
    Verificar(
        "Rechazar modificación de campo no permitido",
        ModificarEvaluacion(
            id_evaluacion,
            {
                "IdSolicitud": 999
            },
            ctx["admin"]
        ),
        esperado=False
    )

    # 6. Estudiante no puede modificar.
    Verificar(
        "Permisos: estudiante no puede modificar evaluaciones",
        ModificarEvaluacion(
            id_evaluacion,
            {"Observaciones": "Cambio no autorizado."},
            ctx["estudiante"]
        ),
        esperado=False
    )


# --------------------------------------------------
# PRUEBAS DE ELIMINACIÓN
# --------------------------------------------------

def PruebasEliminacion(ctx):

    print("\n===================================")
    print("PRUEBAS DE ELIMINACIÓN")
    print("===================================")

    id_evaluacion = ctx["evaluacion3"]

    # 1. Cancelar evaluación.
    Verificar(
        "Cancelar evaluación",
        EliminarEvaluacion(
            id_evaluacion,
            ctx["admin"]
        )
    )

    # 2. Cancelar nuevamente.
    Verificar(
        "Cancelar evaluación por segunda vez",
        EliminarEvaluacion(
            id_evaluacion,
            ctx["admin"]
        ),
        esperado=False
    )

    # 3. Estudiante no puede cancelar.
    Verificar(
        "Permisos: estudiante no puede cancelar evaluaciones",
        EliminarEvaluacion(
            ctx["evaluacion1"],
            ctx["estudiante"]
        ),
        esperado=False
    )

    # 4. Comprobar eliminación lógica.
    estado = ConsultarUno("""
        SELECT EstadoEvaluacion
        FROM Evaluacion
        WHERE IdEvaluacion = ?
    """, (id_evaluacion,))

    Verificar(
        "Verificar estado CANCELADA",
        (
            estado == "CANCELADA",
            f"Estado actual de la evaluación: {estado}"
        )
    )


# --------------------------------------------------
# RESUMEN
# --------------------------------------------------

def Main():

    print("\n===================================")
    print("PRUEBAS DEL MÓDULO DE EVALUACIÓN")
    print("===================================")

    try:
        ctx = PrepararDatos()

    except Exception as error:
        print(f"Error preparando los datos: {error}")
        return

    # Adaptar los datos para las funciones de prueba.
    ctx["solicitud1"] = ctx["solicitudes"][0]
    ctx["solicitud2"] = ctx["solicitudes"][1]
    ctx["solicitud3"] = ctx["solicitudes"][2]

    # Los montos de prueba son de ₡50.000.
    ctx["monto1"] = Decimal("50000.00")
    ctx["monto2"] = Decimal("50000.00")
    ctx["monto3"] = Decimal("50000.00")

    PrepararSesion = True

    ctx["evaluacion1"] = None
    ctx["evaluacion2"] = None
    ctx["evaluacion3"] = None

    # Ejecutar las pruebas.
    if PruebasRegistro(ctx):
        PruebasConsulta(ctx)
        PruebasInformacionAdicional(ctx)
        PruebasModificacion(ctx)
        PruebasEliminacion(ctx)

    print("\n===================================")
    print("RESUMEN DE PRUEBAS")
    print("===================================")

    correctas = sum(1 for _, ok in resultados if ok)

    for nombre, ok in resultados:
        print(f"{'OK    ' if ok else 'FALLA '} {nombre}")

    print(f"\n{correctas} de {len(resultados)} pruebas correctas")


if __name__ == "__main__":
    Main()