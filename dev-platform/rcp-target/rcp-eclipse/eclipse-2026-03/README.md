# Eclipse RCP 2026-03 staging area

This directory is the **parallel staging area** for the first coherent RCP re-vendoring slice.

## Current status
- It is **not** part of the active target definition.
- The active build still uses `../eclipse/` as the baseline RCP repository.
- This staging area is currently intended for **metadata-first auditing** before any target swap.

## Source repository
- Composite release URL: `https://download.eclipse.org/releases/2026-03/`
- Direct child repository selected for staging: `https://download.eclipse.org/releases/2026-03/202603111000/`

## Files expected here
- `content.jar`
- `content.xml`
- `artifacts.jar`
- `artifacts.xml`
- `stage-manifest.json`

## Refresh command
```zsh
python3 -u /Users/david/IdeaProjects/Modelio/dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03/stage_metadata.py
```

## Repinning-slice preparation command
```zsh
python3 -u /Users/david/IdeaProjects/Modelio/dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03/stage_repin_slice.py
```

This writes:
- `repin-suggestions.json` with proposed `2026-03` replacements/removals for:
  - `features/opensource/org.modelio.e4.rcp/feature.xml`
  - `features/opensource/org.modelio.rcp/feature.xml`
  - `features/opensource/org.modelio.platform.feature/feature.xml`
- `slice-cache/plugins/` and `slice-cache/features/` with the direct staged artefacts referenced by those suggestions.

## Important rule
Do not point `dev-platform/rcp-target/rcp.target` at this directory until the grouped repinning work for:
- `features/opensource/org.modelio.e4.rcp/feature.xml`
- `features/opensource/org.modelio.rcp/feature.xml`
- `features/opensource/org.modelio.platform.feature/feature.xml`
- `products/modelio-os.product`
has been prepared against the staged metadata.

