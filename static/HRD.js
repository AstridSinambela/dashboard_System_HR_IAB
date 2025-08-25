// Login check
function checkLogin() {
  const loggedIn = localStorage.getItem("isLoggedIn");
  if (!loggedIn) {
    window.location.href = "login.html";
  }
}

// Highlight active nav link
document.addEventListener("DOMContentLoaded", function () {
  const normalizePath = (path) => path.replace(/\/+$/, ""); // hapus slash di akhir
  const currentPath = normalizePath(window.location.pathname);
  const navLinks = document.querySelectorAll(".offcanvas-body .nav-link");

  navLinks.forEach(link => {
    const linkPath = normalizePath(link.getAttribute("href"));
    if (linkPath === currentPath) {link.classList.add("active");    }
    console.log("path:", window.location.pathname);

  });

   if (localStorage.getItem("showToast") === "true") {
    alert("Data berhasil disimpan!"); // atau munculkan toast
    localStorage.removeItem("showToast");
  }
});

// >>> helper: ubah "YYYY-MM-DD" atau Date ke "MM/DD/YYYY"
function formatDateToMMDDYYYY(dateStr) {
  if (!dateStr) return "";
  const [year, month, day] = dateStr.split("-");
  return `${month}/${day}/${year}`;
}

// ==================== Upload File ====================
function fileToBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result.split(",")[1]);
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}

// Upload file to server
async function uploadFile(nik, index, certificationType) {
  const fileInput    = document.querySelectorAll(".form-upload")[index];
  const docNo        = document.querySelectorAll(".form-upload-docno")[index].value;
  const trainingDate = document.querySelectorAll(".upload-training")[index].value;
  const expiredDate  = document.querySelectorAll(".upload-expired")[index].value;
  const statusSpan   = document.querySelectorAll(".upload-status span")[index];
  const status       = statusSpan?.innerText.includes("Pass") ? "Pass" : "Not Yet";

  const file = fileInput.files[0];
  if (!file) {
    console.warn(`No file selected for ${certificationType}`);
    return;
  }

  const base64File = await fileToBase64(file);

  // >>> payload sesuai tipe + tanggal ke MM/DD/YYYY
  let payload = { nik, status };
  const t = formatDateToMMDDYYYY(trainingDate);
  const e = formatDateToMMDDYYYY(expiredDate);

  if (certificationType === "Soldering") {
    Object.assign(payload, {
      soldering_docno: docNo,
      soldering_traindate: t,
      soldering_expdate: e,
      file_soldering: base64File
    });
  } else if (certificationType === "Screwing") {
    Object.assign(payload, {
      screwing_docno: docNo,
      screwing_traindate: t,
      screwing_expdate: e,
      file_screwing: base64File
    });
  } else if (certificationType === "MSA") {
    Object.assign(payload, {
      msa_docno: docNo,
      msa_traindate: t,
      msa_expdate: e,
      file_msa: base64File
    });
  } else {
    console.warn("Unknown certificationType:", certificationType);
  }

  const res = await fetch("/api/certification/upload", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(payload)
  });

  if (!res.ok) throw new Error(`Failed to upload file for ${certificationType}`);
  console.log(`${certificationType} file uploaded successfully.`);
}

// ==================== Validasi Sebelum Simpan ====================

function validateBeforeSave() {
  const errors = [];

  function isPassValue(val) {
    if (!val) return false;
    return String(val).trim().toLowerCase() === "pass";
  }

  // 1) Soldering
  const solderingSection = document.querySelector(".cert-soldering");
  let solderingResult = "";
  if (solderingSection) {
    const inputs = solderingSection.querySelectorAll("input");
    if (inputs.length >= 3) solderingResult = inputs[2].value || "";
  }
  if (!isPassValue(solderingResult)) errors.push("Soldering result is Not Pass or empty");

  // 2) Screwing
  const screwingSection = document.querySelector(".cert-screwing");
  let screwingResult = "";
  if (screwingSection) {
    const inputs = screwingSection.querySelectorAll("input");
    if (inputs.length >= 3) screwingResult = inputs[2].value || "";
  }
  if (!isPassValue(screwingResult)) errors.push("Screwing result is Not Pass or empty.");

  // 3) Data Screening (index 4)
  const screeningSection = document.querySelector(".cert-screening");
  let screeningResult = "";
  if (screeningSection) {
    const inputs = screeningSection.querySelectorAll("input");
    if (inputs.length >= 5) screeningResult = inputs[4].value || "";
  }
  if (!isPassValue(screeningResult)) errors.push("Data Screening result is Not Pass or empty.");

  // 4) Line Simulation (.cert-line-result)
  const lineResultEl = document.querySelector(".cert-line-result");
  const lineResult = lineResultEl ? (lineResultEl.value || "") : "";
  if (!isPassValue(lineResult)) errors.push("Line Simulation result is Not Pass or empty.");

  // 5) MSA (#msa-result)
  const msaEl = document.getElementById("msa-result");
  const msaResult = msaEl ? (msaEl.value || "") : "";
  if (!isPassValue(msaResult)) errors.push("MSA Assessment result is Not Pass or empty.");

  // 6) Certification Skills statuses (table)
  const certRows = document.querySelectorAll("#uploadCertTable tbody tr");
  if (!certRows || certRows.length === 0) {
    errors.push("Certification Skills table not found or empty.");
  } else {
    certRows.forEach((row, idx) => {
      const certNameCell = row.querySelector("td:first-child");
      const certName = certNameCell ? certNameCell.textContent.trim() : `Certification ${idx+1}`;
      const statusSpan = row.querySelector(".upload-status span");
      // gunakan textContent dan trim
      const statusText = statusSpan ? statusSpan.textContent.trim() : "";
      if (!isPassValue(statusText)) {
        errors.push(`${certName} status is Not Yet`);
      }
    });
  }

  if (errors.length > 0) {
    let msg = "Cannot save. The following items must be Pass:\n\n";
    msg += errors.map((s, i) => `${i+1}. ${s}`).join("\n");
    alert(msg);
    console.log("Validation errors:", errors);
    return false;
  }

  return true;
}

// =============== Score Calculation ===============
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

let uploadDocDate = ""; // Disimpan di memori

// =============== Line Simulation ===============
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

// =============== Expired Date ===============
document.addEventListener("DOMContentLoaded", () => {
  const trainingInputs = document.querySelectorAll(".upload-training");
  const expiredInputs = document.querySelectorAll(".upload-expired");

  trainingInputs.forEach((trainingInput, index) => {
    trainingInput.addEventListener("change", () => {
      const trainingDate = new Date(trainingInput.value);
      if (!isNaN(trainingDate.getTime())) {
        // Tambah 23 bulan
        const expiredDate = new Date(trainingDate);
        expiredDate.setMonth(expiredDate.getMonth() + 23);

        // Format YYYY-MM-DD
        const yyyy = expiredDate.getFullYear();
        const mm = String(expiredDate.getMonth() + 1).padStart(2, '0');
        const dd = String(expiredDate.getDate()).padStart(2, '0');
        expiredInputs[index].value = `${yyyy}-${mm}-${dd}`;
      } else {
        expiredInputs[index].value = "";
      }
    });
  });
});

// =============== Status ===============
document.addEventListener("DOMContentLoaded", () => {
  const table = document.querySelector("#uploadCertTable");
  const rows = table.querySelectorAll("tbody tr");

  rows.forEach(row => {
  const docNoInput = row.querySelector(".form-upload-docno");
  const fileInput = row.querySelector(".form-upload");
  const trainInput = row.querySelector(".upload-training");
  const expireInput = row.querySelector(".upload-expired");
  const statusCell = row.querySelector(".upload-status");

  const checkStatus = () => {
    const isDocFilled = docNoInput.value.trim() !== "";
    const isFileFilled = fileInput.files.length > 0;
    const isTrainFilled = trainInput.value.trim() !== "";
    const isExpireFilled = expireInput.value.trim() !== "";

    const isPdf = fileInput.files[0]?.type === "application/pdf";
    const isSizeValid = fileInput.files[0]?.size <= 1024 * 1024;
    const isFileValid = isPdf && isSizeValid;

    if (isDocFilled && isFileFilled && isFileValid && isTrainFilled && isExpireFilled) {
      statusCell.innerHTML = `<span class="status-pass"><i class="bi bi-check-circle-fill"></i> Pass</span>`;
    } else {
      statusCell.innerHTML = `<span class="status-notyet"><i class="bi bi-x-circle-fill"></i> Not Yet</span>`;
    }
  };

  [docNoInput, fileInput, trainInput, expireInput].forEach(input => {
    input.addEventListener("input", checkStatus);
    input.addEventListener("change", checkStatus);
  });

  // ✅ PANGGIL DI SINI AGAR VARIABEL ADA
  checkStatus();
});

  });



// =============== Upload Documents Button ===============
document.addEventListener("DOMContentLoaded", () => {
  const uploadButtons = document.querySelectorAll(".btn-upload-trigger");

  uploadButtons.forEach((button) => {
    const row = button.closest("tr");
    const fileInput = row.querySelector(".form-upload");
    const progressContainer = row.querySelector(".progress");
    const progressBar = row.querySelector(".progress-bar");

    // Klik tombol = buka file input
    button.addEventListener("click", () => {
      fileInput.click();
    });

    // Saat file dipilih
    fileInput.addEventListener("change", () => {
      const file = fileInput.files[0];
      if (!file) return;

      // Validasi
      if (file.type !== "application/pdf") {
        alert("Only PDF files are allowed.");
        fileInput.value = "";
        fileInput.dataset.valid = "false";
        return;
      }
      if (file.size > 1024 * 1024) {
        alert("File size must be less than or equal to 1 MB.");
        fileInput.value = "";
        fileInput.dataset.valid = "false";
        return;
      }
      fileInput.dataset.valid = "true";
      fileInput.dispatchEvent(new Event("input", { bubbles: true }));

      // Reset progress bar
      progressContainer.classList.remove("d-none");
      progressBar.style.width = "0%";
      progressBar.innerText = "0%";
      button.disabled = true;

      // Simulasi upload progress
      let progress = 0;
      const fakeUpload = setInterval(() => {
        if (progress >= 100) {
          clearInterval(fakeUpload);
          button.disabled = false;
          progressBar.style.width = "100%";
          progressBar.innerText = "100%";
          progressContainer.classList.add("d-none");

          // Ganti isi tombol dengan nama file
          button.querySelector(".btn-label").innerText = file.name;
        
        //fileToBase64(file).then((base64Data) => {
        //attachViewButton(row, base64Data);
      //});

        } else {
          progress += 10;
          progressBar.style.width = progress + "%";
          progressBar.innerText = progress + "%";
        }
      }, 100);

      
    });
    
    // Open base64 PDF in a new window
 function openBase64Pdf(base64) {
  const binary = atob(base64);
  const len = binary.length;
  const buffer = new Uint8Array(len);
  for (let i = 0; i < len; i++) {
    buffer[i] = binary.charCodeAt(i);
  }
  const blob = new Blob([buffer], { type: "application/pdf" });
  const url = URL.createObjectURL(blob);
  window.open(url, "_blank");
}


  });
});




// =============== SEARCH BY NIK (COMBINED ENDPOINT)  ===============
document.addEventListener("DOMContentLoaded", () => {
    const searchBtn = document.getElementById("search-nik-btn");
    const nikInput = document.getElementById("nik");
    const nikTooltip = document.getElementById("nik-tooltip");

    const nameInput = document.getElementById("name");
    const lineInput = document.getElementById("line");
    const levelInput = document.getElementById("job-level");
    const contractStatusInput = document.getElementById("contract-status");
    const endDateInput = document.getElementById("end-date");
    const photoPreview = document.getElementById("photo-preview");
    const alertBox = document.getElementById("search-alert");
    const spinner = document.getElementById("spinner");

    // Filter hanya angka saat diketik
    nikInput.addEventListener("keypress", (e) => {
        const char = String.fromCharCode(e.which);
        if (!/[0-9]/.test(char)) {
            e.preventDefault();
        }
    });

    // Bersihkan karakter tidak valid dan batasi 8 digit
    nikInput.addEventListener("input", () => {
        nikInput.value = nikInput.value.replace(/[^0-9]/g, '').slice(0, 8);
        if (/^\d{8}$/.test(nikInput.value)) {
            nikTooltip.classList.add("d-none");
        }
    });

    // Trigger pencarian dengan tombol Enter
    nikInput.addEventListener("keypress", (event) => {
        if (event.key === "Enter") {
            searchOperator();
        }

    
    });

    function showNikTooltip(message) {
  const tooltip = document.getElementById("nik-tooltip");
  tooltip.innerText = message;
  tooltip.classList.remove("d-none");
  nikInput.classList.add("is-invalid");

  setTimeout(() => {
    tooltip.classList.add("d-none");
    nikInput.classList.remove("is-invalid");
  }, 3000);
}

    searchBtn.addEventListener("click", searchOperator);


    // ==================== Tooltip ====================
    document.getElementById('search-nik-btn').addEventListener('click', function () {
  const nikInput = document.getElementById('nik');
  const nik = nikInput.value.trim();

  if (!/^\d{8}$/.test(nik)) {
    const tooltip = document.getElementById('nik-tooltip');
    tooltip.classList.remove('d-none');
    nikInput.classList.add('is-invalid');

    // Hide alert after few seconds
    setTimeout(() => {
      tooltip.classList.add('d-none');
      nikInput.classList.remove('is-invalid');
    }, 3000);

    return; // Stop further execution
  }

});

// >>> BARU: isi semua field dari certification
function fillCertificationForm(cert) {
  // ---- Soldering ----
  const solderingInputs = document.querySelectorAll(".cert-soldering input");
  if (solderingInputs.length >= 3) {
    solderingInputs[0].value = cert.soldering_written ?? "";
    solderingInputs[1].value = cert.soldering_practical ?? "";
    solderingInputs[2].value = cert.soldering_result ?? "";
    applyResultColor(solderingInputs[2], solderingInputs[2].value);
  }

  // ---- Screwing ----
  const screwingInputs = document.querySelectorAll(".cert-screwing input");
  if (screwingInputs.length >= 3) {
    screwingInputs[0].value = cert.screwing_technique ?? "";
    screwingInputs[1].value = cert.screwing_work ?? "";
    screwingInputs[2].value = cert.screwing_result ?? "";
    applyResultColor(screwingInputs[2], screwingInputs[2].value);
  }

  // ---- Data Screening ----
  const screeningInputs = document.querySelectorAll(".cert-screening input");
  if (screeningInputs.length >= 5) {
    screeningInputs[0].value = cert.ds_tiu ?? "";
    screeningInputs[1].value = cert.ds_accu ?? "";
    screeningInputs[2].value = cert.ds_heco ?? "";
    screeningInputs[3].value = cert.ds_mcc ?? "";
    screeningInputs[4].value = cert.ds_result ?? "";
    applyResultColor(screeningInputs[4], screeningInputs[4].value);
  }

  // ---- Line Simulation ----
  const processSelect = document.querySelector(".cert-line-process");
  const targetInput   = document.querySelector(".cert-line-target");
  const actualInput   = document.querySelector(".cert-line-actual");
  const achieveInput  = document.querySelector(".cert-line-achievement");
  const resultInput   = document.querySelector(".cert-line-result");

  if (processSelect) processSelect.value = cert.process || "";
  if (targetInput)   targetInput.value   = cert.ls_target ?? "";
  if (actualInput)   actualInput.value   = cert.ls_actual ?? "";

  if (achieveInput) {
    // Tampilkan dengan " %", biar konsisten sama kalkulasi existing
    const ach = cert.ls_achievement;
    achieveInput.value = (ach === null || ach === undefined) ? "" : `${parseFloat(ach).toFixed(1)} %`;
  }
  if (resultInput) {
    resultInput.value = cert.ls_result ?? "";
    applyResultColor(resultInput, resultInput.value);
  }

  // ---- MSA Assessment ----
  const msaScores = document.querySelectorAll(".msa-score");
  if (msaScores.length >= 4) {
    msaScores[0].value = cert.msaa_accuracy ?? "";
    msaScores[1].value = cert.msaa_missrate ?? "";
    msaScores[2].value = cert.msaa_falsealarm ?? "";
    msaScores[3].value = cert.msaa_confidence ?? "";
  }
  const msaResult = document.getElementById("msa-result");
  if (msaResult) {
    msaResult.value = cert.msaa_result ?? "";
    applyResultColor(msaResult, msaResult.value);
  }

  // ---- Certification Skills table (doc no, training, expired, status) ----
  const docNos       = document.querySelectorAll(".form-upload-docno");
  const trainingDates= document.querySelectorAll(".upload-training");
  const expiredDates = document.querySelectorAll(".upload-expired");
  if (docNos[0])       docNos[0].value       = cert.soldering_docno ?? "";
  if (trainingDates[0])trainingDates[0].value= cert.soldering_traindate ?? "";
  if (expiredDates[0]) expiredDates[0].value = cert.soldering_expdate ?? "";

  if (docNos[1]) docNos[1].value = cert.screwing_docno ?? "";
  if (trainingDates[1]) trainingDates[1].value = cert.screwing_traindate ?? "";
  if (expiredDates[1]) expiredDates[1].value = cert.screwing_expdate ?? "";

  if (docNos[2]) docNos[2].value = cert.msa_docno ?? "";
  if (trainingDates[2]) trainingDates[2].value = cert.msa_traindate ?? "";
  if (expiredDates[2]) expiredDates[2].value = cert.msa_expdate ?? "";

  // Set status setiap baris berdasarkan ada/tidaknya file base64 yang tersimpan
  const rows = document.querySelectorAll("#uploadCertTable tbody tr");
  if (rows[0]) rows[0].querySelector(".upload-status").innerHTML =
    cert.file_soldering ? `<span class="status-pass"><i class="bi bi-check-circle-fill"></i> Pass</span>` 
                        : `<span class="status-notyet"><i class="bi bi-x-circle-fill"></i> Not Yet</span>`;
  if (rows[1]) rows[1].querySelector(".upload-status").innerHTML =
    cert.file_screwing ? `<span class="status-pass"><i class="bi bi-check-circle-fill"></i> Pass</span>` 
                       : `<span class="status-notyet"><i class="bi bi-x-circle-fill"></i> Not Yet</span>`;
  if (rows[2]) rows[2].querySelector(".upload-status").innerHTML =
    cert.file_msa ? `<span class="status-pass"><i class="bi bi-check-circle-fill"></i> Pass</span>` 
                  : `<span class="status-notyet"><i class="bi bi-x-circle-fill"></i> Not Yet</span>`;

  // Trigger kalkulasi & pewarnaan ulang supaya UI konsisten
  attachScoreListeners();
  evaluateScreeningResult();
  evaluateMSAResult();
}

// >>> BARU: reset field kalau tidak ada certification
function clearCertificationForm() {
  // Soldering
  document.querySelectorAll(".cert-soldering input").forEach((el, idx) => {
    el.value = "";
    if (idx === 2) applyResultColor(el, ""); // clear color
  });

  // Screwing
  document.querySelectorAll(".cert-screwing input").forEach((el, idx) => {
    el.value = "";
    if (idx === 2) applyResultColor(el, "");
  });

  // Screening
  document.querySelectorAll(".cert-screening input").forEach((el, idx) => {
    el.value = "";
    if (idx === 4) applyResultColor(el, "");
  });

  // Line Simulation
  const lsRes = document.querySelector(".cert-line-result");
  if (document.querySelector(".cert-line-process")) document.querySelector(".cert-line-process").value = "";
  if (document.querySelector(".cert-line-target")) document.querySelector(".cert-line-target").value = "";
  if (document.querySelector(".cert-line-actual")) document.querySelector(".cert-line-actual").value = "";
  if (document.querySelector(".cert-line-achievement")) document.querySelector(".cert-line-achievement").value = "";
  if (lsRes) { lsRes.value = ""; applyResultColor(lsRes, ""); }

  // MSA
  document.querySelectorAll(".msa-score").forEach(el => el.value = "");
  const msaResult = document.getElementById("msa-result");
  if (msaResult) { msaResult.value = ""; applyResultColor(msaResult, ""); }

  // Certification Skills table
  const docNos        = document.querySelectorAll(".form-upload-docno");
  const trainingDates = document.querySelectorAll(".upload-training");
  const expiredDates  = document.querySelectorAll(".upload-expired");

  // Soldering
  if (docNos[0])        docNos[0].value        = "";
  if (trainingDates[0]) trainingDates[0].value = "";
  if (expiredDates[0])  expiredDates[0].value  = "";

  // Screwing
  if (docNos[1])        docNos[1].value        = "";
  if (trainingDates[1]) trainingDates[1].value = "";
  if (expiredDates[1])  expiredDates[1].value  = "";

  // MSA
  if (docNos[2])        docNos[2].value        = "";
  if (trainingDates[2]) trainingDates[2].value = "";
  if (expiredDates[2])  expiredDates[2].value  = "";

  const rows = document.querySelectorAll("#uploadCertTable tbody tr");
  rows.forEach(row => {
    const statusCell = row.querySelector(".upload-status");
    if (statusCell) statusCell.innerHTML = `<span class="status-notyet"><i class="bi bi-x-circle-fill"></i> Not Yet</span>`;
  });
}




    // ==================== Form Status ====================
    function updateFormStatus(status) {
    const formStatusCard = document.getElementById("form-status-card");
    const formStatusText = document.getElementById("form-status-text");

    formStatusCard.classList.remove("waiting", "new", "closed");

    if (status === "New") {
        formStatusCard.classList.add("new");
        formStatusText.textContent = "Form Status: New";
    } else if (status === "Closed") {
        formStatusCard.classList.add("closed");
        formStatusText.textContent = "Form Status: Closed";
    } else {
        formStatusCard.classList.add("waiting");
        formStatusText.textContent = "Waiting for search...";
    }
}

    async function searchOperator() {
        const nik = nikInput.value.trim();

        if (!/^\d{8}$/.test(nik)) {
          showNikTooltip("NIK must be exactly 8 digits");
          return;
        }

        nikTooltip.classList.add("d-none");
        //alertBox.classList.add("d-none");
        spinner.style.display = "inline-block";

        try {
            const response = await fetch(`/api/hrd/operator?nik=${nik}`);
            if (!response.ok) throw new Error("Operator not found");

            const data = await response.json();

            nameInput.value = data.name ?? "";
            lineInput.value = data.line ?? "";
            levelInput.value = data.job_level ?? "";
            contractStatusInput.value = data.contract_status ?? "";

            if (data.contract_status && data.contract_status.toLowerCase() === "permanen") {
                endDateInput.value = "-";
            } else {
                endDateInput.value = data.end_contract_date ?? "";
            }

            if (data.Photo) {
                photoPreview.src = `data:image/jpeg;base64,${data.Photo}`;
            } else {
                photoPreview.src = "static/assets/img/profile-iconn.png";
            }

            updateFormStatus(data.form_status);
            // >>> TAMBAHAN: isi form certification kalau ada datanya
            if (data.certification) {
              fillCertificationForm(data.certification);
            } else {
              clearCertificationForm();
            }


        } catch (error) {
            console.error("Search error:", error);
            const operatorTooltip = document.getElementById("operator-tooltip");
            operatorTooltip.innerText = "Operator not found";
            operatorTooltip.classList.remove("d-none");
            nikInput.classList.add("is-invalid");

        setTimeout(() => {
          operatorTooltip.classList.add("d-none");
          nikInput.classList.remove("is-invalid");
          }, 3000);

            nameInput.value = "";
            lineInput.value = "";
            levelInput.value = "";
            contractStatusInput.value = "";
            endDateInput.value = "";
            photoPreview.src = "static/assets/img/profile-iconn.png";
        
           // setTimeout(() => {
              //alertBox.classList.add("d-none");
            //}, 4000);
        
            //console.error("Error fetching operator:", error);
            updateFormStatus(null);
            clearCertificationForm(); // >>> kosongkan form cert kalau gagal cari


          } finally {
            spinner.style.display = "none";
        }
    }
});

function fetchCertification(nik, type) {
  fetch(`/api/certification/${nik}`)
    .then(res => res.json())
    .then(cert => {
      if (!cert) return;

      // mapping field sesuai type
      const docField   = `${type}_docno`;
      const trainField = `${type}_traindate`;
      const expField   = `${type}_expdate`;

      // mapping ID elemen input dengan suffix type
      document.getElementById(`docNumber_${type}`).value    = cert[docField]   || "-";
      document.getElementById(`trainingDate_${type}`).value = cert[trainField] || "-";
      document.getElementById(`expiredDate_${type}`).value  = cert[expField]   || "-";
    })
    .catch(err => console.error(err));
}

// ==================== SAVE BUTTON ====================
document.getElementById("submit-btn").addEventListener("click", async (e) => {
  e.preventDefault();

  //console.log("Calling validateBeforeSave...");
  if (!validateBeforeSave()) //{
    //console.log("Validation failed. Aborting save.");
    return;
  //}

  // --- ambil semua data sama seperti sebelumnya ---
  const nik = document.getElementById("nik").value.trim();
  const docNos = document.querySelectorAll(".form-upload-docno");
  const trainingDates = document.querySelectorAll(".upload-training");
  const expiredDates = document.querySelectorAll(".upload-expired");

  const solderingInputs = document.querySelectorAll(".cert-soldering input");
  const screwingInputs = document.querySelectorAll(".cert-screwing input");
  const lineProcess = document.querySelector(".cert-line-process").value;
  const lineTarget = document.querySelector(".cert-line-target").value;
  const lineActual = document.querySelector(".cert-line-actual").value;
  const lineAchievement = document.querySelector(".cert-line-achievement").value;
  const lineResult = document.querySelector(".cert-line-result").value;

  const screeningInputs = document.querySelectorAll(".cert-screening input");
  const screeningResult = screeningInputs[4].value;

  const msaScores = document.querySelectorAll(".msa-score");
  const msaResult = document.getElementById("msa-result").value;

  // build payload
const certificationData = {
  nik: document.getElementById("nik").value,
  soldering_written: parseInt(solderingInputs[0].value),
  soldering_practical: parseInt(solderingInputs[1].value),
  soldering_result: solderingInputs[2].value,
  screwing_technique: parseInt(screwingInputs[0].value),
  screwing_work: parseInt(screwingInputs[1].value),
  screwing_result: screwingInputs[2].value,
  ds_tiu: parseInt(screeningInputs[0].value),
  ds_accu: parseInt(screeningInputs[1].value),
  ds_heco: parseInt(screeningInputs[2].value),
  ds_mcc: parseInt(screeningInputs[3].value),
  ds_result: screeningResult,
  process: lineProcess,
  ls_target: parseFloat(lineTarget),
  ls_actual: parseFloat(lineActual),
  ls_achievement: parseFloat(lineAchievement),
  ls_result: lineResult,
  msaa_accuracy: parseInt(msaScores[0].value),
  msaa_missrate: parseInt(msaScores[1].value),
  msaa_falsealarm: parseInt(msaScores[2].value),
  msaa_confidence: parseInt(msaScores[3].value),
  msaa_result: msaResult,
  soldering_docno: docNos[0].value,
  soldering_traindate: formatDateToMMDDYYYY(trainingDates[0].value),
  soldering_expdate: formatDateToMMDDYYYY(expiredDates[0].value),
  screwing_docno: docNos[1].value,
  screwing_traindate: formatDateToMMDDYYYY(trainingDates[1].value),
  screwing_expdate: formatDateToMMDDYYYY(expiredDates[1].value),
  msa_docno: docNos[2].value,
  msa_traindate: formatDateToMMDDYYYY(trainingDates[2].value),
  msa_expdate: formatDateToMMDDYYYY(expiredDates[2].value),
  file_soldering: "",
  file_screwing: "",
  file_msa: "",
  status: document.querySelectorAll(".upload-status span").length &&
          Array.from(document.querySelectorAll(".upload-status span"))
            .every(s => s.textContent.trim().toLowerCase().includes("pass"))
          ? "Pass" : "Not Yet"
};


  try {
    const res = await fetch('/api/certification', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(certificationData)
    });

    if (!res.ok) throw new Error("Failed to save certification data.");

    // Upload files
    await uploadFile(nik, 0, "Soldering");
    await uploadFile(nik, 1, "Screwing");
    await uploadFile(nik, 2, "MSA");

    const toastElement = document.getElementById("saveToast");
    const toast = new bootstrap.Toast(toastElement);
    toast.show();
    localStorage.setItem("showToast", "true");
    setTimeout(() => location.reload(), 1000);

  } catch (err) {
    console.error("Error saving certification record:", err);
    alert("Error saving data: " + err.message);
  }

  
  

});


// ==================== Show Toast Function ====================
function showToast(message, type = "success") {
  // Scroll ke atas supaya toast selalu kelihatan
  window.scrollTo({ top: 0, behavior: "smooth" });

  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerText = message;
  document.body.appendChild(toast);

  // Trigger animasi fade-in
  setTimeout(() => toast.classList.add("show"), 10);

  // Hilangkan setelah 3 detik
  setTimeout(() => {
    toast.classList.remove("show");
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

