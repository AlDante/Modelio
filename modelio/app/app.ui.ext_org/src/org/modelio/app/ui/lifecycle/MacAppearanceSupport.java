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
import org.eclipse.swt.widgets.Display;
import org.modelio.app.ui.plugin.AppUi;

/**
 * Forces Modelio to use the SWT/Cocoa Aqua appearance on macOS.
 * <p>
 * Modelio's workbench colours are designed for a light theme. Recent SWT builds
 * can inherit macOS dark appearance at the native Cocoa level, which makes SWT
 * controls such as trees and part stacks dark while the diagram canvas remains
 * light. The public SWT API only exposes dark-theme detection, so this class uses
 * the package-private SWT appearance hooks reflectively and degrades gracefully if
 * they change in a future SWT release.
 */
@objid ("ec94be3e-b342-4b40-bf74-d3937de66f0b")
final class MacAppearanceSupport {
    @objid ("b9a8d9f7-ae2e-48d4-96c2-bf6f2e8bda0b")
    private static final String USE_SYSTEM_THEME_PROPERTY = "org.eclipse.swt.display.useSystemTheme";

    @objid ("2bc8917a-75dc-4a3d-b6e4-6f3aee0b0877")
    private MacAppearanceSupport() {
        // Utility class.
    }

    @objid ("3f4cbf20-3285-4a27-924d-ce7c45c9de6e")
    static void forceLightAppearance() {
        System.setProperty(MacAppearanceSupport.USE_SYSTEM_THEME_PROPERTY, "false");

        if (!"cocoa".equals(SWT.getPlatform())) {
            return;
        }

        final Display display = Display.getCurrent() != null ? Display.getCurrent() : Display.getDefault();
        if (display == null || display.isDisposed()) {
            return;
        }

        try {
            final Class<?> appearanceClass = Class.forName("org.eclipse.swt.widgets.Display$APPEARANCE");
            final Field lightField = appearanceClass.getField("Light");
            lightField.setAccessible(true);
            final Object lightAppearance = lightField.get(null);

            invokeAppearanceMethod(display, "setAppAppearance", appearanceClass, lightAppearance);
            invokeAppearanceMethod(display, "setWindowsAppearance", appearanceClass, lightAppearance);
        } catch (final ReflectiveOperationException | RuntimeException e) {
            AppUi.LOG.debug(e);
        }
    }

    @objid ("3984f56e-52e7-4bf1-b18d-8d53d13bb7e8")
    private static void invokeAppearanceMethod(final Display display, final String methodName, final Class<?> appearanceClass, final Object appearance)
            throws ReflectiveOperationException {
        final Method method = Display.class.getDeclaredMethod(methodName, appearanceClass);
        method.setAccessible(true);
        method.invoke(display, appearance);
    }
}
