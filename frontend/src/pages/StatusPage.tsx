import { useEffect, useState } from "react";
import { api } from "../api";

export default function StatusPage() {
  const [count, setCount] = useState(0);
  const [err, setErr] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => {
    api.statusCount().then((r) => setCount(r.count)).catch(() => undefined);
  }, []);

  async function onImport(file: File | null) {
    if (!file) return;
    try {
      const r: any = await api.importStatus(file);
      setMsg(r.message);
      setCount((await api.statusCount()).count);
      setErr(null);
    } catch (e: any) {
      setErr(e.message);
    }
  }

  async function onImportPo(file: File | null) {
    if (!file) return;
    try {
      const r: any = await api.importPo(file);
      setMsg(r.message);
      setErr(null);
    } catch (e: any) {
      setErr(e.message);
    }
  }

  return (
    <div className="card">
      <h1>Impor data STATUS dan PO</h1>
      <p className="muted">
        Upload sumber STATUS & PO Unit untuk perhitungan PA / BA / Lampiran.
        {count > 0 ? ` STATUS terunggah: ${count} baris.` : ""}
      </p>
      {err && <div className="alert error">{err}</div>}
      {msg && <div className="alert ok">{msg}</div>}

      <div className="grid grid-2">
        <label>Import STATUS (.xlsx / .xlsm)
          <input type="file" accept=".xlsx,.xlsm" onChange={(e) => onImport(e.target.files?.[0] || null)} />
        </label>
        <label>Import PO Unit (untuk BA)
          <input type="file" accept=".xlsx,.xlsm" onChange={(e) => onImportPo(e.target.files?.[0] || null)} />
        </label>
      </div>
    </div>
  );
}
