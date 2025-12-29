"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.browserManager = exports.BrowserManager = void 0;
const puppeteer_1 = __importDefault(require("puppeteer"));
class BrowserManager {
    constructor() {
        this.browserInstances = new Set();
    }
    async launchBrowser() {
        let browser = null;
        try {
            // Try to find system Chrome as fallback
            let executablePath;
            // Common Chrome installation paths on Windows
            const chromePaths = [
                'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
                'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
                process.env.CHROME_PATH
            ].filter(Boolean);
            // Check if system Chrome exists
            const fs = require('fs');
            for (const path of chromePaths) {
                if (path && fs.existsSync(path)) {
                    executablePath = path;
                    console.log(`Using system Chrome: ${path}`);
                    break;
                }
            }
            browser = await puppeteer_1.default.launch({
                headless: 'new',
                executablePath, // Use system Chrome if found, otherwise use bundled
                args: [
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--window-size=1920,1080'
                ],
                defaultViewport: { width: 1920, height: 1080, deviceScaleFactor: 2 },
                timeout: 30000
            });
            this.browserInstances.add(browser);
            browser.on('disconnected', () => {
                this.browserInstances.delete(browser);
            });
            return browser;
        }
        catch (error) {
            if (browser) {
                try {
                    await browser.close();
                }
                catch (e) { }
            }
            throw error;
        }
    }
    async navigateToPage(browser, url) {
        const page = await browser.newPage();
        try {
            await page.goto(url, {
                waitUntil: 'domcontentloaded',
                timeout: 30000
            });
            return page;
        }
        catch (error) {
            await page.close().catch(() => { });
            throw error;
        }
    }
    async cleanup() {
        const promises = Array.from(this.browserInstances).map(browser => {
            return browser.close().catch(() => {
                try {
                    browser.process()?.kill('SIGKILL');
                }
                catch (e) { }
            });
        });
        await Promise.all(promises);
        this.browserInstances.clear();
    }
}
exports.BrowserManager = BrowserManager;
exports.browserManager = new BrowserManager();
