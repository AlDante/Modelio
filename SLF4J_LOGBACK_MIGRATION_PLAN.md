# SLF4J and Logback migration plan for `org.modelio.platform.utils`

## Scope
This note records two migration options for moving `org.modelio.platform.utils` from the legacy logging runtime:

- `slf4j.api 1.7.25`
- `ch.qos.logback.classic 1.2.7`
- `ch.qos.logback.core 1.2.7`

onto the newer runtime already present in the Eclipse 2026-03 target:

- `slf4j.api 2.0.17`
- `ch.qos.logback.classic 1.5.32`
- `ch.qos.logback.core 1.5.32`

The first goal is to remove the product/runtime regression without keeping the old logging stack pinned indefinitely. The second goal is to reduce future upgrade fragility.

## Current findings

### Main compatibility constraints
`modelio/platform/platform.utils/META-INF/MANIFEST.MF` currently pins the legacy logging stack:

- `Require-Bundle: ch.qos.logback.classic;bundle-version="1.2.7"`
- `Require-Bundle: ch.qos.logback.core;bundle-version="1.2.7"`
- `Import-Package: org.slf4j;version="1.7.25"`

### Main code touchpoints
`modelio/platform/platform.utils/src/org/modelio/platform/utils/plugin/Utils.java` is the only class with direct Logback backend usage:

- `LoggerFactory.getILoggerFactory()` cast to `LoggerContext`
- programmatic `JoranConfigurator` setup
- direct appender lookup to find the logfile
- direct `LoggerContext.stop()` on bundle shutdown

The rest of the bundle mainly uses stable SLF4J façade APIs:

- `KernelLogger.java`
- `PluginLogger.java`

### Product-level workaround currently in place
`features/opensource/org.modelio.platform.libraries/feature.xml` is currently pinned back to the old logging stack to keep the application starting.

That workaround should remain only until the plugin itself is compatible with the newer runtime.

## Option A - minimal compatibility migration

### Objective
Keep the current design, including direct Logback usage inside `org.modelio.platform.utils`, but update the bundle so that it resolves and starts cleanly with:

- `slf4j.api 2.0.17`
- `ch.qos.logback.classic 1.5.32`
- `ch.qos.logback.core 1.5.32`

### Files expected to change
- `modelio/platform/platform.utils/META-INF/MANIFEST.MF`
- `modelio/platform/platform.utils/src/org/modelio/platform/utils/plugin/Utils.java`
- `features/opensource/org.modelio.platform.libraries/feature.xml`

### Planned manifest changes
Replace exact legacy requirements with modern ranges aligned with the target platform exports:

- `ch.qos.logback.classic;bundle-version="[1.5.0,2.0.0)"`
- `ch.qos.logback.core;bundle-version="[1.5.0,2.0.0)"`
- `Import-Package: org.slf4j;version="[2.0.0,3.0.0)"`

### Planned code changes in `Utils.java`
1. Add a helper that safely resolves the SLF4J backend and verifies that it is a Logback `LoggerContext`.
2. Fail with a clear message if the runtime backend is not Logback instead of crashing on a blind cast.
3. Use try-with-resources for the `logback.xml` stream.
4. Check for a missing `config/logback.xml` resource explicitly.
5. Make `stop()` tolerant of backend lookup failures.
6. Simplify or fix logfile discovery so it no longer loops over all loggers while always inspecting the root logger appenders.

### Runtime pinning strategy for the migration slice
Do not jump directly from the current old-version feature pins to floating `0.0.0`.

Instead, for the first modernisation slice, pin `features/opensource/org.modelio.platform.libraries/feature.xml` to the newer known runtime versions:

- `ch.qos.logback.classic` -> `1.5.32`
- `ch.qos.logback.core` -> `1.5.32`
- `slf4j.api` -> `2.0.17`

This keeps the migration deterministic while the bundle metadata and code are being updated.

### Validation plan for Option A
Build in increasing scope using one fresh scratch Maven repository:

1. `AGGREGATOR/plugins/platform/pom.xml` with `clean install`
2. `AGGREGATOR/features/opensource/pom.xml` with `clean install`
3. `AGGREGATOR/products/pom.xml` with `-Pplatform.mac.aarch64,product.org clean package`

Then verify:

- `bundles.info` contains `ch.qos.logback.classic 1.5.32`
- `bundles.info` contains `ch.qos.logback.core 1.5.32`
- `bundles.info` contains `slf4j.api 2.0.17`
- the product starts successfully
- the application log file is created and written
- no startup failure remains for `org.modelio.platform.utils`

### Expected difficulty
Low to moderate.

This is the recommended first slice because it directly addresses the version mismatch while keeping the change set small.

## Option B - cleaner backend separation

### Objective
Reduce future runtime upgrade fragility by moving backend-specific Logback bootstrap logic out of `org.modelio.platform.utils`.

### Proposed design
Create a new platform plugin, for example `org.modelio.platform.logging.logback`, that owns:

- Logback `LoggerContext` initialisation
- Logback configuration loading
- logfile discovery
- backend shutdown

`org.modelio.platform.utils` would then depend only on a small internal logging-backend contract rather than directly on Logback internals.

### Files expected to change
Existing files:
- `modelio/platform/platform.utils/META-INF/MANIFEST.MF`
- `modelio/platform/platform.utils/src/org/modelio/platform/utils/plugin/Utils.java`
- `AGGREGATOR/plugins/platform/pom.xml`
- `features/opensource/org.modelio.application.services/feature.xml`
- `features/opensource/org.modelio.platform.libraries/feature.xml`

New plugin skeleton:
- `modelio/platform/platform.logging.logback/pom.xml`
- `modelio/platform/platform.logging.logback/META-INF/MANIFEST.MF`
- `modelio/platform/platform.logging.logback/build.properties`
- `modelio/platform/platform.logging.logback/config/logback.xml`
- one or more Java classes implementing the backend contract

### Planned architectural steps
1. Add a tiny internal service contract in `platform.utils`, for example methods to configure logging, stop the backend, and return the current logfile path.
2. Reduce `Utils.java` so it wires the Modelio/kernel logger bridge and delegates backend-specific work.
3. Implement the Logback-specific backend in the new plugin.
4. Register the backend as an OSGi service.
5. Remove direct Logback requirements from `org.modelio.platform.utils`.
6. Wire the new plugin into the platform aggregator and the relevant open-source feature.

### Validation plan for Option B
Use the same staged build order as Option A, but additionally confirm:

- `org.modelio.platform.utils` no longer requires `ch.qos.logback.*`
- the new backend plugin is present in the product
- service registration happens early enough for startup
- logfile creation and shutdown behaviour remain correct

### Expected difficulty
Moderate.

This is a design improvement rather than the shortest path to a modern runtime. It should be done only after Option A is green, or as a clearly separate follow-up slice.

## Recommended delivery order

### Slice 1 - implement first
Option A:

- update the `platform.utils` manifest for SLF4J 2 and Logback 1.5
- harden `Utils.java`
- pin the feature to the newer runtime versions for deterministic packaging
- rebuild and re-test the product

### Slice 2 - optional follow-up
Option B:

- introduce a dedicated backend plugin
- remove direct Logback coupling from `platform.utils`
- keep the modern runtime versions
- rebuild and re-test again

## Decision rule
Choose Option A if the immediate goal is to stop relying on the legacy logging runtime.

Choose Option B if the longer-term goal is to make future target-platform upgrades less brittle by separating backend-specific bootstrap logic from general platform utilities.

