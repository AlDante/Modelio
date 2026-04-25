# AGENTS.md

## Scope and intent
- This repo is an Eclipse RCP/Tycho monorepo for Modelio 5.4.1 (`Java 21` build toolchain, macOS `aarch64` product metadata on `Java 21`, Tycho `5.0.2`) centered on OSGi plugins, features, and packaged products.
- Build orchestration is Maven-first; most deployable artifacts are `eclipse-plugin`, `eclipse-feature`, or `eclipse-repository` modules.
- Default operating mode is correctness-first: preserve module wiring, verify each impacted layer, and prefer fail-fast scoped builds before broad packaging.

## Big-picture layout (follow this dependency flow)
- Core plugin sources live under `modelio/` (domains split as `core/`, `platform/`, `app/`, `uml/`, `bpmn/`, `plugdule/`).
- Aggregators under `AGGREGATOR/` define build order and stitch modules from `modelio/`, `features/`, and `products/`.
- Feature composition is in `features/opensource/*` (for example `features/opensource/org.modelio.application.ui/feature.xml`).
- Final product definition is `products/modelio-os.product`; packaging profiles are in `products/pom.xml`.
- Target platform is local-file based from `dev-platform/rcp-target/rcp.target`; the supported macOS `aarch64` path now resolves its upstream RCP content from `dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03/` without active `eclipse/`, `eclipse-fr/`, `jna/repository/`, or `openjdk-jre11` fallback wiring.

## Canonical build entrypoints
- Full staged build (prebuild + plugins + features + products): run from `AGGREGATOR/pom.xml`.
- Prebuild validates the shared parent + target-definition modules first (`AGGREGATOR/prebuild/pom.xml` builds root + `dev-platform/rcp-target` against the cleaned 2026-03 baseline wiring).
- Run Maven on `Java 21` for the current Tycho baseline; the supported macOS `aarch64` product path now validates with Java 21 launcher metadata and no active `openjdk-jre11` target wiring.
- Product packaging variants are profile-driven in `products/pom.xml`:
  - `product.org` for the OpenSource product archive.
  - `repositoryP2` for p2 repository output.
  - `platform.mac.aarch64` for the supported native Apple Silicon product path.
- Root `pom.xml` holds shared Tycho config and local p2 repository wiring; avoid duplicating repository declarations in child modules.

## Project-specific patterns to preserve
- Aggregator poms reference modules with relative paths into `modelio/*` (example: `AGGREGATOR/plugins/core/pom.xml`); keep new modules wired in both source tree and matching aggregator.
- Plugin module poms are minimal and usually only declare `artifactId` + `packaging` (example: `modelio/platform/platform.ui/pom.xml`).
- OSGi dependencies are primarily declared in `META-INF/MANIFEST.MF` (`Require-Bundle`, `Export-Package`), not in Maven dependencies.
- UI and contribution wiring uses `plugin.xml` + e4 fragments (example: `modelio/app/app.project.ui/plugin.xml` -> `e4model/projectui.e4xmi`).
- `*.ext_org` plugins/features are paired variants used by the open-source distribution; check sibling modules before adding new extension points.

## Integration points and external deps
- External libs are vendored as local p2 directories under `dev-platform/rcp-target/**` and consumed via `file://` URLs in root `pom.xml`.
- Product runtime config (VM args, launcher icons, OSGi areas, startup bundles) is centralized in `products/modelio-os.product`.
- `dev-platform/rcp-target/rcp.target` contains an ordering-sensitive note for test resources (`test-resources/files` first).

## Correctness-first change checklist
- For plugin code changes, update all relevant descriptors together: sources/resources, `META-INF/MANIFEST.MF`, and `plugin.xml` when extension points or e4 fragments are involved.
- If bundle visibility changes, verify `Require-Bundle` and `Export-Package` in the touched plugin manifests (example baseline: `modelio/platform/platform.ui/META-INF/MANIFEST.MF`).
- If a plugin is added/renamed, wire it in the owning aggregator (`AGGREGATOR/plugins/*/pom.xml`) and in the consuming feature (`features/opensource/*/feature.xml`).
- Confirm product-level inclusion when feature composition changes by checking `products/modelio-os.product` feature list.
- Treat `*.ext_org` as distribution-coupled variants; compare with sibling non-`ext_org` modules before changing IDs, extension points, or feature membership.

## Verification workflow (smallest scope first)
- Validate target definition first when dependencies change: run Maven from `AGGREGATOR/prebuild/pom.xml`.
- Build only the affected plugin family via `AGGREGATOR/plugins/{core|platform|app|uml|bpmn|plugdules}/pom.xml`.
- Rebuild impacted features via `AGGREGATOR/features/opensource/pom.xml` when plugin membership or feature.xml changes.
- Run product packaging only after plugin+feature success, using `AGGREGATOR/products/pom.xml` or `products/pom.xml` with `product.org` and `platform.mac.aarch64` for the supported product path, or `repositoryP2` when you only need p2 repository output.
- There are no obvious `eclipse-test-plugin` modules in current poms; rely on targeted Tycho compile/package validation across touched aggregators.

## Existing AI-instruction sources found
- A glob search for common AI rule files found no repo-level agent instruction files; only third-party/vendor READMEs under CKEditor/Freemarker paths.

## Prefer MacPorts to Homebrew
- If utilities need to be installed, use MacPorts. Use Homebrew only if a required utility is unavailable via MacPorts.

## Mac M1 aarch64 only build
- The only platform that we need to support is Mac M1 aarch64, so we can target that architecture specifically in our build configuration. We do not need to worry about cross-compilation or multi-arch builds.
- For the canonical native Apple Silicon build flow, overlay generation steps, intermediate output directories, and final app/archive locations, consult `MACOS_AARCH64_BUILD_PROCESS.md`.
