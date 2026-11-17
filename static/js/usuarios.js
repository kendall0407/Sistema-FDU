
const buscador = document.getElementById("buscarUsuario");
const filas = document.querySelectorAll("#tablaUsuarios tbody tr");

buscador.addEventListener("input", function () {
    const texto = buscador.value.toLowerCase().trim();

    filas.forEach(function (fila) {
        const contenido = fila.textContent.toLowerCase();

        fila.hidden = !contenido.includes(texto);
    });
});
