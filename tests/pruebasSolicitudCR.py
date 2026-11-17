
from conexion import ObtenerConexion
from solicitudes import CrearSolicitud, BuscarSolicitudes


CORREO_ADMIN = "admin@sgfdu.com"


# Obtener una línea de acción válida para la prueba
def ObtenerLineaAccion():
    conexion = ObtenerConexion()
    cursor = conexion.cursor()

    try:
        cursor.execute(
            """
            SELECT TOP 1 IdLineaAccion
            FROM LineaAccion
            WHERE MontoMaximo >= 50000
            AND Estado = 'ACTIVA'
            ORDER BY IdLineaAccion
            """
        )

        fila = cursor.fetchone()
        return fila[0] if fila else None

    finally:
        cursor.close()
        conexion.close()


# Ejecutar una prueba de creación
def ProbarCrearSolicitud(usuario_id, descripcion):
    print(f"\n========== {descripcion} ==========")

    linea_accion = ObtenerLineaAccion()

    if linea_accion is None:
        print("No existe una línea de acción que permita solicitar 50000.")
        return

    resultado, mensaje = CrearSolicitud(
        usuario_id=usuario_id,
        monto=50000,
        informacion_bancaria="Banco Nacional - Cuenta de prueba",
        nombre_actividad="Actividad de prueba",
        justificacion="Solicitud creada para verificar el funcionamiento del sistema.",
        linea_accion=linea_accion
    )

    print("Resultado:", resultado)
    print("Mensaje:", mensaje)


# Obtener el ID de un usuario de prueba
def ObtenerIdUsuario(correo):
    conexion = ObtenerConexion()
    cursor = conexion.cursor()

    try:
        cursor.execute(
            """
            SELECT id
            FROM Usuario
            WHERE correo = ?
              AND estado_id = 1
              AND bloqueado = 0
            """,
            (correo,)
        )

        fila = cursor.fetchone()
        return fila[0] if fila else None

    finally:
        cursor.close()
        conexion.close()


# Mostrar resultados de búsqueda
def mostrar_resultados(resultado, mensaje):
    print("Resultado:", resultado)

    if not resultado:
        print("Mensaje:", mensaje)
        return None

    print("Solicitudes encontradas:")

    for solicitud in mensaje:
        print(
            f"ID: {solicitud['IdSolicitud']} | "
            f"Solicitante: {solicitud['NombreSolicitante']} | "
            f"Estado: {solicitud['estado']}"
        )

    return mensaje


# TEST 1 - Buscar solicitud de estudiante
def probar_buscar_estudiante():
    print("\n========== TEST 1 - Buscar estudiante ==========")

    resultado, mensaje = BuscarSolicitudes(
        "Graduado Prueba",
        CORREO_ADMIN
    )

    return mostrar_resultados(resultado, mensaje)


# TEST 2 - Buscar solicitud de graduado
def probar_buscar_graduado():
    print("\n========== TEST 2 - Buscar graduado ==========")

    resultado, mensaje = BuscarSolicitudes(
        "Graduado Prueba",
        CORREO_ADMIN
    )

    return mostrar_resultados(resultado, mensaje)


# TEST 3 - Buscar solicitud de administrativo
def probar_buscar_administrativo():
    print("\n========== TEST 3 - Buscar administrativo ==========")

    resultado, mensaje = BuscarSolicitudes(
        "Administrador Sistema",
        CORREO_ADMIN
    )

    return mostrar_resultados(resultado, mensaje)


# TEST 4 - Buscar por ID de solicitud
def probar_buscar_por_id(solicitudes):
    print("\n========== TEST 4 - Buscar por ID ==========")

    if not solicitudes:
        print("No hay solicitudes disponibles para probar.")
        return

    id_solicitud = solicitudes[0]["IdSolicitud"]

    resultado, mensaje = BuscarSolicitudes(
        str(id_solicitud),
        CORREO_ADMIN
    )

    mostrar_resultados(resultado, mensaje)


# TEST 5 - Buscar solicitud inexistente
def probar_busqueda_inexistente():
    print("\n========== TEST 5 - Búsqueda inexistente ==========")

    resultado, mensaje = BuscarSolicitudes(
        "Solicitante Que No Existe",
        CORREO_ADMIN
    )

    mostrar_resultados(resultado, mensaje)


# TEST 6 - Criterio vacío
def probar_criterio_vacio():
    print("\n========== TEST 6 - Criterio vacío ==========")

    resultado, mensaje = BuscarSolicitudes(
        "",
        CORREO_ADMIN
    )

    mostrar_resultados(resultado, mensaje)


# TEST 7 - Usuario sin permisos
def probar_sin_permisos():
    print("\n========== TEST 7 - Usuario sin permisos ==========")

    resultado, mensaje = BuscarSolicitudes(
        "Estudiante Prueba",
        "estudiante@sgfdu.com"
    )

    mostrar_resultados(resultado, mensaje)


if __name__ == "__main__":

    # Obtener los IDs reales de los usuarios de prueba
    id_estudiante = ObtenerIdUsuario("estudiante@sgfdu.com")
    id_graduado = ObtenerIdUsuario("graduado@sgfdu.com")
    id_admin = ObtenerIdUsuario("admin@sgfdu.com")
    id_comite = ObtenerIdUsuario("comite@sgfdu.com")
    id_asistente = ObtenerIdUsuario("asistente@sgfdu.com")

    # Roles autorizados
    if id_estudiante:
        ProbarCrearSolicitud(
            id_estudiante,
            "TEST 1 - Estudiante crea solicitud"
        )

    if id_graduado:
        ProbarCrearSolicitud(
            id_graduado,
            "TEST 2 - Graduado crea solicitud"
        )

    if id_admin:
        ProbarCrearSolicitud(
            id_admin,
            "TEST 3 - Administrativo crea solicitud"
        )

    # Roles no autorizados
    if id_comite:
        ProbarCrearSolicitud(
            id_comite,
            "TEST 4 - Comité intenta crear solicitud"
        )

    if id_asistente:
        ProbarCrearSolicitud(
            id_asistente,
            "TEST 5 - Asistente CIC intenta crear solicitud"
        )

    # Pruebas de búsqueda
    estudiante = probar_buscar_estudiante()
    graduado = probar_buscar_graduado()
    administrativo = probar_buscar_administrativo()

    solicitudes_encontradas = []

    for grupo in (estudiante, graduado, administrativo):
        if grupo:
            solicitudes_encontradas.extend(grupo)

    probar_buscar_por_id(solicitudes_encontradas)
    probar_busqueda_inexistente()
    probar_criterio_vacio()
    probar_sin_permisos()
