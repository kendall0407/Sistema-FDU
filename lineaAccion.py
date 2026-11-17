
from decimal import Decimal, InvalidOperation
from conexion import ObtenerConexion


ROL_ASISTENTE_CIC = 4
ROL_ADMINISTRATIVO = 5
ESTADO_ACTIVO = 1

ROLES_GESTIONAR_LINEAS = {
    ROL_ASISTENTE_CIC,
    ROL_ADMINISTRATIVO
}


def _ObtenerRol(cursor, usuario_id):
    if not usuario_id:
        return None

    cursor.execute("""
        SELECT rol_id
        FROM Usuario
        WHERE id = ?
          AND estado_id = ?
          AND bloqueado = 0
    """, (usuario_id, ESTADO_ACTIVO))

    fila = cursor.fetchone()
    return fila[0] if fila else None


def CrearLineaAccion(texto_linea, monto_maximo,
                     porcentaje, usuario_id):

    conexion = None

    try:
        # Validar nombre
        if not isinstance(texto_linea, str) or not texto_linea.strip():
            return False, "El nombre de la línea es obligatorio."

        texto_linea = texto_linea.strip()

        if len(texto_linea) > 100:
            return False, "El nombre no puede superar los 100 caracteres."

        # Validar monto
        try:
            monto_maximo = Decimal(str(monto_maximo))
        except (InvalidOperation, ValueError, TypeError):
            return False, "El monto máximo no es válido."

        if not monto_maximo.is_finite() or monto_maximo <= 0:
            return False, "El monto máximo debe ser positivo."

        # Validar porcentaje
        try:
            porcentaje = Decimal(str(porcentaje))
        except (InvalidOperation, ValueError, TypeError):
            return False, "El porcentaje no es válido."

        if not porcentaje.is_finite() or not (0 < porcentaje <= 100):
            return False, "El porcentaje debe estar entre 0 y 100."

        conexion = ObtenerConexion()
        cursor = conexion.cursor()

        # Verificar permisos
        rol = _ObtenerRol(cursor, usuario_id)

        if rol not in ROLES_GESTIONAR_LINEAS:
            return False, "No tiene permisos para crear líneas de acción."

        # Verificar nombre duplicado
        cursor.execute("""
            SELECT 1
            FROM LineaAccion
            WHERE TextoLinea = ?
        """, (texto_linea,))

        if cursor.fetchone():
            return False, "Ya existe una línea de acción con ese nombre."

        # Insertar línea
        cursor.execute("""
            INSERT INTO LineaAccion
                (TextoLinea, MontoMaximo, Porcentaje)
            OUTPUT INSERTED.IdLineaAccion
            VALUES (?, ?, ?)
        """, (texto_linea, monto_maximo, porcentaje))

        id_linea = cursor.fetchone()[0]

        # Registrar historial
        valores_nuevos = (
            f"Nombre: {texto_linea}; "
            f"Monto máximo: {monto_maximo}; "
            f"Porcentaje: {porcentaje}"
        )

        cursor.execute("""
            INSERT INTO HistorialLineaAccion (
                IdLineaAccion,
                UsuarioModificador,
                TipoCambio,
                ValoresAnteriores,
                ValoresNuevos
            )
            VALUES (?, ?, 'CREACION', NULL, ?)
        """, (id_linea, usuario_id, valores_nuevos))

        conexion.commit()

        return True, f"Línea de acción creada correctamente. ID: {id_linea}"

    except Exception as e:
        if conexion:
            conexion.rollback()

        return False, f"Error al crear la línea de acción: {str(e)}"

    finally:
        if conexion:
            conexion.close()



from decimal import Decimal, InvalidOperation
from conexion import ObtenerConexion


def ModificarLineaAccion(id_linea_accion, cambios, usuario_id):

    conexion = None

    try:
        # Validar identificador
        if not isinstance(id_linea_accion, int) or id_linea_accion <= 0:
            return False, "El identificador de la línea no es válido."

        if not isinstance(cambios, dict) or not cambios:
            return False, "Debe indicar los cambios que desea realizar."

        # Campos que se pueden modificar
        campos_permitidos = {
            "TextoLinea",
            "MontoMaximo",
            "Porcentaje"
        }

        if not set(cambios.keys()).issubset(campos_permitidos):
            return False, "Se intentó modificar un campo no permitido."

        conexion = ObtenerConexion()
        cursor = conexion.cursor()

        # Verificar permisos
        rol = _ObtenerRol(cursor, usuario_id)

        if rol not in ROLES_GESTIONAR_LINEAS:
            return False, "No tiene permisos para modificar líneas de acción."

        # Obtener información actual
        cursor.execute("""
            SELECT TextoLinea, MontoMaximo, Porcentaje
            FROM LineaAccion
            WHERE IdLineaAccion = ?
        """, (id_linea_accion,))

        fila = cursor.fetchone()

        if not fila:
            return False, "La línea de acción no existe."

        nombre_actual = fila[0]
        monto_actual = Decimal(str(fila[1]))
        porcentaje_actual = Decimal(str(fila[2]))

        # Preparar valores nuevos
        nombre_nuevo = nombre_actual
        monto_nuevo = monto_actual
        porcentaje_nuevo = porcentaje_actual

        # Validar nombre
        if "TextoLinea" in cambios:
            nombre = cambios["TextoLinea"]

            if not isinstance(nombre, str) or not nombre.strip():
                return False, "El nombre de la línea es obligatorio."

            nombre_nuevo = nombre.strip()

            if len(nombre_nuevo) > 100:
                return False, "El nombre no puede superar los 100 caracteres."

            # Comprobar que no exista otro nombre igual
            cursor.execute("""
                SELECT 1
                FROM LineaAccion
                WHERE TextoLinea = ?
                  AND IdLineaAccion <> ?
            """, (nombre_nuevo, id_linea_accion))

            if cursor.fetchone():
                return False, "Ya existe otra línea con ese nombre."

        # Validar monto máximo
        if "MontoMaximo" in cambios:
            try:
                monto_nuevo = Decimal(str(cambios["MontoMaximo"]))
            except (InvalidOperation, ValueError, TypeError):
                return False, "El monto máximo no es válido."

            if not monto_nuevo.is_finite() or monto_nuevo <= 0:
                return False, "El monto máximo debe ser positivo."

        # Validar porcentaje
        if "Porcentaje" in cambios:
            try:
                porcentaje_nuevo = Decimal(str(cambios["Porcentaje"]))
            except (InvalidOperation, ValueError, TypeError):
                return False, "El porcentaje no es válido."

            if not porcentaje_nuevo.is_finite() or not (
                0 < porcentaje_nuevo <= 100
            ):
                return False, "El porcentaje debe estar entre 0 y 100."

        # Detectar si realmente hubo cambios
        if (
            nombre_nuevo == nombre_actual
            and monto_nuevo == monto_actual
            and porcentaje_nuevo == porcentaje_actual
        ):
            return False, "No se detectaron cambios en la línea de acción."

        # Guardar valores anteriores y nuevos para el historial
        valores_anteriores = (
            f"Nombre: {nombre_actual}; "
            f"Monto máximo: {monto_actual}; "
            f"Porcentaje: {porcentaje_actual}"
        )

        valores_nuevos = (
            f"Nombre: {nombre_nuevo}; "
            f"Monto máximo: {monto_nuevo}; "
            f"Porcentaje: {porcentaje_nuevo}"
        )

        # Actualizar línea de acción
        cursor.execute("""
            UPDATE LineaAccion
            SET TextoLinea = ?,
                MontoMaximo = ?,
                Porcentaje = ?,
                FechaModificacion = SYSDATETIME()
            WHERE IdLineaAccion = ?
        """, (
            nombre_nuevo,
            monto_nuevo,
            porcentaje_nuevo,
            id_linea_accion
        ))

        # Registrar historial
        cursor.execute("""
            INSERT INTO HistorialLineaAccion (
                IdLineaAccion,
                UsuarioModificador,
                TipoCambio,
                ValoresAnteriores,
                ValoresNuevos
            )
            VALUES (?, ?, 'MODIFICACION', ?, ?)
        """, (
            id_linea_accion,
            usuario_id,
            valores_anteriores,
            valores_nuevos
        ))

        conexion.commit()

        return True, "Línea de acción modificada correctamente."

    except Exception as e:
        if conexion:
            conexion.rollback()

        return False, f"Error al modificar la línea de acción: {str(e)}"

    finally:
        if conexion:
            conexion.close()



from conexion import ObtenerConexion


def EliminarLineaAccion(id_linea_accion, usuario_id):

    conexion = None

    try:
        # Validar identificador
        if not isinstance(id_linea_accion, int) or id_linea_accion <= 0:
            return False, "El identificador de la línea no es válido."

        conexion = ObtenerConexion()
        cursor = conexion.cursor()

        # Verificar permisos
        rol = _ObtenerRol(cursor, usuario_id)

        if rol not in ROLES_GESTIONAR_LINEAS:
            return False, "No tiene permisos para eliminar líneas de acción."

        # Consultar línea de acción
        cursor.execute("""
            SELECT TextoLinea, MontoMaximo, Porcentaje, Estado
            FROM LineaAccion
            WHERE IdLineaAccion = ?
        """, (id_linea_accion,))

        fila = cursor.fetchone()

        if not fila:
            return False, "La línea de acción no existe."

        nombre, monto, porcentaje, estado = fila

        # Verificar que esté activa
        if estado != "ACTIVA":
            return False, "La línea de acción ya se encuentra inactiva."

        # Desactivar línea
        cursor.execute("""
            UPDATE LineaAccion
            SET Estado = 'INACTIVA',
                FechaModificacion = SYSDATETIME()
            WHERE IdLineaAccion = ?
        """, (id_linea_accion,))

        # Registrar historial
        valores_anteriores = (
            f"Nombre: {nombre}; "
            f"Monto máximo: {monto}; "
            f"Porcentaje: {porcentaje}; "
            f"Estado: ACTIVA"
        )

        valores_nuevos = (
            f"Nombre: {nombre}; "
            f"Monto máximo: {monto}; "
            f"Porcentaje: {porcentaje}; "
            f"Estado: INACTIVA"
        )

        cursor.execute("""
            INSERT INTO HistorialLineaAccion (
                IdLineaAccion,
                UsuarioModificador,
                TipoCambio,
                ValoresAnteriores,
                ValoresNuevos
            )
            VALUES (?, ?, 'ELIMINACION', ?, ?)
        """, (
            id_linea_accion,
            usuario_id,
            valores_anteriores,
            valores_nuevos
        ))

        conexion.commit()

        return True, "Línea de acción desactivada correctamente."

    except Exception as e:
        if conexion:
            conexion.rollback()

        return False, f"Error al eliminar la línea de acción: {str(e)}"

    finally:
        if conexion:
            conexion.close()



from conexion import ObtenerConexion


def ConsultarLineasAccion(usuario_id, incluir_inactivas=False):

    conexion = None

    try:
        conexion = ObtenerConexion()
        cursor = conexion.cursor()

        # Verificar permisos
        rol = _ObtenerRol(cursor, usuario_id)

        if rol not in ROLES_GESTIONAR_LINEAS:
            return False, "No tiene permisos para consultar las líneas de acción."

        if incluir_inactivas:
            cursor.execute("""
                SELECT
                    IdLineaAccion,
                    TextoLinea,
                    MontoMaximo,
                    Porcentaje,
                    Estado,
                    FechaModificacion
                FROM LineaAccion
                ORDER BY IdLineaAccion
            """)
        else:
            cursor.execute("""
                SELECT
                    IdLineaAccion,
                    TextoLinea,
                    MontoMaximo,
                    Porcentaje,
                    Estado,
                    FechaModificacion
                FROM LineaAccion
                WHERE Estado = 'ACTIVA'
                ORDER BY IdLineaAccion
            """)

        filas = cursor.fetchall()

        lineas = []

        for fila in filas:
            lineas.append({
                "IdLineaAccion": fila[0],
                "TextoLinea": fila[1],
                "MontoMaximo": float(fila[2]),
                "Porcentaje": float(fila[3]),
                "Estado": fila[4],
                "FechaModificacion": fila[5]
            })

        return True, lineas

    except Exception as e:
        return False, f"Error al consultar las líneas: {str(e)}"

    finally:
        if conexion:
            conexion.close()



def ConsultarLineaAccion(id_linea_accion, usuario_id):

    conexion = None

    try:
        if not isinstance(id_linea_accion, int) or id_linea_accion <= 0:
            return False, "El identificador de la línea no es válido."

        conexion = ObtenerConexion()
        cursor = conexion.cursor()

        # Verificar permisos
        rol = _ObtenerRol(cursor, usuario_id)

        if rol not in ROLES_GESTIONAR_LINEAS:
            return False, "No tiene permisos para consultar esta línea."

        cursor.execute("""
            SELECT
                IdLineaAccion,
                TextoLinea,
                MontoMaximo,
                Porcentaje,
                Estado,
                FechaModificacion
            FROM LineaAccion
            WHERE IdLineaAccion = ?
        """, (id_linea_accion,))

        fila = cursor.fetchone()

        if not fila:
            return False, "La línea de acción no existe."

        linea = {
            "IdLineaAccion": fila[0],
            "TextoLinea": fila[1],
            "MontoMaximo": float(fila[2]),
            "Porcentaje": float(fila[3]),
            "Estado": fila[4],
            "FechaModificacion": fila[5]
        }

        return True, linea

    except Exception as e:
        return False, f"Error al consultar la línea: {str(e)}"

    finally:
        if conexion:
            conexion.close()




from conexion import ObtenerConexion


def ConsultarHistorialLineaAccion(usuario_id, id_linea_accion=None):

    conexion = None

    try:
        conexion = ObtenerConexion()
        cursor = conexion.cursor()

        # Verificar permisos
        rol = _ObtenerRol(cursor, usuario_id)

        if rol not in ROLES_GESTIONAR_LINEAS:
            return False, "No tiene permisos para consultar el historial."

        # Consultar historial general o de una línea específica
        consulta = """
            SELECT
                H.IdHistorial,
                H.IdLineaAccion,
                L.TextoLinea,
                H.UsuarioModificador,
                U.nombre,
                U.apellidos,
                H.TipoCambio,
                H.ValoresAnteriores,
                H.ValoresNuevos,
                H.FechaCambio
            FROM HistorialLineaAccion H
            INNER JOIN LineaAccion L
                ON H.IdLineaAccion = L.IdLineaAccion
            INNER JOIN Usuario U
                ON H.UsuarioModificador = U.id
        """

        parametros = ()

        if id_linea_accion is not None:

            if not isinstance(id_linea_accion, int) or id_linea_accion <= 0:
                return False, "El identificador de la línea no es válido."

            consulta += """
                WHERE H.IdLineaAccion = ?
            """

            parametros = (id_linea_accion,)

        consulta += """
            ORDER BY H.FechaCambio DESC, H.IdHistorial DESC
        """

        cursor.execute(consulta, parametros)

        filas = cursor.fetchall()

        historial = []

        for fila in filas:
            historial.append({
                "IdHistorial": fila[0],
                "IdLineaAccion": fila[1],
                "NombreLinea": fila[2],
                "UsuarioModificador": fila[3],
                "NombreUsuario": f"{fila[4]} {fila[5]}",
                "TipoCambio": fila[6],
                "ValoresAnteriores": fila[7],
                "ValoresNuevos": fila[8],
                "FechaCambio": fila[9]
            })

        return True, historial

    except Exception as e:
        return False, f"Error al consultar el historial: {str(e)}"

    finally:
        if conexion:
            conexion.close()
