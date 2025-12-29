import { Snapshot, MultiDeviceCaptureOptions, MultiDeviceSnapshot } from './types';
import { computeDiff } from './diff';
import type { CaptureOptions } from './types';
export declare function captureSnapshot(url: string, options?: CaptureOptions): Promise<Snapshot>;
export declare function setLastSnapshot(snapshot: Snapshot): void;
export declare function compareLastTwo(): ReturnType<typeof computeDiff> | null;
export declare function compareSnapshots(snapshot1: Snapshot, snapshot2: Snapshot): ReturnType<typeof computeDiff>;
export { validateServer } from './server';
export { isPortInUse } from './server';
export { computeDiff } from './diff';
export { RenderTellError } from './errors';
export { generateEventTimeline, analyzeTimeline } from './timeline';
export { DEVICE_PRESETS } from './types';
export type { Snapshot, SnapshotMetadata, ElementData, ElementRegistry, SnapshotDiff, TimelineEvent, ViewportConfig, MultiDeviceCaptureOptions, MultiDeviceSnapshot } from './types';
/**
 * Capture snapshots for multiple devices/viewports
 * Useful for cross-device compatibility testing
 */
export declare function captureMultiDevice(options: MultiDeviceCaptureOptions): Promise<MultiDeviceSnapshot>;
//# sourceMappingURL=index.d.ts.map