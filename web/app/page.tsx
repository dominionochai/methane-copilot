"use client";

import { useState } from "react";

type Tab = "source" | "bill" | "heal";

const CASE = {
  name: "North separator • flange F-14",
  latitude: "28.08833° N",
  longitude: "9.78350° E",
  methane: "12.4 t CH₄",
  commodity: "$1,934.40",
  climate: "$19,840",
  footprint: "347.2 t CO₂e",
  carbon: "$26,040",
};

const tabs: Array<{ id: Tab; label: string; kicker: string; text: string }> = [
  { id: "source", label: "SOURCE", kicker: "Detect", text: "Trace the measured plume to a named asset." },
  { id: "bill", label: "BILL", kicker: "Account", text: "Translate a measured loss into accountable cost." },
  { id: "heal", label: "HEAL", kicker: "Resolve", text: "Close the loop with a verified repair." },
];

const timeline = [
  ["detected", "Detected", "Plume threshold crossed", "09 Sep 2026 · 08:12 UTC"],
  ["source_named", "Source named", CASE.name, "09 Sep 2026 · 11:36 UTC"],
  ["billed", "Billed", `${CASE.methane} loss booked`, "10 Sep 2026 · 09:05 UTC"],
  ["repair_scheduled", "Repair scheduled", "Field crew · work order WO-284", "11 Sep 2026 · 14:20 UTC"],
  ["resolved", "Resolved", "Post-repair scan below threshold", "14 Sep 2026 · 16:42 UTC"],
] as const;

function Mark() {
  return (
    <span className="mark" aria-hidden="true">
      <i />
      <i />
      <i />
    </span>
  );
}

function Icon({ kind }: { kind: Tab }) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      {kind === "source" ? (
        <>
          <circle cx="12" cy="12" r="8" />
          <path d="M12 12 18 6M5 7a10 10 0 0 0 0 10M19 7a10 10 0 0 1 0 10" />
        </>
      ) : kind === "bill" ? (
        <>
          <path d="M6 3.5h12v17l-3-1.8-3 1.8-3-1.8-3 1.8z" />
          <path d="M9 8h6M9 12h6M9 16h3" />
        </>
      ) : (
        <>
          <path d="M3.8 20.2 6.5 19l10.9-10.9-4-4L2.5 15.5l-.7 2.7 2 2z" />
          <path d="m13.1 6.9 4 4M16.5 3.5l4 4" />
        </>
      )}
    </svg>
  );
}

function CaseDetails() {
  return (
    <div className="panel coords" aria-label="Plume case details">
      <p className="eyebrow">Plume case</p>
      <h3>{CASE.name}</h3>
      <dl>
        <div>
          <dt>Latitude</dt>
          <dd>{CASE.latitude}</dd>
        </div>
        <div>
          <dt>Longitude</dt>
          <dd>{CASE.longitude}</dd>
        </div>
      </dl>
    </div>
  );
}

function SourceMap() {
  return (
    <div className="map-wrap">
      <div className="map-top">
        <span><i className="live-dot" /> S2L SCAN · TILE 09.14.26</span>
        <span>N ↑ · LOCAL GEOMETRY</span>
      </div>
      <svg className="map" viewBox="0 0 860 440" role="img" aria-labelledby="map-title map-desc">
        <title id="map-title">Methane plume source attribution</title>
        <desc id="map-desc">A teal plume trail leads from the monitored separator to a back-traced source, with wind direction and sensor tracks.</desc>
        <defs>
          <linearGradient id="plume-gradient" x1="0" x2="1">
            <stop stopColor="#55e0c2" stopOpacity=".9" />
            <stop offset="1" stopColor="#1d6c71" stopOpacity=".04" />
          </linearGradient>
          <radialGradient id="hot-gradient">
            <stop stopColor="#ffd078" />
            <stop offset="1" stopColor="#ed9065" stopOpacity="0" />
          </radialGradient>
          <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto">
            <path d="M0 0 10 5 0 10Z" fill="#88f5d7" />
          </marker>
        </defs>
        <rect width="860" height="440" rx="18" fill="#0b1a1c" />
        <g className="grid">
          <path d="M40 80h780M40 160h780M40 240h780M40 320h780M140 32v376M280 32v376M420 32v376M560 32v376M700 32v376" />
        </g>
        <path className="contour" d="M52 110c104-42 166 28 271-4s174-9 262 22 167-28 245-4M55 342c108-48 202 22 292-17s154-28 238 8 159 5 220-14" />
        <path className="road" d="M70 380c135-39 188-99 279-92s157 63 243 40 131-76 225-91" />
        <path className="plume" d="M184 282c70-44 102-102 182-127 77-24 131-4 208-31 87-30 153-65 242-65-50 41-98 86-153 116-71 39-125 28-205 60-82 33-153 99-274 122Z" fill="url(#plume-gradient)" />
        <path className="edge" d="M204 275c70-37 109-89 174-111 82-28 130-3 208-29 65-22 132-57 202-65" />
        <path className="candidate" d="M184 291c79-43 119-77 191-104 84-31 131-26 213-52" markerEnd="url(#arrow)" />
        <circle className="hotspot" cx="184" cy="291" r="44" fill="url(#hot-gradient)" />
        <g className="marker">
          <circle className="pulse" cx="184" cy="291" r="24" />
          <circle cx="184" cy="291" r="9" />
          <path d="M184 301v20" />
        </g>
        <g className="sensors">
          <circle cx="306" cy="202" r="6" />
          <circle cx="420" cy="164" r="6" />
          <circle cx="548" cy="132" r="6" />
          <circle cx="680" cy="88" r="6" />
        </g>
        <line className="wind" x1="685" y1="350" x2="760" y2="350" markerEnd="url(#arrow)" />
        <text className="svg-label bright" x="687" y="329">WIND 3.8 m/s</text>
        <text className="svg-label" x="687" y="373">NW · 312°</text>
        <text className="svg-label bright" x="93" y="350">MONITORED SOURCE</text>
        <text className="svg-label" x="93" y="371">NORTH SEPARATOR / FLANGE F-14</text>
        <text className="svg-label" x="51" y="55">TILE 28.08833° N / 9.78350° E</text>
        <text className="svg-label" x="714" y="405">200 m</text>
        <path className="scale" d="M714 388h96M714 388v8M810 388v8" />
      </svg>
      <div className="legend">
        <span><i className="lp" /> methane concentration</span>
        <span><i className="ls" /> back-traced source</span>
        <span><i className="ln" /> sensor track</span>
      </div>
    </div>
  );
}

function Source() {
  return (
    <section className="module" aria-labelledby="source-title">
      <div className="section-head">
        <div>
          <p className="eyebrow">Observation · 14 Sep 2026</p>
          <h2 id="source-title">Back-trace the plume.</h2>
          <p className="lede">A detection becomes useful when its signal resolves to an accountable piece of equipment.</p>
        </div>
        <span className="status"><i className="live-dot" /> LIVE CASE</span>
      </div>
      <div className="source-grid">
        <div className="panel map-panel"><SourceMap /></div>
        <aside className="source-aside">
          <div className="panel confidence">
            <div className="label-row"><span>Attribution result</span><b>HIGH</b></div>
            <strong>87<small>%</small></strong>
            <p>Heuristic confidence from plume shape, wind alignment, and facility geometry.</p>
            <div className="confidence-bar"><i /></div>
            <div className="split"><span><b>3.8 m/s</b> wind</span><span><b>NW 312°</b> direction</span></div>
          </div>
          <CaseDetails />
          <div className="panel detected">
            <span>Measured methane</span>
            <b>{CASE.methane}</b>
            <small>release per scan</small>
            <div className="spark" aria-hidden="true"><i /><i /><i /><i /><i /></div>
          </div>
        </aside>
      </div>
    </section>
  );
}

function Bill() {
  return (
    <section className="module" aria-labelledby="bill-title">
      <div className="section-head">
        <div>
          <p className="eyebrow">Case financial lens</p>
          <h2 id="bill-title">Put a price on waiting.</h2>
          <p className="lede">The measured {CASE.methane} loss has three accountable lenses: commodity value, climate damage, and a stated carbon price.</p>
        </div>
      </div>
      <div className="bill-grid">
        <div className="bill-main">
          <CaseDetails />
          <div className="total">
            <span>FINANCIAL EXPOSURE</span>
            <b>$21,774.40</b>
            <small>commodity + EPA climate damage</small>
          </div>
          <div className="panel ledger">
            <div className="label-row"><span>Impact ledger</span><em>CASE DATA</em></div>
            <div className="impact-group">
              <div className="group-label"><span>Financial loss · USD</span><span>{CASE.commodity} + {CASE.climate}</span></div>
              <div className="impact"><div><span>Lost-gas commodity</span><b>{CASE.commodity}</b></div><i className="commodity" /><small>at $3 / MMBtu</small></div>
              <div className="impact"><div><span>EPA climate damage</span><b>{CASE.climate}</b></div><i className="damage" /><small>2020 USD screening value</small></div>
            </div>
            <div className="impact-group footprint">
              <div className="group-label"><span>Physical footprint · tCO₂e</span><span>separate unit</span></div>
              <div className="impact"><div><span>Climate footprint</span><b>{CASE.footprint}</b></div><i /><small>GWP100 = 28 methane conversion</small></div>
              <div className="demo-value"><span>Carbon-price equivalent</span><b>{CASE.carbon}</b><small>at $75 / tCO₂e · not added to USD loss bars</small></div>
            </div>
          </div>
        </div>
        <aside className="bill-side">
          <div className="panel formula">
            <div className="label-row"><span>Transparent math</span><b>Σ</b></div>
            <h3>One scan, four views.</h3>
            <div className="formula-list">
              <div><span>Lost gas</span><code>12.4 t × 52 MMBtu/t × $3</code><b>{CASE.commodity}</b></div>
              <div><span>EPA climate damage</span><code>12.4 t × $1,600 / t CH₄</code><b>{CASE.climate}</b></div>
              <div><span>CO₂e</span><code>12.4 t × GWP 28</code><b>{CASE.footprint}</b></div>
              <div><span>Carbon-price value</span><code>347.2 t CO₂e × $75 / tCO₂e</code><b>{CASE.carbon}</b></div>
            </div>
          </div>
          <div className="conventions"><b>Source conventions</b><span><b>52 MMBtu / metric ton CH₄</b> · conversion</span><span><b>$3 / MMBtu</b> · Henry Hub</span><span><b>$1,600 / metric ton CH₄</b> · EPA 2023</span><span><b>$75 / tCO₂e</b> · carbon price</span></div>
        </aside>
      </div>
    </section>
  );
}

function Heal() {
  return (
    <section className="module" aria-labelledby="heal-title">
      <div className="section-head">
        <div>
          <p className="eyebrow">Case operations loop</p>
          <h2 id="heal-title">Close the loop, not just the ticket.</h2>
          <p className="lede">A source only becomes resolved when the repair is scheduled, completed, and checked by another observation.</p>
        </div>
        <div className="resolved"><b>✓</b><span>RESOLVED<small>verified 14 Sep 2026</small></span></div>
      </div>
      <div className="heal-grid">
        <div className="panel timeline-panel">
          <div className="label-row"><div><p className="eyebrow">Case MTH-0247</p><h3>{CASE.name}</h3></div><em>CASE TIMELINE</em></div>
          <div className="timeline">{timeline.map(([stage, label, detail, time]) => <div className={`event ${stage}`} key={stage}><i>{stage === "resolved" ? "✓" : ""}</i><div><b>{label}</b><time>{time}</time><p>{detail}</p></div></div>)}</div>
        </div>
        <aside className="heal-side">
          <div className="panel playbook">
            <div className="label-row"><div><p className="eyebrow">Repair playbook</p><h3>Make field action obvious.</h3></div><b className="play-icon">↗</b></div>
            <div className="repair"><div><span>F-14</span><section><p className="eyebrow">Observed pattern</p><h4>Flange leak</h4><p>Likely gasket compression loss at the north separator outlet.</p></section></div><b>→</b><div className="fix"><span>FIX</span><section><p className="eyebrow">Recommended action</p><h4>Torque and reseal</h4><p>Isolate line, torque fasteners, replace gasket, then rescan.</p></section></div></div>
          </div>
          <div className="panel economics"><p className="eyebrow">Repair economics</p><h3>Fix it before the next shift.</h3><div className="econ-row"><span>Estimated fix cost</span><b>$2,400</b></div><div className="econ-row"><span>Current daily burn</span><b>$161.20 <small>/ day</small></b></div><div className="cost-bars"><div><span>REPAIR</span><i style={{ width: "18%" }} /></div><div><span>BURN · 12 DAYS</span><i /></div></div><div className="payback"><span>Payback on repair</span><b>14.9 days</b><small>based on {CASE.commodity} commodity loss spread across a 12-day observation window</small></div></div>
        </aside>
      </div>
    </section>
  );
}

export default function Home() {
  const [active, setActive] = useState<Tab>("source");
  const current = tabs.find((tab) => tab.id === active) ?? tabs[0];

  return (
    <main className="shell">
      <header className="topbar">
        <a className="brand" href="#top"><Mark /><span>METHANE <b>COPILOT</b></span></a>
        <div className="top-right"><span className="system"><i className="live-dot" /> MARS-S2L v1 · live scan</span><span>LOCAL MODE <em /> NO API KEYS</span></div>
      </header>
      <section className="hero" id="top">
        <div className="hero-copy">
          <p className="eyebrow">Operational methane intelligence</p>
          <h1>We don&apos;t just find methane leaks. <em>We watch until they&apos;re fixed.</em></h1>
          <p className="hero-lede">A field-ready operating story for turning an invisible loss into a named source, a defensible bill, and a verified repair.</p>
          <div className="loop"><b>DETECT</b><i>→</i><span>BILL</span><i>→</i><span>HEAL</span><i>→</i></div>
        </div>
        <div className="orbit" aria-hidden="true"><div /><div /><strong><Mark /> CH₄<small>signal</small><small>action</small><small>proof</small></strong></div>
      </section>
      <nav className="tabs" aria-label="Case views" role="tablist">
        {tabs.map((tab, index) => <button key={tab.id} role="tab" aria-selected={active === tab.id} aria-controls={`${tab.id}-panel`} className={active === tab.id ? "selected" : ""} onClick={() => setActive(tab.id)}><small>0{index + 1}</small><span className="tab-icon"><Icon kind={tab.id} /></span><span><b>{tab.label}</b><em>{tab.text}</em></span><i>›</i></button>)}
      </nav>
      <div className="content-heading"><div><p className="eyebrow">{current.kicker} · 0{tabs.findIndex((tab) => tab.id === active) + 1}</p><h2>{current.text}</h2></div><p>All visuals are local geometry<br />and embedded case data.</p></div>
      <div id="source-panel" role="tabpanel" hidden={active !== "source"}>{active === "source" && <Source />}</div>
      <div id="bill-panel" role="tabpanel" hidden={active !== "bill"}>{active === "bill" && <Bill />}</div>
      <div id="heal-panel" role="tabpanel" hidden={active !== "heal"}>{active === "heal" && <Heal />}</div>
      <footer><span><Mark /> Methane Copilot</span><span>DETECT · BILL · HEAL</span><span>Local mode · v1.0</span></footer>
    </main>
  );
}
