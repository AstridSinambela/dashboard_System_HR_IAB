// global.js
function showLoading() {
  document.getElementById("loading-overlay").style.display = "flex";
}

function hideLoading() {
  document.getElementById("loading-overlay").style.display = "none";
}

document.addEventListener("DOMContentLoaded", () => {
  hideLoading();

  document.querySelectorAll("form").forEach((form) => {
    form.addEventListener("submit", () => {
      showLoading();
    });
  });
});
