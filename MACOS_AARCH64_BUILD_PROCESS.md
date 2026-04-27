# Modelio macOS aarch64 Build Process

This document describes the current **native macOS Apple Silicon (`macosx/cocoa/aarch64`)** build flow for this repository.

It is intended as a practical map from:
- source inputs,
- to intermediate build artifacts,
- to the final packaged Modelio application.

The goal is to avoid future guesswork about where each stage writes its outputs.

## 1. Build topology

The repo is a Tycho/Eclipse RCP monorepo.

The top-level staged build entrypoint is:
- `AGGREGATOR/pom.xml`

That aggregator runs the build in this order:
1. `AGGREGATOR/doc`
2. `AGGREGATOR/prebuild`
3. `AGGREGATOR/plugins`
4. `AGGREGATOR/features`
5. `AGGREGATOR/products`

Relevant files:
- `AGGREGATOR/pom.xml`
- `AGGREGATOR/prebuild/pom.xml`
- `AGGREGATOR/plugins/pom.xml`
- `AGGREGATOR/features/pom.xml`
- `AGGREGATOR/features/opensource/pom.xml`
- `AGGREGATOR/products/pom.xml`
- `products/pom.xml`
- `products/modelio-os.product`

## 2. Canonical macOS aarch64 command sequence

Before running any Maven command in this document, export the current build JDK:

```zsh
export JAVA_HOME=/Library/Java/JavaVirtualMachines/temurin-21.jdk/Contents/Home
```

Current validated toolchain split:
- build JDK: `Java 21` (required by `Tycho 5.0.2`)
- product launcher metadata: `Java 21`
- bundled runtime note: the currently validated macOS `aarch64` app does **not** materialise a repo-owned JRE directory, and active `openjdk-jre11` target wiring has been removed from this supported path

### 2.1 JNA status

The Apple Silicon build no longer requires an external JNA source checkout as a manual prerequisite.

The active Slice A wiring now consumes the upstream `2026-03` JNA bundles directly from:
- `dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03/plugins/`

The retired repo-owned JNA overlay is no longer part of the working tree. If JNA ever needs refreshing again, mirror the required upstream bundles directly into `dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03/plugins/` alongside the existing Slice A audit artefacts.

The active upstream RCP baseline path is the one used by:
- `pom.xml`
- `dev-platform/rcp-target/rcp.target`
- `dev-platform/rcp-target/rcp_debug.target`

### 2.2 Retired JNA overlay note

There is no longer a repo-owned JNA overlay project on the supported path.

The current maintenance rule is simple:
- keep the active JNA payload aligned with the vendored `eclipse-2026-03` baseline,
- if a future refresh is needed, mirror the required bundles directly into `dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03/plugins/`,
- then regenerate the Slice A audit artefacts under `dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03/`.

### 2.3 Validate the target definition

```zsh
cd /Users/david/IdeaProjects/Modelio
mvn -f /Users/david/IdeaProjects/Modelio/AGGREGATOR/prebuild/pom.xml -Pplatform.mac.aarch64 verify
```

This standalone `verify` form is enough when you only want to validate the target definition.
The current prebuild reactor validates the cleaned `eclipse-2026-03`-only target wiring directly; it no longer depends on the legacy, French-localisation, or JNA fallback repositories for the supported Apple Silicon path.
If you are driving the build as separate IntelliJ Maven targets with a fresh scratch local repository,
use the split scratch sequence in section `2.7` instead so the generated target artifact is installed for later stages.

### 2.4 Build plugins

```zsh
cd /Users/david/IdeaProjects/Modelio
mvn -f /Users/david/IdeaProjects/Modelio/AGGREGATOR/plugins/pom.xml -Pplatform.mac.aarch64 verify
```

This standalone `verify` form is enough when you only want to validate plugin compilation.
If later reactors (`features`, `doc`, `products`) will run separately against a scratch local repository,
the plugins stage must use `install` as shown in section `2.7`.

### 2.5 Build features

```zsh
cd /Users/david/IdeaProjects/Modelio
mvn -f /Users/david/IdeaProjects/Modelio/AGGREGATOR/features/opensource/pom.xml -Pplatform.mac.aarch64 verify
```

As with plugins, this standalone `verify` form is fine for isolated validation.
For split IntelliJ scratch builds, use `install` so the produced features are visible to the later `products` stage.

### 2.6 Build the full staged product in one reactor

The simplest complete rebuild from zero is a single full reactor run with a dedicated scratch local repository:

```zsh
cd /Users/david/IdeaProjects/Modelio
mvn -Dmaven.repo.local=/Users/david/IdeaProjects/Modelio/tmp/m2-scratch -f /Users/david/IdeaProjects/Modelio/AGGREGATOR/pom.xml -Pplatform.mac.aarch64,product.org clean package
```

This remains the simplest one-line command when the goal is:
- resolve the target,
- build plugins,
- build features,
- build documentation features,
- materialize the final product.

However, the split staged workflow in section `2.7` remains the currently validated correctness-first path for scratch rebuilds.

After the SWT-resolution fix on `2026-04-17`, this one-shot `AGGREGATOR/pom.xml` path was also revalidated from a fresh local Maven repository.

### 2.7 Split scratch build from IntelliJ Maven targets

When the build is driven as separate IntelliJ Maven targets, use a shared scratch local repository for every stage in the same build cycle:
- `/Users/david/IdeaProjects/Modelio/tmp/m2-scratch`

Delete that directory before starting a fresh cycle:

```zsh
rm -rf /Users/david/IdeaProjects/Modelio/tmp/m2-scratch
```

Important validated rule for split reactors:
- producer stages must use `install`
- the final `products` stage uses `package`

This is required because later reactors resolve earlier outputs through Maven coordinates:
- `AGGREGATOR/prebuild` produces `org.modelio:rcp:target:5.4.1-SNAPSHOT`
- `AGGREGATOR/plugins` produces plugin IUs needed by `features`
- `AGGREGATOR/features/opensource` and `AGGREGATOR/doc` produce feature IUs needed by `products`

Validated IntelliJ Maven target order:

1. `Modelio - Prebuild From Scratch`
   ```text
   -Dmaven.repo.local=/Users/david/IdeaProjects/Modelio/tmp/m2-scratch -Pplatform.mac.aarch64 -f /Users/david/IdeaProjects/Modelio/AGGREGATOR/prebuild/pom.xml clean install
   ```
2. `Modelio - Plugins From Scratch`
   ```text
   -Dmaven.repo.local=/Users/david/IdeaProjects/Modelio/tmp/m2-scratch -Pplatform.mac.aarch64 -f /Users/david/IdeaProjects/Modelio/AGGREGATOR/plugins/pom.xml clean install
   ```
3. `Modelio - Features From Scratch`
   ```text
   -Dmaven.repo.local=/Users/david/IdeaProjects/Modelio/tmp/m2-scratch -Pplatform.mac.aarch64 -f /Users/david/IdeaProjects/Modelio/AGGREGATOR/features/opensource/pom.xml clean install
   ```
4. `Modelio - Docs From Scratch`
   ```text
   -Dmaven.repo.local=/Users/david/IdeaProjects/Modelio/tmp/m2-scratch -Pplatform.mac.aarch64 -f /Users/david/IdeaProjects/Modelio/AGGREGATOR/doc/pom.xml clean install
   ```
5. `Modelio - Products From Scratch`
   ```text
   -Dmaven.repo.local=/Users/david/IdeaProjects/Modelio/tmp/m2-scratch -Pplatform.mac.aarch64,product.org -f /Users/david/IdeaProjects/Modelio/AGGREGATOR/products/pom.xml clean package
   ```

Notes:
- `AGGREGATOR/doc` is required before `products` because `products/modelio-os.product` includes `org.modelio.documentation.modeler.feature`.
- `product.org` is required for product materialization; without it, the `products` build may still create repository outputs under `products/target/`, but it will not produce the launchable `.app` bundle.
- In IntelliJ, either keep the full Maven invocation in one command-line field or split it cleanly across the IDE fields without duplicating `-P`, `-f`, or `-Dmaven.repo.local`.
- The current native flow no longer depends on an external JNA checkout.
- The retired repo-owned JNA overlay is no longer part of the supported maintenance workflow.

## 3. How the target platform is assembled

### 3.1 Root Tycho target selection

The root `pom.xml` tells Tycho to use the local target-definition artifact:
- groupId: `org.modelio`
- artifactId: `rcp`
- version: `5.4.1-SNAPSHOT`

Relevant file:
- `pom.xml`

The target-definition project is:
- `dev-platform/rcp-target/pom.xml`

It validates:
- `dev-platform/rcp-target/rcp.target`

### 3.2 Target input locations

The target definition (`dev-platform/rcp-target/rcp.target`) pulls from local directory repositories.

Key macOS aarch64-relevant inputs are:
- `dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03`
- `dev-platform/rcp-target/javax/jaxb`
- `dev-platform/rcp-target/modelio-integ/**`
- `dev-platform/rcp-target/apache/**`
- `dev-platform/rcp-target/org.eclipse/**`
- `dev-platform/rcp-target/tmatesoft/svnkit-1.10.9`
- `dev-platform/rcp-target/org.slf4j/slf4j`
- `dev-platform/rcp-target/ch.qos/logback`

Relevant files:
- `dev-platform/rcp-target/rcp.target`
- `dev-platform/rcp-target/rcp_debug.target`
- `pom.xml`
- `maven/modelio-parent/pom.xml`

The current normalized contract is:
- the target-definition files and both shared parent POMs point at the same `eclipse-2026-03` upstream baseline plus the same companion vendored repositories under `dev-platform/rcp-target/**`;
- the supported macOS `aarch64` path no longer carries active `openjdk-jre11` target wiring;
- the supported macOS `aarch64` path no longer carries active `eclipse/`, `eclipse-fr/`, or `jna/repository/` fallback wiring;
- the retired `dev-platform/rcp-target/rcp-eclipse/eclipse/`, `eclipse-fr/`, and `jna/` directories have been removed from the working tree;
- the packaged app now validates with Java 21 launcher metadata in `products/modelio-os.product` / `modelio.ini`.
- platform-specific launcher fragments, SWT fragments, and JNA bundles now resolve from `dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03` itself.

### 3.3 Additive p2 overlays

For the supported Apple Silicon path there are now **no active additive RCP overlays** in the target or shared Maven repository wiring.

The launcher fragments, macOS native fragments, and JNA bundles required by the product are resolved directly from:
- `dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03`

The older `eclipse/`, `eclipse-fr/`, and `jna/` directories have been retired from the tree. The remaining historical Apple Silicon helper directories are now limited to `launcher-arm64/` and `macos-arm64/`, and they are not part of the active build path.

### 3.4 macOS aarch64 SWT guardrail

The root `pom.xml` `platform.mac.aarch64` profile now explicitly requires:
- `org.eclipse.swt.cocoa.macosx.aarch64` `3.133.0.v20260225-1014`

Reason:
- the resolved `org.eclipse.swt` base bundle is only a stub jar for compilation purposes;
- the actual widget classes (`Control`, `Shell`, `Browser`, etc.) come from the platform fragment;
- without an explicit Apple Silicon SWT fragment requirement, fresh scratch builds could resolve `org.eclipse.swt` without also mirroring the macOS `aarch64` SWT fragment, which broke compilation in `org.modelio.platform.rcp`.

The current checked build therefore treats the SWT fragment as a deterministic part of the Apple Silicon target contract, not as an optional side effect of p2 resolution.

## 4. JNA transition note

Earlier Apple Silicon enablement work needed a repo-owned JNA overlay because the older vendored baseline did not provide a suitable native JNA line for the supported product path.

The feature that had to be updated was:
- `features/opensource/org.modelio.e4.rcp/feature.xml`

That feature now requests:
- `com.sun.jna 5.18.1.v20251001-0800`
- `com.sun.jna.platform 5.18.1`

The active `eclipse-2026-03` baseline now supplies those bundles directly, so the supported product path no longer depends on a repo-owned JNA overlay.

The generated macOS aarch64 product is expected to ship:
- `Contents/Eclipse/plugins/com.sun.jna_5.18.1.jar`
- `Contents/Eclipse/plugins/com.sun.jna.platform_5.18.1.jar`

## 5. Plugin stage outputs

The plugin stage is driven by:
- `AGGREGATOR/plugins/pom.xml`

It delegates to plugin-family aggregators:
- `AGGREGATOR/plugins/core`
- `AGGREGATOR/plugins/platform`
- `AGGREGATOR/plugins/app`
- `AGGREGATOR/plugins/uml`
- `AGGREGATOR/plugins/bpmn`
- `AGGREGATOR/plugins/plugdules`

Each plugin module writes its own normal Tycho `target/` directory under its module.

Example pattern:
- `modelio/core/core.kernel/target/`
- `modelio/platform/platform.ui/target/`
- `modelio/app/app.ui/target/`

These plugin outputs are reactor inputs for the later feature stage.

## 6. Feature stage outputs

The feature stage is driven by:
- `AGGREGATOR/features/pom.xml`
- `AGGREGATOR/features/opensource/pom.xml`

The feature aggregation is important because many feature builds require the plugin reactor outputs to already exist.

Example feature modules:
- `features/opensource/org.modelio.e4.rcp`
- `features/opensource/org.modelio.platform.feature`
- `features/opensource/org.modelio.rcp`

Each feature writes a normal Tycho `target/` directory.

Example:
- `features/opensource/org.modelio.e4.rcp/target/`

That directory contains the packaged feature jar and p2 metadata generated for the feature.

## 7. Product packaging stage

### 7.1 Product identity

The product definition is:
- `products/modelio-os.product`

Important identifiers:
- product UID: `org.modelio.product`
- product id: `org.modelio.app.ui.modelio`
- application: `org.eclipse.e4.ui.workbench.swt.E4Application`

The product is feature-based (`useFeatures="true"`), not plugin-list based.

### 7.2 Product build profiles

Relevant profiles in `products/pom.xml` are:
- `product.org`
- `platform.mac.aarch64`
- `repositoryP2`

For the native Apple Silicon app build, the key combination is:
- `product.org,platform.mac.aarch64`

### 7.3 Main product output directory

The product build writes under:
- `products/target/`

This directory contains both:
- intermediate packaging artifacts,
- final packaged products.

## 8. Product output map: beginning to final app

This is the directory map to check first.

### 8.1 Active baseline inputs

For the supported Apple Silicon path, inspect the active vendored baseline first:
- `dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03/`

Important payload now expected there includes:
- `plugins/com.sun.jna_5.18.1.v20251001-0800.jar`
- `plugins/com.sun.jna.platform_5.18.1.jar`
- `plugins/org.eclipse.equinox.launcher.cocoa.macosx.aarch64_1.2.1400.v20250801-0854.jar`
- `plugins/org.eclipse.swt.cocoa.macosx.aarch64_3.133.0.v20260225-1014.jar`

The retired `eclipse/`, `eclipse-fr/`, and `jna/` directories are no longer present. If you need historical context, the remaining background-only helper directories are `launcher-arm64/` and `macos-arm64/`, but they are no longer primary lookup points for the active product path.

### 8.2 Product packaging intermediates

Under `products/target/` you will see directories such as:
- `org.eclipse.equinox.executable-3.8.1000.v20200915-1508/`
- `p2agent/`
- `targetPlatformRepository/`
- `repository/`
- `products/`

These are **not all final deliverables**.

#### `products/target/org.eclipse.equinox.executable-.../`
This is an intermediate Tycho/Eclipse packaging area created while materializing the product.

It may contain upstream executable rootfiles such as:
- `bin/cocoa/macosx/x86_64/Eclipse.app`

This does **not** mean the final product is Intel.
It is an intermediate unpacked executable feature.

#### `products/target/p2agent/`
This is p2 director/agent working state used during product materialization.

#### `products/target/targetPlatformRepository/`
This is Tycho/director target-platform staging metadata used during packaging.

#### `products/target/repository/`
This is a p2 repository output area.
Its main use depends on the selected profile.
It becomes more important when building with `repositoryP2`.

### 8.3 Final packaged products

The final materialized products live under:
- `products/target/products/`

For the native Apple Silicon build, the final app bundle is:
- `products/target/products/org.modelio.product/macosx/cocoa/aarch64/Modelio.app`

The final archived product is:
- `products/target/products/org.modelio.product-macosx.cocoa.aarch64.tar.gz`

These are the directories/files to inspect first when you need the actual end product.

If `products/target/` only contains repository-style outputs such as `repository/`, `p2content.xml`, `p2artifacts.xml`, `targetPlatformRepository/`, and `products-5.4.1-SNAPSHOT.zip`, then the last `products` run did not materialize the macOS product bundle. In the validated native flow, that usually means the `product.org` profile was not active.

## 9. Final generated bundle layout (current actual state)

Inside the generated bundle directory:
- `products/target/products/org.modelio.product/macosx/cocoa/aarch64/Modelio.app/Contents/`

the current checked build produces:
- `Contents/Eclipse/`
- `Contents/Info.plist`
- `Contents/MacOS/modelio`
- `Contents/Resources/modelio.icns`

and inside that Eclipse payload:
- `Contents/Eclipse/plugins/`
- `Contents/Eclipse/configuration/`
- `Contents/Eclipse/modelio.ini`

The current checked build now automatically applies the checked-in macOS wrapper patch during `product.org` packaging.

That means the generated `.app` directory is no longer just an Eclipse payload in an app-shaped folder; it now contains the normal wrapper files that macOS expects.

The current macOS packaging also keeps the human-facing bundle name stable as `Modelio.app` and stores the trackable version in the usual macOS metadata fields inside `Contents/Info.plist`:
- `CFBundleShortVersionString` for the marketing version (`5.4.1`)
- `CFBundleVersion` for the concrete packaged build version

The packaged plugin directory is still the most reliable place to confirm what was actually shipped.

Examples confirmed in the current native build:
- `org.eclipse.swt.cocoa.macosx.aarch64_3.133.0.v20260225-1014.jar`
- `org.eclipse.equinox.launcher.cocoa.macosx_1.2.1400.v20250801-0854/.../eclipse_*.so`
- `com.sun.jna_5.18.1.jar`
- `com.sun.jna.platform_5.18.1.jar`

## 10. How to start the current generated output

### 10.1 Why the bundle now starts like a normal macOS app

macOS does not launch an `.app` just because a directory ends with `.app`.
A normal app bundle also needs:
- an `Info.plist` in `Contents/`
- a `CFBundleExecutable` entry inside that plist
- the actual executable file in `Contents/MacOS/`

The current generated output now includes those wrapper files, so Finder and `open` have a normal macOS app entrypoint to execute.

If you type the `.app` path directly into `zsh`, the shell will report **permission denied** because `Modelio.app` is a directory bundle, not a Mach-O executable file. In Terminal, use one of these instead:

```zsh
open "/Users/david/IdeaProjects/Modelio/products/target/products/org.modelio.product/macosx/cocoa/aarch64/Modelio.app"
```

or:

```zsh
"/Users/david/IdeaProjects/Modelio/products/target/products/org.modelio.product/macosx/cocoa/aarch64/Modelio.app/Contents/MacOS/modelio"
```

### 10.1.1 macOS launch-services failure that was diagnosed in this repo

One important failure mode that was reproduced during this work was:
- `RBSRequestErrorDomain Code=5 "Launch failed"`
- with underlying `NSPOSIXErrorDomain Code=163` / `Launchd job spawn failed`

In the checked build history for this repo, that failure was traced to the generated bundle being modified after wrapper files were copied in, without re-signing the final `.app`, and with a residual quarantine attribute still present on the copied launcher.

The concrete symptoms that were verified were:
- `codesign --verify --deep --strict` reported `invalid Info.plist (plist or signature have been modified)`
- `Contents/MacOS/modelio` still had `com.apple.quarantine`

The current post-processing step now clears quarantine on the generated app bundle and then performs an ad-hoc re-sign of the final `.app` after `Info.plist`, launcher, and icon patching.

As a result, a plain:

```zsh
open "/Users/david/IdeaProjects/Modelio/products/target/products/org.modelio.product/macosx/cocoa/aarch64/Modelio.app"
```

now returns cleanly in the validated local build instead of failing immediately in LaunchServices.

### 10.2 Where is the Eclipse payload relative to the macOS wrapper?

The generated product still contains the **Eclipse/OSGi installation payload** under:
- `Contents/Eclipse/`

The file:
- `Contents/Eclipse/modelio.ini`

is **not** the macOS executable. It is an Equinox/Eclipse launcher configuration file that tells the launcher jar:
- which startup jar to use,
- which native launcher fragment directory to use,
- which JVM arguments to pass.

In other words:
- `modelio.ini` is configuration,
- while `Contents/MacOS/modelio` is the wrapper executable.

### 10.3 Tested manual launch path

Although the generated bundle is now wrapper-complete, the Eclipse payload inside it can still be started manually with Java when you want lower-level debugging.

Use the same Java 21 toolchain as the normal build path:

```zsh
cd "/Users/david/IdeaProjects/Modelio/products/target/products/org.modelio.product/macosx/cocoa/aarch64/Modelio.app/Contents/Eclipse"

"$JAVA_HOME/bin/java" \
  -Xms512m \
  -Xmx2048m \
  -Dpython.console.encoding=UTF-8 \
  -Dosgi.requiredJavaVersion=21 \
  --add-modules=ALL-SYSTEM \
  -XstartOnFirstThread \
  -Dorg.eclipse.swt.internal.carbon.smallFonts \
  -jar plugins/org.eclipse.equinox.launcher_1.7.100.v20251111-0406.jar \
  -consoleLog \
  -clean \
  -configuration configuration \
  -data /Users/david/IdeaProjects/Modelio/.runtime-jar-data
```

This was also verified in a local smoke-launch run. The observed results were:
- `BootLoader constants: OS=macosx, ARCH=aarch64, WS=cocoa`
- Modelio startup messages
- no `com.sun.jna` / `org.eclipse.urischeme` unresolved-bundle failure

The helper timed out after startup because it was intentionally run under a timeout, not because startup failed.

### 10.4 What to inspect to launch manually

The two most important files are:
- `Contents/Eclipse/modelio.ini`
- `Contents/Eclipse/configuration/config.ini`

These describe:
- the Equinox launcher jar,
- the native launcher fragment directory,
- the OSGi configuration area,
- the OSGi data area.

The current wrapper patch also inserts an explicit:
- `-configuration ../Eclipse/configuration`

into `Contents/Eclipse/modelio.ini` so that the native wrapper starts from the app-local Eclipse configuration rather than reusing an older stale user-cache configuration by accident.

## 11. Final Apple Silicon verification (current generated payload)

### 11.1 JNA check

In the generated product, confirm these exist under:
- `Contents/Eclipse/plugins/`

Expected:
- `com.sun.jna_5.18.1.jar`
- `com.sun.jna.platform_5.18.1.jar`

### 11.2 ARM launcher fragment check

In the generated product, confirm the ARM launcher fragment exists under:
- `Contents/Eclipse/plugins/org.eclipse.equinox.launcher.cocoa.macosx_1.2.1400.v20250801-0854/`

Historical evidence files in this repo such as `diagnostics/macos-aarch64/launcher-filetypes.txt` and `diagnostics/macos-aarch64/final-aarch64-launcher-check.txt` remain useful as background verification artifacts, but the checked-in build now generates `Contents/MacOS/modelio` directly.

### 11.3 Wrapper signing and quarantine check

For the current checked macOS aarch64 build, the most useful wrapper-level verification commands are:

```zsh
plutil -lint "/Users/david/IdeaProjects/Modelio/products/target/products/org.modelio.product/macosx/cocoa/aarch64/Modelio.app/Contents/Info.plist"

codesign --verify --deep --strict --verbose=4 \
  "/Users/david/IdeaProjects/Modelio/products/target/products/org.modelio.product/macosx/cocoa/aarch64/Modelio.app"

xattr -lr \
  "/Users/david/IdeaProjects/Modelio/products/target/products/org.modelio.product/macosx/cocoa/aarch64/Modelio.app"
```

What was actually verified in this repo after the wrapper/signing fix:
- `Info.plist` is valid
- `codesign --verify --deep --strict` succeeds on the final `.app`
- no `com.apple.quarantine` attribute remains on the generated bundle

Important nuance:
- the current build uses an **ad-hoc** signature to keep the local generated app launchable after post-processing
- `codesign --verify` success means the bundle is internally consistent and launchable for local development
- this is **not** the same thing as notarization or full Gatekeeper acceptance for external distribution

In other words, treat the current checked build as:
- locally signed well enough for development launch on the build machine
- but not automatically equivalent to a notarized release artifact

## 12. About the x86_64 `org.eclipse.equinox.executable` staging tree

You may see this intermediate directory during packaging:
- `products/target/org.eclipse.equinox.executable-3.8.1000.v20200915-1508/bin/cocoa/macosx/x86_64/Eclipse.app`

That path comes from the upstream executable feature stored in:
- the matching `org.eclipse.equinox.executable_*` feature inside `dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03/features/`

The staging tree exists because Tycho unpacks the executable feature during product assembly.

It is **not** the final product.

The correct final product to inspect is instead:
- `products/target/products/org.modelio.product/macosx/cocoa/aarch64/Modelio.app`

If you need to know whether the actual shipped product is ARM or Intel, always inspect the final app bundle, not the unpacked `org.eclipse.equinox.executable-*` staging area.

## 13. Checked-in post-processing helper

This repo contains a standalone helper:
- `products/patch_macos_aarch64_app.py`

That helper script writes macOS app wrapper files into the final bundle, using:
- preserved Intel `Info.plist`
- preserved ARM launcher rootfiles
- the repo icon

It targets:
- `products/target/products/org.modelio.product/macosx/cocoa/aarch64/Modelio.app/Contents`

If the final bundle contains:
- `Contents/MacOS/modelio`
- `Contents/Info.plist`
- `Contents/Resources/modelio.icns`

then this helper has been applied by the checked-in Maven packaging flow for the macOS aarch64 `product.org` build.

Important current finding:
- `products/pom.xml` now invokes `products/patch_macos_aarch64_app.py` during `product.org` packaging through `maven-antrun-plugin`.

Therefore, the current checked build process should be treated as producing:
- a valid Eclipse payload under `Contents/Eclipse/`
- and a complete macOS wrapper under `Contents/Info.plist`, `Contents/MacOS/`, and `Contents/Resources/` by default.
- and a `modelio.ini` launcher configuration that points the native wrapper back to the app-local `Contents/Eclipse/configuration` directory rather than an older stale user-cache configuration
- and a final app bundle that is de-quarantined and ad-hoc signed after wrapper patching

The helper now performs these macOS-specific post-processing actions in one place:
- copy launcher/icon resources into the generated `.app`
- rewrite `Info.plist` with `Modelio` bundle naming and current version fields
- inject the app-local `-configuration` entry into `modelio.ini`
- clear `com.apple.quarantine` recursively on the generated app
- re-sign the final `.app` with an ad-hoc signature

## 14. Practical “look here first” checklist

When debugging or locating outputs, use this order.

### Target and overlays
1. `dev-platform/rcp-target/rcp.target`
2. `dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03/`
3. `dev-platform/rcp-target/rcp-eclipse/launcher-arm64/` and `dev-platform/rcp-target/rcp-eclipse/macos-arm64/` (historical reference only)
4. retired directories `dev-platform/rcp-target/rcp-eclipse/eclipse/`, `eclipse-fr/`, and `jna/` are no longer present and should not be recreated for the supported path

### Plugin and feature outputs
5. module-local `target/` directories under `modelio/**` and `features/**`

### Product packaging
6. `products/target/products/`
7. `products/target/products/org.modelio.product/macosx/cocoa/aarch64/Modelio.app`
8. `products/target/products/org.modelio.product-macosx.cocoa.aarch64.tar.gz`
9. `products/patch_macos_aarch64_app.py`

### Manual launch/debug of the current generated payload
10. `products/target/products/org.modelio.product/macosx/cocoa/aarch64/Modelio.app/Contents/Eclipse/modelio.ini`
11. `products/target/products/org.modelio.product/macosx/cocoa/aarch64/Modelio.app/Contents/Eclipse/configuration/config.ini`
12. `~/.modelio/5.4/opensource-cache/conf`
13. `~/.modelio/5.4/opensource-cache/data/.metadata/.log`

### Wrapper/signature verification
14. `products/target/products/org.modelio.product/macosx/cocoa/aarch64/Modelio.app/Contents/Info.plist`
15. `codesign --verify --deep --strict --verbose=4 .../Modelio.app`
16. `xattr -lr .../Modelio.app`

### Only after that, inspect intermediates
17. `products/target/org.eclipse.equinox.executable-*`
18. `products/target/repository/`
20. `products/target/targetPlatformRepository/`
21. `products/target/p2agent/`

## 15. Recommended future workflow

If you need the full native macOS aarch64 product again, use this order:

```zsh
rm -rf /Users/david/IdeaProjects/Modelio/tmp/m2-scratch

cd /Users/david/IdeaProjects/Modelio
mvn -Dmaven.repo.local=/Users/david/IdeaProjects/Modelio/tmp/m2-scratch -f /Users/david/IdeaProjects/Modelio/AGGREGATOR/prebuild/pom.xml -Pplatform.mac.aarch64 clean install
mvn -Dmaven.repo.local=/Users/david/IdeaProjects/Modelio/tmp/m2-scratch -f /Users/david/IdeaProjects/Modelio/AGGREGATOR/plugins/pom.xml -Pplatform.mac.aarch64 clean install
mvn -Dmaven.repo.local=/Users/david/IdeaProjects/Modelio/tmp/m2-scratch -f /Users/david/IdeaProjects/Modelio/AGGREGATOR/features/opensource/pom.xml -Pplatform.mac.aarch64 clean install
mvn -Dmaven.repo.local=/Users/david/IdeaProjects/Modelio/tmp/m2-scratch -f /Users/david/IdeaProjects/Modelio/AGGREGATOR/doc/pom.xml -Pplatform.mac.aarch64 clean install
mvn -Dmaven.repo.local=/Users/david/IdeaProjects/Modelio/tmp/m2-scratch -f /Users/david/IdeaProjects/Modelio/AGGREGATOR/products/pom.xml -Pplatform.mac.aarch64,product.org clean package
```

If you do not need split IntelliJ stages, the simpler one-shot alternative is still:

```zsh
cd /Users/david/IdeaProjects/Modelio
mvn -Dmaven.repo.local=/Users/david/IdeaProjects/Modelio/tmp/m2-scratch -f /Users/david/IdeaProjects/Modelio/AGGREGATOR/pom.xml -Pplatform.mac.aarch64,product.org clean package
```

Then inspect:
- `products/target/products/org.modelio.product/macosx/cocoa/aarch64/Modelio.app`
- `products/target/products/org.modelio.product-macosx.cocoa.aarch64.tar.gz`

If you need to **run** the generated output normally, launch the `.app` bundle or execute `Contents/MacOS/modelio` directly.

If you need lower-level startup debugging, use the manual Java launch path from section `10.3`.

If a future JNA refresh is required, mirror the replacement bundles directly into `dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03/plugins/` and then regenerate the Slice A audit artefacts.

## 16. Summary

The most important path to remember is:

1. validate the target,
2. build plugins,
3. build features,
4. package products,
5. inspect the generated product here:
   - `products/target/products/org.modelio.product/macosx/cocoa/aarch64/Modelio.app`

Current important distinction:
- the generated `.app` contains the Eclipse payload under `Contents/Eclipse/`
- and now also contains the standard macOS wrapper files under `Contents/Info.plist`, `Contents/MacOS/`, and `Contents/Resources/`
- and the wrapper patch now clears quarantine and ad-hoc signs the final bundle after patching
- therefore the default checked build is now Finder/`open` launchable in the normal macOS way for local development on the validated machine

If you are trying to answer “where is the final Modelio app?”, the answer is:
- `products/target/products/org.modelio.product/macosx/cocoa/aarch64/Modelio.app`

If you are trying to answer “how do I start the current generated output?”, the answer is:
- launch `products/target/products/org.modelio.product/macosx/cocoa/aarch64/Modelio.app`
- or run `Contents/MacOS/modelio` directly
- or, for low-level debugging, start the Eclipse payload manually using the Java command documented in section `10.3`

If you are trying to answer “where is the packaged archive?”, the answer is:
- `products/target/products/org.modelio.product-macosx.cocoa.aarch64.tar.gz`

