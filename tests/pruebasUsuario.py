
from usuarios import (
    CrearUsuario,
    ObtenerUsuario,
    ActualizarUsuario,
    EliminarUsuario,
    ReactivarUsuario
)


# =====================================================
# TEST 1: CREAR USUARIO
# =====================================================

def probar_crear_usuario():

    print("\n========== PRUEBAS CrearUsuario ==========")

    print("\nTEST 1 - Usuario válido")
    print(CrearUsuario(
        "123456789", "Kendall", "Sanabria",
        "kendall_test@gmail.com", "88888888",
        "Password123", 3
    ))

    print("\nTEST 2 - Identificación vacía")
    print(CrearUsuario(
        "", "Kendall", "Sanabria",
        "test2@gmail.com", "88888888",
        "Password123", 3
    ))

    print("\nTEST 3 - Nombre vacío")
    print(CrearUsuario(
        "123456790", "", "Sanabria",
        "test3@gmail.com", "88888888",
        "Password123", 3
    ))

    print("\nTEST 4 - Apellido vacío")
    print(CrearUsuario(
        "123456791", "Kendall", "",
        "test4@gmail.com", "88888888",
        "Password123", 3
    ))

    print("\nTEST 5 - Correo vacío")
    print(CrearUsuario(
        "123456792", "Kendall", "Sanabria",
        "", "88888888", "Password123", 3
    ))

    print("\nTEST 6 - Contraseña vacía")
    print(CrearUsuario(
        "123456793", "Kendall", "Sanabria",
        "test6@gmail.com", "88888888", "", 3
    ))

    print("\nTEST 7 - Correo sin @")
    print(CrearUsuario(
        "123456794", "Kendall", "Sanabria",
        "testcorreo.com", "88888888", "Password123", 3
    ))

    print("\nTEST 8 - Contraseña de 7 caracteres")
    print(CrearUsuario(
        "123456795", "Kendall", "Sanabria",
        "test8@gmail.com", "88888888", "1234567", 3
    ))

    print("\nTEST 9 - Contraseña exactamente de 8 caracteres")
    print(CrearUsuario(
        "123456796", "Kendall", "Sanabria",
        "test9@gmail.com", "88888888", "12345678", 3
    ))

    print("\nTEST 10 - Identificación duplicada")
    print(CrearUsuario(
        "123456789", "Otro", "Usuario",
        "otro_usuario@gmail.com", "88888888",
        "Password123", 3
    ))

    print("\nTEST 11 - Correo duplicado")
    print(CrearUsuario(
        "999999999", "Otro", "Usuario",
        "kendall_test@gmail.com", "88888888",
        "Password123", 3
    ))

    print("\nTEST 12 - Teléfono vacío")
    print(CrearUsuario(
        "123456797", "Kendall", "Sanabria",
        "test12@gmail.com", "", "Password123", 3
    ))

    print("\nTEST 13 - Rol inexistente")
    print(CrearUsuario(
        "123456798", "Kendall", "Sanabria",
        "test13@gmail.com", "88888888",
        "Password123", 999
    ))

    print("\nTEST 14 - Identificación None")
    print(CrearUsuario(
        None, "Kendall", "Sanabria",
        "test14@gmail.com", "88888888",
        "Password123", 3
    ))

    print("\nTEST 15 - Correo None")
    print(CrearUsuario(
        "123456799", "Kendall", "Sanabria",
        None, "88888888", "Password123", 3
    ))

    
    print("\nTEST 16 - Identificación duplicada con otro correo")
    print(CrearUsuario(
        "123456789",
        "Otro",
        "Usuario",
        "otro_correo16@gmail.com",
        "88888888",
        "Password123",
        3
    ))

    print("\nTEST 17 - Correo duplicado con otra identificación")
    print(CrearUsuario(
        "987654321",
        "Otro",
        "Usuario",
        "kendall_test@gmail.com",
        "88888888",
        "Password123",
        3
    ))

    print("\nTEST 18 - Identificación y correo duplicados")
    print(CrearUsuario(
        "123456789",
        "Otro",
        "Usuario",
        "kendall_test@gmail.com",
        "88888888",
        "Password123",
        3
    ))

    print("\nTEST 19 - Correo con espacios")
    print(CrearUsuario(
        "123456822", "Kendall", "Sanabria",
        "   kendall_test123@gmail.com   ",
        "88888888", "Password123", 3
    ))



# =====================================================
# TEST 2: OBTENER USUARIO
# =====================================================


# =====================================================
# TEST: OBTENER USUARIO
# =====================================================

def probar_obtener_usuario():

    print("\n========== PRUEBAS ObtenerUsuario ==========")

    correo_solicitante = "admin@sgfdu.com"

    print("\nTEST 1 - Usuario existente")
    print(ObtenerUsuario("estudiante@sgfdu.com", correo_solicitante))

    print("\nTEST 2 - Usuario inexistente")
    print(ObtenerUsuario("usuarioquenoexiste@gmail.com", correo_solicitante))

    print("\nTEST 3 - Correo vacío")
    print(ObtenerUsuario("", correo_solicitante))

    print("\nTEST 4 - Correo None")
    print(ObtenerUsuario(None, correo_solicitante))

    print("\nTEST 5 - Correo con espacios")
    print(ObtenerUsuario("   estudiante@sgfdu.com   ", correo_solicitante))


# =====================================================
# TEST: ACTUALIZAR USUARIO
# =====================================================

def probar_actualizar_usuario():

    print("\n========== PRUEBAS ActualizarUsuario ==========")

    correo = "estudiante@sgfdu.com"
    correo_solicitante = "estudiante@sgfdu.com"

    print("\nTEST 1 - Actualizar nombre")
    print(ActualizarUsuario(correo, correo_solicitante, nombre="NuevoNombre"))

    print("\nTEST 2 - Actualizar apellido")
    print(ActualizarUsuario(correo, correo_solicitante, apellido="NuevoApellido"))

    print("\nTEST 3 - Actualizar contraseña")
    print(ActualizarUsuario(correo, correo_solicitante, contrasena="NuevaClave123"))

    print("\nTEST 4 - Actualizar varios campos")
    print(ActualizarUsuario(
        correo,
        correo_solicitante,
        nombre="NombreActualizado",
        apellido="ApellidoActualizado",
        contrasena="OtraClave123"
    ))

    print("\nTEST 5 - Correo vacío")
    print(ActualizarUsuario("", correo_solicitante))

    print("\nTEST 6 - Correo None")
    print(ActualizarUsuario(None, correo_solicitante))

    print("\nTEST 7 - Contraseña menor a 8 caracteres")
    print(ActualizarUsuario(correo, correo_solicitante, contrasena="1234567"))

    print("\nTEST 8 - Sin campos para actualizar")
    print(ActualizarUsuario(correo, correo_solicitante))

    print("\nTEST 9 - Usuario inexistente")
    print(ActualizarUsuario(
        "noexiste@gmail.com",
        correo_solicitante,
        nombre="Prueba"
    ))


# =====================================================
# TEST: ELIMINAR USUARIO
# =====================================================

def probar_eliminar_usuario():

    print("\n========== PRUEBAS EliminarUsuario ==========")

    correo = "estudiante@sgfdu.com"
    correo_solicitante = "admin@sgfdu.com"

    print("\nTEST 1 - Desactivar usuario existente")
    print(EliminarUsuario(correo, correo_solicitante))

    print("\nTEST 2 - Verificar que quedó inactivo")
    print(ObtenerUsuario(correo, "admin@sgfdu.com"))

    print("\nTEST 3 - Desactivar usuario ya inactivo")
    print(EliminarUsuario(correo, correo_solicitante))

    print("\nTEST 4 - Correo vacío")
    print(EliminarUsuario("", correo_solicitante))

    print("\nTEST 5 - Correo None")
    print(EliminarUsuario(None, correo_solicitante))

    print("\nTEST 6 - Usuario inexistente")
    print(EliminarUsuario("noexiste@gmail.com", correo_solicitante))


# =====================================================
# TEST: REACTIVAR USUARIO
# =====================================================

def probar_reactivar_usuario():

    print("\n========== PRUEBAS ReactivarUsuario ==========")

    correo = "estudiante@sgfdu.com"
    correo_solicitante = "admin@sgfdu.com"

    print("\nTEST 1 - Reactivar usuario desactivado")
    print(ReactivarUsuario(correo, correo_solicitante))

    print("\nTEST 2 - Reactivar usuario ya activo")
    print(ReactivarUsuario(correo, correo_solicitante))

    print("\nTEST 3 - Correo vacío")
    print(ReactivarUsuario("", correo_solicitante))

    print("\nTEST 4 - Correo None")
    print(ReactivarUsuario(None, correo_solicitante))

    print("\nTEST 5 - Usuario inexistente")
    print(ReactivarUsuario("noexiste@gmail.com", correo_solicitante))


# =====================================================
# EJECUTAR TODAS LAS PRUEBAS
# =====================================================

if __name__ == "__main__":
    probar_crear_usuario()
    probar_obtener_usuario()
    probar_actualizar_usuario()
    probar_eliminar_usuario()
    probar_reactivar_usuario()



