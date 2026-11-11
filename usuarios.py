from conexion import ObtenerConexion
import pyodbc

def CrearUsuario(identificacion, nombre, apellido, correo, telefono, contrasena, rol_id):
    conexion = ObtenerConexion()
    cursor = conexion.cursor()

    # Validar campos obligatorios
    if not identificacion or not nombre or not apellido or not correo or not contrasena:
        return False, "Los campos obligatorios deben completarse"

    # Validar correo
    if "@" not in correo:
        return False, "El correo no es válido"

    # Validar contraseña
    if len(contrasena) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"

    try:
        # Verificar si ya existe identificación o correo
        cursor.execute(
            """
            SELECT id
            FROM Usuario
            WHERE identificacion = ? OR correo = ?
            """,
            (identificacion, correo)
        )

        usuario_existente = cursor.fetchone()

        if usuario_existente is not None:
            cursor.close()
            return False, "Ya existe un usuario con esa identificación o correo"

        # Insertar usuario
        cursor.execute(
            """
            INSERT INTO Usuario
            (identificacion, nombre, apellido, correo, telefono, contrasena, rol_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (identificacion, nombre, apellido, correo, telefono, contrasena, rol_id)
        )

        conexion.commit()
        cursor.close()

        return True, "Usuario creado correctamente"

    except pyodbc.Error as error:
        conexion.rollback()
        cursor.close()
        return False, f"Error al crear el usuario: {error}"

    

def ObtenerUsuario(correo):
    conexion = ObtenerConexion()
    cursor = conexion.cursor()

    if not correo:
        return False, "El correo es obligatorio"

    try:
        cursor.execute(
            """
            SELECT id, nombre, apellidos, correo, rol_id, estado_id
            FROM Usuario
            WHERE correo = ?
            """,
            (correo,)
        )

        fila = cursor.fetchone()

        if fila is None:
            cursor.close()
            return False, "Usuario no encontrado"

        usuario = {
            "id": fila[0],
            "nombre": fila[1],
            "apellido": fila[2],
            "correo": fila[3],
            "rol_id": fila[4],
            "estado_id": fila[5]
        }

        cursor.close()
        return True, usuario

    except pyodbc.Error as error:
        cursor.close()
        return False, f"Error al obtener el usuario: {error}"


def ActualizarUsuario(correo, nombre=None, apellido=None, contrasena=None):
    conexion = ObtenerConexion()
    cursor = conexion.cursor()

    if not correo:
        return False, "El correo es obligatorio"

    if contrasena is not None and len(contrasena) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"

    # Solo se actualizan los campos que llegan con valor
    campos = []
    valores = []

    if nombre:
        campos.append("nombre = ?")
        valores.append(nombre)

    if apellido:
        campos.append("apellidos = ?")
        valores.append(apellido)

    if contrasena:
        campos.append("contrasena = ?")
        valores.append(contrasena)

    if not campos:
        return False, "No hay campos para actualizar"


    valores.append(correo)

    try:
        cursor.execute(
            f"UPDATE Usuario SET {', '.join(campos)} WHERE correo = ?",
            valores
        )

        if cursor.rowcount == 0:
            conexion.rollback()
            cursor.close()
            return False, "Usuario no encontrado"

        conexion.commit()
        cursor.close()
        return True, "Usuario actualizado correctamente"

    except pyodbc.Error as error:
        conexion.rollback()
        cursor.close()
        return False, f"Error al actualizar el usuario: {error}"


def EliminarUsuario(correo):
    conexion = ObtenerConexion()
    cursor = conexion.cursor()

    if not correo:
        return False, "El correo es obligatorio"

    try:
        # Baja lógica: el usuario queda INACTIVO y se conserva el historial
        cursor.execute(
            """
            UPDATE Usuario
            SET estado_id = 2,
            fecha_desactivacion = SYSDATETIME(),
                fecha_modificacion = SYSDATETIME()
            WHERE correo = ? AND estado_id = 1
            """,
            (correo,)
        )

        if cursor.rowcount == 0:
            conexion.rollback()
            cursor.close()
            return False, "Usuario no encontrado o ya estaba inactivo"

        conexion.commit()
        cursor.close()
        return True, "Usuario desactivado correctamente"

    except pyodbc.Error as error:
        conexion.rollback()
        cursor.close()
        return False, f"Error al desactivar el usuario: {error}"

