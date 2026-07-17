import { useEffect, useRef, useState } from "react";
import { api, downloadUrl } from "../api";
import { num2 } from "../format";
import { wrapHeader } from "../wrapHeader";

const BA_COLS = [
  "No", "PO Numb.", "Periode PO", "Type Alat", "No Unit", "Tahun Unit",
  "PA Unit", "Total HM Sebelum Dipotong", "Total Pemotongan HM",
  "BD & No Operator", "Standby Force Majeure", "Standby Schedule",
  "TOTAL HM", "PA<80%", "PA>90%", "HM Yang Ditagihkan", "KETERANGAN PEKERJAAN",
];

const NUM_COLS = new Set([
  "Total HM Sebelum Dipotong", "Total Pemotongan HM", "BD & No Operator",
  "Standby Force Majeure", "Standby Schedule", "TOTAL HM",
  "PA<80%", "PA>90%", "HM Yang Ditagihkan",
]);

const BA_PICS_TIER1 = [
  { role: "admin", title: "Admin Project", roleLabel: "Dibuat Oleh,", namaKey: "nama_admin", hasKey: "has_ttd_admin" },
  { role: "sp", title: "Superintendent Project", roleLabel: "Mengetahui,", namaKey: "nama_sp", hasKey: "has_ttd_sp" },
  { role: "pm", title: "Manager Project PT. KAN", roleLabel: "Diperiksa Oleh,", namaKey: "nama_pm", hasKey: "has_ttd_pm" },
  { role: "sig", title: "SIG", roleLabel: "Mengetahui,", namaKey: "nama_sig", hasKey: "has_ttd_sig" },
] as const;

const BA_PICS_TIER2 = [
  { role: "pjo", title: "PJO Vendor", roleLabel: "Disetujui Oleh,", namaKey: "nama_pjo", hasKey: "has_ttd_pjo", jabatan: "Penanggung Jawab Operasional" },
  { role: "ml", title: "Manager Logistik PT. KAN", roleLabel: "Diketahui Oleh,", namaKey: "nama_ml", hasKey: "has_ttd_ml", jabatan: "Manager Logistik dan Commercial" },
] as const;

const NO_THOUSAND_SEP = new Set(["No", "No Unit", "Tahun Unit", "PO Numb.", "Periode PO"]);

function formatBaCell(k: string, v: unknown): string {
  if (v === null || v === undefined || v === "") return "";
  if (k === "PA Unit") return `${num2(Number(v) * 100)}%`;
  if (NO_THOUSAND_SEP.has(k)) return String(v).trim();
  if (NUM_COLS.has(k) || (typeof v === "number" && Number.isFinite(v))) return num2(v);
  if (typeof v === "string" && /^-?\d+(\.\d+)?$/.test(v.trim())) return num2(v);
  return String(v);
}

function sumCol(rows: any[], col: string): number {
  return rows.reduce((acc, r) => acc + (Number(r?.[col]) || 0), 0);
}

export default function BeritaAcaraPage() {
  const [cfg, setCfg] = useState<any>(null);
  const [preview, setPreview] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [ttdBust, setTtdBust] = useState(Date.now());
  const fileRefs = useRef<Record<string, HTMLInputElement | null>>({});

  useEffect(() => {
    api.baConfig().then(setCfg).catch((e) => setErr(e.message));
  }, []);

  async function save() {
    try {
      setCfg(await api.saveBaConfig(cfg));
      setMsg("Konfigurasi BA tersimpan");
    } catch (e: any) {
      setErr(e.message);
    }
  }

  async function loadPreview() {
    try {
      setPreview(await api.baPreview(cfg?.vendor || undefined));
      setErr(null);
    } catch (e: any) {
      setErr(e.message);
    }
  }

  async function onPickTtd(role: string, file?: File | null) {
    if (!file) return;
    try {
      await api.uploadTtd(role, file);
      setCfg(await api.baConfig());
      setTtdBust(Date.now());
      setMsg(`Tanda tangan ${role} berhasil diunggah`);
      setErr(null);
    } catch (e: any) {
      setErr(e.message);
    }
  }

  async function onClearTtd(role: string) {
    if (!confirm("Hapus tanda tangan ini?")) return;
    try {
      await api.deleteTtd(role);
      setCfg(await api.baConfig());
      setTtdBust(Date.now());
      setMsg(`Tanda tangan ${role} dihapus`);
    } catch (e: any) {
      setErr(e.message);
    }
  }

  function renderTtdCard(pic: {
    role: string;
    title: string;
    namaKey: string;
    hasKey: string;
  }) {
    const has = Boolean(cfg[pic.hasKey]);
    return (
      <div key={pic.role} className="ttd-upload-card">
        <div className="ttd-upload-title">{pic.title}</div>
        <label>Nama
          <input
            value={cfg[pic.namaKey] || ""}
            onChange={(e) => set(pic.namaKey, e.target.value)}
          />
        </label>
        <div className="ttd-upload-preview">
          {has ? (
            <img src={api.ttdUrl(pic.role, ttdBust)} alt={`TTD ${pic.title}`} />
          ) : (
            <span className="muted">Belum ada tanda tangan</span>
          )}
        </div>
        <input
          ref={(el) => { fileRefs.current[pic.role] = el; }}
          type="file"
          accept="image/png,image/jpeg,image/webp,image/gif"
          hidden
          onChange={(e) => {
            onPickTtd(pic.role, e.target.files?.[0]);
            e.target.value = "";
          }}
        />
        <div className="actions" style={{ marginTop: "0.5rem" }}>
          <button
            type="button"
            className="btn secondary"
            onClick={() => fileRefs.current[pic.role]?.click()}
          >
            Browse TTD
          </button>
          {has && (
            <button type="button" className="btn danger" onClick={() => onClearTtd(pic.role)}>
              Hapus
            </button>
          )}
        </div>
        <div className={`ttd-status ${has ? "ok" : ""}`}>
          {has ? "TTD tersimpan" : "Belum diunggah"}
        </div>
      </div>
    );
  }

  if (!cfg) return <div className="card">Memuat konfigurasi…</div>;

  function set(k: string, v: string) {
    setCfg((c: any) => ({ ...c, [k]: v }));
  }

  const cols = preview?.columns?.length ? preview.columns : BA_COLS;
  const rows = preview?.rows || [];
  const vendorShort = (preview?.vendor || cfg.vendor || "").replace(/PT\.?\s*/i, "").trim();
  const companyName = preview?.company_name || "PT. Kayong Aluminium Nusantara";

  return (
    <div className="card doc-page">
      <h1>Berita Acara</h1>
      <p className="muted">Preview mengikuti layout & warna COVER BA Excel.</p>
      {err && <div className="alert error">{err}</div>}
      {msg && <div className="alert ok">{msg}</div>}

      <h2>Konfigurasi</h2>
      <div className="grid grid-3">
        <label>Nomor BA<input value={cfg.no_ba} onChange={(e) => set("no_ba", e.target.value)} /></label>
        <label>Lokasi TTD<input value={cfg.lokasi_ttd} onChange={(e) => set("lokasi_ttd", e.target.value)} /></label>
        <label>Vendor<input value={cfg.vendor} onChange={(e) => set("vendor", e.target.value)} placeholder="PT. PIK" /></label>
      </div>

      <h2 style={{ marginTop: "1rem" }}>TTD Tier 1 (PIC)</h2>
      <div className="grid grid-4">
        {BA_PICS_TIER1.map(renderTtdCard)}
      </div>

      <h2 style={{ marginTop: "1rem" }}>TTD Tier 2 (PIC)</h2>
      <div className="grid grid-2">
        {BA_PICS_TIER2.map(renderTtdCard)}
      </div>

      <div className="actions">
        <button className="btn secondary" onClick={save}>Simpan Config</button>
        <button className="btn" onClick={loadPreview}>Preview BA</button>
        <button className="btn accent" onClick={() => downloadUrl(`/api/ba/export${cfg.vendor ? `?vendor=${encodeURIComponent(cfg.vendor)}` : ""}`)}>
          Export Excel
        </button>
        <button className="btn" onClick={() => downloadUrl(`/api/ba/export-pdf${cfg.vendor ? `?vendor=${encodeURIComponent(cfg.vendor)}` : ""}`)}>
          Export PDF
        </button>
      </div>

      {preview && (
        <div className="doc-sheet ba-sheet doc-page-frame" style={{ marginTop: "1.25rem" }}>
          <div className="doc-top">
            <div className="ba-kop">{preview.company_name || "PT. Kayong Aluminium Nusantara"}</div>
            <div className="ba-alamat">{preview.company_address_line1}</div>
            <div className="ba-alamat">{preview.company_address_line2}</div>

            <div className="ba-judul">{preview.title}</div>
            <div className="ba-no">No.{preview.no_ba}</div>
            <p className="ba-narasi">{preview.narasi}</p>

            <div className="doc-table-wrap">
              <table className="doc-table ba-table">
                <thead>
                  <tr>
                    {cols.map((k: string) => {
                      if (k === "BD & No Operator") {
                        return <th key="Status" colSpan={3} className="head-gray">{wrapHeader("Status")}</th>;
                      }
                      if (k === "Standby Force Majeure" || k === "Standby Schedule") return null;
                      return (
                        <th key={k} rowSpan={2} className="head-gray">{wrapHeader(k)}</th>
                      );
                    })}
                  </tr>
                  <tr>
                    <th className="head-gray">{wrapHeader("BD & No Operator")}</th>
                    <th className="head-gray">{wrapHeader("Standby Force Majeure")}</th>
                    <th className="head-gray">{wrapHeader("Standby Schedule")}</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r: any, i: number) => (
                    <tr key={i}>
                      {cols.map((k: string) => (
                        <td
                          key={k}
                          className={
                            k === "HM Yang Ditagihkan"
                              ? "cell-tagih"
                              : k === "KETERANGAN PEKERJAAN"
                                ? "cell-wrap"
                                : NUM_COLS.has(k) || k === "PA Unit"
                                  ? "cell-num"
                                  : "cell-center"
                          }
                        >
                          {formatBaCell(k, r[k])}
                        </td>
                      ))}
                    </tr>
                  ))}
                  {!!rows.length && (
                    <tr className="row-total">
                      {cols.map((k: string) => {
                        if (k === "PO Numb.") return <td key={k} colSpan={3} className="head-gray"><strong>Grand Total</strong></td>;
                        if (k === "Periode PO" || k === "Type Alat") return null;
                        if (NUM_COLS.has(k)) return <td key={k} className="head-gray cell-num"><strong>{num2(sumCol(rows, k))}</strong></td>;
                        return <td key={k} className="head-gray" />;
                      })}
                    </tr>
                  )}
                  {!rows.length && (
                    <tr><td colSpan={cols.length}>Belum ada data.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="doc-bottom">
            <p className="ba-tgl">{preview.tanggal_ttd}</p>

            <div className="ttd-grid tier1">
              {BA_PICS_TIER1.map((pic) => {
                const has = Boolean(cfg[pic.hasKey]);
                return (
                  <div key={pic.role} className="ttd-block">
                    <div className="ttd-inst">{companyName}</div>
                    <div className="ttd-role">{pic.roleLabel}</div>
                    <div className="ttd-space">
                      {has && (
                        <img className="ttd-img" src={api.ttdUrl(pic.role, ttdBust)} alt={`TTD ${pic.title}`} />
                      )}
                    </div>
                    <div className="ttd-nama">{cfg[pic.namaKey]}</div>
                    <div className="ttd-jabatan">{pic.title}</div>
                  </div>
                );
              })}
            </div>

            <div className="ttd-grid tier2">
              {BA_PICS_TIER2.map((pic) => {
                const has = Boolean(cfg[pic.hasKey]);
                const inst = pic.role === "pjo"
                  ? `PT. ${vendorShort}`
                  : companyName;
                return (
                  <div key={pic.role} className="ttd-block">
                    <div className="ttd-inst">{inst}</div>
                    <div className="ttd-role">{pic.roleLabel}</div>
                    <div className="ttd-space">
                      {has && (
                        <img className="ttd-img" src={api.ttdUrl(pic.role, ttdBust)} alt={`TTD ${pic.title}`} />
                      )}
                    </div>
                    <div className="ttd-nama">{cfg[pic.namaKey]}</div>
                    <div className="ttd-jabatan">{pic.jabatan}</div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
