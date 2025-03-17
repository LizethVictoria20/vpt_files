const searchInput = document.getElementById("searchInput");
const liveResults = document.getElementById("liveResults");

searchInput.addEventListener("keyup", async function () {
  const query = searchInput.value.trim();

  if (!query) {
    liveResults.innerHTML = "";
    return;
  }

  try {
    const response = await fetch(
      `/admin/buscar_archivos_json?q=${encodeURIComponent(query)}`
    );
    const data = await response.json();
    console.log("DATA from admin/buscar_archivos_json =>", data);  // <-- AÑADE ESTE LOG
    
    renderResults(data.files);
    console.log(data.files);
    
  } catch (error) { 
    console.error("Error al buscar archivos:", error);
  }
});

function renderResults(files) {
  liveResults.innerHTML = "";

  if (files.length === 0) {
    liveResults.innerHTML = `
      <p class="text-sm text-gray-500">Sin coincidencias.</p>
    `;
    return;
  }

  let html = "";
  files.forEach((file) => {
    html += `
      <div class="bg-white shadow-lg rounded-lg p-4 hover:shadow-xl transition-shadow duration-300 border border-gray-100">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-3">
            <div class="flex-shrink-0">
              <div class="h-10 w-10 bg-red-50 rounded-full flex items-center justify-center text-red-600">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
            </div>
            <div>
              <p class="text-base font-medium text-gray-900">${
                file.filename
              }</p>
              <div class="flex items-center mt-1">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-gray-400 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                </svg>
                <p class="text-xs text-gray-500">Carpeta: ${
                  file.drive_id
                }</p>
              </div>
            </div>
          </div>
          
          <a href="/carpeta/${
            file.folder_id
          }?openGroup=${encodeURIComponent(
      file.group_label
    )}&openLabel=${encodeURIComponent(file.etiquetas)}"
            <span>Ver carpeta</span>
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 ml-1" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M12.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-2.293-2.293a1 1 0 010-1.414z" clip-rule="evenodd" />
            </svg>
          </a>
        </div>
      </div>
    `;
  });

  liveResults.innerHTML = html;
}