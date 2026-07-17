import { useEffect, useRef, useState } from "react";
import { api, downloadUrl } from "../api";
import { num2, pct2 } from "../format";
import { wrapHeader } from "../wrapHeader";

const LAMPIRAN_PICS = [
  {
    role: "dibuat",
    title: "Dibuat Oleh",
    namaKey: "nama_dibuat",
    jabatanKey: "jabatan_dibuat",
    hasKey: "has_ttd_dibuat",
  },
  {
    role: "diperiksa",
    title: "Diperiksa Oleh",
    namaKey: "nama_diperiksa",
    jabatanKey: "jabatan_diperiksa",
    hasKey: "has_ttd_diperiksa",
  },
  {
    role: "diketahui",
    title: "Diketahui Oleh",
    namaKey: "nama_diketahui",
    jabatanKey: "jabatan_diketahui",
    hasKey: "has_ttd_diketahui",
  },
] as const;

export default function LampiranPage() {
  const [data, setData] = useState<any>(null);
  const [unit, setUnit] = useState("");
  const [cfg, setCfg] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [ttdBust, setTtdBust] = useState(Date.now());
  const fileRefs = useRef<Record<string, HTMLInputElement | null>>({});

  useEffect(() => {
    api.baConfig().then(setCfg).catch(() => undefined);
    api.lampiran().then((d) => {
      setData(d);
      setUnit(d.unit || d.units?.[0] || "");
    }).catch((e) => setErr(e.message));
  }, []);

  async function load(u: string) {
    try {
      const d = await api.lampiran(u);
      setData(d);
      setUnit(d.unit || u);
      setErr(null);
    } catch (e: any) {
      setErr(e.message);
    }
  }

  async function saveNames() {
    if (!cfg) return;
    try {
      const payload = {
        ...cfg,
        jabatan_diketahui: cfg.vendor ? `Admin ${cfg.vendor}` : "Admin Vendor",
      };
      setCfg(await api.saveBaConfig(payload));
      setMsg("Nama & jabatan TTD tersimpan");
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

  const rows = data?.rows || [];
  const sub = data?.subtotal || {};
  const names = data?.names || cfg || {};

  return (
    <div className="card doc-page">
      <h1>Lampiran</h1>
      <p className="muted">Preview mengikuti layout & warna sheet Lampiran Excel.</p>
      {err && <div className="alert error">{err}</div>}
      {msg && <div className="alert ok">{msg}</div>}

      {cfg && (
        <>
          <h2>TTD Lampiran (PIC)</h2>
          <div className="grid grid-3">
            {LAMPIRAN_PICS.map((pic) => {
              const has = Boolean(cfg[pic.hasKey]);
              return (
                <div key={pic.role} className="ttd-upload-card">
                  <div className="ttd-upload-title">{pic.title}</div>
                  <label>Nama
                    <input
                      value={cfg[pic.namaKey] || ""}
                      onChange={(e) => setCfg({ ...cfg, [pic.namaKey]: e.target.value })}
                    />
                  </label>
                  <label>Jabatan
                    <input
                      value={
                        pic.role === "diketahui"
                          ? (cfg.vendor ? `Admin ${cfg.vendor}` : "Admin Vendor")
                          : (cfg[pic.jabatanKey] || "")
                      }
                      readOnly={pic.role === "diketahui"}
                      onChange={(e) => {
                        if (pic.role === "diketahui") return;
                        setCfg({ ...cfg, [pic.jabatanKey]: e.target.value });
                      }}
                      title={pic.role === "diketahui" ? "Otomatis dari vendor Cover BA" : undefined}
                    />
                  </label>
                  <div className="ttd-upload-preview">
                    {has ? (
                      <img
                        src={api.ttdUrl(pic.role, ttdBust)}
                        alt={`TTD ${pic.title}`}
                      />
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
                      const f = e.target.files?.[0];
                      onPickTtd(pic.role, f);
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
                      <button
                        type="button"
                        className="btn danger"
                        onClick={() => onClearTtd(pic.role)}
                      >
                        Hapus
                      </button>
                    )}
                  </div>
                  <div className={`ttd-status ${has ? "ok" : ""}`}>
                    {has ? "TTD tersimpan" : "Belum diunggah"}
                  </div>
                </div>
              );
            })}
          </div>
          <div className="actions">
            <button className="btn secondary" onClick={saveNames}>Simpan Nama TTD</button>
          </div>
        </>
      )}

      <div className="actions" style={{ marginTop: "1rem" }}>
        <button className="btn accent" disabled={!unit} onClick={() => downloadUrl(`/api/ba/lampiran/export?unit=${encodeURIComponent(unit)}`)}>
          Export Excel
        </button>
        <button
          className="btn"
          disabled={!(data?.units?.length)}
          onClick={() => downloadUrl(`/api/ba/lampiran/export-pdf${cfg?.vendor ? `?vendor=${encodeURIComponent(cfg.vendor)}` : ""}`)}
          title="Export PDF semua unit di dropdown"
        >
          Export PDF (Semua Unit)
        </button>
      </div>

      {data && (
        <div className="doc-sheet lampiran-sheet doc-page-frame" style={{ marginTop: "1.25rem" }}>
          <div className="lampiran-pick no-print">
            <label className="lampiran-pick-label">
              <span>PILIH UNIT:</span>
              <select
                className="lampiran-pick-select"
                value={unit}
                onChange={(e) => {
                  const u = e.target.value;
                  setUnit(u);
                  load(u);
                }}
              >
                {(data.unit_options || data.units || []).map((opt: any) => {
                  const code = typeof opt === "string" ? opt : opt.code_unit;
                  return (
                    <option key={code} value={code}>{code}</option>
                  );
                })}
              </select>
            </label>
          </div>

          <div className="doc-top">
            <div className="lampiran-title">
              DAILY REKAPITULASI PEMAKAIAN UNIT RENTAL {data.vendor}
            </div>

            <div className="lampiran-meta">
              <div>
                <div><strong>Type Unit&nbsp;&nbsp;&nbsp;:</strong> {data.type_unit || "—"}</div>
                <div><strong>Code Unit :</strong> {data.unit}</div>
              </div>
              <div className="lampiran-meta-right">
                <div><strong>Th Unit:</strong> {data.th_unit || "—"}</div>
                <div><strong>PA :</strong> {pct2(data.pa)}</div>
              </div>
            </div>

            <div className="doc-table-wrap">
              <table className="doc-table lampiran-table">
                <thead>
                  <tr>
                    <th rowSpan={2} className="head-soft">{wrapHeader("DATE")}</th>
                    <th rowSpan={2} className="head-soft">{wrapHeader("SHIFT")}</th>
                    <th colSpan={5} className="head-soft">{wrapHeader("Hour meter (HM)")}</th>
                    <th colSpan={3} className="head-soft">{wrapHeader("Status (Jam)")}</th>
                    <th rowSpan={2} className="head-soft">{wrapHeader("AREA KERJA")}</th>
                    <th rowSpan={2} className="head-soft">{wrapHeader("PEKERJAAN")}</th>
                    <th rowSpan={2} className="head-soft">{wrapHeader("KETERANGAN")}</th>
                  </tr>
                  <tr>
                    <th className="head-soft">{wrapHeader("HM Start")}</th>
                    <th className="head-soft">{wrapHeader("HM Stop")}</th>
                    <th className="head-soft">{wrapHeader("HM Stop")}</th>
                    <th className="head-soft">{wrapHeader("HM Not Working")}</th>
                    <th className="head-soft">{wrapHeader("HM Working")}</th>
                    <th className="head-soft">{wrapHeader("BD & No Operator")}</th>
                    <th className="head-soft">{wrapHeader("Standby Force Majeure")}</th>
                    <th className="head-soft">{wrapHeader("Standby Schedule")}</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r: any, i: number) => (
                    <tr key={i}>
                      <td className="cell-center">{r.DATE}</td>
                      <td className="cell-center">{r.SHIFT}</td>
                      <td className="cell-num">{num2(r.HM_START)}</td>
                      <td className="cell-num">{num2(r.HM_STOP)}</td>
                      <td className="cell-num">{num2(r.HM_STOP_ADJ ?? r.HM_STOP)}</td>
                      <td className="cell-num">{num2(r.HM_NOT_WORKING)}</td>
                      <td className="cell-num">{num2(r.HM_WORKING ?? r.WORKING)}</td>
                      <td className="cell-num">{num2(r.BD)}</td>
                      <td className="cell-num">{num2(r.FM)}</td>
                      <td className="cell-num">{num2(r.STBY)}</td>
                      <td className="cell-wrap">{r.AREA || ""}</td>
                      <td className="cell-wrap">{r.PEKERJAAN || ""}</td>
                      <td className="cell-wrap">{r.KETERANGAN || r.INFORMATION || ""}</td>
                    </tr>
                  ))}
                  <tr className="row-subtotal">
                    <td colSpan={6} className="cell-sub-lab"><strong>SUBTOTAL</strong></td>
                    <td className="cell-num"><strong>{num2(sub.HM_WORKING)}</strong></td>
                    <td className="cell-num"><strong>{num2(sub.BD)}</strong></td>
                    <td className="cell-num"><strong>{num2(sub.FM)}</strong></td>
                    <td className="cell-num"><strong>{num2(sub.STBY)}</strong></td>
                    <td colSpan={3} />
                  </tr>
                  {!rows.length && (
                    <tr><td colSpan={13}>Belum ada data untuk unit ini.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="doc-bottom">
            <div className="ttd-grid lampiran-ttd">
              {LAMPIRAN_PICS.map((pic) => {
                const has = Boolean(cfg?.[pic.hasKey]);
                return (
                  <div key={pic.role} className="ttd-block">
                    <div className="ttd-role">{pic.title},</div>
                    <div className="ttd-space">
                      {has && (
                        <img
                          className="ttd-img"
                          src={api.ttdUrl(pic.role, ttdBust)}
                          alt={`TTD ${pic.title}`}
                        />
                      )}
                    </div>
                    <div className="ttd-nama">{names[pic.namaKey] || cfg?.[pic.namaKey]}</div>
                    <div className="ttd-jabatan">
                      {pic.role === "diketahui"
                        ? (names.jabatan_diketahui || (data.vendor ? `Admin ${data.vendor}` : "Admin Vendor"))
                        : (names[pic.jabatanKey] || cfg?.[pic.jabatanKey])}
                    </div>
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
