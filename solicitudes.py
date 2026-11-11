from conexion import ObtenerConexion
import pyodbc

def CrearSolicitud(nombre_solicitante, carne, correo,
                   numero_celular, monto_solicitado,
                   informacion_bancaria, nombre_actividad,
                   linea_accion):

    conexion = ObtenerConexion()
    cursor = conexion.cursor()

    try:
        sql = """
        INSERT INTO Solicitudes (
            NombreSolicitante,
            Carne,
            CorreoElectronico,
            NumeroCelular,
            MontoSolicitado,
            InformacionBancaria,
            NombreActividad,
            LineaAccion
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """

        cursor.execute(sql, (
            nombre_solicitante,
            carne,
            correo,
            numero_celular,
            monto_solicitado,
            informacion_bancaria,
            nombre_actividad,
            linea_accion
        ))

        conexion.commit()

        return True, "Solicitud creada correctamente"

    except pyodbc.Error as error:
        conexion.rollback()
        return False, f"Error al crear la solicitud: {error}"

    finally:
        cursor.close()
        conexion.close()