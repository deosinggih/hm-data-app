import type { ReactNode } from "react";

/** Wrap header label ke maksimal 2 baris (satu break di tengah/spasi), selalu center. */
export function wrapHeader(label: string): ReactNode {
  const text = String(label || "").trim();
  if (!text) return <span className="th-label">{text}</span>;

  const words = text.split(/\s+/);
  if (words.length === 1) {
    // Satu kata panjang: potong di tengah jika perlu
    if (text.length <= 12) {
      return <span className="th-label">{text}</span>;
    }
    const mid = Math.ceil(text.length / 2);
    return (
      <span className="th-label">
        {text.slice(0, mid)}
        <br />
        {text.slice(mid)}
      </span>
    );
  }

  // Pecah di spasi terdekat ke tengah
  const mid = text.length / 2;
  let best = -1;
  let bestDist = Infinity;
  let pos = 0;
  for (let i = 0; i < words.length - 1; i++) {
    pos += words[i].length;
    const dist = Math.abs(pos - mid);
    if (dist < bestDist) {
      bestDist = dist;
      best = pos;
    }
    pos += 1; // spasi
  }
  if (best < 0) return <span className="th-label">{text}</span>;

  return (
    <span className="th-label">
      {text.slice(0, best).trimEnd()}
      <br />
      {text.slice(best).trimStart()}
    </span>
  );
}
