# Methane Copilot web demo

A self-contained Next.js + TypeScript App Router frontend for the methane detection → billing → repair story. It uses only local CSS, inline SVG geometry, and explicit baked-in sample data. No API keys, Python calls, external maps, fonts, images, CDNs, or network services are required.

## Requirements

- Node.js 18.17 or newer (Node.js 20 LTS recommended)
- npm 9 or newer

## Run locally

From this directory (`web/`):

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

For a production check:

```bash
npm run build
npm run start
```

The demo defaults to the SOURCE tab. Use the SOURCE, BILL, and HEAL tabs to walk through the local sample case. All values are intentionally labeled as sample data.
