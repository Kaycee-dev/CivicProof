# Verified static deployment

Live demo: https://civicproof.pages.dev

Public repository: https://github.com/Kaycee-dev/CivicProof

Deployment URL: https://859db965.civicproof.pages.dev

Production deployment identifier: `859db965-8762-4692-8c84-be4623284705`.

Source commit: `62b9dbb81b66d668908a15d034906a474640d870` (the initial clean public release). Subsequent live-URL documentation changes do not change the deployed application or its artifacts.

Cloudflare Pages Direct Upload serves the locally verified static export. No cloud build, server functions, backend, runtime model or runtime data generation was enabled. The initial repository contains only the approved allowlist and no private development history. All five live verification downloads match the final local artifact bytes. Browser smoke tests cover search, five dossiers, dimensions, provenance, all fixed answers, candidate/excluded boundaries, narrow viewport and source-link failure behavior. All 64 served static-file bodies match the verified local export; the remaining `_headers` file is host configuration and its response behavior was checked.

For a later explicitly authorized deployment, first repeat the documented local build and release checks, then use the existing Pages project:

```sh
npx wrangler pages deploy apps/web/out --project-name civicproof --branch main --commit-hash <verified-public-commit>
```

The existing project is `civicproof`, production branch `main`. Wrangler 4.135.0 initially attempted Workers delegation during project creation; that failed without a deployment. The `pages project create civicproof --production-branch main --force` option created the required Pages project directly. Normal Pages deploy was used thereafter. Do not create a cloud build from the private workspace.

Static routes have trailing slashes. The allowlisted `_headers` file supplies artifact cache revalidation, `nosniff` and referrer policy. The browser independently verifies build-pinned artifact SHA-256 before rendering. A Python-urllib byte-check request received Cloudflare error 1010; normal Chromium access succeeded without credentials or security-setting changes and verified every served file. This is an observed client-specific access limitation, not an artifact mismatch.

Gate 7 release execution is authorized and the live product is verified. Hackathon submission and final submission production remain separately gated. Source-data rights are separate from the CivicProof code license.

Provider references: [Direct Upload](https://developers.cloudflare.com/pages/get-started/direct-upload/) and [Pages CLI](https://developers.cloudflare.com/workers/wrangler/commands/pages/).
