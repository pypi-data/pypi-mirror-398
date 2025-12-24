let currentZoom = 1;
let isDragging = false;
let startX, startY, translateX = 0, translateY = 0;
let lastTranslateX = 0, lastTranslateY = 0;
let showGrid = true;
let isRulerMode = false;
let isDrawing = false;
let startPoint = null;
let currentLine = null;
let measurements = [];
let lastValidCoords = { x: 0, y: 0 };

const container = document.getElementById('svg-container');
const content = document.getElementById('svg-content');

// Add these helper functions for style processing
function extractStyleRules(svgElement) {
    const styleElement = svgElement.querySelector('style');
    if (!styleElement) return null;
    
    const styleRules = {};
    const styleText = styleElement.textContent;
    
    const rules = styleText.match(/[^}]+\{[^}]+\}/g) || [];
    rules.forEach(rule => {
        const [selector, styles] = rule.split('{');
        const styleObj = {};
        
        // Extract color from stroke or fill
        const colorMatch = styles.match(/(?:stroke|fill):\s*(#[a-fA-F0-9]{6})/);
        if (colorMatch) {
            styleObj.color = colorMatch[1];
        }
        
        styles.replace('}', '').split(';').forEach(style => {
            const [prop, value] = style.split(':').map(s => s.trim());
            if (prop && value) {
                styleObj[prop] = value;
            }
        });
        
        styleRules[selector.trim()] = styleObj;
    });
    
    return styleRules;
}

function updateStyles(svgElement, zoom) {
    const originalRules = JSON.parse(svgElement.dataset.originalStyles || '{}');
    const dynamicStyle = svgElement.querySelector('style');
    
    let newStyles = '';
    Object.entries(originalRules).forEach(([selector, styles]) => {
        newStyles += `${selector} {`;
        Object.entries(styles).forEach(([prop, value]) => {
            if (prop === 'stroke-width') {
                const originalValue = parseFloat(value);
                const scaledValue = originalValue / zoom;
                newStyles += `${prop}: ${scaledValue}px;`;
            } else if (prop === 'font-size') {
                const originalValue = parseFloat(value);
                const scaledValue = originalValue / zoom;
                newStyles += `${prop}: ${scaledValue}px;`;
            } else {
                newStyles += `${prop}: ${value};`;
            }
        });
        newStyles += '}\n';
    });
    
    // Calculate scale factors for port symbols
    const symbolScale = 0.5 / zoom;  // More gradual scaling for symbols
    
    // Add specific styles for ports and related elements
    newStyles += `
        .port,
        .port-arrow,
        .port-marker,
        .port-connection,
        .virtual-connection,
        marker[id^="port"],
        path[class*="port"],
        marker path,
        #port-symbol,
        path#port-symbol,
        path#ref-port-symbol,
        use[href="#port-symbol"] {
            vector-effect: non-scaling-stroke;
            stroke-width: ${3 / zoom}px;
        }
        
        use[href="#port-symbol"] {
            transform: scale(${1.5*symbolScale});
            transform-origin: 0 0;
        }

        use[href="#ref-port-symbol"] {
            transform: scale(${1.5*symbolScale});
            transform-origin: 0 0;
        }

        #connection-symbol {
            r: ${symbolScale};
        }
    `;
    
    dynamicStyle.textContent = newStyles;
}

function processSVGForScaling(svgElement) {
    const originalRules = extractStyleRules(svgElement);
    svgElement.dataset.originalStyles = JSON.stringify(originalRules);
    
    // Store original port symbol dimensions
    const portSymbol = svgElement.querySelector('#port-symbol');
    if (portSymbol) {
        const d = portSymbol.getAttribute('d');
        svgElement.dataset.originalPortSymbolPath = d;
    }
    
    const refPortSymbol = svgElement.querySelector('#ref-port-symbol');
    if (refPortSymbol) {
        const d = refPortSymbol.getAttribute('d');
        svgElement.dataset.originalRefPortSymbolPath = d;
    }
    
    // Process all use elements that reference port symbols
    const useElements = svgElement.querySelectorAll('use[href="#port-symbol"], use[href="#ref-port-symbol"]');
    useElements.forEach(useEl => {
        useEl.setAttribute('vector-effect', 'non-scaling-stroke');
        // Store original transform if it exists
        const transform = useEl.getAttribute('transform');
        if (transform) {
            useEl.dataset.originalTransform = transform;
        }
    });
    
    const originalStyle = svgElement.querySelector('style');
    if (originalStyle) {
        const dynamicStyle = document.createElement('style');
        svgElement.insertBefore(dynamicStyle, svgElement.firstChild);
        originalStyle.remove();
    }
    
    updateStyles(svgElement, currentZoom);
    const styleElement = document.createElement('style');
    styleElement.textContent = `
        .label {
            transition: font-size 0.1s ease-out;
        }
    `;
    svgElement.insertBefore(styleElement, svgElement.firstChild);
}

// Add these helper functions for viewport checking
function isElementInViewport(el, container) {
    const containerRect = container.getBoundingClientRect();
    const elRect = el.getBoundingClientRect();
    
    return !(
        elRect.bottom < containerRect.top || 
        elRect.top > containerRect.bottom ||
        elRect.right < containerRect.left || 
        elRect.left > containerRect.right
    );
}

function updateStylesOnly() {
    const svg = content.querySelector('svg');
    if (!svg) return;
    
    // Only update critical styles that need to scale
    let styleString = '';
    
    // Use sqrt for more gradual scaling when zooming out
    const arrowScale = Math.sqrt(1 / currentZoom);
    const labelScale = Math.max(0.2, 1 / Math.sqrt(currentZoom));  // Allow text to get smaller
    const connectionScale = Math.sqrt(1 / currentZoom);  // Match port arrow scaling
    
    styleString += `
        .port, .port-arrow, .port-marker, .port-connection {
            stroke-width: ${arrowScale}px;
        }
        
        .label {
            font-size: ${12 * labelScale}px;
        }
        
        #connection-symbol {
            r: ${connectionScale};
        }
    `;
    
    // Update styles in a single operation
    let styleEl = svg.querySelector('style');
    if (!styleEl) {
        styleEl = document.createElement('style');
        svg.insertBefore(styleEl, svg.firstChild);
    }
    styleEl.textContent = styleString;
}

// Replace the existing transform update with this optimized version
function updateTransformOnly() {
    requestAnimationFrame(() => {
        content.style.transform = `translate(${translateX}px, ${translateY}px) scale(${currentZoom})`;
        updateCoordinatesDisplay();
        updateZoomDisplay();
        
        // Update measurement text sizes if they exist
        const measurementTexts = document.querySelectorAll('.measurement-group text');
        if (measurementTexts.length > 0) {
            measurementTexts.forEach(text => {
                text.setAttribute('font-size', `${12/currentZoom}`);
            });
        }
        
        if (showGrid) {
            debouncedUpdateGrid();
        }
    });
}

// Add this new function to handle coordinates display updates
function updateCoordinatesDisplay(coords) {
    const coordsDisplay = document.getElementById('coordinates');
    if (coords) {
        lastValidCoords = coords;  // Store the valid coordinates
        coordsDisplay.textContent = `Coordinates: (${coords.x.toFixed(3)} μm, ${coords.y.toFixed(3)} μm)`;
    } else {
        // Use last valid coordinates instead of defaulting to 0,0
        coordsDisplay.textContent = `Coordinates: (${lastValidCoords.x.toFixed(3)} μm, ${lastValidCoords.y.toFixed(3)} μm)`;
    }
}

// Add new function to update zoom display
function updateZoomDisplay() {
    const zoomDisplay = document.getElementById('zoom-display');
    const zoomPercentage = (currentZoom * 100).toFixed(0);
    zoomDisplay.textContent = `Zoom: ${zoomPercentage}%`;
}

// Use longer debounce times for less critical updates
const debouncedUpdateStyles = debounce(updateStylesOnly, 100);  // Increased from 32ms
const debouncedUpdateGrid = debounce(updateGrid, 150);  // Increased from 100ms

function zoomIn() {
    currentZoom = Math.min(currentZoom * 1.2, 5000);
    clearMeasurements();  // Clear measurements on zoom
    updateTransformOnly();
    debouncedUpdateStyles();
    updateRuler();
}

function zoomOut() {
    currentZoom = Math.max(currentZoom / 1.2, 0.1);
    clearMeasurements();  // Clear measurements on zoom
    updateTransformOnly();
    debouncedUpdateStyles();
    updateRuler();
}

function resetZoom() {
    currentZoom = 1;
    translateX = 0;
    translateY = 0;
    lastTranslateX = 0;
    lastTranslateY = 0;
    clearMeasurements();  // Clear measurements on reset
    updateTransformOnly();
    debouncedUpdateStyles();
    updateRuler();
}

container.addEventListener('mousedown', (e) => {
    if (isRulerMode) {
        const gridContainer = document.getElementById('grid-container');
        const rect = gridContainer.getBoundingClientRect();
        
        if (!isDrawing) {
            // First click - start drawing
            isDrawing = true;
            startPoint = {
                x: e.clientX - rect.left,
                y: e.clientY - rect.top
            };
            currentLine = createMeasurementLine(startPoint.x, startPoint.y, startPoint.x, startPoint.y);
        } else {
            // Second click - finish drawing
            let endX = e.clientX - rect.left;
            let endY = e.clientY - rect.top;
            
            // Handle shift key constraints
            if (e.shiftKey) {
                const dx = Math.abs(endX - startPoint.x);
                const dy = Math.abs(endY - startPoint.y);
                
                if (dx > dy) {
                    endY = startPoint.y;
                } else {
                    endX = startPoint.x;
                }
            }
            
            if (currentLine) currentLine.remove();
            currentLine = createMeasurementLine(startPoint.x, startPoint.y, endX, endY, true);
            measurements.push(currentLine);
            
            isDrawing = false;
            startPoint = null;
            currentLine = null;
        }
        e.preventDefault();
        return;
    }
    
    // Normal panning when not in ruler mode
    isDragging = true;
    startX = e.clientX - lastTranslateX;
    startY = e.clientY - lastTranslateY;
    container.classList.add('dragging');
});

container.addEventListener('mousemove', (e) => {
    if (!isDragging && !isDrawing) {
        const coords = getSVGCoordinates(e);
        if (coords) {
            updateCoordinatesDisplay(coords);
        }
    }
    
    if (isRulerMode && isDrawing && startPoint) {
        const gridContainer = document.getElementById('grid-container');
        const rect = gridContainer.getBoundingClientRect();
        
        let endX = e.clientX - rect.left;
        let endY = e.clientY - rect.top;
        
        if (e.shiftKey) {
            const dx = Math.abs(endX - startPoint.x);
            const dy = Math.abs(endY - startPoint.y);
            
            if (dx > dy) {
                endY = startPoint.y;
            } else {
                endX = startPoint.x;
            }
        }
        
        if (currentLine) currentLine.remove();
        currentLine = createMeasurementLine(startPoint.x, startPoint.y, endX, endY);
    }
    
    // Handle panning when not in ruler mode
    if (isDragging && !isRulerMode) {
        translateX = e.clientX - startX;
        translateY = e.clientY - startY;
        lastTranslateX = translateX;
        lastTranslateY = translateY;
        updateTransformOnly();
    }
});

window.addEventListener('mouseup', (e) => {
    isDragging = false;
    container.classList.remove('dragging');
});

// Add this debounce function near the top of the script
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Modify the wheel event handler
container.addEventListener('wheel', (e) => {
    e.preventDefault();
    
    const rect = container.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const scale = e.deltaY > 0 ? 0.9 : 1.1;
    currentZoom = Math.max(0.1, Math.min(50000, currentZoom * scale));

    translateX = mouseX - (mouseX - translateX) * scale;
    translateY = mouseY - (mouseY - translateY) * scale;
    lastTranslateX = translateX;
    lastTranslateY = translateY;

    clearMeasurements();  // Clear measurements on wheel zoom
    updateTransformOnly();
    debouncedUpdateStyles();
});

// Modify the EventSource handler
const evtSource = new EventSource('/events');
evtSource.onmessage = function(event) {
    // Clear any existing child nodes
    while (content.firstChild) {
        content.removeChild(content.firstChild);
    }
    // Insert the new SVG markup
    content.insertAdjacentHTML('beforeend', event.data);
    const svg = content.querySelector('svg');
    if (svg) {
        parseLayersFromSVG(svg);
        parseComponentsFromSVG(svg);
        processSVGForScaling(svg);
        updateStyles(svg, currentZoom);
        applyLayerVisibility(svg);
        applyComponentVisibility(svg);
        updateRuler();
        updateGrid();
        //analyzeDOMNodes();
    }
};

// Add proper connection cleanup
window.addEventListener('beforeunload', () => {
    evtSource.close();
});

function updateRuler() {
    const svg = content.querySelector('svg');
    if (!svg) return;

    const viewBox = svg.viewBox.baseVal;
    const svgRect = svg.getBoundingClientRect();
    const scaleX = viewBox.width / svgRect.width;
    
    let baseUnitSize = viewBox.width / 5;
    let unitSize = baseUnitSize / currentZoom;
    
    // Round to nice numbers
    if (unitSize >= 1) {
        const exp = Math.floor(Math.log10(unitSize));
        const base = unitSize / Math.pow(10, exp);
        if (base < 1.5) unitSize = Math.pow(10, exp);
        else if (base < 3.5) unitSize = 2 * Math.pow(10, exp);
        else if (base < 7.5) unitSize = 5 * Math.pow(10, exp);
        else unitSize = 10 * Math.pow(10, exp);
    } else {
        const exp = Math.floor(Math.log10(unitSize));
        const base = unitSize / Math.pow(10, exp);
        if (base < 1.5) unitSize = Math.pow(10, exp);
        else if (base < 3.5) unitSize = 2 * Math.pow(10, exp);
        else if (base < 7.5) unitSize = 5 * Math.pow(10, exp);
        else unitSize = 10 * Math.pow(10, exp);
    }
    
    const rulerContent = document.querySelector('#ruler-content');
    const rulerSvg = document.querySelector('#ruler svg');
    
    // Update the ruler SVG attributes
    rulerSvg.setAttribute('width', '300');
    rulerSvg.setAttribute('height', '30');  // Increased height to accommodate larger font
    rulerSvg.setAttribute('preserveAspectRatio', 'none');
    rulerSvg.style.overflow = 'visible';
    
    let unitLabel;
    if (unitSize >= 1) {
        unitLabel = `${unitSize} μm`;
    } else {
        unitLabel = `${(unitSize * 1000).toFixed(0)} nm`;
    }
    
    rulerContent.innerHTML = `
        <!-- Main horizontal line -->
        <line x1="10" y1="15" x2="${(unitSize/scaleX) + 10}" y2="15" 
              stroke="#c43c5c" stroke-width="2px"/>
        
        <!-- Vertical end ticks -->
        <line x1="10" y1="10" x2="10" y2="20" 
              stroke="#c43c5c" stroke-width="2px"/>
        <line x1="${(unitSize/scaleX) + 10}" y1="10" x2="${(unitSize/scaleX) + 10}" y2="20" 
              stroke="#c43c5c" stroke-width="2px"/>
        
        <!-- Label -->
        <text x="${(unitSize/scaleX)/2 + 10}" y="35" 
              text-anchor="middle" 
              font-size="16"
              fill="#c43c5c"
              font-family="system-ui, -apple-system, sans-serif">${unitLabel}</text>
    `;
}

function handleGridButtonClick() {
    const checkbox = document.getElementById('gridToggle');
    checkbox.checked = !checkbox.checked;  // Toggle the checkbox state
    toggleGrid();  // Call the existing toggle function
}

function toggleGrid() {
    const checkbox = document.getElementById('gridToggle');
    showGrid = checkbox.checked;
    requestAnimationFrame(updateGrid);
}

function updateGrid() {
    if (!showGrid) {
        const existingGrid = document.querySelector('#grid-overlay');
        if (existingGrid) existingGrid.remove();
        return;
    }

    // First, ensure grid container exists
    let gridContainer = document.getElementById('grid-container');
    if (!gridContainer) {
        gridContainer = document.createElement('div');
        gridContainer.id = 'grid-container';
        gridContainer.style.position = 'absolute';
        gridContainer.style.top = '0';
        gridContainer.style.left = '0';
        gridContainer.style.width = '100%';
        gridContainer.style.height = '100%';
        gridContainer.style.pointerEvents = 'none';
        container.appendChild(gridContainer);  // Add to main container
    }

    let gridCanvas = document.querySelector('#grid-overlay');
    if (!gridCanvas) {
        gridCanvas = document.createElement('canvas');
        gridCanvas.id = 'grid-overlay';
        gridCanvas.style.position = 'absolute';
        gridCanvas.style.top = '0';
        gridCanvas.style.left = '0';
        gridCanvas.style.pointerEvents = 'none';
        gridContainer.appendChild(gridCanvas);
    }

    const container = document.getElementById('grid-container');
    const rect = container.getBoundingClientRect();
    
    // Set canvas size accounting for device pixel ratio
    const dpr = window.devicePixelRatio || 1;
    gridCanvas.width = rect.width * dpr;
    gridCanvas.height = rect.height * dpr;
    gridCanvas.style.width = `${rect.width}px`;
    gridCanvas.style.height = `${rect.height}px`;

    const ctx = gridCanvas.getContext('2d');
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, rect.width, rect.height);
    
    // Get SVG scaling information
    const svg = content.querySelector('svg');
    if (!svg) return;
    
    // Get the ruler spacing directly from the ruler element
    const rulerContent = document.querySelector('#ruler-content');
    if (!rulerContent) return;
    
    const rulerLine = rulerContent.querySelector('line[x2]');
    if (!rulerLine) return;
    
    // Get the pixel spacing directly from the ruler
    const pixelSpacing = parseFloat(rulerLine.getAttribute('x2'));
    
    // Calculate grid origin based on current transform
    const startX = translateX % pixelSpacing;
    const startY = translateY % pixelSpacing;
    
    // Draw grid
    ctx.beginPath();
    ctx.strokeStyle = '#808080';
    ctx.globalAlpha = 0.3;
    ctx.lineWidth = 1;

    // Vertical lines
    for (let x = startX; x <= rect.width; x += pixelSpacing) {
        ctx.moveTo(x, 0);
        ctx.lineTo(x, rect.height);
    }

    // Horizontal lines
    for (let y = startY; y <= rect.height; y += pixelSpacing) {
        ctx.moveTo(0, y);
        ctx.lineTo(rect.width, y);
    }

    ctx.stroke();
}

// Add this function to analyze DOM nodes
function analyzeDOMNodes() {
    const svg = content.querySelector('svg');
    if (!svg) return;
    
    // Count nodes by type
    const counts = {};
    const countNode = (node) => {
        const type = node.tagName || node.nodeName;
        counts[type] = (counts[type] || 0) + 1;
        node.childNodes.forEach(countNode);
    };
    
    countNode(svg);
}

// Add this near the end of the script, after all function definitions
// Initialize grid if it's enabled by default
document.addEventListener('DOMContentLoaded', function() {
    if (showGrid) {
        requestAnimationFrame(updateGrid);  // Use requestAnimationFrame for smoother initial render
    }
});

// Add keydown event listener for escape key (add near other event listeners)
window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && isRulerMode) {
        toggleRulerMode();
    }
});

// Update the toggleRulerMode function
function toggleRulerMode() {
    isRulerMode = !isRulerMode;
    const rulerButton = document.getElementById('rulerButton');
    
    if (isRulerMode) {
        rulerButton.classList.add('active');
        container.style.cursor = 'crosshair';
    } else {
        rulerButton.classList.remove('active');
        container.style.cursor = 'default';
    }
}

// Keep the original getSVGCoordinates function for coordinate display
function getSVGCoordinates(event) {
    const svg = content.querySelector('svg');
    if (!svg) return null;

    const svgRect = svg.getBoundingClientRect();
    const viewBox = svg.viewBox.baseVal;
    
    // Calculate scales
    const scaleX = viewBox.width / svgRect.width;
    const scaleY = viewBox.height / svgRect.height;
    
    // Get mouse position relative to SVG
    const x = event.clientX - svgRect.left;
    const y = event.clientY - svgRect.top;
    
    // Transform to SVG coordinates
    const svgX = (x * scaleX) + viewBox.x;
    
    // First convert to viewBox coordinates
    const viewBoxY = (y * scaleY) + viewBox.y;
    // Then apply the scale(1 -1) transform
    const svgY = -viewBoxY;
    
    return { x: svgX, y: svgY };
}

// Update createMeasurementLine to handle drawing state
function createMeasurementLine(x1, y1, x2, y2, showMeasurement = false) {
    const gridContainer = document.getElementById('grid-container');
    let measurementSvg = gridContainer.querySelector('#measurement-svg');
    
    if (!measurementSvg) {
        measurementSvg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        measurementSvg.setAttribute('id', 'measurement-svg');
        measurementSvg.setAttribute('style', 'position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none;');
        gridContainer.appendChild(measurementSvg);
    }

    const group = document.createElementNS("http://www.w3.org/2000/svg", "g");
    group.setAttribute('class', 'measurement-group');

    // Main measurement line
    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute('x1', x1);
    line.setAttribute('y1', y1);
    line.setAttribute('x2', x2);
    line.setAttribute('y2', y2);
    line.setAttribute('stroke', '#c43c5c');
    line.setAttribute('stroke-width', '2');
    line.setAttribute('vector-effect', 'non-scaling-stroke');
    
    // Calculate perpendicular direction for ticks
    const dx = x2 - x1;
    const dy = y2 - y1;
    const length = Math.sqrt(dx * dx + dy * dy);
    const tickLength = 10; // Length of the tick marks
    
    if (length > 0) {
        const perpX = -dy / length * tickLength;
        const perpY = dx / length * tickLength;

        // Start tick
        const startTick = document.createElementNS("http://www.w3.org/2000/svg", "line");
        startTick.setAttribute('x1', x1 - perpX/2);
        startTick.setAttribute('y1', y1 - perpY/2);
        startTick.setAttribute('x2', x1 + perpX/2);
        startTick.setAttribute('y2', y1 + perpY/2);
        startTick.setAttribute('stroke', '#c43c5c');
        startTick.setAttribute('stroke-width', '2');
        startTick.setAttribute('vector-effect', 'non-scaling-stroke');

        // End tick
        const endTick = document.createElementNS("http://www.w3.org/2000/svg", "line");
        endTick.setAttribute('x1', x2 - perpX/2);
        endTick.setAttribute('y1', y2 - perpY/2);
        endTick.setAttribute('x2', x2 + perpX/2);
        endTick.setAttribute('y2', y2 + perpY/2);
        endTick.setAttribute('stroke', '#c43c5c');
        endTick.setAttribute('stroke-width', '2');
        endTick.setAttribute('vector-effect', 'non-scaling-stroke');

        group.appendChild(line);
        group.appendChild(startTick);
        group.appendChild(endTick);
    } else {
        group.appendChild(line);
    }

    if (showMeasurement) {
        // Get SVG coordinates for measurements
        const coords1 = getSVGCoordinates({ 
            clientX: x1 + gridContainer.getBoundingClientRect().left, 
            clientY: y1 + gridContainer.getBoundingClientRect().top 
        });
        const coords2 = getSVGCoordinates({ 
            clientX: x2 + gridContainer.getBoundingClientRect().left, 
            clientY: y2 + gridContainer.getBoundingClientRect().top 
        });
        
        const dx = (coords2.x - coords1.x).toFixed(3);
        const dy = (coords2.y - coords1.y).toFixed(3);
        const length = Math.sqrt(Math.pow(coords2.x - coords1.x, 2) + Math.pow(coords2.y - coords1.y, 2)).toFixed(3);
        
        const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
        const midX = (x1 + x2) / 2;
        const midY = (y1 + y2) / 2;
        text.setAttribute('x', midX);
        text.setAttribute('y', midY - 10);
        text.setAttribute('fill', '#c43c5c');
        text.setAttribute('text-anchor', 'middle');
        text.setAttribute('font-family', 'system-ui, -apple-system, sans-serif');
        text.setAttribute('font-size', '18');
        text.setAttribute('vector-effect', 'non-scaling-stroke');
        text.textContent = `dx: ${dx}μm, dy: ${dy}μm, L: ${length}μm`;
        
        group.appendChild(text);
    }
    
    measurementSvg.appendChild(group);
    return group;
}

function clearMeasurements() {
    const measurementSvg = document.querySelector('#measurement-svg');
    if (measurementSvg) {
        measurementSvg.innerHTML = '';
    }
    measurements = [];
}

// Global object to store layer information
let layerInfo = {};
let hasProcessedLayers = false;  // Flag to track if layers have been processed

function parseLayersFromSVG(svg) {
    // Only process layers if we haven't done it yet
    if (hasProcessedLayers) {
        return;
    }
    
    const styleElement = svg.querySelector('style');
    if (!styleElement) return;
    
    const styleText = styleElement.textContent;
    const layerRegex = /\.layer_(\d+)_(\d+)\s*{([^}]*)}/g;
    const newLayerInfo = {};
    
    // First get all defined layers
    let match;
    while ((match = layerRegex.exec(styleText)) !== null) {
        const layerId = `layer_${match[1]}_${match[2]}`;
        const styleContent = match[3];
        
        // Extract color from stroke or fill, checking both properties
        let color = '#808080'; // default color
        const strokeMatch = styleContent.match(/stroke:\s*(#[a-fA-F0-9]{6}|#[a-fA-F0-9]{3})/);
        const fillMatch = styleContent.match(/fill:\s*(#[a-fA-F0-9]{6}|#[a-fA-F0-9]{3})/);
        
        // Prefer stroke color over fill color if both exist
        if (strokeMatch) {
            color = strokeMatch[1];
        } else if (fillMatch) {
            color = fillMatch[1];
        }
        
        // Check if this layer is actually used in any element
        const layerElements = svg.getElementsByClassName(layerId);
        const isUsed = layerElements.length > 0;
        
        newLayerInfo[layerId] = {
            color: color,
            visible: true,
            isUsed: isUsed
        };
    }
    
    // Only update if we found layers
    if (Object.keys(newLayerInfo).length > 0) {
        Object.assign(layerInfo, newLayerInfo);
        hasProcessedLayers = true;
    }
}

function applyLayerVisibility(svg) {
    if (!svg) return;
    
    // Apply visibility based on current layer states
    Object.entries(layerInfo).forEach(([layerId, info]) => {
        const layerElements = svg.getElementsByClassName(layerId);
        Array.from(layerElements).forEach(element => {
            element.style.display = info.visible ? '' : 'none';
        });
    });
}

function updateLayerControls() {
    const layerList = document.getElementById('layer-list');
    layerList.innerHTML = '';
    
    // Convert to array and sort by usage first, then by layer numbers
    const sortedLayers = Object.entries(layerInfo)
        .map(([layerId, info]) => {
            const [_, num1, num2] = layerId.match(/layer_(\d+)_(\d+)/);
            return {
                layerId,
                info,
                num1: parseInt(num1),
                num2: parseInt(num2)
            };
        })
        .sort((a, b) => {
            // First sort by usage (used layers come first)
            if (a.info.isUsed !== b.info.isUsed) {
                return b.info.isUsed ? 1 : -1;  // true values first
            }
            // Then sort by first number
            if (a.num1 !== b.num1) {
                return a.num1 - b.num1;
            }
            // Finally sort by second number
            return a.num2 - b.num2;
        });
    
    sortedLayers.forEach(({ layerId, info }) => {
        const item = document.createElement('div');
        item.className = 'layer-item';
        if (!info.isUsed) {
            item.style.opacity = '0.5';  // Make unused layers appear faded
            item.style.fontStyle = 'italic';
        }
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.checked = info.visible;
        checkbox.onchange = (e) => {
            layerInfo[layerId].visible = e.target.checked;
            
            const svg = content.querySelector('svg');
            applyLayerVisibility(svg);
        };
        
        const colorIndicator = document.createElement('div');
        colorIndicator.className = 'layer-color-indicator';
        colorIndicator.style.backgroundColor = info.color;
        
        const [_, layerNum1, layerNum2] = layerId.match(/layer_(\d+)_(\d+)/);
        const label = document.createElement('span');
        label.textContent = `Layer (${layerNum1},${layerNum2})`;
        
        item.appendChild(checkbox);
        item.appendChild(colorIndicator);
        item.appendChild(label);
        layerList.appendChild(item);
    });
}

// Global object to store component information
let componentInfo = {
    definitions: {},  // Store component definitions from <defs>
    instances: {},    // Store component instances (uses)
    hierarchy: {}     // Store parent-child relationships
};
let hasProcessedComponents = false;  // Flag to track if components have been processed

function parseComponentsFromSVG(svg) {
    // Only process components if we haven't done it yet
    if (hasProcessedComponents) {
        return;
    }
    
    const defs = svg.querySelector('defs');
    const definitions = defs ? defs.querySelectorAll('g[id]') : [];
    const newComponentInfo = {
        definitions: {},
        instances: {},
        hierarchy: {}
    };
    
    // Process definitions first
    definitions.forEach(def => {
        const id = def.id;
        newComponentInfo.definitions[id] = {
            type: 'definition',
            children: Array.from(def.querySelectorAll(':scope > use')).map(use => {
                const href = use.getAttribute('href');
                return href ? href.substring(1) : null;
            }).filter(id => id)
        };
    });
    
    // Find and process the main circuit
    const mainCircuit = svg.querySelector('g[transform="scale(1 -1)"] > g[id]');
    if (!mainCircuit) return;
    
    function processComponent(element, parentId = null) {
        const id = element.id;
        if (!id) return;
        
        newComponentInfo.instances[id] = {
            type: 'instance',
            parent: parentId,
            children: [],
            visible: true
        };
        
        if (parentId) {
            newComponentInfo.instances[parentId].children.push(id);
        }
        
        // Process use elements and their definitions
        const uses = element.querySelectorAll(':scope > use');
        uses.forEach(use => {
            const href = use.getAttribute('href');
            if (href) {
                const definitionId = href.substring(1);
                const definition = newComponentInfo.definitions[definitionId];
                
                if (definition) {
                    const instanceId = `${definitionId}_instance_${Math.random().toString(36).substr(2, 9)}`;
                    newComponentInfo.instances[instanceId] = {
                        type: 'instance',
                        definitionId: definitionId,
                        parent: id,
                        children: [],
                        visible: true
                    };
                    newComponentInfo.instances[id].children.push(instanceId);
                    
                    // Add children from definition
                    definition.children.forEach(childDefId => {
                        const childInstanceId = `${childDefId}_instance_${Math.random().toString(36).substr(2, 9)}`;
                        newComponentInfo.instances[childInstanceId] = {
                            type: 'instance',
                            definitionId: childDefId,
                            parent: instanceId,
                            children: [],
                            visible: true
                        };
                        newComponentInfo.instances[instanceId].children.push(childInstanceId);
                    });
                }
            }
        });
    }
    
    processComponent(mainCircuit);
    
    if (Object.keys(newComponentInfo.instances).length > 0) {
        componentInfo = newComponentInfo;
        hasProcessedComponents = true;
        updateComponentControls();
    }
}

function applyComponentVisibility(svg) {
    if (!svg) return;
    
    // Helper function to find component elements
    function findComponentElement(id) {
        // First try direct ID
        let element = svg.getElementById(id);
        if (element) return element;
        
        // If not found, look for use elements referencing the definition
        const info = componentInfo.instances[id];
        if (info && info.definitionId) {
            return svg.querySelector(`use[href="#${info.definitionId}"]`);
        }
        return null;
    }
    
    // Apply visibility based on current component states
    Object.entries(componentInfo.instances).forEach(([id, info]) => {
        const element = findComponentElement(id);
        if (element) {
            element.style.display = info.visible ? '' : 'none';
        }
    });
}

function createComponentItem(id, level = 0) {
    const info = componentInfo.instances[id];
    if (!info) return null;
    
    const container = document.createElement('div');
    container.className = 'component-container';
    
    const item = document.createElement('div');
    item.className = 'component-item';
    item.style.setProperty('--level', level);
    
    // Add toggle button if has children
    if (info.children && info.children.length > 0) {
        const toggle = document.createElement('span');
        toggle.className = 'component-toggle';
        toggle.onclick = (e) => {
            e.stopPropagation();
            toggle.classList.toggle('collapsed');
            const childrenContainer = container.querySelector('.component-children');
            if (childrenContainer) {
                childrenContainer.classList.toggle('collapsed');
            }
        };
        item.appendChild(toggle);
    }
    
    const label = document.createElement('span');
    const displayName = info.definitionId || id;
    label.textContent = displayName.split('-')[0];
    
    item.appendChild(label);
    container.appendChild(item);
    
    // Create container for children
    if (info.children && info.children.length > 0) {
        const childrenContainer = document.createElement('div');
        childrenContainer.className = 'component-children';
        // Start collapsed if level is greater than 2
        if (level > 2) {
            childrenContainer.classList.add('collapsed');
            item.querySelector('.component-toggle').classList.add('collapsed');
        }
        info.children.forEach(childId => {
            const childItem = createComponentItem(childId, level + 1);
            if (childItem) {
                childrenContainer.appendChild(childItem);
            }
        });
        container.appendChild(childrenContainer);
    }
    
    return container;
}

function updateComponentControls() {
    const componentTree = document.getElementById('component-tree');
    if (!componentTree) return;
    
    componentTree.innerHTML = '';
    
    function buildTree(parentId = null, level = 0) {
        const children = Object.entries(componentInfo.instances)
            .filter(([_, info]) => info.parent === parentId)
            .map(([id, _]) => id);
        
        children.forEach(id => {
            const item = createComponentItem(id, level);
            if (item) {
                componentTree.appendChild(item);
            }
        });
    }
    
    buildTree();
}

// Add this new function
function toggleSection(sectionId) {
    const section = document.getElementById(sectionId);
    const header = section.previousElementSibling;
    const caret = header.querySelector('.caret');
    const refreshIcon = header.querySelector('.refresh-icon');
    
    // Toggle collapsed state
    const isCollapsing = !section.classList.contains('collapsed');
    section.classList.toggle('collapsed');
    
    // Toggle caret expanded state
    caret.classList.toggle('expanded', !isCollapsing);
    
    // If we're expanding the section, trigger the refresh
    if (!isCollapsing && refreshIcon) {
        // Simulate a click on the refresh icon
        refreshIcon.click();
    }
    
    // Update maxHeight if expanding
    if (!isCollapsing) {
        section.style.maxHeight = section.scrollHeight + "px";
    } else {
        section.style.maxHeight = "0";
    }
}

// Update the initialization
document.addEventListener('DOMContentLoaded', function() {
    // Start with all sections collapsed
    const sections = document.querySelectorAll('.section-content');
    sections.forEach(section => {
        section.style.maxHeight = "0";
    });
});

// Add refresh icons to the section headers in the HTML
document.addEventListener('DOMContentLoaded', function() {
    // Add refresh icons to section headers
    const layersHeader = document.querySelector('#layer-section .section-header');
    const componentsHeader = document.querySelector('#component-section .section-header');
    
    // Function to create controls group
    function createControlsGroup(header) {
        // Remove existing caret
        const existingCaret = header.querySelector('.caret');
        if (existingCaret) {
            existingCaret.remove();
        }
        
        // Create controls group
        const controlsGroup = document.createElement('div');
        controlsGroup.className = 'controls-group';
        
        // Create refresh icon
        const refresh = document.createElement('span');
        refresh.className = 'refresh-icon';
        refresh.innerHTML = '↻';
        
        // Create new caret
        const caret = document.createElement('span');
        caret.className = 'caret collapsed';
        
        // Add both to controls group
        controlsGroup.appendChild(refresh);
        controlsGroup.appendChild(caret);
        
        return { controlsGroup, refresh };
    }
    
    // Setup layers controls
    const layersControls = createControlsGroup(layersHeader);
    layersControls.refresh.title = 'Refresh layers';
    layersControls.refresh.addEventListener('click', (e) => {
        e.stopPropagation();
        
        // Clear existing layer info to force complete reprocessing
        layerInfo = {};
        hasProcessedLayers = false;
        
        const svg = content.querySelector('svg');
        if (svg) {
            // Process layers from SVG, which will extract colors from the style definitions
            parseLayersFromSVG(svg);
            updateLayerControls();
            applyLayerVisibility(svg);
        }
    });
    layersHeader.appendChild(layersControls.controlsGroup);
    
    // Setup components controls
    const componentsControls = createControlsGroup(componentsHeader);
    componentsControls.refresh.title = 'Refresh components';
    componentsControls.refresh.addEventListener('click', (e) => {
        e.stopPropagation();
        componentInfo = {
            definitions: {},
            instances: {},
            hierarchy: {}
        };
        hasProcessedComponents = false;
        const svg = content.querySelector('svg');
        if (svg) {
            parseComponentsFromSVG(svg);
            updateComponentControls();
            applyComponentVisibility(svg);
        }
    });
    componentsHeader.appendChild(componentsControls.controlsGroup);
});
