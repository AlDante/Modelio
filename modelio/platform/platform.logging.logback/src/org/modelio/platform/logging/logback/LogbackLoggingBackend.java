package org.modelio.platform.logging.logback;

import java.io.IOException;
import java.net.URL;
import java.util.Iterator;
import ch.qos.logback.classic.Logger;
import ch.qos.logback.classic.LoggerContext;
import ch.qos.logback.classic.joran.JoranConfigurator;
import ch.qos.logback.classic.spi.ILoggingEvent;
import ch.qos.logback.core.Appender;
import ch.qos.logback.core.FileAppender;
import ch.qos.logback.core.joran.spi.JoranException;
import org.eclipse.core.runtime.FileLocator;
import org.eclipse.core.runtime.Path;
import org.modelio.platform.utils.plugin.LoggingBackend;
import org.modelio.version.ModelioVersion;
import org.osgi.framework.BundleContext;
import org.osgi.framework.Bundle;
import org.osgi.framework.ServiceReference;
import org.slf4j.ILoggerFactory;
import org.slf4j.LoggerFactory;
import org.slf4j.spi.SLF4JServiceProvider;

final class LogbackLoggingBackend implements LoggingBackend {
    private static final long PROVIDER_WAIT_TIMEOUT_MILLIS = 5_000L;

    private static final long LOGGER_CONTEXT_WAIT_TIMEOUT_MILLIS = 2_000L;

    private static final long LOGGER_CONTEXT_RETRY_DELAY_MILLIS = 100L;

    private final BundleContext bundleContext;

    private final Bundle bundle;

    LogbackLoggingBackend(BundleContext bundleContext) {
        this.bundleContext = bundleContext;
        this.bundle = bundleContext.getBundle();
    }

    @Override
    public void configure() throws IOException {
        LoggerContext context = getRequiredLoggerContext();
        JoranConfigurator configurator = new JoranConfigurator();
        configurator.setContext(context);
        context.reset();
        context.putProperty("MODELIO_VERSION_SUBDIR", getVersionSubdirectory());

        URL logbackConfigFileUrl = FileLocator.find(this.bundle, new Path("config/logback.xml"), null);
        if (logbackConfigFileUrl == null) {
            throw new IOException("Unable to locate config/logback.xml in bundle " + this.bundle.getSymbolicName());
        }

        try (var logbackConfigStream = logbackConfigFileUrl.openStream()) {
            configurator.doConfigure(logbackConfigStream);
        } catch (JoranException e) {
            throw new IOException("Unable to configure Logback in bundle " + this.bundle.getSymbolicName(), e);
        }
    }

    private static String getVersionSubdirectory() {
        String[] versionParts = ModelioVersion.STR_VERSION.split("\\.");
        if (versionParts.length >= 2) {
            return versionParts[0] + "." + versionParts[1];
        }
        return ModelioVersion.STR_VERSION;
    }

    @Override
    public void stop() {
        LoggerContext loggerContext = getLoggerContext();
        if (loggerContext != null) {
            loggerContext.stop();
        }
    }

    @Override
    public String getLogFile() {
        LoggerContext loggerContext = getLoggerContext();
        if (loggerContext == null) {
            return null;
        }

        Logger rootLogger = loggerContext.getLogger(org.slf4j.Logger.ROOT_LOGGER_NAME);
        Appender<ILoggingEvent> appender = rootLogger.getAppender("LOGFILE");
        if (appender instanceof FileAppender<?>) {
            return ((FileAppender<?>) appender).getFile();
        }

        Iterator<Appender<ILoggingEvent>> appenders = rootLogger.iteratorForAppenders();
        while (appenders.hasNext()) {
            Appender<ILoggingEvent> currentAppender = appenders.next();
            if (currentAppender instanceof FileAppender<?>) {
                return ((FileAppender<?>) currentAppender).getFile();
            }
        }
        return null;
    }

    private LoggerContext getRequiredLoggerContext() {
        waitForSlf4jProviderRegistration();

        LoggerContext loggerContext = waitForLoggerContext();
        if (loggerContext != null) {
            return loggerContext;
        }

        ILoggerFactory loggerFactory = LoggerFactory.getILoggerFactory();
        String actualFactory = loggerFactory == null ? "null" : loggerFactory.getClass().getName();
        throw new IllegalStateException("Expected Logback LoggerContext but got " + actualFactory);
    }

    private void waitForSlf4jProviderRegistration() {
        ServiceReference<SLF4JServiceProvider> reference = this.bundleContext.getServiceReference(SLF4JServiceProvider.class);
        if (reference != null) {
            return;
        }

        long deadline = System.nanoTime() + (PROVIDER_WAIT_TIMEOUT_MILLIS * 1_000_000L);
        while (System.nanoTime() < deadline) {
            sleepQuietly(LOGGER_CONTEXT_RETRY_DELAY_MILLIS, "Interrupted while waiting for SLF4J provider registration.");
            reference = this.bundleContext.getServiceReference(SLF4JServiceProvider.class);
            if (reference != null) {
                return;
            }
        }

        throw new IllegalStateException(
                "Timed out waiting for OSGi registration of org.slf4j.spi.SLF4JServiceProvider. "
                + "Ensure org.apache.aries.spifly.dynamic.bundle is present and started before logging backend configuration."
        );
    }

    private static LoggerContext waitForLoggerContext() {
        LoggerContext loggerContext = getLoggerContext();
        if (loggerContext != null) {
            return loggerContext;
        }

        long deadline = System.nanoTime() + (LOGGER_CONTEXT_WAIT_TIMEOUT_MILLIS * 1_000_000L);
        while (System.nanoTime() < deadline) {
            sleepQuietly(LOGGER_CONTEXT_RETRY_DELAY_MILLIS, "Interrupted while waiting for Logback LoggerContext initialization.");
            loggerContext = getLoggerContext();
            if (loggerContext != null) {
                return loggerContext;
            }
        }

        return getLoggerContext();
    }

    private static void sleepQuietly(long delayMillis, String interruptionMessage) {
        try {
            Thread.sleep(delayMillis);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException(interruptionMessage, e);
        }
    }

    private static LoggerContext getLoggerContext() {
        ILoggerFactory loggerFactory = LoggerFactory.getILoggerFactory();
        if (loggerFactory instanceof LoggerContext) {
            return (LoggerContext) loggerFactory;
        }
        return null;
    }
}

