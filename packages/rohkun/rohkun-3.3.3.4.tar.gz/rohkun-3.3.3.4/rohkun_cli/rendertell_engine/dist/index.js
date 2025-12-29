"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.DEVICE_PRESETS = exports.analyzeTimeline = exports.generateEventTimeline = exports.RenderTellError = exports.computeDiff = exports.isPortInUse = exports.validateServer = void 0;
exports.captureSnapshot = captureSnapshot;
exports.setLastSnapshot = setLastSnapshot;
exports.compareLastTwo = compareLastTwo;
exports.compareSnapshots = compareSnapshots;
exports.captureMultiDevice = captureMultiDevice;
const types_1 = require("./types");
const browser_1 = require("./browser");
const diff_1 = require("./diff");
const errors_1 = require("./errors");
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
// Cache for probe script
let probeScriptCache = null;
function getProbeScript() {
    if (probeScriptCache) {
        return probeScriptCache;
    }
    // Try to read from dist folder
    const probePath = path.join(__dirname, '../../probe/dist/index.js');
    if (fs.existsSync(probePath)) {
        probeScriptCache = fs.readFileSync(probePath, 'utf-8');
        return probeScriptCache;
    }
    // Fallback to inline stub if probe not found
    return `
    (function() {
      window.__RENDERTELL_PROBE__ = {
        collect: function() {
          const elements = {};
          const allElements = document.querySelectorAll('*');
          
          allElements.forEach((el, index) => {
            const rect = el.getBoundingClientRect();
            elements['el_' + index] = {
              id: 'el_' + index,
              selector: el.tagName.toLowerCase(),
              tag: el.tagName,
              rect: {
                x: rect.x,
                y: rect.y,
                width: rect.width,
                height: rect.height,
                top: rect.top,
                left: rect.left,
                right: rect.right,
                bottom: rect.bottom
              }
            };
          });
          
          return { elements: elements };
        },
        startWatching: function() {},
        stopWatching: function() {}
      };
    })();
  `;
}
async function captureSnapshot(url, options = {}) {
    let browser = null;
    let page = null;
    try {
        // Validate URL
        try {
            new URL(url);
        }
        catch (e) {
            throw new errors_1.RenderTellError(`Invalid URL: ${url}`, 'INVALID_URL', 'Please provide a valid URL (e.g., http://localhost:3000)');
        }
        // Launch browser with retry
        let retries = 3;
        while (retries > 0) {
            try {
                browser = await browser_1.browserManager.launchBrowser();
                break;
            }
            catch (error) {
                retries--;
                if (retries === 0) {
                    throw new errors_1.RenderTellError(`Failed to launch browser: ${error instanceof Error ? error.message : String(error)}`, 'BROWSER_LAUNCH_FAILED', 'Failed to launch browser. Make sure Chrome/Chromium is installed or Puppeteer can download it.');
                }
                await new Promise(resolve => setTimeout(resolve, 1000));
            }
        }
        if (!browser) {
            throw new errors_1.RenderTellError('Browser launch failed', 'BROWSER_LAUNCH_FAILED', 'Failed to launch browser. Make sure Chrome/Chromium is installed or Puppeteer can download it.');
        }
        // Navigate to page
        try {
            page = await browser_1.browserManager.navigateToPage(browser, url);
        }
        catch (error) {
            if (error instanceof Error && error.message.includes('net::ERR_CONNECTION_REFUSED')) {
                throw new errors_1.RenderTellError(`Connection refused: ${url}`, 'CONNECTION_REFUSED', `Cannot connect to ${url}. Make sure your development server is running.`);
            }
            throw new errors_1.RenderTellError(`Failed to navigate to ${url}: ${error instanceof Error ? error.message : String(error)}`, 'NAVIGATION_FAILED', `Failed to load page at ${url}. Check that the server is running and accessible.`);
        }
        // Set viewport if specified
        if (options.viewport) {
            try {
                await page.setViewport({
                    width: options.viewport.width,
                    height: options.viewport.height,
                    deviceScaleFactor: options.viewport.deviceScaleFactor || 1,
                    isMobile: options.viewport.isMobile || false,
                    hasTouch: options.viewport.hasTouch || false
                });
                // Wait a bit for layout to adjust
                await new Promise(resolve => setTimeout(resolve, 500));
            }
            catch (error) {
                // Non-fatal - continue with default viewport
                console.warn('Failed to set viewport:', error);
            }
        }
        // Wait for page to be ready
        try {
            await page.waitForNavigation({ waitUntil: 'networkidle0', timeout: 10000 }).catch(() => {
                // Navigation may already be complete, continue anyway
            });
        }
        catch (error) {
            // Continue even if navigation timeout - page might still be usable
        }
        // Inject probe script
        try {
            const probeScript = getProbeScript();
            await page.addScriptTag({ content: probeScript });
        }
        catch (error) {
            throw new errors_1.RenderTellError(`Failed to inject probe script: ${error instanceof Error ? error.message : String(error)}`, 'PROBE_INJECTION_FAILED', 'Failed to inject inspection script. The page may have content security policies blocking scripts.');
        }
        // Start watching for mutations if requested
        if (options.includeMutationHistory) {
            try {
                await page.evaluate(() => {
                    // @ts-ignore
                    if (window.__RENDERTELL_PROBE__ && window.__RENDERTELL_PROBE__.startWatching) {
                        // @ts-ignore
                        window.__RENDERTELL_PROBE__.startWatching();
                    }
                });
            }
            catch (error) {
                // Non-fatal - continue without mutation tracking
                console.warn('Failed to start mutation tracking:', error);
            }
        }
        // Wait a bit for initial mutations to settle
        await new Promise(resolve => setTimeout(resolve, 500));
        // Handle scroll positions if specified
        const scrollSnapshots = [];
        if (options.scrollPositions && options.scrollPositions.length > 0) {
            // Capture at each scroll position
            for (const scrollPos of options.scrollPositions) {
                try {
                    await page.evaluate((pos) => {
                        window.scrollTo(pos.x, pos.y);
                    }, scrollPos);
                    await new Promise(resolve => setTimeout(resolve, 300)); // Wait for scroll to complete
                    const scrollSnapshotData = await page.evaluate((opts) => {
                        // @ts-ignore
                        if (window.__RENDERTELL_PROBE__ && window.__RENDERTELL_PROBE__.collect) {
                            // @ts-ignore
                            return window.__RENDERTELL_PROBE__.collect(opts);
                        }
                        return { elements: {} };
                    }, {
                        includeMutationHistory: options.includeMutationHistory,
                        performanceProfile: options.performanceProfile || 'balanced',
                        viewportOnly: options.viewportOnly,
                        scanDepth: options.scanDepth
                    });
                    scrollSnapshots.push({
                        position: scrollPos,
                        snapshot: scrollSnapshotData
                    });
                }
                catch (error) {
                    console.warn(`Failed to capture at scroll position (${scrollPos.x}, ${scrollPos.y}):`, error);
                }
            }
            // Scroll back to top for main snapshot
            await page.evaluate(() => window.scrollTo(0, 0));
            await new Promise(resolve => setTimeout(resolve, 300));
        }
        // Collect snapshot data
        let snapshotData;
        try {
            snapshotData = await page.evaluate((opts) => {
                // @ts-ignore
                if (window.__RENDERTELL_PROBE__ && window.__RENDERTELL_PROBE__.collect) {
                    // @ts-ignore
                    return window.__RENDERTELL_PROBE__.collect(opts);
                }
                return { elements: {} };
            }, {
                includeMutationHistory: options.includeMutationHistory,
                performanceProfile: options.performanceProfile || 'balanced',
                viewportOnly: options.viewportOnly,
                scanDepth: options.scanDepth
            });
        }
        catch (error) {
            throw new errors_1.RenderTellError(`Failed to collect snapshot data: ${error instanceof Error ? error.message : String(error)}`, 'COLLECTION_FAILED', 'Failed to collect page data. The page may have errors or be blocking script execution.');
        }
        if (!snapshotData || !snapshotData.elements) {
            throw new errors_1.RenderTellError('No elements collected from page', 'NO_ELEMENTS', 'No elements were found on the page. The page may be empty or not fully loaded.');
        }
        const snapshot = {
            meta: {
                version: '1.0.0',
                url: page.url(),
                timestamp: Date.now(),
                viewport: {
                    width: await page.evaluate(() => window.innerWidth).catch(() => 1920),
                    height: await page.evaluate(() => window.innerHeight).catch(() => 1080)
                },
                devicePixelRatio: await page.evaluate(() => window.devicePixelRatio).catch(() => 1),
                userAgent: await page.evaluate(() => navigator.userAgent).catch(() => 'Unknown'),
                deviceName: options.viewport?.name || undefined
            },
            elements: snapshotData.elements || {},
            pageInfo: snapshotData.pageInfo || {},
            mutations: snapshotData.mutations,
            layoutShifts: snapshotData.layoutShifts,
            console: snapshotData.console,
            eventTimeline: snapshotData.eventTimeline,
            reflowTriggers: snapshotData.reflowTriggers,
            eventListeners: snapshotData.eventListeners,
            scrollSnapshots: scrollSnapshots.length > 0 ? scrollSnapshots : undefined
        };
        return snapshot;
    }
    catch (error) {
        if (error instanceof errors_1.RenderTellError) {
            throw error;
        }
        throw new errors_1.RenderTellError(`Unexpected error: ${error instanceof Error ? error.message : String(error)}`, 'UNKNOWN_ERROR', 'An unexpected error occurred while capturing the snapshot. Please try again.');
    }
    finally {
        if (page) {
            try {
                await page.close();
            }
            catch (e) {
                // Ignore cleanup errors
            }
        }
        if (browser) {
            try {
                await browser.close();
            }
            catch (e) {
                // Ignore cleanup errors
            }
        }
    }
}
// Store last two snapshots for comparison
let lastSnapshot = null;
let previousSnapshot = null;
function setLastSnapshot(snapshot) {
    previousSnapshot = lastSnapshot;
    lastSnapshot = snapshot;
}
function compareLastTwo() {
    if (!lastSnapshot || !previousSnapshot) {
        return null;
    }
    return (0, diff_1.computeDiff)(previousSnapshot, lastSnapshot);
}
function compareSnapshots(snapshot1, snapshot2) {
    return (0, diff_1.computeDiff)(snapshot1, snapshot2);
}
var server_1 = require("./server");
Object.defineProperty(exports, "validateServer", { enumerable: true, get: function () { return server_1.validateServer; } });
var server_2 = require("./server");
Object.defineProperty(exports, "isPortInUse", { enumerable: true, get: function () { return server_2.isPortInUse; } });
var diff_2 = require("./diff");
Object.defineProperty(exports, "computeDiff", { enumerable: true, get: function () { return diff_2.computeDiff; } });
var errors_2 = require("./errors");
Object.defineProperty(exports, "RenderTellError", { enumerable: true, get: function () { return errors_2.RenderTellError; } });
var timeline_1 = require("./timeline");
Object.defineProperty(exports, "generateEventTimeline", { enumerable: true, get: function () { return timeline_1.generateEventTimeline; } });
Object.defineProperty(exports, "analyzeTimeline", { enumerable: true, get: function () { return timeline_1.analyzeTimeline; } });
var types_2 = require("./types");
Object.defineProperty(exports, "DEVICE_PRESETS", { enumerable: true, get: function () { return types_2.DEVICE_PRESETS; } });
/**
 * Capture snapshots for multiple devices/viewports
 * Useful for cross-device compatibility testing
 */
async function captureMultiDevice(options) {
    const devices = [];
    // Add preset devices
    if (options.devices) {
        for (const deviceName of options.devices) {
            const preset = types_1.DEVICE_PRESETS[deviceName];
            if (preset) {
                devices.push(preset);
            }
        }
    }
    // Add custom viewports
    if (options.customViewports) {
        devices.push(...options.customViewports);
    }
    // Default to common devices if none specified
    if (devices.length === 0) {
        devices.push(types_1.DEVICE_PRESETS['Desktop'], types_1.DEVICE_PRESETS['iPhone 15'], types_1.DEVICE_PRESETS['iPad']);
    }
    const deviceSnapshots = [];
    for (const device of devices) {
        try {
            const snapshot = await captureSnapshot(options.url, {
                viewport: device,
                scrollPositions: options.scrollPositions,
                includeMutationHistory: options.includeMutationHistory,
                performanceProfile: options.performanceProfile || 'balanced'
            });
            deviceSnapshots.push({ device, snapshot });
        }
        catch (error) {
            console.warn(`Failed to capture snapshot for device ${device.name || `${device.width}x${device.height}`}:`, error);
            // Continue with other devices
        }
    }
    return {
        url: options.url,
        timestamp: Date.now(),
        devices: deviceSnapshots
    };
}
