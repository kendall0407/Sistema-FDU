from usuarios import ObtenerUsuario


print("\n========== PRUEBAS ObtenerUsuario ==========")


print("\nPrueba 1 - Usuario existente")
resultado = ObtenerUsuario("correo_existente@gmail.com")
print(resultado)


print("\nPrueba 2 - Usuario inexistente")
resultado = ObtenerUsuario("usuarioquenoexiste@gmail.com")
print(resultado)


print("\nPrueba 3 - Correo vacío")
resultado = ObtenerUsuario("")
print(resultado)


print("\nPrueba 4 - Correo None")
resultado = ObtenerUsuario(None)
print(resultado)


print("\nPrueba 5 - Correo con espacios")
resultado = ObtenerUsuario("   correo_existente@gmail.com   ")
print(resultado)