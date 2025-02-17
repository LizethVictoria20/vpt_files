function handleFileChange(event) {
  const file = event.target.files[0];
  if(file) {
    document.getElementById('archivoSeleccionado').textContent = 
      "Archivo seleccionado: " + file.name;
  }
}

document.getElementById('archivo').addEventListener('change', function() {
  const archivo = this.files[0];
  if (archivo) {
      document.getElementById('nombre-archivo').textContent = "Archivo seleccionado: " + archivo.name;
  } else {
      document.getElementById('nombre-archivo').textContent = "";
  }
});