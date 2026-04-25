# Copilot instructions for Modelio

## Repository summary
- Modelio is an Eclipse RCP / Tycho monorepo for the **Modelio 5.4.1** UML modelling tool.
- This repo is being modernized while preserving a working native macOS Apple Silicon product path. 
- The current bridge baseline is Tycho 5.0.2; the longer-term goal is Eclipse RCP 2026-03 and Java 21 or Java 25 if possible.
- Main technologies: currently: **Java 21** for the build toolchain and the validated macOS Apple Silicon product metadata, Maven, Tycho **5.0.2**, OSGi bundles, Eclipse features, `.product` packaging, XML descriptors.
- Main source is under `modelio/`; feature composition is under `features/opensource/`; product packaging is under `products/`; target-platform inputs are under `dev-platform/rcp-target/`; staged build entrypoints are under `AGGREGATOR/`.
- The currently validated native path is **macOS Apple Silicon** via `platform.mac.aarch64`. Prefer that profile unless the task explicitly targets another platform.

## Bootstrap and environment rules
```zsh
export JAVA_HOME=/Library/Java/JavaVirtualMachines/temurin-21.jdk/Contents/Home
mvn -version
```
- Validated runtime/tooling in this workspace: Maven **3.9.14**, Java **21.0.5**.
- `Tycho 5.0.2` itself now requires Maven to run on Java 21; running it on Java 11 fails before project resolution with `P2ArtifactRepositoryLayout has been compiled by a more recent version of the Java Runtime`.
- The supported macOS Apple Silicon product path now validates with Java 21 launcher metadata, and the active upstream RCP wiring now resolves from `dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03/` only; the old `eclipse/`, `eclipse-fr/`, `jna/repository/`, and `openjdk-jre11` fallback inputs are no longer active for this path.
- Prefer **MacPorts** tooling. Toolchain templates exist in `maven/toolchains.macos.macports.xml` and `AGGREGATOR/toolchains.xml`, but the most reliable build bootstrap is still `JAVA_HOME`.
- The shell is flaky. Prefer one command per invocation or a temporary script. **Do not use `&` command chaining.**
- For scratch validation, use a fresh local Maven repo instead of `~/.m2` to avoid stale Tycho/p2 mirror state.
- British spelling is to be used when creating any new documentation.

## Commands to trust first
### Fastest full validation
Validated in this workspace (~**4 min 54 s**):
```zsh
export JAVA_HOME=/Library/Java/JavaVirtualMachines/temurin-21.jdk/Contents/Home
mvn -Dmaven.repo.local=/Users/david/IdeaProjects/Modelio/tmp/m2-scratch \
  -f /Users/david/IdeaProjects/Modelio/AGGREGATOR/pom.xml \
  -Pplatform.mac.aarch64,product.org clean package
```
Postcondition: `products/target/products/org.modelio.product/macosx/cocoa/aarch64/Modelio.app` exists.

### Smallest-scope target validation
Validated in this workspace (~**1 min** from a fresh scratch repository):
```zsh
export JAVA_HOME=/Library/Java/JavaVirtualMachines/temurin-21.jdk/Contents/Home
mvn -Dmaven.repo.local=/Users/david/IdeaProjects/Modelio/tmp/m2-prebuild \
  -f /Users/david/IdeaProjects/Modelio/AGGREGATOR/prebuild/pom.xml \
  -Pplatform.mac.aarch64 verify
```
Use this first when editing `pom.xml`, `products/pom.xml`, or `dev-platform/rcp-target/**`. It validates the cleaned 2026-03-only target wiring before broader staged builds.

### Split staged build for scoped work
Use one shared scratch repo for the whole cycle and delete it first:
```zsh
rm -rf /Users/david/IdeaProjects/Modelio/tmp/m2-scratch
```
Then run, in order:
1. `AGGREGATOR/prebuild/pom.xml` with `clean install`
2. `AGGREGATOR/plugins/pom.xml` or `AGGREGATOR/plugins/{core|platform|app|uml|bpmn|plugdules}/pom.xml` with `clean install`
3. `AGGREGATOR/features/opensource/pom.xml` with `clean install`
4. `AGGREGATOR/doc/pom.xml` with `clean install`
5. `AGGREGATOR/products/pom.xml` with `-Pplatform.mac.aarch64,product.org clean package`

Producer stages must use `install`, not `verify`, because later split reactors consume installed artifacts (`org.modelio:rcp:target`, plugin IUs, feature IUs, doc features).

### Package verification and run
Validated bundle integrity checks:
```zsh
plutil -lint /Users/david/IdeaProjects/Modelio/products/target/products/org.modelio.product/macosx/cocoa/aarch64/Modelio.app/Contents/Info.plist
codesign --verify --deep --strict --verbose=2 /Users/david/IdeaProjects/Modelio/products/target/products/org.modelio.product/macosx/cocoa/aarch64/Modelio.app
```
Interactive run path:
```zsh
open /Users/david/IdeaProjects/Modelio/products/target/products/org.modelio.product/macosx/cocoa/aarch64/Modelio.app
```

## What is not present
- No `.github/workflows` directory was found.
- No `.mvn/` directory was found.
- No `CONTRIBUTING.md` was found.
- No dedicated repo-level lint command/config was found.
- No obvious `eclipse-test-plugin` modules were found; use **Tycho compile/package validation as the test gate**.
- `doc/parent/pom.xml` is a separate doc parent and still uses Java 8 compiler settings; do not assume the docs branch shares the same compiler configuration as runtime plugins.

## Layout and change rules
- `AGGREGATOR/pom.xml` is the staged top-level build and runs `doc -> prebuild -> plugins -> features -> products`.
- `dev-platform/rcp-target/pom.xml` builds the local target-definition artifact `org.modelio:rcp`; `dev-platform/rcp-target/rcp.target` is the main target file.
- Root `pom.xml` centralizes Tycho config and local p2 repositories; the active upstream RCP baseline is now `dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03` without legacy Eclipse, French localisation, or JNA fallback repositories.
- `products/modelio-os.product` is the final product definition. `products/pom.xml` controls profile-based packaging (`product.org`, `repositoryP2`, `platform.*`) and patches/signs the macOS app with `products/patch_macos_aarch64_app.py`.
- OSGi dependencies are usually declared in `META-INF/MANIFEST.MF`, not Maven dependencies. Example: `modelio/platform/platform.rcp/META-INF/MANIFEST.MF` requires `org.eclipse.swt`; `modelio/platform/platform.ui/META-INF/MANIFEST.MF` requires `org.eclipse.gef` and `org.eclipse.nebula.widgets.gallery`.
- UI wiring often spans `plugin.xml` plus e4 fragments. Example: `modelio/app/app.project.ui/plugin.xml` contributes `e4model/projectui.e4xmi`.
- `*.ext_org` modules are paired open-source variants. Before changing one, check its non-`ext_org` sibling.
- If you add or rename a plugin, wire it in the owning `AGGREGATOR/plugins/*/pom.xml` and in consuming `features/opensource/*/feature.xml`.
- If you change feature membership or packaging, verify `products/modelio-os.product` and finish with `AGGREGATOR/products` or the full `AGGREGATOR/pom.xml` build.
- If you change extension points or UI contributions, update source + `META-INF/MANIFEST.MF` + `plugin.xml` + e4 fragments together.
- Do **not** add Maven dependencies for OSGi bundles already supplied by the target platform; check manifests first.
- Create a long-form commit message after each stage or slice. Short-form commit messages are not required.

## High-value files and directories
- Root files: `pom.xml`, `AGENTS.md`, `README.asciidoc`, `MACOS_AARCH64_BUILD_PROCESS.md`, `MODERNIZATION_PLAN.md`, `products/modelio-os.product`.
- Root directories: `AGGREGATOR/`, `modelio/`, `features/`, `products/`, `dev-platform/`, `doc/`, `maven/`, `diagnostics/`.
- Representative layout examples: `AGGREGATOR/plugins/pom.xml`, `AGGREGATOR/features/opensource/pom.xml`, `features/opensource/org.modelio.application.ui/feature.xml`, `modelio/app/app.project.ui/plugin.xml`, `modelio/app/app.project.ui/e4model/projectui.e4xmi`.

Trust these instructions first. Only search the repository if they are incomplete for the task at hand, or if current file contents contradict them.
