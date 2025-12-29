import { Browser, Page } from 'puppeteer';
export declare class BrowserManager {
    private browserInstances;
    launchBrowser(): Promise<Browser>;
    navigateToPage(browser: Browser, url: string): Promise<Page>;
    cleanup(): Promise<void>;
}
export declare const browserManager: BrowserManager;
//# sourceMappingURL=browser.d.ts.map