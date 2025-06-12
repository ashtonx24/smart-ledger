function requireAuth() {
  const publicPaths = ["/register", "/login", "/select-db"];
  const isPublic = publicPaths.some(p => window.location.pathname.startsWith(p));
  
  if (!isPublic && !localStorage.getItem("access_token")) {
    window.location.href = "/login";
  }
}
requireAuth(); // run this at the top

function getHeaders() {
  const token = localStorage.getItem("access_token");
  const headers = {
    "Content-Type": "application/json",
    "X-Database-Name": localStorage.getItem("selectedDatabase") || "Practice"
  };
  if (token) {
    headers["Authorization"] = "Bearer " + token;
  }
  return headers;
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

// ===== Dynamic Table Creation Logic =====

function handleDynamicTablePage() {
  const tableNameInput = document.getElementById("table-name");
  const columnsTbody = document.getElementById("columns-tbody");
  const addColumnBtn = document.getElementById("add-column-btn");
  const createTableBtn = document.getElementById("create-table-btn");
  const sqlPreview = document.getElementById("sql-preview");
  const statusMsg = document.getElementById("status-msg");

  if (!tableNameInput || !columnsTbody || !addColumnBtn || !createTableBtn) return;

  // Supported types
  const dataTypes = ["INT", "VARCHAR(255)", "TEXT", "DATE", "FLOAT", "BOOLEAN"];

  // Initial state
  let columns = [
    { name: "", type: "INT", pk: false, notNull: false, unique: false }
  ];

  function renderColumns() {
    columnsTbody.innerHTML = "";
    columns.forEach((col, idx) => {
      const row = document.createElement("tr");

      // Name
      const nameTd = document.createElement("td");
      const nameInput = document.createElement("input");
      nameInput.type = "text";
      nameInput.value = col.name;
      nameInput.oninput = (e) => { columns[idx].name = e.target.value; updateSQLPreview(); };
      nameTd.appendChild(nameInput);

      // Type
      const typeTd = document.createElement("td");
      const typeSelect = document.createElement("select");
      dataTypes.forEach(type => {
        const opt = document.createElement("option");
        opt.value = type;
        opt.textContent = type;
        if (col.type === type) opt.selected = true;
        typeSelect.appendChild(opt);
      });
      typeSelect.onchange = (e) => { columns[idx].type = e.target.value; updateSQLPreview(); };
      typeTd.appendChild(typeSelect);

      // PK
      const pkTd = document.createElement("td");
      const pkCheckbox = document.createElement("input");
      pkCheckbox.type = "checkbox";
      pkCheckbox.checked = col.pk;
      pkCheckbox.onchange = (e) => { columns[idx].pk = e.target.checked; updateSQLPreview(); };
      pkTd.appendChild(pkCheckbox);

      // Not Null
      const nnTd = document.createElement("td");
      const nnCheckbox = document.createElement("input");
      nnCheckbox.type = "checkbox";
      nnCheckbox.checked = col.notNull;
      nnCheckbox.onchange = (e) => { columns[idx].notNull = e.target.checked; updateSQLPreview(); };
      nnTd.appendChild(nnCheckbox);

      // Unique
      const uqTd = document.createElement("td");
      const uqCheckbox = document.createElement("input");
      uqCheckbox.type = "checkbox";
      uqCheckbox.checked = col.unique;
      uqCheckbox.onchange = (e) => { columns[idx].unique = e.target.checked; updateSQLPreview(); };
      uqTd.appendChild(uqCheckbox);

      // Remove
      const removeTd = document.createElement("td");
      if (columns.length > 1) {
        const removeBtn = document.createElement("button");
        removeBtn.textContent = "Remove";
        removeBtn.className = "btn btn-remove";
        removeBtn.onclick = () => { columns.splice(idx, 1); renderColumns(); updateSQLPreview(); };
        removeTd.appendChild(removeBtn);
      }

      row.appendChild(nameTd);
      row.appendChild(typeTd);
      row.appendChild(pkTd);
      row.appendChild(nnTd);
      row.appendChild(uqTd);
      row.appendChild(removeTd);

      columnsTbody.appendChild(row);
    });
  }

  function updateSQLPreview() {
    const tableName = tableNameInput.value.trim() || "table_name";
    const colDefs = columns.map(col => {
      let def = `${col.name || "col"} ${col.type}`;
      if (col.pk) def += " PRIMARY KEY";
      if (col.notNull) def += " NOT NULL";
      if (col.unique) def += " UNIQUE";
      return def;
    });
    sqlPreview.textContent = `CREATE TABLE ${tableName} (${colDefs.join(", ")});`;
  }

  addColumnBtn.onclick = () => {
    columns.push({ name: "", type: "INT", pk: false, notNull: false, unique: false });
    renderColumns();
    updateSQLPreview();
  };

  tableNameInput.oninput = updateSQLPreview;

  createTableBtn.onclick = async () => {
    statusMsg.textContent = "";
    statusMsg.classList.remove("error");

    const tableName = tableNameInput.value.trim();
    if (!tableName) {
      statusMsg.textContent = "Table name required.";
      statusMsg.classList.add("error");
      return;
    }
    if (columns.some(col => !col.name)) {
      statusMsg.textContent = "All columns must have a name.";
      statusMsg.classList.add("error");
      return;
    }

    // Prepare payload
    const payload = {
      table_name: tableName,
      columns: columns.map(col => ({
        name: col.name,
        type: col.type,
        constraints: [
          ...(col.pk ? ["PRIMARY KEY"] : []),
          ...(col.notNull ? ["NOT NULL"] : []),
          ...(col.unique ? ["UNIQUE"] : [])
        ]
      }))
    };

    // Get shop name from URL (assuming /shop/{shop_name}/dynamic-table)
    const pathParts = window.location.pathname.split("/");
    const shopName = pathParts[pathParts.indexOf("shop") + 1];

    try {
      const res = await fetch(`/shops/${shopName}/create-dynamic-table`, {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (res.ok) {
        statusMsg.textContent = `✅ Table created! SQL: ${data.sql}`;
        statusMsg.classList.remove("error");
      } else {
        statusMsg.textContent = `❌ Error: ${data.detail || "Unknown error"}`;
        statusMsg.classList.add("error");
      }
    } catch (err) {
      statusMsg.textContent = "❌ Network/server error.";
      statusMsg.classList.add("error");
    }
  };

  // Initial render
  renderColumns();
  updateSQLPreview();
}

// Add to your DOMContentLoaded handler:
document.addEventListener("DOMContentLoaded", () => {
  // ...existing handlers
  handleDynamicTablePage();
});

function handleLoginPage() {
  const shopInput = document.getElementById("shop-name");
  const userInput = document.getElementById("username");
  const passInput = document.getElementById("password");
  const btn = document.getElementById("login-btn");
  const status = document.getElementById("login-status");
  if (!btn) return;

  btn.onclick = async () => {
    status.textContent = "Logging in...";
    try {
      const res = await fetch(`/login?shop_name=${encodeURIComponent(shopInput.value)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: userInput.value,
          password: passInput.value
        })
      });
      const data = await res.json();
      if (res.ok) {
        localStorage.setItem("access_token", data.access_token);
        status.textContent = "Login successful!";
        // Redirect to dashboard
        window.location.href = `/shop/${shopInput.value}`;
      } else {
        status.textContent = data.detail || "Login failed";
      }
    } catch {
      status.textContent = "Network error.";
    }
  };
}

document.addEventListener("DOMContentLoaded", () => {
  handleLoginPage();
  // ...other handlers
});
