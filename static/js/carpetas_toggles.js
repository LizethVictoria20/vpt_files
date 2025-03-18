// carpetas_toggles.js

/************************************************
 *  FUNCIONES PARA EXPANDIR/COLAPSAR (toggleGroup, toggleLabel)
 ************************************************/
function toggleGroup(groupId) {
  const groupContent = document.getElementById(groupId);
  if (!groupContent) return;

  const allGroups = document.querySelectorAll("[id^='group_']");
  allGroups.forEach((g) => {
    if (g.id !== groupId) {
      g.style.display = "none";
      const gidx = g.id.split("_")[1];
      const gicon = document.getElementById("group_icon_" + gidx);
      if (gicon) gicon.classList.add("-rotate-90");

      const allLabels = g.querySelectorAll("[id^='label_']");
      allLabels.forEach((lbl) => {
        lbl.style.display = "none";
        const lparts = lbl.id.split("_");
        if (lparts.length >= 3) {
          const licon = document.getElementById(`label_icon_${lparts[1]}_${lparts[2]}`);
          if (licon) licon.classList.add("-rotate-90");
        }
      });
    }
  });

  const idx = groupId.split("_")[1];
  const icon = document.getElementById("group_icon_" + idx);

  if (groupContent.style.display === "none") {
    groupContent.style.display = "block";
    icon?.classList.remove("-rotate-90");
  } else {
    groupContent.style.display = "none";
    icon?.classList.add("-rotate-90");

    const groupLabels = groupContent.querySelectorAll("[id^='label_']");
    groupLabels.forEach((lbl) => {
      lbl.style.display = "none";
      const lparts = lbl.id.split("_");
      if (lparts.length >= 3) {
        const licon = document.getElementById(`label_icon_${lparts[1]}_${lparts[2]}`);
        if (licon) licon.classList.add("-rotate-90");
      }
    });
  }
}

function toggleLabel(labelId) {
  const labelContent = document.getElementById(labelId);
  if (!labelContent) return;

  const allLabels = document.querySelectorAll("[id^='label_']");
  allLabels.forEach((lbl) => {
    if (lbl.id !== labelId) {
      lbl.style.display = "none";
      const parts = lbl.id.split("_");
      if (parts.length >= 3) {
        const lblIcon = document.getElementById(`label_icon_${parts[1]}_${parts[2]}`);
        if (lblIcon) lblIcon.classList.add("-rotate-90");
      }
    }
  });

  const parts = labelId.split("_");
  if (labelContent.style.display === "none") {
    labelContent.style.display = "block";
    const lblIcon = document.getElementById(`label_icon_${parts[1]}_${parts[2]}`);
    lblIcon?.classList.remove("-rotate-90");

    setTimeout(() => {
      labelContent.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 100);
  } else {
    labelContent.style.display = "none";
    const lblIcon = document.getElementById(`label_icon_${parts[1]}_${parts[2]}`);
    lblIcon?.classList.add("-rotate-90");
  }
}

/************************************************
 *  FUNCIONES PARA PREVIEW (openPreviewModal, closePreviewModal)
 ************************************************/
function openPreviewModal(fileId, extension) {
  const modal = document.getElementById("viewerModal");
  const content = document.getElementById("viewerContent");
  content.innerHTML = "";

  if (["pdf", "jpg", "jpeg", "png", "gif"].includes(extension)) {
    content.innerHTML = `<iframe src="/preview_file/${fileId}" frameborder="0" class="w-full h-[80vh]"></iframe>`;
  } else if (["doc", "docx"].includes(extension)) {
    content.innerHTML = `<iframe src="/preview_file/${fileId}" frameborder="0" class="w-full h-[80vh]"></iframe>`;
  } else {
    content.innerHTML = `
      <p class="text-gray-600">
        Formato no soportado. 
        <a class="text-blue-600 underline" href="/descargar_archivo/${fileId}">
          Descargar
        </a>
      </p>`;
  }

  modal.classList.remove("hidden");
}

function closePreviewModal() {
  const modal = document.getElementById("viewerModal");
  const content = document.getElementById("viewerContent");
  modal.classList.add("hidden");
  content.innerHTML = "";
}

/************************************************
 *  FUNCIONES PARA ELIMINAR, ETC.
 ************************************************/


document.addEventListener("DOMContentLoaded", () => {
  // Lógica de inicialización: por ejemplo, ocultar grupos, leer URL, etc.
  const groupElements = document.querySelectorAll("[id^='group_']");
  const labelElements = document.querySelectorAll("[id^='label_']");

  groupElements.forEach((groupEl) => {
    groupEl.style.display = "none";
    const idx = groupEl.id.split("_")[1];
    const icon = document.getElementById("group_icon_" + idx);
    if (icon) icon.classList.add("-rotate-90");
  });

  labelElements.forEach((labelEl) => {
    labelEl.style.display = "none";
    const parts = labelEl.id.split("_");
    if (parts.length >= 3) {
      const labelIcon = document.getElementById(`label_icon_${parts[1]}_${parts[2]}`);
      if (labelIcon) labelIcon.classList.add("-rotate-90");
    }
  });

  // Leer parámetros de la URL (openGroup, openLabel) => expandir si corresponde
  const params = new URLSearchParams(window.location.search);
  const openGroup = params.get("openGroup");
  const openLabel = params.get("openLabel");

  if (openGroup) {
    const groupToOpen = document.querySelector(`[data-group="${openGroup}"]`);
    if (groupToOpen) {
      groupToOpen.style.display = "block";
      const idx = groupToOpen.id.split("_")[1];
      const icon = document.getElementById("group_icon_" + idx);
      if (icon) icon.classList.remove("-rotate-90");
    }
  }

  if (openLabel) {
    const labelToOpen = document.querySelector(`[data-label="${openLabel}"]`);
    if (labelToOpen) {
      const parentGroup = labelToOpen.closest(".group-content");
      if (parentGroup) {
        parentGroup.style.display = "block";
        const groupID = parentGroup.id;
        const groupIdx = groupID.split("_")[1];
        const iconGroup = document.getElementById("group_icon_" + groupIdx);
        if (iconGroup) iconGroup.classList.remove("-rotate-90");
      }
      labelToOpen.style.display = "block";
      const parts = labelToOpen.id.split("_");
      if (parts.length >= 3) {
        const labelIcon = document.getElementById(`label_icon_${parts[1]}_${parts[2]}`);
        if (labelIcon) labelIcon.classList.remove("-rotate-90");
      }
      labelToOpen.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }
});
