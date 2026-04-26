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
import java.net.URL;
import java.util.Iterator;
import ch.qos.logback.classic.Logger;
import ch.qos.logback.classic.LoggerContext;
import ch.qos.logback.classic.joran.JoranConfigurator;
import ch.qos.logback.classic.spi.ILoggingEvent;
import ch.qos.logback.core.Appender;
import ch.qos.logback.core.FileAppender;
import ch.qos.logback.core.joran.spi.JoranException;
import com.modeliosoft.modelio.javadesigner.annotations.objid;
import org.eclipse.core.runtime.FileLocator;
import org.eclipse.core.runtime.Path;
import org.modelio.version.ModelioVersion;
import org.osgi.framework.Bundle;
import org.osgi.framework.BundleActivator;
import org.osgi.framework.BundleContext;
import org.slf4j.ILoggerFactory;
import org.slf4j.LoggerFactory;

@objid ("0049aab6-4382-1fe3-9845-001ec947cd2a")
public class Utils implements BundleActivator {
    @objid ("0055b0ea-4447-1fe3-9845-001ec947cd2a")
    public static final String PLUGIN_ID = "org.modelio.platform.utils";

    @objid ("004ffcae-4447-1fe3-9845-001ec947cd2a")
    @Override
    public void start(BundleContext bundleContext) {
        try {
            configureLogbackInBundle(bundleContext.getBundle());
        } catch (JoranException | IOException | IllegalStateException e) {
            e.printStackTrace();
        }
        plugKernelLogToEclipseLog();
        
    }

    @objid ("f7d6e294-28b7-4056-86c0-197f5ccb3f52")
    private void configureLogbackInBundle(Bundle bundle) throws IOException, JoranException {
        LoggerContext context = getRequiredLoggerContext();
        JoranConfigurator jc = new JoranConfigurator();
        jc.setContext(context);
        context.reset();
        
        // overriding the log directory property programmatically
        context.putProperty("MODELIO_VERSION_SUBDIR", ModelioVersion.VERSION.toString("V.R"));
        
        // this assumes that the logback.xml file is in the root of the bundle.
        URL logbackConfigFileUrl = FileLocator.find(bundle, new Path("config/logback.xml"), null);
        if (logbackConfigFileUrl == null) {
            throw new IOException("Unable to locate config/logback.xml in bundle " + bundle.getSymbolicName());
        }
        try (var logbackConfigStream = logbackConfigFileUrl.openStream()) {
            jc.doConfigure(logbackConfigStream);
        }

    }

    @objid ("005028aa-4447-1fe3-9845-001ec947cd2a")
    @Override
    public void stop(BundleContext bundleContext) {
        LoggerContext loggerContext = getLoggerContext();
        if (loggerContext != null) {
            loggerContext.stop();
        }

    }

    private static LoggerContext getRequiredLoggerContext() {
        LoggerContext loggerContext = getLoggerContext();
        if (loggerContext != null) {
            return loggerContext;
        }

        ILoggerFactory loggerFactory = LoggerFactory.getILoggerFactory();
        String actualFactory = loggerFactory == null ? "null" : loggerFactory.getClass().getName();
        throw new IllegalStateException("Expected Logback LoggerContext for " + PLUGIN_ID + " but got " + actualFactory);
    }

    private static LoggerContext getLoggerContext() {
        ILoggerFactory loggerFactory = LoggerFactory.getILoggerFactory();
        if (loggerFactory instanceof LoggerContext) {
            return (LoggerContext) loggerFactory;
        }
        return null;
    }

    @objid ("5d0016a8-64f0-493c-9f8f-0158238c4637")
    private void plugKernelLogToEclipseLog() {
        // Set Modelio kernel logger
        org.modelio.vbasic.log.Log.setLogger(new KernelLogger());
        
    }

    /**
     * Find the current Modelio log file from the logback current configuration.
     * @return the current Modelio log file, null if unable to find it.
     */
    @objid ("2ba8983e-a272-477b-811d-dc94502b0907")
    public static String getLogFile() {
        LoggerContext lc = getLoggerContext();
        if (lc == null) {
            return null;
        }

        // Look for default FILE appender on the root logger.
        Logger rootLogger = lc.getLogger(org.slf4j.Logger.ROOT_LOGGER_NAME);
        
        Appender<ILoggingEvent> appender = rootLogger.getAppender("LOGFILE");
        if (appender instanceof FileAppender<?>) {
            return ((FileAppender<?>) appender).getFile();
        }
        
        // Configuration file hacked, return the first file appender.
        Iterator<Appender<ILoggingEvent>> it = rootLogger.iteratorForAppenders();
        while (it.hasNext()) {
            Appender<ILoggingEvent> append = it.next();
            if (append instanceof FileAppender<?>) {
                return ((FileAppender<?>) append).getFile();
            }
        }
        
        // don't know what to do
        return null;
    }

}
