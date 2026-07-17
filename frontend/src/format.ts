/** Format angka: English — decimal `.`, thousand `,` (1,234.56). */
export function num2(v: unknown): string {
  if (v === null || v === undefined || v === "") return "";
  const n = Number(v);
  if (!Number.isFinite(n)) return String(v);
  return n.toLocaleString("en-US", {
    maximumFractionDigits: 2,
    minimumFractionDigits: 0,
  });
}

/** Format persen (nilai sudah dalam skala 0–100). */
export function pct2(v: unknown): string {
  const s = num2(v);
  return s === "" ? "" : `${s}%`;
}
