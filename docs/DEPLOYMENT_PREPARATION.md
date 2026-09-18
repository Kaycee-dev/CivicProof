# Static deployment preparation — not executed

Recommended path: Cloudflare Pages Direct Upload of the verified `apps/web/out` directory. This accepts the existing static export, requires no backend, and avoids rebuilding facts on a hosting service. [Official Direct Upload documentation](https://developers.cloudflare.com/pages/get-started/direct-upload/) and [Pages CLI reference](https://developers.cloudflare.com/workers/wrangler/commands/pages/).

Operator Gate 7 release approval is complete. After all final pre-publication checks pass, the authorized operator can authenticate Wrangler and execute:

```sh
npx wrangler pages project create civicproof
npx wrangler pages deploy apps/web/out --project-name civicproof
```

Project-name availability and account access are not asserted. No account was connected, resource created, token requested or deployment executed in this preparation. The exact local public-only output and its SHA manifest are authoritative. Do not point hosting at the private research repository or use a cloud build with different inputs.

Static routes are exported with trailing slashes; no server functions, rewrites, API routes or runtime environment variables are needed. Cache revalidation for artifact JSON and ordinary browser security headers can be supplied through the allowlisted `_headers` file. The artifact loader also checks exact build-pinned SHA before rendering. A custom domain is optional and not required for the capstone.

The initial GitHub tree is prepared from the release allowlist only, with no private history or remote. Repository creation, initial public commit/push and deployment are authorized after successful final preflight; they have not yet been executed. README, MIT code license, data notice and canonical description/topics are included in the candidate.
