import { NavLink, Outlet } from "react-router-dom";

const links = [
  ["/", "Home"],
  ["/live", "Live"],
  ["/matches", "Matches"],
  ["/competitions", "Competitions"],
  ["/teams", "Teams"],
  ["/players", "Players"],
  ["/search", "Search"],
  ["/endpoints", "40 routes"],
] as const;

export function Layout() {
  return (
    <div className="shell">
      <header className="topbar">
        <div className="brand">
          <strong>Ice Hockey Lab</strong>
          <span>Live ice hockey</span>
        </div>
        <nav className="nav">
          {links.map(([to, label]) => (
            <NavLink key={to} to={to} end={to === "/"} className={({ isActive }) => (isActive ? "active" : "")}>
              {label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main className="page">
        <Outlet />
      </main>
      <footer className="footer">SportsAPI365 ice hockey · no local API</footer>
    </div>
  );
}
