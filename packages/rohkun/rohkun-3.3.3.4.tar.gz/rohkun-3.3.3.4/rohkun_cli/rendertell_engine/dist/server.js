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
exports.isPortInUse = isPortInUse;
exports.validateServer = validateServer;
const net = __importStar(require("net"));
const path = __importStar(require("path"));
const fs = __importStar(require("fs"));
async function isPortInUse(port) {
    return new Promise(resolve => {
        const server = net.createServer();
        server.once('error', () => resolve(true));
        server.once('listening', () => {
            server.close(() => resolve(false));
        });
        server.listen(port);
    });
}
async function validateServer(url, workspacePath) {
    try {
        const tempDir = path.join(workspacePath, '.rendertell');
        if (!fs.existsSync(tempDir)) {
            fs.mkdirSync(tempDir, { recursive: true });
        }
        const tempFile = path.join(tempDir, '.validation-temp.txt');
        const uniqueString = `rendertell-${Date.now()}-${Math.random()}`;
        fs.writeFileSync(tempFile, uniqueString);
        try {
            const tempUrl = new URL('.rendertell/.validation-temp.txt', url).href;
            const response = await fetch(tempUrl, {
                method: 'GET',
                signal: AbortSignal.timeout(5000)
            });
            if (response.ok) {
                const content = await response.text();
                if (content.trim() === uniqueString) {
                    fs.unlinkSync(tempFile);
                    return true;
                }
            }
        }
        finally {
            try {
                if (fs.existsSync(tempFile)) {
                    fs.unlinkSync(tempFile);
                }
            }
            catch (e) { }
        }
    }
    catch (error) {
        // Continue to fallback
    }
    // Fallback: HTTP 200 check
    try {
        const response = await fetch(url, {
            method: 'GET',
            signal: AbortSignal.timeout(2000)
        });
        return response.ok;
    }
    catch (error) {
        return false;
    }
}
