function getHeaders() {
  return {
    "Content-Type": "application/json",
    "X-Database-Name": localStorage.getItem("selectedDatabase") || "Practice"
  };
}

function setStatus(message, isError = false) {
  const statusMsg = document.getElementById("status-msg");
  if (!statusMsg) return;
  statusMsg.textContent = message;
  statusMsg.classList.toggle("error", isError);
}

// Logic for select-db.html
async function handleDatabaseSelectionPage() {
  const dbSelect = document.getElementById("db-select");
  const selectBtn = document.getElementById("select-btn");

  if (!dbSelect || !selectBtn) return;

  // Load databases on page load
  try {
    const res = await fetch("/shops");
    const data = await res.json();
    dbSelect.innerHTML = "";

    const defaultOpt = document.createElement("option");
    defaultOpt.value = "Practice";
    defaultOpt.textContent = "Practice (Primary DB)";
    dbSelect.appendChild(defaultOpt);

    data.shops.forEach((db) => {
      const opt = document.createElement("option");
      opt.value = db;
      opt.textContent = db;
      dbSelect.appendChild(opt);
    });

    const saved = localStorage.getItem("selectedDatabase");
    if (saved) {
      dbSelect.value = saved;
      setStatus(`Database "${saved}" selected.`);
    }
  } catch {
    setStatus("Failed to load databases.", true);
  }

  selectBtn.addEventListener("click", () => {
    const selected = dbSelect.value;
    localStorage.setItem("selectedDatabase", selected);

    fetch("/select-db", {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ db_name: selected })
    })
      .then(res => res.json())
      .then(() => {
        setStatus(`Database "${selected}" selected successfully.`);
      })
      .catch(err => {
        setStatus(`Error selecting DB: ${err.message}`, true);
      });
  });
}

// Logic for create-db.html
function handleCreateDbPage() {
  const createBtn = document.getElementById("create-btn");
  const shopInput = document.getElementById("shop-name");

  if (!createBtn || !shopInput) return;

  createBtn.addEventListener("click", async () => {
    const name = shopInput.value.trim();
    if (!name) {
      setStatus("Please enter a shop name.", true);
      return;
    }

    setStatus("Creating database...");

    try {
      const res = await fetch("/shops", {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify({ name, owner: "default_owner" })
      });
      const data = await res.json();

      if (res.ok) {
        setStatus(`Success! Database created: ${data.database}`);
        shopInput.value = "";
      } else {
        setStatus(`Error: ${data.detail || "Unknown error"}`, true);
      }
    } catch {
      setStatus("Network error. Please try again.", true);
    }
  });
}

// Logic for shop.html
function handleShopDashboard() {
  const shopName = window.location.pathname.split("/").pop().toLowerCase();
  const title = document.getElementById("shop-title");

  if (!title) return;

  document.title = `Shop: ${shopName}`;
  title.textContent = `Dashboard – ${shopName}`;

  window.createTable = async function (type) {
    try {
      const res = await fetch(`/shops/${shopName}/create-table`, {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify({ table_type: type })
      });

      const data = await res.json();
      if (res.ok) {
        setStatus(`✅ '${type}' table created successfully.`);
      } else {
        setStatus(`❌ Error: ${data.detail}`, true);
      }
    } catch {
      setStatus("❌ Network error or server issue.", true);
    }
  };
}

// Auto-detect page type and invoke handler
document.addEventListener("DOMContentLoaded", () => {
  handleDatabaseSelectionPage();
  handleCreateDbPage();
  handleShopDashboard();
});
