# macOS Recovery Plan for Modelio

## Goal
Restore a working macOS build with the smallest practical change set.

## Current status
Phase 1 is now **functionally proven** on an Apple Silicon Mac using:
- the packaged Intel macOS build (`x86_64`),
- Rosetta,
- an externally installed Java 11 runtime.

Example launch command used during validation:

```zsh
cd /Users/david
export HOME=/Users/david/IdeaProjects/Modelio/products/target/runtime-home-java11-x64
mkdir -p "$HOME"
arch -x86_64 "/Users/david/IdeaProjects/Modelio/products/preserved-macos/Modelio 5.4.1 x86_64.app/Contents/MacOS/modelio" \
  -vm "/Library/Java/JavaVirtualMachines/temurin-11.jdk/Contents/Home/bin/java" \
  -clean \
  -consoleLog
```

The validated Rosetta app bundle is preserved outside build output at:
`products/preserved-macos/Modelio 5.4.1 x86_64.app`


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
Phase 2 target: produce a **fully native Apple Silicon build** with **no `x86_64` code anywhere** in the shipped macOS product.

This means more than changing the product architecture in one POM. The final `.app` must contain:
- an `arm64` launcher,
- `arm64` SWT fragments,
- `arm64` browser support or an explicit browser replacement/removal,
- `arm64` Modelio-native fragments,
- no shipped `x86_64` macOS bundles, libraries, or helper executables.

### Phase 2 workstream 1: packaging and product metadata
Goal: create a native `macosx/cocoa/aarch64` product path.

Files likely involved:
- `products/pom.xml`
- root `pom.xml`
- `maven/modelio-parent/pom.xml`
- `products/modelio-os.product`

Concrete tasks:
1. Add a native mac profile for `macosx/cocoa/aarch64` alongside the current Intel profile. ✅ DONE as a parallel `platform.mac.aarch64` profile so the working `platform.mac` (`x86_64`) path remains unchanged.
2. Decide whether to keep both mac architectures in parallel during migration or switch the main mac profile entirely to `aarch64`.
3. Ensure the packaged mac archive name and environments reflect `aarch64` rather than `x86_64`.
4. Keep the mac product on an external Java runtime initially unless a bundled ARM JRE is deliberately added.

Definition of done for this stream:
- Tycho can package a `macosx/cocoa/aarch64` product archive.

### Phase 2 workstream 2: Eclipse launcher and SWT
Goal: replace the Intel mac launcher/SWT path with native Apple Silicon equivalents.

Files likely involved:
- `features/opensource/org.modelio.e4.rcp/feature.xml`
- `features/opensource/org.modelio.rcp/feature.xml`
- `dev-platform/rcp-target/rcp-eclipse/eclipse/*`
- `dev-platform/rcp-target/rcp-eclipse/swt/pom.xml`

Concrete tasks:
1. Add `org.eclipse.equinox.launcher.cocoa.macosx.aarch64` to the local target platform. ✅ DONE via the additive local p2 site `dev-platform/rcp-target/rcp-eclipse/launcher-arm64`.
2. Wire `org.eclipse.equinox.launcher.cocoa.macosx.aarch64` into `org.modelio.e4.rcp` alongside the Intel mac launcher fragment. ✅ DONE.
3. Wire `org.eclipse.swt.cocoa.macosx.aarch64` into `org.modelio.e4.rcp` alongside the Intel SWT mac fragment. ✅ DONE.
4. Validate that the current Eclipse/RCP baseline can actually resolve and launch with these ARM fragments. ✅ PARTIALLY DONE at feature scope: `org.modelio.e4.rcp` now packages successfully under `-P platform.mac.aarch64`.
5. If the current vendored Eclipse platform cannot supply a coherent ARM launcher/SWT stack, refresh the vendored Eclipse target platform before going further.

Current gate after Phase 2 step 1:
- `org.eclipse.swt.cocoa.macosx.aarch64` is already locally staged in `dev-platform/rcp-target/rcp-eclipse/swt/plugins`.
- `org.eclipse.equinox.launcher.cocoa.macosx.aarch64` is now staged through the additive local site `dev-platform/rcp-target/rcp-eclipse/launcher-arm64`.
- `features/opensource/org.modelio.e4.rcp/feature.xml` now includes parallel macOS `aarch64` launcher and SWT fragments, and the feature packages successfully under `platform.mac.aarch64`.
- The next safe move is to extend validation beyond the feature itself and identify the next native ARM blocker in the broader product stack.

Additional blocker discovered during staged ARM validation:
- `features/opensource/org.modelio.platform.feature/feature.xml` still depends on mac platform fragments whose vendored versions are Intel-filtered (`org.eclipse.core.filesystem.macosx 1.3.200` and `org.eclipse.equinox.security.macosx 1.101.200`).
- Compatible macOS fragments with `aarch64` support are now staged through the additive local site `dev-platform/rcp-target/rcp-eclipse/macos-arm64`.

Decision gate:
- If `org.eclipse.equinox.launcher.cocoa.macosx.aarch64` is unavailable or incompatible in the current target, a platform refresh becomes mandatory.

Definition of done for this stream:
- the packaged mac launcher binary reports `arm64`,
- SWT resolves and the app reaches UI startup without Rosetta.

### Phase 2 workstream 3: embedded browser strategy
Goal: eliminate the Intel-only Chromium browser fragment from the mac build.

Files likely involved:
- `features/opensource/org.modelio.e4.rcp/feature.xml`
- local Eclipse target platform under `dev-platform/rcp-target/rcp-eclipse/**`

Current blocker in repo state:
- `org.eclipse.swt.browser.chromium.cocoa.macosx.x86_64` is explicitly shipped today.

Concrete tasks:
1. Determine whether an `org.eclipse.swt.browser.chromium.cocoa.macosx.aarch64` artifact exists and is stable enough for this Eclipse baseline.
2. If yes, add it to the target and wire it into the feature.
3. If no, decide one of the following explicitly:
   - refresh the Eclipse baseline to one that supports ARM Chromium cleanly,
   - switch to a different browser strategy on macOS,
   - temporarily disable browser-dependent functionality for native ARM until a supported replacement exists.

Decision gate:
- Native ARM cannot be considered complete while the shipped mac product still depends on the Intel-only Chromium fragment.

Definition of done for this stream:
- no `org.eclipse.swt.browser.chromium.cocoa.macosx.x86_64` remains in the shipped mac product.

### Phase 2 workstream 4: Modelio-native fragments
Goal: remove or replace Modelio-specific Intel-only mac binaries.

Files likely involved:
- `features/opensource/org.modelio.platform.libraries/feature.xml`
- `dev-platform/rcp-target/modelio-integ/org.astyle/astyle/*`
- any source/build project used to generate `org.modelio.astyle.*`

Current blocker in repo state:
- `org.modelio.astyle.macosx.cocoa.x86_64` is explicitly shipped today.

Concrete tasks:
1. Build or acquire an `arm64` variant of the AStyle fragment.
2. Publish it into the local p2 repository under `dev-platform/rcp-target/modelio-integ/org.astyle/astyle`.
3. Add the new ARM fragment to `org.modelio.platform.libraries`.
4. Remove the Intel mac AStyle fragment from the native ARM product path.
5. Audit for any additional mac-native helper binaries and apply the same rule.

Definition of done for this stream:
- no Modelio-shipped mac fragment in the final product is `x86_64`.

### Phase 2 workstream 5: runtime policy
Goal: run natively on Apple Silicon without Rosetta.

Files likely involved:
- `products/modelio-os.product`
- `dev-platform/pack-resources/openjdk-jre11/**` if a bundled mac JRE is introduced

Concrete tasks:
1. Keep external Java as the default early in Phase 2 to reduce moving parts.
2. Validate native launch with an `arm64` Java 11 runtime first.
3. Only after native launch succeeds, decide whether to:
   - keep external Java on macOS, or
   - add a bundled macOS ARM JRE.
4. If a bundled JRE is added, ensure it is `arm64` only for the native build and does not reintroduce Intel-only payloads.

Definition of done for this stream:
- the native Apple Silicon app launches using an `arm64` Java runtime with no Rosetta involvement.

### Phase 2 workstream 6: validation and zero-`x86_64` exit criteria
Goal: prove the native product is truly ARM-only.

Required validation sequence:
1. Validate target resolution with the native mac environment.
2. Build affected plugins/features.
3. Package the native mac product archive.
4. Launch the app on Apple Silicon without Rosetta.
5. Run the same smoke tests as Phase 1, plus:
   - save and reopen a project,
   - exercise at least one browser/help workflow,
   - exercise any feature depending on `org.modelio.astyle` if applicable.

Required artifact inspection:
1. Check the launcher with `file` and confirm `arm64`.
2. Inspect mac-native Eclipse fragments in the packaged app and confirm there is no `cocoa.macosx.x86_64` fragment shipped.
3. Inspect Modelio-native mac fragments and confirm there is no `org.modelio.*.macosx.cocoa.x86_64` artifact shipped.
4. If a JRE is bundled, inspect it and confirm no `x86_64` binaries are present.
5. Search the final packaged mac product contents for `x86_64` references and treat any surviving macOS-native hit as a release blocker.

Phase 2 exit criteria:
- the packaged mac app launches natively on Apple Silicon,
- no Rosetta is required,
- no shipped macOS-native executable, fragment, or helper binary is `x86_64`,
- no `cocoa.macosx.x86_64` mac fragment remains in the final product,
- core manual workflows complete successfully on the native build.

### Recommended implementation order
1. Packaging profile for `aarch64`.
2. ARM launcher fragment.
3. ARM SWT fragment.
4. Browser strategy decision.
5. ARM AStyle / Modelio-native fragments.
6. Native launch validation.
7. Zero-`x86_64` artifact audit.

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

