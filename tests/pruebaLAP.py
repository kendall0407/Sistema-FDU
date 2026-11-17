
from datetime import datetime
from conexion import ObtenerConexion

from lineaAccion import (
    CrearLineaAccion,
    ModificarLineaAccion,
    EliminarLineaAccion,
    ConsultarLineasAccion,
    ConsultarLineaAccion,
    ConsultarHistorialLineaAccion
)


def ObtenerUsuariosPrueba():
    """Busca usuarios existentes. Solo consulta; no modifica nada."""

    conexion = ObtenerConexion()

    try:
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT TOP 1 id
            FROM Usuario
            WHERE rol_id IN (4, 5)
              AND estado_id = 1
              AND bloqueado = 0
            ORDER BY rol_id
        """)

        fila_autorizado = cursor.fetchone()

        cursor.execute("""
            SELECT TOP 1 id
            FROM Usuario
            WHERE rol_id = 1
              AND estado_id = 1
              AND bloqueado = 0
        """)

        fila_estudiante = cursor.fetchone()

        if not fila_autorizado:
            raise Exception(
                "No existe un usuario activo con rol de Asistente CIC o Administrativo."
            )

        if not fila_estudiante:
            raise Exception(
                "No existe un estudiante activo para probar los permisos."
            )

        return fila_autorizado[0], fila_estudiante[0]

    finally:
        conexion.close()


def MostrarPrueba(nombre, resultado, esperado=True):

    correcto = resultado[0] == esperado

    print(f"\n{nombre}")
    print("Resultado:", resultado[1])
    print("PRUEBA CORRECTA" if correcto else "PRUEBA FALLIDA")

    return correcto


def EjecutarPruebas():

    pruebas = []

    print("===================================")
    print("PRUEBAS DEL MÓDULO DE LÍNEAS DE ACCIÓN")
    print("===================================")

    # Obtener usuarios existentes sin modificarlos
    usuario_admin, usuario_estudiante = ObtenerUsuariosPrueba()

    print("Usuario autorizado:", usuario_admin)
    print("Usuario estudiante:", usuario_estudiante)

    # Crear un nombre único para evitar conflictos con otras pruebas
    identificador = datetime.now().strftime("%Y%m%d%H%M%S%f")
    nombre_linea = f"LINEA PRUEBA {identificador}"

    id_linea = None

    print("\n===================================")
    print("PRUEBAS DE CREACIÓN")
    print("===================================")

    # Crear una línea exclusiva para las pruebas
    resultado = CrearLineaAccion(
        nombre_linea,
        1000000,
        25,
        usuario_admin
    )

    pruebas.append(
        MostrarPrueba("Crear línea de acción", resultado)
    )

    if not resultado[0]:
        print("\nNo se pudo crear la línea. Se detienen las pruebas.")
        return

    # Obtener el ID generado desde el mensaje de creación
    id_linea = int(resultado[1].split("ID: ")[-1])

    print("ID de la línea de prueba:", id_linea)

    # Intentar crear otra línea con el mismo nombre
    resultado = CrearLineaAccion(
        nombre_linea,
        1000000,
        25,
        usuario_admin
    )

    pruebas.append(
        MostrarPrueba(
            "Rechazar nombre duplicado",
            resultado,
            esperado=False
        )
    )

    # Intentar crear con monto inválido
    resultado = CrearLineaAccion(
        f"LINEA INVALIDA {identificador}",
        -500,
        25,
        usuario_admin
    )

    pruebas.append(
        MostrarPrueba(
            "Rechazar monto negativo",
            resultado,
            esperado=False
        )
    )

    # Intentar crear con porcentaje inválido
    resultado = CrearLineaAccion(
        f"LINEA INVALIDA 2 {identificador}",
        1000000,
        150,
        usuario_admin
    )

    pruebas.append(
        MostrarPrueba(
            "Rechazar porcentaje superior a 100",
            resultado,
            esperado=False
        )
    )

    # Comprobar permisos
    resultado = CrearLineaAccion(
        f"LINEA SIN PERMISOS {identificador}",
        1000000,
        25,
        usuario_estudiante
    )

    pruebas.append(
        MostrarPrueba(
            "Estudiante no puede crear líneas",
            resultado,
            esperado=False
        )
    )

    print("\n===================================")
    print("PRUEBAS DE CONSULTA")
    print("===================================")

    resultado = ConsultarLineaAccion(
        id_linea,
        usuario_admin
    )

    pruebas.append(
        MostrarPrueba("Consultar línea creada", resultado)
    )

    resultado = ConsultarLineasAccion(usuario_admin)

    pruebas.append(
        MostrarPrueba("Consultar líneas activas", resultado)
    )

    resultado = ConsultarLineaAccion(
        999999999,
        usuario_admin
    )

    pruebas.append(
        MostrarPrueba(
            "Consultar línea inexistente",
            resultado,
            esperado=False
        )
    )

    resultado = ConsultarLineaAccion(
        id_linea,
        usuario_estudiante
    )

    pruebas.append(
        MostrarPrueba(
            "Estudiante no puede consultar líneas",
            resultado,
            esperado=False
        )
    )

    print("\n===================================")
    print("PRUEBAS DE MODIFICACIÓN")
    print("===================================")

    # Modificar únicamente nuestra línea de prueba
    resultado = ModificarLineaAccion(
        id_linea,
        {
            "TextoLinea": f"LINEA MODIFICADA {identificador}",
            "MontoMaximo": 900000,
            "Porcentaje": 30
        },
        usuario_admin
    )

    pruebas.append(
        MostrarPrueba("Modificar línea creada", resultado)
    )

    # Consultar para comprobar los nuevos valores
    resultado = ConsultarLineaAccion(
        id_linea,
        usuario_admin
    )

    pruebas.append(
        MostrarPrueba("Verificar modificación", resultado)
    )

    # Intentar modificar con monto inválido
    resultado = ModificarLineaAccion(
        id_linea,
        {"MontoMaximo": -100},
        usuario_admin
    )

    pruebas.append(
        MostrarPrueba(
            "Rechazar monto negativo al modificar",
            resultado,
            esperado=False
        )
    )

    # Intentar modificar con porcentaje inválido
    resultado = ModificarLineaAccion(
        id_linea,
        {"Porcentaje": 150},
        usuario_admin
    )

    pruebas.append(
        MostrarPrueba(
            "Rechazar porcentaje inválido al modificar",
            resultado,
            esperado=False
        )
    )

    # Intentar modificar un campo no permitido
    resultado = ModificarLineaAccion(
        id_linea,
        {"Estado": "INACTIVA"},
        usuario_admin
    )

    pruebas.append(
        MostrarPrueba(
            "Rechazar campo no permitido",
            resultado,
            esperado=False
        )
    )

    # Intentar modificar sin permisos
    resultado = ModificarLineaAccion(
        id_linea,
        {"MontoMaximo": 800000},
        usuario_estudiante
    )

    pruebas.append(
        MostrarPrueba(
            "Estudiante no puede modificar líneas",
            resultado,
            esperado=False
        )
    )

    print("\n===================================")
    print("PRUEBAS DE HISTORIAL")
    print("===================================")

    resultado = ConsultarHistorialLineaAccion(
        usuario_admin,
        id_linea
    )

    pruebas.append(
        MostrarPrueba("Consultar historial de la línea", resultado)
    )

    print("\n===================================")
    print("PRUEBAS DE ELIMINACIÓN")
    print("===================================")

    # Desactivar exclusivamente la línea que acabamos de crear
    resultado = EliminarLineaAccion(
        id_linea,
        usuario_admin
    )

    pruebas.append(
        MostrarPrueba("Desactivar línea creada", resultado)
    )

    # Intentar desactivarla otra vez
    resultado = EliminarLineaAccion(
        id_linea,
        usuario_admin
    )

    pruebas.append(
        MostrarPrueba(
            "Rechazar segunda desactivación",
            resultado,
            esperado=False
        )
    )

    # Verificar que realmente quedó inactiva
    resultado = ConsultarLineaAccion(
        id_linea,
        usuario_admin
    )

    correcta = (
        resultado[0]
        and resultado[1]["Estado"] == "INACTIVA"
    )

    print("\nVerificar estado INACTIVA")
    print("Resultado:", resultado[1] if resultado[0] else resultado[1])
    print("PRUEBA CORRECTA" if correcta else "PRUEBA FALLIDA")

    pruebas.append(correcta)

    # Verificar que se puede consultar incluyendo inactivas
    resultado = ConsultarLineasAccion(
        usuario_admin,
        incluir_inactivas=True
    )

    pruebas.append(
        MostrarPrueba(
            "Consultar líneas incluyendo inactivas",
            resultado
        )
    )

    # Comprobar que el historial registra creación, modificación y eliminación
    resultado = ConsultarHistorialLineaAccion(
        usuario_admin,
        id_linea
    )

    tipos_esperados = {
        "CREACION",
        "MODIFICACION",
        "ELIMINACION"
    }

    tipos_encontrados = (
        {registro["TipoCambio"] for registro in resultado[1]}
        if resultado[0] else set()
    )

    correcta = (
        resultado[0]
        and tipos_esperados.issubset(tipos_encontrados)
    )

    print("\nVerificar historial completo")
    print("Tipos encontrados:", tipos_encontrados)
    print("PRUEBA CORRECTA" if correcta else "PRUEBA FALLIDA")

    pruebas.append(correcta)

    print("\n===================================")
    print("RESUMEN DE PRUEBAS")
    print("===================================")

    total = len(pruebas)
    correctas = sum(pruebas)

    print(f"{correctas} de {total} pruebas correctas")


if __name__ == "__main__":
    EjecutarPruebas()
