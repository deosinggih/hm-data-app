import { useState } from "react";
import { api, downloadUrl } from "../api";
import { num2, pct2 } from "../format";

export default function SummaryPaPage() {
  const [data, setData] = useState<any>(null);
  const [vendor, setVendor] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function run() {
    setLoading(true);
    setErr(null);
    try {
      const q = vendor ? `?vendor=${encodeURIComponent(vendor)}` : "";
      setData(await api.paSummary(q));
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card">
      <h1>Summary PA Unit</h1>
      <p className="muted">Perhitungan PA dari DATA HM + STATUS (logic ba-hm-monitoring).</p>
      {err && <div className="alert error">{err}</div>}

      <div className="grid grid-3">
        <label>Filter Vendor
          <input value={vendor} onChange={(e) => setVendor(e.target.value)} placeholder="PT. PIK" />
        </label>
        <div className="actions" style={{ alignItems: "end" }}>
          <button className="btn" onClick={run} disabled={loading}>
            {loading ? "Menghitung…" : "Hitung Summary PA"}
          </button>
          <button className="btn secondary" onClick={() => downloadUrl(`/api/pa/export${vendor ? `?vendor=${encodeURIComponent(vendor)}` : ""}`)}>
            Export Excel
          </button>
        </div>
      </div>

      {data && (
        <div className="table-wrap" style={{ marginTop: "1rem" }}>
          <table>
            <thead>
              <tr>
                <th>Vendor</th>
                <th>Code Unit</th>
                <th>Total HM Working</th>
                <th>Total Breakdown</th>
                <th>Total Standby</th>
                <th>Total Forcemaejure</th>
                <th>Persentage PA</th>
              </tr>
            </thead>
            <tbody>
              {data.recap.map((r: any, i: number) => (
                <tr key={i}>
                  <td>{r.VENDOR}</td>
                  <td>{r["CODE UNIT"]}</td>
                  <td>{num2(r.WORKING)}</td>
                  <td>{num2(r.BD)}</td>
                  <td>{num2(r.STBY)}</td>
                  <td>{num2(r.FM)}</td>
                  <td>{pct2(r["PA (%)"])}</td>
                </tr>
              ))}
              {!data.recap.length && (
                <tr><td colSpan={7}>Tidak ada data.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
