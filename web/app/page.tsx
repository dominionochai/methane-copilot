"use client";

import { useState } from "react";

type TabId = "source" | "bill" | "heal";
const tabs: { id: TabId; label: string; kicker: string; description: string }[] = [
  { id: "source", label: "SOURCE", kicker: "Detect", description: "Turn a plume into a named source." },
  { id: "bill", label: "BILL", kicker: "Account", description: "Make the cost of inaction visible." },
  { id: "heal", label: "HEAL", kicker: "Resolve", description: "Keep watching until the fix is verified." },
];
const money = (n: number) => new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 2 }).format(n);

function Mark() { return <span className="mark" aria-hidden="true"><i /><i /><i /></span>; }

function Source() {
  return <section className="source-layout" aria-labelledby="source-title">
    <div className="card map-card">
      <div className="card-head"><div><p className="eyebrow">Sample observation · 14 Sep 2026</p><h2 id="source-title">Back-trace the plume</h2></div><span className="pill"><span className="pulse" /> SAMPLE LIVE</span></div>
      <div className="map-wrap">
        <svg viewBox="0 0 760 430" className="map" role="img" aria-labelledby="map-title map-desc">
          <title id="map-title">Inline sample methane plume map</title><desc id="map-desc">A teal plume trails downwind from a candidate flange source.</desc>
          <defs><linearGradient id="plume" x1="0" x2="1"><stop stopColor="#63f5bb" stopOpacity=".72" /><stop offset="1" stopColor="#22b8b0" stopOpacity=".04" /></linearGradient><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 10 5 0 10z" fill="#75f6c1" /></marker></defs>
          <rect width="760" height="430" rx="18" fill="#0c2428" />
          <g className="grid"><path d="M45 75h670M45 150h670M45 225h670M45 300h670M45 375h670M130 35v360M250 35v360M370 35v360M490 35v360M610 35v360" /></g>
          <path d="M55 95c95-28 150 18 225-2s155-27 238 9 139 18 190-15M75 344c90-42 160 7 250-14s190-28 368 16M116 40c-14 98 38 154 20 246s29 94 46 112M542 35c-20 82 37 150 8 222s27 113 66 138" fill="none" stroke="#285258" strokeWidth="2" />
          <path d="M166 246c82-37 126-54 187-72 88-26 177-11 298 22-75 36-166 50-252 48-86-3-155 25-233 42z" fill="url(#plume)" />
          <path d="M182 264c85-33 138-64 214-74 86-11 155 1 222 15" fill="none" stroke="#8cffcb" strokeOpacity=".75" strokeWidth="2" strokeDasharray="5 8" />
          <g className="sensors"><circle cx="208" cy="117" r="8" /><circle cx="310" cy="126" r="8" /><circle cx="430" cy="112" r="8" /><circle cx="560" cy="132" r="8" /></g>
          <g className="pin"><circle cx="166" cy="264" r="18" /><circle cx="166" cy="264" r="7" /><path d="M166 279v22" /></g>
          <path d="M211 264c60-13 113-36 174-62" fill="none" stroke="#ffbe66" strokeWidth="2" strokeDasharray="4 6" markerEnd="url(#arrow)" />
          <path d="M592 85h58" stroke="#75f6c1" strokeWidth="3" markerEnd="url(#arrow)" /><text x="581" y="66" className="svg-label">WIND · 3.8 m/s</text>
          <text x="120" y="330" className="svg-label bright">CANDIDATE SOURCE</text><text x="120" y="348" className="svg-label">north separator / flange F-14</text><text x="50" y="57" className="svg-label">SAMPLE TILE · 9.78°E / 28.09°N</text><text x="580" y="380" className="svg-label">200 m</text><path d="M580 367h100M580 363v8M680 363v8" stroke="#a6c4c3" strokeWidth="2" />
        </svg>
        <div className="legend"><span><i className="l-plume" /> plume concentration</span><span><i className="l-source" /> back-traced source</span><span><i className="l-sensor" /> sensor track</span></div>
      </div>
    </div>
    <aside className="source-side">
      <div className="card confidence"><div className="card-head small"><p className="eyebrow">Attribution result</p><b className="high">HIGH</b></div><strong>87<span>%</span></strong><p className="muted">Heuristic confidence from plume shape, wind alignment, and facility geometry.</p><div className="confidence-bar"><i /></div><div className="split"><span><b>3.8 m/s</b> wind</span><span><b>NW → SE</b> direction</span></div></div>
      <div className="card coordinates"><p className="eyebrow">Back-traced candidate</p><h3>North separator · flange F-14</h3><div><span>Latitude</span><b>28.088330° N</b></div><div><span>Longitude</span><b>9.783509° E</b></div><div><span>Estimated flux</span><b>9,640 kg CH4/h</b></div><p className="note">↗ Candidate point is back-traced upwind from the brightest plume pixels. This is a sample attribution, not a live alert.</p></div>
    </aside>
  </section>;
}

function Bill() {
  const tons = 12.4, commodity = 1934.4, damage = 19840, co2e = 347.2, carbon = co2e * 75;
  const metrics = [["Methane detected", "12.4", "metric tons CH4", "teal"], ["Lost-gas commodity", money(commodity), "at $3 / MMBtu", "amber"], ["EPA climate damage", money(damage), "2020 USD screening", "coral"], ["Climate footprint", "347.2", "metric tons CO₂e", "violet"], ["Carbon-price value", money(carbon), "$75 / tCO₂e demo", "lime"]];
  return <section aria-labelledby="bill-title"><div className="bill-intro"><div><p className="eyebrow">Sample case · finance lens</p><h2 id="bill-title">Put a price on waiting.</h2><p className="lede">The same 12.4-ton sample loss reads differently to an operator, a regulator, and a climate ledger. Keep every convention visible.</p></div><div className="card visible"><span>Visible impact</span><b>{money(damage + carbon)}</b><small>EPA damage + demo carbon value</small></div></div>
    <div className="metric-grid">{metrics.map(([label, value, unit, color]) => <article className={`metric ${color}`} key={label}><span>{label}</span><b>{value}</b><small>{unit}</small></article>)}</div>
    <div className="bill-lower"><div className="card formula"><div className="card-head small"><div><p className="eyebrow">Transparent math</p><h3>One sample, four views</h3></div><b className="sample">SAMPLE DATA</b></div><div className="formulas"><div><span>Lost gas</span><code>{tons} × 52 MMBtu/t × $3/MMBtu</code><b>{money(commodity)}</b></div><div><span>EPA climate damage</span><code>{tons} × $1,600/t CH4</code><b>{money(damage)}</b></div><div><span>CO₂e</span><code>{tons} × GWP 28</code><b>{co2e.toFixed(1)} t</b></div><div><span>Carbon-price value</span><code>{co2e.toFixed(1)} t × $75/tCO₂e</code><b>{money(carbon)}</b></div></div></div>
      <div className="card conventions"><p className="eyebrow">Source conventions</p><h3>Numbers you can audit</h3><ul><li><b>52 MMBtu / metric ton CH4</b><span>HHV screening conversion</span></li><li><b>$3 / MMBtu</b><span>Henry Hub fallback price</span></li><li><b>$1,600 / metric ton CH4</b><span>EPA 2023 SC-CH4, 2020 USD</span></li><li><b>GWP100 = 28</b><span>Methane to CO₂e conversion</span></li><li><b>$75 / tCO₂e</b><span>Clearly stated demo carbon price</span></li></ul><p className="note">ⓘ All values here are baked-in sample outputs. The frontend performs no API calls and does not invoke Python.</p></div></div>
  </section>;
}

const lifecycle = [["detected", "Detected", "Plume threshold crossed", "09 Sep 2026 · 08:12 UTC"], ["source_named", "Source named", "North separator · flange F-14", "09 Sep 2026 · 11:36 UTC"], ["billed", "Billed", "12.4 t CH4 loss booked", "10 Sep 2026 · 09:05 UTC"], ["repair_scheduled", "Repair scheduled", "Field crew · work order WO-284", "11 Sep 2026 · 14:20 UTC"], ["resolved", "Resolved", "Post-repair scan below threshold", "14 Sep 2026 · 16:42 UTC"]];
function Heal() {
  const daily = 161.2, fix = 2400, payback = fix / daily;
  return <section aria-labelledby="heal-title"><div className="heal-head"><div><p className="eyebrow">Sample case · operations loop</p><h2 id="heal-title">Close the loop, not just the ticket.</h2><p className="lede">A source only becomes a solved source when the repair is scheduled, completed, and checked by another observation.</p></div><div className="resolved"><b>✓</b><span>RESOLVED<small>Verified 14 Sep 2026</small></span></div></div>
    <div className="card timeline-card"><div className="card-head small"><div><p className="eyebrow">Case MTH-0247</p><h3>North separator · flange F-14</h3></div><b className="sample">SAMPLE TIMELINE</b></div><div className="timeline">{lifecycle.map(([stage, label, detail, time]) => <div className={`event ${stage}`} key={stage}><i>✓</i><div><div><b>{label}</b><time>{time}</time></div><p>{detail}</p></div></div>)}</div></div>
    <div className="heal-grid"><div className="card playbook"><div className="card-head small"><div><p className="eyebrow">Repair playbook</p><h3>Make the field action obvious</h3></div><b className="play-icon">⌁</b></div><div className="repair"><strong>F-14</strong><div><p className="eyebrow">Observed pattern</p><h4>Flange leak</h4><p>Likely gasket compression loss at the north separator outlet.</p></div></div><div className="down">↓</div><div className="repair recommended"><strong>FIX</strong><div><p className="eyebrow">Recommended action</p><h4>Torque and reseal</h4><p>Isolate line, torque fasteners, replace gasket, then rescan.</p></div></div></div><div className="card economics"><p className="eyebrow">Repair economics</p><h3>Fix it before the next shift</h3><div><span>Estimated fix cost</span><b>{money(fix)}</b></div><div><span>Current daily burn</span><b>{money(daily)} <small>/ day</small></b></div><div className="payback"><p><span>Payback on repair</span><b>{payback.toFixed(1)} days</b></p><i><em /></i><small>Sample assumption: $1,934.40 commodity loss spread across a 12-day observation window.</small></div></div></div>
  </section>;
}

export default function Home() {
  const [active, setActive] = useState<TabId>("source");
  const current = tabs.find((tab) => tab.id === active) ?? tabs[0];
  return <main className="shell"><header className="topbar"><a className="brand" href="#top"><Mark />METHANE <b>COPILOT</b></a><span className="top-meta"><i /> LOCAL DEMO <em /> NO API KEYS</span></header><div id="top" className="hero"><div><p className="eyebrow hero-eyebrow">— Operational methane intelligence</p><h1>We don&apos;t just find methane leaks. <em>We watch until they&apos;re fixed.</em></h1><p className="hero-lede">A field-ready story for turning an invisible loss into a named source, a defensible bill, and a verified repair.</p><div className="loop"><b>DETECT</b><i>→</i><span>BILL</span><i>→</i><span>HEAL</span><i>↻</i></div></div><div className="orbit" aria-hidden="true"><div /><div /><strong><Mark />CH₄</strong><small>signal</small><small>action</small><small>proof</small></div></div><nav className="tabs" aria-label="Demo pillars">{tabs.map((tab, index) => <button className={active === tab.id ? "selected" : ""} key={tab.id} onClick={() => setActive(tab.id)}><small>0{index + 1}</small><span><b>{tab.label}</b><em>{tab.description}</em></span><i>↗</i></button>)}</nav><div className="content-heading"><div><p className="eyebrow">{current.kicker} / 0{tabs.findIndex((tab) => tab.id === active) + 1}</p><h2>{current.description}</h2></div><p>All visuals are local geometry<br />and baked-in sample data.</p></div>{active === "source" && <Source />}{active === "bill" && <Bill />}{active === "heal" && <Heal />}<footer><span><Mark /> Methane Copilot</span><span>DETECT → BILL → HEAL</span><span>Local demo · v0.1</span></footer></main>;
}
