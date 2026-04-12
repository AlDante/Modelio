# macOS Recovery Plan for Modelio

## Goal
Restore a working macOS build with the smallest practical change set.

## Current status
Phase 1 is now **functionally proven** on an Apple Silicon Mac using:
- the packaged Intel macOS build (`x86_64`),
- Rosetta,
- an externally installed Java 11 runtime. 
`cd /Users/david
export HOME=/Users/david/IdeaProjects/Modelio/products/target/runtime-home-java11-x64
mkdir -p "$HOME"
arch -x86_64 "/Users/david/IdeaProjects/Modelio/products/target/mac-run/Modelio 5.4.1.app/Contents/MacOS/modelio" \
  -vm "/Library/Java/JavaVirtualMachines/temurin-11.jdk/Contents/Home/bin/java" \
  -clean \
  -consoleLog`


Manual validation completed so far:
- Modelio launched successfully,
- a project was created,
- a class diagram was created.

This proves the minimum-change recovery path is viable on Apple Silicon through Rosetta.
It does **not** yet prove full feature coverage, nor does it replace a separate Intel Mac validation run.

## Recommended scope
Phase 1 should target **Intel macOS (`x86_64`) packaging**, with **Apple Silicon running the Intel build via Rosetta**.

Why this is the minimum-change path:
- The repo still contains Intel-mac feature wiring in `features/opensource/org.modelio.e4.rcp/feature.xml` and `features/opensource/org.modelio.rcp/feature.xml`.
- The repo does **not** contain a complete native Apple Silicon path: there is no `org.eclipse.equinox.launcher.cocoa.macosx.aarch64` in the workspace, and the shipped feature XMLs do not reference `cocoa.macosx.aarch64`.
- The bundled JRE site under `dev-platform/pack-resources/openjdk-jre11` has Linux/Windows roots only.

## What the repo already supports
The current source tree still includes Intel-mac pieces:
- `features/opensource/org.modelio.e4.rcp/feature.xml`
  - `org.eclipse.equinox.launcher.cocoa.macosx.x86_64`
  - `org.eclipse.swt.cocoa.macosx.x86_64`
  - `org.eclipse.swt.browser.chromium.cocoa.macosx.x86_64`
- `features/opensource/org.modelio.rcp/feature.xml`
  - `org.eclipse.ui.cocoa`
- `features/opensource/org.modelio.platform.feature/feature.xml`
  - `org.eclipse.core.filesystem.macosx`
  - `org.eclipse.equinox.security.macosx`
- `features/opensource/org.modelio.platform.libraries/feature.xml`
  - `org.modelio.astyle.macosx.cocoa.x86_64`

## Main gaps to close
1. `products/pom.xml` no longer defines an active macOS packaging profile.
2. `products/pom.xml` only packages Linux and Windows in `package.all`.
3. `dev-platform/pack-resources/openjdk-jre11` does not provide a macOS JRE root.
4. Native Apple Silicon is incomplete because the launcher fragment is missing.

## Phase 1 plan: restore Intel-mac packaging

### Step 1: add a real mac packaging profile ✅ DONE
`products/pom.xml` has been updated with:
- a new `platform.mac` profile (`macosx/cocoa/x86_64`) equivalent to `platform.linux` and `platform.win`,
- `macosx/cocoa/x86_64` added to the `package.all` environment list,
- `<macosx>tar.gz</macosx>` added to the `formats` block in both `package.all` and `product.org`.

### Step 2: keep `products/modelio-os.product` unchanged initially
Do not start by changing launcher args or feature lists.

Reason:
- The product file already contains a mac launcher section and `vmArgsMac`.
- The immediate gap is packaging/runtime supply, not product identity.

### Step 3: do not bundle a mac JRE in Phase 1
Treat macOS as requiring an installed Java 11 runtime for the first recovery pass.

Evidence:
- `dev-platform/pack-resources/openjdk-jre11/features/net.adoptium.temurin.jre.feature_11.0.15/build.properties` has mac root entries commented out.
- `dev-platform/pack-resources/openjdk-jre11/binary` contains Linux and Windows roots only.

This keeps the first recovery attempt small and avoids introducing a second packaging problem.

### Step 4: validate Intel-mac dependency resolution before broader changes
Before attempting native ARM support, confirm that current Intel-mac bundles still resolve through the existing target platform and features.

Validation sequence — run these in order:

```zsh
# 1. Validate the target platform definition (run from repo root or prebuild dir)
mvn -f /Users/david/IdeaProjects/Modelio/AGGREGATOR/prebuild/pom.xml verify

# 2. Build all plugins
mvn -f /Users/david/IdeaProjects/Modelio/AGGREGATOR/plugins/pom.xml package

# 3. Build all features
mvn -f /Users/david/IdeaProjects/Modelio/AGGREGATOR/features/opensource/pom.xml package

# 4. Package the mac product archive
mvn -f /Users/david/IdeaProjects/Modelio/products/pom.xml package -P product.org,platform.mac
```

Expected output of Step 4: a `.tar.gz` file in `products/target/` for `macosx.cocoa.x86_64`.

These commands are derived from the checked POM structure; they should be verified in the local build environment.

### Step 5: test launch on macOS ✅ PARTIALLY VERIFIED
Validation order:
1. Intel Mac, if available.
2. Apple Silicon Mac under Rosetta.

Verified result so far:
- the packaged Intel macOS build launches on Apple Silicon via Rosetta,
- Java 11 is supplied externally on macOS,
- basic modeling workflow works in manual testing.

Manual validation record:
- launch the packaged app,
- create a project,
- create a class diagram.

Remaining Phase 1 confirmation still desirable:
- validate launch on an actual Intel Mac,
- extend smoke testing beyond the first basic modeling workflow.

Success criteria for Phase 1:
- a macOS product archive is produced,
- the application launches on Apple Silicon via Rosetta,
- basic manual modeling workflow succeeds,
- Java 11 is supplied externally on macOS.

## Short macOS validation checklist

Use this checklist for future macOS validation runs:

1. Build and package the mac product archive.
2. Extract and launch `Modelio 5.4.1.app`.
3. Confirm external Java 11 is used.
4. Verify the application opens without immediate launcher/runtime failure.
5. Create a project.
6. Create and save a class diagram.
7. Close and reopen the project.
8. Exercise one browser- or help-related feature if available.
9. Record whether the run was on:
   - Intel Mac, or
   - Apple Silicon via Rosetta.

## Phase 1 non-goals
Do **not** include these in the minimum-change pass:
- native Apple Silicon packaging,
- bundled macOS JRE,
- Eclipse RCP modernization,
- cleanup of legacy `vmArgsMac` unless they are proven to block launch.

## Phase 2: native Apple Silicon support
Only start this after the Intel-mac build works.

Expected additional work:
- refresh the target platform / Eclipse baseline,
- add `org.eclipse.equinox.launcher.cocoa.macosx.aarch64`,
- wire `cocoa.macosx.aarch64` fragments into the shipped features,
- decide whether to bundle a macOS ARM JRE,
- validate SWT/Chromium behavior on current macOS.

## Risks and likely blockers
- Gatekeeper, signing, and notarization are not visible in the current repo and may still affect distribution usability.
- The browser stack (`org.eclipse.swt.browser.chromium.cocoa.macosx.x86_64`) may have runtime issues on current macOS even if packaging succeeds.
- Apple Silicon support remains incomplete until the launcher fragment and feature wiring are modernized.

## Recommended decision
If the priority is to make Modelio usable on Macs again quickly, the confirmed first move is:
1. restore `x86_64` mac packaging,
2. rely on installed Java 11 for macOS,
3. run Apple Silicon through Rosetta,
4. defer native ARM support to a second phase.

That Phase 1 path is now validated for basic manual usage on Apple Silicon via Rosetta.

