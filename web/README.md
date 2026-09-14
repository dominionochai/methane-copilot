# Methane Copilot web console

A self-contained Next.js + TypeScript App Router frontend for the methane detection, billing, and repair story. It uses local CSS, inline SVG geometry, and embedded case data. No API keys, Python calls, external maps, fonts, images, CDNs, or network services are required.

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
npm run build
npm run start
```

The console opens to the SOURCE view. Use SOURCE, BILL, and HEAL to walk through the embedded methane case. All values are explicitly labeled as case data.
