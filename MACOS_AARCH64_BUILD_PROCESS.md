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

### 2.1 JNA prerequisite

The macOS aarch64 flow currently depends on a locally built JNA source checkout that is published into a local p2 overlay.

The external checkout used during validation was:
- `/Users/david/IdeaProjects/_external/jna`

The toolchain used was:
- Java 11 from MacPorts/OpenJDK Temurin
- `apache-ant` from MacPorts

Build JNA from the cloned source:

```zsh
cd /Users/david/IdeaProjects/_external/jna
/opt/local/bin/ant -Drelease=true install
```

This installs JNA into the local Maven repository at:
- `/Users/david/.m2/repository/net/java/dev/jna/jna/5.18.1/`
- `/Users/david/.m2/repository/net/java/dev/jna/jna-platform/5.18.1/`

### 2.2 Generate the local JNA p2 overlay

The overlay project is:
- `dev-platform/rcp-target/rcp-eclipse/jna/pom.xml`

Generate its p2 repository:

```zsh
cd /Users/david/IdeaProjects/Modelio/dev-platform/rcp-target/rcp-eclipse/jna
mvn generate-resources
```

This produces the repository at:
- `dev-platform/rcp-target/rcp-eclipse/jna/target/repository/`

Important: the build consumes **`target/repository`**, not the parent `jna/` directory.

### 2.3 Validate the target definition

```zsh
cd /Users/david/IdeaProjects/Modelio
mvn -f /Users/david/IdeaProjects/Modelio/AGGREGATOR/prebuild/pom.xml -Pplatform.mac.aarch64 verify
```

### 2.4 Build plugins

```zsh
cd /Users/david/IdeaProjects/Modelio
mvn -f /Users/david/IdeaProjects/Modelio/AGGREGATOR/plugins/pom.xml -Pplatform.mac.aarch64 verify
```

### 2.5 Build features

```zsh
cd /Users/david/IdeaProjects/Modelio
mvn -f /Users/david/IdeaProjects/Modelio/AGGREGATOR/features/opensource/pom.xml -Pplatform.mac.aarch64 verify
```

### 2.6 Build the full staged product

The full staged native macOS aarch64 build validated during this session was:

```zsh
cd /Users/david/IdeaProjects/Modelio
mvn -f /Users/david/IdeaProjects/Modelio/AGGREGATOR/pom.xml -Pplatform.mac.aarch64,product.org package
```

This is the best single command when the goal is:
- resolve the target,
- build plugins,
- build features,
- materialize the final product.

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
- `dev-platform/rcp-target/rcp-eclipse/eclipse`
- `dev-platform/rcp-target/rcp-eclipse/eclipse-fr`
- `dev-platform/rcp-target/rcp-eclipse/launcher-arm64`
- `dev-platform/rcp-target/rcp-eclipse/macos-arm64`
- `dev-platform/rcp-target/rcp-eclipse/jna/target/repository`
- `dev-platform/rcp-target/rcp-eclipse/swt`
- `dev-platform/pack-resources/openjdk-jre11`

Relevant files:
- `dev-platform/rcp-target/rcp.target`
- `dev-platform/rcp-target/rcp_debug.target`

### 3.3 Additive p2 overlays

The base vendored Eclipse site is supplemented by small local p2 overlays.

#### ARM launcher overlay
Project:
- `dev-platform/rcp-target/rcp-eclipse/launcher-arm64/pom.xml`

Publishes:
- `org.eclipse.equinox.launcher.cocoa.macosx`
- `org.eclipse.equinox.launcher.cocoa.macosx.aarch64`

Repository location:
- `dev-platform/rcp-target/rcp-eclipse/launcher-arm64/`

#### macOS fragment overlay
Project:
- `dev-platform/rcp-target/rcp-eclipse/macos-arm64/pom.xml`

Publishes:
- `org.eclipse.core.filesystem.macosx`
- `org.eclipse.equinox.security.macosx`

Repository location:
- `dev-platform/rcp-target/rcp-eclipse/macos-arm64/`

#### JNA overlay
Project:
- `dev-platform/rcp-target/rcp-eclipse/jna/pom.xml`

Publishes:
- `com.sun.jna`
- `com.sun.jna.platform`

Generated repository location:
- `dev-platform/rcp-target/rcp-eclipse/jna/target/repository/`

## 4. Why the JNA overlay exists

The old vendored Eclipse baseline still contains:
- `com.sun.jna 4.5.1`
- `com.sun.jna.platform 4.5.1`

That version is Intel-only on macOS and does not satisfy Apple Silicon native resolution.

The feature that had to be updated was:
- `features/opensource/org.modelio.e4.rcp/feature.xml`

That feature now requests:
- `com.sun.jna 5.18.1`
- `com.sun.jna.platform 5.18.1`

The generated macOS aarch64 product now ships:
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

### 8.1 Overlay build outputs

#### JNA overlay repository
- `dev-platform/rcp-target/rcp-eclipse/jna/target/repository/`
- files:
  - `artifacts.jar`
  - `content.jar`
  - `plugins/com.sun.jna_5.18.1.jar`
  - `plugins/com.sun.jna.platform_5.18.1.jar`

#### Launcher overlay repository
- `dev-platform/rcp-target/rcp-eclipse/launcher-arm64/`

#### macOS fragment overlay repository
- `dev-platform/rcp-target/rcp-eclipse/macos-arm64/`

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
- `org.eclipse.swt.cocoa.macosx.aarch64_3.120.0.v20220530-1036.jar`
- `org.eclipse.equinox.launcher.cocoa.macosx_1.2.200.v20210527-0259/.../eclipse_11408.so`
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

The following path was tested successfully and the application reached UI startup:

```zsh
cd "/Users/david/IdeaProjects/Modelio/products/target/products/org.modelio.product/macosx/cocoa/aarch64/Modelio.app/Contents/Eclipse"

"/opt/local/Library/Java/JavaVirtualMachines/openjdk11-temurin/Contents/Home/bin/java" \
  -Xms512m \
  -Xmx2048m \
  -Dpython.console.encoding=UTF-8 \
  -Dosgi.requiredJavaVersion=11 \
  --add-modules=ALL-SYSTEM \
  -XstartOnFirstThread \
  -Dorg.eclipse.swt.internal.carbon.smallFonts \
  -jar plugins/org.eclipse.equinox.launcher_1.6.0.v20200915-1508.jar \
  -consoleLog \
  -clean \
  -configuration configuration \
  -data /Users/david/IdeaProjects/Modelio/.runtime-jar-data
```

This was verified by the smoke-launch log in:
- `diagnostics/macos-aarch64/runtime-jar-smoke.log`

That log shows:
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
- `Contents/Eclipse/plugins/org.eclipse.equinox.launcher.cocoa.macosx_1.2.200.v20210527-0259/`

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
- `dev-platform/rcp-target/rcp-eclipse/eclipse/features/org.eclipse.equinox.executable_3.8.1000.v20200915-1508/feature.xml`

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
2. `dev-platform/rcp-target/rcp-eclipse/jna/target/repository/`
3. `dev-platform/rcp-target/rcp-eclipse/launcher-arm64/`
4. `dev-platform/rcp-target/rcp-eclipse/macos-arm64/`

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
12. `diagnostics/macos-aarch64/runtime-jar-smoke.log`
13. `~/.modelio/5.4/opensource-cache/conf`
14. `~/.modelio/5.4/opensource-cache/data/.metadata/.log`

### Wrapper/signature verification
15. `products/target/products/org.modelio.product/macosx/cocoa/aarch64/Modelio.app/Contents/Info.plist`
16. `codesign --verify --deep --strict --verbose=4 .../Modelio.app`
17. `xattr -lr .../Modelio.app`

### Only after that, inspect intermediates
18. `products/target/org.eclipse.equinox.executable-*`
19. `products/target/repository/`
20. `products/target/targetPlatformRepository/`
21. `products/target/p2agent/`

## 15. Recommended future workflow

If you need the full native macOS aarch64 product again, use this order:

```zsh
cd /Users/david/IdeaProjects/_external/jna
/opt/local/bin/ant -Drelease=true install

cd /Users/david/IdeaProjects/Modelio/dev-platform/rcp-target/rcp-eclipse/jna
mvn generate-resources

cd /Users/david/IdeaProjects/Modelio
mvn -f /Users/david/IdeaProjects/Modelio/AGGREGATOR/prebuild/pom.xml -Pplatform.mac.aarch64 verify
mvn -f /Users/david/IdeaProjects/Modelio/AGGREGATOR/plugins/pom.xml -Pplatform.mac.aarch64 verify
mvn -f /Users/david/IdeaProjects/Modelio/AGGREGATOR/features/opensource/pom.xml -Pplatform.mac.aarch64 verify
mvn -f /Users/david/IdeaProjects/Modelio/AGGREGATOR/pom.xml -Pplatform.mac.aarch64,product.org package
```

Then inspect:
- `products/target/products/org.modelio.product/macosx/cocoa/aarch64/Modelio.app`
- `products/target/products/org.modelio.product-macosx.cocoa.aarch64.tar.gz`

If you need to **run** the generated output normally, launch the `.app` bundle or execute `Contents/MacOS/modelio` directly.

If you need lower-level startup debugging, use the manual Java launch path from section `10.3`.

## 16. Summary

The most important path to remember is:

1. build or refresh overlays,
2. validate the target,
3. build plugins,
4. build features,
5. package products,
6. inspect the generated product here:
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

