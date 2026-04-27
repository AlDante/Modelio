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
import org.osgi.framework.Bundle;
import org.slf4j.ILoggerFactory;
import org.slf4j.LoggerFactory;

final class LogbackLoggingBackend implements LoggingBackend {
    private final Bundle bundle;

    LogbackLoggingBackend(Bundle bundle) {
        this.bundle = bundle;
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

    private static LoggerContext getRequiredLoggerContext() {
        LoggerContext loggerContext = getLoggerContext();
        if (loggerContext != null) {
            return loggerContext;
        }

        ILoggerFactory loggerFactory = LoggerFactory.getILoggerFactory();
        String actualFactory = loggerFactory == null ? "null" : loggerFactory.getClass().getName();
        throw new IllegalStateException("Expected Logback LoggerContext but got " + actualFactory);
    }

    private static LoggerContext getLoggerContext() {
        ILoggerFactory loggerFactory = LoggerFactory.getILoggerFactory();
        if (loggerFactory instanceof LoggerContext) {
            return (LoggerContext) loggerFactory;
        }
        return null;
    }
}

