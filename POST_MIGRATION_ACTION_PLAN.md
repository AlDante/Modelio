# Post-migration action plan

## Status summary

As of **2026-05-06**, the supported macOS Apple Silicon (`platform.mac.aarch64,product.org`) migration is **complete at the plan-of-record level**.

What is already true for the supported path:
- fresh-scratch staged validation is green;
- the one-shot acceptance build from `AGGREGATOR/pom.xml` is green;
- packaged-app Apple Silicon contract validation is green;
- logging-stack validation is green;
- runtime logging smoke is green;
- diagram-editor smoke is green.

This means there is **no mandatory migration work left** for the supported path.

What remains is optional follow-up aimed at one or more of:
- reducing future upgrade fragility;
- simplifying maintenance;
- aligning documentation with the current implementation;
- removing small leftover inconsistencies.

## How to read this document

- **Priority 1** items are the most worthwhile next cleanups.
- **Priority 2** items are maintainability improvements with clear long-term value.
- **Priority 3** items are larger compatibility-debt reductions that should be treated as optional hardening, not required migration work.
- **Priority 4** items are only worth doing if a broader modernisation wave is explicitly desired.

## Recommendation in one sentence

The migration can be considered complete for the supported path; if more work is done, it should now be framed as **optional cleanup and future-proofing**, not as unfinished migration engineering.

---

## Priority 1 — recommended cleanup next

### 1. Align migration documentation with the current logging implementation

**Status**

Completed on **2026-05-06**.

**Why this is first**

Some documentation still refers to the older reflective Logback bootstrap fallback as if it still exists or still needs later review, but the codebase now uses the newer OSGi-native startup ordering and provider-wait approach.

**Representative files**
- `MODERNIZATION_PLAN.md`
- `SLF4J_LOGBACK_MIGRATION_PLAN.md`

**Suggested work**
- remove stale references to the reflective logging-bootstrap fallback;
- describe the current implementation instead:
  - explicit `org.apache.aries.spifly.dynamic.bundle` inclusion,
  - ordered startup in `platform.utils`,
  - bounded wait for `org.slf4j.spi.SLF4JServiceProvider`,
  - repeated green runtime smoke evidence.

**Outcome**
- the active migration documents now describe the current SPI Fly / OSGi-native logging bootstrap path rather than the retired reflective fallback wording.

---

### 2. Tidy `products/modelio-os.product`

**Status**

Completed on **2026-05-07**.

**Completed work**
- removed the duplicate `org.modelio.functions.modelviewtemplate` feature entry;
- corrected `osgi.sharedConfiguration.area.readOnly`;
- retired the obsolete Apple AWT flags:
  - `-Dapple.awt.graphics.UseQuartz=true`
  - `-Dcom.apple.smallTabs=true`
- retired `-Dorg.eclipse.swt.internal.carbon.smallFonts` from the supported product definition and packaged-app patch path after a fresh products-stage rebuild plus runtime smoke confirmed that the active Apple Silicon path no longer depends on it.

**Representative file**
- `products/modelio-os.product`

**Expected benefit**
- removes avoidable noise from the product contract;
- reduces the risk of silently ignored properties or obsolete launcher flags.

---

### 3. Simplify and harden `products/pom.xml`

**Status**

Completed on **2026-05-06**.

**Clarification recorded on 2026-05-06**

The earlier note about the shell being flaky applies to **Copilot-driven interactive shell usage**, not to Maven invoking shell commands during the build. Shell execution from Maven is therefore **not a problem in itself**.

**Outcome**

The bulky inline packaging shell payloads have now been extracted into checked-in helper scripts:
- `products/patch_and_archive_macos_aarch64_product.py`
- `products/verify_macos_aarch64_app.py`

`products/pom.xml` now keeps Maven responsible for lifecycle wiring and argument passing, while the multi-step packaging logic lives in reviewable helper scripts.

**Representative file**
- `products/pom.xml`


**Expected benefit**
- clearer product packaging logic;
- easier local debugging and review;
- smaller, less brittle POM diffs in future packaging changes.

---

### 4. Verify that the cleanup leaves the repo English-only

**Status**

Completed on **2026-05-06**.

**Completed work**
- removed the French documentation reactors and source trees from the active Maven build graph;
- retired the French-only docs parent property that existed only to support `nl/fr` documentation generation;
- rechecked that `products/modelio-os.product` already ships only the English documentation feature.
- removed the remaining French runtime resource files under `modelio/`, including `plugin_fr.properties`, `module_fr.properties`, `fragment_fr.properties`, `*_fr.properties`, `*_fr.html`, and CKEditor `fr*.js` files;
- updated the affected `build.properties` files so retired French root resources are no longer packaged by accident.

**Why it matters**

The supported macOS Apple Silicon product path is now aligned with the English-only cleanup work across both the documentation build graph and the runtime resource layer.

**Representative files**
- `doc/plugins/pom.xml`
- `doc/features/pom.xml`
- `modelio/**/build.properties`
- `modelio/platform/platform.ui/rte/ckeditor/**`

**Things to check in the cleanup**
- keep non-English documentation/plugin aggregators retired when they are no longer part of the intended product;
- verify that no `*.nl_fr*` bundles, features, or fragments re-enter the build by accident;
- keep embedded French runtime resources such as `plugin_fr.properties` out of the repository if the English-only policy remains in force;
- confirm that the supported product definition and packaging inputs continue to ship English-only content.

**Current audit note**

As of **2026-05-06**, the documentation build graph no longer contains any `nl_fr` artefacts, and the runtime tree under `modelio/` no longer contains French resource files or CKEditor French translation payloads.

**Expected benefit**
- clearer scope for supported language content;
- less risk of reintroducing retired localisation inputs during future build or product changes.

---

## Priority 2 — useful maintainability improvements

### 5. Reduce duplicated parent-POM truth

**Status**

Partially completed on **2026-05-07**.

**Completed work**
- aligned `maven/modelio-parent/pom.xml` so `modelio.rootFolder` now matches the primary parent (`Modelio 5.4.1`);
- documented that the secondary parent still intentionally resolves `modelio.ws.path` from `ECLIPSE_WS` because the legacy `maven/aggregators/**` entrypoints depend on that behaviour.
- revalidated the legacy `maven/aggregators/prebuild` path against a scratch local repository once the shared `modelio-parent` artefact had been installed, confirming that the `modelio.rootFolder` alignment did not break that supported legacy prebuild entrypoint.
- retired the dead `products/os-archimate` module reference from `maven/aggregators/products/pom.xml`, leaving the legacy products wrapper pointed only at the live `products/` module.
- retired the secondary-parent-only `realtimebuild`, `setversion`, `debug`, and `tests` profiles plus the unused `sonar-maven-plugin` version pin, so the remaining parent divergence is now limited to intentional `ECLIPSE_WS` workspace resolution.

**Why it matters**

There is near-duplicate repository and Tycho configuration in both:
- `pom.xml`
- `maven/modelio-parent/pom.xml`

They are not identical, which creates drift risk.

**Examples of current differences**
- workspace path derivation differs;
- only the secondary parent uses `ECLIPSE_WS`.

**Suggested work**
- identify why both parents still need to exist in their current form;
- consolidate shared repository and Tycho setup where practical;
- document any remaining intentional divergence explicitly;
- revisit whether the legacy `maven/aggregators/**` path can stop depending on `ECLIPSE_WS` without breaking workspace-root resolution.

**Expected benefit**
- less build-configuration drift;
- lower maintenance cost for future target-platform updates.

---

### 6. Resolve the Java-level signalling mismatch in build metadata

**Status**

Partially completed on **2026-05-07**.

**Completed work**
- documented in `pom.xml`, `maven/modelio-parent/pom.xml`, and `doc/parent/pom.xml` that the current `maven.compiler.source` / `maven.compiler.target` values are retained as legacy workspace/build metadata and are not the authoritative runtime contract for the supported Apple Silicon path;
- updated the remaining `modelio/**/.classpath` JRE container metadata from `JavaSE-11` to `JavaSE-21` so Eclipse workspace metadata now matches the supported runtime baseline more closely;
- raised the explicit compiler `source` / `target` pins from 11 to 21 in `modelio/bpmn/bpmn.metamodel.api/pom.xml` and `modelio/bpmn/bpmn.metamodel.implementation/pom.xml`, matching the `JavaSE-21` execution-environment contract those bundles already declared;
- raised the explicit compiler `source` / `target` pins from 11 to 21 in `modelio/core/version/pom.xml` and aligned that module's Eclipse JDT compiler preferences to 21, matching the `JavaSE-21` execution-environment contract it already declared;
- raised the explicit compiler `source` / `target` pins plus the PDE `javacSource` / `javacTarget` metadata from 11 to 21 in `modelio/core/core.project.data`, matching the `JavaSE-21` execution-environment contract that bundle already declared;
- raised the explicit compiler `source` / `target` pins plus the PDE and Eclipse JDT compiler metadata from 11/1.8 to 21 in `modelio/core/core.utils`, matching the `JavaSE-21` execution-environment contract and Java 21 workspace container that bundle already declared;
- raised the explicit compiler `source` / `target` pins plus the PDE `javacSource` / `javacTarget` metadata from 11 to 21 in `modelio/core/core.kernel` and `modelio/core/core.session`, validating that shared dependency boundary on the canonical plugins reactor;
- raised the explicit compiler `source` / `target` pins plus the PDE `javacSource` / `javacTarget` metadata from 11 to 21 in `modelio/core/core.store.exml`, matching the `JavaSE-21` execution-environment contract and Java 21 workspace container that bundle already declared;
- raised the explicit compiler `source` / `target` pins plus the PDE `javacSource` / `javacTarget` metadata from 11 to 21 in `modelio/core/core.project`, `modelio/core/core.metamodel.api`, and `modelio/core/core.metamodel.impl`, matching the `JavaSE-21` execution-environment contract those core bundles already declared;
- revalidated the primary and legacy prebuild/doc entrypoints after that clarification and workspace-metadata alignment change.

**Why it matters**

The supported path now clearly targets Java 21 at runtime and many bundles already declare `Bundle-RequiredExecutionEnvironment: JavaSE-21`, but the shared Maven compiler properties still advertise Java 11 in multiple parent POMs.

**Representative files**
- `pom.xml`
- `maven/modelio-parent/pom.xml`
- `doc/parent/pom.xml`

**Suggested work**
- audit the remaining explicit module-level `source` / `target` 11 compiler pins in runtime plugin POMs;
- if they are no longer required, align them with the current supported Java 21 contract in small separately validated slices, starting with low-fan-in bundles that already declare `JavaSE-21`;
- treat the remaining broad shared bundles as later, higher-risk waves even when they already declare `JavaSE-21`;
- keep using canonical `AGGREGATOR/plugins` validation as the acceptance gate once a slice touches broad core bundles with many downstream consumers;
- otherwise keep the current parent-POM comments so the distinction between module build metadata and the supported runtime contract remains explicit.

**Expected benefit**
- clearer toolchain intent;
- less confusion during future Java or Tycho upgrades.

---

### 7. Modernise the documentation build configuration

**Status**

Partially completed on **2026-05-06**.

**Why it matters**

The docs build works, but it still emits avoidable warnings and relies on older repeated plugin configuration.

**Representative files**
- `doc/parent/pom.xml`
- `doc/plugins/en/documentation.bpmn/pom.xml`
- sibling doc plugin POMs under `doc/plugins/en/` and `doc/plugins/fr/`

**Observed points**
- the Asciidoctor configuration still uses the unsupported `compact` parameter;
- many doc plugin POMs repeated nearly identical plugin setup;
- simple file operations still rely on old Ant invocations.

**Completed work**
- the English documentation plugin POMs now inherit the shared Tycho configuration directly from `doc/parent/pom.xml` instead of repeating the same `tycho-maven-plugin` and `tycho-packaging-plugin` blocks in every child POM.

**Suggested work**
- remove unsupported Asciidoctor parameters;
- centralise shared configuration in `doc/parent/pom.xml`;
- replace simple Ant file operations with standard Maven plugins where practical.

**Expected benefit**
- quieter builds;
- simpler docs maintenance;
- less duplicated configuration.

---

## Priority 3 — optional hardening against future platform changes

### 8. Revisit `GefWorkbenchBridge`

**Why this stands out**

This is the most obviously fragile remaining compatibility shim in the repo.

**Representative file**
- `modelio/app/app.diagram.editor/src/org/modelio/diagram/editor/plugin/GefWorkbenchBridge.java`

**Current behaviour**
- uses `sun.misc.Unsafe`;
- instantiates internal Eclipse workbench classes without constructors;
- writes internal fields reflectively.

**Suggested work**
- keep this as-is unless there is a concrete need to touch it;
- if a future slice targets GEF/E4 cleanup, investigate whether the shim can be removed, narrowed, or version-guarded more explicitly.

**Expected benefit**
- reduced risk during future Eclipse train upgrades.

---

### 9. Reduce dependence on Eclipse internal proxy UI APIs

**Representative files**
- `modelio/platform/platform.preferences/src/org/modelio/platform/preferences/proxy/ProxyPreferencePage.java`
- `modelio/platform/platform.preferences/src/org/modelio/platform/preferences/proxy/ProxyEntriesComposite.java`
- `modelio/platform/platform.preferences/src/org/modelio/platform/preferences/proxy/NonProxyHostsComposite.java`

**Why it matters**

These classes depend on `org.eclipse.ui.internal.net.*` and `org.eclipse.core.internal.net.*`, which makes them sensitive to upstream internal refactors.

**Suggested work**
- review whether equivalent public APIs are now available;
- otherwise consider owning the minimal proxy UI logic locally instead of depending on Eclipse internals.

**Expected benefit**
- lower upgrade fragility in the preferences/UI layer.

---

### 10. Reassess the macOS appearance compatibility layer

**Representative files**
- `modelio/app/app.ui.ext_org/src/org/modelio/app/ui/lifecycle/MacAppearanceSupport.java`
- `products/modelio-os.product`

**Why it matters**

The current fix is pragmatic, but it still relies on reflective access to non-public SWT appearance hooks.

**Suggested work**
- revalidate whether the current light-appearance forcing is still required on the active SWT baseline;
- test whether any of the legacy macOS VM flags can now be removed;
- keep the compatibility layer only where it still provides measurable value.

**Expected benefit**
- smaller macOS-specific maintenance surface;
- less dependence on internal SWT behaviour.

---

### 11. Remove or archive unused experimental reflective utilities

**Representative file**
- `modelio/platform/platform.ui/src/org/modelio/platform/ui/swt/DpiChangeListener.java`

**Why it matters**

This class is marked deprecated, experimental, and appears unused.

**Suggested work**
- delete it if it is truly dead code;
- otherwise move it into a clearly marked legacy or archival location.

**Expected benefit**
- smaller codebase;
- fewer distracting reflective utilities for future reviewers.

---

### 12. Replace the legacy browser-launch helper

**Representative file**
- `modelio/app/app.xmi/src/org/modelio/xmi/util/BareBonesBrowserLaunch.java`

**Why it matters**

This helper still uses very old platform-specific logic, including:
- `com.apple.eio.FileManager` on macOS;
- manual browser probing for historic Unix browsers.

**Suggested work**
- replace it with `java.awt.Desktop` or the relevant Eclipse browser support APIs, subject to UI/runtime constraints.

**Expected benefit**
- removes one of the most visibly outdated utility classes in the repo.

---

## Priority 4 — only if a broader modernisation wave is wanted

### 13. Gradually reduce manual `BundleActivator` usage where there is clear payoff

**Why it matters**

The repo still contains many bundles driven by explicit `BundleActivator` lifecycle code. This is not wrong, but it is older OSGi style and can encourage startup-order coupling.

**Suggested approach**
- do not rewrite stable bundles for the sake of style alone;
- only migrate activator-based code when there is a concrete benefit, such as simpler service registration or easier testing.

---

### 14. Normalise minor naming/version drift in build metadata

**Examples**
- `AGGREGATOR/pom.xml` still uses artifactId `Modelio541`;
- root-folder naming differs between parent POMs.

**Suggested approach**
- only tidy this if it can be done without disturbing existing consumers, scripts, or assumptions.

---

## What should not be treated as required next work

The following are **not** currently recommended as immediate follow-up:
- a broad “upgrade everything again” target-platform slice;
- a repo-wide Declarative Services conversion;
- a blanket removal of all reflective compatibility hooks in one pass;
- a forced Java-language-level uplift everywhere without a narrow scoped reason.

These may become worthwhile later, but they are no longer part of completing the current migration stream.

## Suggested execution order

If optional follow-up is desired, the recommended order is:

1. **Documentation truth pass**
   - update migration/logging documents to reflect the current implementation.
2. **Product hygiene pass**
   - clean `products/modelio-os.product`;
   - simplify `products/pom.xml` by extracting helper scripts.
3. **English-only cleanup pass**
   - keep doc/plugin aggregators and any `*.nl_fr*` artefacts out of the intended build scope;
   - keep French runtime resource payloads out of `modelio/` if the English-only policy remains in force.
4. **Build-maintenance pass**
   - reduce duplicated parent-POM truth;
   - clarify Java-level build signalling;
   - tidy doc-build configuration.
5. **Future-upgrade hardening pass**
   - review `GefWorkbenchBridge`;
   - review internal Eclipse proxy UI usage;
   - review the macOS appearance shim.

## Final recommendation

For the supported macOS Apple Silicon path, the repo can now be considered **migration-complete**.

Further work is optional and should be justified as one of:
- maintenance simplification;
- documentation alignment;
- technical-debt reduction;
- future-upgrade hardening.

That is a healthy place for the project to be.
