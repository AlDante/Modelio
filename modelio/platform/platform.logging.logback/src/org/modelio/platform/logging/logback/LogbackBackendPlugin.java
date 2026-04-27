package org.modelio.platform.logging.logback;

import org.modelio.platform.utils.plugin.LoggingBackend;
import org.osgi.framework.BundleActivator;
import org.osgi.framework.BundleContext;
import org.osgi.framework.ServiceRegistration;

/**
 * Registers the Logback-backed logging service for Modelio startup.
 */
public class LogbackBackendPlugin implements BundleActivator {
    private ServiceRegistration<LoggingBackend> registration;

    private LogbackLoggingBackend loggingBackend;

    @Override
    public void start(BundleContext bundleContext) {
        this.loggingBackend = new LogbackLoggingBackend(bundleContext.getBundle());
        this.registration = bundleContext.registerService(LoggingBackend.class, this.loggingBackend, null);
    }

    @Override
    public void stop(BundleContext bundleContext) {
        if (this.loggingBackend != null) {
            this.loggingBackend.stop();
            this.loggingBackend = null;
        }
        if (this.registration != null) {
            this.registration.unregister();
            this.registration = null;
        }
    }
}

