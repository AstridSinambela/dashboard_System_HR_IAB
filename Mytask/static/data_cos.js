document.addEventListener("DOMContentLoaded", function () {
  const searchInput = document.getElementById("searchInput");
  const table = document.getElementById("cosTable");
  const tbody = table.querySelector("tbody");
  const rows = table.getElementsByTagName("tr");
  const autocompleteBox = document.getElementById("autocomplete-list");

  // 🌐 WebSocket
  const wsProtocol = location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${wsProtocol}://${location.host}/ws/cos`);

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.event === "new_cos") {
      console.log("📥 COS baru:", msg);

      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><a href="/issuer/detail_cos?id_cos=${msg.id_cos}" target="content_is">${msg.id_cos}</a></td>
        <td>${msg.creator_name || "-"}</td>
        <td>${new Date(msg.created_at).toLocaleString()}</td>
        <td>${msg.updater_name || "-"}</td>
        <td>${msg.updated_at ? new Date(msg.updated_at).toLocaleString() : "-"}</td>
        <td>${msg.status}</td>
        <td>${msg.total_opt ?? 0}</td>
      `;
      tbody.prepend(tr);
    }
  };

  // 🔍 filter tabel
  function filterTable(query) {
    const filter = query.toLowerCase();
    for (let i = 1; i < rows.length; i++) {
      const cell = rows[i].getElementsByTagName("td")[0]; // kolom ID COS
      if (cell) {
        const textValue = cell.textContent || cell.innerText;
        rows[i].style.display = textValue.toLowerCase().indexOf(filter) > -1 ? "" : "none";
      }
    }
  }

  // 🔽 tampilkan suggestion
  function showSuggestions(value) {
    autocompleteBox.innerHTML = "";
    autocompleteBox.classList.remove("active");
    if (!value) return;

    const rect = searchInput.getBoundingClientRect();
    autocompleteBox.style.top = rect.bottom + window.scrollY + "px";
    autocompleteBox.style.left = rect.left + window.scrollX + "px";
    autocompleteBox.style.width = rect.width + "px";

    const filtered = ID_COS_LIST.filter(id => id.toLowerCase().includes(value.toLowerCase()));
    if (filtered.length > 0) {
      autocompleteBox.classList.add("active");
      filtered.slice(0, 10).forEach(id => {
        const item = document.createElement("div");
        const regex = new RegExp(`(${value})`, "gi");
        item.innerHTML = id.replace(regex, "<span class='autocomplete-highlight'>$1</span>");
        item.addEventListener("click", () => {
          searchInput.value = id;
          autocompleteBox.innerHTML = "";
          autocompleteBox.classList.remove("active");
          filterTable(id);
        });
        autocompleteBox.appendChild(item);
      });
    }
  }

  // event: ketik di input
  searchInput.addEventListener("input", function () {
    showSuggestions(this.value);
    filterTable(this.value);
  });

  // event: klik luar → tutup suggestion
  document.addEventListener("click", function (e) {
    if (e.target !== searchInput) {
      autocompleteBox.innerHTML = "";
      autocompleteBox.classList.remove("active");
    }
  });
});
