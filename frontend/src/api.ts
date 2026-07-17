const BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, init);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const j = await res.json();
      detail = j.detail || JSON.stringify(j);
    } catch {
      /* ignore */
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) return res.json();
  return res as unknown as T;
}

export type VendorUnits = {
  vendors: string[];
  units_by_vendor: Record<string, string[]>;
};

export type HmRow = {
  id?: number;
  date: string;
  shift: string;
  vendor: string;
  code_unit: string;
  code_unit_lapangan?: string | null;
  hm_start: number;
  hm_stop: number;
  hours_start?: string | null;
  hours_stop?: string | null;
  jam_bd?: number;
  jam_standby?: number;
  ritase?: number;
  fuel?: number;
  hm_pengisian?: number;
  located?: string | null;
  job_description?: string | null;
  operator_name?: string | null;
  keterangan?: string | null;
  exp_difference?: string | null;
  amount_hm?: number | null;
  amount_ew?: number | null;
  hm_difference?: string | null;
  information?: string | null;
  hm_today?: number | null;
  pemotongan_hm?: number | null;
  ewh?: number | null;
  stb?: number | null;
  bd?: number | null;
  cn?: string | null;
  queery?: string | null;
};

export const api = {
  health: () => req<{ ok: boolean }>("/api/health"),
  vendorsUnits: () => req<VendorUnits>("/api/master/vendors-units"),
  seedMaster: () => req("/api/master/seed", { method: "POST" }),
  listHm: (q = "") => req<HmRow[]>(`/api/hm${q}`),
  createHm: (body: HmRow) =>
    req<HmRow>("/api/hm", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  updateHm: (id: number, body: HmRow) =>
    req<HmRow>(`/api/hm/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  deleteHm: (id: number) => req(`/api/hm/${id}`, { method: "DELETE" }),
  suggestStart: (code_unit: string, date: string, shift: string) =>
    req<{ hm_start: number | null; message: string }>(
      `/api/hm/suggest-start?code_unit=${encodeURIComponent(code_unit)}&date=${date}&shift=${encodeURIComponent(shift)}`,
    ),
  recompute: () => req("/api/hm/recompute", { method: "POST" }),
  importHm: async (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return req<{ sheet: string; rows: number; message: string }>("/api/hm/import", {
      method: "POST",
      body: fd,
    });
  },
  importStatus: async (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return req("/api/status/import", { method: "POST", body: fd });
  },
  browseStatus: (q = "") => req<any[]>(`/api/status${q}`),
  statusCount: () => req<{ count: number }>("/api/status/count"),
  importPo: async (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return req("/api/po/import", { method: "POST", body: fd });
  },
  paSummary: (q = "") => req<any>(`/api/pa/summary${q}`),
  baConfig: () => req<any>("/api/ba/config"),
  saveBaConfig: (body: any) =>
    req("/api/ba/config", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  uploadTtd: async (role: string, file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return req<{ ok: boolean; role: string; has_ttd: boolean }>(
      `/api/ba/config/ttd/${encodeURIComponent(role)}`,
      { method: "POST", body: fd },
    );
  },
  deleteTtd: (role: string) =>
    req<{ ok: boolean; role: string; has_ttd: boolean }>(
      `/api/ba/config/ttd/${encodeURIComponent(role)}`,
      { method: "DELETE" },
    ),
  ttdUrl: (role: string, bust = Date.now()) =>
    `/api/ba/config/ttd/${encodeURIComponent(role)}?t=${bust}`,
  baPreview: (vendor?: string) =>
    req<any>(`/api/ba/preview${vendor ? `?vendor=${encodeURIComponent(vendor)}` : ""}`),
  lampiran: (unit?: string) =>
    req<any>(`/api/ba/lampiran${unit ? `?unit=${encodeURIComponent(unit)}` : ""}`),
};

export function downloadUrl(path: string) {
  window.open(path, "_blank");
}