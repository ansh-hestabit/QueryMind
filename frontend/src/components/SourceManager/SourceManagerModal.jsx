import { useState, useCallback, useRef } from "react";
import "./SourceManagerModal.css";

const API_BASE = "/api/v1";

const SOURCE_TYPE_FIELDS = {
  postgresql: [
    { key: "host", label: "Host", placeholder: "localhost", type: "text" },
    { key: "port", label: "Port", placeholder: "5432", type: "number" },
    { key: "database", label: "Database", placeholder: "mydb", type: "text" },
    { key: "username", label: "Username", placeholder: "postgres", type: "text" },
    { key: "password", label: "Password", placeholder: "••••••••", type: "password" },
  ],
  mongodb: [
    { key: "uri", label: "Connection URI", placeholder: "mongodb+srv://user:pass@cluster.mongodb.net/mydb", type: "text" },
  ],
};

export default function SourceManagerModal({ onClose, onSourceAdded }) {
  const [activeTab, setActiveTab] = useState("upload");

  // Upload state
  const [dragOver, setDragOver]     = useState(false);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadName, setUploadName] = useState("");
  const [uploading, setUploading]   = useState(false);
  const [uploadError, setUploadError] = useState("");
  const fileInputRef = useRef(null);

  // Credentials form state
  const [sourceType, setSourceType] = useState("postgresql");
  const [fields, setFields]         = useState({});
  const [sourceName, setSourceName] = useState("");
  const [connecting, setConnecting] = useState(false);
  const [connectError, setConnectError] = useState("");

  // ── File Upload handlers ───────────────────────────────────────────────────
  const handleFileDrop = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer?.files?.[0];
    if (f) selectFile(f);
  }, []);

  const selectFile = (f) => {
    setUploadFile(f);
    setUploadName(f.name.replace(/\.[^.]+$/, ""));
    setUploadError("");
  };

  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    if (!uploadFile) return;
    setUploading(true);
    setUploadError("");
    try {
      const form = new FormData();
      form.append("file", uploadFile);
      form.append("name", uploadName || uploadFile.name);
      const res = await fetch(`${API_BASE}/sources/upload`, { method: "POST", body: form });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Upload failed" }));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      const source = await res.json();
      onSourceAdded(source);
      onClose();
    } catch (err) {
      setUploadError(err.message);
    } finally {
      setUploading(false);
    }
  };

  // ── Credentials Form handlers ──────────────────────────────────────────────
  const handleFieldChange = (key, value) => setFields((f) => ({ ...f, [key]: value }));

  const handleConnectSubmit = async (e) => {
    e.preventDefault();
    if (!sourceName.trim()) { setConnectError("Source name is required."); return; }
    setConnecting(true);
    setConnectError("");
    try {
      const credentials = { ...fields };
      if (sourceType === "postgresql") credentials.port = parseInt(credentials.port || "5432", 10);
      const res = await fetch(`${API_BASE}/sources`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: sourceName, source_type: sourceType, credentials }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Registration failed" }));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      const source = await res.json();
      // Trigger schema crawl
      await fetch(`${API_BASE}/sources/${source.id}/crawl-schema`, { method: "POST" });
      onSourceAdded(source);
      onClose();
    } catch (err) {
      setConnectError(err.message);
    } finally {
      setConnecting(false);
    }
  };

  return (
    <div className="modal-backdrop" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal-box" role="dialog" aria-modal="true" aria-label="Add Data Source">
        <div className="modal-header">
          <span className="modal-title">Add Data Source</span>
          <button className="modal-close" onClick={onClose} aria-label="Close">✕</button>
        </div>

        <div className="modal-tabs">
          <button
            id="tab-upload"
            className={`modal-tab ${activeTab === "upload" ? "active" : ""}`}
            onClick={() => setActiveTab("upload")}
          >
            📂 Upload File
          </button>
          <button
            id="tab-connect"
            className={`modal-tab ${activeTab === "connect" ? "active" : ""}`}
            onClick={() => setActiveTab("connect")}
          >
            🔌 Connect Database
          </button>
        </div>

        {/* ── Tab: Upload File ─────────────────────────────────────────── */}
        {activeTab === "upload" && (
          <form onSubmit={handleUploadSubmit} className="modal-body">
            <div
              id="drop-zone"
              className={`drop-zone ${dragOver ? "drag-over" : ""} ${uploadFile ? "has-file" : ""}`}
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleFileDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,.parquet,.tsv"
                style={{ display: "none" }}
                onChange={(e) => e.target.files[0] && selectFile(e.target.files[0])}
              />
              {uploadFile ? (
                <>
                  <div className="drop-icon">✅</div>
                  <div className="drop-filename">{uploadFile.name}</div>
                  <div className="drop-hint">({(uploadFile.size / 1024).toFixed(1)} KB) — click to change</div>
                </>
              ) : (
                <>
                  <div className="drop-icon">📁</div>
                  <div className="drop-label">Drag & drop a file here</div>
                  <div className="drop-hint">Supports .csv, .parquet, .tsv — click to browse</div>
                </>
              )}
            </div>

            <label className="field-label">
              Source Name
              <input
                id="upload-name"
                className="field-input"
                type="text"
                placeholder="My Dataset"
                value={uploadName}
                onChange={(e) => setUploadName(e.target.value)}
              />
            </label>

            {uploadError && <div className="modal-error">{uploadError}</div>}

            <button
              id="btn-upload-submit"
              type="submit"
              className="modal-submit"
              disabled={!uploadFile || uploading}
            >
              {uploading ? (
                <><span className="spinner" /> Uploading & indexing…</>
              ) : "Upload & Register"}
            </button>
          </form>
        )}

        {/* ── Tab: Connect Database ────────────────────────────────────── */}
        {activeTab === "connect" && (
          <form onSubmit={handleConnectSubmit} className="modal-body">
            <label className="field-label">
              Source Name
              <input
                id="connect-name"
                className="field-input"
                type="text"
                placeholder="My Production DB"
                value={sourceName}
                onChange={(e) => setSourceName(e.target.value)}
                required
              />
            </label>

            <label className="field-label">
              Database Type
              <select
                id="db-type-select"
                className="field-input"
                value={sourceType}
                onChange={(e) => { setSourceType(e.target.value); setFields({}); }}
              >
                <option value="postgresql">PostgreSQL</option>
                <option value="mongodb">MongoDB</option>
              </select>
            </label>

            {(SOURCE_TYPE_FIELDS[sourceType] || []).map((f) => (
              <label key={f.key} className="field-label">
                {f.label}
                <input
                  id={`field-${f.key}`}
                  className="field-input"
                  type={f.type}
                  placeholder={f.placeholder}
                  value={fields[f.key] || ""}
                  onChange={(e) => handleFieldChange(f.key, e.target.value)}
                  required
                />
              </label>
            ))}

            {connectError && <div className="modal-error">{connectError}</div>}

            <button
              id="btn-connect-submit"
              type="submit"
              className="modal-submit"
              disabled={connecting}
            >
              {connecting ? (
                <><span className="spinner" /> Connecting & indexing schema…</>
              ) : "Connect & Register"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
