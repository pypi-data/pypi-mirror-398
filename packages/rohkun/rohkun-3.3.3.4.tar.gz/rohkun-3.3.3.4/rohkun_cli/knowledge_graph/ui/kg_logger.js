/**
 * Knowledge Graph Logger
 * External logging system that intercepts and logs all API calls, errors, and events
 * to the browser console without modifying existing code.
 * 
 * Usage: Include this file before graph_v2.html's main script
 */

(function() {
    'use strict';
    
    // Logger configuration
    const LOG_CONFIG = {
        enabled: true,
        logLevel: 'debug', // 'debug', 'info', 'warn', 'error'
        logAPI: true,
        logErrors: true,
        logEvents: true,
        logPerformance: true,
        timestamp: true,
        colors: {
            debug: '#9ca3af',
            info: '#3b82f6',
            warn: '#FFE600',
            error: '#FF003C',
            success: '#00FF94',
            api: '#7c3aed'
        }
    };
    
    // Log levels
    const LOG_LEVELS = {
        debug: 0,
        info: 1,
        warn: 2,
        error: 3
    };
    
    // Logger class
    class KGLogger {
        constructor() {
            this.logs = [];
            this.apiCalls = [];
            this.errors = [];
            this.performance = [];
            this.startTime = performance.now();
            
            // Store original console methods BEFORE intercepting
            this.originalConsole = {
                log: console.log.bind(console),
                error: console.error.bind(console),
                warn: console.warn.bind(console),
                info: console.info.bind(console)
            };
            
            this.setupInterceptors();
            this.log('info', '🔷 Knowledge Graph Logger initialized', { timestamp: new Date().toISOString() });
        }
        
        /**
         * Setup interceptors for fetch, console, and errors
         */
        setupInterceptors() {
            // Intercept fetch API calls
            if (LOG_CONFIG.logAPI) {
                this.interceptFetch();
            }
            
            // Intercept console methods
            this.interceptConsole();
            
            // Intercept global errors
            if (LOG_CONFIG.logErrors) {
                this.interceptErrors();
            }
            
            // Intercept performance
            if (LOG_CONFIG.logPerformance) {
                this.interceptPerformance();
            }
        }
        
        /**
         * Intercept fetch API calls
         */
        interceptFetch() {
            const originalFetch = window.fetch;
            const self = this;
            
            window.fetch = function(...args) {
                const url = args[0];
                const options = args[1] || {};
                const method = options.method || 'GET';
                const startTime = performance.now();
                
                // Log request
                self.log('api', `🌐 ${method} ${url}`, {
                    method,
                    url,
                    headers: options.headers,
                    body: options.body
                });
                
                // Call original fetch
                return originalFetch.apply(this, args)
                    .then(response => {
                        const duration = performance.now() - startTime;
                        
                        // Clone response to read body without consuming it
                        const clonedResponse = response.clone();
                        
                        // Log response
                        clonedResponse.text().then(text => {
                            let responseData = null;
                            try {
                                responseData = JSON.parse(text);
                            } catch (e) {
                                responseData = text;
                            }
                            
                            if (response.ok) {
                                self.log('success', `✅ ${method} ${url} - ${response.status} (${duration.toFixed(2)}ms)`, {
                                    status: response.status,
                                    statusText: response.statusText,
                                    duration,
                                    data: responseData
                                });
                            } else {
                                self.log('error', `❌ ${method} ${url} - ${response.status} ${response.statusText} (${duration.toFixed(2)}ms)`, {
                                    status: response.status,
                                    statusText: response.statusText,
                                    duration,
                                    error: responseData
                                });
                            }
                            
                            // Store API call
                            self.apiCalls.push({
                                method,
                                url,
                                status: response.status,
                                duration,
                                timestamp: new Date().toISOString(),
                                request: { headers: options.headers, body: options.body },
                                response: responseData
                            });
                        }).catch(err => {
                            self.log('error', `❌ Failed to parse response for ${url}`, { error: err.message });
                        });
                        
                        return response;
                    })
                    .catch(error => {
                        const duration = performance.now() - startTime;
                        self.log('error', `❌ ${method} ${url} - Network Error (${duration.toFixed(2)}ms)`, {
                            error: error.message,
                            duration
                        });
                        
                        self.errors.push({
                            type: 'network',
                            method,
                            url,
                            error: error.message,
                            timestamp: new Date().toISOString()
                        });
                        
                        throw error;
                    });
            };
        }
        
        /**
         * Intercept console methods
         */
        interceptConsole() {
            const self = this;
            
            console.log = function(...args) {
                self.log('debug', args.join(' '), { args });
                self.originalConsole.log.apply(console, args);
            };
            
            console.error = function(...args) {
                self.log('error', args.join(' '), { args });
                self.originalConsole.error.apply(console, args);
            };
            
            console.warn = function(...args) {
                self.log('warn', args.join(' '), { args });
                self.originalConsole.warn.apply(console, args);
            };
            
            console.info = function(...args) {
                self.log('info', args.join(' '), { args });
                self.originalConsole.info.apply(console, args);
            };
        }
        
        /**
         * Intercept global errors
         */
        interceptErrors() {
            const self = this;
            
            // Unhandled errors
            window.addEventListener('error', (event) => {
                self.log('error', `💥 Unhandled Error: ${event.message}`, {
                    message: event.message,
                    filename: event.filename,
                    lineno: event.lineno,
                    colno: event.colno,
                    error: event.error
                });
                
                self.errors.push({
                    type: 'unhandled',
                    message: event.message,
                    filename: event.filename,
                    lineno: event.lineno,
                    colno: event.colno,
                    stack: event.error?.stack,
                    timestamp: new Date().toISOString()
                });
            });
            
            // Unhandled promise rejections
            window.addEventListener('unhandledrejection', (event) => {
                self.log('error', `💥 Unhandled Promise Rejection: ${event.reason}`, {
                    reason: event.reason,
                    error: event.reason
                });
                
                self.errors.push({
                    type: 'promise',
                    reason: event.reason?.toString(),
                    stack: event.reason?.stack,
                    timestamp: new Date().toISOString()
                });
            });
        }
        
        /**
         * Intercept performance metrics
         */
        interceptPerformance() {
            const self = this;
            
            // Monitor long tasks
            if ('PerformanceObserver' in window) {
                try {
                    const observer = new PerformanceObserver((list) => {
                        for (const entry of list.getEntries()) {
                            if (entry.duration > 50) { // Log tasks longer than 50ms
                                self.log('warn', `⏱️ Long Task: ${entry.duration.toFixed(2)}ms`, {
                                    duration: entry.duration,
                                    name: entry.name,
                                    startTime: entry.startTime
                                });
                                
                                self.performance.push({
                                    type: 'long-task',
                                    duration: entry.duration,
                                    name: entry.name,
                                    timestamp: new Date().toISOString()
                                });
                            }
                        }
                    });
                    observer.observe({ entryTypes: ['measure', 'navigation'] });
                } catch (e) {
                    // PerformanceObserver not supported
                }
            }
        }
        
        /**
         * Main log method
         */
        log(level, message, data = {}) {
            if (!LOG_CONFIG.enabled) return;
            
            const levelNum = LOG_LEVELS[level] || 0;
            const configLevelNum = LOG_LEVELS[LOG_CONFIG.logLevel] || 0;
            
            if (levelNum < configLevelNum) return;
            
            const timestamp = LOG_CONFIG.timestamp ? 
                `[${new Date().toLocaleTimeString()}]` : '';
            
            const color = LOG_CONFIG.colors[level] || LOG_CONFIG.colors.info;
            const prefix = `%c${timestamp} [KG-LOG]`;
            const style = `color: ${color}; font-weight: bold; font-family: 'JetBrains Mono', monospace;`;
            
            // Store log
            const logEntry = {
                level,
                message,
                data,
                timestamp: new Date().toISOString(),
                timeSinceStart: (performance.now() - this.startTime).toFixed(2) + 'ms'
            };
            
            this.logs.push(logEntry);
            
            // Keep only last 1000 logs
            if (this.logs.length > 1000) {
                this.logs.shift();
            }
            
            // Output to console using original console method to avoid recursion
            if (Object.keys(data).length > 0) {
                this.originalConsole.log(prefix, style, message, data);
            } else {
                this.originalConsole.log(prefix, style, message);
            }
        }
        
        /**
         * Get all logs
         */
        getLogs() {
            return this.logs;
        }
        
        /**
         * Get API calls
         */
        getAPICalls() {
            return this.apiCalls;
        }
        
        /**
         * Get errors
         */
        getErrors() {
            return this.errors;
        }
        
        /**
         * Get performance metrics
         */
        getPerformance() {
            return this.performance;
        }
        
        /**
         * Get summary
         */
        getSummary() {
            return {
                totalLogs: this.logs.length,
                apiCalls: this.apiCalls.length,
                errors: this.errors.length,
                performance: this.performance.length,
                uptime: (performance.now() - this.startTime).toFixed(2) + 'ms',
                timestamp: new Date().toISOString()
            };
        }
        
        /**
         * Export logs
         */
        exportLogs() {
            return {
                logs: this.logs,
                apiCalls: this.apiCalls,
                errors: this.errors,
                performance: this.performance,
                summary: this.getSummary()
            };
        }
        
        /**
         * Clear logs
         */
        clear() {
            this.logs = [];
            this.apiCalls = [];
            this.errors = [];
            this.performance = [];
            this.log('info', '🧹 Logs cleared');
        }
    }
    
    // Initialize logger
    const kgLogger = new KGLogger();
    
    // Expose to window for debugging
    window.kgLogger = kgLogger;
    
    // Log initialization using original console (before interception)
    const originalConsole = {
        log: console.log.bind(console),
        error: console.error.bind(console),
        warn: console.warn.bind(console),
        info: console.info.bind(console)
    };
    
    originalConsole.log('%c🔷 Knowledge Graph Logger loaded', 'color: #7c3aed; font-weight: bold; font-size: 14px;');
    originalConsole.log('%cAccess logger via: window.kgLogger', 'color: #9ca3af; font-style: italic;');
    originalConsole.log('%cMethods: getLogs(), getAPICalls(), getErrors(), getSummary(), exportLogs(), clear()', 'color: #9ca3af; font-style: italic;');
    
    // Log page load
    window.addEventListener('load', () => {
        kgLogger.log('info', '📄 Page loaded', {
            url: window.location.href,
            userAgent: navigator.userAgent,
            viewport: {
                width: window.innerWidth,
                height: window.innerHeight
            }
        });
    });
    
    // Log visibility changes
    document.addEventListener('visibilitychange', () => {
        kgLogger.log('debug', `👁️ Visibility changed: ${document.hidden ? 'hidden' : 'visible'}`);
    });
    
})();

