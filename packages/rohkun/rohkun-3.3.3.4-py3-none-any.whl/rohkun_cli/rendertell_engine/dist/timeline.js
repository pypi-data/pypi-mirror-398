"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.generateEventTimeline = generateEventTimeline;
exports.analyzeTimeline = analyzeTimeline;
/**
 * Generate a human-readable chronological event log from snapshot
 */
function generateEventTimeline(snapshot) {
    if (!snapshot.eventTimeline || snapshot.eventTimeline.length === 0) {
        return ['No events captured in timeline'];
    }
    const timeline = snapshot.eventTimeline.slice().sort((a, b) => a.timestamp - b.timestamp);
    const startTime = timeline[0]?.timestamp || 0;
    const lines = [];
    lines.push('📋 Event Timeline (Chronological Order)');
    lines.push('='.repeat(80));
    lines.push('');
    timeline.forEach((event, index) => {
        const relativeTime = ((event.timestamp - startTime) / 1000).toFixed(3);
        const categoryIcon = getCategoryIcon(event.category);
        const eventIcon = getEventIcon(event.eventType);
        lines.push(`${relativeTime.padStart(8)}s | ${categoryIcon} ${eventIcon} ${event.description}`);
        // Add additional context for specific event types
        if (event.eventType === 'DOM_NODE_ADDED' && event.parentSelector) {
            lines.push(`         |    └─ Parent: ${event.parentSelector}`);
        }
        if (event.eventType === 'DOM_ATTRIBUTE_CHANGE') {
            lines.push(`         |    └─ ${event.attribute}: "${event.before}" → "${event.after}"`);
        }
        if (event.eventType === 'ELEMENT_RESIZE' && event.before && event.after) {
            lines.push(`         |    └─ Size: ${event.before.width}×${event.before.height} → ${event.after.width}×${event.after.height}`);
        }
        if (event.eventType === 'LAYOUT_SHIFT' && event.previousPosition && event.currentPosition) {
            lines.push(`         |    └─ Position: (${event.previousPosition.x}, ${event.previousPosition.y}) → (${event.currentPosition.x}, ${event.currentPosition.y})`);
            lines.push(`         |    └─ Score: ${event.score?.toFixed(3)}`);
        }
        if (event.eventType === 'CONSOLE_LOG') {
            lines.push(`         |    └─ [${event.level}] ${event.message}`);
        }
        if (event.selector && event.selector.length < 60) {
            lines.push(`         |    └─ Element: ${event.selector}`);
        }
        lines.push('');
    });
    lines.push('='.repeat(80));
    lines.push(`Total events: ${timeline.length}`);
    lines.push(`Time span: ${((timeline[timeline.length - 1].timestamp - startTime) / 1000).toFixed(3)}s`);
    return lines;
}
/**
 * Get category icon
 */
function getCategoryIcon(category) {
    const icons = {
        'mutation': '🧬',
        'layout': '📐',
        'performance': '⚡',
        'console': '💬',
        'system': '⚙️'
    };
    return icons[category] || '•';
}
/**
 * Get event type icon
 */
function getEventIcon(eventType) {
    const icons = {
        'DOM_NODE_ADDED': '➕',
        'DOM_NODE_REMOVED': '➖',
        'DOM_ATTRIBUTE_CHANGE': '🔧',
        'ELEMENT_RESIZE': '📏',
        'LAYOUT_SHIFT': '📊',
        'CONSOLE_LOG': '📝',
        'CONSOLE_WARN': '⚠️',
        'CONSOLE_ERROR': '❌',
        'WATCHING_STARTED': '▶️',
        'PAGE_LOADED': '✅',
        'PAGE_INTERACTIVE': '🔄'
    };
    return icons[eventType] || '•';
}
/**
 * Analyze timeline for potential issues
 */
function analyzeTimeline(snapshot) {
    const warnings = [];
    const raceConditions = [];
    const orderingIssues = [];
    if (!snapshot.eventTimeline || snapshot.eventTimeline.length === 0) {
        return { warnings, raceConditions, orderingIssues };
    }
    const timeline = snapshot.eventTimeline.slice().sort((a, b) => a.timestamp - b.timestamp);
    // Check for rapid successive changes (potential race conditions)
    for (let i = 1; i < timeline.length; i++) {
        const prev = timeline[i - 1];
        const curr = timeline[i];
        const timeDiff = curr.timestamp - prev.timestamp;
        // If two events happen within 10ms and affect the same element
        if (timeDiff < 10 && curr.elementId === prev.elementId) {
            raceConditions.push(`Potential race condition: ${prev.description} and ${curr.description} ` +
                `happened ${timeDiff.toFixed(2)}ms apart on same element`);
        }
    }
    // Check for ordering issues (e.g., element used before it's created)
    const elementCreation = new Map();
    const elementUsage = new Map();
    timeline.forEach(event => {
        if (event.eventType === 'DOM_NODE_ADDED' && event.elementId) {
            elementCreation.set(event.elementId, event.timestamp);
        }
        if (event.elementId && event.eventType !== 'DOM_NODE_ADDED') {
            if (!elementUsage.has(event.elementId)) {
                elementUsage.set(event.elementId, []);
            }
            elementUsage.get(event.elementId).push(event.timestamp);
        }
    });
    // Check if elements are used before creation
    elementUsage.forEach((usageTimes, elementId) => {
        const creationTime = elementCreation.get(elementId);
        if (creationTime !== undefined) {
            usageTimes.forEach(usageTime => {
                if (usageTime < creationTime) {
                    orderingIssues.push(`Element ${elementId} was used at ${usageTime.toFixed(2)}ms ` +
                        `but created at ${creationTime.toFixed(2)}ms (used before creation!)`);
                }
            });
        }
    });
    // Check for layout shifts (performance warnings)
    const layoutShifts = timeline.filter(e => e.eventType === 'LAYOUT_SHIFT');
    if (layoutShifts.length > 5) {
        warnings.push(`High number of layout shifts detected: ${layoutShifts.length} (may indicate performance issues)`);
    }
    // Check for console errors
    const errors = timeline.filter(e => e.eventType === 'CONSOLE_LOG' && e.level === 'error');
    if (errors.length > 0) {
        warnings.push(`${errors.length} console error(s) detected during timeline`);
    }
    return { warnings, raceConditions, orderingIssues };
}
