# Eclipse RCP 2026-03 mirror

This directory is the **active primary vendored RCP baseline** for the current modernised path.

## Current status
- The active target and shared repository wiring now point at `eclipse-2026-03/` only for the upstream RCP baseline.
- Fresh-scratch validation with the current active wiring is green through:
  - `AGGREGATOR/prebuild`
  - `AGGREGATOR/plugins`
  - `AGGREGATOR/features/opensource`
  - `AGGREGATOR/doc`
  - `AGGREGATOR/products`
- The mirror no longer presents as a metadata-only staging area; it is now part of the live build path.
- The legacy `eclipse/`, `eclipse-fr/`, and `jna/repository/` inputs are no longer part of the active target or shared repository wiring, and the retired `../eclipse/`, `../eclipse-fr/`, and `../jna/` directories have now been removed from the working tree.

## Source repository
- Composite release URL: `https://download.eclipse.org/releases/2026-03/`
- Direct child repository selected for mirroring: `https://download.eclipse.org/releases/2026-03/202603111000/`

## Slice A audit artefacts
- `stage-manifest.json`
  - records the initially staged upstream metadata inputs.
- `slice-a-resolution-audit.json`
  - records which active `features/opensource/*/feature.xml` RCP-family entries resolve from `eclipse-2026-03`.
- `generate_slice_a_resolution_audit.py`
  - regenerates `slice-a-resolution-audit.json`.

## Slice A completion state
From the committed audit in `slice-a-resolution-audit.json`:
- `151` audited entries resolve from `eclipse-2026-03` only.
- `0` audited entries resolve from duplicate fallback sources.
- `0` audited entries still depend on `eclipse/`, `eclipse-fr/`, or `jna/repository`.
- `0` audited entries are unresolved within the active RCP-family scope.

Slice A is now complete for the active RCP baseline:
- the target and shared Tycho repository wiring resolve from `eclipse-2026-03` without historical fallback repos,
- `features/opensource/org.modelio.e4.rcp/feature.xml` and `features/opensource/org.modelio.platform.feature/feature.xml` have been repinned to modern 2026-03-provided payloads,
- the French-only `org.eclipse.jface.nl_fr` and French product documentation feature have been removed from the supported product path,
- the product definition now uses the modern `org.eclipse.equinox.p2.user.ui` feature instead of the obsolete `httpclient45` ECF feature stack,
- the missing upstream `com.jcraft.jsch_0.1.55.v20230916-1400.jar` and matching source bundle were mirrored into `eclipse-2026-03/plugins/` so the vendored baseline is self-contained.

## Slice B retirement state
- The supported feature and product path continues to resolve from `eclipse-2026-03` only.
- The retired sibling directories `../eclipse/`, `../eclipse-fr/`, and `../jna/` have been removed so the clean vendored train is now the only in-tree RCP baseline/fallback path in this folder family.

Boundary that still remains outside this specific audit:
- the separately vendored `org.eclipse.uml2*` line continues to be supplied from `dev-platform/rcp-target/org.eclipse/uml2/`, not from the RCP mirror.

## Regeneration commands
```zsh
python3 -u /Users/david/IdeaProjects/Modelio/dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03/stage_metadata.py
python3 -u /Users/david/IdeaProjects/Modelio/dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03/stage_repin_slice.py
python3 -u /Users/david/IdeaProjects/Modelio/dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03/generate_slice_a_resolution_audit.py
```

