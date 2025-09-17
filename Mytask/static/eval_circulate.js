document.addEventListener("DOMContentLoaded", function () {
  const searchInput = document.getElementById("search-cos");
  const suggestionsBox = document.getElementById("suggestions");
  const rows = document.querySelectorAll(".table-row");

  // 🔍 filter table
  function filterTable(query) {
    const filter = query.toLowerCase();
    rows.forEach(row => {
      const cosCell = row.querySelector("div:first-child");
      if (cosCell) {
        const textValue = cosCell.textContent || cosCell.innerText;
        row.style.display = textValue.toLowerCase().includes(filter) ? "" : "none";
      }
    });
  }

  // 🔽 tampilkan suggestion
    function showSuggestions(value) {
        suggestionsBox.innerHTML = "";
        suggestionsBox.style.display = "none";
        if (!value) return;

        const rect = searchInput.getBoundingClientRect();
        suggestionsBox.style.top = rect.bottom + window.scrollY + "px";
        suggestionsBox.style.left = rect.left + window.scrollX + "px";
        suggestionsBox.style.width = rect.width + "px";

        const filtered = ID_COS_LIST.filter(id => id.toLowerCase().includes(value.toLowerCase()));
        if (filtered.length > 0) {
            suggestionsBox.style.display = "block";
            filtered.slice(0, 10).forEach(id => {
            const item = document.createElement("div");
            const regex = new RegExp(`(${value})`, "gi");
            item.innerHTML = id.replace(regex, "<span class='autocomplete-highlight'>$1</span>");
            item.addEventListener("click", () => {
                searchInput.value = id;
                suggestionsBox.style.display = "none";
                filterTable(id);
            });
            suggestionsBox.appendChild(item);
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
      suggestionsBox.innerHTML = "";
      suggestionsBox.style.display = "none";
    }
  });
});
