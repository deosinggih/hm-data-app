import { FormEvent, useEffect, useMemo, useState } from "react";
import { api, HmRow, VendorUnits } from "../api";

const EXP_OPTS = ["", "HM Error", "HM Serap Unit", "Ganti Unit", "Salah Input"];

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

export default function InputHmPage() {
  const [master, setMaster] = useState<VendorUnits>({ vendors: [], units_by_vendor: {} });
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [importing, setImporting] = useState(false);
  const [form, setForm] = useState<HmRow>({
    date: todayStr(),
    shift: "Shift 1",
    vendor: "",
    code_unit: "",
    hm_start: 0,
    hm_stop: 0,
    hours_start: "06:00:00",
    hours_stop: "18:00:00",
    jam_bd: 0,
    jam_standby: 0,
    ritase: 0,
    fuel: 0,
    hm_pengisian: 0,
    located: "",
    job_description: "",
    operator_name: "",
    keterangan: "",
    exp_difference: "",
  });

  useEffect(() => {
    api.vendorsUnits().then((m) => {
      setMaster(m);
      if (m.vendors.length && !form.vendor) {
        const v = m.vendors[0];
        const u = m.units_by_vendor[v]?.[0] || "";
        setForm((f) => ({ ...f, vendor: v, code_unit: u }));
      }
    }).catch((e) => setErr(String(e.message || e)));
  }, []);

  const units = useMemo(
    () => master.units_by_vendor[form.vendor] || [],
    [master, form.vendor],
  );

  useEffect(() => {
    if (form.shift.includes("2")) {
      setForm((f) => ({ ...f, hours_start: "18:00:00", hours_stop: "06:00:00" }));
    } else {
      setForm((f) => ({ ...f, hours_start: "06:00:00", hours_stop: "18:00:00" }));
    }
  }, [form.shift]);

  async function suggest() {
    if (!form.code_unit) return;
    try {
      const s = await api.suggestStart(form.code_unit, form.date, form.shift);
      if (s.hm_start != null) {
        setForm((f) => ({ ...f, hm_start: s.hm_start! }));
        setMsg(s.message);
      } else setMsg(s.message);
    } catch (e: any) {
      setErr(e.message);
    }
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setErr(null);
    setMsg(null);
    setSaving(true);
    try {
      const payload = {
        ...form,
        hours_start: form.hours_start?.length === 5 ? `${form.hours_start}:00` : form.hours_start,
        hours_stop: form.hours_stop?.length === 5 ? `${form.hours_stop}:00` : form.hours_stop,
      };
      await api.createHm(payload);
      setMsg("DATA HM tersimpan. Kolom hitung mengikuti rumus Excel BA Monitoring.");
      setForm((f) => ({
        ...f,
        hm_start: f.hm_stop,
        hm_stop: f.hm_stop,
        ritase: 0,
        fuel: 0,
        hm_pengisian: 0,
        keterangan: "",
        exp_difference: "",
      }));
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setSaving(false);
    }
  }

  function set<K extends keyof HmRow>(key: K, value: HmRow[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function onImportExcel(file: File | null) {
    if (!file) return;
    setErr(null);
    setMsg(null);
    setImporting(true);
    try {
      const r = await api.importHm(file);
      setMsg(r.message || `Berhasil impor ${r.rows} baris dari sheet DATA HM`);
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setImporting(false);
    }
  }

  return (
    <div className="card">
      <h1>Input DATA HM</h1>
      {err && <div className="alert error">{err}</div>}
      {msg && <div className="alert ok">{msg}</div>}

      <div className="import-excel-bar">
        <label className="import-excel-label">
          <span>Browse Excel (sheet DATA HM)</span>
          <input
            type="file"
            accept=".xlsx,.xlsm,.xls"
            disabled={importing}
            onChange={(e) => {
              const f = e.target.files?.[0] || null;
              onImportExcel(f);
              e.target.value = "";
            }}
          />
        </label>
        {importing && <span className="muted">Mengimpor…</span>}
      </div>

      <form onSubmit={onSubmit}>
        <div className="grid grid-4">
          <label>DATE
            <input type="date" required value={form.date} onChange={(e) => set("date", e.target.value)} />
          </label>
          <label>SHIFT
            <select value={form.shift} onChange={(e) => set("shift", e.target.value)}>
              <option>Shift 1</option>
              <option>Shift 2</option>
            </select>
          </label>
          <label>VENDOR
            <select
              required
              value={form.vendor}
              onChange={(e) => {
                const v = e.target.value;
                setForm((f) => ({
                  ...f,
                  vendor: v,
                  code_unit: master.units_by_vendor[v]?.[0] || "",
                }));
              }}
            >
              {master.vendors.map((v) => <option key={v} value={v}>{v}</option>)}
            </select>
          </label>
          <label>CODE UNIT
            <select required value={form.code_unit} onChange={(e) => set("code_unit", e.target.value)}>
              {units.map((u) => <option key={u} value={u}>{u}</option>)}
            </select>
          </label>
        </div>

        <div className="grid grid-4" style={{ marginTop: "0.75rem" }}>
          <label>HM START
            <input type="number" step="0.01" value={form.hm_start} onChange={(e) => set("hm_start", Number(e.target.value))} />
          </label>
          <label>HM STOP
            <input type="number" step="0.01" value={form.hm_stop} onChange={(e) => set("hm_stop", Number(e.target.value))} />
          </label>
          <label>HOURS START
            <input type="time" value={(form.hours_start || "").slice(0, 5)} onChange={(e) => set("hours_start", e.target.value)} />
          </label>
          <label>HOURS STOP
            <input type="time" value={(form.hours_stop || "").slice(0, 5)} onChange={(e) => set("hours_stop", e.target.value)} />
          </label>
        </div>

        <div className="grid grid-4" style={{ marginTop: "0.75rem" }}>
          <label>JAM BD
            <input type="number" step="0.01" value={form.jam_bd} onChange={(e) => set("jam_bd", Number(e.target.value))} />
          </label>
          <label>JAM STANDBY
            <input type="number" step="0.01" value={form.jam_standby} onChange={(e) => set("jam_standby", Number(e.target.value))} />
          </label>
          <label>RITASE
            <input type="number" step="1" value={form.ritase} onChange={(e) => set("ritase", Number(e.target.value))} />
          </label>
          <label>Fuel
            <input type="number" step="0.01" value={form.fuel} onChange={(e) => set("fuel", Number(e.target.value))} />
          </label>
        </div>

        <div className="grid grid-3" style={{ marginTop: "0.75rem" }}>
          <label>HM Pengisian
            <input type="number" step="0.01" value={form.hm_pengisian} onChange={(e) => set("hm_pengisian", Number(e.target.value))} />
          </label>
          <label>LOCATED
            <input value={form.located || ""} onChange={(e) => set("located", e.target.value)} />
          </label>
          <label>OPERATORE NAME
            <input value={form.operator_name || ""} onChange={(e) => set("operator_name", e.target.value)} />
          </label>
        </div>

        <div className="grid grid-2" style={{ marginTop: "0.75rem" }}>
          <label>JOB DESCRIPTION
            <input value={form.job_description || ""} onChange={(e) => set("job_description", e.target.value)} />
          </label>
          <label>EXP. DIFFERENCE
            <select value={form.exp_difference || ""} onChange={(e) => set("exp_difference", e.target.value)}>
              {EXP_OPTS.map((o) => <option key={o || "empty"} value={o}>{o || "(kosong)"}</option>)}
            </select>
          </label>
        </div>

        <label style={{ marginTop: "0.75rem" }}>Keterangan
          <textarea value={form.keterangan || ""} onChange={(e) => set("keterangan", e.target.value)} />
        </label>

        <div className="actions">
          <button type="button" className="btn secondary" onClick={suggest}>Suggest HM START</button>
          <button className="btn" disabled={saving}>{saving ? "Menyimpan…" : "Simpan DATA HM"}</button>
        </div>
      </form>
    </div>
  );
}