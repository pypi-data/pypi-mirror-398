import { Snapshot } from './types';
/**
 * Generate a human-readable chronological event log from snapshot
 */
export declare function generateEventTimeline(snapshot: Snapshot): string[];
/**
 * Analyze timeline for potential issues
 */
export declare function analyzeTimeline(snapshot: Snapshot): {
    warnings: string[];
    raceConditions: string[];
    orderingIssues: string[];
};
//# sourceMappingURL=timeline.d.ts.map