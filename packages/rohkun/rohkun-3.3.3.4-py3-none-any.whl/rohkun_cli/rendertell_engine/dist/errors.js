"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.RenderTellError = void 0;
class RenderTellError extends Error {
    constructor(message, code, userMessage) {
        super(message);
        this.code = code;
        this.userMessage = userMessage;
        this.name = 'RenderTellError';
    }
}
exports.RenderTellError = RenderTellError;
