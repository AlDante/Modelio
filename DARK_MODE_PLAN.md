# Dark mode plan for Modelio on macOS

## Context

Modelio's workbench is designed for a light colour scheme. On macOS, when the system
appearance is set to Dark Mode, SWT/Cocoa controls inherit dark native colours at the
point of widget creation — before Modelio's own code has an opportunity to intervene.
The existing `MacAppearanceSupport` class attempts to correct this using event-driven
hooks (`SWT.Show`, `SWT.Activate`, `SWT.Paint`, `SWT.Skin`, `SWT.Settings`) and
reflective Cocoa NSAppearance manipulation.  However, these hooks run *after* the first
visible paint of the workbench shell, causing a dark flash on startup and, in some cases,
persistent dark colouring on native-backed widgets (trees, tables, list backgrounds).

The CSS file `default.cocoa.css` declares explicit light colours for all major SWT control
types, but CSS application is also post-creation; on Cocoa it cannot prevent native dark
drawing before the first CSS pass.

---

## Short-term goal: eliminate visible dark-mode artefacts at startup

### Objective

Ensure that no user-visible surface in the Modelio workbench appears dark on macOS when
the system appearance is Dark Mode.  The acceptance criterion is: **every control starts
light at the first visible paint** and remains light throughout the session.

### Phase 1 — Pre-shell creation appearance lock (P0)

| Step | Description | Files | Rationale |
|------|-------------|-------|-----------|
| 1.1 | Set `org.eclipse.swt.display.useSystemTheme=false` in the product `.ini` (VM arguments) before `Display` construction | `products/modelio-os.product` | Prevents SWT from inheriting macOS dark appearance at Display creation. This is the earliest possible intervention point. |
| 1.2 | Call `applyLightDisplayAppearance(display)` and `applyLightShellWindowAppearance(shell)` synchronously from a `Display.addFilter(SWT.Skin, ...)` listener registered at Display creation, before the e4 workbench model is processed | `OsLifeCycleManager.java`, `MacAppearanceSupport.java` | Intercepts shell/control theming at the `Skin` event, which fires when a widget is first styled — before `Show` or `Paint`. |
| 1.3 | Register a `Display.addFilter(SWT.Skin, ...)` hook that calls `applyLightControlThemeSelf()` on every newly-skinned control, targeting `Shell` and `CTabFolder` specifically | `MacAppearanceSupport.java` | Catches upstream e4 renderer creation of `WBWRenderer.createWidget()` and `StackRenderer.createWidget()` before those widgets are made visible. |
| 1.4 | Demote the existing `SWT.Show`/`SWT.Activate`/`SWT.Paint` hooks to safety-net-only status; remove global refresh scheduling except for `SWT.Settings` (system theme change) | `MacAppearanceSupport.java` | Reduces overhead and prevents flickering repaint loops. The primary protection is now creation-time via `Skin`. |

**Validation**: build with `AGGREGATOR/pom.xml -Pplatform.mac.aarch64,product.org`; launch
`Modelio.app` with macOS Dark Mode active; observe no dark flash on the main shell, tab
strips or bottom stack at any point during startup.

### Phase 2 — Modelio-owned part roots (P1)

| Step | Description | Files | Rationale |
|------|-------------|-------|-----------|
| 2.1 | Set explicit light background on `AppStatusBar` root composites at creation time | `AppStatusBar.java` | Currently relies on inherited native colours. |
| 2.2 | Set explicit light background/foreground on `DiagramOutlineView.panel` in `createPartControl()` | `DiagramOutlineView.java` | Host composite relies on inherited colours. |
| 2.3 | Set explicit light background on `AuditView` parent composite in `createControls()` and on `AuditPanelProvider.area` and `auditTable.getTree()` in `createPanel()` | `AuditView.java`, `AuditPanelProvider.java` | Deferred content does not benefit from the shell-level fix alone. |
| 2.4 | Set explicit light background on `DiagramBrowserView.parent` in `createPartControl()` and on `DiagramBrowserPanelProvider.treeViewer.getTree()` in `createPanel()` | `DiagramBrowserView.java`, `DiagramBrowserPanelProvider.java` | Same deferred-content pattern. |
| 2.5 | Audit `PropertyView` contributor panels for any root composites that do not have explicit colours; set them where needed | `PropertyView.java`, contributor panels | The `VTabFolder` fix is already partial; ensure no contributor reintroduces dark defaults. |
| 2.6 | Set explicit light background on the `ScriptView` `SashForm` host | `ScriptView.java` | Input/output already explicitly themed; only the host is missing. |

**Validation**: rebuild the affected plugin family via `AGGREGATOR/plugins/app/pom.xml`;
repackage via `AGGREGATOR/products/pom.xml`; launch and confirm each bottom-tab view
starts light.

### Phase 3 — Link editor appearance island (P1)

| Step | Description | Files | Rationale |
|------|-------------|-------|-----------|
| 3.1 | Replace `ColorConstants.listBackground` on the viewer host control with `UIColor.WHITE` | `LinkEditorPanelUi.java` | `listBackground` tracks the native list colour, which is dark in Dark Mode. |
| 3.2 | Replace `ColorConstants.listBackground` and system colours for non-central node figures with explicit light colours | `NodeEditPart.java` | Same system-colour leakage problem. |
| 3.3 | Verify `BackgroundEditPart` figure colours remain correct (`UIColor.TEXT_WRITABLE_BG` / `UIColor.POSTIT_YELLOW`); no change expected | `BackgroundEditPart.java` | Already explicit; confirm only. |

**Validation**: open a project with link-editor content; confirm background and nodes
are light regardless of system appearance.

### Phase 4 — Remove diagnostic overhead

| Step | Description | Files | Rationale |
|------|-------------|-------|-----------|
| 4.1 | Remove or guard all `logDiagnostic()` calls behind a compile-time constant or system property, retaining only: shell creation interception, first-paint confirmation for `Shell`/`CTabFolder`/`Tree`/`StyledText` | `MacAppearanceSupport.java` | Reduces log noise once the real fixes are in place. |
| 4.2 | Remove stale key constants (`FIRST_SHOW_LOG_KEY`, `FIRST_PAINT_LOG_KEY`, `FIRST_THEME_LOG_KEY`) if no longer referenced | `MacAppearanceSupport.java` | Code hygiene. |

### Phase 5 — VM argument hardening

| Step | Description | Files | Rationale |
|------|-------------|-------|-----------|
| 5.1 | Add `-Dorg.eclipse.swt.display.useSystemTheme=false` to the `vmArgs` section of `modelio-os.product` if not already present | `products/modelio-os.product` | Belt-and-braces: even if `MacAppearanceSupport` sets it programmatically, having it in the `.ini` ensures it is effective before Display construction on all code paths. |
| 5.2 | Add `-Dorg.osgi.framework.bundle.parent=ext` if needed for reflective access in Java 21 module system | `products/modelio-os.product` | `MacAppearanceSupport` uses reflection on `Shell.window` and `Display` internals; this may require `--add-opens` directives depending on the SWT build. |
| 5.3 | Validate that `--add-opens=java.base/java.lang=ALL-UNNAMED` and any SWT-internal opens needed for `applyLightShellWindowAppearance` are present | `products/modelio-os.product` | Without these, Java 21 may block the reflective NSWindow appearance manipulation. |

---

## Medium-term goal: full native dark mode support on macOS

### Objective

Provide a first-class dark appearance for all Modelio UI elements when the user's macOS
system appearance is set to Dark Mode.  Colours, contrast, legibility and visual
coherence must be correct for every control, diagram canvas, GEF figure, dialog and
custom widget.

### Principles

1. **Theme-aware colour resolution** — all colour references must resolve through a
   theme-aware indirection rather than hard-coded RGB values.
2. **Single source of truth** — the active theme (light or dark) must be determined once
   at startup (from the system appearance) and propagated through a consistent mechanism.
3. **CSS-first for SWT controls** — use the e4 CSS engine with paired stylesheets, one
   light and one dark, selected at startup.
4. **Diagram/GEF engine colour service** — diagram colours must go through a Modelio
   colour service that resolves to light or dark palettes.
5. **No flicker** — the selected theme must be applied before first paint (same
   creation-time strategy as the short-term fix, but now selecting the correct palette
   rather than forcing light).

### Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     macOS System Appearance                       │
└────────────────────────────────┬─────────────────────────────────┘
                                 │ detected at Display creation
                                 ▼
┌──────────────────────────────────────────────────────────────────┐
│              ModelioThemeManager (new singleton)                  │
│  • reads system appearance via SWT or Cocoa API                  │
│  • exposes ThemeMode.LIGHT / ThemeMode.DARK                      │
│  • selects CSS stylesheet path                                   │
│  • provides colour-resolution API for non-CSS consumers          │
│  • listens to SWT.Settings for runtime theme changes             │
└────────┬───────────────────────┬─────────────────────────────────┘
         │                       │
         ▼                       ▼
┌────────────────────┐  ┌───────────────────────────────────────────┐
│ e4 CSS engine      │  │ ModelioColourService (replaces UIColor     │
│ loads either:      │  │   hard-coded constants)                    │
│ • default.cocoa.css│  │ • provides bg(), fg(), accent() etc.       │
│   (light)          │  │ • backed by light/dark palette definitions │
│ • dark.cocoa.css   │  │ • consumed by diagrams, GEF, custom        │
│   (dark)           │  │   widgets, dialogs                         │
└────────────────────┘  └───────────────────────────────────────────┘
```

### Staged implementation plan

#### Stage A — Theme infrastructure

| Step | Description | Notes |
|------|-------------|-------|
| A.1 | Create `ModelioThemeManager` in `platform.ui` | Singleton; reads system appearance at construction; exposes `getThemeMode()`. |
| A.2 | Define `ThemeMode` enum (`LIGHT`, `DARK`) | In `platform.ui`. |
| A.3 | Create `ModelioColourService` interface and default implementation | Provides semantic colour accessors: `textBackground()`, `textForeground()`, `panelBackground()`, `diagramCanvasBackground()`, `nodeBackground()`, `accentColour()`, etc. |
| A.4 | Define light and dark palette property files or constants | Initial dark palette can start with macOS system colours; light palette matches current hard-coded values. |
| A.5 | Register `ModelioThemeManager` and `ModelioColourService` in the Eclipse context | Available for injection by all downstream plugins. |

#### Stage B — CSS dual-stylesheet support

| Step | Description | Notes |
|------|-------------|-------|
| B.1 | Create `dark.cocoa.css` with dark palette values | Mirror all selectors from `default.cocoa.css` with dark-appropriate colours. |
| B.2 | Modify the product/application model to select stylesheet based on `ModelioThemeManager.getThemeMode()` | Use the e4 CSS `applicationCSS` property or a custom theme-extension contribution. |
| B.3 | Test CSS-only coverage: shells, composites, CTabFolders, trees, tables, text, toolbars | Confirm that the CSS pass alone produces a coherent dark workbench frame. |

#### Stage C — UIColor and colour-constant migration

| Step | Description | Notes |
|------|-------------|-------|
| C.1 | Audit all usages of `UIColor.*` constants across the codebase | Identify which are hard-coded light colours that would be illegible on a dark background. |
| C.2 | Replace hard-coded `UIColor.WHITE`, `UIColor.BLACK`, `UIColor.POSTIT_YELLOW` etc. with `ModelioColourService` semantic accessors | E.g., `colourService.textBackground()` instead of `UIColor.WHITE`. |
| C.3 | Replace usages of `ColorConstants.listBackground`, `Display.getSystemColor(SWT.COLOR_LIST_BACKGROUND)` etc. with service calls | These system colours track the OS theme, which is correct for full dark mode support but must go through a validated path. |
| C.4 | Deprecate direct `UIColor` constant usage for background/foreground colours; retain named colours only for domain-semantic use (e.g., severity indicators) | Gradual migration. |

#### Stage D — Diagram and GEF dark support

| Step | Description | Notes |
|------|-------------|-------|
| D.1 | Audit diagram canvas background (`AbstractDiagramEditor`, `DiagramGraphicalViewer`) | Currently likely hard-coded white. |
| D.2 | Provide a dark canvas background option in `ModelioColourService` | E.g., `#1e1e1e` or `#2d2d2d` — must contrast well with coloured shapes. |
| D.3 | Audit GEF figure colours: `BackgroundEditPart`, `NodeEditPart`, all diagram element figures | Many use `UIColor` constants or `ColorConstants`. |
| D.4 | Implement figure-level colour resolution via `ModelioColourService` | Figures query the service at creation time and on `SWT.Settings` refresh. |
| D.5 | Handle per-element user-specified colours | User-set colours (stored in the model) must be preserved; only *default* colours should follow the theme. |
| D.6 | Validate legibility: ensure text on shapes, connector labels, and annotation text remain legible on dark backgrounds | May require dynamic contrast calculation for edge cases. |

#### Stage E — Dialogs, wizards and pop-ups

| Step | Description | Notes |
|------|-------------|-------|
| E.1 | Audit all `Shell`-creating code in `modelio/app/**` and `modelio/platform/**` | Dialogs and wizards must inherit the active theme. |
| E.2 | Replace explicit colour assignments in dialog code with service calls | Where dialogs set `WHITE` backgrounds explicitly, replace with `colourService.dialogBackground()`. |
| E.3 | Verify that JFace dialogs (`TitleAreaDialog`, `WizardDialog`) inherit CSS correctly | These typically respect the workbench theme if CSS covers their widget types. |
| E.4 | Handle the splash screen: either make it theme-aware or ensure it looks acceptable on both backgrounds | Likely keep the splash image fixed (it has its own explicit background). |

#### Stage F — Property view, custom widgets, VTabFolder

| Step | Description | Notes |
|------|-------------|-------|
| F.1 | Make `VTabFolder` and `VTabFolderRenderer` theme-aware | Query `ModelioColourService` for tab backgrounds, selection colours, borders. |
| F.2 | Audit all `IPanelProvider` implementations for hard-coded colours | Each contributor panel root must use the service or CSS. |
| F.3 | Verify the property view header gradient in both themes | May need a dark gradient definition. |

#### Stage G — Welcome page and browser views

| Step | Description | Notes |
|------|-------------|-------|
| G.1 | Create a dark variant of the welcome HTML/CSS | Or use `prefers-color-scheme: dark` in the existing welcome CSS. |
| G.2 | Pass the active theme to the browser URL or inject a `<style>` element | The SWT `Browser` widget renders HTML independently of SWT colours. |

#### Stage H — Runtime theme switching (optional, deferred)

| Step | Description | Notes |
|------|-------------|-------|
| H.1 | Listen to `SWT.Settings` for system appearance changes during runtime | `ModelioThemeManager` updates `getThemeMode()`. |
| H.2 | Trigger CSS re-application and `ModelioColourService` palette swap | SWT CSS engine supports runtime stylesheet changes via `IStylingEngine.setStyleSheet()`. |
| H.3 | Notify diagram editors to refresh figure colours | Via an OSGi event or Eclipse context property change. |
| H.4 | Handle edge cases: open dialogs, active modal shells, ongoing drag operations | These may need deferred refresh. |

### Dark palette colour guide (initial)

| Semantic role | Light value | Dark value (proposed) |
|---------------|-------------|-----------------------|
| Shell/panel background | `#ffffff` | `#1e1e1e` |
| Control background (tree, table, text) | `#ffffff` | `#252526` |
| Text foreground | `#000000` | `#d4d4d4` |
| Tab strip unselected | `#f6f6f6` | `#2d2d2d` |
| Tab strip selected | `#ffffff` | `#1e1e1e` |
| Tab outline / keyline | `#eaeaea` | `#3c3c3c` |
| Accent / selection highlight | `#5983c5` | `#264f78` |
| Diagram canvas | `#ffffff` | `#1e1e1e` or `#2d2d2d` |
| Post-it / note background | `#ffffd2` | `#3d3d00` (muted yellow) |
| Writable text background | `#ffffff` | `#1e1e1e` |

These values should be validated against WCAG AA contrast ratios (minimum 4.5:1 for
normal text, 3:1 for large text and UI components).

### Risks and mitigations

| Risk | Mitigation |
|------|------------|
| Reflective Cocoa access breaks in future SWT | Stage A provides a clean fallback: if reflection fails, the app falls back to the CSS/service path alone. |
| Third-party or vendored plugins with hard-coded colours | Audit `*.ext_org` modules; file issues for external modules. |
| Model-persisted colours become illegible on dark backgrounds | Stage D.5: distinguish user-set colours from theme-default colours; only default colours follow the theme. |
| Performance overhead of service lookups in diagram painting | Cache palette colours in the service instance; invalidate only on theme change. |
| Java 21 module system blocks reflection | Phase 5 of the short-term plan ensures the required `--add-opens` are in place; the medium-term plan gradually removes the need for reflection by using legitimate SWT/e4 APIs. |

---

## Priority and dependencies

```
Short-term (force light)          Medium-term (full dark support)
─────────────────────────         ─────────────────────────────────
Phase 1 (P0 shell/tabs)     ───► Stage A (theme infrastructure)
Phase 2 (P1 part roots)     ───► Stage B (CSS dual-stylesheet)
Phase 3 (P1 link editor)    ───► Stage C (UIColor migration)
Phase 4 (diagnostics trim)       Stage D (diagram/GEF)
Phase 5 (VM hardening)           Stage E (dialogs/wizards)
                                  Stage F (property view/custom)
                                  Stage G (welcome/browser)
                                  Stage H (runtime switching)
```

The short-term plan is a prerequisite for the medium-term plan: it validates the
creation-time interception pattern, cleans up the event-driven fallback, and establishes
the VM configuration needed for both approaches.  The medium-term plan then replaces the
"force everything white" strategy with a proper theme-selection architecture.

---

## Validation gates

### Short-term acceptance

1. Build succeeds: `AGGREGATOR/pom.xml -Pplatform.mac.aarch64,product.org clean package`
2. macOS Dark Mode active → launch Modelio → no dark flash at any point during startup
3. All bottom-tab views (property, audit, diagram browser, script, link editor, outline)
   start and remain light
4. Diagnostics script `diagnostics/macos-aarch64/validate_macos_aarch64_contract.py` passes
5. No illegal reflective access warnings in the console log

### Medium-term acceptance

1. macOS Dark Mode active → launch Modelio → all surfaces render in the dark palette
2. macOS Light Mode active → launch Modelio → all surfaces render in the light palette
3. Every text label achieves ≥ 4.5:1 contrast against its background
4. Diagram elements remain legible; user-customised colours are preserved
5. Runtime theme switch (if implemented) transitions without crash or orphaned colours
6. No regression in the light-mode appearance

---

## References

- `STARTUP_UI_INSTANTIATION_AND_VISIBILITY.md` — per-element fix list and execution order
- `STARTUP_MODELIO_UI_ELEMENTS.dox` — class-level appearance ownership documentation
- `modelio/app/app.ui.ext_org/src/org/modelio/app/ui/lifecycle/MacAppearanceSupport.java`
- `modelio/app/app.ui/css/default.cocoa.css`
- `modelio/platform/platform.ui/src/org/modelio/platform/ui/UIColor.java`
- `products/modelio-os.product`

