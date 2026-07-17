import { NavLink, Route, Routes } from "react-router-dom";
import InputHmPage from "./pages/InputHmPage";
import TableHmPage from "./pages/TableHmPage";
import SummaryPaPage from "./pages/SummaryPaPage";
import BeritaAcaraPage from "./pages/BeritaAcaraPage";
import LampiranPage from "./pages/LampiranPage";
import StatusPage from "./pages/StatusPage";

const links = [
  { to: "/", label: "Input DATA HM", end: true },
  { to: "/tabel", label: "Tabel DATA HM" },
  { to: "/status", label: "Impor STATUS & PO" },
  { to: "/pa", label: "Summary PA" },
  { to: "/ba", label: "Berita Acara" },
  { to: "/lampiran", label: "Lampiran" },
];

export default function App() {
  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true" />
          <span className="brand-text">BA HM GENERATOR</span>
        </div>
        <nav className="nav" aria-label="Menu utama">
          {links.map((l) => (
            <NavLink key={l.to} to={l.to} end={l.end} className={({ isActive }) => (isActive ? "active" : "")}>
              {l.label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main className="main">
        <Routes>
          <Route path="/" element={<InputHmPage />} />
          <Route path="/tabel" element={<TableHmPage />} />
          <Route path="/status" element={<StatusPage />} />
          <Route path="/pa" element={<SummaryPaPage />} />
          <Route path="/ba" element={<BeritaAcaraPage />} />
          <Route path="/lampiran" element={<LampiranPage />} />
        </Routes>
      </main>
    </div>
  );
}
