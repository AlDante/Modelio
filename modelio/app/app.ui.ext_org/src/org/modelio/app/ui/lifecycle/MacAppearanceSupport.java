/*
 * Copyright 2013-2026 Modeliosoft
 *
 * This file is part of Modelio.
 *
 * Modelio is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * Modelio is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Modelio.  If not, see <http://www.gnu.org/licenses/>.
 *
 */
package org.modelio.app.ui.lifecycle;

import java.lang.reflect.Field;
import java.lang.reflect.Method;
import com.modeliosoft.modelio.javadesigner.annotations.objid;
import org.eclipse.swt.SWT;
import org.eclipse.swt.custom.CTabFolder;
import org.eclipse.swt.custom.ScrolledComposite;
import org.eclipse.swt.custom.StyledText;
import org.eclipse.swt.graphics.Color;
import org.eclipse.swt.widgets.Button;
import org.eclipse.swt.widgets.Canvas;
import org.eclipse.swt.widgets.Combo;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.swt.widgets.Control;
import org.eclipse.swt.widgets.CoolBar;
import org.eclipse.swt.widgets.Display;
import org.eclipse.swt.widgets.ExpandBar;
import org.eclipse.swt.widgets.Event;
import org.eclipse.swt.widgets.Group;
import org.eclipse.swt.widgets.Label;
import org.eclipse.swt.widgets.Link;
import org.eclipse.swt.widgets.List;
import org.eclipse.swt.widgets.Listener;
import org.eclipse.swt.widgets.Sash;
import org.eclipse.swt.widgets.Shell;
import org.eclipse.swt.widgets.Spinner;
import org.eclipse.swt.widgets.Table;
import org.eclipse.swt.widgets.TabFolder;
import org.eclipse.swt.widgets.Text;
import org.eclipse.swt.widgets.ToolBar;
import org.eclipse.swt.widgets.Tree;
import org.modelio.app.ui.plugin.AppUi;

/**
 * Forces Modelio to use the SWT/Cocoa Aqua appearance on macOS.
 * <p>
 * Modelio's workbench colours are designed for a light theme. Recent SWT builds
 * can inherit macOS dark appearance at the native Cocoa level, which makes SWT
 * controls such as trees and part stacks dark while the diagram canvas remains
 * light. The public SWT API only exposes dark-theme detection, so this class uses
 * the package-private SWT appearance hooks reflectively and degrades gracefully if
 * they change in a future SWT release. As an additional fallback, shells and core
 * SWT workbench controls are normalised to a light appearance so
 * older ad-hoc dialogs and native-backed trees/tab folders do not inherit dark
 * macOS colours. Editor part stacks on Cocoa repaint their tab strip after
 * startup, and the main workbench can repaint again when modal edit shells
 * activate/deactivate, so the light theme is reasserted on shell lifecycle
 * changes rather than on every child control event.
 */
@objid ("ec94be3e-b342-4b40-bf74-d3937de66f0b")
final class MacAppearanceSupport {
    @objid ("b9a8d9f7-ae2e-48d4-96c2-bf6f2e8bda0b")
    private static final String USE_SYSTEM_THEME_PROPERTY = "org.eclipse.swt.display.useSystemTheme";

    @objid ("a2d55d58-c92a-4881-94a0-75fbc9b66a43")
    private static final String DEBUG_PROPERTY = "org.modelio.app.ui.macAppearance.debug";

    @objid ("90b9fd9d-2a43-4aa3-b7d6-a5683a6be1d4")
    private static final String SHELL_HOOK_KEY = MacAppearanceSupport.class.getName() + ".shellHookInstalled";

    @objid ("5da21e0b-cf7f-4f87-a431-f8b29fb8229a")
    private static final String SHELL_REFRESH_KEY = MacAppearanceSupport.class.getName() + ".refreshScheduled";

    @objid ("c4a0d77a-1735-4d4d-98f2-70bc907402c4")
    private static final String DISPLAY_REFRESH_KEY = MacAppearanceSupport.class.getName() + ".displayRefreshScheduled";

    @objid ("39b37d38-3177-4f7d-9310-9183d6b8ed78")
    private static final String ACTIVE_SHELL_KEY = MacAppearanceSupport.class.getName() + ".activeShell";

    @objid ("22b7eef7-37b9-490b-bad6-4a4f6554838b")
    private static final String SHELL_WINDOW_THEME_KEY = MacAppearanceSupport.class.getName() + ".windowThemeApplied";

    @objid ("0d59112d-ec44-42a0-a567-fda0b2cafb7f")
    private static final String DEBUG_HOOK_KEY = MacAppearanceSupport.class.getName() + ".debugHookInstalled";

    @objid ("11bc0a10-f604-4635-aa2e-525e2f37d6ad")
    private static final String FIRST_THEME_LOG_KEY = MacAppearanceSupport.class.getName() + ".firstThemeLogged";

    @objid ("4d4249a4-cf47-48b8-9d16-909b24deaf7e")
    private static final String FIRST_SHOW_LOG_KEY = MacAppearanceSupport.class.getName() + ".firstShowLogged";

    @objid ("33150fd5-3146-4614-9a95-26bbd5119b5b")
    private static final String FIRST_PAINT_LOG_KEY = MacAppearanceSupport.class.getName() + ".firstPaintLogged";

    @objid ("2bc8917a-75dc-4a3d-b6e4-6f3aee0b0877")
    private MacAppearanceSupport() {
        // Utility class.
    }

    @objid ("3f4cbf20-3285-4a27-924d-ce7c45c9de6e")
    static void forceLightAppearance() {
        forceLightAppearance("unspecified");
    }

    @objid ("f3bd3c53-2518-47a2-a61a-4736c18c23c4")
    static void forceLightAppearance(final String source) {
        System.setProperty(MacAppearanceSupport.USE_SYSTEM_THEME_PROPERTY, "false");

        logDiagnostic("forceLightAppearance source=%s platform=%s", source, SWT.getPlatform());

        if (!"cocoa".equals(SWT.getPlatform())) {
            logDiagnostic("forceLightAppearance source=%s skipped: non-cocoa platform", source);
            return;
        }

        final Display display = Display.getCurrent() != null ? Display.getCurrent() : Display.getDefault();
        if (display == null || display.isDisposed()) {
            logDiagnostic("forceLightAppearance source=%s skipped: no live display", source);
            return;
        }

        logDiagnostic("forceLightAppearance source=%s display=%s shells=%d", source, describeDisplay(display), display.getShells().length);

        applyLightDisplayAppearance(display);

        installLightControlHook(display);
    }

    @objid ("b2866428-8a22-4a8e-a8e8-f7307d3d2bda")
    private static void installLightControlHook(final Display display) {
        if (Boolean.TRUE.equals(display.getData(SHELL_HOOK_KEY))) {
            logDiagnostic("installLightControlHook skipped: already installed on %s", describeDisplay(display));
            return;
        }

        final Listener listener = new Listener() {
            @Override
            public void handleEvent(final Event event) {
                if (display.isDisposed()) {
                    return;
                }

                if (shouldLogEvent(event)) {
                    logDiagnostic("event=%s widget=%s colours=%s", eventName(event.type), describeWidget(event.widget), describeWidgetColours(event.widget));
                }

                if (event.type == SWT.Settings) {
                    applyLightDisplayAppearance(display);
                    scheduleGlobalRefresh(display, 0, "settings");
                }

                if (event.widget instanceof Control control) {
                    if (event.type == SWT.Skin) {
                        applyLightDisplayAppearance(display);
                        if (control instanceof Shell shell) {
                            applyLightShellTheme(shell);
                        } else {
                            applyLightControlThemeAncestors(control);
                            applyLightControlThemeSelf(control);
                        }
                    } else if (event.type == SWT.Paint) {
                        if (control instanceof Shell shell) {
                            applyLightShellTheme(shell);
                        } else if (control instanceof CTabFolder) {
                            applyLightControlThemeSelf(control);
                        }
                    } else if (event.type == SWT.Show) {
                        applyLightDisplayAppearance(display);
                        if (control instanceof Shell shell) {
                            applyLightShellTheme(shell);
                            scheduleShellRefresh(shell);
                            scheduleGlobalRefresh(display, 0, "shellShow");
                        } else {
                            applyLightControlThemeAncestors(control);
                            applyLightControlTheme(control);
                        }
                    } else if (control instanceof Shell shell) {
                        if (event.type == SWT.Activate || event.type == SWT.Deactivate) {
                            applyLightDisplayAppearance(display);
                            applyLightShellTheme(shell);
                            scheduleShellRefresh(shell);
                            if (updateActiveShell(display)) {
                                scheduleGlobalRefresh(display, 0, "shellActiveChange");
                            }
                        }
                    } else if (control instanceof CTabFolder && (event.type == SWT.Activate || event.type == SWT.Show)) {
                        applyLightControlTheme(control);
                    }
                }
            }
        };

        display.addFilter(SWT.Activate, listener);
        display.addFilter(SWT.Deactivate, listener);
        display.addFilter(SWT.Skin, listener);
        display.addFilter(SWT.Paint, listener);
        display.addFilter(SWT.Show, listener);
        display.addFilter(SWT.Settings, listener);
        display.setData(SHELL_HOOK_KEY, Boolean.TRUE);
        display.setData(ACTIVE_SHELL_KEY, display.getActiveShell());

        logDiagnostic("installLightControlHook installed on %s shells=%d", describeDisplay(display), display.getShells().length);

        for (final Shell shell : display.getShells()) {
            applyLightShellTheme(shell);
            scheduleShellRefresh(shell);
        }

        scheduleGlobalRefresh(display, 0, "initialInstall");
    }

    @objid ("eb9a5265-60b9-48d4-831d-08d115953c0d")
    private static void scheduleGlobalRefresh(final Display display, final int delayMs, final String reason) {
        if (display.isDisposed()) {
            return;
        }

        if (Boolean.TRUE.equals(display.getData(DISPLAY_REFRESH_KEY))) {
            logDiagnostic("scheduleGlobalRefresh skipped delayMs=%d reason=%s display=%s shells=%d pending=true",
                    delayMs,
                    reason,
                    describeDisplay(display),
                    display.getShells().length);
            return;
        }

        display.setData(DISPLAY_REFRESH_KEY, Boolean.TRUE);
        logDiagnostic("scheduleGlobalRefresh delayMs=%d reason=%s display=%s shells=%d pending=false",
                delayMs,
                reason,
                describeDisplay(display),
                display.getShells().length);
        display.timerExec(delayMs, new Runnable() {
            @Override
            public void run() {
                try {
                    if (display.isDisposed()) {
                        return;
                    }

                    logDiagnostic("runGlobalRefresh delayMs=%d reason=%s display=%s shells=%d",
                            delayMs,
                            reason,
                            describeDisplay(display),
                            display.getShells().length);

                    for (final Shell shell : display.getShells()) {
                        applyLightControlTheme(shell);
                    }
                } finally {
                    if (!display.isDisposed()) {
                        display.setData(DISPLAY_REFRESH_KEY, null);
                    }
                }
            }
        });
    }

    @objid ("0345f042-2662-4f9b-aaaf-ae498b514e22")
    private static boolean updateActiveShell(final Display display) {
        final Shell currentActiveShell = display.getActiveShell();
        final Object previousActiveShell = display.getData(ACTIVE_SHELL_KEY);
        if (previousActiveShell == currentActiveShell) {
            logDiagnostic("activeShell unchanged display=%s shell=%s",
                    describeDisplay(display),
                    describeWidget(currentActiveShell));
            return false;
        }

        display.setData(ACTIVE_SHELL_KEY, currentActiveShell);
        logDiagnostic("activeShell changed display=%s previous=%s current=%s",
                describeDisplay(display),
                describeWidget(previousActiveShell),
                describeWidget(currentActiveShell));
        return true;
    }

    @objid ("ab3bf57a-bf76-4eb4-bf2a-45c71389da89")
    private static void scheduleShellRefresh(final Shell shell) {
        if (shell.isDisposed() || Boolean.TRUE.equals(shell.getData(SHELL_REFRESH_KEY))) {
            if (!shell.isDisposed()) {
                logDiagnostic("scheduleShellRefresh skipped shell=%s pending=%s", describeControl(shell), shell.getData(SHELL_REFRESH_KEY));
            }
            return;
        }

        shell.setData(SHELL_REFRESH_KEY, Boolean.TRUE);
        final Display display = shell.getDisplay();
        logDiagnostic("scheduleShellRefresh shell=%s", describeControl(shell));
        display.asyncExec(new Runnable() {
            @Override
            public void run() {
                try {
                    if (!shell.isDisposed()) {
                        logDiagnostic("runShellRefresh shell=%s", describeControl(shell));
                        applyLightShellTheme(shell);
                    }
                } finally {
                    if (!shell.isDisposed()) {
                        shell.setData(SHELL_REFRESH_KEY, null);
                    }
                }
            }
        });
    }

    @objid ("10d3e29a-1f8c-4232-9246-b4f7117b3c0e")
    private static void applyLightControlTheme(final Control control) {
        if (control == null || control.isDisposed()) {
            return;
        }

        applyLightControlThemeSelf(control);

        if (control instanceof Composite composite) {
            for (final Control child : composite.getChildren()) {
                applyLightControlTheme(child);
            }
        }
    }

    @objid ("c74ba365-0d6f-4ff5-bb51-a07ab2493115")
    private static void applyLightShellTheme(final Shell shell) {
        if (shell == null || shell.isDisposed()) {
            return;
        }

        applyLightShellWindowAppearance(shell);
        applyLightControlTheme(shell);
    }

    @objid ("13d8cfd3-7ecc-48b7-a004-76dba0e31785")
    private static void applyLightControlThemeAncestors(final Control control) {
        if (control == null || control.isDisposed()) {
            return;
        }

        Composite parent = control.getParent();
        while (parent != null && !parent.isDisposed()) {
            applyLightControlThemeSelf(parent);
            parent = parent.getParent();
        }
    }

    @objid ("a5e5c568-5c2a-4f67-b1e0-c2a7d2d70ad4")
    private static void applyLightControlThemeSelf(final Control control) {
        if (control == null || control.isDisposed()) {
            return;
        }

        installDebugProbe(control);

        final boolean logControl = shouldProbeControl(control);
        final String beforeColours = logControl ? describeControlColours(control) : null;

        final Display display = control.getDisplay();
        final Color white = display.getSystemColor(SWT.COLOR_WHITE);
        final Color black = display.getSystemColor(SWT.COLOR_BLACK);
        if (white == null || black == null) {
            return;
        }

        if (control instanceof Shell shell) {
            shell.setAlpha(255);
            shell.setBackgroundMode(SWT.INHERIT_DEFAULT);
            applyLightShellWindowAppearance(shell);
        } else if (control instanceof Composite composite) {
            composite.setBackgroundMode(SWT.INHERIT_DEFAULT);
        }

        if (supportsLightBackground(control)) {
            control.setBackground(white);
        }

        if (supportsDarkText(control)) {
            control.setForeground(black);
        }

        if (control instanceof CTabFolder tabFolder) {
            tabFolder.setBackground(new Color[] { white, white }, new int[] { 100 }, true);
            tabFolder.setSelectionBackground(white);
            tabFolder.setSelectionBackground(new Color[] { white, white }, new int[] { 100 }, true);
            tabFolder.setSelectionForeground(black);
            tabFolder.setForeground(black);
            applyLightTabFolderRendererTheme(tabFolder, white);
        }


        if (logControl) {
            final String afterColours = describeControlColours(control);
            final boolean firstLog = !Boolean.TRUE.equals(control.getData(FIRST_THEME_LOG_KEY));
            if (firstLog || !beforeColours.equals(afterColours)) {
                control.setData(FIRST_THEME_LOG_KEY, Boolean.TRUE);
                logDiagnostic("theme control=%s before=%s after=%s children=%d",
                        describeControl(control),
                        beforeColours,
                        afterColours,
                        control instanceof Composite composite ? composite.getChildren().length : 0);
            }
        }
    }

    @objid ("7ba7cb4b-31f4-46bb-8b8f-72f8020aa4a4")
    private static boolean supportsLightBackground(final Control control) {
        return control instanceof Shell
                || control instanceof Composite
                || control instanceof Canvas
                || control instanceof Group
                || control instanceof ScrolledComposite
                || control instanceof Tree
                || control instanceof Table
                || control instanceof List
                || control instanceof Text
                || control instanceof StyledText
                || control instanceof Combo
                || control instanceof Spinner
                || control instanceof TabFolder
                || control instanceof ToolBar
                || control instanceof CoolBar
                || control instanceof ExpandBar
                || control instanceof Sash
                || control instanceof CTabFolder;
    }

    @objid ("7fd3402d-e863-4e56-9d38-3c5c17cf6bf0")
    private static boolean supportsDarkText(final Control control) {
        return control instanceof Shell
                || control instanceof Composite
                || control instanceof Canvas
                || control instanceof Group
                || control instanceof ScrolledComposite
                || control instanceof Tree
                || control instanceof Table
                || control instanceof List
                || control instanceof Text
                || control instanceof StyledText
                || control instanceof Combo
                || control instanceof Spinner
                || control instanceof TabFolder
                || control instanceof ToolBar
                || control instanceof CTabFolder
                || control instanceof Label
                || control instanceof Link
                || control instanceof Button;
    }

    @objid ("165a8c8e-dbfb-430e-bd2a-1494af6949d3")
    private static void installDebugProbe(final Control control) {
        if (!shouldProbeControl(control) || !isDiagnosticsEnabled() || Boolean.TRUE.equals(control.getData(DEBUG_HOOK_KEY))) {
            return;
        }

        final Listener listener = new Listener() {
            @Override
            public void handleEvent(final Event event) {
                if (control.isDisposed()) {
                    return;
                }

                if (event.type == SWT.Show) {
                    if (Boolean.TRUE.equals(control.getData(FIRST_SHOW_LOG_KEY))) {
                        return;
                    }
                    control.setData(FIRST_SHOW_LOG_KEY, Boolean.TRUE);
                } else if (event.type == SWT.Paint) {
                    if (Boolean.TRUE.equals(control.getData(FIRST_PAINT_LOG_KEY))) {
                        return;
                    }
                    control.setData(FIRST_PAINT_LOG_KEY, Boolean.TRUE);
                }

                logDiagnostic("probe event=%s control=%s colours=%s", eventName(event.type), describeControl(control), describeControlColours(control));
            }
        };

        control.addListener(SWT.Show, listener);
        control.addListener(SWT.Paint, listener);
        if (control instanceof Shell) {
            control.addListener(SWT.Activate, listener);
            control.addListener(SWT.Deactivate, listener);
        }
        control.setData(DEBUG_HOOK_KEY, Boolean.TRUE);
        logDiagnostic("probe installed control=%s", describeControl(control));
    }

    @objid ("ad012ebe-fd29-4cb7-b626-c6d9c58c66b6")
    private static boolean isDiagnosticsEnabled() {
        return Boolean.getBoolean(DEBUG_PROPERTY) || AppUi.LOG != null && AppUi.LOG.isDebugEnabled();
    }

    @objid ("81407144-2430-4bc3-9084-d30305113716")
    private static void logDiagnostic(final String format, final Object... arguments) {
        if (!isDiagnosticsEnabled()) {
            return;
        }

        final String message = "[MacAppearance] " + String.format(format, arguments);
        if (AppUi.LOG != null) {
            if (AppUi.LOG.isDebugEnabled()) {
                AppUi.LOG.debug(message);
            } else {
                AppUi.LOG.info(message);
            }
        } else {
            System.out.println(message);
        }
    }

    @objid ("50d846ae-3dbf-43da-afb6-5d8441a0a672")
    private static boolean shouldLogEvent(final Event event) {
        if (!isDiagnosticsEnabled()) {
            return false;
        }

        return event.widget instanceof Shell
                || event.widget instanceof CTabFolder
                || event.type == SWT.Settings
                || event.type == SWT.Skin;
    }

    @objid ("31d8a2e5-f043-4af5-88d2-4ee4c0ca9135")
    private static boolean shouldProbeControl(final Control control) {
        return control instanceof Shell
                || control instanceof CTabFolder
                || control instanceof Tree
                || control instanceof Table
                || control instanceof Text
                || control instanceof StyledText
                || control instanceof Combo;
    }

    @objid ("79289d76-82ce-4d06-88f6-c6d442bc0ce2")
    private static String eventName(final int eventType) {
        switch (eventType) {
        case SWT.Activate:
            return "Activate";
        case SWT.Deactivate:
            return "Deactivate";
        case SWT.Show:
            return "Show";
        case SWT.Skin:
            return "Skin";
        case SWT.Paint:
            return "Paint";
        case SWT.Settings:
            return "Settings";
        default:
            return Integer.toString(eventType);
        }
    }

    @objid ("b57a0015-5937-4b54-9ce8-9754af5d87d5")
    private static String describeDisplay(final Display display) {
        return display == null ? "null" : "Display@" + Integer.toHexString(System.identityHashCode(display));
    }

    @objid ("1110f16c-cdbd-4b83-a6e2-c245f0db78be")
    private static String describeWidget(final Object widget) {
        if (widget instanceof Control control) {
            return describeControl(control);
        }

        return widget == null ? "null" : widget.getClass().getSimpleName() + '@' + Integer.toHexString(System.identityHashCode(widget));
    }

    @objid ("a72ea605-4c41-4c64-8e2f-ea14a8904f0d")
    private static String describeControl(final Control control) {
        final String cssId = control.getData("org.eclipse.e4.ui.css.id") != null ? String.valueOf(control.getData("org.eclipse.e4.ui.css.id")) : "-";
        final String shellText = control.getShell() != null && !control.getShell().isDisposed() ? control.getShell().getText() : "-";
        return String.format("%s@%s shell=%s cssId=%s",
                control.getClass().getSimpleName(),
                Integer.toHexString(System.identityHashCode(control)),
                shellText,
                cssId);
    }

    @objid ("ed5ab682-cf85-4bf7-a4ae-868eef9b8569")
    private static String describeWidgetColours(final Object widget) {
        return widget instanceof Control control ? describeControlColours(control) : "n/a";
    }

    @objid ("7dcfb6b2-40f6-4d25-8120-ac8d4316da31")
    private static String describeControlColours(final Control control) {
        final String renderer = control instanceof CTabFolder tabFolder && tabFolder.getRenderer() != null
                ? tabFolder.getRenderer().getClass().getSimpleName()
                : "-";
        final int backgroundMode = control instanceof Shell shell
                ? shell.getBackgroundMode()
                : control instanceof Composite composite ? composite.getBackgroundMode() : -1;
        return String.format("bg=%s fg=%s mode=%d renderer=%s visible=%s",
                describeColor(control.getBackground()),
                describeColor(control.getForeground()),
                backgroundMode,
                renderer,
                control.isVisible());
    }

    @objid ("8f6cf4e3-9719-427b-99d1-2e4d7e3d11d7")
    private static String describeColor(final Color color) {
        if (color == null) {
            return "null";
        }
        if (color.isDisposed()) {
            return "disposed";
        }
        return String.format("rgb(%d,%d,%d)", color.getRed(), color.getGreen(), color.getBlue());
    }

    @objid ("0b471f4b-41ab-4069-b747-080e1a049abc")
    private static void applyLightDisplayAppearance(final Display display) {
        logDiagnostic("applyLightDisplayAppearance display=%s shells=%d", describeDisplay(display), display.getShells().length);
        try {
            final Class<?> appearanceClass = Class.forName("org.eclipse.swt.widgets.Display$APPEARANCE");
            final Object lightAppearance = getLightAppearanceValue(appearanceClass);

            invokeAppearanceMethod(display, "setAppAppearance", appearanceClass, lightAppearance);
            invokeAppearanceMethod(display, "setWindowsAppearance", appearanceClass, lightAppearance);
        } catch (final ReflectiveOperationException | RuntimeException e) {
            AppUi.LOG.debug(e);
        }
    }

    @objid ("0f7dd98f-c2e9-46e2-a7cf-a8c27fa6808d")
    private static void applyLightShellWindowAppearance(final Shell shell) {
        if (shell == null || shell.isDisposed()) {
            return;
        }

        try {
            final Field windowField = Shell.class.getDeclaredField("window");
            windowField.setAccessible(true);
            final Object nsWindow = windowField.get(shell);
            if (nsWindow == null) {
                return;
            }

            final Display display = shell.getDisplay();
            final Class<?> displayAppearanceClass = Class.forName("org.eclipse.swt.widgets.Display$APPEARANCE");
            final Object lightAppearance = getLightAppearanceValue(displayAppearanceClass);

            final Method getAppearanceMethod = Display.class.getDeclaredMethod("getAppearance", displayAppearanceClass);
            getAppearanceMethod.setAccessible(true);
            final Object nsAppearance = getAppearanceMethod.invoke(display, lightAppearance);

            final Method setWindowAppearanceMethod = Display.class.getDeclaredMethod(
                    "setWindowAppearance",
                    Class.forName("org.eclipse.swt.internal.cocoa.NSWindow"),
                    Class.forName("org.eclipse.swt.internal.cocoa.NSAppearance"));
            setWindowAppearanceMethod.setAccessible(true);
            setWindowAppearanceMethod.invoke(display, nsWindow, nsAppearance);

            if (!Boolean.TRUE.equals(shell.getData(SHELL_WINDOW_THEME_KEY))) {
                shell.setData(SHELL_WINDOW_THEME_KEY, Boolean.TRUE);
                logDiagnostic("shell window appearance themed shell=%s", describeControl(shell));
            }
        } catch (final ReflectiveOperationException | RuntimeException e) {
            AppUi.LOG.debug(e);
        }
    }

    @objid ("49a1d609-6f54-4bcb-aef5-6d7f5ff04a85")
    private static Object getLightAppearanceValue(final Class<?> appearanceClass) throws ReflectiveOperationException {
        final Field lightField = appearanceClass.getField("Light");
        lightField.setAccessible(true);
        return lightField.get(null);
    }

    @objid ("1bb0c6c7-bf8b-42d1-9404-93f5f71603bc")
    private static void applyLightTabFolderRendererTheme(final CTabFolder tabFolder, final Color white) {
        try {
            final Object renderer = tabFolder.getRenderer();
            if (renderer == null || !"org.eclipse.e4.ui.workbench.renderers.swt.CTabRendering".equals(renderer.getClass().getName())) {
                logDiagnostic("tabFolder renderer skipped control=%s renderer=%s", describeControl(tabFolder), renderer == null ? "null" : renderer.getClass().getName());
                return;
            }

            logDiagnostic("tabFolder renderer themed control=%s renderer=%s", describeControl(tabFolder), renderer.getClass().getName());

            invokeRendererMethod(renderer, "setSelectedTabFill", new Class<?>[] { Color[].class, int[].class },
                    new Object[] { new Color[] { white, white }, new int[] { 100 } });
            invokeRendererMethod(renderer, "setUnselectedTabsColor", new Class<?>[] { Color[].class, int[].class },
                    new Object[] { new Color[] { white, white }, new int[] { 100 } });
            invokeRendererMethod(renderer, "setTabOutline", new Class<?>[] { Color.class }, new Object[] { white });
            invokeRendererMethod(renderer, "setInnerKeyline", new Class<?>[] { Color.class }, new Object[] { white });
            invokeRendererMethod(renderer, "setOuterKeyline", new Class<?>[] { Color.class }, new Object[] { white });
            invokeRendererMethod(renderer, "setSelectedTabHighlight", new Class<?>[] { Color.class }, new Object[] { white });
            invokeRendererMethod(renderer, "setDrawCustomTabContentBackground", new Class<?>[] { boolean.class },
                    new Object[] { Boolean.TRUE });
            invokeRendererMethod(renderer, "setActive", new Class<?>[] { boolean.class }, new Object[] { Boolean.TRUE });
        } catch (final ReflectiveOperationException | RuntimeException e) {
            AppUi.LOG.debug(e);
        }
    }

    @objid ("18d31b6f-754f-45f5-8d20-0fe7d8c1a6d8")
    private static void invokeRendererMethod(final Object renderer, final String methodName, final Class<?>[] parameterTypes,
            final Object[] arguments) throws ReflectiveOperationException {
        final Method method = renderer.getClass().getMethod(methodName, parameterTypes);
        method.setAccessible(true);
        method.invoke(renderer, arguments);
    }

    @objid ("3984f56e-52e7-4bf1-b18d-8d53d13bb7e8")
    private static void invokeAppearanceMethod(final Display display, final String methodName, final Class<?> appearanceClass, final Object appearance)
            throws ReflectiveOperationException {
        final Method method = Display.class.getDeclaredMethod(methodName, appearanceClass);
        method.setAccessible(true);
        method.invoke(display, appearance);
    }
}
