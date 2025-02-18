function openUploadModal() {
  document.getElementById("uploadModal").classList.remove("hidden");
  document.body.style.overflow = "hidden";
}

function closeUploadModal() {
  document.getElementById("uploadModal").classList.add("hidden");
  document.body.style.overflow = "auto";
}

document.addEventListener("keydown", function (event) {
  if (event.key === "Escape") {
    closeUploadModal();
  }
});

document
  .querySelector("#uploadModal")
  .addEventListener("click", function (event) {
    if (event.target === this) {
      closeUploadModal();
    }
  });