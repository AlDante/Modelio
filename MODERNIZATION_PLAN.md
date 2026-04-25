# Modernisation plan

## Status of this document

This document now has a single active execution plan: **Slices A–D** below.

Earlier roadmap material from previous iterations is retained only where it helps explain why the repository ended up in its current state. Any such material should be treated as **historical context only**, not as the plan of record.

## Current mixed pieces vs the clean target

The repository is now much healthier than the starting point, but it is still a **deliberate hybrid**: some parts already come from the modern upstream stack, while other parts are still carried forward from older or locally-preserved inputs to keep the build and product assembly moving.

The clean end-state is a repository that builds and ships from **one internally consistent vendored train**, with Apple Silicon treated as a first-class supported platform rather than a compatibility add-on.

| Area | Current mixed state | Clean target |
|---|---|---|
| Target platform contents | Combination of modern upstream bundles plus older locally-carried/vendored pieces used to fill resolution gaps | One pinned, mirrored, internally consistent vendored release train with no silent fallbacks |
| Feature composition | Some features/products still rely on a mixture of old and new inputs | All features resolved only from the chosen vendored train |
| Product assembly | Product definitions still tolerate historical carry-overs to keep packaging working | Products assembled only from the clean vendored stack |
| macOS runtime stack | Apple Silicon support works in places, but some launcher/runtime assumptions still reflect older Intel-era packaging | Fully clean macOS/aarch64 product stack: launcher, SWT fragments, runtime, metadata, validation |
| Provenance/versioning | Some artefacts are effectively “known-good carried pieces” rather than part of one aligned train | Every shipped IU traceable to the chosen mirrored upstream baseline or an explicit in-repo patch fork |
| Validation | Fresh scratch validation is mostly green, but the full ladder still needs to be completed and locked in | Repeatable full scratch validation with app integrity/artefact checks as standard acceptance gates |

## How much work remains?

The modernisation is **substantially advanced but not yet complete**.

What is already true:
- the scratch-repo build can progress on the modernised path,
- `prebuild` is green from a fresh repo,
- the repo is no longer blocked on the original legacy-only stack,
- Apple Silicon enablement is no longer theoretical.

What is not yet true:
- the repository does **not** yet represent one fully clean, internally consistent vendored train,
- all remaining historical carry-overs have **not** yet been eliminated,
- the full validation ladder and final product integrity checks are **not** yet all signed off.

### Remaining effort estimate

Assuming no major new upstream incompatibility is uncovered, the remaining work is approximately:

| Slice | Scope | Rough effort |
|---|---|---|
| Slice A | Top up missing upstream bundles into the vendored train and freeze the resolved baseline | 3–5 days |
| Slice B | Recut features/products to consume only the clean vendored train and remove historical fallbacks | 3–6 days |
| Slice C | Finish the clean Apple Silicon product/runtime stack and packaging integrity work | 4–7 days |
| Slice D | Complete validation, lock CI gates, and retire the hybrid path | 2–4 days |

**Overall remaining work:** roughly **2–4 focused weeks** of engineering/validation, depending on how many additional missing IUs are exposed during Slice A and whether product packaging reveals any macOS-specific edge cases.

## Active plan of record

The following slices are the active plan we are working to going forward. These supersede earlier roadmap variants.

# Active execution plan: Slices A–D

## Slice A — Complete the vendored upstream train

### Objective
Eliminate the current “hybrid” target platform by topping up the missing upstream bundles/features that are still being carried indirectly, historically, or opportunistically.

### Why this is first
Until the vendored repository contains the full set of upstream IUs actually needed by our features/products, the build can remain green for the wrong reasons:
- accidental resolution against historical carried bundles,
- transitive availability from non-authoritative repos,
- inconsistent versions across platform layers,
- Apple Silicon artefacts assembled from a mixed baseline.

### What needs topping up

The current gap is not “everything”; it is the set of upstream bundle families that are still missing from the vendored train but are required by the modernised build/product stack.

The top-up work should explicitly check and mirror the following bundle families as needed by the current feature/product graph:

#### 1. Equinox runtime/service layer
These are often the first source of hidden hybridisation because older carried copies can satisfy them quietly:
- `org.eclipse.osgi`
- `org.eclipse.equinox.common`
- `org.eclipse.equinox.registry`
- `org.eclipse.equinox.preferences`
- `org.eclipse.equinox.app`
- `org.eclipse.equinox.ds`
- `org.eclipse.equinox.event`
- `org.eclipse.equinox.cm`
- `org.eclipse.equinox.metatype`
- `org.eclipse.equinox.console` (if still used)
- `org.eclipse.equinox.launcher`
- macOS launcher fragments, especially:
  - `org.eclipse.equinox.launcher.cocoa.macosx.x86_64`
  - `org.eclipse.equinox.launcher.cocoa.macosx.aarch64`

#### 2. Core Eclipse runtime bundles
These frequently appear as transitive gaps when features are recut against a cleaner baseline:
- `org.eclipse.core.runtime`
- `org.eclipse.core.jobs`
- `org.eclipse.core.contenttype`
- `org.eclipse.core.filesystem`
- `org.eclipse.core.resources`
- `org.eclipse.core.expressions`
- `org.eclipse.core.commands`
- `org.eclipse.core.databinding*` (if still consumed)

#### 3. UI / workbench / e4 compatibility layer
If the product still depends on the 4.x workbench stack, these need to come from the same chosen train:
- `org.eclipse.swt`
- `org.eclipse.swt.cocoa.macosx.aarch64`
- `org.eclipse.jface`
- `org.eclipse.ui`
- `org.eclipse.ui.workbench`
- `org.eclipse.ui.ide` (if applicable)
- `org.eclipse.e4.core.contexts`
- `org.eclipse.e4.core.di`
- `org.eclipse.e4.core.commands`
- `org.eclipse.e4.ui.services`
- `org.eclipse.e4.ui.workbench`
- `org.eclipse.e4.ui.workbench.swt`
- `org.eclipse.e4.ui.css.core`
- `org.eclipse.e4.ui.css.swt`

#### 4. p2 / install / update stack
If products or tests rely on provisioning/update flows, these must also be aligned rather than inherited ad hoc:
- `org.eclipse.equinox.p2.core`
- `org.eclipse.equinox.p2.engine`
- `org.eclipse.equinox.p2.director`
- `org.eclipse.equinox.p2.metadata`
- `org.eclipse.equinox.p2.repository`
- `org.eclipse.equinox.p2.artifact.repository`
- `org.eclipse.equinox.p2.metadata.repository`
- `org.eclipse.equinox.p2.garbagecollector`
- relevant p2 UI bundles if they are part of the shipped product

#### 5. Third-party/Orbit bundles required by the above
We should not guess these. We should mirror the exact ones exposed by the resolved dependency graph, for example service-component and annotation/runtime support bundles where required by the selected train.

### How Slice A will happen

#### Step A1 — Freeze the chosen upstream baseline
Pick the exact upstream train/repositories that define the clean target baseline for this repo.

That chosen baseline must become the sole authoritative source for:
- platform bundles,
- launcher fragments,
- SWT/native fragments,
- p2 stack,
- any shipped runtime pieces that are meant to come from upstream.

#### Step A2 — Generate the missing-IU delta
Run target resolution and feature/product assembly against the chosen baseline and produce the explicit delta of missing installable units:
- what the build currently needs,
- what is already mirrored,
- what is still being satisfied only by historical carry-overs or incidental availability.

This delta should be recorded in source control as a reviewable allow-list or manifest, not left implicit.

#### Step A3 — Mirror the missing upstream artefacts into the vendored repo
Top up the vendored repository by mirroring the missing IUs from the chosen upstream source into the in-repo/vendor-controlled p2 repository.

This should include:
- binary bundles,
- associated source bundles where we normally keep them,
- platform-specific fragments needed for macOS/aarch64,
- any required feature IUs used directly by our build/products.

#### Step A4 — Re-resolve using only the vendored repo
After the mirror is topped up, rerun resolution/builds with non-vendored fallback repos removed or disabled so that accidental hybrid resolution cannot hide remaining gaps.

#### Step A5 — Freeze and document the result
Record:
- the exact upstream baseline,
- the exact mirrored IU set,
- why each non-upstream carried artefact still exists, if any remain.

### Definition of done for Slice A
Slice A is complete when:
- the vendored repository contains the full upstream IU set needed by the current feature/product graph,
- resolution succeeds without depending on historical fallback pieces,
- macOS/aarch64 launcher/SWT/runtime artefacts are present from the same chosen baseline,
- the remaining “mixed” area is visibly smaller and explicitly documented.

---

## Slice B — Recut features and products onto the clean train

### Objective
Move feature definitions, product definitions, and aggregation metadata fully onto the topped-up vendored train so that the repository stops depending on historical compatibility allowances.

### Work
- Update features to reference the clean vendored units only.
- Remove or isolate legacy inclusions that were kept only to bridge earlier migration gaps.
- Align product definitions with the chosen train versions.
- Remove obsolete repository references and compatibility scaffolding.
- Ensure generated p2 metadata reflects only the clean source set.

### Definition of done
- `AGGREGATOR/features/opensource`, `AGGREGATOR/doc`, and `AGGREGATOR/products` resolve against the vendored train without historical fallbacks.
- Product definitions no longer need mixed old/new inputs to assemble.
- Any remaining legacy inclusion is explicitly justified as temporary and tracked.

---

## Slice C — Finish the clean Apple Silicon stack

### Objective
Make macOS Apple Silicon a first-class, internally consistent product/runtime path rather than a “works with exceptions” path.

### Work
- Ensure the product uses the correct `cocoa.macosx.aarch64` launcher/SWT fragments from the chosen train.
- Align the bundled runtime/JRE strategy for macOS/aarch64.
- Verify product metadata (`Info.plist`, launcher naming, app layout) is consistent.
- Validate artefact integrity for app bundles, launchers, native fragments, and packaged runtime.
- Remove any remaining Intel-era assumptions that survive only because the repo is still hybrid.

### Definition of done
- Built macOS products are natively Apple Silicon clean.
- No Intel-era compatibility artefacts are required for the standard path.
- App integrity/artefact checks pass on the produced deliverables.

---

## Slice D — Lock validation, CI, and retirement of the hybrid path

### Objective
Turn the now-cleaned build path into the normal path and demote the mixed/historical path to archival relevance only.

### Work
- Complete fresh scratch validation across:
  - `AGGREGATOR/prebuild`
  - `AGGREGATOR/plugins`
  - `AGGREGATOR/features/opensource`
  - `AGGREGATOR/doc`
  - `AGGREGATOR/products`
- Run final app integrity and artefact checks.
- Add CI gates/assertions so the build fails if:
  - non-vendored repos are pulled in unexpectedly,
  - wrong-arch native fragments appear,
  - historical fallback pieces re-enter silently.
- Mark any pre-slices roadmap material as historical.

### Definition of done
- Full scratch-repo validation is green.
- Product and artefact checks are green.
- CI protects the repository from regressing back into a mixed stack.
- This document’s active plan is complete.

---

# Historical material

Any roadmap sections below this point are retained only for historical relevance, auditability, or context. They are **not** the active execution plan.

> **Historical note:** The sections below describe previous planning iterations. They are preserved for context only and should not be treated as the current delivery plan. The active plan of record is the Slices A–D section above.

## [Historical] Status snapshot as of 2026-04-18
- The immediate recovery goal is already achieved: the project builds and a signed Apple Silicon `Modelio.app` can be produced and launched.
- The modernization plan is still correctness-first. The intended order remains: stabilize the current platform composition first, then clean up remaining mac-native skew, then revisit Tycho, then move Java, then re-vendor Eclipse/RCP.
- The bounded `Tycho 5.0.2` probe is now green on the current vendored `4.18` runtime target.
- That does **not** change the broader sequencing: the next modernization hop after this tool uplift should be Java-baseline cleanup, then the larger RCP re-vendoring.
- Current verified Tycho state in the workspace:
  - `pom.xml` = `5.0.2`
  - `maven/modelio-parent/pom.xml` = `5.0.2`
  - `doc/parent/pom.xml` = `5.0.2`
  - `dev-platform/rcp-target/jakarta/jaxb/pom.xml` = `5.0.2`

## [Historical] Build-orchestration note from 2026-04-18
- The temporary mixed-Tycho reactor blocker is gone because the main build, the shared modelio parent, and the docs parent are now all aligned on `Tycho 5.0.2`.
- `AGGREGATOR/prebuild/pom.xml` now refreshes the stable Apple Silicon overlay repositories (`swt`, `launcher-arm64`, `macos-arm64`, `jna`) before validating `dev-platform/rcp-target/rcp.target`.
- The product-side `separateEnvironments` warning was removed from `products/pom.xml`, and the packaged macOS app no longer needs an explicit `org.eclipse.equinox.executable` feature entry to materialize successfully.
- `Tycho 5.0.2` must be run on `Java 21`; attempting to run Maven on `Java 11` now fails before project resolution with `P2ArtifactRepositoryLayout has been compiled by a more recent version of the Java Runtime`.
- This is a build-tool runtime requirement first, and the supported macOS `aarch64` product path now also validates with Java 21 launcher metadata and no active `openjdk-jre11` target wiring.

## [Historical] Status update as of 2026-04-17
- The documented macOS `aarch64` scratch-build workflow is now verified through `products`, not just through `plugins` and `features`.
- A clean staged run using a dedicated scratch local repository now succeeds in this order: `prebuild -> plugins -> features -> doc -> products`.
- The `products` stage required an explicit fix in `products/pom.xml` so the `platform.mac.aarch64` profile requests the Equinox mac launcher bundles during product materialization.
- `MACOS_AARCH64_BUILD_PROCESS.md` now records:
  - the validated IntelliJ/Maven scratch-build targets,
  - the required stage order,
  - the shared scratch local repository flow,
  - and the final launchable output path `products/target/products/org.modelio.product/macosx/cocoa/aarch64/Modelio.app`.
- This means the current `Tycho 5.0.2` / `Java 21` build contract is reproducible from scratch for the Apple Silicon product path, now without active `openjdk-jre11` target wiring.

### [Historical] Immediate next modernisation step
- **Do not broaden the work into RCP re-vendoring yet.**
- The repo-owned runtime metadata cleanup, runtime-baseline audit, Java 21 runtime spike, and `openjdk-jre11` wiring cleanup are now complete for the supported macOS `aarch64` path.
- The next bounded step can now broaden back out to platform modernisation work rather than more Java-baseline housekeeping.

### [Historical] Progress update on 2026-04-17
- The headless target-definition cleanup has now started and its first pass is complete.
- `dev-platform/rcp-target/rcp.target` and `dev-platform/rcp-target/rcp_debug.target` were changed from `${project_loc:/...}` paths to workspace-relative paths.
- The stale missing `test-resources/files` target entry was removed from both target definitions.
- Revalidation of `AGGREGATOR/prebuild/pom.xml` on `platform.mac.aarch64` is green, and the previous `${project_loc:/rcp-target}`, `${project_loc:/pack-resources}`, `${project_loc:/test-resources}`, and `target resoloution might be incomplete` warnings are no longer present in the new log `diagnostics/macos-aarch64/prebuild-verify-after-target-path-cleanup.log`.
- The Apple Silicon JNA overlay can now be generated headlessly from Maven alone against a fresh local repository; the old external JNA source checkout is no longer required to create the overlay.
- The build now uses a stable repo-owned JNA p2 path at `dev-platform/rcp-target/rcp-eclipse/jna/repository/`, and the JNA generator now refreshes that stable path while deleting the transient staged `target/repository` output before the build completes.
- `AGGREGATOR/prebuild/pom.xml` now includes the JNA overlay generator module so the overlay can be refreshed inside the staged build flow, while the stable checked-in repository remains available before reactor resolution starts.
- The target-platform contract is now normalized across `dev-platform/rcp-target/rcp.target`, `dev-platform/rcp-target/rcp_debug.target`, `pom.xml`, `maven/modelio-parent/pom.xml`, and IntelliJ repository metadata so the same Apple Silicon overlay set is described consistently in every build entrypoint.
- This means the original immediate target-platform hardening goal is substantially complete: the headless path warnings are gone and the external/manual JNA prerequisite has been removed from the validated staged workflow.

### [Historical] Remaining follow-up after target-platform hardening
- The one-shot `AGGREGATOR/pom.xml` scratch path has now also been revalidated after the SWT-resolution investigation.
- Root cause of the transient `org.modelio.platform.rcp` compile failure: fresh scratch resolution was mirroring the `org.eclipse.swt` base bundle without also mirroring the Apple Silicon SWT fragment, and the base SWT jar is only a stub for compilation purposes.
- The fix was to explicitly require `org.eclipse.swt.cocoa.macosx.aarch64` in the root `platform.mac.aarch64` profile.
- This means both documented workflows are now green again:
  1. the correctness-first staged `prebuild -> plugins -> features -> doc -> products` path,
  2. the one-shot `AGGREGATOR/pom.xml -Pplatform.mac.aarch64,product.org clean package` path from a fresh local Maven repository.
- Only after this should the plan broaden again toward lower-priority build-hygiene cleanup or renewed Tycho bridge work.

### [Historical] Why this was the next step
- The major build-breaker work is now done: scratch `products` packaging can complete and materialize the final `.app`.
- The highest remaining reproducibility risks are now in the target-platform contract itself, not in plugin/feature/product reactor wiring.
- Until the target platform is self-contained and warning-clean, further Tycho uplift or broader platform modernization will keep producing noisy and harder-to-localize failures.

### [Historical] Deferred until after target-platform cleanup
- central encoding cleanup,
- missing `.settings/org.eclipse.jdt.core.prefs` cleanup,
- further Tycho bridge work beyond the already-proved bounded experiments,
- broader Java baseline movement.

## [Historical] Current baseline verified from the repo
- Build/tooling is now centered on `Tycho 5.0.2` and `Java 21` in `pom.xml`, `maven/modelio-parent/pom.xml`, and `doc/parent/pom.xml`.
- The vendored Eclipse platform in `dev-platform/rcp-target/rcp-eclipse/eclipse` is still the `2020-12` line (`org.eclipse.platform_4.18.0.v20201202-1800`).
- `features/opensource/org.modelio.e4.rcp/feature.xml` and `features/opensource/org.modelio.rcp/feature.xml` hard-pin many 2020-era bundle versions.
- The repo is currently in a hybrid state: older platform/equinox bundles, but newer SWT overlays (`3.120.0`) and ARM-specific mac fragments staged separately.
- macOS is still mid-modernization, but the known Intel-only feature-composition exceptions have now been intentionally removed rather than shipped; mac Chromium and mac AStyle are both disabled pending native `aarch64` replacements.
- Bundle execution-environment baselines in owned source manifests are now normalized to `JavaSE-21` for the supported macOS `aarch64` path; the repo no longer has owned source `JavaSE-1.8` BREE declarations under `modelio/**/META-INF/MANIFEST.MF`.
- Remaining Java-era assumptions still exist mostly as historical or unsupported-path metadata: the repo-owned runtime `.classpath` JRE containers and docs parent compiler metadata are aligned, the macOS launcher metadata is now on Java 21, and active `openjdk-jre11` target wiring has been removed from the supported macOS path.

## [Historical] Recommended destination
- **Primary platform target:** a coherent vendored Eclipse/RCP `2026-03` stack, not a launcher-only uplift.
- **Primary Java target:** stabilize first on a modern LTS baseline (`Java 21`) for build + runtime.
- **Stretch Java target:** evaluate `Java 25` only after the `2026-03` migration is green end-to-end.
- **macOS target:** full native Apple Silicon product with no shipped `x86_64` mac-native code.

## [Historical] Why not jump straight to Java 25?
Because this repo is constrained by four compatibility layers at once: Tycho, Eclipse RCP, vendored p2 content, and OSGi bundle execution environments. Jumping straight from the current `Java 11` / `RCP 4.18` baseline to `Java 25` would blur together toolchain failures, API breakage, reflective-access issues, and product packaging regressions.

## [Historical] Tycho upgrade evaluation
- The main build, including the docs branch parent, is now green on `Tycho 5.0.2` in `pom.xml`, `maven/modelio-parent/pom.xml`, and `doc/parent/pom.xml`.
- The build-tool objective for this phase is therefore met: the same source tree now builds cleanly on the newer Tycho line while still targeting the unchanged vendored `4.18` runtime.
- The next build-layer step should not be another Tycho experiment; it should be to keep `5.0.2` stable while the remaining Java-baseline cleanup is completed.

### [Historical] Recommendation
- **Do not combine the newly green `5.0.2` baseline with runtime-side modernization.**
- **Do keep the vendored `4.18` runtime fixed while the remaining Java-baseline cleanup is finished.**
- Use a staged path:
  1. keep `5.0.2` while freezing the current build contract and removing obvious remaining Java-baseline skew,
  2. validate a Java 21 runtime uplift only after those Java 8 build-metadata remnants are gone,
  3. only then move to `RCP 2026-03`, after Tycho is already boring.

### [Historical] Why we ran a Tycho probe anyway
- The early `2.7.5` trial was a bounded compatibility probe to answer one question: “is the build-tool uplift likely to be a cheap isolated step?”
- The answer appears to be **no, not yet**. Tycho hit target-validation problems in the current vendored target layout before any useful product-level signal was obtained.
- That result supports the original sequencing rather than contradicting it: the repo still needs more platform cleanup before Tycho becomes a low-noise change.

### [Historical] Why this timing was safer
- Right now the repo still mixes old platform bundles with newer SWT/native overlays; an immediate Tycho jump would make it unclear whether a failure came from the build tool, the target platform, or native fragment composition.
- A Tycho-only spike against the unchanged `4.18` target gives a much cleaner signal.
- By the time the Eclipse train is re-vendored, the build layer should already be stable.

### [Historical] Go / no-go rule for Tycho
- **Go** if prebuild, plugin aggregation, feature aggregation, and product packaging all stay green with the same vendored target content.
- **No-go** if the Tycho change forces broad `feature.xml` repinning, introduces new p2 ambiguity, or breaks the native mac package before any platform upgrade has begun.

## [Historical] Migration sequence

### [Historical] Phase 0 - Freeze and measure the current contract
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

### [Historical] Phase 1 - Remove baseline skew before any major uplift
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

#### [Historical] Concrete remaining checklist for Phase 1
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

#### [Historical] Phase 1 Step 1 findings - mixed-train inventory completed on 2026-04-15
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

#### [Historical] Phase 1 Step 2 findings - baseline normalization target chosen on 2026-04-15
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

#### [Historical] Phase 1 Step 3 findings - `org.modelio.e4.rcp` audit completed on 2026-04-15
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

#### [Historical] Phase 1 Step 4 findings - mac Chromium browser disabled on 2026-04-15
- `org.eclipse.swt.browser.chromium.cocoa.macosx.x86_64` is **not required for basic Modelio startup**.
- The codebase uses generic SWT `Browser` widgets, but no Chromium-specific selection or `SWT.CHROMIUM` usage was found.
- Startup-adjacent browser usage exists in the first-launch `WelcomeView`, but that code still relies on the generic SWT browser API rather than on the Chromium fragment specifically.
- To eliminate non-native exceptions on Apple Silicon, the Intel-only mac Chromium fragment has been removed from `features/opensource/org.modelio.e4.rcp/feature.xml`.
- Decision: **disable mac Chromium integration for now rather than ship Intel-only browser native code**.

Restoration note for later modernization:
- mac embedded-browser support on macOS should be restored only when a coherent native `aarch64` browser-capable solution exists in the modernized platform stack.
- That restoration belongs after the broader RCP modernization work, not as a one-off exception in the current hybrid baseline.
- If browser-backed UI on macOS shows regressions before then, prefer targeted fallback behavior (for example, welcome/help degradation) over re-introducing `x86_64` browser native code.

#### [Historical] Phase 2 Step 1 findings - mac AStyle fragment disabled on 2026-04-15
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

#### [Historical] Phase 2 Step 2 findings - packaged app native audit completed on 2026-04-15
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

### [Historical] Phase 2 - Complete mac parity at the current functional level
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

### [Historical] Phase 3 - Upgrade build infrastructure before language level
Scope:
- Move Maven/Tycho/toolchain configuration to versions that can support the chosen new Eclipse train.
- Keep repository wiring centralized in the parent POMs; do not duplicate p2 declarations across modules.
- Revalidate `AGGREGATOR/prebuild`, plugin aggregators, feature aggregators, and `products/pom.xml` packaging profiles.

Status today:
- **Tooling uplift completed.**
- The main staged reactor is green on `Tycho 5.0.2` across `pom.xml`, `maven/modelio-parent/pom.xml`, `doc/parent/pom.xml`, and `dev-platform/rcp-target/jakarta/jaxb/pom.xml`.
- The remaining work in this phase is no longer “make `5.0.2` work”; it is to preserve this now-green baseline while later phases move Java and the vendored RCP stack.

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

#### [Historical] Phase 3 completion update - 2026-04-17
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

#### [Historical] Phase 3 completion update - 2026-04-18
- The bounded `Tycho 5.0.2` probe is also green, but **only when Maven runs on Java 21**.
- Validated staged ladder on `Java 21`:
  - `AGGREGATOR/prebuild/pom.xml -Pplatform.mac.aarch64 clean install`
  - `AGGREGATOR/plugins/pom.xml -Pplatform.mac.aarch64 clean install`
  - `AGGREGATOR/features/opensource/pom.xml -Pplatform.mac.aarch64 clean install`
  - `AGGREGATOR/doc/pom.xml clean install`
  - `products/pom.xml -Pplatform.mac.aarch64,product.org clean package`
- The one-shot fresh-scratch path is also green on `Java 21`:
  - `AGGREGATOR/pom.xml -Pplatform.mac.aarch64,product.org clean package`
- Verified postconditions for the `5.0.2` probe:
  - `products/target/products/org.modelio.product/macosx/cocoa/aarch64/Modelio.app` still materialises successfully,
  - packaging-time `plutil` and `codesign --verify --deep --strict --verbose=2` checks still pass,
  - `diagnostics/macos-aarch64/final-app-x86_64-audit-after-tycho-502.txt` reports `HITS 0`.
- Immediate interpretation:
  - `Tycho 5.0.2` is now an accepted baseline for this repo,
  - the next bounded step should move away from Tycho experiments and back to Java-baseline cleanup inside owned bundles.

#### [Historical] Exploratory Phase 3 notes from the early Tycho probe

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

### [Historical] Phase 4 - Normalize Java baselines, but only to a safe stepping stone
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

#### Java 8 assumption scan after BREE normalization - 2026-04-18
Runtime-significant findings:
- A follow-up rescan on `2026-04-18` found **no remaining** runtime `build.properties` files pinned to Java 8 under `modelio/**/build.properties`.
- The real owned-runtime cleanup target turned out to be stale Eclipse project metadata instead: repo-owned `modelio/**/.classpath` files that still pointed at `JavaSE-1.8` or a generic `org.eclipse.jdt.launching.JRE_CONTAINER` have now been normalised to the explicit `JavaSE-11` container.
- A full rescan on `2026-04-18` found **no remaining** generic `org.eclipse.jdt.launching.JRE_CONTAINER` entries under `modelio/**/.classpath`.
- Validation completed on the current `Tycho 5.0.2` / `Java 21` baseline using a fresh scratch Maven repository:
  - `AGGREGATOR/prebuild/pom.xml -Pplatform.mac.aarch64 clean install` succeeded
  - `AGGREGATOR/plugins/core/pom.xml -Pplatform.mac.aarch64 clean install` succeeded
  - `AGGREGATOR/plugins/plugdules/pom.xml -Pplatform.mac.aarch64 clean install` succeeded
  - `AGGREGATOR/plugins/platform/pom.xml -Pplatform.mac.aarch64 clean install` succeeded
  - `AGGREGATOR/plugins/app/pom.xml -Pplatform.mac.aarch64 clean install` succeeded
  - `AGGREGATOR/plugins/bpmn/pom.xml -Pplatform.mac.aarch64 clean install` succeeded
  - `AGGREGATOR/plugins/uml/pom.xml -Pplatform.mac.aarch64 clean install` succeeded
  - `AGGREGATOR/plugins/pom.xml -Pplatform.mac.aarch64 clean verify` succeeded

Tooling-only / lower-priority findings:
- `doc/parent/pom.xml` still uses `<maven.compiler.source>1.8</maven.compiler.source>` and `<maven.compiler.target>1.8</maven.compiler.target>`; this currently affects the doc branch, not the main runtime.
- `modelio/core/core.utils/lib/build_deps/pom.xml` still contains commented `1.8` compiler settings inside a disabled block; this is stale local helper-build history, not an active main-reactor input.

Interpretation:
- The manifest normalization is complete, and the originally suspected runtime `build.properties` drift was a false lead.
- The owned-runtime Eclipse metadata is now aligned to the Java 11 baseline, including explicit `.classpath` JRE containers, so the remaining Java-baseline skew is concentrated in doc/tooling-only metadata and in the eventual runtime-JDK uplift decision.

#### Runtime baseline audit before any packaged-Java uplift - 2026-04-18
Scope of this audit:
- distinguish true packaged-runtime constraints from build-only or IDE-only leftovers,
- keep the current `Tycho 5.0.2` / `Java 21` build contract fixed,
- inspect only the Java baseline actually required by the shipped product path on macOS `aarch64`.

Runtime-significant findings from inspected control points:

| Evidence | Files inspected | Classification | Practical meaning |
| --- | --- | --- | --- |
| The shared build and target wiring originally still referenced a vendored Java 11 p2 repository. | `pom.xml`, `maven/modelio-parent/pom.xml`, `dev-platform/rcp-target/rcp.target`, `dev-platform/pack-resources/openjdk-jre11/` | runtime-significant at audit time | This was the remaining shared Java 11 runtime signal that needed to be tested and then either removed or retargeted for the supported path. |
| The product originally still hard-coded Java 11 as the required runtime baseline. | `products/modelio-os.product` | runtime-significant at audit time | `-Dosgi.requiredJavaVersion=11` and `JavaSE-11` VM entries were the main owned product metadata blockers before the Java 21 runtime spike. |
| Owned OSGi runtime bundles originally still declared Java 11 as their required execution environment. | `modelio/**/META-INF/MANIFEST.MF` | runtime-significant at audit time | A full rescan on `2026-04-18` found **99** `Bundle-RequiredExecutionEnvironment` declarations, all set to `JavaSE-11` before the later Java 21 runtime spike. |
| JAXB is no longer expected from the JDK itself; it is shipped as vendored runtime content. | `dev-platform/rcp-target/jakarta/jaxb/pom.xml`, `products/modelio-os.product`, `modelio/bpmn/bpmn.xml/**/*.java` | runtime-significant | Runtime code now imports `jakarta.xml.bind`, and the product includes `org.modelio.jaxb.feature`, so any future runtime uplift must preserve the vendored JAXB/Jakarta feature path rather than assuming JDK-provided JAXB. |
| SWT browser usage is still part of the runtime surface, but not through Chromium-specific code. | `features/opensource/org.modelio.e4.rcp/feature.xml`, `features/opensource/org.modelio.platform.feature/feature.xml`, `modelio/**/*.java` searches for `Browser` and `SWT.CHROMIUM` | runtime-significant | SWT `Browser` widgets are still used in owned UI code, but no `SWT.CHROMIUM` usage was found; browser behaviour remains a runtime compatibility concern, just not a Chromium-specific API blocker. |
| Native loading remains in the runtime surface, but the known macOS AStyle path is already optional. | `modelio/platform/platform.api/src/org/modelio/api/astyle/AStyleInterface.java`, `features/opensource/org.modelio.platform.libraries/feature.xml` | runtime-significant | Native AStyle loading still exists in code, but failure is handled and the Intel-only mac fragment is already removed, so it is not the primary blocker for a later Java uplift. |

Tooling-only / lower-priority findings from the same audit:
- `doc/parent/pom.xml` had remained on Java 8 compiler metadata and was the main owned doc/tooling drift still left after the runtime audit.
- `maven/toolchains.macos.macports.xml` and `AGGREGATOR/toolchains.xml` had still carried `JavaSE-1.8` template entries; these were tooling templates, not packaged-runtime declarations.
- `modelio/core/core.utils/lib/build_deps/pom.xml` still contains commented Java 8 compiler settings inside a disabled helper-build block.
- The repo-owned `modelio/**/.classpath` JRE containers are now aligned to `JavaSE-11`, so they are no longer the main source of ambiguity for this phase.

Audit interpretation:
- The next runtime uplift was clearly blocked by **explicit product and manifest Java 11 declarations**, not by stale IDE metadata.
- The build-layer split is now well defined:
  - build JDK = `Java 21` for Maven/Tycho,
  - packaged runtime baseline at audit time = vendored `Java 11` content plus `JavaSE-11` bundle declarations.
- The repo has already removed the old JDK-provided JAXB assumption by moving runtime JAXB usage to vendored Jakarta/JAXB p2 content, which reduces one common Java 11+ migration risk.

Go / no-go rule before any packaged-runtime uplift:
- **No-go** for a Java runtime uplift while all three of the following remain true:
  1. `products/modelio-os.product` still injects `-Dosgi.requiredJavaVersion=11`,
  2. the packaged runtime still resolves from `dev-platform/pack-resources/openjdk-jre11`,
  3. owned runtime bundles still declare `Bundle-RequiredExecutionEnvironment: JavaSE-11`.
- **Go** only after a bounded follow-up slice explicitly updates those three layers together and revalidates the full Apple Silicon product path.

Recommended next bounded step after this audit:
- keep the packaged-runtime question narrowly scoped,
- first validate whether the current macOS Apple Silicon product path actually depends on `dev-platform/pack-resources/openjdk-jre11`,
- then either retarget or remove that stale Java 11 runtime wiring for the supported macOS path before broader RCP re-vendoring.

#### Doc/tooling Java metadata cleanup completed - 2026-04-18
Changes completed in this bounded slice:
- `doc/parent/pom.xml` now uses `<maven.compiler.source>11</maven.compiler.source>` and `<maven.compiler.target>11</maven.compiler.target>`.
- `maven/toolchains.macos.macports.xml` now carries `JavaSE-21` and `JavaSE-11` toolchain templates instead of a stale `JavaSE-1.8` template.
- `AGGREGATOR/toolchains.xml` now carries `JavaSE-21` and `JavaSE-11` toolchain templates instead of a stale `JavaSE-1.8` template.

Validation completed:
- a direct rescan of those three files on `2026-04-18` found **no remaining** `1.8` or `JavaSE-1.8` markers,
- `AGGREGATOR/doc/pom.xml clean install` succeeded on the current `Tycho 5.0.2` / `Java 21` baseline.

Interpretation after this cleanup:
- the owned doc/tooling Java 8 drift is now reduced to the commented helper-build history in `modelio/core/core.utils/lib/build_deps/pom.xml`,
- the next real Java-baseline decision is no longer doc/tooling metadata; it is the packaged-runtime uplift question described in the runtime audit.

#### Java 21 runtime spike on macOS aarch64 - completed on 2026-04-18
Changes completed in this bounded spike:
- `products/modelio-os.product` now injects `-Dosgi.requiredJavaVersion=21` instead of `11`.
- The product VM container entries in `products/modelio-os.product` now point at `JavaSE-21`.
- Owned runtime bundle manifests under `modelio/**/META-INF/MANIFEST.MF` were bulk-raised from `Bundle-RequiredExecutionEnvironment: JavaSE-11` to `JavaSE-21`.

Validation completed on the current `Tycho 5.0.2` / `Java 21` build baseline using a fresh scratch Maven repository:
- `AGGREGATOR/prebuild/pom.xml -Pplatform.mac.aarch64 clean install` succeeded
- `AGGREGATOR/plugins/core/pom.xml -Pplatform.mac.aarch64 clean install` succeeded
- `AGGREGATOR/plugins/plugdules/pom.xml -Pplatform.mac.aarch64 clean install` succeeded
- `AGGREGATOR/plugins/platform/pom.xml -Pplatform.mac.aarch64 clean install` succeeded
- `AGGREGATOR/plugins/app/pom.xml -Pplatform.mac.aarch64 clean install` succeeded
- `AGGREGATOR/plugins/bpmn/pom.xml -Pplatform.mac.aarch64 clean install` succeeded
- `AGGREGATOR/plugins/uml/pom.xml -Pplatform.mac.aarch64 clean install` succeeded
- `AGGREGATOR/features/opensource/pom.xml -Pplatform.mac.aarch64 clean install` succeeded
- `AGGREGATOR/doc/pom.xml clean install` succeeded
- `AGGREGATOR/products/pom.xml -Pplatform.mac.aarch64,product.org clean package` succeeded
- `AGGREGATOR/pom.xml -Pplatform.mac.aarch64,product.org clean package` also succeeded as a one-shot full reactor

Observed product-level result:
- the rebuilt `Modelio.app` now contains `-Dosgi.requiredJavaVersion=21` in `Contents/Eclipse/modelio.ini`,
- the packaged macOS `aarch64` app still passes the built-in `plutil` and `codesign` verification steps,
- the packaged app audit still finds no shipped `x86_64` payload.

Important interpretation from this spike:
- no macOS `aarch64` build, feature, or packaging failure was triggered by moving owned bundle BREEs and product launcher metadata from Java 11 to Java 21,
- the currently built macOS app still does **not** embed an Adoptium/OpenJDK runtime directory,
- the shared target/repository wiring still points at `dev-platform/pack-resources/openjdk-jre11`, but that repo does not appear to materialise into the current macOS `aarch64` app bundle.

Practical consequence:
- for the currently supported macOS Apple Silicon path, the first successful Java 21 runtime signal came from product metadata plus owned bundle BREE changes,
- the next bounded cleanup should clarify whether `openjdk-jre11` is still a real macOS runtime dependency or just stale cross-platform target metadata for paths we no longer actively support.

#### Remaining openjdk-jre11 wiring cleanup - completed on 2026-04-18
Changes completed in this bounded slice:
- removed the `openjdk-jre11` repository declaration from `pom.xml`,
- removed the matching `openjdk-jre11` repository declaration from `maven/modelio-parent/pom.xml`,
- removed the `dev-platform/pack-resources/openjdk-jre11` location from `dev-platform/rcp-target/rcp.target`,
- removed the matching `dev-platform/pack-resources/openjdk-jre11` location from `dev-platform/rcp-target/rcp_debug.target`.

Validation completed:
- `AGGREGATOR/prebuild/pom.xml -Pplatform.mac.aarch64 clean install` succeeded with a fresh scratch Maven repository,
- `AGGREGATOR/pom.xml -Pplatform.mac.aarch64,product.org clean package` also succeeded as a one-shot full reactor after the wiring removal.

Interpretation after this cleanup:
- the supported macOS `aarch64` path no longer carries active `openjdk-jre11` target or shared repository wiring,
- the still-present `dev-platform/pack-resources/openjdk-jre11/` directory now appears to be historical or for unsupported non-macOS paths rather than an active input for the validated Apple Silicon build,
- the next meaningful step is no longer Java-baseline wiring cleanup; it is broader platform modernisation work on top of the now-green Java 21 macOS baseline.

#### Mixed-train RCP audit refresh and first coherent-target cleanup slice - completed on 2026-04-19
Audit refresh findings from the current repo state:
- the active RCP target is still a deliberate hybrid made from `dev-platform/rcp-target/rcp-eclipse/eclipse`, `eclipse-fr`, `swt`, `launcher-arm64`, `macos-arm64`, and `jna/repository`,
- `eclipse-fr` is still a live input rather than removable baggage because `features/opensource/org.modelio.platform.libraries/feature.xml` still includes `org.eclipse.jface.nl_fr`,
- the broad SWT overlay remains the least-minimal mixed-train input because `features/opensource/org.modelio.e4.rcp/feature.xml` still explicitly pins `org.eclipse.swt.win32.win32.x86_64`, `org.eclipse.swt.gtk.linux.x86_64`, `org.eclipse.swt.cocoa.macosx.x86_64`, and `org.eclipse.swt.cocoa.macosx.aarch64` at `3.120.0.v20220530-1036`,
- that means the first coherent-target slice should not yet try to remove `eclipse-fr` or prune non-mac SWT fragments directly, because those would now broaden into feature-composition changes rather than target hygiene.

Chosen first cleanup slice:
- make the active overlay set reproducible as one coherent prebuild contract before narrowing any feature composition,
- specifically, add `dev-platform/rcp-target/rcp-eclipse/swt` to `AGGREGATOR/prebuild/pom.xml` so all currently active non-baseline Apple Silicon overlays (`swt`, `launcher-arm64`, `macos-arm64`, and `jna`) are refreshed together before the root build and `dev-platform/rcp-target` target-definition validation.

Validation completed for this slice:
- `AGGREGATOR/prebuild/pom.xml -Pplatform.mac.aarch64 clean install` succeeded on `Java 21` with a fresh scratch Maven repository at `/Users/david/IdeaProjects/Modelio/tmp/m2-coherent-target-prebuild`,
- reactor result: `swt-4-24-p2-site`, `equinox-launcher-arm64-p2-site`, `macos-arm64-p2-site`, `jna-p2-site`, `modelio-parent`, `rcp`, and `aggregator-prebuild` all finished `SUCCESS`.

Interpretation after this slice:
- the mixed-train target is still intentionally hybrid, but the active overlay portion is now regenerated coherently rather than partly checked-in and partly refreshed,
- the next bounded platform step should focus on narrowing feature composition for the supported Apple Silicon path, with the SWT overlay being the first high-value candidate because it still carries unsupported Windows, Linux, and Intel mac fragment pins.

#### SWT feature-composition narrowing for the supported Apple Silicon path - completed on 2026-04-19
Changes completed in this bounded slice:
- removed the explicit `org.eclipse.swt.win32.win32.x86_64` pin from `features/opensource/org.modelio.e4.rcp/feature.xml`,
- removed the explicit `org.eclipse.swt.gtk.linux.x86_64` pin from the same feature,
- removed the explicit `org.eclipse.swt.cocoa.macosx.x86_64` pin from the same feature,
- kept the newer SWT base bundle `org.eclipse.swt` and the supported `org.eclipse.swt.cocoa.macosx.aarch64` fragment pin in place.

Reason for this slice:
- the repo guidance now treats macOS Apple Silicon as the only supported runtime path,
- the SWT overlay had remained the broadest mixed-train exception because `org.modelio.e4.rcp` still pinned newer SWT fragments for unsupported Windows, Linux, and Intel mac targets,
- narrowing those pins reduced cross-platform skew without changing the approved Apple Silicon overlay family itself.

Validation completed:
- `AGGREGATOR/prebuild/pom.xml -Pplatform.mac.aarch64 clean install` succeeded with a fresh scratch Maven repository,
- `AGGREGATOR/plugins/pom.xml -Pplatform.mac.aarch64 clean install` succeeded against the same scratch repository,
- `AGGREGATOR/features/opensource/pom.xml -Pplatform.mac.aarch64 clean install` succeeded against the same scratch repository,
- `AGGREGATOR/doc/pom.xml clean install` succeeded against the same scratch repository,
- `AGGREGATOR/products/pom.xml -Pplatform.mac.aarch64,product.org clean package` succeeded against the same scratch repository.

Interpretation after this slice:
- `org.modelio.e4.rcp` now treats the newer SWT overlay as an Apple Silicon-specific exception rather than a broader cross-platform replacement family,
- the next bounded platform task should revisit whether the remaining non-aarch64 launcher/profile residue should also be narrowed to the supported path.

#### Launcher-fragment narrowing for the supported Apple Silicon path - completed on 2026-04-19
Changes completed in this bounded slice:
- removed the explicit `org.eclipse.equinox.launcher.cocoa.macosx.x86_64` pin from `features/opensource/org.modelio.e4.rcp/feature.xml`,
- removed the explicit `org.eclipse.equinox.launcher.gtk.linux.ppc64le` pin from the same feature,
- removed the explicit `org.eclipse.equinox.launcher.gtk.linux.aarch64` pin from the same feature,
- removed the explicit `org.eclipse.equinox.launcher.gtk.linux.x86_64` pin from the same feature,
- removed the explicit `org.eclipse.equinox.launcher.win32.win32.x86_64` pin from the same feature,
- kept the core `org.eclipse.equinox.launcher` bundle and the supported `org.eclipse.equinox.launcher.cocoa.macosx.aarch64` fragment pin in place.

Reason for this slice:
- after the earlier SWT narrowing, the most obvious remaining cross-platform residue inside `org.modelio.e4.rcp` was the explicit launcher-fragment set for unsupported Intel mac, Linux, and Windows targets,
- the repo guidance for this modernization stream now treats macOS Apple Silicon as the only supported runtime path,
- narrowing the launcher fragment composition reduced another layer of mixed-train, cross-platform residue without broadening the change into product-profile deletion or target re-vendoring.

Validation completed:
- `AGGREGATOR/prebuild/pom.xml -Pplatform.mac.aarch64 clean install` succeeded with a fresh scratch Maven repository,
- `AGGREGATOR/plugins/pom.xml -Pplatform.mac.aarch64 clean install` succeeded against the same scratch repository,
- `AGGREGATOR/features/opensource/pom.xml -Pplatform.mac.aarch64 clean install` succeeded against the same scratch repository,
- `AGGREGATOR/doc/pom.xml clean install` succeeded against the same scratch repository,
- `AGGREGATOR/products/pom.xml -Pplatform.mac.aarch64,product.org clean package` succeeded against the same scratch repository.

Interpretation after this slice:
- `org.modelio.e4.rcp` now carries only the Apple Silicon launcher fragment as an explicit launcher override,
- the remaining legacy profile residue now lives primarily in profile definitions such as `platform.mac`, `platform.win`, and `platform.linux`, which should be handled in a separate bounded product/profile cleanup slice rather than mixed into feature composition work.

#### Product/profile cleanup for the supported Apple Silicon path - completed on 2026-04-19
Changes completed in this bounded slice:
- removed the legacy `package.all` profile from `products/pom.xml`,
- removed the unsupported `platform.linux`, `platform.win`, and `platform.mac` packaging profiles from `products/pom.xml`,
- kept `product.org`, `repositoryP2`, and `platform.mac.aarch64` in `products/pom.xml`,
- removed the unsupported `platform.mac` profile from the root `pom.xml`,
- removed the unsupported `platform.mac` profile from `maven/modelio-parent/pom.xml`,
- updated `AGENTS.md` so the documented packaging contract now treats `platform.mac.aarch64` as the supported product profile.

Reason for this slice:
- after the SWT and launcher-fragment narrowing work, the remaining platform residue was concentrated in legacy packaging/profile declarations rather than feature composition,
- the repo guidance for this modernization stream now treats macOS Apple Silicon as the only supported build and packaging target,
- removing those unsupported product/profile declarations reduced configuration drift without changing the validated Apple Silicon path itself.

Validation completed:
- `AGGREGATOR/prebuild/pom.xml -Pplatform.mac.aarch64 clean install` succeeded with a fresh scratch Maven repository,
- `AGGREGATOR/plugins/pom.xml -Pplatform.mac.aarch64 clean install` succeeded against the same scratch repository,
- `AGGREGATOR/features/opensource/pom.xml -Pplatform.mac.aarch64 clean install` succeeded against the same scratch repository,
- `AGGREGATOR/doc/pom.xml clean install` succeeded against the same scratch repository,
- `AGGREGATOR/products/pom.xml -Pplatform.mac.aarch64,product.org clean package` succeeded against the same scratch repository.

Interpretation after this slice:
- the supported Apple Silicon packaging path is now less encumbered by obsolete Linux, Windows, and Intel mac profile declarations,
- the next meaningful platform step is no longer profile pruning; it is either deciding whether historical docs like `MACOS_RECOVERY_PLAN.md` should be retired or moving on to the larger coherent-target / RCP re-vendoring work.

#### [Historical] Phase 5 preparation audit - coherent RCP re-vendoring boundary refreshed on 2026-04-19
Audit goal:
- identify the exact platform layers that still define the real modernization boundary after the Apple Silicon cleanup work,
- avoid treating the remaining work as a vague “upgrade Eclipse” task when the repo still contains a very specific hybrid contract.

Current audited platform stack:
- the vendored base repository `dev-platform/rcp-target/rcp-eclipse/eclipse` still publishes the Eclipse `4.18 / 2020-12` train, including:
  - `org.eclipse.platform.feature.group` `4.18.0.v20201202-1800`,
  - `org.eclipse.rcp.feature.group` `4.18.0.v20201202-1800`,
  - `org.eclipse.e4.rcp.feature.group` `4.18.0.v20201202-1103`,
  - `org.eclipse.swt` `3.115.100.v20201202-1103`.
- the active Apple Silicon overlay repositories still publish these replacement units on top of that baseline:
  - `swt/` publishes `org.eclipse.swt` `3.120.0.v20220530-1036` plus mac SWT fragments including `org.eclipse.swt.cocoa.macosx.aarch64`,
  - `launcher-arm64/` publishes `org.eclipse.equinox.launcher.cocoa.macosx` and `org.eclipse.equinox.launcher.cocoa.macosx.aarch64` `1.2.200.v20210527-0259`,
  - `macos-arm64/` publishes `org.eclipse.core.filesystem.macosx` `1.3.400.v20220812-1420` and `org.eclipse.equinox.security.macosx` `1.101.400.v20210427-1958`,
  - `jna/repository/` publishes `com.sun.jna` and `com.sun.jna.platform` `5.18.1`.
- the repo-owned feature and product layers that still sit directly on that contract are:
  - `features/opensource/org.modelio.e4.rcp/feature.xml` at `4.18.0.v20201202-1103`,
  - `features/opensource/org.modelio.rcp/feature.xml` at `4.18.0.v20201202-1800`,
  - `features/opensource/org.modelio.platform.feature/feature.xml` at `4.18.0.v20201202-1800`,
  - `products/modelio-os.product`, which still includes `org.modelio.e4.rcp`, `org.modelio.rcp`, and `org.modelio.platform.feature` directly.

Interpretation from this audit:
- the project is no longer blocked by packaging/profile residue; the remaining modernization boundary is the still-vendored `4.18` runtime contract itself,
- the next real platform step cannot be just “bump one overlay” or “edit one feature”; the base `eclipse/` repository and the three repo-owned feature layers above it now need to be treated as one change set,
- because `products/modelio-os.product` includes those features directly, product metadata belongs in the first coherent re-vendoring slice rather than as a later afterthought.

Chosen first coherent re-vendoring slice to prepare next:
- prepare a parallel replacement for the `dev-platform/rcp-target/rcp-eclipse/eclipse` baseline repository,
- then repin together, in one bounded slice:
  - `features/opensource/org.modelio.e4.rcp/feature.xml`,
  - `features/opensource/org.modelio.rcp/feature.xml`,
  - `features/opensource/org.modelio.platform.feature/feature.xml`,
  - `products/modelio-os.product`.

Explicit non-goal for that first slice:
- do **not** attempt Java 25, Tycho uplift, or unrelated product-behaviour cleanup at the same time,
- do **not** treat the current overlay generators as the destination state; after the base train is re-vendored, each overlay should be re-justified or removed.

#### [Historical] Phase 5 preparation audit - repo-owned `org.eclipse.*` pin groups refreshed on 2026-04-19
Audit purpose:
- move from a repo-level “the platform is still 4.18 plus overlays” statement to an actionable inventory of the `org.eclipse.*` pins that must move together in the first coherent re-vendoring slice.

Feature-layer inventory from the current repo state:

1. `features/opensource/org.modelio.e4.rcp/feature.xml`
   - This is the lowest repo-owned Eclipse feature layer and still carries the densest `org.eclipse.*` pin set.
   - The bulk of its pins are still `4.18 / 2020-12` era workbench and Equinox bundles, especially these groups:
     - **E4 workbench / DI / CSS core:** `org.eclipse.e4.core.services`, `org.eclipse.e4.core.commands`, `org.eclipse.e4.core.di`, `org.eclipse.e4.core.contexts`, `org.eclipse.e4.core.di.extensions`, `org.eclipse.e4.ui.*` bundles,
     - **Equinox / OSGi runtime:** `org.eclipse.equinox.common`, `org.eclipse.equinox.event`, `org.eclipse.equinox.preferences`, `org.eclipse.equinox.registry`, `org.eclipse.equinox.simpleconfigurator`, `org.eclipse.equinox.app`, `org.eclipse.osgi`, `org.eclipse.osgi.compatibility.state`, `org.eclipse.osgi.services`, `org.eclipse.osgi.util`,
     - **Core runtime / databinding / expressions:** `org.eclipse.core.commands`, `org.eclipse.core.contenttype`, `org.eclipse.core.databinding*`, `org.eclipse.core.expressions`, `org.eclipse.core.jobs`, `org.eclipse.core.runtime`,
     - **UI shell:** `org.eclipse.jface`, `org.eclipse.jface.databinding`, `org.eclipse.jface.notifications`, `org.eclipse.equinox.console`, `org.eclipse.equinox.bidi`, `org.eclipse.urischeme`.
   - This feature also still carries the active overlay-derived replacement pins that define the current hybrid runtime:
     - `org.eclipse.equinox.launcher.cocoa.macosx.aarch64` `1.2.200.v20210527-0259`,
     - `org.eclipse.swt` `3.120.0.v20220530-1036`,
     - `org.eclipse.swt.cocoa.macosx.aarch64` `3.120.0.v20220530-1036`.
   - It also still carries non-mac Chromium baseline fragments for unsupported platforms:
     - `org.eclipse.swt.browser.chromium.win32.win32.x86_64`,
     - `org.eclipse.swt.browser.chromium.gtk.linux.x86_64`.

2. `features/opensource/org.modelio.rcp/feature.xml`
   - This is now a relatively thin wrapper over `org.modelio.e4.rcp`, but it still carries baseline UI shell pins that must move in lockstep with the e4 layer:
     - `org.eclipse.help`,
     - `org.eclipse.ui`,
     - `org.eclipse.ui.workbench`,
     - `org.eclipse.update.configurator`,
     - `org.eclipse.rcp`,
     - `org.eclipse.ui.cocoa`.
   - Because `org.modelio.rcp` includes `org.modelio.e4.rcp`, the first coherent re-vendoring slice cannot safely update this feature independently of the e4 feature below it.

3. `features/opensource/org.modelio.platform.feature/feature.xml`
   - This layer is the broadest repo-owned Eclipse feature surface above `org.modelio.rcp`.
   - It still carries a large `4.18 / 2020-12` era platform IDE set, including families such as:
     - **platform / resources / variables / filebuffers:** `org.eclipse.platform`, `org.eclipse.core.resources`, `org.eclipse.core.filebuffers`, `org.eclipse.core.variables`,
     - **debug / compare / search / refactoring:** `org.eclipse.debug.*`, `org.eclipse.compare*`, `org.eclipse.search`, `org.eclipse.ltk.*`,
     - **text / editors / forms / navigator / IDE UI:** `org.eclipse.text`, `org.eclipse.jface.text`, `org.eclipse.ui.console`, `org.eclipse.ui.*`, `org.eclipse.ui.ide`, `org.eclipse.ui.ide.application`, `org.eclipse.ui.forms`, `org.eclipse.ui.views.properties.tabbed`,
     - **team / jsch / p2 UI:** `org.eclipse.team.*`, `org.eclipse.jsch.*`, `org.eclipse.equinox.p2.user.ui`, `org.eclipse.equinox.p2.reconciler.dropins`.
   - It also still carries the remaining active overlay-derived mac-native fragment pins:
     - `org.eclipse.core.filesystem.macosx` `1.3.400.v20220812-1420`,
     - `org.eclipse.equinox.security.macosx` `1.101.400.v20210427-1958`.
   - So this feature is where the first coherent re-vendoring slice must reconcile the older baseline platform UI set with the newer mac-native fragment story.

Practical conclusion from this pin inventory:
- the first coherent re-vendoring slice should be treated as **three coupled repo-owned feature layers plus product metadata**, not as one feature file at a time,
- the move order inside that slice should be:
  1. replace the vendored `dev-platform/rcp-target/rcp-eclipse/eclipse` baseline,
  2. repin `org.modelio.e4.rcp` against the new train,
  3. repin `org.modelio.rcp` on top of that new e4 layer,
  4. repin `org.modelio.platform.feature` on the same train,
  5. update `products/modelio-os.product` only after those three feature layers are internally coherent again.

Specific boundary for the first execution slice:
- keep `eclipse-fr` and `org.modelio.platform.libraries` out of the first re-vendoring change unless the new train forces them to move,
- keep `JNA` as an explicit follow-up check rather than assuming it disappears automatically,
- treat the current overlay families (`swt`, `launcher-arm64`, `macos-arm64`, `jna`) as compatibility shims to be re-justified after the new base train is in place, not as part of the destination contract.

#### [Historical] Phase 5 execution prep - concrete re-vendoring checklist and initial version-diff audit on 2026-04-19
Decision taken for the first real replacement slice:
- the replacement target train for the next platform move is **Eclipse RCP `2026-03`**,
- this is now the explicit planning target because the repo guidance already converges on it in:
  - `MODERNIZATION_PLAN.md` (`Primary platform target` and `Phase 5 - Re-vendor the full Eclipse/RCP stack to 2026-03`),
  - `AGENTS.md` (Apple Silicon-only supported path on the current `Tycho 5.0.2` / `Java 21` build baseline),
  - `.github/copilot-instructions.md` (longer-term goal is `Eclipse RCP 2026-03`).
- the exact bundle and feature versions for that train are now staged locally as a **metadata-first parallel repository** under `dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03/`, so the next execution step can move from abstract planning to concrete repinning preparation without touching the active target yet.

Current baseline contents re-confirmed from `dev-platform/rcp-target/rcp-eclipse/eclipse/content.xml`:
- `org.eclipse.platform.feature.group` = `4.18.0.v20201202-1800`,
- `org.eclipse.rcp.feature.group` = `4.18.0.v20201202-1800`,
- `org.eclipse.e4.rcp.feature.group` = `4.18.0.v20201202-1103`,
- `org.eclipse.platform` = `4.18.0.v20201202-1800`,
- `org.eclipse.rcp` = `4.18.0.v20201202-1800`,
- `org.eclipse.swt` = `3.115.100.v20201202-1103`,
- `org.eclipse.ui.workbench` = `3.122.0.v20201122-1345`,
- `org.eclipse.core.runtime` = `3.20.0.v20201027-1526`,
- `org.eclipse.equinox.launcher` = `1.6.0.v20200915-1508`,
- `org.eclipse.core.filesystem.macosx` = `1.3.200.v20190903-0945`,
- `org.eclipse.equinox.security.macosx` = `1.101.200.v20190903-0934`,
- `com.sun.jna` / `com.sun.jna.platform` = `4.5.1.v20190425-1842`.

Initial version-diff audit against the still-active overlay set:

| Area | Baseline in `eclipse/` | Current active replacement | Current source of replacement | Practical meaning for the first slice |
| --- | --- | --- | --- | --- |
| SWT base | `org.eclipse.swt` `3.115.100.v20201202-1103` | `org.eclipse.swt` `3.120.0.v20220530-1036` | `rcp-eclipse/swt` | The new vendored `2026-03` train must absorb the SWT uplift so the broad SWT overlay can later be retired or sharply reduced. |
| Mac SWT fragment | baseline SWT family is still `3.115.100` | `org.eclipse.swt.cocoa.macosx.aarch64` `3.120.0.v20220530-1036` | `rcp-eclipse/swt` | Apple Silicon SWT is still coming from the overlay, not from the base train. |
| Mac launcher fragment | no `org.eclipse.equinox.launcher.cocoa.macosx.aarch64` in the baseline repo | `1.2.200.v20210527-0259` | `rcp-eclipse/launcher-arm64` | The future base train must supply a native Apple Silicon launcher path or this overlay remains justified. |
| Mac filesystem fragment | `org.eclipse.core.filesystem.macosx` `1.3.200.v20190903-0945` | `1.3.400.v20220812-1420` | `rcp-eclipse/macos-arm64` | The new train must be checked for a sufficiently modern native mac fragment before removing the overlay. |
| Mac security fragment | `org.eclipse.equinox.security.macosx` `1.101.200.v20190903-0934` | `1.101.400.v20210427-1958` | `rcp-eclipse/macos-arm64` | Same rule as the filesystem fragment: the first slice should measure the new train before deciding whether the overlay still adds value. |
| JNA | `com.sun.jna` / `com.sun.jna.platform` `4.5.1.v20190425-1842` | `5.18.1` | `rcp-eclipse/jna/repository` | JNA remains a version skew even after the Apple Silicon cleanup; the first slice must verify whether the new train removes or reduces that gap. |

Repo-owned feature-layer impact, refreshed with the temporary audit helper `tmp/feature_pin_audit.py`:
- `features/opensource/org.modelio.e4.rcp/feature.xml`
  - still resolves the large majority of its `org.eclipse.*` pins from the old baseline repo,
  - still carries the active overlay/backfill pins for:
    - `org.eclipse.equinox.launcher.cocoa.macosx.aarch64` `1.2.200.v20210527-0259`,
    - `org.eclipse.swt` `3.120.0.v20220530-1036`,
    - `org.eclipse.swt.cocoa.macosx.aarch64` `3.120.0.v20220530-1036`,
    - `com.sun.jna` `5.18.1`,
    - `com.sun.jna.platform` `5.18.1`.
- `features/opensource/org.modelio.rcp/feature.xml`
  - is still entirely baseline-aligned today,
  - so its first re-vendoring role is to follow the new e4/workbench/UI train coherently rather than carry independent overlay logic.
- `features/opensource/org.modelio.platform.feature/feature.xml`
  - still resolves most of its Eclipse platform/UI pins from the baseline repo,
  - but it is the current carrier for the `macos-arm64` replacements:
    - `org.eclipse.core.filesystem.macosx` `1.3.400.v20220812-1420`,
    - `org.eclipse.equinox.security.macosx` `1.101.400.v20210427-1958`.

Smallest first replacement-slice plan:
1. **Stage the new base repo in parallel, do not replace the active one yet.**
   - Create a sibling vendored repository such as `dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03/`.
   - Keep `dev-platform/rcp-target/rcp-eclipse/eclipse/` untouched until the new train has been audited and mapped.
2. **Harvest exact versions from the staged `2026-03` repo before editing feature files.**
   - Re-run the same inventory against the new `content.xml`:
     - `org.eclipse.platform.feature.group`,
     - `org.eclipse.rcp.feature.group`,
     - `org.eclipse.e4.rcp.feature.group`,
     - `org.eclipse.swt`,
     - `org.eclipse.ui.workbench`,
     - `org.eclipse.core.runtime`,
     - `org.eclipse.equinox.launcher`,
     - `org.eclipse.core.filesystem.macosx`,
     - `org.eclipse.equinox.security.macosx`,
     - `com.sun.jna`,
     - `com.sun.jna.platform`.
   - Do not hand-author new bundle versions before this inventory exists.
3. **Draft one grouped repinning patch across the three feature layers, not three isolated edits.**
   - `features/opensource/org.modelio.e4.rcp/feature.xml`: repin the E4, Equinox, SWT, launcher, and JNA-adjacent entries from the new train inventory.
   - `features/opensource/org.modelio.rcp/feature.xml`: repin the wrapper workbench/UI shell layer against the same train.
   - `features/opensource/org.modelio.platform.feature/feature.xml`: repin the broad IDE/platform layer and decide, based on the staged repo contents, whether the current `macos-arm64` fragment overrides still remain necessary.
4. **Touch `products/modelio-os.product` only after those three feature files are internally coherent.**
   - Verify whether any included feature ids, application ids, or startup bundle assumptions need adjustment for the new train.
   - Keep the product touch surface bounded to feature membership and runtime metadata, not unrelated behaviour changes.
5. **Swap target wiring only after the repinned features resolve.**
   - Update `dev-platform/rcp-target/rcp.target` to point at the staged `2026-03` base repo only when the grouped repinning patch exists.
   - Re-justify each overlay (`swt`, `launcher-arm64`, `macos-arm64`, `jna`) against the new train rather than assuming any of them disappear automatically.

Practical no-go rules for this first slice:
- do **not** mix the `2026-03` base-repo staging with a second Java move,
- do **not** combine it with another Tycho upgrade,
- do **not** remove `eclipse-fr` in the same patch unless the staged train immediately forces the associated feature-layer move,
- do **not** guess final overlay deletions until the staged `2026-03` metadata proves whether those overrides are still required.

Execution update from the first concrete staging step on `2026-04-19`:
- created the parallel staging directory `dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03/`,
- added `README.md` there to document that the directory is **not** yet part of the active target and is currently intended for metadata-first auditing only,
- added `stage_metadata.py` there so the staging step is reproducible rather than a one-off manual download,
- downloaded and extracted these direct-child `2026-03` p2 metadata files from `https://download.eclipse.org/releases/2026-03/202603111000/`:
  - `content.jar` -> `content.xml`,
  - `artifacts.jar` -> `artifacts.xml`,
- recorded the fetched source URLs and file sizes in `dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03/stage-manifest.json`.

Exact staged `2026-03` versions harvested for the first grouped repinning pass:
- `org.eclipse.platform.feature.group` = `4.39.0.v20260226-0420`,
- `org.eclipse.rcp.feature.group` = `4.39.0.v20260226-0420`,
- `org.eclipse.e4.rcp.feature.group` = `4.39.0.v20260225-1014`,
- `org.eclipse.platform` = `4.39.0.v20260226-0420`,
- `org.eclipse.rcp` = `4.39.0.v20260226-0420`,
- `org.eclipse.ui` = `3.208.0.v20251219-1043`,
- `org.eclipse.ui.workbench` = `3.138.0.v20260204-1601`,
- `org.eclipse.ui.cocoa` = `1.3.400.v20260123-2255`,
- `org.eclipse.core.runtime` = `3.34.200.v20251220-0953`,
- `org.eclipse.equinox.launcher` = `1.7.100.v20251111-0406`,
- `org.eclipse.equinox.launcher.cocoa.macosx.aarch64` = `1.2.1400.v20250801-0854`,
- `org.eclipse.swt` = `3.133.0.v20260225-1014`,
- `org.eclipse.swt.cocoa.macosx.aarch64` = `3.133.0.v20260225-1014`,
- `org.eclipse.core.filesystem.macosx` = `1.3.400.v20220812-1420`,
- `org.eclipse.equinox.security.macosx` = `1.102.500.v20250521-0414`,
- `com.sun.jna` = `5.18.1.v20251001-0800`,
- `com.sun.jna.platform` = `5.18.1`.

Immediate interpretation from the staged metadata:
- the staged base train now **directly contains** the Apple Silicon launcher fragment, so `launcher-arm64` moves from “probably necessary” to “candidate for removal after repinning validation”,
- the staged base train also **directly contains** the Apple Silicon SWT fragment, so the broad `swt` overlay is now a strong candidate for retirement rather than a likely long-term shim,
- the staged base train contains `org.eclipse.core.filesystem.macosx` at exactly the same version as the current `macos-arm64` overlay pin, which is a strong signal that at least part of that overlay may already be redundant,
- the staged base train contains a **newer** `org.eclipse.equinox.security.macosx` than the current overlay pin, which makes the current `macos-arm64` security override look obsolete for the first grouped repin,
- the staged base train carries JNA `5.18.1`, so the repo can now test whether the standalone `jna` overlay is removable rather than assuming it remains part of the destination contract.

Staged metadata gaps and shape changes that must influence the grouped repinning patch:
- no `org.eclipse.swt.browser.chromium*` units were found in the staged `2026-03` metadata, so the current non-mac Chromium fragment pins in `features/opensource/org.modelio.e4.rcp/feature.xml` cannot simply be version-bumped and should be removed or replaced deliberately in the first grouped repinning patch,
- these legacy native fragments from `features/opensource/org.modelio.platform.feature/feature.xml` were not found in the staged `2026-03` metadata either:
  - `org.eclipse.core.net.linux.x86_64`,
  - `org.eclipse.core.net.win32.x86_64`,
  - `org.eclipse.core.resources.win32.x86_64`,
  - `org.eclipse.core.filesystem.win32.x86_64`,
  - `org.eclipse.equinox.security.win32.x86_64`,
  - `org.eclipse.equinox.security.linux.x86_64`.

Refined next action after staging:
- use the harvested versions above to draft the first real grouped repinning patch across:
  - `features/opensource/org.modelio.e4.rcp/feature.xml`,
  - `features/opensource/org.modelio.rcp/feature.xml`,
  - `features/opensource/org.modelio.platform.feature/feature.xml`,
- treat the missing Chromium and cross-platform native-fragment entries as deliberate removal decisions that belong in that same grouped patch,
- leave `dev-platform/rcp-target/rcp.target` unchanged until that grouped patch has been prepared and audited.

Follow-up execution prep completed on `2026-04-19` after the metadata staging:
- added `dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03/stage_repin_slice.py` so the staged metadata can be turned into a concrete grouped-repinning manifest instead of remaining a manual grep exercise,
- generated `dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03/repin-suggestions.json`,
- downloaded a direct artefact cache into `dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03/slice-cache/` for the current repo-owned feature entries that have staged `2026-03` replacements.

Observed results from `repin-suggestions.json`:
- direct staged artefacts cached: **118**,
- `org.modelio.e4.rcp`: **55** direct replacements, **2** removals,
- `org.modelio.rcp`: **6** direct replacements, **0** removals,
- `org.modelio.platform.feature`: **61** direct replacements, **6** removals.

Current removal candidates surfaced by the staged `2026-03` repo:
- from `features/opensource/org.modelio.e4.rcp/feature.xml`:
  - `org.eclipse.swt.browser.chromium.win32.win32.x86_64`,
  - `org.eclipse.swt.browser.chromium.gtk.linux.x86_64`.
- from `features/opensource/org.modelio.platform.feature/feature.xml`:
  - `org.eclipse.core.net.linux.x86_64`,
  - `org.eclipse.core.net.win32.x86_64`,
  - `org.eclipse.core.resources.win32.x86_64`,
  - `org.eclipse.core.filesystem.win32.x86_64`,
  - `org.eclipse.equinox.security.win32.x86_64`,
  - `org.eclipse.equinox.security.linux.x86_64`.

Practical consequence of this extra prep step:
- the next grouped patch no longer needs to guess either the replacement versions or the direct staged artefacts for the three affected repo-owned feature layers,
- the first grouped repinning patch can now be authored directly from `repin-suggestions.json`, while still leaving `dev-platform/rcp-target/rcp.target` and the active baseline repo untouched until that patch is ready.

#### [Historical] Phase 5 execution slice - grouped repo-owned feature repinning prepared on 2026-04-20
Changes completed in this slice:
- repinned `features/opensource/org.modelio.e4.rcp/feature.xml` from the old `4.18 / 2020-12` Eclipse pin set to the staged `2026-03` versions for the E4 workbench, Equinox runtime, SWT, launcher, JFace, and JNA-facing entries,
- repaired the previously stray `org.eclipse.swt` text lines in that feature back into a proper `<plugin .../>` entry and set it to `3.133.0.v20260225-1014`,
- removed the two Chromium fragment pins that are absent from the staged `2026-03` train:
  - `org.eclipse.swt.browser.chromium.win32.win32.x86_64`,
  - `org.eclipse.swt.browser.chromium.gtk.linux.x86_64`,
- repinned `features/opensource/org.modelio.rcp/feature.xml` to the staged `2026-03` workbench/UI shell versions and aligned its include on the repinned `org.modelio.e4.rcp` feature version,
- repinned `features/opensource/org.modelio.platform.feature/feature.xml` to the staged `2026-03` platform/IDE versions, aligned its include on the repinned `org.modelio.rcp` feature version, and removed the legacy native fragment pins that are absent from the staged train:
  - `org.eclipse.core.net.linux.x86_64`,
  - `org.eclipse.core.net.win32.x86_64`,
  - `org.eclipse.core.resources.win32.x86_64`,
  - `org.eclipse.core.filesystem.win32.x86_64`,
  - `org.eclipse.equinox.security.win32.x86_64`,
  - `org.eclipse.equinox.security.linux.x86_64`.

Resulting feature versions after the grouped patch:
- `org.modelio.e4.rcp` = `4.39.0.v20260225-1014`,
- `org.modelio.rcp` = `4.39.0.v20260226-0420`,
- `org.modelio.platform.feature` = `4.39.0.v20260226-0420`.

Validation completed for this slice:
- direct XML/error validation on the three edited feature files found no problems,
- a metadata-level consistency check using `tmp/validate_feature_repin.py` completed successfully and confirmed that every repinned `org.eclipse.*` and `com.sun.jna*` entry in:
  - `features/opensource/org.modelio.e4.rcp/feature.xml`,
  - `features/opensource/org.modelio.rcp/feature.xml`,
  - `features/opensource/org.modelio.platform.feature/feature.xml`
  now exists at the same version in the staged `dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03/content.xml` metadata.

Important boundary after this slice:
- the repo-owned feature layers are now repinned to the staged `2026-03` metadata contract,
- the active target and shared repository wiring now point at `dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03` in `dev-platform/rcp-target/rcp.target`, `pom.xml`, and `maven/modelio-parent/pom.xml`,
- and the remaining risk is no longer “make the new train active at all”, but “finish stabilising the active `2026-03` mirror and retire temporary compatibility baggage deliberately”.

Practical next step after this grouped patch:
- keep topping up any missing upstream bundles exposed by the active `2026-03` packaging path until the staged mirror is complete,
- rerun the normal staged Maven validation ladder from a fresh scratch repository against the active `2026-03` baseline,
- then audit each remaining overlay/input family (`swt`, `launcher-arm64`, `macos-arm64`, `jna`, and the direct staged mirror contents) to decide which ones are still justified on the fully active train.

#### [Historical] Follow-up note from the earlier phase-based plan - target-platform provenance and binary ownership
- The current `dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03/` mirror is still a correctness-first staging area backed by vendored upstream p2 artefacts, and some packaging fixes have required topping up missing external bundles directly in that mirror.
- That is acceptable during the active `2026-03` migration because it keeps the modernization slice focused on feature/product correctness rather than on inventing a new provisioning system mid-flight.
- It is **not** the intended final ownership model.
- After the full modernization is complete and the `2026-03` stack is green end-to-end, run one final bounded follow-up to decide how those external jars should be provisioned long-term.

Questions that follow-up must answer:
1. Should the repo continue to vendor the full staged p2 mirror under `dev-platform/rcp-target/rcp-eclipse/**` and commit missing upstream bundles directly?
2. Should the mirror instead be regenerated from a documented bootstrap step (for example a repo-owned fetch/materialisation script) so clean clones do not depend on ad-hoc manual top-ups?
3. Which currently vendored overlay repos should remain repo-owned generators (`jna`, any still-justified Apple Silicon overlays) versus plain mirrored upstream inputs?
4. What minimal reproducibility contract should a clean clone satisfy before the first Maven build starts?

Boundary for now:
- do **not** broaden the active modernization work into this provisioning redesign yet,
- do **not** block the current `2026-03` migration on replacing the vendored-mirror approach,
- treat this as one of the last cleanup tasks, after the modernized product path is already stable and boring.

#### [Historical] Material from earlier plan iterations
- The remaining Tycho retry notes, older phase labels, and earlier sequencing rules below are kept for historical relevance only.
- Do **not** use them as the current roadmap; use Slices A-D above instead.

#### [Historical] Bounded Tycho 2.7.5 retry preparation - ready state as of 2026-04-16
Why the retry is now cleaner than before:
- the main staged reactor is green again on `Tycho 2.2.0`;
- Apple Silicon packaging is green;
- final packaged `Modelio.app` audits clean (`HITS 0` for shipped `x86_64` payload);
- source BREE declarations are normalized to `JavaSE-11`.

What still makes the next modernization slice noisy if left unchanged:
- the main remaining Java-baseline noise is now confined to helper or template history rather than active doc/runtime metadata.

Recommendation before any future retry:
- treat runtime plugin metadata cleanup as complete and focus the next slice on real runtime-baseline constraints rather than Eclipse project metadata.
- or, if running the retry sooner, record any remaining helper-build/template remnants as known background noise so they are not confused with a true Tycho/target-layout failure.

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

### [Historical] Phase 5 - Re-vendor the full Eclipse/RCP stack to 2026-03
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

### [Historical] Phase 6 - Reassess Java 25 as an optional final hop
Scope:
- Only now test the highest Java level.
- Treat this as a separate change with its own compiler/runtime verification and packaging run.

Decision rule:
- If `Java 25` causes unresolved Tycho, PDE, or runtime issues, stop at the latest stable LTS baseline and ship that.

Exit gate:
- `Java 25` is adopted only if build, packaging, and runtime are all cleaner than the LTS alternative.

## [Historical] Order I would insist on
1. Reproducible current baseline.
2. Coherent target platform.
3. Native mac parity.
4. Build tooling uplift.
5. Java LTS uplift.
6. Full RCP `2026-03` uplift.
7. Optional `Java 25` evaluation.

## [Historical] Operational verification ladder

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

## [Historical] What I would explicitly avoid
- No big-bang migration of Tycho + RCP + Java + mac-native fragments in one shot.
- No claim that `2026-03` is “done” if the app still ships `x86_64` browser or AStyle fragments on macOS.
- No `Java 25` commitment until the codebase is already green on the modernized RCP stack.
- No keeping long-term hand-maintained version skew inside `feature.xml` unless a specific override is documented and tested.
- No direct `Tycho 2.2.0 -> 5.0.2` jump unless a short spike proves it is genuinely low-risk.

## [Historical] Friend review - skeptical critique
A cautious reviewer would push back on one point: aiming for both `RCP 2026-03` and `Java 25` as a single declared destination is probably too ambitious for a Tycho/OSGi product with vendored p2 repositories and custom native fragments. The safer interpretation of “most current possible” is:
- **commit to `RCP 2026-03`,**
- **stabilize on `Java 21` first,**
- **treat `Java 25` as a bonus hop only if it is boring.**

That reviewer would also insist that native mac cleanup is not a side quest. In this repo, it is part of platform correctness because the product still carries explicit mac-native fragments in feature composition.

