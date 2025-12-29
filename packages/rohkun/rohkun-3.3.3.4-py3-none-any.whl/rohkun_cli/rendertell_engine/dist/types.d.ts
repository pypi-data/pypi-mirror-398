export interface Snapshot {
    meta: SnapshotMetadata;
    elements: ElementRegistry;
    pageInfo?: PageInfo;
    mutations?: MutationEvent[];
    layoutShifts?: LayoutShiftEvent[];
    console?: ConsoleLogEntry[];
    eventTimeline?: TimelineEvent[];
    reflowTriggers?: ReflowTrigger[];
    eventListeners?: Array<{
        elementId: string;
        listeners: EventListenerInfo[];
    }>;
    scrollSnapshots?: Array<{
        position: {
            x: number;
            y: number;
            name?: string;
        };
        snapshot: {
            elements: ElementRegistry;
            pageInfo?: PageInfo;
        };
    }>;
}
export interface TimelineEvent {
    timestamp: number;
    eventType: string;
    category: 'mutation' | 'layout' | 'performance' | 'console' | 'system';
    elementId?: string;
    selector?: string;
    description: string;
    [key: string]: any;
}
export interface SnapshotMetadata {
    version: string;
    url: string;
    timestamp: number;
    viewport: {
        width: number;
        height: number;
    };
    devicePixelRatio?: number;
    userAgent?: string;
    deviceName?: string;
}
export type ElementRegistry = Record<string, ElementData>;
export interface ElementData {
    id: string;
    selector: string;
    tag: string;
    rect: {
        x: number;
        y: number;
        width: number;
        height: number;
        top: number;
        left: number;
        right: number;
        bottom: number;
    };
    computedStyles?: ComputedStyles;
    visibility?: VisibilityState;
    parentId?: string;
    childrenIds?: string[];
    attributes?: Record<string, string>;
    classes?: string[];
    textContent?: string;
    image?: ImageInfo;
    link?: LinkInfo;
    form?: FormInfo;
    accessibility?: AccessibilityInfo;
    contrast?: ContrastInfo;
}
export interface ComputedStyles {
    display: string;
    position: string;
    opacity: string;
    visibility: string;
    zIndex: string;
    pointerEvents: string;
    cursor: string;
    color?: string;
    backgroundColor?: string;
    fontSize?: string;
    fontWeight?: string;
    margin?: string;
    padding?: string;
    border?: string;
    width?: string;
    height?: string;
    top?: string;
    right?: string;
    bottom?: string;
    left?: string;
    transform?: string;
}
export interface VisibilityState {
    isVisible: boolean;
    isInViewport: boolean;
    isCovered: boolean;
    coveringElement?: string;
    visibleAreaFraction: number;
    display: string;
    visibility: string;
    opacity: number;
    pointerEvents: string;
    ariaHidden?: boolean;
}
export interface ImageInfo {
    src: string;
    alt: string | null;
    naturalWidth: number;
    naturalHeight: number;
    complete: boolean;
    loading: string;
    failed: boolean;
}
export interface LinkInfo {
    href: string;
    target: string;
    rel: string | null;
    download: string | null;
}
export interface FormInfo {
    type: string;
    value: string;
    disabled: boolean;
    required: boolean;
    readOnly: boolean;
    placeholder?: string | null;
    checked?: boolean;
    min?: string | null;
    max?: string | null;
    step?: string | null;
    options?: Array<{
        value: string;
        text: string;
        selected: boolean;
    }>;
    selectedIndex?: number;
    validation?: {
        valid: boolean;
        valueMissing: boolean;
        typeMismatch: boolean;
        patternMismatch: boolean;
        tooLong: boolean;
        tooShort: boolean;
        rangeUnderflow: boolean;
        rangeOverflow: boolean;
        stepMismatch: boolean;
        badInput: boolean;
        customError: boolean;
    };
    validationMessage?: string | null;
}
export interface AccessibilityInfo {
    role?: string;
    label?: string;
    labelledBy?: string;
    describedBy?: string;
    live?: string;
    expanded?: boolean;
    hidden?: boolean;
    tabIndex?: number;
    focusable: boolean;
    hasFocus: boolean;
}
export interface ContrastInfo {
    textColor: string;
    backgroundColor: string;
}
export interface PageInfo {
    scrollPosition: {
        x: number;
        y: number;
    };
    viewport: {
        width: number;
        height: number;
    };
    documentSize: {
        width: number;
        height: number;
    };
    resources?: {
        loaded: number;
        failed: number;
        css: Array<{
            url: string;
            size: number;
            duration: number;
            startTime: number;
        }>;
        js: Array<{
            url: string;
            size: number;
            duration: number;
            startTime: number;
        }>;
        images: Array<{
            url: string;
            size: number;
            duration: number;
            startTime: number;
        }>;
        fonts: Array<{
            url: string;
            size: number;
            duration: number;
            startTime: number;
        }>;
    };
    fonts?: Array<{
        family: string;
        status: string;
        loaded: boolean;
    }>;
    brokenImages?: string[];
    externalLinks?: string[];
}
export interface StackingContextInfo {
    createsStackingContext: boolean;
    zIndex: string;
    position: string;
    parentStackingContext: string | null;
    parentStackingContextId: string | null;
}
export interface CascadeAnalysis {
    [property: string]: {
        inline: string | null;
        computed: string | null;
        overridden: boolean;
    };
}
export interface EventListenerInfo {
    type: string;
    timestamp: number;
    selector: string;
    hasHandler: boolean;
    stackTrace?: string;
}
export interface ReflowTrigger {
    timestamp: number;
    elementId: string;
    selector: string;
    type: 'stylePropertySet' | 'reflowTriggered';
    property: string;
    value?: string;
    stackTrace?: string;
}
export interface MutationEvent {
    timestamp: number;
    type: 'attribute' | 'childList' | 'characterData' | 'classAdded' | 'classRemoved' | 'styleChanged';
    elementId: string;
    attributeName?: string;
    oldValue?: any;
    newValue?: any;
    addedNodes?: string[];
    removedNodes?: string[];
    triggeredBy?: string;
}
export interface LayoutShiftEvent {
    timestamp: number;
    score: number;
    movedElements: string[];
    sources: Array<{
        elementId: string;
        previousRect: {
            x: number;
            y: number;
            width: number;
            height: number;
        };
        currentRect: {
            x: number;
            y: number;
            width: number;
            height: number;
        };
    }>;
}
export interface ConsoleLogEntry {
    timestamp: number;
    level: 'log' | 'warn' | 'error' | 'info';
    message: string;
    stack?: string;
}
export interface SnapshotDiff {
    timeRange: {
        start: number;
        end: number;
    };
    changedElements: ElementChange[];
    layoutShifts: LayoutShiftEvent[];
    addedElements: string[];
    removedElements: string[];
    styleChanges: StyleChange[];
    geometryChanges: GeometryChange[];
}
export interface ElementChange {
    elementId: string;
    selector: string;
    changes: Array<{
        type: 'class' | 'style' | 'attribute' | 'geometry' | 'visibility';
        before: any;
        after: any;
        timestamp: number;
        cause?: string;
    }>;
}
export interface StyleChange {
    elementId: string;
    property: string;
    before: string;
    after: string;
    timestamp: number;
}
export interface GeometryChange {
    elementId: string;
    before: {
        x: number;
        y: number;
        width: number;
        height: number;
    };
    after: {
        x: number;
        y: number;
        width: number;
        height: number;
    };
    timestamp: number;
}
export interface ViewportConfig {
    width: number;
    height: number;
    deviceScaleFactor?: number;
    isMobile?: boolean;
    hasTouch?: boolean;
    name?: string;
}
export interface CaptureOptions {
    includeMutationHistory?: boolean;
    performanceProfile?: 'fast' | 'balanced' | 'exhaustive';
    viewportOnly?: boolean;
    scanDepth?: number;
    viewport?: ViewportConfig;
    scrollPositions?: Array<{
        x: number;
        y: number;
        name?: string;
    }>;
}
export declare const DEVICE_PRESETS: Record<string, ViewportConfig>;
export interface MultiDeviceCaptureOptions {
    url: string;
    devices?: string[];
    customViewports?: ViewportConfig[];
    scrollPositions?: Array<{
        x: number;
        y: number;
        name?: string;
    }>;
    includeMutationHistory?: boolean;
    performanceProfile?: 'fast' | 'balanced' | 'exhaustive';
}
export interface MultiDeviceSnapshot {
    url: string;
    timestamp: number;
    devices: Array<{
        device: ViewportConfig;
        snapshot: Snapshot;
    }>;
}
export interface ServerConfig {
    command?: string;
    port: number;
    protocol?: 'http' | 'https';
    workspacePath: string;
    startupTimeout?: number;
    healthCheckInterval?: number;
}
//# sourceMappingURL=types.d.ts.map