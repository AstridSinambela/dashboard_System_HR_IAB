document.addEventListener("DOMContentLoaded", function () {
  const searchInput = document.getElementById("searchOperator");
  const table = document.getElementById("operatorTable");
  const rows = table.getElementsByTagName("tr");
  const autocompleteBox = document.getElementById("autocomplete-operator");

  // Filter tabel berdasarkan NIK
  function filterTable(query) {
    const filter = query.toLowerCase();
    for (let i = 1; i < rows.length; i++) {
      const nikCell = rows[i].getElementsByTagName("td")[1];
      const nameCell = rows[i].getElementsByTagName("td")[2];
      if (nikCell &&
         nameCell) {
        const nikValue = nikCell.textContent.toLowerCase();
        const nameValue = nameCell.textContent.toLowerCase();
        rows[i].style.display = (nikValue.includes(filter) || nameValue.includes(filter)) ? "" : "none";
      }
    }
  }

  // Autocomplete suggestion
  function showSuggestions(value) {
    autocompleteBox.innerHTML = "";
    autocompleteBox.classList.remove("active");
    if (!value) return;

    const rect = searchInput.getBoundingClientRect();
    autocompleteBox.style.top = rect.bottom + window.scrollY + "px";
    autocompleteBox.style.left = rect.left + window.scrollX + "px";
    autocompleteBox.style.width = rect.width + "px";

    const filtered = OPERATOR_LIST.filter(op =>
      op.nik.toLowerCase().includes(value.toLowerCase()) ||
      op.name.toLowerCase().includes(value.toLowerCase())
    );

    if (filtered.length > 0) {
      autocompleteBox.classList.add("active");
      filtered.slice(0, 8).forEach(op => {
        const item = document.createElement("div");
        const regex = new RegExp(`(${value})`, "gi");
        item.innerHTML = `${op.nik} - ${op.name}`.replace(regex, "<span class='autocomplete-highlight'>$1</span>");
        item.addEventListener("click", () => {
          searchInput.value = op.nik; // atau bisa `${op.nik} - ${op.name}`
          autocompleteBox.innerHTML = "";
          autocompleteBox.classList.remove("active");
          filterTable(op.nik);
        });
        autocompleteBox.appendChild(item);
      });
    }
  }

  searchInput.addEventListener("input", function () {
    showSuggestions(this.value);
    filterTable(this.value);
  });

  document.addEventListener("click", function (e) {
    if (e.target !== searchInput) {
      autocompleteBox.innerHTML = "";
      autocompleteBox.classList.remove("active");
    }
  });
});
