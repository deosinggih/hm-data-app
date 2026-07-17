import { useEffect, useState } from "react";
import { api, downloadUrl, HmRow } from "../api";
import { num2 } from "../format";

export default function TableHmPage() {
  const [rows, setRows] = useState<HmRow[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [vendor, setVendor] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  async function load() {
    try {
      const qs = new URLSearchParams();
      if (vendor) qs.set("vendor", vendor);
      if (dateFrom) qs.set("date_from", dateFrom);
      if (dateTo) qs.set("date_to", dateTo);
      const q = qs.toString() ? `?${qs}` : "";
      setRows(await api.listHm(q));
      setErr(null);
    } catch (e: any) {
      setErr(e.message);
    }
  }

  useEffect(() => { load(); }, []);

  async function remove(id?: number) {
    if (!id || !confirm("Hapus baris ini?")) return;
    await api.deleteHm(id);
    load();
  }

  return (
    <div className="card">
      <h1>Tabel DATA HM</h1>
      <p className="muted">Database hasil inputan. Export Excel format form HM.xlsx (Master Unit + DATA HM).</p>
      {err && <div className="alert error">{err}</div>}

      <div className="grid grid-4">
        <label>Vendor filter
          <input value={vendor} onChange={(e) => setVendor(e.target.value)} placeholder="PT. PIK" />
        </label>
        <label>Dari
          <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
        </label>
        <label>Sampai
          <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
        </label>
        <div className="actions" style={{ alignItems: "end" }}>
          <button className="btn secondary" onClick={load}>Filter</button>
          <button className="btn" onClick={() => downloadUrl("/api/export/data-hm")}>Export Excel</button>
          <button className="btn secondary" onClick={() => api.recompute().then(load)}>Recompute</button>
        </div>
      </div>

      <div className="table-wrap" style={{ marginTop: "1rem" }}>
        <table>
          <thead>
            <tr>
              <th>VENDOR</th><th>CODE UNIT</th>
              <th>HM START</th><th>HM STOP</th><th>AMOUNT HM</th><th>AMOUNT EW</th>
              <th>HM DIFF</th><th>EXP</th><th>INFO</th><th>EWH</th><th>STB</th><th>BD</th><th></th>
            </tr>
          </thead>
          <tbody>
            {(() => {
              if (!rows.length) {
                return <tr><td colSpan={13}>Belum ada data. Isi lewat menu Input DATA HM.</td></tr>;
              }
              let lastDate = "";
              let lastShift = "";
              const elements = [];
              rows.forEach((r, idx) => {
                if (r.date !== lastDate) {
                  elements.push(
                    <tr key={`date-${r.date}`} style={{ backgroundColor: "var(--bg-2)", fontWeight: "600" }}>
                      <td colSpan={13} style={{ padding: "0.5rem" }}>📅 {r.date}</td>
                    </tr>
                  );
                  lastDate = r.date;
                  lastShift = "";
                }
                if (r.shift !== lastShift) {
                  elements.push(
                    <tr key={`shift-${r.date}-${r.shift}`} style={{ backgroundColor: "var(--bg)", fontWeight: "500", fontSize: "0.9em" }}>
                      <td colSpan={13} style={{ padding: "0.3rem 0.5rem", paddingLeft: "2rem" }}>→ {r.shift}</td>
                    </tr>
                  );
                  lastShift = r.shift;
                }
                elements.push(
                  <tr key={r.id}>
                    <td>{r.vendor}</td>
                    <td>{r.code_unit}</td>
                    <td>{num2(r.hm_start)}</td>
                    <td>{num2(r.hm_stop)}</td>
                    <td>{num2(r.amount_hm)}</td>
                    <td>{num2(r.amount_ew)}</td>
                    <td>{num2(r.hm_difference)}</td>
                    <td>{r.exp_difference ?? ""}</td>
                    <td>{r.information ?? ""}</td>
                    <td>{num2(r.ewh)}</td>
                    <td>{num2(r.stb)}</td>
                    <td>{num2(r.bd)}</td>
                    <td><button className="btn danger" onClick={() => remove(r.id)}>Hapus</button></td>
                  </tr>
                );
              });
              return elements;
            })()}
          </tbody>
        </table>
      </div>
    </div>
  );
}