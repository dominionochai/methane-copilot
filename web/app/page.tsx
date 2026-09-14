"use client";

import { useState } from "react";
import styles from "./credit.module.css";

type TabId = "source" | "bill" | "heal" | "credit";
type Tab = { id: TabId; label: string; kicker: string; text: string };

const CASE = {
  name: "North separator — flange F-14",
  latitude: "28.08833° N",
  longitude: "9.78350° E",
  methane: "12.4 t CH4",
  commodity: "$1,934.40",
  climate: "$19,840",
  footprint: "347.2 tCO2e",
  carbon: "$26,040",
};

const tabs: readonly Tab[] = [
  {
    id: "source",
    label: "SOURCE",
    kicker: "Detect",
    text: "Trace the measured plume to a named asset.",
  },
  {
    id: "bill",
    label: "BILL",
    kicker: "Account",
    text: "Translate a measured loss into accountable cost.",
  },
  {
    id: "heal",
    label: "HEAL",
    kicker: "Resolve",
    text: "Close the loop with a verified repair.",
  },
  {
    id: "credit",
    label: "CREDIT",
    kicker: "Monetize",
    text: "Model the pathway from avoided methane to a credit sale.",
  },
];

const pipeline = ["minted", "verified", "listed", "sold"] as const;

function Mark() {
  return (
    <span className="mark" aria-hidden="true">
      <i />
      <i />
      <i />
    </span>
  );
}

function Icon({ kind }: { kind: TabId }) {
  return (
    <span className="tab-icon" aria-hidden="true">
      <svg viewBox="0 0 24 24" fill="none">
        {kind === "source" && (
          <>
            <circle cx="12" cy="12" r="8" />
            <path d="M12 12 18 6M5 7a10 10 0 0 0 0 10M19 7a10 10 0 0 1 0 10" />
          </>
        )}
        {kind === "bill" && (
          <>
            <path d="M6 3.5h12v17l-3-1.8-3 1.8-3-1.8-3 1.8z" />
            <path d="M9 8h6M9 12h6M9 16h3" />
          </>
        )}
        {kind === "heal" && (
          <>
            <path d="m3.8 20.2 2.7-1.2 10.9-10.9-4-4L2.5 15.5l-.7 2.7 2 2z" />
            <path d="m13.1 6.9 4 4M16.5 3.5l4 4" />
          </>
        )}
        {kind === "credit" && (
          <>
            <circle cx="12" cy="12" r="8" />
            <path d="M12 7v10M9 9h4a2 2 0 0 1 0 4H9h4a2 2 0 0 1 0 4H9" />
          </>
        )}
      </svg>
    </span>
  );
}

function CaseDetails() {
  return (
    <div className="panel coords" aria-label="Plume case details">
      <p className="eyebrow">Plume case</p>
      <h3>{CASE.name}</h3>
      <dl>
        <div><dt>Latitude</dt><dd>{CASE.latitude}</dd></div>
        <div><dt>Longitude</dt><dd>{CASE.longitude}</dd></div>
      </dl>
    </div>
  );
}

function Source() {
  return (
    <section className="module" aria-labelledby="source-title">
      <div className="section-head">
        <div>
          <p className="eyebrow">Observation — 14 Sep 2026</p>
          <h2 id="source-title">Back-trace the plume.</h2>
          <p className="lede">A detection becomes useful when its signal resolves to an accountable piece of equipment.</p>
        </div>
        <span className="status"><i className="live-dot" /> LIVE CASE</span>
      </div>
      <div className="source-grid">
        <div className="panel source-card">
          <div className="source-map-label"><span><i className="live-dot" /> S2L SCAN — TILE 09.14.26</span><span>N 28.08833° · LOCAL GEOMETRY</span></div>
          <div className="source-visual" role="img" aria-label="Local methane plume source geometry">
            <span className="source-grid-lines" />
            <span className="source-plume" />
            <span className="source-hotspot" />
            <span className="source-marker">●<small>F-14</small></span>
            <span className="source-wind">WIND 3.8 m/s →</span>
            <span className="source-coordinate">MONITORED SOURCE<br />NORTH SEPARATOR / FLANGE F-14</span>
          </div>
          <div className="legend"><span><i className="legend-methane" /> methane concentration</span><span><i className="legend-source" /> back-traced source</span><span><i className="legend-sensor" /> sensor track</span></div>
        </div>
        <aside className="source-aside">
          <div className="panel confidence">
            <div className="label-row"><span>Attribution result</span><b>HIGH</b></div>
            <strong>87<small>%</small></strong>
            <p>Heuristic confidence from plume shape, wind alignment, and facility geometry.</p>
            <div className="confidence-bar"><i /></div>
            <div className="split"><span><b>3.8 m/s</b> wind</span><span><b>NW 312°</b> direction</span></div>
          </div>
          <CaseDetails />
          <div className="panel detected"><span>Measured methane</span><b>{CASE.methane}</b><small>release per scan</small><div className="spark" aria-hidden="true"><i /><i /><i /><i /><i /></div></div>
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
          <div className="total"><span>FINANCIAL EXPOSURE</span><b>$21,774.40</b><small>commodity + EPA climate damage</small></div>
          <div className="panel ledger">
            <div className="label-row"><span>Impact ledger</span><em>CASE DATA</em></div>
            <div className="impact-group"><div className="group-label"><span>Financial loss — USD</span><span>{CASE.commodity} + $19,840</span></div><div className="impact"><div><span>Lost-gas commodity</span><b>{CASE.commodity}</b></div><i className="commodity" /><small>at $3 / MMBtu</small></div><div className="impact"><div><span>EPA climate damage</span><b>$19,840</b></div><i className="damage" /><small>2020 USD screening value</small></div></div>
            <div className="impact-group footprint"><div className="group-label"><span>Physical footprint — tCO2e</span><span>separate unit</span></div><div className="impact"><div><span>Climate footprint</span><b>{CASE.footprint}</b></div><i /><small>GWP100 = 28 methane conversion</small></div><div className="demo-value"><span>Carbon-price equivalent</span><b>{CASE.carbon}</b><small>at $75 / tCO2e — not added to USD loss bars</small></div></div>
          </div>
        </div>
        <aside className="panel formula"><div className="label-row"><span>Transparent math</span><b>∑</b></div><h3>One scan, four views.</h3><div className="formula-list"><div><span>Lost gas</span><code>12.4 t CH4 × 52 MMBtu/t × $3</code><b>{CASE.commodity}</b></div><div><span>EPA climate damage</span><code>12.4 t CH4 × $1,600 / t CH4</code><b>$19,840</b></div><div><span>CO2e</span><code>12.4 t CH4 × GWP 28</code><b>{CASE.footprint}</b></div><div><span>Carbon-price value</span><code>347.2 tCO2e × $75 / tCO2e</code><b>{CASE.carbon}</b></div></div><div className="conventions"><b>Source conventions</b><span><b>52 MMBtu / metric ton CH4</b> — conversion</span><span><b>$3 / MMBtu</b> — Henry Hub</span><span><b>$1,600 / metric ton CH4</b> — EPA 2023</span><span><b>$75 / tCO2e</b> — carbon price</span></div></aside>
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
        <div className="panel timeline-panel"><div className="label-row"><div><p className="eyebrow">Case MTH-0247</p><h3>{CASE.name}</h3></div><em>CASE TIMELINE</em></div><div className="timeline"><div className="event resolved-event"><i>✓</i><div><b>Resolved</b><time>14 Sep 2026</time><p>Post-repair scan below threshold</p></div></div><div className="event"><i /><div><b>Repair scheduled</b><time>11 Sep 2026 · 14:20 UTC</time><p>Field crew — work order WO-2847</p></div></div><div className="event"><i /><div><b>Billed</b><time>10 Sep 2026 · 09:05 UTC</time><p>{CASE.methane} loss booked</p></div></div><div className="event"><i /><div><b>Source named</b><time>09 Sep 2026 · 11:36 UTC</time><p>{CASE.name}</p></div></div></div></div>
        <aside className="heal-side"><div className="panel playbook"><div className="label-row"><div><p className="eyebrow">Repair playbook</p><h3>Make field action obvious.</h3></div><b className="play-icon">↗</b></div><div className="repair"><div><span>F-14</span><section><p className="eyebrow">Observed pattern</p><h4>Flange leak</h4><p>Likely gasket compression loss at the north separator outlet.</p></section></div><b>↻</b><div className="fix"><span>FIX</span><section><p className="eyebrow">Recommended action</p><h4>Torque and reseal</h4><p>Isolate line, torque fasteners, replace gasket, then rescan.</p></section></div></div></div><div className="panel economics"><p className="eyebrow">Repair economics</p><h3>Fix it before the next shift.</h3><div className="econ-row"><span>Estimated fix cost</span><b>$2,400</b></div><div className="econ-row"><span>Current daily burn</span><b>$161.20 <small>/ day</small></b></div><div className="cost-bars"><div><span>REPAIR</span><i /></div><div><span>BURN — 12 DAYS</span><i /></div></div><div className="payback"><span>Payback on repair</span><b>14.9 days</b><small>based on {CASE.commodity} commodity loss spread across a 12-day observation window</small></div></div></aside>
      </div>
    </section>
  );
}

function Credit() {
  return (
    <section className={styles.creditPanel} aria-labelledby="credit-title">
      <div className={styles.creditHeader}>
        <div>
          <p className={styles.kicker}>Case credit pathway</p>
          <h2 id="credit-title">Turn measured methane into a modeled credit.</h2>
          <p className={styles.lead}>A transparent view of the North separator case, from {CASE.methane} avoided to a modeled sale. No registry transaction is performed here.</p>
        </div>
        <span className={styles.badge}><i /> OFFLINE MODEL</span>
      </div>
      <div className={styles.statGrid}>
        <div className={styles.statCard}><span>Measured methane</span><strong>12.4 t CH4</strong><small>canonical case loss</small></div>
        <div className={styles.statCard}><span>Climate equivalent</span><strong>347.2 tCO2e</strong><small>12.4 t CH4 × GWP 28</small></div>
        <div className={styles.statCard}><span>Credit display</span><strong>347 credits</strong><small>whole-credit display</small></div>
      </div>
      <div className={styles.creditColumns}>
        <div className={styles.creditMain}>
          <div className={styles.card}>
            <div className={styles.cardHeading}><div><p className={styles.kicker}>Registry pathway</p><h3>From signal to settlement.</h3></div><span>CASE MTH-0247</span></div>
            <div className={styles.pipeline} aria-label="Credit pipeline: minted, verified, listed, sold">
              {pipeline.map((step, index) => <div className={styles.pipelineItem} key={step}><div className={styles.pipelineNode}>{index + 1}</div><b>{step}</b>{index < pipeline.length - 1 && <span className={styles.pipelineArrow} aria-hidden="true">→</span>}</div>)}
            </div>
            <p className={styles.note}><b>Registry verification required (Verra/Gold Standard).</b> Modeled economics, not legal issuance.</p>
          </div>
          <div className={styles.card}>
            <div className={styles.cardHeading}><div><p className={styles.kicker}>Modeled settlement</p><h3>Transparent economics.</h3></div><span>$15 / tCO2e</span></div>
            <div className={styles.mathRows}><div><span>Modeled climate basis</span><b>347.2 tCO2e × $15</b><strong>$5,208.00</strong></div><div><span>Commission</span><b>15% of estimated revenue</b><strong>−$781.20</strong></div><div className={styles.netRow}><span>Facility net</span><b>estimated revenue less commission</b><strong>$4,426.80</strong></div></div>
          </div>
        </div>
        <aside className={styles.creditAside}>
          <div className={styles.card}><p className={styles.kicker}>Display convention</p><h3>Keep the case consistent.</h3><p className={styles.body}>347 credits is the whole-credit display of 347.2 tCO2e. The revenue model uses the full 347.2 tCO2e at $15/tCO2e, producing estimated revenue of $5,208.00.</p><div className={styles.caseLine}><span>Case</span><b>{CASE.name}</b></div><div className={styles.caseLine}><span>Basis</span><b>{CASE.methane} → {CASE.footprint}</b></div></div>
          <div className={styles.warning}><span>!</span><p>Credits remain modeled until an approved registry verifies the project and issues units. This screen does not represent legal issuance.</p></div>
        </aside>
      </div>
    </section>
  );
}

export default function Home() {
  const [active, setActive] = useState<TabId>("source");
  const current = tabs.find((tab) => tab.id === active) ?? tabs[0];

  return (
    <main className="shell">
      <header className="topbar"><a className="brand" href="#top"><Mark /><span>METHANE <b>COPILOT</b></span></a><div className="top-right"><span className="system"><i className="live-dot" /> MARSS-2L v1 — live scan</span><span>LOCAL MODE <em /> NO API KEYS</span></div></header>
      <section className="hero" id="top"><div className="hero-copy"><p className="eyebrow">Operational methane intelligence</p><h1>We don&apos;t just find methane leaks. <em>We watch until they&apos;re fixed.</em></h1><p className="hero-lede">A field-ready operating story for turning an invisible loss into a named source, a defensible bill, a verified repair, and a modeled credit pathway.</p><div className="loop"><b>DETECT</b><i>↗</i><span>BILL</span><i>↗</i><span>HEAL</span><i>↗</i><span>CREDIT</span></div></div><div className="orbit" aria-hidden="true"><div /><div /><strong><Mark /> CH4<small>signal</small><small>action</small><small>proof</small></strong></div></section>
      <nav className="tabs" aria-label="Case views" role="tablist">{tabs.map((tab, index) => <button key={tab.id} role="tab" aria-selected={active === tab.id} aria-controls={`${tab.id}-panel`} className={active === tab.id ? "selected" : ""} onClick={() => setActive(tab.id)}><small>{index + 1}</small><Icon kind={tab.id} /><span><b>{tab.label}</b><em>{tab.text}</em></span><i>↘</i></button>)}</nav>
      <div className="content-heading"><div><p className="eyebrow">{current.kicker} — {tabs.findIndex((tab) => tab.id === active) + 1} / {tabs.length}</p><h2>{current.text}</h2></div><p>All visuals are local geometry<br />and embedded case data.</p></div>
      <div id={`${active}-panel`} role="tabpanel" tabIndex={0}>{active === "source" && <Source />}{active === "bill" && <Bill />}{active === "heal" && <Heal />}{active === "credit" && <Credit />}</div>
      <footer><span><Mark /> Methane Copilot</span><span>DETECT ↗ BILL ↗ HEAL ↗ CREDIT</span><span>Local mode ↗ v1.0</span></footer>
    </main>
  );
}
