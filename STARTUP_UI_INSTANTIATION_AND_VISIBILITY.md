# Startup UI targeted fix list

This note is the action-oriented version of the startup trace. For each relevant startup UI element it records:

- where it is instantiated,
- where it first becomes visible,
- what currently determines its appearance,
- where the appearance parameters are set,
- and what the most targeted fix should be.

The goal is to stop treating the problem as a single generic “make everything white later” issue and instead fix each appearance owner at the point where it actually takes effect.

## 1. The appearance-control stack

At startup, appearance is not owned by one place. It is split across four layers that must be distinguished:

1. **e4 model metadata**
   - labels, icons, toolbars, placeholders, selected perspective, stack visibility.
   - Files: `modelio/app/app.ui/e4model/modelio.e4xmi` and fragment `*.e4xmi` files.
2. **upstream e4 SWT renderers**
   - creation of `Shell`, `CTabFolder`, `CTabItem` and container widgets.
   - First visible owner for the workbench shell and part stacks.
3. **Modelio part classes and panel providers**
   - creation of inner `Composite`, `TreeViewer`, `StyledText`, `Browser`, `GraphicalViewer`, custom widgets and deferred content.
4. **theme and runtime overrides**
   - `modelio/app/app.ui/css/default.cocoa.css`
   - `modelio/app/app.ui.ext_org/src/org/modelio/app/ui/lifecycle/MacAppearanceSupport.java`
   - explicit colour assignments in Modelio Java code such as `UIColor.WHITE`, `UIColor.POSTIT_YELLOW`, `ColorConstants.listBackground` and `Display.getSystemColor(...)`.

That split is the practical reason why “where instantiated?” and “where made visible?” are different questions, and why “where does appearance come from?” is a third question again.

## 2. High-priority fix list

| Priority | Surface | Why it still goes dark | Current appearance owner | Targeted fix |
| --- | --- | --- | --- | --- |
| P0 | Main workbench shell | `MacAppearanceSupport` runs after upstream shell creation; `WBWRenderer` still owns first visible `Shell.open()` | upstream `WBWRenderer#createWidget()` + `WBWRenderer#open()` + `default.cocoa.css` + `MacAppearanceSupport` | Move the light-appearance fix to the shell creation path, not only `SWT.Show`. The primary fix must run between `new Shell(...)` and `Shell.open()`. |
| P0 | Workbench part stacks (`CTabFolder`) | e4 creates `CTabFolder` with native defaults before Modelio code sees the selected part | upstream `StackRenderer#createWidget()` + e4 `CTabRendering` + `default.cocoa.css` | Add a creation-time hook for e4 part-stack folders so selected and unselected tab fill, outline and foreground are set before first paint. |
| P0 | Generic “post-show repaint” strategy | `SWT.Show` is already too late for the first dark paint on macOS | `MacAppearanceSupport` display filters | Keep `Show`/`Activate` handling only as fallback; do not treat it as the primary fix mechanism. |
| P1 | Property sub-tabs (`VTabFolder`) | custom widget historically cached list colours; inner panels still depend on contributor roots | `VTabFolder`, `VTabFolderRenderer`, `PropertyView`, contributor panels | Keep the `VTabFolder` default-colour fix, then audit contributor panel roots so they do not reintroduce dark child controls. |
| P1 | Status bar / outline / audit / diagram browser roots | these part roots largely inherit background and foreground rather than setting them explicitly | part root `Composite`/`TreeViewer` creation in Modelio classes | Set explicit light root colours on controls that are always meant to be light and currently rely on inherited native defaults. |
| P1 | Link editor | the hosting `GraphicalViewer` uses `ColorConstants.listBackground`, which can track dark list colours | `LinkEditorPanelUi`, `BackgroundEditPart`, `NodeEditPart` | Replace list/system-derived colours with explicit Modelio light colours for the viewer host and non-central nodes. |
| P1 | Deferred tree-based views | audit and diagram browser create real content only after project open | `AuditView`, `AuditPanelProvider`, `DiagramBrowserView`, `DiagramBrowserPanelProvider` | When deferred content is created, set the light theme on the newly created tree controls immediately rather than relying on a later global pass. |
| P2 | Welcome browser | browser host inherits workbench colours, while page appearance comes from the loaded HTML | `WelcomeView` + welcome HTML/CSS | Decide whether the browser host must be forced light, or whether only the surrounding stack/shell needs fixing. |
| P2 | Instrumentation | current logging explains timing but not ownership cleanly enough for the next code change | `MacAppearanceSupport` diagnostics | Keep only logging that confirms creation-time interception and first-paint colours for `Shell`, `CTabFolder`, `Tree`, `StyledText` and `GraphicalViewer`. |

## 3. Per-element inventory: instantiation, visibility and appearance ownership

| UI element | Class or model type | Instantiated in | First made visible in | Appearance currently determined by | Appearance parameters currently set in | Targeted fix |
| --- | --- | --- | --- | --- | --- | --- |
| Splash window | `org.modelio.app.ui.login.Splash` | `OsLifeCycleManager.postContextCreate()` -> `new Splash()` -> `new Shell(SWT.INHERIT_NONE | SWT.NO_TRIM)` | `Splash.open()` -> `shell.open()` | explicit splash image plus explicit label colours | `modelio/app/app.ui/src/org/modelio/app/ui/login/Splash.java` | Low risk. Keep as-is unless the splash shell itself flashes before the background image paints. |
| Main workbench window | e4 model `basic:TrimmedWindow` + SWT `Shell` | upstream `org.eclipse.e4.ui.workbench.renderers.swt.WBWRenderer#createWidget()` | upstream `WBWRenderer` -> `Shell.open()` / `Shell.setVisible(...)` | native Cocoa defaults first, then e4 CSS, then `MacAppearanceSupport` | `modelio/app/app.ui/e4model/modelio.e4xmi`, `modelio/app/app.ui/css/default.cocoa.css`, `modelio/app/app.ui.ext_org/src/org/modelio/app/ui/lifecycle/MacAppearanceSupport.java` | Primary P0 fix target. Intercept before `Shell.open()`. |
| Limbo shell | upstream helper `Shell` | upstream `PartRenderingEngine#getLimboShell()` | off-screen only | native defaults only | upstream e4 internals | No user-facing fix needed unless reparenting leaks dark defaults into child controls. |
| Perspective stack | e4 model `advanced:PerspectiveStack` | loaded from `modelio/app/app.ui/e4model/modelio.e4xmi` | `PerspectiveManager.showWelcome(false)` and `switchToPerspective(...)` | stack renderer, CSS and selected perspective state | `modelio/app/app.ui/e4model/modelio.e4xmi`, `modelio/app/app.ui.ext_org/src/org/modelio/app/ui/lifecycle/PerspectiveManager.java`, `modelio/app/app.ui/css/default.cocoa.css` | Treat as part of the workbench `CTabFolder` creation-time fix. |
| Welcome stack | e4 model `basic:PartStack` | fragment `modelio/app/app.ui.welcome/e4model/welcome.e4xmi` | `PerspectiveManager.showWelcome(true)` | stack renderer + CSS + welcome part contents | `modelio/app/app.ui.welcome/e4model/welcome.e4xmi`, `default.cocoa.css` | Same as perspective-stack fix; host container must be correct before showing the welcome part. |
| Bottom workbench strip | e4 model `basic:PartStack` rendered as `CTabFolder` | upstream `StackRenderer#createWidget()` | visible when its parent shell/perspective is visible | e4 `CTabFolder` renderer plus CSS plus native defaults at creation time | `modelio/app/app.ui/e4model/modelio.e4xmi`, `default.cocoa.css`, `MacAppearanceSupport` fallback | Primary P0 fix target after the main shell. |
| Status bar | `org.modelio.app.ui.statusbar.AppStatusBar` | `AppStatusBar.createControls(...)` | visible with the trimmed window | inherited composite colours; extension-contributed child controls may override | `modelio/app/app.ui/src/org/modelio/app/ui/statusbar/AppStatusBar.java`, extension contributions, `default.cocoa.css` | Set explicit light colours on the status-bar root composites to remove dependence on inherited native defaults. |
| Welcome view | `org.modelio.app.ui.welcome.impl.WelcomeView` | `WelcomeView.createControls(...)` creates `Browser` | welcome stack visibility + shell open | browser host colours from SWT/container; page colours from the loaded welcome HTML | `modelio/app/app.ui.welcome/src/org/modelio/app/ui/welcome/impl/WelcomeView.java`, welcome HTML/CSS | Fix surrounding stack/shell first; only force the browser host if it still flashes dark. |
| Property view root | `org.modelio.propertyview.PropertyView` | `PropertyView.createGui(...)` creates `Composite`, `CLabel`, `VTabFolder` | bottom-stack selection/show path | explicit header gradient/foreground, custom `VTabFolder`, contributor panels | `modelio/app/app.propertyview/src/org/modelio/propertyview/PropertyView.java` | Keep explicit header colours; make contributor-root backgrounds explicit where needed. |
| Property sub-tab folder | `org.modelio.propertyview.vtabfolder.VTabFolder` extends `Composite` | `PropertyView.createGui(...)` | visible when the property view itself is shown and tabs are added in `showTabFor(...)` | `VTabFolderRenderer`, `selectionBackground`, `selectionForeground`, control background/foreground | `modelio/app/app.propertyview/src/org/modelio/propertyview/vtabfolder/VTabFolder.java`, `.../VTabFolderRenderer.java` | Already partially fixed. Follow up by checking contributor panels and any remaining renderer use of list/system colours. |
| Diagram outline outer host | `org.modelio.diagram.outline.view.DiagramOutlineView` | `createPartControl(...)` creates outer `Composite panel` | bottom-stack selection/show path | inherited composite colours | `modelio/app/app.diagram.outline/src/org/modelio/diagram/outline/view/DiagramOutlineView.java`, `default.cocoa.css` | Set explicit light background/foreground on the outer panel. |
| Diagram outline real control | active editor’s `IContentOutlinePage` | `activePartChanged(...)` -> `outlinePage.createControl(panel)` | after active-part change and layout | whichever active part supplies the outline page | active editor implementation, not this view class | Theme the outer host immediately; then trace any remaining dark outline pages back to their owning editor implementations. |
| Audit view outer host | `org.modelio.audit.view.AuditView` | `createControls(...)` stores parent and forces toolbar visible | bottom-stack selection/show path | part toolbar from e4 model; inner content from `AuditPanelProvider` | `modelio/app/app.audit/e4model/auditui.e4xmi`, `modelio/app/app.audit/src/org/modelio/audit/view/AuditView.java` | Keep toolbar metadata in the model; set explicit colours on the parent composite before creating deferred content. |
| Audit real content | `org.modelio.audit.view.AuditPanelProvider` implements `IPanelProvider` | `onProjectOpened(...)` -> `createPanel(parentComposite)` -> `Composite` + `TreeViewer` | after project-open handling and layout | tree widget defaults, viewer label/content providers, toolbar icons | `modelio/app/app.audit/src/org/modelio/audit/view/AuditPanelProvider.java`, `auditui.e4xmi` | Explicitly theme the `Composite` and `TreeViewer.getTree()` at creation time. |
| Diagram browser outer host | `org.modelio.diagram.browser.view.DiagramBrowserView` | `createPartControl(...)` stores parent and forces toolbar visible | bottom-stack selection/show path | e4 toolbar model plus inner provider | `modelio/app/app.diagram.browser/e4model/diagrambrowser.e4xmi`, `DiagramBrowserView.java` | Explicitly theme the stored parent composite before or when the provider is created. |
| Diagram browser real content | `org.modelio.diagram.browser.view.DiagramBrowserPanelProvider` implements `IPanelProvider` | `initDiagramBrowserPanelProvider(...)` -> `createPanel(parent)` -> `new TreeViewer(parent, SWT.MULTI)` | after project-open handling and layout | `TreeViewer` native defaults plus model-specific label/content providers | `modelio/app/app.diagram.browser/src/org/modelio/diagram/browser/view/DiagramBrowserPanelProvider.java` | Explicitly theme `treeViewer.getTree()` immediately after creation. |
| Script view | `org.modelio.script.view.ScriptView` | `createPartControl(...)` -> `SashForm`, `OutputView`, `InputView` | bottom-stack selection/show path | explicit output yellow, explicit input white, font setup, toolbar model | `modelio/app/app.script.ui/src/org/modelio/script/view/ScriptView.java`, `scriptui.e4xmi` | Mostly already explicit. Verify the `SashForm` host and toolbar background only. |
| Script input | `org.modelio.script.view.InputView` extends `SourceViewer` | `new InputView(...)` inside `ScriptView.createPartControl(...)` | immediately when the part is shown | explicit font plus parent/host colours, then explicit white on `getControl()` | `ScriptView.java`, `InputView.java` | Already acceptable; only ensure parent host is explicitly light. |
| Script output | `org.modelio.script.view.OutputView` extends `StyledText` | `new OutputView(...)` inside `ScriptView.createPartControl(...)` | immediately when the part is shown | explicit `UIColor.POSTIT_YELLOW` background and styled writers | `ScriptView.java`, `OutputView.java` | No startup light-theme fix required beyond confirming the host stays light. |
| Link editor outer host | `org.modelio.linkeditor.ext.view.LinkEditorView` implements `ILinkEditorView` | `postConstruct(...)` creates `LinkEditorPanelProvider` and forces toolbar visible | bottom-stack selection/show path | e4 toolbar model plus inner graphical viewer | `modelio/app/app.link.editor.ext_org/e4model/link.editor.ext_org.e4xmi`, `LinkEditorView.java` | Fix the inner viewer host and figure colours rather than the toolbar metadata. |
| Link editor panel provider | `org.modelio.linkeditor.panel.LinkEditorPanelProvider` implements `ILinkEditor` | `createPanel(...)` delegates to controller/UI | immediate with part creation | controller/UI composition | `modelio/app/app.link.editor/src/org/modelio/linkeditor/panel/LinkEditorPanelProvider.java` | No direct colour policy here; fix the UI layer instead. |
| Link editor viewer host | `org.modelio.linkeditor.panel.LinkEditorPanelUi` | `createGraphicalViewer(...)` -> `viewer.createControl(parent)` | immediate with part creation | explicit `viewer.getControl().setBackground(ColorConstants.listBackground)` | `modelio/app/app.link.editor/src/org/modelio/linkeditor/panel/LinkEditorPanelUi.java` | Replace list-derived background with explicit light Modelio colour. |
| Link editor background figure | `org.modelio.linkeditor.gef.background.BackgroundEditPart` | figure created when graphical contents are built | when the graphical viewer paints its content | explicit `UIColor.TEXT_WRITABLE_BG` or `UIColor.POSTIT_YELLOW` | `modelio/app/app.link.editor/src/org/modelio/linkeditor/gef/background/BackgroundEditPart.java` | Likely already acceptable; keep unless first-paint evidence shows otherwise. |
| Link editor node figures | `org.modelio.linkeditor.gef.node.NodeEditPart` | figure created by GEF edit part factory | when the graphical viewer paints nodes | non-central nodes use `ColorConstants.listBackground`; text uses list/system colours | `modelio/app/app.link.editor/src/org/modelio/linkeditor/gef/node/NodeEditPart.java` | Replace list/system-derived node colours with explicit light colours. |

## 4. What this means for the actual code changes

### 4.1 Fix the first visible owner first

The first two fixes should not be more logging or more generic repaint hooks. They should be concrete creation-path changes:

1. **Main shell**
   - Target: `modelio/app/app.ui.ext_org/src/org/modelio/app/ui/lifecycle/MacAppearanceSupport.java`
   - Required outcome: the workbench `Shell` has the light appearance before `WBWRenderer` calls `Shell.open()`.
   - Implication: the current `SWT.Show` strategy is too late to be the primary mechanism.

2. **Workbench part-stack `CTabFolder`**
   - Target: the e4 part-stack creation path and/or a Modelio-specific hook that runs during that creation path.
   - Required outcome: stack background, tab fill, outlines and foregrounds are set before the first selected tab strip is painted.
   - Implication: CSS remains useful, but it is not sufficient on its own for the first Cocoa paint.

### 4.2 Then fix Modelio-owned roots that still rely on inherited defaults

Once the shell and workbench stacks are correct, fix Modelio-owned part roots that still depend on native inheritance:

- `AppStatusBar` root composites
- `DiagramOutlineView.panel`
- `AuditView.parentComposite` and `AuditPanelProvider.area`
- `AuditPanelProvider.auditTable.getTree()`
- `DiagramBrowserView.parent`
- `DiagramBrowserPanelProvider.treeViewer.getTree()`
- any property-view contributor root controls that still appear dark

These are simpler, lower-risk changes because Modelio fully owns their creation sites.

### 4.3 Treat link editor as its own appearance island

The link editor is not a plain `Composite`/`Tree` case. Its appearance is split between:

- the SWT host control (`GraphicalViewer` control),
- the background figure (`BackgroundEditPart`),
- and the node figure colouriser (`NodeEditPart`).

So the fix there should be explicit and local:

- replace `ColorConstants.listBackground` on the viewer host,
- replace list-derived colours for non-central nodes,
- keep the existing explicit `UIColor` background figure colours unless tests show they still flash dark.

### 4.4 Keep deferred-content fixes local to the deferred owner

For views that create content only after project open or active-part changes, the correct fix is local to the deferred creation method:

- `AuditView.onProjectOpened(...)`
- `DiagramBrowserView.onProjectOpened(...)`
- `DiagramOutlineView.activePartChanged(...)`

When these methods create a `Tree`, `Composite` or other host control, they should set the expected light appearance immediately, rather than depending on a later global pass.

## 5. Suggested execution order

1. Implement a creation-time fix for the workbench `Shell`.
2. Implement a creation-time fix for workbench `CTabFolder` instances.
3. Re-test the initial black frame / bottom strip behaviour.
4. If any Modelio-owned surfaces still flash dark, explicitly fix the part-root controls listed above.
5. Then fix the link editor’s list-derived colours.
6. Keep only the diagnostics needed to verify first-paint ownership after the real fixes are in place.

## 6. Validation gate for each fix slice

For each slice, validate against the supported macOS Apple Silicon path:

1. targeted plugin or aggregator build,
2. product packaging on `platform.mac.aarch64` when the change affects startup/workbench behaviour,
3. direct visual confirmation of first paint for:
   - splash,
   - project-selection/startup shell,
   - bottom stack tab strip,
   - property view,
   - audit/browser/script/link-editor tabs.

The key acceptance criterion is not “eventually becomes white”; it is **starts light at the first visible paint**.
