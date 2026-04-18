# Modelio modernization plan

## Purpose
Modernize Modelio in a correctness-first sequence without breaking the now-working Apple Silicon packaging flow.

## Status snapshot as of 2026-04-17
- The immediate recovery goal is already achieved: the project builds and a signed Apple Silicon `Modelio.app` can be produced and launched.
- The modernization plan is still correctness-first. The intended order remains: stabilize the current platform composition first, then clean up remaining mac-native skew, then revisit Tycho, then move Java, then re-vendor Eclipse/RCP.
- The bounded `Tycho 2.7.5` bridge uplift is now complete on the current vendored `4.18` runtime target.
- That does **not** change the broader sequencing: the next modernization hop after this bridge remains a bounded `Tycho 5.0.2` probe, then Java-baseline cleanup, then the larger RCP re-vendoring.
- Current verified Tycho state in the workspace:
  - `pom.xml` = `2.7.5`
  - `maven/modelio-parent/pom.xml` = `2.7.5`
  - `doc/parent/pom.xml` = `2.7.5`
  - `dev-platform/rcp-target/jakarta/jaxb/pom.xml` = `2.7.5`

## Build-orchestration note from 2026-04-17
- The temporary mixed-Tycho reactor blocker is gone because the main build, the shared modelio parent, and the docs parent are now all aligned on `Tycho 2.7.5`.
- `AGGREGATOR/prebuild/pom.xml` now refreshes the stable Apple Silicon overlay repositories (`launcher-arm64`, `macos-arm64`, `jna`) before validating `dev-platform/rcp-target/rcp.target`.
- The product-side `separateEnvironments` warning was removed from `products/pom.xml`, and the packaged macOS app no longer needs an explicit `org.eclipse.equinox.executable` feature entry to materialize successfully.

## Status update as of 2026-04-17
- The documented macOS `aarch64` scratch-build workflow is now verified through `products`, not just through `plugins` and `features`.
- A clean staged run using a dedicated scratch local repository now succeeds in this order: `prebuild -> plugins -> features -> doc -> products`.
- The `products` stage required an explicit fix in `products/pom.xml` so the `platform.mac.aarch64` profile requests the Equinox mac launcher bundles during product materialization.
- `MACOS_AARCH64_BUILD_PROCESS.md` now records:
  - the validated IntelliJ/Maven scratch-build targets,
  - the required stage order,
  - the shared scratch local repository flow,
  - and the final launchable output path `products/target/products/org.modelio.product/macosx/cocoa/aarch64/Modelio.app`.
- This means the current `Tycho 2.7.5` / `Java 11` build contract is reproducible from scratch for the Apple Silicon product path.

### Immediate next modernization step
- **Do not broaden the work yet.**
- The best next step is to make the target platform self-contained and headless-clean before any broader Tycho or Java uplift.
- That means prioritizing these two items:
  1. remove the external/manual JNA prerequisite from the Apple Silicon build flow,
  2. eliminate the `${project_loc:/...}` warnings emitted from `dev-platform/rcp-target/rcp.target` during headless Maven/Tycho validation.

### Progress update on 2026-04-17
- The headless target-definition cleanup has now started and its first pass is complete.
- `dev-platform/rcp-target/rcp.target` and `dev-platform/rcp-target/rcp_debug.target` were changed from `${project_loc:/...}` paths to workspace-relative paths.
- The stale missing `test-resources/files` target entry was removed from both target definitions.
- Revalidation of `AGGREGATOR/prebuild/pom.xml` on `platform.mac.aarch64` is green, and the previous `${project_loc:/rcp-target}`, `${project_loc:/pack-resources}`, `${project_loc:/test-resources}`, and `target resoloution might be incomplete` warnings are no longer present in the new log `diagnostics/macos-aarch64/prebuild-verify-after-target-path-cleanup.log`.
- The Apple Silicon JNA overlay can now be generated headlessly from Maven alone against a fresh local repository; the old external JNA source checkout is no longer required to create the overlay.
- The build now uses a stable repo-owned JNA p2 path at `dev-platform/rcp-target/rcp-eclipse/jna/repository/`, and the JNA generator now refreshes that stable path while deleting the transient staged `target/repository` output before the build completes.
- `AGGREGATOR/prebuild/pom.xml` now includes the JNA overlay generator module so the overlay can be refreshed inside the staged build flow, while the stable checked-in repository remains available before reactor resolution starts.
- The target-platform contract is now normalized across `dev-platform/rcp-target/rcp.target`, `dev-platform/rcp-target/rcp_debug.target`, `pom.xml`, `maven/modelio-parent/pom.xml`, and IntelliJ repository metadata so the same Apple Silicon overlay set is described consistently in every build entrypoint.
- This means the original immediate target-platform hardening goal is substantially complete: the headless path warnings are gone and the external/manual JNA prerequisite has been removed from the validated staged workflow.

### Remaining follow-up after target-platform hardening
- The one-shot `AGGREGATOR/pom.xml` scratch path has now also been revalidated after the SWT-resolution investigation.
- Root cause of the transient `org.modelio.platform.rcp` compile failure: fresh scratch resolution was mirroring the `org.eclipse.swt` base bundle without also mirroring the Apple Silicon SWT fragment, and the base SWT jar is only a stub for compilation purposes.
- The fix was to explicitly require `org.eclipse.swt.cocoa.macosx.aarch64` in the root `platform.mac.aarch64` profile.
- This means both documented workflows are now green again:
  1. the correctness-first staged `prebuild -> plugins -> features -> doc -> products` path,
  2. the one-shot `AGGREGATOR/pom.xml -Pplatform.mac.aarch64,product.org clean package` path from a fresh local Maven repository.
- Only after this should the plan broaden again toward lower-priority build-hygiene cleanup or renewed Tycho bridge work.

### Why this is the next step
- The major build-breaker work is now done: scratch `products` packaging can complete and materialize the final `.app`.
- The highest remaining reproducibility risks are now in the target-platform contract itself, not in plugin/feature/product reactor wiring.
- Until the target platform is self-contained and warning-clean, further Tycho uplift or broader platform modernization will keep producing noisy and harder-to-localize failures.

### Deferred until after target-platform cleanup
- central encoding cleanup,
- missing `.settings/org.eclipse.jdt.core.prefs` cleanup,
- further Tycho bridge work beyond the already-proved bounded experiments,
- broader Java baseline movement.

## Current baseline verified from the repo
- Build/tooling is now centered on `Tycho 2.7.5` and `Java 11` in `pom.xml`, `maven/modelio-parent/pom.xml`, and `doc/parent/pom.xml`.
- The vendored Eclipse platform in `dev-platform/rcp-target/rcp-eclipse/eclipse` is still the `2020-12` line (`org.eclipse.platform_4.18.0.v20201202-1800`).
- `features/opensource/org.modelio.e4.rcp/feature.xml` and `features/opensource/org.modelio.rcp/feature.xml` hard-pin many 2020-era bundle versions.
- The repo is currently in a hybrid state: older platform/equinox bundles, but newer SWT overlays (`3.120.0`) and ARM-specific mac fragments staged separately.
- macOS is still mid-modernization, but the known Intel-only feature-composition exceptions have now been intentionally removed rather than shipped; mac Chromium and mac AStyle are both disabled pending native `aarch64` replacements.
- Bundle execution-environment baselines in source manifests are now normalized to `JavaSE-11` for the previously lagging core/BPMN bundles; the repo no longer has source `JavaSE-1.8` BREE declarations under `modelio/**/META-INF/MANIFEST.MF`.
- Remaining Java-8-era assumptions still exist in build metadata: several runtime bundles still have `javacSource/javacTarget = 1.8` in `build.properties`, while `doc/parent/pom.xml` remains on Java 8 as a doc/tooling-only branch.

## Recommended destination
- **Primary platform target:** a coherent vendored Eclipse/RCP `2026-03` stack, not a launcher-only uplift.
- **Primary Java target:** stabilize first on a modern LTS baseline (`Java 21`) for build + runtime.
- **Stretch Java target:** evaluate `Java 25` only after the `2026-03` migration is green end-to-end.
- **macOS target:** full native Apple Silicon product with no shipped `x86_64` mac-native code.

## Why not jump straight to Java 25?
Because this repo is constrained by four compatibility layers at once: Tycho, Eclipse RCP, vendored p2 content, and OSGi bundle execution environments. Jumping straight from the current `Java 11` / `RCP 4.18` baseline to `Java 25` would blur together toolchain failures, API breakage, reflective-access issues, and product packaging regressions.

## Tycho upgrade evaluation
- The main build, including the docs branch parent, is now green on `Tycho 2.7.5` in `pom.xml`, `maven/modelio-parent/pom.xml`, and `doc/parent/pom.xml`.
- The bridge objective for this phase is therefore met: the same source tree now builds cleanly on the newer Tycho line while still targeting the unchanged vendored `4.18` runtime.
- Given that the current public Tycho line is newer still (`5.0.2`, per your note), the next bounded tooling experiment is now `2.7.5 -> 5.0.2`, not `2.2.0 -> 5.0.2`.

### Recommendation
- **Do not combine the next Tycho step with runtime-side modernization.**
- **Do revisit Tycho again before the full `RCP 2026-03` re-vendoring, but from the new `2.7.5` baseline rather than from `2.2.0`.**
- Use a staged path:
  1. keep `2.7.5` while freezing the current build contract and removing obvious remaining Java-baseline skew,
  2. do a bounded uplift to `5.0.2` against the existing vendored `4.18` target,
  3. only then move to `RCP 2026-03`, after Tycho is already boring.

### Why we ran a Tycho probe anyway
- The early `2.7.5` trial was a bounded compatibility probe to answer one question: “is the build-tool uplift likely to be a cheap isolated step?”
- The answer appears to be **no, not yet**. Tycho hit target-validation problems in the current vendored target layout before any useful product-level signal was obtained.
- That result supports the original sequencing rather than contradicting it: the repo still needs more platform cleanup before Tycho becomes a low-noise change.

### Why this timing is safer
- Right now the repo still mixes old platform bundles with newer SWT/native overlays; an immediate Tycho jump would make it unclear whether a failure came from the build tool, the target platform, or native fragment composition.
- A Tycho-only spike against the unchanged `4.18` target gives a much cleaner signal.
- By the time the Eclipse train is re-vendored, the build layer should already be stable.

### Go / no-go rule for Tycho
- **Go** if prebuild, plugin aggregation, feature aggregation, and product packaging all stay green with the same vendored target content.
- **No-go** if the Tycho change forces broad `feature.xml` repinning, introduces new p2 ambiguity, or breaks the native mac package before any platform upgrade has begun.

## Migration sequence

### Phase 0 - Freeze and measure the current contract
Scope:
- Record the exact current platform, Tycho, Java, and native-fragment inventory.
- Treat `dev-platform/rcp-target/**`, `products/modelio-os.product`, and `features/opensource/org.modelio.*/*.xml` as the contract to preserve while upgrading.

Primary files:
- `pom.xml`
- `maven/modelio-parent/pom.xml`
- `doc/parent/pom.xml`
- `dev-platform/rcp-target/rcp.target`
- `products/modelio-os.product`

Exit gate:
- We can reproduce the current working macOS ARM package and the existing Linux/Windows builds from a clean workspace.

### Phase 1 - Remove baseline skew before any major uplift
Scope:
- Stop mixing unrelated Eclipse generations in `org.modelio.e4.rcp`.
- Align SWT, Equinox, workbench, launcher, and native fragments to one coherent train.
- Decide explicitly whether the browser fragment remains Chromium-based or is replaced/disabled on macOS.

Status today:
- **Partially completed, not complete.**
- Already done:
  - the repo now carries explicit Apple Silicon overlay repositories under `dev-platform/rcp-target/rcp-eclipse/`, notably `swt/`, `launcher-arm64/`, `macos-arm64/`, and `jna/`;
  - `features/opensource/org.modelio.e4.rcp/feature.xml` now includes an Apple Silicon launcher fragment (`org.eclipse.equinox.launcher.cocoa.macosx` for `aarch64`) and Apple Silicon SWT fragment (`org.eclipse.swt.cocoa.macosx.aarch64`);
  - the product can now be built and launched on Apple Silicon, which proves the recovery work succeeded at a practical level.
- Still not done:
  - `org.modelio.e4.rcp` is still a hybrid composition mixing `4.18/2020-12` platform bundles with newer SWT `3.120.0` overlays and newer arm64 launcher/native pieces;
  - `features/opensource/org.modelio.e4.rcp/feature.xml` still contains Intel-only mac browser content (`org.eclipse.swt.browser.chromium.cocoa.macosx.x86_64`);
  - the Phase 1 exit gate is therefore **not yet met**: we do not yet have one internally consistent vendored target train.

Why first:
- A mixed 2020 + 2022 + local-overlay stack makes later failures impossible to localize.

Primary files:
- `features/opensource/org.modelio.e4.rcp/feature.xml`
- `features/opensource/org.modelio.rcp/feature.xml`
- `dev-platform/rcp-target/rcp-eclipse/**`
- `dev-platform/rcp-target/rcp.target`

Exit gate:
- The existing product packages cleanly from one internally consistent vendored target platform.

#### Concrete remaining checklist for Phase 1
1. **Inventory the mixed-train inputs.**
   - Review `features/opensource/org.modelio.e4.rcp/feature.xml` and `dev-platform/rcp-target/rcp.target`.
   - Classify every non-baseline overlay currently involved in the Apple Silicon recovery path: newer `SWT`, arm64 launcher fragments, mac arm64 native fragments, `JNA`, and any browser-related fragment.
   - Exit condition: every mixed-generation contribution is explicitly identified as baseline, overlay, or unresolved.

2. **Choose the single runtime baseline that Phase 1 is normalizing to.**
   - Use only content that is already vendored under `dev-platform/rcp-target/rcp-eclipse/`.
   - Decide, for each overlay repository under that directory, whether it is being kept temporarily, replaced, or removed from the Phase 1 composition.
   - Exit condition: there is one documented target train that `org.modelio.e4.rcp` is supposed to represent.

3. **Re-pin `org.modelio.e4.rcp` to that one train.**
   - Align `SWT`, Equinox launcher fragments, workbench-adjacent native fragments, and related platform bundles inside `features/opensource/org.modelio.e4.rcp/feature.xml`.
   - The goal here is not to modernize to `2026-03`; it is to stop mixing unrelated platform generations in one feature.
   - Exit condition: `org.modelio.e4.rcp` no longer contains an ad-hoc `2020 + 2022 + local overlay` mixture.

4. **Make the mac browser decision explicit.**
   - Decide whether `org.eclipse.swt.browser.chromium.cocoa.macosx.x86_64` remains temporarily, is replaced by a coherent equivalent, or is disabled on macOS for the Phase 1 baseline.
   - Update `features/opensource/org.modelio.rcp/feature.xml` only if that decision requires matching composition changes there.
   - Exit condition: browser behavior is intentional rather than accidental, and the two RCP features are internally consistent.

5. **Trim `rcp.target` to the minimum target layout required by that choice.**
   - Keep Phase 1 focused on target consistency, not on a broad target re-vendoring.
   - Remove target-definition ambiguity that exists only because multiple platform generations are being tolerated at once.
   - Exit condition: `dev-platform/rcp-target/rcp.target` points at one internally consistent vendored platform layout.

6. **Re-run the current build ladder on the unchanged Tycho/Java baseline.**
   - Validate with the existing `Tycho 2.2.0` main build and `Java 11` baseline.
   - Re-run prebuild, plugin aggregation, feature aggregation, and product packaging before claiming Phase 1 complete.
   - Exit condition: the existing product packages cleanly from the coherent vendored target, satisfying the Phase 1 gate.

#### Phase 1 Step 1 findings - mixed-train inventory completed on 2026-04-15
- `dev-platform/rcp-target/rcp.target` currently resolves the RCP layer from **six** separate inputs at once: `eclipse/`, `eclipse-fr/`, `launcher-arm64/`, `macos-arm64/`, `jna/repository`, and `swt/`.
- The dominant baseline is still the vendored Eclipse `4.18 / 2020-12` repository under `dev-platform/rcp-target/rcp-eclipse/eclipse`.
- Apple Silicon support was recovered by layering newer repos on top of that baseline rather than by re-vendoring one coherent platform train.
- The most important unresolved skew is the browser stack: SWT itself is newer, but the mac Chromium browser fragment is still only present as `x86_64` baseline content.

| Area | Feature pin / active version | Vendored source | Classification | Note |
| --- | --- | --- | --- | --- |
| Core launcher | `org.eclipse.equinox.launcher` `1.6.0.v20200915-1508` | `rcp-eclipse/eclipse` | baseline | Matches the main `4.18 / 2020-12` train. |
| mac launcher x86_64 | `org.eclipse.equinox.launcher.cocoa.macosx.x86_64` `1.2.0.v20200915-1442` | `rcp-eclipse/eclipse` | baseline | Old Intel launcher fragment kept alongside Apple Silicon support. |
| mac launcher arm64 | `org.eclipse.equinox.launcher.cocoa.macosx` `1.2.200.v20210527-0259` | `rcp-eclipse/launcher-arm64` | overlay | Newer arm64-only recovery overlay; outside the baseline train. |
| SWT base bundle | `org.eclipse.swt` `3.120.0.v20220530-1036` | `rcp-eclipse/swt` | overlay | Baseline `eclipse/` repo still contains only `3.115.100.v20201202-1103`. |
| SWT mac fragments | `org.eclipse.swt.cocoa.macosx.x86_64` and `org.eclipse.swt.cocoa.macosx.aarch64` `3.120.0.v20220530-1036` | `rcp-eclipse/swt` | overlay | Apple Silicon runtime depends on the newer SWT family, not the `4.18` baseline SWT. |
| Chromium browser | `org.eclipse.swt.browser.chromium.cocoa.macosx.x86_64` `3.115.100.v20201202-1103` | `rcp-eclipse/eclipse` | unresolved | No matching vendored arm64 Chromium fragment was found; browser support is still Intel-only on macOS. |
| JNA | `com.sun.jna` and `com.sun.jna.platform` `5.18.1` | `rcp-eclipse/jna/repository` | overlay | Baseline `eclipse/` repo still ships `4.5.1.v20190425-1842`. |
| mac filesystem fragment | `org.eclipse.core.filesystem.macosx` `1.3.400.v20220812-1420` | `rcp-eclipse/macos-arm64` | overlay | `org.modelio.platform.feature` uses a newer mac fragment than the baseline `1.3.200.v20190903-0945`. |
| mac security fragment | `org.eclipse.equinox.security.macosx` `1.101.400.v20210427-1958` | `rcp-eclipse/macos-arm64` | overlay | `org.modelio.platform.feature` uses a newer mac fragment than the baseline `1.101.200.v20190903-0934`. |

Implication for Phase 1 Step 2:
- The most realistic normalization target is still the current `4.18 / 2020-12` baseline, with only the minimum Apple Silicon overlays kept deliberately.
- The browser fragment is the clearest item that cannot currently be normalized into a native arm64 story from the vendored inputs alone.

#### Phase 1 Step 2 findings - baseline normalization target chosen on 2026-04-15
- **Chosen Phase 1 baseline:** keep `dev-platform/rcp-target/rcp-eclipse/eclipse` as the canonical runtime train to normalize around.
- **Reason:** it is still the dominant vendored RCP stack, and the current Apple Silicon recovery works by layering a small number of newer repos over it.
- **Normalization rule for Phase 1:** remove no repos immediately; instead, classify each repo as canonical baseline, baseline-adjacent, temporary Apple Silicon overlay, or unresolved exception.
- **Important boundary:** this is still a stabilization exercise, not a `2026-03` uplift.

| Target input | Decision for Phase 1 | Why |
| --- | --- | --- |
| `rcp-eclipse/eclipse` | **Keep as canonical baseline** | Contains the main Eclipse `4.18 / 2020-12` platform and remains the dominant source for Equinox, workbench, RCP, browser fragments, and most runtime bundles. |
| `rcp-eclipse/eclipse-fr` | **Keep as baseline-adjacent** | It is aligned to the same `4.18` line and is still justified by feature usage such as `org.eclipse.jface.nl_fr` in `features/opensource/org.modelio.platform.libraries/feature.xml`. |
| `rcp-eclipse/launcher-arm64` | **Keep as temporary Apple Silicon overlay** | Required for `org.eclipse.equinox.launcher.cocoa.macosx` `1.2.200.v20210527-0259`, which has no equivalent arm64 fragment in the baseline repo. |
| `rcp-eclipse/macos-arm64` | **Keep as temporary Apple Silicon overlay** | Required for newer mac-native fragments such as `org.eclipse.core.filesystem.macosx` `1.3.400.v20220812-1420` and `org.eclipse.equinox.security.macosx` `1.101.400.v20210427-1958`. |
| `rcp-eclipse/jna/repository` | **Keep as temporary overlay** | Required because `org.modelio.e4.rcp` pins `com.sun.jna` and `com.sun.jna.platform` `5.18.1`, newer than the baseline `4.5.1` payload in `eclipse/`. |
| `rcp-eclipse/swt` | **Keep as temporary overlay, but treat as the least minimal one** | Required because the current runtime depends on the newer `org.eclipse.swt` family `3.120.0.v20220530-1036`; however, this overlay replaces a broad cross-platform SWT family rather than a narrow mac-only fragment. |

Explicit unresolved exception carried forward from Step 2:
- `org.eclipse.swt.browser.chromium.cocoa.macosx.x86_64` remains unresolved.
- The vendored inputs currently provide only the Intel mac Chromium fragment in the baseline `eclipse/` repo.
- Therefore Phase 1 can normalize the surrounding platform composition, but it cannot yet make the mac browser story fully native from existing vendored inputs alone.

Immediate consequence for Phase 1 Step 3:
- Re-pinning should aim for a **deliberate hybrid** rather than an accidental one: baseline `4.18 / 2020-12`, plus only the four explicitly retained overlays above.
- Any bundle pin that still falls outside that rule after re-checking should be treated as new skew and either justified or removed.

#### Phase 1 Step 3 findings - `org.modelio.e4.rcp` audit completed on 2026-04-15
- A repo-to-feature audit of `features/opensource/org.modelio.e4.rcp/feature.xml` found **86** pinned plugins.
- After checking those pins against the approved repo set from Step 2, `org.modelio.e4.rcp` is already very close to the intended deliberate hybrid.
- In practice, the feature currently resolves from:
  - canonical baseline `rcp-eclipse/eclipse`,
  - temporary overlays `rcp-eclipse/swt`, `rcp-eclipse/launcher-arm64`, and `rcp-eclipse/jna/repository`,
  - plus the explicit unresolved exception `org.eclipse.swt.browser.chromium.cocoa.macosx.x86_64`.
- No direct `macos-arm64` usage was found in `org.modelio.e4.rcp`; those newer mac-native fragments belong to `org.modelio.platform.feature`, not this e4 feature.
- No direct `eclipse-fr` usage was found in `org.modelio.e4.rcp`; foreign-language content is therefore **not** a blocker for this Step 3 audit.

Decision table for Step 3:

| Category inside `org.modelio.e4.rcp` | Decision | Notes |
| --- | --- | --- |
| Baseline `4.18 / 2020-12` pins | **Keep** | The large majority of the feature remains correctly pinned to the canonical `eclipse/` repo. |
| `org.eclipse.equinox.launcher.cocoa.macosx` `1.2.200.v20210527-0259` | **Keep as justified overlay** | This is the approved arm64 launcher overlay from `launcher-arm64/`. |
| `org.eclipse.swt*` `3.120.0.v20220530-1036` | **Keep as justified overlay** | This is the approved SWT overlay family from `swt/`. |
| `com.sun.jna` and `com.sun.jna.platform` `5.18.1` | **Keep as justified overlay** | This is the approved JNA overlay from `jna/repository`. |
| `org.eclipse.swt.browser.chromium.cocoa.macosx.x86_64` `3.115.100.v20201202-1103` | **Carry forward as explicit unresolved exception** | This stays in scope for Phase 1 Step 4 and Phase 2, not as silent skew. |

Net result of Step 3:
- There is **no newly discovered accidental skew inside `org.modelio.e4.rcp` beyond the already-known browser exception**.
- That means Phase 1 does **not** need a broad repinning sweep in this feature before the browser decision is made.
- The next meaningful action is Phase 1 Step 4: make the mac browser decision explicit.

Foreign-language support note:
- Dropping foreign-language support is **not required** for Phase 1 Step 3.
- `org.modelio.e4.rcp` itself does not depend on `nl_*` bundles.
- If simplification becomes necessary during a later modernization step, `eclipse-fr` is a reasonable early candidate to drop because its current justification comes from separate feature composition, not from this e4 runtime core.

#### Phase 1 Step 4 findings - mac Chromium browser disabled on 2026-04-15
- `org.eclipse.swt.browser.chromium.cocoa.macosx.x86_64` is **not required for basic Modelio startup**.
- The codebase uses generic SWT `Browser` widgets, but no Chromium-specific selection or `SWT.CHROMIUM` usage was found.
- Startup-adjacent browser usage exists in the first-launch `WelcomeView`, but that code still relies on the generic SWT browser API rather than on the Chromium fragment specifically.
- To eliminate non-native exceptions on Apple Silicon, the Intel-only mac Chromium fragment has been removed from `features/opensource/org.modelio.e4.rcp/feature.xml`.
- Decision: **disable mac Chromium integration for now rather than ship Intel-only browser native code**.

Restoration note for later modernization:
- mac embedded-browser support on macOS should be restored only when a coherent native `aarch64` browser-capable solution exists in the modernized platform stack.
- That restoration belongs after the broader RCP modernization work, not as a one-off exception in the current hybrid baseline.
- If browser-backed UI on macOS shows regressions before then, prefer targeted fallback behavior (for example, welcome/help degradation) over re-introducing `x86_64` browser native code.

#### Phase 2 Step 1 findings - mac AStyle fragment disabled on 2026-04-15
- `org.modelio.astyle.macosx.cocoa.x86_64` was shipped only as an Intel mac fragment from `dev-platform/rcp-target/modelio-integ/org.astyle/astyle/plugins/`.
- No vendored native `aarch64` AStyle fragment exists in the current repo.
- Code inspection indicates AStyle is not required for basic application startup:
  - native loading is wrapped in `UnsatisfiedLinkError` handling in `modelio/platform/platform.api/src/org/modelio/api/astyle/AStyleInterface.java`,
  - the exposed API appears to serve optional formatting/script functionality rather than startup wiring.
- To avoid shipping non-native mac code, `org.modelio.astyle.macosx.cocoa.x86_64` has been removed from `features/opensource/org.modelio.platform.libraries/feature.xml`.
- Decision: **disable mac AStyle integration for now rather than ship Intel-only AStyle native code**.

Restoration note for AStyle:
- mac AStyle support should be restored only when a native `aarch64` fragment is available and vendored into the modernized platform stack.
- Until then, prefer temporary loss of AStyle-backed formatting on macOS ARM over re-introducing Intel-only native payload.

#### Phase 2 Step 2 findings - packaged app native audit completed on 2026-04-15
- Audited artifact:
  - `products/target/products/org.modelio.product/macosx/cocoa/aarch64/Modelio.app`
- Audit method:
  - walked every file in the final `.app` bundle and checked it with `/usr/bin/file` for `x86_64` markers.
- Result:
  - `HITS 0`
- Interpretation:
  - the **final packaged Apple Silicon app currently contains no shipped `x86_64` files**.
  - This is the product-level source of truth for the no-Intel-payload checkpoint.
  - It also means some remaining `x86_64` entries in source `feature.xml` files may be filtered out by OS/arch-specific packaging and therefore do not automatically imply a shipped Intel payload.

Practical implication:
- The no-`x86_64` packaged-artifact check is already green for the currently built `Modelio.app`.
- The remaining cleanup work is therefore mostly about keeping source composition intentional and preparing for modernization, not about fixing a currently shipped Intel binary in the final app bundle.

#### Revalidation after source changes - rebuilt product audit completed on 2026-04-16
- A direct full rebuild from `AGGREGATOR/pom.xml` had been blocked by mixed Tycho versions in one reactor:
  - the main build was on `Tycho 2.2.0`,
  - the doc branch had temporarily been on `Tycho 2.7.5`.
- That blocker was build-tooling related, not a product-native-payload failure.
- It has now been removed by aligning `doc/parent/pom.xml` back to `2.2.0`.
- To revalidate the latest source state anyway, the product was rebuilt with a scoped staged sequence:
  1. install plugins: `AGGREGATOR/plugins/pom.xml -Pplatform.mac.aarch64 install`
  2. install opensource features: `AGGREGATOR/features/opensource/pom.xml -Pplatform.mac.aarch64 install`
  3. install docs separately: `doc/aggregator/pom.xml install`
  4. package product: `products/pom.xml -Pproduct.org,platform.mac.aarch64 package`
- Recorded diagnostics:
  - `diagnostics/macos-aarch64/plugins-install.log`
  - `diagnostics/macos-aarch64/features-opensource-install.log`
  - `diagnostics/macos-aarch64/doc-aggregator-install.log`
  - `diagnostics/macos-aarch64/products-package-final.log`
- The final product package step succeeded after that scoped install path.

Post-rebuild packaged-app audit:
- Audited artifact:
  - `products/target/products/org.modelio.product/macosx/cocoa/aarch64/Modelio.app`
- Recorded result:
  - `diagnostics/macos-aarch64/final-app-x86_64-audit-after-rebuild.txt`
- Audit result:
  - `HITS 0`

Interpretation after rebuild:
- The latest rebuilt Apple Silicon `Modelio.app` still contains **no shipped `x86_64` files** after disabling the mac Chromium and mac AStyle fragments.
- So the product-level native-payload goal is preserved by the current source changes.

#### Tycho issue resolution progress - 2026-04-16
- `doc/parent/pom.xml` has been reverted from `Tycho 2.7.5` to `Tycho 2.2.0` to match the main reactor.
- Validation completed:
  - `doc/aggregator/pom.xml install` succeeded (`diagnostics/macos-aarch64/doc-aggregator-install-after-tycho-align.exit` = `0`)
  - `AGGREGATOR/pom.xml validate` succeeded (`diagnostics/macos-aarch64/aggregator-validate-after-tycho-align.exit` = `0`)
- Practical interpretation:
  - the specific **"Several versions of tycho plugins are configured"** blocker is now resolved.
  - This restores a single-Tycho main staged reactor without committing to a broader Tycho uplift.

#### Full staged build status after Tycho alignment - 2026-04-16
- `AGGREGATOR/pom.xml -Pplatform.mac.aarch64,product.org package` now succeeds again on `Java 11`.
- Recorded build artifacts:
  - `diagnostics/macos-aarch64/aggregator-package-after-tycho-fix.log`
  - `diagnostics/macos-aarch64/aggregator-package-after-tycho-fix.exit`
- Summary tail captured in:
  - `diagnostics/macos-aarch64/aggregator-package-after-tycho-fix.tail.txt`
- Key outcome:
  - `BUILD SUCCESS`
  - total staged build time recorded: `01:49 min`

Post-AGGREGATOR packaged-app audit:
- Audited artifact:
  - `products/target/products/org.modelio.product/macosx/cocoa/aarch64/Modelio.app`
- Recorded result:
  - `diagnostics/macos-aarch64/final-app-x86_64-audit-after-aggregator-success.txt`
- Audit result:
  - `HITS 0`

Interpretation:
- The full staged reactor is operational again.
- The final Apple Silicon app remains free of shipped `x86_64` payload after the Tycho-alignment fix.

### Phase 2 - Complete mac parity at the current functional level
Scope:
- Replace or remove Intel-only mac fragments in:
  - `features/opensource/org.modelio.platform.feature/feature.xml`
  - `features/opensource/org.modelio.platform.libraries/feature.xml`
- Specifically resolve:
- Restore mac embedded-browser support only with a native `aarch64` implementation after platform modernization.
- Restore mac AStyle support only with a native `aarch64` implementation after platform modernization.
- Verify the final packaged `.app` contains no mac-native `x86_64` payload.

Why before the RCP uplift:
- Otherwise mac-specific regressions will be wrongly blamed on the new Eclipse train.

Primary files:
- `features/opensource/org.modelio.e4.rcp/feature.xml`
- `features/opensource/org.modelio.platform.feature/feature.xml`
- `features/opensource/org.modelio.platform.libraries/feature.xml`
- `products/pom.xml`
- `products/modelio-os.product`

Exit gate:
- Apple Silicon package launches natively and artifact inspection finds no shipped `x86_64` mac binaries.

### Phase 3 - Upgrade build infrastructure before language level
Scope:
- Move Maven/Tycho/toolchain configuration to versions that can support the chosen new Eclipse train.
- Keep repository wiring centralized in the parent POMs; do not duplicate p2 declarations across modules.
- Revalidate `AGGREGATOR/prebuild`, plugin aggregators, feature aggregators, and `products/pom.xml` packaging profiles.

Status today:
- **Bridge uplift completed.**
- The main staged reactor is green on `Tycho 2.7.5` across `pom.xml`, `maven/modelio-parent/pom.xml`, and `doc/parent/pom.xml`.
- The remaining work in this phase is no longer “make `2.7.5` work”; it is the next bounded tooling hop to `5.0.2`.

Tycho-specific recommendation for this phase:
- First try `2.7.5` because the repo already contains one local use of it in `dev-platform/rcp-target/jakarta/jaxb/pom.xml`.
- If `2.7.5` is stable against the unchanged `4.18` target, then try `5.0.2` as a second isolated step.
- Keep `feature.xml` pins and vendored p2 content unchanged during Tycho-only trials.

Why here:
- Newer RCP baselines usually force newer Tycho behavior long before application code must change.

Primary files:
- `pom.xml`
- `maven/modelio-parent/pom.xml`
- `doc/parent/pom.xml`
- `products/pom.xml`
- `dev-platform/rcp-target/jakarta/jaxb/pom.xml`

Exit gate:
- The same source tree builds cleanly with the upgraded build stack while still targeting the pre-uplift runtime.

#### Phase 3 completion update - 2026-04-17
- The full `Tycho 2.7.5` validation ladder is now green on `Java 11`:
  - `AGGREGATOR/prebuild/pom.xml -Pplatform.mac.aarch64 clean install`
  - `AGGREGATOR/plugins/pom.xml -Pplatform.mac.aarch64 clean install`
  - `AGGREGATOR/features/opensource/pom.xml -Pplatform.mac.aarch64 clean install`
  - `AGGREGATOR/doc/pom.xml clean install`
  - `products/pom.xml -Pplatform.mac.aarch64,product.org clean package`
- The one-shot fresh-scratch path is also green:
  - `AGGREGATOR/pom.xml -Pplatform.mac.aarch64,product.org clean package`
- The product-only blocker was resolved without broad runtime-side repinning by:
  - making `AGGREGATOR/prebuild/pom.xml` regenerate the stable `launcher-arm64` and `macos-arm64` overlay repositories alongside `jna`,
  - keeping the launcher bundle requirements explicit in `products/pom.xml`,
  - removing the unsupported `separateEnvironments` configuration from the product module,
  - and dropping the explicit `org.eclipse.equinox.executable` feature entry from `products/modelio-os.product` so the packaged Apple Silicon app stays free of shipped `x86_64` launcher payload.
- Verified postconditions:
  - `products/target/products/org.modelio.product/macosx/cocoa/aarch64/Modelio.app` exists,
  - packaging-time `plutil` and `codesign --verify --deep --strict --verbose=2` checks pass,
  - `diagnostics/macos-aarch64/final-app-x86_64-audit-after-tycho-275.txt` reports `HITS 0`.

#### Exploratory Phase 3 notes from the early Tycho probe

##### Freeze rule for the Tycho trial
During the Tycho-only uplift, do **not** edit these runtime-side files:
- `dev-platform/rcp-target/rcp.target`
- `products/modelio-os.product`
- `features/opensource/**/*.xml`
- vendored p2 content under `dev-platform/rcp-target/rcp-eclipse/**`

The point of Phase 3 is to test the build layer in isolation.

##### Probe A - Trial `Tycho 2.7.5`
Edit exactly these files for a clean future trial of the main build:
- `pom.xml`: change `<tycho-version>2.2.0</tycho-version>` to `<tycho-version>2.7.5</tycho-version>`
- `maven/modelio-parent/pom.xml`: change `<tycho-version>2.2.0</tycho-version>` to `<tycho-version>2.7.5</tycho-version>`

Leave these files unchanged at this step:
- `doc/parent/pom.xml` should stay aligned with the main reactor during any future whole-reactor Tycho trial
- `dev-platform/rcp-target/jakarta/jaxb/pom.xml` already uses `2.7.5`

Validation order for the `2.7.5` trial:

```zsh
mvn -f /Users/david/IdeaProjects/Modelio/AGGREGATOR/prebuild/pom.xml verify
mvn -f /Users/david/IdeaProjects/Modelio/doc/aggregator/pom.xml package
mvn -f /Users/david/IdeaProjects/Modelio/AGGREGATOR/plugins/pom.xml package
mvn -f /Users/david/IdeaProjects/Modelio/AGGREGATOR/features/opensource/pom.xml package
mvn -f /Users/david/IdeaProjects/Modelio/products/pom.xml package -P product.org,platform.mac.aarch64
```

Promotion criteria for `2.7.5`:
- all five builds pass against the unchanged runtime target,
- no new p2 ambiguity appears,
- no `feature.xml` repinning is required,
- no target-definition churn is required,
- the native mac package still materializes successfully.

Observed result from the first real `2.7.5` trial on `2026-04-15`:
- The shell had come back on `Java 21`, and `mvn -f AGGREGATOR/prebuild/pom.xml verify` failed immediately with `Unknown OSGi execution environment: 'JavaSE-21'`.
- Re-running the same prebuild step with `JAVA_HOME=/opt/local/Library/Java/JavaVirtualMachines/openjdk11-temurin/Contents/Home` removed that false blocker, so Phase 3 must be evaluated on `Java 11`, not on the shell default JDK.
- Under `Java 11`, the same prebuild step still fails in `target-platform-validation-plugin:2.7.5` while reading the directory-based target: `org.eclipse.core.runtime.AssertionFailedException: null argument` from `ArtifactKey` creation.
- The crash happens while scanning vendored target content that contains many non-bundle jars and feature jars without OSGi bundle metadata, for example `dev-platform/rcp-target/apache/commons-compress/plugins/commons-compress-1.18-javadoc.jar` and `dev-platform/rcp-target/apache/commons-compress/plugins/commons-compress-1.18-sources.jar`.
- Practical interpretation: `Tycho 2.7.5` is not yet green against the current directory-style vendored target layout, so **do not proceed to `5.0.2` yet**, and do not treat Tycho uplift as the main active stream until earlier cleanup is done.

##### Step 3.2 - Trial `Tycho 5.0.2`
Only after `2.7.5` is green, edit these files:
- `pom.xml`: change `<tycho-version>2.7.5</tycho-version>` to `<tycho-version>5.0.2</tycho-version>`
- `maven/modelio-parent/pom.xml`: change `<tycho-version>2.7.5</tycho-version>` to `<tycho-version>5.0.2</tycho-version>`
- `doc/parent/pom.xml`: change `<tycho-version>2.7.5</tycho-version>` to `<tycho-version>5.0.2</tycho-version>`
- `dev-platform/rcp-target/jakarta/jaxb/pom.xml`: change `<tycho-version>2.7.5</tycho-version>` to `<tycho-version>5.0.2</tycho-version>`

Use the **same** validation ladder again:

```zsh
mvn -f /Users/david/IdeaProjects/Modelio/AGGREGATOR/prebuild/pom.xml verify
mvn -f /Users/david/IdeaProjects/Modelio/doc/aggregator/pom.xml package
mvn -f /Users/david/IdeaProjects/Modelio/AGGREGATOR/plugins/pom.xml package
mvn -f /Users/david/IdeaProjects/Modelio/AGGREGATOR/features/opensource/pom.xml package
mvn -f /Users/david/IdeaProjects/Modelio/products/pom.xml package -P product.org,platform.mac.aarch64
```

Promotion criteria for `5.0.2`:
- the same build ladder stays green,
- the `jakarta/jaxb` module no longer needs to be a Tycho-version exception,
- no compensating changes are required outside those four POMs,
- native mac packaging still succeeds,
- no new resolver drift appears in the unchanged `4.18` target.

Fallback rule:
- if `5.0.2` is noisy or forces runtime-side changes, stop Phase 3 at `2.7.5`, record the blocker, and defer the `5.0.2` jump until the Eclipse train uplift.

##### Current interpretation after the first `2.7.5` probe
Current state to remember:
- the workspace is **not** uniformly on `2.7.5`; the main build remains on `2.2.0`, `doc/parent/pom.xml` has been realigned to `2.2.0`, and `dev-platform/rcp-target/jakarta/jaxb/pom.xml` is the remaining isolated `2.7.5` exception;
- the first gate (`AGGREGATOR/prebuild/pom.xml`) is **not green** for the `2.7.5` probe against the current directory-based target layout;
- always export `JAVA_HOME=/opt/local/Library/Java/JavaVirtualMachines/openjdk11-temurin/Contents/Home` before evaluating Tycho in this phase; a shell-default `Java 21` run produces a misleading failure.

The next recommended action is **not** `5.0.2`, and also **not** “push deeper into Tycho first”.
It is to decide later, in a separate bounded spike, whether the `2.7.5` blocker should be solved by:
- cleaning the directory-based target inputs so validation only sees proper OSGi bundle artifacts,
- converting the problematic raw directories to cleaner p2 repositories,
- or explicitly deferring the Tycho uplift until the larger Eclipse target re-vendoring phase.

##### Updated Phase 3 probe status after target sidecar cleanup - 2026-04-16
- The directory-style target blocker was reduced by moving **11 target-visible non-bundle sidecars** (`-sources.jar` / `-javadoc.jar`) out of active `rcp.target` repository roots and into `dev-platform/rcp-target/_sidecars/`:
  - `apache/commons-compress` (2)
  - `apache/commons-lang` (2)
  - `org.slf4j/slf4j` (3)
  - `modelio-integ/apache/jena` (4)
- Recorded cleanup report:
  - `tmp/tycho-cleanup/tycho-sidecar-cleanup-report.txt`
- Resulting `Tycho 2.7.5` ladder status on `Java 11`:
  - `AGGREGATOR/prebuild/pom.xml verify` = **green**
  - `doc/aggregator/pom.xml package` = **green**
  - `AGGREGATOR/plugins/pom.xml package` = **green**
  - `AGGREGATOR/features/opensource/pom.xml package` = **green**
  - `products/pom.xml -Pproduct.org,platform.mac.aarch64 package` = **still failing**

Remaining product-only blocker under `Tycho 2.7.5`:
- The failure is now isolated to `tycho-p2-director:materialize-products` for `macosx/cocoa/aarch64`.
- Exact unresolved IU chain:
  - `toolingorg.eclipse.equinox.launcher.cocoa.macosx.aarch64 1.2.200.v20210527-0259`
  - missing required bundle `org.eclipse.equinox.launcher.cocoa.macosx.aarch64 1.2.200.v20210527-0259`
- This is **not** the old target-validation crash anymore; it is a later product-publication/materialization issue.

What has already been tried against this product blocker:
- `features/opensource/org.modelio.e4.rcp/feature.xml` was aligned from the generic Apple Silicon launcher fragment id to the explicit `org.eclipse.equinox.launcher.cocoa.macosx.aarch64` id.
- The vendored executable feature content under `dev-platform/rcp-target/rcp-eclipse/eclipse/features/org.eclipse.equinox.executable_3.8.1000.v20200915-1508/` was resynced into the shipped feature jar, including:
  - the Apple Silicon launcher root in `build.properties`
  - the explicit Apple Silicon launcher fragment id in `feature.xml`
- `products/modelio-os.product` was also tried with an explicit `org.eclipse.equinox.executable` feature inclusion.
- Despite that, `products/pom.xml` packaging still fails with the same missing launcher-bundle requirement.

Current interpretation after the updated probe:
- `Tycho 2.7.5` is now **mostly green for this repo** on the unchanged runtime target: prebuild, docs, plugins, and features all pass.
- The remaining blocker is specifically the **product materialization path for the Apple Silicon launcher**, not general target resolution.
- Strong hint from the current logs:
  - `products/pom.xml` on `Tycho 2.7.5` warns that `separateEnvironments` is an unknown parameter for `target-platform-configuration` in this module.
  - The staged `org.eclipse.equinox.executable` feature now contains the `aarch64` mac root and explicit launcher fragment id, yet the product-side director inputs still do not expose the required launcher bundle IU/artifact during materialization.
  - The `launcher-arm64` overlay repository itself does publish both launcher IUs (`org.eclipse.equinox.launcher.cocoa.macosx` and `org.eclipse.equinox.launcher.cocoa.macosx.aarch64`), so the remaining failure is no longer about missing vendored source content; it is about how the product materialization path on `Tycho 2.7.5` surfaces that launcher into the director input repositories.

Recommended next bounded Phase 3 task:
- Keep `2.7.5` as the active bridge target for now.
- Investigate **only** the product-publication side:
  - how `products/pom.xml` should express environment separation on `Tycho 2.7.5`, and
  - how the Apple Silicon launcher bundle/artifact is supposed to be surfaced to `materialize-products`.
- Do **not** treat this as evidence for a broader rollback of the now-green prebuild/plugins/features steps.

Interpretation rule from this point:
- if `2.7.5` can later be made green **without** broad runtime-side churn, re-run the full ladder and only then consider **Step 3.2 - Trial `Tycho 5.0.2`**,
- if fixing `2.7.5` requires widespread target cleanup, feature repinning, or re-vendoring, treat that as evidence to postpone the Tycho uplift rather than smuggling a platform migration into Phase 3.

### Phase 4 - Normalize Java baselines, but only to a safe stepping stone
Scope:
- First eliminate remaining `JavaSE-1.8` manifests and normalize everything to `JavaSE-11` or the selected intermediate baseline.
- Then move the codebase to `Java 17` or `Java 21` together with manifest, compiler, and packaging updates.
- Audit reflective access, JAXB/Jakarta usage, and any removed JDK behavior during this hop.

Status today:
- **First manifest-normalization wave completed.**
- Updated from `JavaSE-1.8` to `JavaSE-11` in these source bundles:
  - `modelio/core/core.utils/META-INF/MANIFEST.MF`
  - `modelio/core/core.kernel/META-INF/MANIFEST.MF`
  - `modelio/core/core.session/META-INF/MANIFEST.MF`
  - `modelio/core/core.metamodel.api/META-INF/MANIFEST.MF`
  - `modelio/core/core.metamodel.impl/META-INF/MANIFEST.MF`
  - `modelio/core/core.store.exml/META-INF/MANIFEST.MF`
  - `modelio/core/core.project.data/META-INF/MANIFEST.MF`
  - `modelio/core/core.project/META-INF/MANIFEST.MF`
  - `modelio/core/version/META-INF/MANIFEST.MF`
  - `modelio/bpmn/bpmn.metamodel.api/META-INF/MANIFEST.MF`
  - `modelio/bpmn/bpmn.metamodel.implementation/META-INF/MANIFEST.MF`
- Validation completed:
  - `AGGREGATOR/plugins/core/pom.xml -Pplatform.mac.aarch64 verify` succeeded (`diagnostics/macos-aarch64/plugins-core-bree-java11.exit` = `0`)
  - `AGGREGATOR/plugins/bpmn/pom.xml -Pplatform.mac.aarch64 verify` succeeded (`diagnostics/macos-aarch64/plugins-bpmn-bree-java11.exit` = `0`)
- Current repo signal:
  - a source-manifest search for `Bundle-RequiredExecutionEnvironment: JavaSE-1.8` under `modelio/**/META-INF/MANIFEST.MF` now returns no results.

#### Java 8 assumption scan after BREE normalization - 2026-04-16
Runtime-significant findings:
- Remaining `build.properties` still pinned to Java 8 (`javacSource = 1.8`, `javacTarget = 1.8`) were found in these source bundles:
  - `modelio/core/core.kernel/build.properties`
  - `modelio/core/core.session/build.properties`
  - `modelio/core/core.metamodel.api/build.properties`
  - `modelio/core/core.metamodel.impl/build.properties`
  - `modelio/core/core.store.exml/build.properties`
  - `modelio/core/core.project.data/build.properties`
  - `modelio/core/core.project/build.properties`
  - `modelio/core/version/build.properties`
  - `modelio/bpmn/bpmn.metamodel.api/build.properties`
  - `modelio/bpmn/bpmn.metamodel.implementation/build.properties`
- These now lag behind the normalized `JavaSE-11` manifest declarations and are the main remaining Java-baseline inconsistency inside owned runtime/source bundles.

Tooling-only / lower-priority findings:
- `doc/parent/pom.xml` still uses `<maven.compiler.source>1.8</maven.compiler.source>` and `<maven.compiler.target>1.8</maven.compiler.target>`; this currently affects the doc branch, not the main runtime.
- `modelio/core/core.utils/lib/build_deps/pom.xml` still contains commented `1.8` compiler settings inside a disabled block; this is stale local helper-build history, not an active main-reactor input.

Interpretation:
- The manifest normalization is complete, but Java-baseline normalization is not fully finished until the remaining runtime `build.properties` values are aligned with Java 11.
- Those `build.properties` pins are a better next Java-cleanup target than changing the doc branch compiler level, because they affect owned runtime bundles.

#### Bounded Tycho 2.7.5 retry preparation - ready state as of 2026-04-16
Why the retry is now cleaner than before:
- the main staged reactor is green again on `Tycho 2.2.0`;
- Apple Silicon packaging is green;
- final packaged `Modelio.app` audits clean (`HITS 0` for shipped `x86_64` payload);
- source BREE declarations are normalized to `JavaSE-11`.

What still makes the retry noisy if left unchanged:
- the ten runtime `build.properties` files listed above still advertise Java 8 compilation assumptions.

Recommendation before any future retry:
- either normalize those ten runtime `build.properties` files to `11` first,
- or, if running the Tycho retry sooner, record them as known background noise so they are not confused with a true Tycho/target-layout failure.

Exact future retry ladder for `Tycho 2.7.5`:
1. change `pom.xml` and `maven/modelio-parent/pom.xml` from `2.2.0` to `2.7.5`
2. keep runtime-side inputs fixed (`rcp.target`, `feature.xml`, vendored p2 content, `products/modelio-os.product`)
3. run on Java 11 only:
   - `AGGREGATOR/prebuild/pom.xml verify`
   - `doc/aggregator/pom.xml package`
   - `AGGREGATOR/plugins/pom.xml package`
   - `AGGREGATOR/features/opensource/pom.xml package`
   - `products/pom.xml package -Pproduct.org,platform.mac.aarch64`
4. stop at the first failure and classify it:
   - `prebuild`/target validation failure = build-layer or target-layout problem
   - plugin compile/package failure = module/build problem
   - feature/product resolution failure after green plugins = packaging-layer problem

Recommended target for this phase:
- `Java 21`, unless an upstream compatibility check proves `Java 25` is already safe in the chosen Tycho/RCP combination.

Primary files:
- `pom.xml`
- `maven/modelio-parent/pom.xml`
- affected `META-INF/MANIFEST.MF` files with `Bundle-RequiredExecutionEnvironment`
- `products/modelio-os.product`

Exit gate:
- Full product build and smoke launch succeed on the new LTS Java without ad-hoc runtime flags.

### Phase 5 - Re-vendor the full Eclipse/RCP stack to 2026-03
Scope:
- Refresh the vendored p2 content under `dev-platform/rcp-target/rcp-eclipse/**` as a coherent train.
- Re-resolve pinned versions in:
  - `features/opensource/org.modelio.e4.rcp/feature.xml`
  - `features/opensource/org.modelio.rcp/feature.xml`
  - `products/modelio-os.product`
- Remove temporary overlays that are no longer needed once the full platform is modernized.

Important rule:
- This is not a launcher swap. The whole Eclipse application stack must move together.

Primary files:
- `dev-platform/rcp-target/rcp-eclipse/**`
- `dev-platform/rcp-target/rcp.target`
- `features/opensource/org.modelio.e4.rcp/feature.xml`
- `features/opensource/org.modelio.rcp/feature.xml`
- `products/modelio-os.product`

Exit gate:
- The full product packages and launches on the new vendored RCP stack across the supported platforms.

### Phase 6 - Reassess Java 25 as an optional final hop
Scope:
- Only now test the highest Java level.
- Treat this as a separate change with its own compiler/runtime verification and packaging run.

Decision rule:
- If `Java 25` causes unresolved Tycho, PDE, or runtime issues, stop at the latest stable LTS baseline and ship that.

Exit gate:
- `Java 25` is adopted only if build, packaging, and runtime are all cleaner than the LTS alternative.

## Order I would insist on
1. Reproducible current baseline.
2. Coherent target platform.
3. Native mac parity.
4. Build tooling uplift.
5. Java LTS uplift.
6. Full RCP `2026-03` uplift.
7. Optional `Java 25` evaluation.

## Operational verification ladder

Use the same smallest-scope-first validation pattern after each phase change:

```zsh
mvn -f /Users/david/IdeaProjects/Modelio/AGGREGATOR/prebuild/pom.xml verify
mvn -f /Users/david/IdeaProjects/Modelio/AGGREGATOR/plugins/pom.xml package
mvn -f /Users/david/IdeaProjects/Modelio/AGGREGATOR/features/opensource/pom.xml package
mvn -f /Users/david/IdeaProjects/Modelio/products/pom.xml package -P product.org,platform.mac.aarch64
```

For Tycho-only trials, keep the runtime target fixed and compare the same build ladder before and after the Tycho bump.

For native mac correctness, add an artifact audit after packaging:

```zsh
find /Users/david/IdeaProjects/Modelio/products/target/products/org.modelio.product/macosx/cocoa/aarch64/Modelio.app -type f -print0 | xargs -0 file | grep 'x86_64'
```

Expected result for a correct native package: no output.

## What I would explicitly avoid
- No big-bang migration of Tycho + RCP + Java + mac-native fragments in one shot.
- No claim that `2026-03` is “done” if the app still ships `x86_64` browser or AStyle fragments on macOS.
- No `Java 25` commitment until the codebase is already green on the modernized RCP stack.
- No keeping long-term hand-maintained version skew inside `feature.xml` unless a specific override is documented and tested.
- No direct `Tycho 2.2.0 -> 5.0.2` jump unless a short spike proves it is genuinely low-risk.

## Friend review - skeptical critique
A cautious reviewer would push back on one point: aiming for both `RCP 2026-03` and `Java 25` as a single declared destination is probably too ambitious for a Tycho/OSGi product with vendored p2 repositories and custom native fragments. The safer interpretation of “most current possible” is:
- **commit to `RCP 2026-03`,**
- **stabilize on `Java 21` first,**
- **treat `Java 25` as a bonus hop only if it is boring.**

That reviewer would also insist that native mac cleanup is not a side quest. In this repo, it is part of platform correctness because the product still carries explicit mac-native fragments in feature composition.

