// Login check
function checkLogin() {
    const loggedIn = localStorage.getItem("isLoggedIn");
    if (!loggedIn) {
      window.location.href = "/login";
    }
  }

  checkLogin(); 

  // --- Certification record ---
    async function safeJson(response) {
      const text = await response.text();     // baca raw body
      if (!text) return null;                 // kalau kosong → return null
      try {
        return JSON.parse(text);              // kalau ada isi → parse JSON
      } catch (e) {
        console.error("JSON parse error:", e, text);
        return null;
      }
    }

// ================ Search Operator by NIK ================
// IAB.js — View-only script for IAB.html
'use strict';

let operatorData = null;
let uploadedFiles = {
  trainingEval: null,
  skillsEval: null,
  trainingInEval: null
};

const fileTrainingEval = document.getElementById("fileTrainingEval");
const fileSkillsEval = document.getElementById("fileSkillsEval");
const fileTrainingInEval = document.getElementById("fileTrainingInEval");
        

document.addEventListener('DOMContentLoaded', () => {

  // --- Elements ---
  const searchBtn = document.getElementById('search-nik-btn');
  const nikInput = document.getElementById('nik');
  const nikTooltip = document.getElementById('nik-tooltip');
  const spinner = document.getElementById('spinner');
  const operatorModal = new bootstrap.Modal(document.getElementById("operatorModal"));
 
  const tableBody = document.getElementById("operatorTableBody");
  const searchInput = document.getElementById("searchOperator");
  
  const nameInput = document.getElementById('name');
  const lineInput = document.getElementById('line');
  const levelInput = document.getElementById('job-level');
  const contractStatusInput = document.getElementById('contract-status');
  const endDateInput = document.getElementById('end-date');
  const photoPreview = document.getElementById('photo-preview');

  const formStatusCard = document.getElementById('form-status-card');
  const formStatusText = document.getElementById('form-status-text');


  // helpers
  const safeSetValue = (el, v) => { if (el) el.value = (v === null || v === undefined) ? '' : v; };
  const safeSetText = (el, v) => { if (el) el.textContent = (v === null || v === undefined) ? '' : v; };
  const exists = (el) => !!el;

   let operators = [];


  // --- Event tombol 🔎 ---
  searchBtn.addEventListener("click", async (e) => {
    e.preventDefault();
    if (nikInput.value.trim() === "") {
      // kalau kosong -> buka modal
      operatorModal.show();
      await loadOperators();
    } else {
      // kalau ada NIK -> jalankan search seperti biasa
      doNikSearch(nikInput.value.trim());
    }
  });

  // --- Pencarian manual di backend ---
  function doNikSearch(nik) {
    console.log("Searching data untuk NIK:", nik);
    // TODO: panggil fungsi search lama kamu di sini
    searchOperator();
    document.getElementById("search-nik-btn").classList.add("disabled");
    setTimeout(() => {
      document.getElementById("search-nik-btn").classList.remove("disabled");
    }, 1000);
  }

  // --- Ambil daftar operator ---
  let operatorTable;

async function loadOperators() {
  if ($.fn.DataTable.isDataTable('#operatorTable')) {
    operatorTable.destroy(); // reset kalau sudah ada
    $('#operatorTable').empty(); // kosongkan agar bisa re-init
    $('#operatorTable').html(`
      <thead class="table-profile">
        <tr><th>NIK</th><th>Nama</th></tr>
      </thead>
    `);
  }

  operatorTable = $('#operatorTable').DataTable({
  serverSide: true,      // penting: gunakan server-side
  processing: true,      // tampilkan loading spinner
  ajax: {
    url: '/api/operators',
    type: 'GET',
    data: function(d) {
      // d contains DataTables params
      // Bisa diteruskan ke backend untuk query
      return {
        search: d.search.value,
        start: d.start,
        length: d.length,
        order_col: d.order[0].column,
        order_dir: d.order[0].dir
      };
    },
    dataSrc: function(json) {
      //console.log('Server response:', json);
      return json.data || [];
    }
  },
  columns: [
    { data: 'nik', defaultContent: '-' },
    { data: 'name', defaultContent: '-' }
  ],
  paging: true,
  searching: true,
  ordering: true,
  responsive: true,
  language: {
    search: "🔍Search:",
    lengthMenu: "Show _MENU_ data",
    info: "Showing _TOTAL_ of _MAX_ operators",
    infoCallback: function(settings, start, end, max, total, pre) {
    // total = jumlah hasil filter
    // max   = total data di database
    return 'Showing ' + total + ' of ' + max + ' operators';
  }
  }
});

$('#operatorModal .dataTables_paginate').hide();

  // Event klik row
  $('#operatorTable tbody').on('click', 'tr', function() {
    const data = operatorTable.row(this).data();
    if (!data) return;
    nikInput.value = data.nik;document.activeElement.blur();

    console.log("Closing modal now...");
    operatorModal.hide();

     setTimeout(() => {
        console.log("Backdrops after hide:", document.querySelectorAll(".modal-backdrop").length);
      }, 500);


    document.getElementById("operatorModal")
      .addEventListener("hidden.bs.modal", () => {
        searchOperator();
      }, { once: true });
  });
}


  // ===== Tooltip Helpers =====
  function showNikTooltip(message) {
    if (!nikTooltip) return;
    nikTooltip.textContent = message;
    nikTooltip.classList.add("show");

    // auto-hide setelah 3 detik
    setTimeout(() => hideNikTooltip(), 3000);
  }

  function hideNikTooltip() {
    if (!nikTooltip) return;
    nikTooltip.classList.remove("show");
}

  // Attach input restrictions to NIK field (only numbers, max 8 digits)
  if (nikInput) {
    nikInput.addEventListener('keypress', (e) => {
      const char = String.fromCharCode(e.which || e.keyCode);
      if (!/[0-9]/.test(char)) e.preventDefault();
    });
    nikInput.addEventListener('input', () => {
      nikInput.value = nikInput.value.replace(/\D/g, '').slice(0, 8);
      if (/^\d{8}$/.test(nikInput.value) && nikTooltip) nikTooltip.classList.add('d-none');
    });
    nikInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        searchOperator();
      }
    });
  }

  // Format and apply pass/fail classes 
  function applyResultColor(fieldEl, value) {
    if (!fieldEl) return;
    fieldEl.classList.remove('input-result-pass', 'input-result-fail');
    if (!value) return;
    const v = String(value).trim().toLowerCase();
    if (v === 'pass') fieldEl.classList.add('input-result-pass');
    else fieldEl.classList.add('input-result-fail');
  }

  // Update form status form (New / Closed / Waiting)
  function updateFormStatus(status) {
    if (!formStatusCard || !formStatusText) return;
    
    formStatusCard.classList.remove('waiting', 'new', 'closed');
    
    if (status === 'New') {
      formStatusCard.classList.add('new');
      formStatusText.textContent = 'Form Status: New';
    } else if (status === 'Closed') {
      formStatusCard.classList.add('closed');
      formStatusText.textContent = 'Form Status: Closed';
    } else {
      formStatusCard.classList.add('waiting');
      formStatusText.textContent = 'Waiting for search...';
    }
  }

  // Clear personal details
  function clearPersonalDetails() {
    safeSetValue(nameInput, '');
    safeSetValue(lineInput, '');
    safeSetValue(levelInput, '');
    safeSetValue(contractStatusInput, '');
    safeSetValue(endDateInput, '');
    if (photoPreview) photoPreview.src = 'static/assets/img/profile-iconn.png';
  }

  // Clear certification sections (make sure read-only stays)
  function clearCertificationFields() {
    // Screwing (3 inputs)
    const screwingInputs = document.querySelectorAll('.cert-screwing input.form-control');
    if (screwingInputs && screwingInputs.length >= 3) {
      screwingInputs[0].value = '';
      screwingInputs[1].value = '';
      screwingInputs[2].value = '';
      applyResultColor(screwingInputs[2], '');
    }

    // Soldering (3 inputs)
    const solderingInputs = document.querySelectorAll('.cert-soldering input.form-control');
    if (solderingInputs && solderingInputs.length >= 3) {
      solderingInputs[0].value = '';
      solderingInputs[1].value = '';
      solderingInputs[2].value = '';
      applyResultColor(solderingInputs[2], '');
    }

    // Line Simulation
    const processSelect = document.querySelector('.cert-line-process');
    const targetInput = document.querySelector('.cert-line-target');
    const actualInput = document.querySelector('.cert-line-actual');
    const achievementInput = document.querySelector('.cert-line-achievement');
    const lsResultInput = document.querySelector('.cert-line-result');
    if (processSelect) { processSelect.value = ''; processSelect.disabled = true; }
    if (targetInput) targetInput.value = '';
    if (actualInput) actualInput.value = '';
    if (achievementInput) achievementInput.value = '';
    if (lsResultInput) { lsResultInput.value = ''; applyResultColor(lsResultInput, ''); }

    // Screening
    const screeningInputs = document.querySelectorAll('.cert-screening input');
    if (screeningInputs && screeningInputs.length >= 5) {
      screeningInputs[0].value = '';
      screeningInputs[1].value = '';
      screeningInputs[2].value = '';
      screeningInputs[3].value = '';
      screeningInputs[4].value = '';
      applyResultColor(screeningInputs[4], '');
    }

    // MSA
    const msaScores = document.querySelectorAll('.cert-msa .msa-score');
    if (msaScores && msaScores.length >= 4) {
      msaScores.forEach(i => i.value = '');
    }
    const msaResult = document.getElementById('msa-result');
    if (msaResult) { msaResult.value = ''; applyResultColor(msaResult, ''); }

    // Certification skills table — clear docno, dates, status, hide view buttons
    const rows = document.querySelectorAll('#uploadCertTable tbody tr');
    rows.forEach(row => {
      const docNo = row.querySelector('.form-upload-docno');
      const train = row.querySelector('.upload-training');
      const expire = row.querySelector('.upload-expired');
      const statusCell = row.querySelector('.upload-status');
      const uploadBtn = row.querySelector('.btn-upload-trigger');
      const viewBtn = row.querySelector('.btn-download');

      if (docNo) docNo.value = '';
      if (train) train.value = '';
      if (expire) expire.value = '';
      if (statusCell) statusCell.innerHTML = '<span class="status-notyet"><i class="bi bi-x-circle-fill"></i> Not Yet</span>';
      if (uploadBtn) { uploadBtn.disabled = true; uploadBtn.classList.add('d-none'); }
      if (viewBtn) { viewBtn.classList.add('d-none'); viewBtn.onclick = null; }
      const hiddenFile = row.querySelector('.form-upload');
      if (hiddenFile) hiddenFile.classList.add('d-none');
    });
  }


  let pdfGenerated = false; // default belum generate

  
  // Initial state
  clearPersonalDetails();
  clearCertificationFields();
  updateFormStatus(null);


  // Open base64 PDF in a new window
  function base64ToBlob(base64, mimeType = 'application/pdf') {
    // Hapus prefix jika ada
    const cleaned = base64.replace(/^data:application\/pdf;base64,/, '');
    const binary = atob(cleaned);
    const len = binary.length;
    const buffer = new Uint8Array(len);
    for (let i = 0; i < len; i++) buffer[i] = binary.charCodeAt(i);
    return new Blob([buffer], { type: mimeType });
}

  function openBase64Pdf(base64) {
    if (!base64) {
      alert('No file data available to display.');
      return;
    }
    try {
      const blob = base64ToBlob(base64, 'application/pdf');
      const url = URL.createObjectURL(blob);
      window.open(url, '_blank');
    } catch (err) {
      console.error('Failed to open PDF:', err);
      alert('Unable to open PDF file. The file may be corrupted.');
    }
  }

  // Populate certification fields from server response
  function populateCertification(cert) {
    if (!cert) {
      clearCertificationFields();
      return;
    }

    // Screwing
    const screwingInputs = document.querySelectorAll('.cert-screwing input.form-control');
    if (screwingInputs && screwingInputs.length >= 3) {
      screwingInputs[0].value = cert.screwing_technique ?? '';
      screwingInputs[1].value = cert.screwing_work ?? '';
      screwingInputs[2].value = cert.screwing_result ?? '';
      applyResultColor(screwingInputs[2], cert.screwing_result);
      // make read-only
      screwingInputs.forEach(i => i.readOnly = true);
    }

    // Soldering
    const solderingInputs = document.querySelectorAll('.cert-soldering input.form-control');
    if (solderingInputs && solderingInputs.length >= 3) {
      solderingInputs[0].value = cert.soldering_written ?? '';
      solderingInputs[1].value = cert.soldering_practical ?? '';
      solderingInputs[2].value = cert.soldering_result ?? '';
      applyResultColor(solderingInputs[2], cert.soldering_result);
      solderingInputs.forEach(i => i.readOnly = true);
    }

    // Line Simulation
    const processSelect = document.querySelector('.cert-line-process');
    const targetInput = document.querySelector('.cert-line-target');
    const actualInput = document.querySelector('.cert-line-actual');
    const achievementInput = document.querySelector('.cert-line-achievement');
    const lsResultInput = document.querySelector('.cert-line-result');

    if (processSelect) { processSelect.value = cert.process ?? ''; processSelect.disabled = true; }
    if (targetInput) { targetInput.value = cert.ls_target ?? ''; targetInput.readOnly = true; }
    if (actualInput) { actualInput.value = cert.ls_actual ?? ''; actualInput.readOnly = true; }
    if (achievementInput) {
      // If numeric provided, keep 1 decimal and append % if looks like percent
      let a = cert.ls_achievement;
      achievementInput.value = (a === null || a === undefined) ? '' : (Number(a).toFixed(1) + ' %');
      achievementInput.readOnly = true;
    }
    if (lsResultInput) { lsResultInput.value = cert.ls_result ?? ''; applyResultColor(lsResultInput, cert.ls_result); lsResultInput.readOnly = true; }

    // Screening
    const screeningInputs = document.querySelectorAll('.cert-screening input');
    if (screeningInputs && screeningInputs.length >= 5) {
      screeningInputs[0].value = cert.ds_tiu ?? '';
      screeningInputs[1].value = cert.ds_accu ?? '';
      screeningInputs[2].value = cert.ds_heco ?? '';
      screeningInputs[3].value = cert.ds_mcc ?? '';
      screeningInputs[4].value = cert.ds_result ?? '';
      applyResultColor(screeningInputs[4], cert.ds_result);
      screeningInputs.forEach(i => i.readOnly = true);
    }

    // MSA
    const msaScores = document.querySelectorAll('.cert-msa .msa-score');
    if (msaScores && msaScores.length >= 4) {
      msaScores[0].value = cert.msaa_accuracy ?? '';
      msaScores[1].value = cert.msaa_missrate ?? '';
      msaScores[2].value = cert.msaa_falsealarm ?? '';
      msaScores[3].value = cert.msaa_confidence ?? '';
      msaScores.forEach(i => i.readOnly = true);
    }
    const msaResult = document.getElementById('msa-result');
    if (msaResult) { msaResult.value = cert.msaa_result ?? ''; applyResultColor(msaResult, cert.msaa_result); }

    // Certification Skills table (three rows: Soldering, Screwing, MSA)
    const rows = document.querySelectorAll('#uploadCertTable tbody tr');
    const fmt = (d) => (d ? String(d).slice(0, 10) : '');

    const items = [
  { // 0: Soldering
    doc: cert.soldering_docno,
    train: cert.soldering_traindate,
    exp: cert.soldering_expdate,
    file: cert.file_soldering
  },
  { // 1: Screwing
    doc: cert.screwing_docno,
    train: cert.screwing_traindate,
    exp: cert.screwing_expdate,
    file: cert.file_screwing
  },
  { // 2: MSA
    doc: cert.msa_docno,
    train: cert.msa_traindate,
    exp: cert.msa_expdate,
    file: cert.file_msa
  }
];

rows.forEach((row, idx) => {
  const docNo = row.querySelector('.form-upload-docno');
  const train = row.querySelector('.upload-training');
  const expire = row.querySelector('.upload-expired');
  const statusCell = row.querySelector('.upload-status');
  const uploadBtn = row.querySelector('.btn-upload-trigger');
  const viewBtn = row.querySelector('.btn-download');
  const hiddenFile = row.querySelector('.form-upload');

  const it = items[idx];

  if (docNo)   docNo.value = it?.doc ?? '';
  if (train) { train.value = fmt(it?.train); train.readOnly = true; }
  if (expire){ expire.value = fmt(it?.exp);  expire.readOnly = true; }

  if (statusCell) {
    const s = (cert.status ?? '').toString();
    const isPass = /pass/i.test(s);
    statusCell.innerHTML = `<span class="${isPass ? 'status-pass' : 'status-notyet'}">
      <i class="bi ${isPass ? 'bi-check-circle-fill' : 'bi-x-circle-fill'}"></i> ${s || 'Not Yet'}</span>`;
  }

  if (uploadBtn) { uploadBtn.disabled = true; uploadBtn.classList.add('d-none'); }
  if (hiddenFile) hiddenFile.classList.add('d-none');

    // isi file evaluation (hanya aktifkan tombol view, jangan auto-open)
    if (operatorData.evaluation) {
        if (operatorData.evaluation.op_train_eval) {
            document.getElementById("viewFileTrainingEval").disabled = false;
            document.getElementById("viewFileTrainingEval").onclick = () =>
                openBase64Pdf(operatorData.evaluation.op_train_eval);
        }
        if (operatorData.evaluation.op_skills_eval) {
            document.getElementById("viewFileSkillsEval").disabled = false;
            document.getElementById("viewFileSkillsEval").onclick = () =>
                openBase64Pdf(operatorData.evaluation.op_skills_eval);
        }
        if (operatorData.evaluation.train_eval) {
            document.getElementById("viewFileEval").disabled = false;
            document.getElementById("viewFileEval").onclick = () =>
                openBase64Pdf(operatorData.evaluation.train_eval);
        }
    }

  // FIX: gunakan it.file, bukan fileBases
  const base64 = it?.file;
  if (viewBtn) {
    if (base64 && base64.length > 10) {
      viewBtn.classList.remove('d-none');
      viewBtn.innerHTML = '<i class="bi bi-eye-fill"></i>';
      viewBtn.title = 'View File';
      viewBtn.onclick = () => openBase64Pdf(base64);
    } else {
      viewBtn.classList.add('d-none');
      viewBtn.onclick = null;
    }

      }
    });
  }



  // Main search logic
  async function searchOperator() {
    if (!nikInput) {
      alert('Internal error: NIK not found');
      return;
    }

    const nik = nikInput.value.trim();
    if (!/^\d{8}$/.test(nik)) {
      showNikTooltip("NIK must be exactly 8 digits");
      nikInput.classList.add("is-invalid");
      setTimeout(() => {
        nikInput.classList.remove("is-invalid");
      }, 3000);
      return;
    }

    if (spinner) spinner.style.display = 'inline-block';

    try {
      // --- Operator data ---
      const resOp = await fetch(`/api/operator/iab?nik=${encodeURIComponent(nik)}`);
      if (!resOp.ok) {
        if (resOp.status === 404) {
          alert('Operator not found in the database.');
        } else {
          alert('Failed to fetch operator data. Please try again.');
        }
        clearPersonalDetails();
        clearCertificationFields();
        updateFormStatus(null);
        return;
      }
      const op = await safeJson(resOp);

      // populate personal details (safely)
      safeSetValue(nameInput, op.name ?? '');
      safeSetValue(lineInput, op.line ?? '');
      safeSetValue(levelInput, op.job_level ?? '');
      safeSetValue(contractStatusInput, op.contract_status ?? '');
      if (op.contract_status &&['permanen', 'resign'].includes(String(op.contract_status).toLowerCase())) 
        {
          safeSetValue(endDateInput, '-');
        } else {
          safeSetValue(endDateInput, op.end_contract_date ?? '');
        }
      if (op.Photo) {
        if (photoPreview) photoPreview.src = `data:image/jpeg;base64,${op.Photo}`;
      } else {
        if (photoPreview) photoPreview.src = 'static/assets/img/profile-iconn.png';
      }

      // Set operator data for evaluation number generation
      operatorData = {
        NIK: op.nik,
        Line: op.line
      };

      updateFormStatus(op.form_status);

    


      // --- Certification record (GET) ---
      // Expectation: backend exposes GET /api/certification?nik=... returning latest certification record.
      const resCert = await fetch(`/api/certification?nik=${encodeURIComponent(nik)}`);
      if (!resCert.ok) {
        if (resCert.status === 404) {
          // Not an error — operator exists but no certification record yet
          clearCertificationFields();
          alert('No certification record found for this operator.');
        } else {
          clearCertificationFields();
          console.error('Certification fetch error:', resCert.status, resCert.statusText);
          alert('Failed to fetch certification data. Please try again later.');
        }
        return;
      }
      const cert = await safeJson(resCert);
      populateCertification(cert);

    } catch (err) {
      console.error('Unexpected error while searching operator:', err);
      alert('An unexpected error occurred. Please try again or contact IT support.');
      clearPersonalDetails();
      clearCertificationFields();
      updateFormStatus(null);
    } finally {
      if (spinner) spinner.style.display = 'none';
    }

    
   // --- Evaluation record (GET) ---
  const resEval = await fetch(`/api/evaluation?nik=${encodeURIComponent(operatorData.NIK)}`);
    if (resEval.ok) {
      const evalData = await safeJson(resEval);
        populateEvaluation(evalData);
          // simpan juga ke operatorData biar bisa dipakai di tempat lain
          operatorData.evaluation = evalData;
        } else {
      const evalData = await safeJson(resEval);
          populateEvaluation(evalData);
          operatorData.evaluation = evalData;
          console.log("Eval data from backend:", evalData);

        }
  
      
      // ===================== Populate existing evaluation if any =========================
      // Populate Evaluation Report dari server response
      function populateEvaluation(evalData) {
        const viewTrainingEval = document.getElementById("viewTrainingEval");
        const viewSkillsEval = document.getElementById("viewSkillsEval");
        const viewTrainingInEval = document.getElementById("viewTrainingInEval");


        const saveBtn = document.getElementById("saveBtn");

        if (!evalData) {
          // kalau belum ada data, input file ENABLE
          [fileTrainingEval, fileSkillsEval, fileTrainingInEval].forEach(inp => {
            if (inp) inp.disabled = false;
          });

          if (saveBtn) saveBtn.disabled = false;

          [viewTrainingEval, viewSkillsEval, viewTrainingInEval].forEach(btn => {
            if (btn) btn.classList.add("d-none");
          });
          return;
        }

        if (saveBtn) saveBtn.disabled = true;

        // Kalau data sudah ada → disable input file
        [fileTrainingEval, fileSkillsEval, fileTrainingInEval].forEach(inp => {
          if (inp) inp.disabled = true;
        });

        // Set tombol view
        if (evalData.op_train_eval) {
          viewTrainingEval.classList.remove("d-none");
          viewTrainingEval.onclick = () => openBase64Pdf(evalData.op_train_eval);
        }
        if (evalData.op_skills_eval) {
          viewSkillsEval.classList.remove("d-none");
          viewSkillsEval.onclick = () => openBase64Pdf(evalData.op_skills_eval);
        }
        if (evalData.train_eval) {
          viewTrainingInEval.classList.remove("d-none");
          viewTrainingInEval.onclick = () => openBase64Pdf(evalData.train_eval);
        }
      }      
    
    }


  function viewFile(base64Data, fileName) {
      const link = document.createElement("a");
      link.href = `data:application/pdf;base64,${base64Data}`;
      link.target = "_blank";
      link.click();
  }

  // ================ File Validation ================
const validatePDF = (file) => {
    if (!file) return false;

    const isPDF = file.type === "application/pdf";
    const isSizeOk = file.size <= 10 * 1024 * 1024; // 1 MB = 1024 * 1024 bytes

    if (!isPDF) {
        alert("Only PDF files are allowed.");
        return false;
    }
    if (!isSizeOk) {
        alert("File size must not exceed 10 MB.");
        return false;
    }
    return true;
}

function fileToBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file); // this includes the data URL prefix
        reader.onload = () => {
            const base64 = reader.result.split(',')[1]; // remove the "data:application/pdf;base64," prefix
            resolve(base64);
        };
        reader.onerror = error => reject(error);
    });
}


// Gunakan di setiap input file
fileTrainingEval.addEventListener("change", e => {
    const file = e.target.files[0];
    if (validatePDF(file)) {
        uploadedFiles.trainingEval = file;
    } else {
        e.target.value = ""; // reset input jika invalid
        uploadedFiles.trainingEval = null;
    }
});
// ================ End File Validation ================

fileSkillsEval.addEventListener("change", e => {
    const file = e.target.files[0];
    if (validatePDF(file)) {
        uploadedFiles.skillsEval = file;
    } else {
        e.target.value = "";
        uploadedFiles.skillsEval = null;
    }
});

fileTrainingInEval.addEventListener("change", e => {
    const file = e.target.files[0];
    if (validatePDF(file)) {
        uploadedFiles.trainingInEval = file;
    } else {
        e.target.value = "";
        uploadedFiles.trainingInEval = null;
    }
});

    
  // ===================== Save data ============================
  saveBtn.addEventListener("click", async () => {
    // === Spinner ON + Disable tombol ===
    saveBtn.disabled = true;
    
    if (!operatorData) {
        alert("Please search and load operator data first.");
        saveBtn.disabled = false;
        return;
    }
    if (!uploadedFiles.trainingEval || !uploadedFiles.skillsEval || !uploadedFiles.trainingInEval) {
        alert("Please upload all three required documents before saving.");
        saveBtn.disabled = false;
        return;
    }

    const requiredFields = document.querySelectorAll(".required-field");
    for (let field of requiredFields) {
    if (field.value.trim() === "") {
        alert("Please complete all required fields before saving."); 
        saveBtn.disabled = false;
        return;
    }
}

    try {
        // ================= 1. Simpan Evaluation ke T_EvaluationDocument =================
        const base64TrainEval = await fileToBase64(uploadedFiles.trainingEval);
        const base64SkillsEval = await fileToBase64(uploadedFiles.skillsEval);
        const base64TrainingInEval = await fileToBase64(uploadedFiles.trainingInEval);

        // ================= 2. Ambil Certification dari backend =================
        const certRes = await fetch(`/api/certification?nik=${operatorData.NIK}`);
        const certData = await safeJson(certRes);
        if (!certData?.file_soldering || !certData?.file_screwing || !certData?.file_msa) {
            alert("3 Certification files are still missing in the system!");
            saveBtn.disabled = false;
            return;
        }

        // ambil certification dari backend
        const res = await fetch("/api/savemerge", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                nik: operatorData.NIK,
                op_train_eval: base64TrainEval,
                op_skills_eval: base64SkillsEval,
                train_eval: base64TrainingInEval,
                file_soldering: certData.file_soldering,
                file_screwing: certData.file_screwing,
                file_msa: certData.file_msa
            }),
        });

        if (!res.ok) throw new Error("Failed to save evaluation data.");
        console.log("Evaluation saved!");

        alert("Evaluation data saved successfully!");

        // Reload biar UI update
        setTimeout(() => window.location.reload(), 800);

    } catch (err) {
        console.error("Save+Merge error:", err);
        alert("An error occurred: " + err.message);
    } finally {
        // === Spinner OFF + Enable tombol lagi ===
        saveBtn.disabled = false;
    }
});


}); // DOMContentLoaded end


