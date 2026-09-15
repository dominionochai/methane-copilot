# Changelog

## [0.2.11](https://github.com/dominionochai/methane-copilot/compare/v0.2.10...v0.2.11) (2026-09-15)


### Features

* add carbon credit minting workflow ([67d7229](https://github.com/dominionochai/methane-copilot/commit/67d722909fc80de3b4fee77f34e1dad228d2a2bf))
* add copilot integration flow for frontend ([d440e3b](https://github.com/dominionochai/methane-copilot/commit/d440e3b20bcf625bb75ba60b605e04695152618b))
* add methane copilot decision layer ([6d3a0fb](https://github.com/dominionochai/methane-copilot/commit/6d3a0fb4d053f056f09b0c6275b0bba59db864c2))
* background-image selection, blob-aware training, GEE module split, loguru ([3df077c](https://github.com/dominionochai/methane-copilot/commit/3df077c2aeb41f7a80ac29f66bb269598615cc71))
* **background:** add BackgroundImageSelector for S2L MBMP background selection (Phase 1) ([cf07913](https://github.com/dominionochai/methane-copilot/commit/cf0791381c7d370706ce051ed51cd26797b997ea))
* **background:** plot target/background RGB, MBMP and CH4 in tutorial; forward S2 angles ([ec1d529](https://github.com/dominionochai/methane-copilot/commit/ec1d5291292cdc459a28a519cf4b287e6691a004))
* **ci,release:** externalize LUT from marshsi package and add notebook/release automation ([0adbac6](https://github.com/dominionochai/methane-copilot/commit/0adbac6be82590a378c9235e42027cf0eba16a68))
* **config:** auto-load .env from cwd; add make test-integration target ([d1cb82f](https://github.com/dominionochai/methane-copilot/commit/d1cb82f473919c478ce978c939fb68acaec1016e))
* **config:** govern all credentials via environment variables ([060187c](https://github.com/dominionochai/methane-copilot/commit/060187c5fdad87155915e13e35ebb9d69cf0a303))
* **config:** govern all credentials via environment variables ([b2e9e3c](https://github.com/dominionochai/methane-copilot/commit/b2e9e3cd642010502870f3c4319179b0e33202c4))
* **train:** blob output support in train_final and trainer (F3 T3.1/T3.2) ([eb046a6](https://github.com/dominionochai/methane-copilot/commit/eb046a689d28024e2958ea8a08dfe7a009440af2))
* **train:** load finetuning weights/config from blob when path is az:// ([0012bc5](https://github.com/dominionochai/methane-copilot/commit/0012bc55ab47249a0de2bc82a39c4cae9d0af216))
* **web:** add methane copilot demo app ([d095d96](https://github.com/dominionochai/methane-copilot/commit/d095d965b763c114e64585dbde0b519bfeecde95))
* **web:** finish methane operations console design ([730d242](https://github.com/dominionochai/methane-copilot/commit/730d242a0ad0920512b379f5d03e6e771111a595))
* **web:** polish demo interface and add local runbook ([1981b1c](https://github.com/dominionochai/methane-copilot/commit/1981b1cb9ae085409f149d5b5f03aafbf2756e01))
* **web:** ship premium methane operations console ([e382de8](https://github.com/dominionochai/methane-copilot/commit/e382de836aec8fe958759357a25d29e892bc389d))


### Bug Fixes

* anchor internal-blocklist exclude so the tracked template stays scanned ([216eb40](https://github.com/dominionochai/methane-copilot/commit/216eb40fa9a928b03a9ecf8ae87fa9bca73c3653))
* **background:** build new GeoTensor in validmask (no in-place dtype change) ([da18333](https://github.com/dominionochai/methane-copilot/commit/da18333cda10f1b9103b4ff2529f669c9338e086))
* **config:** address PR review on GEE creds and external-facing docs ([5649d00](https://github.com/dominionochai/methane-copilot/commit/5649d0047357f57c73ede99ce3e1b2cb14080129))
* fix bug in stats cloudSEN12 and added map of noise per region. ([82fabf1](https://github.com/dominionochai/methane-copilot/commit/82fabf1e8d9063e96a39c26cbfbca6fd84967c13))
* fix bug in stats cloudSEN12 and added map of noise per region. Use logscale for flux rates and concentrations ([7338228](https://github.com/dominionochai/methane-copilot/commit/7338228abaccd1b3a1144ce0864c98864efb6a11))
* rebuild GeoTensor instead of assigning .values (georeader 2.0 compat) ([adbada5](https://github.com/dominionochai/methane-copilot/commit/adbada5a74b178ec1bc799408993f5eee331247b))
* remove internal references and add leak-prevention guardrails ([5800024](https://github.com/dominionochai/methane-copilot/commit/5800024014a8b59f02b1eac8f652d7bbd4d8382e))
* remove internal references and add leak-prevention guardrails ([8ef9c4d](https://github.com/dominionochai/methane-copilot/commit/8ef9c4d608467f7dea77a7dc1652ad8a5d1acd59))
* **review:** address PR [#11](https://github.com/dominionochai/methane-copilot/issues/11) review comments ([e5858cb](https://github.com/dominionochai/methane-copilot/commit/e5858cbbb61e2a05ade07d79c3fe783b19099426))
* **tests:** don't require an HF token; MARS-S2L dataset is public ([f6ed36e](https://github.com/dominionochai/methane-copilot/commit/f6ed36e7e222186f06bf13a09b3187f6686be9c9))
* use valid semver version string 0.2.0 ([e9275e9](https://github.com/dominionochai/methane-copilot/commit/e9275e97b922014403f0e6ef2ec80a3e44d9a8a7))
* **web:** align methane case values and add brand favicon ([ac13978](https://github.com/dominionochai/methane-copilot/commit/ac139786fedf37434ce87684976a7ba9d1546ea4))


### Documentation

* fix bug docs with pinned packages. Add link to docs in readme ([1be6b44](https://github.com/dominionochai/methane-copilot/commit/1be6b44ee7cbd035be51e61c0673c16fccbbab0a))
* fix docs notebooks to be consistent ([9064b85](https://github.com/dominionochai/methane-copilot/commit/9064b8537c466f1ff45f837e04a2e212379e9863))
* fix docs notebooks to be consistent ([5fc1564](https://github.com/dominionochai/methane-copilot/commit/5fc1564e9634e6f0072b33b1b26401e3635d0956))
* updated notebook and added requirements to pyproject ([68a1956](https://github.com/dominionochai/methane-copilot/commit/68a19565a62a7fe8a69656b22f7b39f3d0e3de20))
* updated notebooks ([674b0ed](https://github.com/dominionochai/methane-copilot/commit/674b0ed14d08373a01c5ec24160ddfc86685d913))

## [0.2.10](https://github.com/UNEP-IMEO-MARS/marss2l/compare/v0.2.9...v0.2.10) (2026-07-13)


### Bug Fixes

* remove internal references and add leak-prevention guardrails ([5800024](https://github.com/UNEP-IMEO-MARS/marss2l/commit/5800024014a8b59f02b1eac8f652d7bbd4d8382e))

## [0.2.9](https://github.com/UNEP-IMEO-MARS/marss2l/compare/v0.2.8...v0.2.9) (2026-07-13)


### Bug Fixes

* fix bug in stats cloudSEN12 and added map of noise per region. ([82fabf1](https://github.com/UNEP-IMEO-MARS/marss2l/commit/82fabf1e8d9063e96a39c26cbfbca6fd84967c13))
* fix bug in stats cloudSEN12 and added map of noise per region. Use logscale for flux rates and concentrations ([7338228](https://github.com/UNEP-IMEO-MARS/marss2l/commit/7338228abaccd1b3a1144ce0864c98864efb6a11))

## [0.2.8](https://github.com/UNEP-IMEO-MARS/marss2l/compare/v0.2.7...v0.2.8) (2026-06-30)


### Documentation

* fix docs notebooks to be consistent ([9064b85](https://github.com/UNEP-IMEO-MARS/marss2l/commit/9064b8537c466f1ff45f837e04a2e212379e9863))
* fix docs notebooks to be consistent ([5fc1564](https://github.com/UNEP-IMEO-MARS/marss2l/commit/5fc1564e9634e6f0072b33b1b26401e3635d0956))

## [0.2.7](https://github.com/UNEP-IMEO-MARS/marss2l/compare/v0.2.6...v0.2.7) (2026-06-18)


### Features

* background-image selection, blob-aware training, GEE module split, loguru ([3df077c](https://github.com/UNEP-IMEO-MARS/marss2l/commit/3df077c2aeb41f7a80ac29f66bb269598615cc71))

## [0.2.6](https://github.com/UNEP-IMEO-MARS/marss2l/compare/v0.2.5...v0.2.6) (2026-06-15)


### Features

* **config:** auto-load .env from cwd; add make test-integration target ([d1cb82f](https://github.com/UNEP-IMEO-MARS/marss2l/commit/d1cb82f473919c478ce978c939fb68acaec1016e))
* **config:** govern all credentials via environment variables ([060187c](https://github.com/UNEP-IMEO-MARS/marss2l/commit/060187c5fdad87155915e13e35ebb9d69cf0a303))
* **config:** govern all credentials via environment variables ([b2e9e3c](https://github.com/UNEP-IMEO-MARS/marss2l/commit/b2e9e3cd642010502870f3c4319179b0e33202c4))


### Bug Fixes

* **config:** address PR review on GEE creds and external-facing docs ([5649d00](https://github.com/UNEP-IMEO-MARS/marss2l/commit/5649d0047357f57c73ede99ce3e1b2cb14080129))
* **tests:** don't require an HF token; MARS-S2L dataset is public ([f6ed36e](https://github.com/UNEP-IMEO-MARS/marss2l/commit/f6ed36e7e222186f06bf13a09b3187f6686be9c9))

## [0.2.5](https://github.com/UNEP-IMEO-MARS/marss2l/compare/v0.2.4...v0.2.5) (2026-06-09)


### Bug Fixes

* rebuild GeoTensor instead of assigning .values (georeader 2.0 compat) ([adbada5](https://github.com/UNEP-IMEO-MARS/marss2l/commit/adbada5a74b178ec1bc799408993f5eee331247b))

## [0.2.4](https://github.com/UNEP-IMEO-MARS/marss2l/compare/v0.2.3...v0.2.4) (2026-04-27)


### Documentation

* updated notebook and added requirements to pyproject ([68a1956](https://github.com/UNEP-IMEO-MARS/marss2l/commit/68a19565a62a7fe8a69656b22f7b39f3d0e3de20))

## [0.2.3](https://github.com/UNEP-IMEO-MARS/marss2l/compare/v0.2.2...v0.2.3) (2026-04-27)


### Documentation

* fix bug docs with pinned packages. Add link to docs in readme ([1be6b44](https://github.com/UNEP-IMEO-MARS/marss2l/commit/1be6b44ee7cbd035be51e61c0673c16fccbbab0a))

## [0.2.2](https://github.com/UNEP-IMEO-MARS/marss2l/compare/v0.2.1...v0.2.2) (2026-04-27)


### Documentation

* updated docs notebooks ([674b0ed](https://github.com/UNEP-IMEO-MARS/marss2l/commit/674b0ed14d08373a01c5ec24160ddfc86685d913))

## [0.2.1](https://github.com/UNEP-IMEO-MARS/marss2l/compare/v0.2.0...v0.2.1) (2026-04-23)


### Features

* **ci,release:** externalize LUT from marshsi package and add notebook/release automation ([0adbac6](https://github.com/UNEP-IMEO-MARS/marss2l/commit/0adbac6be82590a378c9235e42027cf0eba16a68))


### Bug Fixes

* use valid semver version string 0.2.0 ([e9275e9](https://github.com/UNEP-IMEO-MARS/marss2l/commit/e9275e97b922014403f0e6ef2ec80a3e44d9a8a7))

## Changelog

All notable changes to this project will be documented in this file.
