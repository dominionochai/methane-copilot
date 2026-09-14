# Methane Copilot web console

A self-contained Next.js + TypeScript App Router frontend for the methane detection, billing, repair, and credit story. It uses local CSS, inline SVG geometry, and embedded case data. No API keys, Python calls, external maps, fonts, images, CDNs, or network services are required.

## Requirements

- Node.js 18.17 or newer (Node.js 20 LTS recommended)
- npm 9 or newer

## Run locally

From this directory (`web/`):

```bash
npm install
npm run dev
```

Open http://localhost:3000 in your browser.

For a production check:

```bash
npx tsc --noEmit
npm run build
npm run start
```

The console opens to the SOURCE view. Use SOURCE, BILL, HEAL, and CREDIT to walk through the embedded North separator — flange F-14 case. The CREDIT view is an offline, modeled economics presentation: 12.4 t CH4 becomes 347.2 tCO2e, displayed as 347 whole credits, with estimated revenue of $5,208.00 at $15/tCO2e, a 15% commission, and facility net of $4,426.80.

Credit values are not legal issuance. Registry verification is required through an approved standard such as Verra or Gold Standard before any units can be issued or sold.

All values are explicitly labeled as case data or modeled economics, and all views remain usable offline.
