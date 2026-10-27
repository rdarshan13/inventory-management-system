function openStockModal(id, name, quantity) {
  const modal = document.getElementById("stockModal");
  if (!modal) return;
  document.getElementById("stockForm").action = `/products/${id}/stock`;
  document.getElementById("stockProductName").textContent = name;
  document.getElementById("currentStock").textContent = `${quantity} units`;
  document.getElementById("stockAmount").value = "";
  modal.classList.add("is-open");
  modal.setAttribute("aria-hidden", "false");
  document.body.classList.add("modal-open");
  document.getElementById("stockAmount").focus();
}
function closeStockModal() {
  const modal = document.getElementById("stockModal");
  if (!modal) return;
  modal.classList.remove("is-open");
  modal.setAttribute("aria-hidden", "true");
  document.body.classList.remove("modal-open");
}
document.addEventListener("keydown", event => {
  if (event.key === "Escape") closeStockModal();
});
document.addEventListener("click", event => {
  const modal = document.getElementById("stockModal");
  if (modal && event.target === modal) closeStockModal();
});
window.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".flash").forEach(flash => {
    setTimeout(() => {
      if (flash.isConnected) {
        flash.style.opacity = "0";
        setTimeout(() => flash.remove(), 300);
      }
    }, 5000);
  });
});
