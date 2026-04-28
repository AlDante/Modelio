/*
 * Copyright 2013-2020 Modeliosoft
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
package org.modelio.diagram.editor.plugin;

import java.lang.reflect.Field;
import org.eclipse.e4.core.contexts.IEclipseContext;
import org.eclipse.ui.PlatformUI;

/**
 * Compatibility bridge for GEF 3.25 in pure E4 applications.
 * <p>
 * GEF 3.25 introduced {@code PaletteColorProvider} which has a static
 * initialiser that calls {@code PlatformUI.getWorkbench().getThemeManager()}.
 * In a pure E4 application (using {@code E4Application}), the compatibility
 * {@code Workbench} singleton is never created, so this call throws
 * {@code IllegalStateException}. Since the failure occurs in {@code <clinit>},
 * the class is permanently marked as failed by the JVM and no
 * {@code PaletteViewer} can ever be constructed, which makes the diagram
 * palette invisible.
 * <p>
 * This bridge pre-populates the internal {@code Workbench.instance} field
 * with a minimal, constructor-free instance whose {@code serviceLocator} is
 * wired to the E4 {@code IEclipseContext}. This is enough for
 * {@code PaletteColorProvider.<clinit>} to succeed and for the
 * {@code WorkbenchThemeManager} to resolve themes through the E4 context.
 * <p>
 * <b>Fragility note</b> &mdash; this class depends on the internal field
 * names {@code org.eclipse.ui.internal.Workbench.instance},
 * {@code org.eclipse.ui.internal.Workbench.serviceLocator}, and
 * {@code org.eclipse.ui.internal.services.ServiceLocator.e4Context}. These
 * are private implementation details of the Eclipse Platform and may change
 * between versions. The current implementation targets Eclipse 2026-03
 * ({@code org.eclipse.ui.workbench 3.138.x}). If the Platform upgrades,
 * verify the field names and adjust accordingly.
 *
 * @see <a href="https://github.com/eclipse/gef-classic">GEF Classic</a>
 */
public final class GefWorkbenchBridge {

    private static volatile boolean initialized = false;

    private GefWorkbenchBridge() {
        // Utility class
    }

    /**
     * Ensure that {@code PlatformUI.getWorkbench()} will not throw when called
     * by GEF 3.25's {@code PaletteColorProvider} static initialiser.
     * <p>
     * If the compatibility workbench is already available, this method is a
     * no-op. Otherwise it creates a minimal reflective shim wired to the
     * given E4 context.
     *
     * @param partContext the {@link IEclipseContext} of the calling part
     *                    (typically from {@code MPart.getContext()}).
     *                    The method walks up to the root context automatically.
     */
    public static synchronized void ensureWorkbench(IEclipseContext partContext) {
        if (initialized) {
            return;
        }
        initialized = true;

        // If the compatibility workbench is already running, nothing to do.
        if (PlatformUI.isWorkbenchRunning()) {
            return;
        }

        try {
            doEnsureWorkbench(partContext);
        } catch (Throwable t) {
            // Never crash the diagram editor for a bridge failure.
            // The palette may be invisible, but the rest of the editor
            // should still work.
            DiagramEditor.LOG.warning("GefWorkbenchBridge: Failed to set up the Workbench compatibility shim for GEF 3.25. "
                    + "The diagram palette may not be visible. Cause: %s", t.toString());
        }
    }

    private static void doEnsureWorkbench(IEclipseContext partContext) throws Exception {
        // Walk up to the application-level (root) context.
        IEclipseContext rootContext = partContext;
        while (rootContext.getParent() != null) {
            rootContext = rootContext.getParent();
        }

        // Obtain sun.misc.Unsafe so we can allocate a Workbench without
        // calling its complex private constructor.
        Object unsafe = getUnsafe();
        Class<?> unsafeClass = unsafe.getClass();
        java.lang.reflect.Method allocateInstance =
                unsafeClass.getMethod("allocateInstance", Class.class);

        // --- Create a bare Workbench instance ---
        Class<?> workbenchClass =
                Class.forName("org.eclipse.ui.internal.Workbench");
        Object workbenchInstance = allocateInstance.invoke(unsafe, workbenchClass);

        // --- Create a ServiceLocator wired to the root IEclipseContext ---
        Class<?> serviceLocatorClass =
                Class.forName("org.eclipse.ui.internal.services.ServiceLocator");
        Object serviceLocator = allocateInstance.invoke(unsafe, serviceLocatorClass);

        Field e4ContextField = serviceLocatorClass.getDeclaredField("e4Context");
        e4ContextField.setAccessible(true);
        e4ContextField.set(serviceLocator, rootContext);

        // --- Wire the Workbench's serviceLocator ---
        Field serviceLocatorField = workbenchClass.getDeclaredField("serviceLocator");
        serviceLocatorField.setAccessible(true);
        serviceLocatorField.set(workbenchInstance, serviceLocator);

        // --- Set the static Workbench.instance field ---
        Field instanceField = workbenchClass.getDeclaredField("instance");
        instanceField.setAccessible(true);
        if (instanceField.get(null) == null) {
            instanceField.set(null, workbenchInstance);
            DiagramEditor.LOG.info("GefWorkbenchBridge: Installed minimal Workbench shim for GEF 3.25 palette support.");
        }
    }

    /**
     * Obtain the {@code sun.misc.Unsafe} singleton via reflection.
     */
    private static Object getUnsafe() throws Exception {
        Class<?> unsafeClass = Class.forName("sun.misc.Unsafe");
        Field theUnsafeField = unsafeClass.getDeclaredField("theUnsafe");
        theUnsafeField.setAccessible(true);
        return theUnsafeField.get(null);
    }
}

