"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.computeDiff = computeDiff;
function computeDiff(snapshot1, snapshot2) {
    const timeRange = {
        start: snapshot1.meta.timestamp,
        end: snapshot2.meta.timestamp
    };
    const changedElements = [];
    const addedElements = [];
    const removedElements = [];
    const styleChanges = [];
    const geometryChanges = [];
    // Find added and removed elements
    const elements1Ids = new Set(Object.keys(snapshot1.elements));
    const elements2Ids = new Set(Object.keys(snapshot2.elements));
    elements2Ids.forEach(id => {
        if (!elements1Ids.has(id)) {
            addedElements.push(id);
        }
    });
    elements1Ids.forEach(id => {
        if (!elements2Ids.has(id)) {
            removedElements.push(id);
        }
    });
    // Find changed elements
    elements1Ids.forEach(id => {
        if (elements2Ids.has(id)) {
            const el1 = snapshot1.elements[id];
            const el2 = snapshot2.elements[id];
            if (!el1 || !el2)
                return;
            const changes = [];
            // Check geometry changes
            if (el1.rect && el2.rect) {
                const rect1 = el1.rect;
                const rect2 = el2.rect;
                if (rect1.x !== rect2.x || rect1.y !== rect2.y ||
                    rect1.width !== rect2.width || rect1.height !== rect2.height) {
                    geometryChanges.push({
                        elementId: id,
                        before: { x: rect1.x, y: rect1.y, width: rect1.width, height: rect1.height },
                        after: { x: rect2.x, y: rect2.y, width: rect2.width, height: rect2.height },
                        timestamp: snapshot2.meta.timestamp
                    });
                    changes.push({
                        type: 'geometry',
                        before: rect1,
                        after: rect2,
                        timestamp: snapshot2.meta.timestamp
                    });
                }
            }
            // Check style changes
            if (el1.computedStyles && el2.computedStyles) {
                const styles1 = el1.computedStyles;
                const styles2 = el2.computedStyles;
                const allStyleKeys = new Set([
                    ...Object.keys(styles1),
                    ...Object.keys(styles2)
                ]);
                allStyleKeys.forEach(prop => {
                    const val1 = styles1[prop];
                    const val2 = styles2[prop];
                    if (val1 !== val2) {
                        styleChanges.push({
                            elementId: id,
                            property: prop,
                            before: String(val1 || ''),
                            after: String(val2 || ''),
                            timestamp: snapshot2.meta.timestamp
                        });
                        changes.push({
                            type: 'style',
                            before: val1,
                            after: val2,
                            timestamp: snapshot2.meta.timestamp
                        });
                    }
                });
            }
            // Check class changes
            const classes1 = new Set(el1.classes || []);
            const classes2 = new Set(el2.classes || []);
            classes2.forEach(cls => {
                if (!classes1.has(cls)) {
                    changes.push({
                        type: 'class',
                        before: null,
                        after: cls,
                        timestamp: snapshot2.meta.timestamp
                    });
                }
            });
            classes1.forEach(cls => {
                if (!classes2.has(cls)) {
                    changes.push({
                        type: 'class',
                        before: cls,
                        after: null,
                        timestamp: snapshot2.meta.timestamp
                    });
                }
            });
            // Check visibility changes
            if (el1.visibility && el2.visibility) {
                const vis1 = el1.visibility;
                const vis2 = el2.visibility;
                if (vis1.isVisible !== vis2.isVisible ||
                    vis1.isInViewport !== vis2.isInViewport ||
                    vis1.display !== vis2.display ||
                    vis1.visibility !== vis2.visibility ||
                    vis1.opacity !== vis2.opacity) {
                    changes.push({
                        type: 'visibility',
                        before: vis1,
                        after: vis2,
                        timestamp: snapshot2.meta.timestamp
                    });
                }
            }
            // Check attribute changes
            if (el1.attributes && el2.attributes) {
                const attrs1 = el1.attributes;
                const attrs2 = el2.attributes;
                const allAttrKeys = new Set([
                    ...Object.keys(attrs1),
                    ...Object.keys(attrs2)
                ]);
                allAttrKeys.forEach(attr => {
                    if (attrs1[attr] !== attrs2[attr]) {
                        changes.push({
                            type: 'attribute',
                            before: attrs1[attr],
                            after: attrs2[attr],
                            timestamp: snapshot2.meta.timestamp
                        });
                    }
                });
            }
            if (changes.length > 0) {
                changedElements.push({
                    elementId: id,
                    selector: el2.selector,
                    changes
                });
            }
        }
    });
    // Include layout shifts from snapshot2 if available
    const layoutShifts = snapshot2.layoutShifts || [];
    return {
        timeRange,
        changedElements,
        layoutShifts,
        addedElements,
        removedElements,
        styleChanges,
        geometryChanges
    };
}
