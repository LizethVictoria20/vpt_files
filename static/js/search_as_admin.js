const searchInput = document.getElementById("searchInput");
const userTableBody = document.getElementById("userTableBody");

searchInput.addEventListener("keyup", async function() {
  const query = searchInput.value.trim();


  try {
    const response = await fetch(`/admin/buscar_usuarios_json?q=${encodeURIComponent(query)}`);
    const data = await response.json();
    const users = data.users;
    
    renderUserTable(users);

  } catch (error) {
    console.error("Error al buscar usuarios:", error);
  }
});

function renderUserTable(users) {
  userTableBody.innerHTML = "";

  if (!users || users.length === 0) {
    userTableBody.innerHTML = `
      <tr>
        <td colspan="5" class="px-6 py-4 text-center text-sm text-gray-500">
          No se encontraron coincidencias.
        </td>
      </tr>
    `;
    return;
  }

  let html = "";
  users.forEach((u) => {
    const displayName = (u.name || "") + " " + (u.lastname || "");
    const iconLetter = u.name ? u.name[0].toUpperCase() : "U";
    const roles = u.roles[0];
    console.log(u);
  
    html += `
      <tr class="hover:bg-gray-50 transition-base">
        <td class="px-6 py-4 whitespace-nowrap">
          <div class="flex items-center">
            <div class="flex-shrink-0 h-10 w-10 rounded-full bg-gray-200 flex items-center justify-center text-gray-500">
              ${iconLetter}
            </div>
            <div class="ml-4">
              <div class="text-sm font-medium text-gray-900">
                ${displayName}
              </div>
            </div>
          </div>
        </td>

        <td class="px-6 py-4 whitespace-nowrap">
          <div class="text-sm text-gray-500">${u.email}</div>
        </td>

        <!-- Si no devuelves roles en JSON, puedes dejar vacío -->
        <td class="px-6 py-4">
          <span class="text-xs text-gray-400">${roles}</span>
        </td>

        <td class="px-6 py-4 whitespace-nowrap">
          <span class="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">
            ${u.folders_count} carpeta
          </span>
        </td>

        <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
          <div class="flex items-center justify-end space-x-3">
            <a href="/admin/admin_carpeta/${u.id}" class="text-blue-600 hover:text-blue-900" title="Ver detalles y carpetas">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M2.458 12C3.732 7.943 7.523 5 
                     12 5c4.478 0 8.268 2.943 
                     9.542 7-1.274 4.057-5.064 7
                     -9.542 7-4.477 0-8.268-2.943
                     -9.542-7z"/>
              </svg>
            </a>
            <!-- Botón eliminar -->
            <button class="text-red-600 hover:text-red-900" title="Eliminar usuario"
              onclick="confirmDeleteUser(${u.id}, '${u.username}')"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21
                     H7.862a2 2 0 01-1.995-1.858L5 7
                     m5 4v6m4-6v6
                     m1-10V4a1 1 0 00-1-1h-4
                     a1 1 0 00-1 1v3M4 7h16"/>
              </svg>
            </button>
          </div>
        </td>
      </tr>
    `;
  });

  userTableBody.innerHTML = html;
}
