package org.modelio.platform.utils.plugin;

import java.io.IOException;

/**
 * Internal logging backend contract used by {@link Utils}.
 */
public interface LoggingBackend {
    /**
     * Configure the backend for Modelio runtime logging.
     * @throws IOException if the backend configuration cannot be loaded.
     */
    void configure() throws IOException;

    /**
     * Stop the backend and release any runtime resources.
     */
    void stop();

    /**
     * @return the current Modelio logfile path, or {@code null} if unavailable.
     */
    String getLogFile();
}

