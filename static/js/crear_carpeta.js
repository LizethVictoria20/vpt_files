const form = document.querySelector("form");
const loadingOverlay = document.getElementById("loadingOverlay");

form.addEventListener("submit", function (e) {
  e.preventDefault();
  loadingOverlay.classList.remove("hidden");

  // Simulamos la creación
  setTimeout(() => {
    loadingOverlay.classList.add("hidden");
    // Mostramos alerta de éxito
    const alert = document.createElement("div");
    alert.className =
      "p-4 rounded-lg border bg-green-50 border-green-200 my-4";
    alert.innerHTML = `
              <div class="flex">
                  <svg class="w-5 h-5 text-green-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                            d="M5 13l4 4L19 7"/>
                  </svg>
                  <p class="text-sm text-green-700">Carpeta creada exitosamente</p>
              </div>
          `;
    form.insertAdjacentElement("beforebegin", alert);
  }, 2000);
});