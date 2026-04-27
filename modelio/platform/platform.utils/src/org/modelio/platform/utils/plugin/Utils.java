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
package org.modelio.platform.utils.plugin;

import java.io.IOException;
import com.modeliosoft.modelio.javadesigner.annotations.objid;
import org.osgi.framework.Bundle;
import org.osgi.framework.BundleActivator;
import org.osgi.framework.BundleContext;
import org.osgi.framework.BundleException;
import org.osgi.framework.ServiceReference;

@objid ("0049aab6-4382-1fe3-9845-001ec947cd2a")
public class Utils implements BundleActivator {
    @objid ("0055b0ea-4447-1fe3-9845-001ec947cd2a")
    public static final String PLUGIN_ID = "org.modelio.platform.utils";

    private static final String DEFAULT_LOGGING_BACKEND_BUNDLE = "org.modelio.platform.logging.logback";

    private static LoggingBackend loggingBackend;

    private static ServiceReference<LoggingBackend> loggingBackendReference;

    @objid ("004ffcae-4447-1fe3-9845-001ec947cd2a")
    @Override
    public void start(BundleContext bundleContext) {
        bindLoggingBackend(bundleContext);
        if (Utils.loggingBackend != null) {
            try {
                Utils.loggingBackend.configure();
            } catch (IOException | IllegalStateException e) {
                e.printStackTrace();
            }
        } else {
            System.err.println("No logging backend service available for " + Utils.PLUGIN_ID);
        }
        plugKernelLogToEclipseLog();
        
    }

    @objid ("005028aa-4447-1fe3-9845-001ec947cd2a")
    @Override
    public void stop(BundleContext bundleContext) {
        if (Utils.loggingBackend != null) {
            Utils.loggingBackend.stop();
        }
        releaseLoggingBackend(bundleContext);

    }

    private static void bindLoggingBackend(BundleContext bundleContext) {
        ServiceReference<LoggingBackend> reference = bundleContext.getServiceReference(LoggingBackend.class);
        if (reference == null) {
            startDefaultLoggingBackend(bundleContext);
            reference = bundleContext.getServiceReference(LoggingBackend.class);
        }
        if (reference == null) {
            return;
        }

        LoggingBackend backend = bundleContext.getService(reference);
        if (backend == null) {
            return;
        }

        Utils.loggingBackendReference = reference;
        Utils.loggingBackend = backend;
    }

    private static void startDefaultLoggingBackend(BundleContext bundleContext) {
        Bundle backendBundle = findBundle(bundleContext, DEFAULT_LOGGING_BACKEND_BUNDLE);
        if (backendBundle == null || backendBundle.getState() == Bundle.UNINSTALLED) {
            return;
        }
        try {
            if (backendBundle.getState() != Bundle.ACTIVE) {
                backendBundle.start(Bundle.START_TRANSIENT);
            }
        } catch (BundleException e) {
            e.printStackTrace();
        }
    }

    private static Bundle findBundle(BundleContext bundleContext, String symbolicName) {
        for (Bundle installedBundle : bundleContext.getBundles()) {
            if (symbolicName.equals(installedBundle.getSymbolicName())) {
                return installedBundle;
            }
        }
        return null;
    }

    private static void releaseLoggingBackend(BundleContext bundleContext) {
        ServiceReference<LoggingBackend> reference = Utils.loggingBackendReference;
        Utils.loggingBackend = null;
        Utils.loggingBackendReference = null;
        if (reference != null) {
            bundleContext.ungetService(reference);
        }
    }

    @objid ("5d0016a8-64f0-493c-9f8f-0158238c4637")
    private void plugKernelLogToEclipseLog() {
        // Set Modelio kernel logger
        org.modelio.vbasic.log.Log.setLogger(new KernelLogger());
        
    }

    /**
     * Find the current Modelio log file from the active logging backend.
     * @return the current Modelio log file, null if unable to find it.
     */
    @objid ("2ba8983e-a272-477b-811d-dc94502b0907")
    public static String getLogFile() {
        if (Utils.loggingBackend == null) {
            return null;
        }
        return Utils.loggingBackend.getLogFile();
    }

}
