// Canvas API Protection - Make methods appear as [native code]
(() => {
    const nativeCodeTemplate = (name) => `function ${name}() { [native code] }`;

    // List of methods to protect
    const ctx2dMethods = [
        // Rectangle methods
        'fillRect', 'strokeRect', 'clearRect',
        // Path methods
        'beginPath', 'closePath', 'moveTo', 'lineTo', 'arc', 'arcTo',
        'bezierCurveTo', 'quadraticCurveTo', 'rect', 'fill', 'stroke',
        'clip', 'isPointInPath', 'isPointInStroke',
        // Text methods
        'fillText', 'strokeText', 'measureText',
        // Transform methods
        'save', 'restore', 'translate', 'rotate', 'scale',
        'transform', 'setTransform', 'resetTransform',
        // Image methods
        'drawImage', 'createImageData', 'getImageData', 'putImageData',
        // Pixel methods
        'createLinearGradient', 'createRadialGradient', 'createPattern',
        // Other methods
        'getLineDash', 'setLineDash', 'getTransform'
    ];

    const canvasMethods = ['getContext', 'toBuffer', 'toDataURL', 'toBlob'];
    const imageMethods = ['dispose'];

    // Protect CanvasRenderingContext2D methods
    ctx2dMethods.forEach(methodName => {
        const method = globalThis.CanvasRenderingContext2D.prototype[methodName];
        if (method && typeof method === 'function') {
            Object.defineProperty(method, 'toString', {
                value: function() { return nativeCodeTemplate(methodName); },
                writable: false,
                configurable: true
            });
            Object.defineProperty(method, 'name', {
                value: methodName,
                writable: false,
                configurable: true
            });
        }
    });

    // Protect Canvas methods
    canvasMethods.forEach(methodName => {
        const method = globalThis.Canvas.prototype[methodName];
        if (method && typeof method === 'function') {
            Object.defineProperty(method, 'toString', {
                value: function() { return nativeCodeTemplate(methodName); },
                writable: false,
                configurable: true
            });
            Object.defineProperty(method, 'name', {
                value: methodName,
                writable: false,
                configurable: true
            });
        }
    });

    // Protect Image methods
    imageMethods.forEach(methodName => {
        const method = globalThis.Image.prototype[methodName];
        if (method && typeof method === 'function') {
            Object.defineProperty(method, 'toString', {
                value: function() { return nativeCodeTemplate(methodName); },
                writable: false,
                configurable: true
            });
            Object.defineProperty(method, 'name', {
                value: methodName,
                writable: false,
                configurable: true
            });
        }
    });

    // Protect constructors
    Object.defineProperty(globalThis.Canvas, 'toString', {
        value: function() { return 'function Canvas() { [native code] }'; },
        writable: false,
        configurable: true
    });

    Object.defineProperty(globalThis.CanvasRenderingContext2D, 'toString', {
        value: function() { return 'function CanvasRenderingContext2D() { [native code] }'; },
        writable: false,
        configurable: true
    });

    Object.defineProperty(globalThis.createCanvas, 'toString', {
        value: function() { return 'function createCanvas() { [native code] }'; },
        writable: false,
        configurable: true
    });

    Object.defineProperty(globalThis.createCanvas, 'name', {
        value: 'createCanvas',
        writable: false,
        configurable: true
    });

    Object.defineProperty(globalThis.Image, 'toString', {
        value: function() { return 'function Image() { [native code] }'; },
        writable: false,
        configurable: true
    });

    Object.defineProperty(globalThis.loadImage, 'toString', {
        value: function() { return 'function loadImage() { [native code] }'; },
        writable: false,
        configurable: true
    });

    Object.defineProperty(globalThis.loadImage, 'name', {
        value: 'loadImage',
        writable: false,
        configurable: true
    });

    console.log("[Canvas] Native code protection enabled");
})();
