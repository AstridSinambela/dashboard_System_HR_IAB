// Login check
function checkLogin() {
  const loggedIn = localStorage.getItem("isLoggedIn");
  if (!loggedIn) {
    window.location.href = "login.html";
  }
}


// Update Status Badge dan Expired Date untuk Certification Table
  document.addEventListener("DOMContentLoaded", () => {
    const rows = document.querySelectorAll("#certificationTable tbody tr");
    rows.forEach(row => {
      const docInput = row.querySelector('td:nth-child(2) input');
      const trainingDateInput = row.querySelector('td:nth-child(4) input');
      const statusCell = row.querySelector('td:nth-child(3)');
      const expiredDateInput = row.querySelector('td:nth-child(5) input');

      function updateRowStatusAndDate() {
        const docFilled = docInput.value.trim() !== "";
        const trainFilled = trainingDateInput.value !== "";

        // Status update
        if (docFilled && trainFilled) {
          statusCell.innerHTML = `<span class="status-pass"><i class="bi bi-check-circle-fill"></i> Pass</span>`;
        } else {
          statusCell.innerHTML = `<span class="status-notyet"><i class="bi bi-x-circle-fill"></i> Not Yet</span>`;
        }

        // Expired Date update
        if (trainFilled) {
          expiredDateInput.value = calculateExpiredDate(trainingDateInput.value);
        } else {
          expiredDateInput.value = "";
        }
      }

      updateRowStatusAndDate();

      docInput.addEventListener("input", updateRowStatusAndDate);
      trainingDateInput.addEventListener("input", updateRowStatusAndDate);
    });

    // Upload Certification Table Logic
    const uploadInputs = document.querySelectorAll("#uploadCertTable .form-upload");
    uploadInputs.forEach(input => {
  input.addEventListener("change", () => {
    const row = input.closest("tr");
    const docNumber = row.querySelector('td:nth-child(2) input');
    const trainingDate = row.querySelector(".upload-training");
    const expiredDate = row.querySelector(".upload-expired");
    const fileUpload = row.querySelector(".form-upload");
    const statusCell = row.querySelector(".upload-status");

    const docFilled = docNumber.value.trim() !== "";
    const fileFilled = fileUpload.files.length > 0;
    const trainFilled = trainingDate.value !== "";
    const expFilled = expiredDate.value !== "";

    if (docFilled && fileFilled && trainFilled && expFilled) {
      statusCell.innerHTML = `<span class="status-pass"><i class="bi bi-check-circle-fill"></i> Pass</span>`;
    } else {
      statusCell.innerHTML = `<span class="status-notyet"><i class="bi bi-x-circle-fill"></i> Not Yet</span>`;
    }

    if (trainFilled) {
      expiredDate.value = calculateExpiredDate(trainingDate.value);
    } else {
      expiredDate.value = "";
    }
  });
});

   // Expired Date otomatis update saat training date berubah
    const trainingDateInputs = document.querySelectorAll(".upload-training");
    trainingDateInputs.forEach(trainingInput => {
      trainingInput.addEventListener("input", () => {
        const row = trainingInput.closest("tr");
        const expiredInput = row.querySelector(".upload-expired");

        if (trainingInput.value) {
          expiredInput.value = calculateExpiredDate(trainingInput.value);
        } else {
          expiredInput.value = "";
        }
      });
    });
  });

  // Helper untuk menghitung Expired Date +23 bulan
  function calculateExpiredDate(dateStr) {
    const date = new Date(dateStr);
    if (isNaN(date)) return "";
    date.setMonth(date.getMonth() + 23);
    const yyyy = date.getFullYear();
    const mm = String(date.getMonth() + 1).padStart(2, '0');
    const dd = String(date.getDate()).padStart(2, '0');
    return `${yyyy}-${mm}-${dd}`;
  }

  // New / Re-certification Handler
  function handleCertificationAction(actionType) {
    const label = document.getElementById("certificationStatusLabel");
    const certSection = document.getElementById("certificationEvaluation");

    // Get all input elements in the certification section
    const allInputs = certSection.querySelectorAll("input");

    // Section references
    const soldering = document.querySelector(".cert-soldering");
    const screwing = document.querySelector(".cert-screwing");
    const msa = document.querySelector(".cert-msa");
    const screening = document.querySelector(".cert-screening");
    const line = document.querySelector(".cert-line");

    // Reset all: disable inputs and mark all sections as disabled
    allInputs.forEach(input => input.setAttribute("disabled", true));
    [soldering, screwing, msa, screening, line].forEach(sec => sec.classList.add("cert-disabled"));
    certSection.classList.add("cert-disabled");


    if (actionType === "New Certification") {
    allInputs.forEach(input => input.removeAttribute("disabled"));
    [soldering, screwing, msa, screening, line].forEach(sec => sec.classList.remove("cert-disabled"));
    certSection.classList.remove("cert-disabled"); // ✅ aktifkan seluruh form
  } 
    else if (actionType === "Re-certification") {
       // Hanya aktifkan Soldering, Screwing, MSA
    [soldering, screwing, msa].forEach(sec => {
      sec.querySelectorAll("input").forEach(input => input.removeAttribute("disabled"));
      sec.classList.remove("cert-disabled");
    });

    // Tetap nonaktifkan Screening & Line
    [screening, line].forEach(sec => {
      sec.querySelectorAll("input").forEach(input => input.setAttribute("disabled", true));
      sec.classList.add("cert-disabled");
    });

     certSection.classList.remove("cert-disabled"); 
  }

  // Update label & scroll
  document.getElementById("certificationStatusLabel").style.display = "flex";
  document.getElementById("certSelectionText").innerHTML = `Selected: <span class="text-dark">${actionType}</span>`;
  document.getElementById("closeCertForm").style.display = "inline-block";
    certSection.scrollIntoView({ behavior: "smooth" });

  // Dropdown highlight
  const allItems = document.querySelectorAll('.dropdown-item');
  allItems.forEach(item => item.classList.remove('active-selection'));
  const selected = [...allItems].find(item => item.textContent.trim() === actionType);
  if (selected) selected.classList.add('active-selection');
}


 
document.addEventListener("DOMContentLoaded", () => {
   
  // Validasi file upload (PDF dan max 1MB)
  const fileInputs = document.querySelectorAll('input[type="file"]');
  fileInputs.forEach(input => {
    input.addEventListener("change", () => {
      const file = input.files[0];
      if (file) {
        const fileType = file.type;
        const fileSize = file.size;

        if (fileType !== "application/pdf") {
          alert("Only PDF files are allowed.");
          input.value = "";
          return;
        }

        if (fileSize > 1024 * 1024) {
          alert("File size must be less than or equal to 1 MB.");
          input.value = "";
          return;
        }
      }
    });
  });

  });


// Fungsi update hasil score
function updateScore(sectionClass, minInputs, resultIndex) {
  const container = document.querySelector(sectionClass);
  if (!container) return;
  
  const inputs = container.querySelectorAll('input.form-control');
  const values = Array.from(inputs)
    .slice(0, minInputs)
    .map(i => parseFloat(i.value));

  const resultField = inputs[resultIndex];

  if (values.some(v => isNaN(v))) {
    resultField.value = "";
    resultField.classList.remove("input-result-pass", "input-result-fail");
    return;
  }
  // Hitung hasil dan apply warna
  const isPass = values.every(v => v >= 80);
  resultField.value = isPass ? "Pass" : "Not Pass";
  applyResultColor(resultField, resultField.value);
}

//update tiap input di section aktif
function attachScoreListeners() {
  updateScore('.cert-soldering', 2, 2);  // indexes: written(0), practical(1), result(2)
  updateScore('.cert-screwing', 2, 2);   // technique(0), work(1), result(2)
}

document.addEventListener("input", (e) => {
  if (e.target.closest('.cert-soldering')) updateScore('.cert-soldering', 2, 2);
  if (e.target.closest('.cert-screwing')) updateScore('.cert-screwing', 2, 2);
});

// aktifkan form, listener otomatis jalan
document.querySelectorAll('.dropdown-item').forEach(item => {
  item.addEventListener("click", () => {
    setTimeout(attachScoreListeners, 50);
  });
});

function evaluateMSAResult() {
  const [accuracy, missRate, falseAlarm, confidence] = document.querySelectorAll(".msa-score");

  const accVal = parseFloat(accuracy.value);
  const missVal = parseFloat(missRate.value);
  const falseVal = parseFloat(falseAlarm.value);
  const confVal = parseFloat(confidence.value);

  const resultField = document.getElementById("msa-result");

  // Pastikan input valid dulu
  if (
    isNaN(accVal) || isNaN(missVal) ||
    isNaN(falseVal) || isNaN(confVal)
  ) {
    resultField.value = "";
    return;
  }

  const isPass =
    accVal >= 90 &&
    missVal <= 2 &&
    falseVal <= 5 &&
    confVal >= 90;

  resultField.value = isPass ? "Pass" : "Not Pass";
  applyResultColor(resultField, resultField.value);
}

// Attach listener ke semua input .msa-score
document.addEventListener("input", (e) => {
  if (e.target.classList.contains("msa-score")) {
    evaluateMSAResult();
  }
});

  // Apply color based on result
  function applyResultColor(field, value) {
  field.classList.remove("input-result-pass", "input-result-fail");

  if (value === "Pass") {
    field.classList.add("input-result-pass");
  } else if (value === "Not Pass") {
    field.classList.add("input-result-fail");
  }
}

// Data Screening Evaluation
function evaluateScreeningResult() {
  const screeningSection = document.querySelector(".cert-screening");
  if (!screeningSection) return;

  const inputs = screeningSection.querySelectorAll("input");
  const tiu = parseFloat(inputs[0].value);
  const accu = parseFloat(inputs[1].value);
  const heco = parseFloat(inputs[2].value);
  const mcc = parseFloat(inputs[3].value);
  const resultInput = inputs[4];

  // Validasi input
  if ([tiu, accu, heco, mcc].some(isNaN)) {
    resultInput.value = "";
    resultInput.classList.remove("input-result-pass", "input-result-fail");
    return;
  }

  const isPass = tiu >= 14 && accu >= 55 && heco >= 80 && mcc >= 80;
  resultInput.value = isPass ? "Pass" : "Not Pass";
  applyResultColor(resultInput, resultInput.value);
}

document.addEventListener("input", (e) => {
  if (e.target.closest(".cert-screening")) {
    evaluateScreeningResult();
  }
});


// Close Certification Form
document.getElementById("closeCertForm").addEventListener("click", () => {
  const certSection = document.getElementById("certificationEvaluation");
  const allInputs = certSection.querySelectorAll("input");
  const labelContainer = document.getElementById("certificationStatusLabel");
  const labelText = document.getElementById("certSelectionText");
  const closeButton = document.getElementById("closeCertForm");

  // Reset semua input dan styling
  allInputs.forEach(input => {
    input.value = "";
    input.setAttribute("disabled", true);
    input.classList.remove("input-result-pass", "input-result-fail");
  });

  // Disable semua section
  document.querySelectorAll(".cert-soldering, .cert-screwing, .cert-msa, .cert-screening, .cert-line")
    .forEach(section => section.classList.add("cert-disabled"));

  // Disable form wrapper
  certSection.classList.add("cert-disabled");

  // Sembunyikan selected label dan tombol close
  labelText.innerHTML = "";
  labelContainer.style.display = "none";
  closeButton.style.display = "none";

  // Hapus highlight dropdown
  document.querySelectorAll(".dropdown-item").forEach(item => {
    item.classList.remove("active-selection");
  });
});

let uploadDocDate = ""; // Disimpan di memori

document.addEventListener("DOMContentLoaded", () => {
  const evalFileInput = document.getElementById("evalFile");

  // Simpan tanggal saat user pilih file
  evalFileInput.addEventListener("change", () => {
    const now = new Date();
    const yyyy = now.getFullYear();
    const mm = String(now.getMonth() + 1).padStart(2, '0');
    const dd = String(now.getDate()).padStart(2, '0');
    uploadDocDate = `${yyyy}${mm}${dd}`;
  });

  const generateBtn = document.querySelector(".btn-custom.w-100");
  const resultField = document.getElementById("generatedEvalNo");

  generateBtn.addEventListener("click", () => {
    const nik = document.getElementById("nik").value.trim();
    const line = document.getElementById("line").value.trim();

    if (!nik || !line) {
      alert("Please fill NIK and Line first");
      return;
    }

     // Validasi NIK harus 8 digit angka
  if (!/^\d{8}$/.test(nik)) {
    alert("NIK must be exactly 8 digits.");
    return;
  }

    if (!uploadDocDate) {
      alert("Please upload the document first");
      return;
    }

    const finalCode = `PD–IAB–${line}–${nik}–${uploadDocDate}`;
    resultField.textContent = finalCode;
  });
});

// Menyalin nilai Nomor Document dan Training Date dari form certification skill kedua ke form pertama
document.addEventListener("DOMContentLoaded", function () {
  const uploadTableRows = document.querySelectorAll("#uploadCertTable tbody tr");
  const certTableRows = document.querySelectorAll("#certificationTable tbody tr");
  const docInputs = document.querySelectorAll(".form-upload-docno");  
  const trainingInputs = document.querySelectorAll(".upload-training");
  const expiredInputs = document.querySelectorAll(".upload-expired");
  const uploadFileInputs = document.querySelectorAll(".form-upload");

  uploadTableRows.forEach((uploadRow, index) => {
    const docUpload = uploadRow.querySelector(".form-upload-docno");
    const trainingUpload = uploadRow.querySelector(".upload-training");
    const expiredUpload = uploadRow.querySelector(".upload-expired");

    const docDisplay = certTableRows[index].querySelector(".form-cert-display-docno");
    const trainingDisplay = certTableRows[index].querySelector(".form-cert-display-training");
    const expiredDisplay = certTableRows[index].querySelector(".form-cert-display-expired");
    const statusCell = certTableRows[index].querySelector('td:nth-child(3)');

    docUpload.addEventListener("input", () => {
      docDisplay.value = docUpload.value;

      // Trigger status update
      const docFilled = docDisplay.value.trim() !== "";
      const trainFilled = trainingDisplay.value !== "";
      statusCell.innerHTML = (docFilled && trainFilled)
        ? `<span class="status-pass"><i class="bi bi-check-circle-fill"></i> Pass</span>`
        : `<span class="status-notyet"><i class="bi bi-x-circle-fill"></i> Not Yet</span>`;
    });

    trainingUpload.addEventListener("input", () => {
      trainingDisplay.value = trainingUpload.value;
      expiredDisplay.value = expiredUpload.value;

      // Trigger status update
      const docFilled = docDisplay.value.trim() !== "";
      const trainFilled = trainingDisplay.value !== "";
      statusCell.innerHTML = (docFilled && trainFilled)
        ? `<span class="status-pass"><i class="bi bi-check-circle-fill"></i> Pass</span>`
        : `<span class="status-notyet"><i class="bi bi-x-circle-fill"></i> Not Yet</span>`;
    });

    // Sync saat halaman dimuat
    docDisplay.value = docUpload.value;
    trainingDisplay.value = trainingUpload.value;
    expiredDisplay.value = expiredUpload.value;

    // Trigger status saat load juga
    const docFilled = docDisplay.value.trim() !== "";
    const trainFilled = trainingDisplay.value !== "";
    statusCell.innerHTML = (docFilled && trainFilled)
      ? `<span class="status-pass"><i class="bi bi-check-circle-fill"></i> Pass</span>`
      : `<span class="status-notyet"><i class="bi bi-x-circle-fill"></i> Not Yet</span>`;
  });
  docInputs.forEach(input => input.addEventListener("input", updateUploadTableStatus));
trainingInputs.forEach(input => input.addEventListener("input", updateUploadTableStatus));
expiredInputs.forEach(input => input.addEventListener("input", updateUploadTableStatus));
uploadFileInputs.forEach(input => input.addEventListener("change", updateUploadTableStatus));

// Jalankan juga saat halaman pertama kali diload
updateUploadTableStatus();
});

function updateUploadTableStatus() {
  const rows = document.querySelectorAll("#uploadCertTable tbody tr");

  rows.forEach(row => {
    const docInput = row.querySelector('.form-upload-docno');
    const fileInput = row.querySelector('.form-upload');
    const trainingInput = row.querySelector('.upload-training');
    const expiredInput = row.querySelector('.upload-expired');
    const statusCell = row.querySelector('.upload-status');

    const docFilled = docInput.value.trim() !== "";
    const fileFilled = fileInput.files.length > 0;
    const trainingFilled = trainingInput.value !== "";
    const expiredFilled = expiredInput.value !== "";

    if (docFilled && fileFilled && trainingFilled && expiredFilled) {
      statusCell.innerHTML = `<span class="status-pass"><i class="bi bi-check-circle-fill"></i> Pass</span>`;
    } else {
      statusCell.innerHTML = `<span class="status-notyet"><i class="bi bi-x-circle-fill"></i> Not Yet</span>`;
    }
  });
}

// VALIDASI NIK
function validateNIK() {
  const nikInput = document.getElementById("nik");
  const nikValue = nikInput.value.trim();

  if (!/^\d*$/.test(nikValue)) {
    alert("NIK must contain only numeric digits.");
    nikInput.value = nikValue.replace(/\D/g, "");
    return;
  }

  if (nikValue.length > 8) {
    alert("NIK must be exactly 8 digits.");
    nikInput.value = nikValue.slice(0, 8);
    return;
  }

  if (nikValue.length < 8 && nikValue.length !== 0) {
    nikInput.setCustomValidity("NIK must be exactly 8 digits.");
  } else {
    nikInput.setCustomValidity("");
  }
}

// document.getElementById("search-nik-btn").addEventListener("click", fetchOperator);

// document.getElementById("line").value = data.line || "";

// FETCH DATA OPERATOR
async function fetchOperator() {
  const nikInput = document.getElementById("nik");
  const nik = nikInput.value.trim();
  const spinner = document.getElementById("spinner");
  const button = document.getElementById("search-nik-btn");
 
  // console.log("Fetching operator for NIK:", nik);  // ✅ Debug log

   if (!nik || nik.length !== 8) {
    showTooltip(nikInput, "Please enter a valid 8-digit NIK");
      return;
  }

   // Aktifkan spinner dan disable tombol
  spinner.style.display = "inline-block";
  button.disabled = true;

  try {
    const response = await fetch(`/api/full-profile?nik=${encodeURIComponent(nik)}`);
    if (!response.ok) throw new Error("Data not found");

    const data = await response.json();
    updateOperatorProfile(data.operator);
    populateCertifications(data.certifications);
    //populateEvaluations(data.evaluations);

    console.log("Data received:", data);  // ✅ Debug log   
          
    // Tampilkan data
    // updateOperatorProfile(data);

    function populateCertifications(certifications) {
  const certTypes = ["soldering", "screwing", "msa"];

  certifications.forEach((cert, index) => {
    const type = cert.type.toLowerCase();
    const docInputs = document.querySelectorAll(".form-cert-display-docno");
    const trainInputs = document.querySelectorAll(".form-cert-display-training");
    const expInputs = document.querySelectorAll(".form-cert-display-expired");
    // Tidak perlu ambil statusSpans jika tidak digunakan
    // const statusSpans = document.querySelectorAll("td span.status-notyet");

    if (certTypes.includes(type)) {
      const i = certTypes.indexOf(type);

      docInputs[i].value = cert.doc_no || "";
      trainInputs[i].value = cert.training_date || "";
      expInputs[i].value = cert.expired_date || "";

         }
  });
}


  } catch (err) {
    console.error("Fetch error:", err);
    resetOperatorProfile();
    showTooltip(nikInput, "Operator not found");
   } finally {
    // Sembunyikan spinner dan aktifkan tombol
    spinner.style.display = "none";
    button.disabled = false;
  }
  
  fetch('/api/update-line', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        nik: document.getElementById('nik').value,
        line: document.getElementById('line').value
    })
})

  }


// UPDATE PROFIL OPERATOR
function updateOperatorProfile(data) {
  document.getElementById("name").value = data.name || "";
  document.getElementById("line").value = data.line || "";
  document.getElementById("job-level").value = data.level || "";
  document.getElementById("contract-status").value = data.contract_status || "";
  // document.getElementById("end-date").value = data.end_contract_date || "";

  const endDateInput = document.getElementById("end-date");
  if (data.contract_status && data.contract_status.toLowerCase() === "permanen") {
  endDateInput.value = "";
  endDateInput.placeholder = "-";
} else {
  // Format ke MM/DD/YYYY jika ada tanggal
  if (data.end_contract_date) {
    const dateObj = new Date(data.end_contract_date);
    const formattedDate = `${String(dateObj.getMonth() + 1).padStart(2, '0')}/${String(dateObj.getDate()).padStart(2, '0')}/${dateObj.getFullYear()}`;
    endDateInput.value = formattedDate;
  } else {
    endDateInput.value = "";
  }
  endDateInput.placeholder = "";
}


  const photoImg = document.getElementById("photo-preview");
  if (data.photo) {
    photoImg.src = data.photo; // base64
  } else {
    photoImg.src = "assets/img/profile-iconn.png"; // fallback image
  }
}

// RESET PROFIL OPERATOR
function resetOperatorProfile() {
  document.getElementById("name").value = "";
  document.getElementById("line").value = "";
  document.getElementById("job-level").value = "";
  document.getElementById("contract-status").value = "";
  document.getElementById("end-date").value = "";
  document.getElementById("photo-preview").src = "assets/img/profile-iconn.png";
}

// INIT SEMUA EVENT
function setupEventListeners() {
  const nikInput = document.getElementById("nik");
  const searchBtn = document.getElementById("search-nik-btn");

  if (nikInput) {
    nikInput.addEventListener("input", validateNIK);
    nikInput.addEventListener("keyup", (e) => {
      if (e.key === "Enter") fetchOperator();
    });
  }
  
  if (searchBtn) {
    searchBtn.addEventListener("click", fetchOperator);
  }

  nikInput.addEventListener("input", () => {
  const tooltip = bootstrap.Tooltip.getInstance(nikInput);
  if (tooltip) tooltip.hide();
  nikInput.classList.remove("is-invalid");
});
}

// JALANKAN SAAT DOKUMEN SIAP
document.addEventListener("DOMContentLoaded", () => {
  
  // Inisialisasi semua elemen dengan data-bs-toggle="tooltip"
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.forEach(el => new bootstrap.Tooltip(el));
  setupEventListeners();
});

// TAMPILKAN TOOLTIP ERROR
function showTooltip(inputEl, message) {
  inputEl.setAttribute("data-bs-original-title", message);
  inputEl.setAttribute("data-bs-placement", "top");
  inputEl.setAttribute("data-bs-toggle", "tooltip");

  const tooltip = bootstrap.Tooltip.getInstance(inputEl) || new bootstrap.Tooltip(inputEl);
  
  tooltip.show();
  inputEl.classList.add("is-invalid");

  // Sembunyikan setelah sekian detik
  setTimeout(() => {
    tooltip.hide();
    inputEl.classList.remove("is-invalid");
  }, 5000);
}

function toggleLineEdit() {
  const btn = document.getElementById("update-line-btn");
  const lineInput = document.getElementById("line");
  const nik = document.getElementById("nik").value;

  const isEditing = btn.getAttribute("data-editing") === "true";

  if (!isEditing) {
    // Enable edit mode
    lineInput.removeAttribute("readonly");
    lineInput.focus();
    btn.innerText = "Save";
    btn.setAttribute("data-editing", "true");
  } else {
    // Save mode
    const newLine = lineInput.value;

    fetch(`/api/update-line`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ nik: nik, line: newLine }),
    })
      .then((res) => {
        if (!res.ok) throw new Error("Failed to update line");
        return res.json();
      })
      .then((data) => {
        alert("Line updated successfully.");
        lineInput.setAttribute("readonly", true);
        btn.innerText = "Update Line";
        btn.setAttribute("data-editing", "false");
      })
      .catch((err) => {
        alert("Error: " + err.message);
      });
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const processSelect = document.querySelector(".cert-line-process");
  const targetInput = document.querySelector(".cert-line-target");
  const actualInput = document.querySelector(".cert-line-actual");
  const achievementInput = document.querySelector(".cert-line-achievement");
  const resultInput = document.querySelector(".cert-line-result");

  const targetMap = {
    "OPT#1": 84.1,
    "OPT#2": 66.8,
    "OPT#3": 126.3,
    "OPT#4": 204.4,
  };

  // Update Target saat OPT dipilih
  processSelect.addEventListener("change", () => {
    const selected = processSelect.value;
    const target = targetMap[selected] || "";

    targetInput.value = target;

    // Reset kolom lain
    actualInput.value = "";
    achievementInput.value = "";
    resultInput.value = "";
    resultInput.classList.remove("input-result-pass", "input-result-fail");

    // Enable kolom actual jika proses dipilih
    actualInput.disabled = !selected;
  });

  // Kalkulasi otomatis saat input actual diketik
  actualInput.addEventListener("input", () => {
    const target = parseFloat(targetInput.value);
    const actual = parseFloat(actualInput.value);

    if (!target || !actual || actual === 0) {
      achievementInput.value = "";
      resultInput.value = "";
      resultInput.classList.remove("input-result-pass", "input-result-fail");
      return;
    }

    const achievement = (target / actual) * 100;
    const isPass = achievement >= 100;

    achievementInput.value = achievement.toFixed(1) + " %";
    resultInput.value = isPass ? "Pass" : "Not Pass";

    resultInput.classList.remove("input-result-pass", "input-result-fail");
    resultInput.classList.add(isPass ? "input-result-pass" : "input-result-fail");
  });
});

document.getElementById("submit-btn").addEventListener("click", async () => {
  const nik = document.getElementById("nik").value.trim();
  const line = document.getElementById("line").value.trim();
  const name = document.getElementById("name").value.trim();
  const jobLevel = document.getElementById("job-level").value.trim();
  const contractStatus = document.getElementById("contract-status").value.trim();
  const endDate = document.getElementById("end-date").value.trim();
  const evalCode = document.getElementById("generatedEvalNo").innerText.trim();

  if (!nik || !line) {
    alert("NIK and Line must be filled.");
    return;
  }

  const formData = new FormData();
  formData.append("nik", nik);
  formData.append("line", line);
  formData.append("name", name);
  formData.append("job_level", jobLevel);
  formData.append("contract_status", contractStatus);
  formData.append("end_contract_date", endDate);
  formData.append("eval_code", evalCode);

  // Tanggal upload otomatis
  const now = new Date();
  formData.append("upload_date", now.toISOString());

  // Upload file dari evaluasi
  const reportInputs = document.querySelectorAll(".form-upload");
  reportInputs.forEach((input, index) => {
    if (input.files[0]) {
      formData.append(`report_file_${index}`, input.files[0]);
    }
  });

  try {
    const res = await fetch("/api/profile/submit", {
      method: "POST",
      body: formData,
    });

    const result = await res.json();
    if (res.ok) {
      alert("Data successfully saved.");
    } else {
      alert("Error: " + result.message);
    }
  } catch (err) {
    alert("Failed to submit: " + err.message);
  }
});

  // Logout function
  function logout() {
    localStorage.removeItem("isLoggedIn");
    window.location.href = "login.html";
  }