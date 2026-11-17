def AgregarParticipanteSesion(id_sesion, id_usuario, usuario_id):

    conexion = None
    cursor = None

    try:

        # 1. Validar datos obligatorios.
        if not id_sesion or not id_usuario or not usuario_id:
            return False, "Faltan datos obligatorios."

        try:
            id_sesion = int(id_sesion)
            id_usuario = int(id_usuario)

            if id_sesion <= 0 or id_usuario <= 0:
                return False, "Los identificadores deben ser positivos."

        except (ValueError, TypeError):
            return False, "Los identificadores deben ser números."

        # 2. Conectar con la base de datos.
        conexion = ObtenerConexion()
        cursor = conexion.cursor()

        # 3. Verificar permisos.
        rol = _ObtenerRol(cursor, usuario_id)

        if rol not in ROLES_GESTIONAR_AGENDA:
            return False, "No tiene permisos para agregar participantes."

        # 4. Verificar que la sesión exista.
        cursor.execute("""
            SELECT IdSesion
            FROM Sesion
            WHERE IdSesion = ?
        """, (id_sesion,))

        if not cursor.fetchone():
            return False, "La sesión indicada no existe."

        # 5. Verificar que el usuario sea un miembro activo del Comité.
        cursor.execute("""
            SELECT id
            FROM Usuario
            WHERE id = ?
              AND rol_id = ?
              AND estado_id = ?
              AND bloqueado = 0
        """, (
            id_usuario,
            ROL_MIEMBRO_COMITE,
            ESTADO_ACTIVO
        ))

        if not cursor.fetchone():
            return False, "El usuario no es un miembro activo del Comité Técnico."

        # 6. Verificar que no esté ya registrado.
        cursor.execute("""
            SELECT IdParticipanteSesion
            FROM ParticipanteSesion
            WHERE IdSesion = ?
              AND IdUsuario = ?
        """, (id_sesion, id_usuario))

        if cursor.fetchone():
            return False, "El usuario ya está registrado como participante de esta sesión."

        # 7. Agregar participante.
        cursor.execute("""
            INSERT INTO ParticipanteSesion (
                IdSesion,
                IdUsuario
            )
            VALUES (?, ?)
        """, (id_sesion, id_usuario))

        # 8. Confirmar cambios.
        conexion.commit()

        return True, "Participante agregado correctamente."

    except Exception as error:

        if conexion:
            conexion.rollback()

        return False, f"Error al agregar participante: {error}"

    finally:

        if cursor:
            cursor.close()

        if conexion:
            conexion.close()