const visualEditor = document.getElementById('visualEditor');
const sourceEditor = document.getElementById('sourceEditor');
const textEditor = document.getElementById('textEditor');
const hiddenContent = document.getElementById('hiddenContent');
const titleInput = document.getElementById('titleInput');
const elementSettings = document.getElementById('elementSettings');
const linkInputDiv = document.getElementById('linkInput');
const linkUrl = document.getElementById('linkUrl');
const addButtonSection = document.getElementById('addButtonSection');
let selectedElement = null;
let draggedBlock = null;
let insertPosition = null;

// --- Toggle Source Code ---
function toggleSourceCode() {
    const panel = document.getElementById('sourceCodePanel');
    const icon = document.getElementById('sourceToggleIcon');
    if (panel.classList.contains('hidden')) {
        panel.classList.remove('hidden');
        icon.textContent = '▲ Hide';
        sourceEditor.value = getCleanHTML();
    } else {
        panel.classList.add('hidden');
        icon.textContent = '▼ Show';
    }
}

// --- Grid Modal ---
function promptAndAddGrid() {
    document.getElementById('gridModal').classList.add('visible');
}
function closeGridModal() {
    document.getElementById('gridModal').classList.remove('visible');
}
function confirmGrid() {
    const cols = parseInt(document.getElementById('gridColsModal').value) || 2;
    if (pendingGridPosition !== null) {
        // Insert at position
        const html = createBlockHTML('grid', cols);
        const temp = document.createElement('div');
        temp.innerHTML = html;
        const newEl = temp.firstElementChild;
        const blocks = Array.from(visualEditor.children).filter(el => el.classList.contains('editor-block'));
        if (pendingGridPosition < blocks.length) {
            visualEditor.insertBefore(newEl, blocks[pendingGridPosition]);
        } else {
            visualEditor.appendChild(newEl);
        }
        pendingGridPosition = null;
        initBlocks();
        syncToSource();
    } else {
        addBlockAtEnd('grid', cols);
    }
    closeGridModal();
}

// --- Get clean HTML ---
function getCleanHTML() {
    const clone = visualEditor.cloneNode(true);
    clone.querySelectorAll('.insert-bar, .drop-indicator').forEach(el => el.remove());
    clone.querySelectorAll('.editor-block').forEach(el => {
        el.classList.remove('editor-block', 'dragging');
        el.removeAttribute('draggable');
    });
    return clone.innerHTML;
}

// --- Sync ---
function syncToSource() {
    const html = getCleanHTML();
    hiddenContent.value = html;
    if (!document.getElementById('sourceCodePanel').classList.contains('hidden')) {
        sourceEditor.value = html;
    }
}

// --- Initialize blocks ---
function initBlocks() {
    // Clear old UI elements
    visualEditor.querySelectorAll('.insert-bar, .drop-indicator').forEach(el => el.remove());

    const blocks = Array.from(visualEditor.children).filter(el =>
        !el.classList.contains('insert-bar') && !el.classList.contains('drop-indicator')
    );

    // Add insert bar at the beginning
    const startBar = createInsertBar(0);
    if (blocks.length > 0) {
        visualEditor.insertBefore(startBar, blocks[0]);
    } else {
        visualEditor.appendChild(startBar);
    }

    blocks.forEach((block, idx) => {
        // Make block draggable
        block.classList.add('editor-block');
        block.setAttribute('draggable', 'true');

        // Drag events
        block.ondragstart = (e) => {
            draggedBlock = block;
            block.classList.add('dragging');
            e.dataTransfer.effectAllowed = 'move';
        };
        block.ondragend = () => {
            block.classList.remove('dragging');
            document.querySelectorAll('.drop-indicator').forEach(el => el.classList.remove('visible'));
            draggedBlock = null;
            syncToSource();
        };

        // Add drop indicator after block
        const indicator = document.createElement('div');
        indicator.className = 'drop-indicator';
        indicator.dataset.position = idx + 1;

        // Drop zone events on block
        block.ondragover = (e) => {
            e.preventDefault();
            if (draggedBlock && draggedBlock !== block) {
                document.querySelectorAll('.drop-indicator').forEach(el => el.classList.remove('visible'));
                indicator.classList.add('visible');
            }
        };
        block.ondragleave = () => {
            indicator.classList.remove('visible');
        };
        block.ondrop = (e) => {
            e.preventDefault();
            indicator.classList.remove('visible');
            if (draggedBlock && draggedBlock !== block) {
                // Insert after this block
                block.parentNode.insertBefore(draggedBlock, block.nextSibling);
                initBlocks();
            }
        };

        // Insert indicator after block
        if (block.nextSibling) {
            visualEditor.insertBefore(indicator, block.nextSibling);
        } else {
            visualEditor.appendChild(indicator);
        }

        // Add insert bar after indicator
        const insertBar = createInsertBar(idx + 1);
        if (indicator.nextSibling) {
            visualEditor.insertBefore(insertBar, indicator.nextSibling);
        } else {
            visualEditor.appendChild(insertBar);
        }
    });
}

function createInsertBar(position) {
    const bar = document.createElement('div');
    bar.className = 'insert-bar';
    bar.innerHTML = `
        <button type="button" class="insert-btn" onclick="promptGridAtPosition(${position})">+ Grid</button>
        <button type="button" class="insert-btn" onclick="insertAtPosition(${position}, 'card')" style="margin-left:4px;">+ Card</button>
        <button type="button" class="insert-btn" onclick="insertAtPosition(${position}, 'text')" style="margin-left:4px;">+ Text</button>
        <button type="button" class="insert-btn" onclick="insertAtPosition(${position}, 'title')" style="margin-left:4px;">+ Title</button>
        <button type="button" class="insert-btn" onclick="insertAtPosition(${position}, 'table')" style="margin-left:4px;">+ Table</button>
        <button type="button" class="insert-btn" onclick="insertAtPosition(${position}, 'button')" style="margin-left:4px;">+ Btn</button>
    `;
    return bar;
}

let pendingGridPosition = null;
function promptGridAtPosition(pos) {
    pendingGridPosition = pos;
    document.getElementById('gridModal').classList.add('visible');
}


function insertAtPosition(pos, type) {
    const html = createBlockHTML(type, 2);
    const temp = document.createElement('div');
    temp.innerHTML = html;
    const newEl = temp.firstElementChild;

    const blocks = Array.from(visualEditor.children).filter(el =>
        el.classList.contains('editor-block')
    );

    if (pos < blocks.length) {
        visualEditor.insertBefore(newEl, blocks[pos]);
    } else {
        visualEditor.appendChild(newEl);
    }

    initBlocks();
    syncToSource();
}

// --- Selection Logic ---
visualEditor.addEventListener('click', (e) => {
    // Check if target is contentEditable
    if (e.target.isContentEditable) {
        // Don't prevent default, allow focus
    } else {
        e.preventDefault(); // Prevent button/link navigation
    }
    e.stopPropagation();

    if (e.target.classList.contains('insert-btn')) return;

    let target = e.target;
    if (target === visualEditor || target.classList.contains('insert-bar') || target.classList.contains('drop-indicator')) {
        hideSettings();
        return;
    }

    // Find clickable element
    while (target && target !== visualEditor) {
        if (['DIV', 'H2', 'H3', 'P', 'A', 'BUTTON', 'SPAN', 'TABLE', 'TH', 'TD'].includes(target.tagName)) break;
        target = target.parentElement;
    }

    if (!target || target === visualEditor) return;

    if (selectedElement) selectedElement.classList.remove('selected-element');
    selectedElement = target;
    selectedElement.classList.add('selected-element');
    showSettings();
});

function showSettings() {
    elementSettings.style.display = 'block';

    // Safety check for innerText
    textEditor.value = selectedElement.innerText || '';

    // Show link input - always visible now
    const isButton = selectedElement.tagName === 'A';
    const isCard = selectedElement.classList.contains('terminal-box');

    if (isButton) {
        linkUrl.value = selectedElement.getAttribute('href') || '';
    } else if (isCard) {
        // Check if card is wrapped in a link
        const parentLink = selectedElement.parentElement;
        if (parentLink && parentLink.tagName === 'A') {
            linkUrl.value = parentLink.getAttribute('href') || '';
        } else {
            linkUrl.value = '';
        }
    } else {
        linkUrl.value = '';
    }

    // Show table controls if inside a table or wrapper
    const isTableWrapper = selectedElement.classList.contains('overflow-x-auto') && selectedElement.querySelector('table');
    const isTable = selectedElement.tagName === 'TABLE';
    const isInsideTable = selectedElement.closest && selectedElement.closest('table');

    if (isTableWrapper || isTable || isInsideTable) {
        document.getElementById('tableControlsSection').style.display = 'block';
    } else {
        document.getElementById('tableControlsSection').style.display = 'none';
    }
}

function getSelectedTable() {
    if (!selectedElement) return null;
    if (selectedElement.tagName === 'TABLE') return selectedElement;
    if (selectedElement.classList.contains('overflow-x-auto') && selectedElement.querySelector('table')) {
        return selectedElement.querySelector('table');
    }
    return selectedElement.closest ? selectedElement.closest('table') : null;
}

function addTableRow() {
    const table = getSelectedTable();
    if (!table) return;

    const tbody = table.querySelector('tbody');
    const cols = table.querySelector('thead tr').children.length;

    const tr = document.createElement('tr');
    for (let i = 0; i < cols; i++) {
        const td = document.createElement('td');
        td.className = "p-4 border-b border-white/10 outline-none focus:bg-white/5";
        td.contentEditable = true;
        td.textContent = `New Cell`;
        tr.appendChild(td);
    }
    tbody.appendChild(tr);
    syncToSource();
}

function addTableCol() {
    const table = getSelectedTable();
    if (!table) return;

    // Header
    const theadTr = table.querySelector('thead tr');
    const th = document.createElement('th');
    th.className = "p-4 border-b border-white/20 text-cyan text-sm uppercase tracking-wider outline-none focus:bg-white/5";
    th.contentEditable = true;
    th.textContent = `HEADER`;
    theadTr.appendChild(th);

    // Body rows
    const rows = table.querySelectorAll('tbody tr');
    rows.forEach(row => {
        const td = document.createElement('td');
        td.className = "p-4 border-b border-white/10 outline-none focus:bg-white/5";
        td.contentEditable = true;
        td.textContent = `New Cell`;
        row.appendChild(td);
    });
    syncToSource();
}

function hideSettings() {
    elementSettings.style.display = 'none';
    if (selectedElement) selectedElement.classList.remove('selected-element');
    selectedElement = null;
}

// --- Text Editor Sync ---
textEditor.addEventListener('input', () => {
    if (selectedElement) {
        // Preserve child elements for cards
        if (selectedElement.classList.contains('terminal-box')) {
            // Don't overwrite - just update the first text node if needed, or do nothing
        } else {
            selectedElement.innerText = textEditor.value;
        }
        syncToSource();
    }
});

// --- Alignment ---
function setAlignment(align) {
    if (!selectedElement) return;

    // For links/buttons inside a card, move the wrapper
    if (selectedElement.tagName === 'A' && selectedElement.parentElement) {
        const parent = selectedElement.parentElement;
        if (parent.classList.contains('btn-wrapper') || parent.classList.contains('flex')) {
            parent.classList.remove('justify-start', 'justify-center', 'justify-end');
            if (align === 'left') parent.classList.add('justify-start');
            else if (align === 'center') parent.classList.add('justify-center');
            else if (align === 'right') parent.classList.add('justify-end');
            syncToSource();
            return;
        }
    }

    // For other elements, use text alignment
    selectedElement.classList.remove('text-left', 'text-center', 'text-right');
    selectedElement.classList.add('text-' + align);
    syncToSource();
}

// --- Color ---
function setColor(color) {
    if (!selectedElement) return;

    // Remove all existing text colors (both utility and arbitrary if possible)
    // We match utilities we know about + anything starting with text-
    const classesToRemove = [];
    selectedElement.classList.forEach(c => {
        // remove known colors
        if (['text-cyan', 'text-pink', 'text-green', 'text-red', 'text-yellow', 'text-white', 'text-amber', 'text-purple'].includes(c)) {
            classesToRemove.push(c);
        }
        // try to remove custom text colors if they look like tailwind text classes
        if (c.startsWith('text-') && !['text-lg', 'text-xl', 'text-sm', 'text-xs', 'text-base', 'text-2xl', 'text-3xl', 'text-left', 'text-center', 'text-right', 'text-bold', 'text-white/60', 'text-white/80'].includes(c)) {
            classesToRemove.push(c);
        }
    });

    classesToRemove.forEach(c => selectedElement.classList.remove(c));

    // If color is a simple name, map it (legacy support for buttons)
    if (['cyan', 'pink', 'green', 'red', 'yellow', 'white', 'amber', 'purple'].includes(color)) {
        selectedElement.classList.add('text-' + color);
        // Also update border if it's a box
        if (selectedElement.classList.contains('terminal-box') || selectedElement.classList.contains('border')) {
            selectedElement.classList.forEach(c => {
                if (c.startsWith('border-') && c !== 'border-b' && c !== 'border-white/20' && c !== 'border-white/10') {
                    selectedElement.classList.remove(c);
                }
            });
            selectedElement.classList.add('border-' + color);
        }
    } else {
        // Assume it's a full class or valid tailwind suffix
        // If user typed "blue-500", make it "text-blue-500"
        let finalColor = color;
        if (!color.startsWith('text-')) {
            finalColor = 'text-' + color;
        }
        selectedElement.classList.add(finalColor);
    }
    syncToSource();
}

function setCustomColor(val) {
    if (!val) return;
    setColor(val);
}

// --- Background Color ---
function setBgColor(bg) {
    if (!selectedElement) return;
    const el = selectedElement;

    // Remove existing bg classes
    const classesToRemove = [];
    el.classList.forEach(c => {
        if (c.startsWith('bg-') && c !== 'bg-gradient-to-r') {
            // Avoid removing bg-black if it's the base
            classesToRemove.push(c);
        }
    });
    classesToRemove.forEach(c => el.classList.remove(c));

    // Add new bg class
    if (bg) {
        el.classList.add(bg);
    }

    // Clear inline styles if they conflict (from previous version hack)
    el.style.backgroundColor = '';

    syncToSource();
}


// --- Size ---
function setSize(size) {
    if (!selectedElement) return;
    selectedElement.classList.remove('text-xs', 'text-sm', 'text-base', 'text-lg', 'text-xl', 'text-2xl', 'text-3xl');
    selectedElement.classList.add(size);
    syncToSource();
}

// --- Link ---
function applyLink() {
    if (!selectedElement) return;
    const url = linkUrl.value.trim();

    if (selectedElement.tagName === 'A') {
        // For buttons/links, just set href
        selectedElement.setAttribute('href', url);
    } else if (selectedElement.classList.contains('terminal-box')) {
        // For cards, wrap in a link or update existing wrapper
        const parent = selectedElement.parentElement;
        if (parent && parent.tagName === 'A') {
            if (url) {
                parent.setAttribute('href', url);
            } else {
                parent.replaceWith(selectedElement);
            }
        } else if (url) {
            const link = document.createElement('a');
            link.href = url;
            link.className = 'block';
            selectedElement.parentNode.insertBefore(link, selectedElement);
            link.appendChild(selectedElement);
        }
    }
    syncToSource();
    initBlocks();
}


// --- Delete ---
function deleteElement() {
    if (!selectedElement) return;
    selectedElement.remove();
    hideSettings();
    initBlocks();
    syncToSource();
}

// --- Source Editor Sync ---
sourceEditor.addEventListener('input', () => {
    visualEditor.innerHTML = sourceEditor.value;
    hiddenContent.value = sourceEditor.value;
    hideSettings();
    initBlocks();
});

// --- Form Submit Sync ---
document.getElementById('pageForm').addEventListener('submit', () => {
    hiddenContent.value = getCleanHTML();
});

// --- Create Block HTML ---
function createBlockHTML(type, cols = 2) {
    switch (type) {
        case 'grid':
            let gridItems = '';
            const colors = ['cyan', 'pink', 'green', 'yellow'];
            for (let i = 0; i < cols; i++) {
                const c = colors[i % colors.length];
                gridItems += `<div class="terminal-box p-6 border-${c}"><h3 class="text-xl font-bold text-${c} mb-2">Feature ${i + 1}</h3><p class="text-white/60">Description here...</p></div>`;
            }
            return `<div class="grid md:grid-cols-${cols} gap-6 mb-8">${gridItems}</div>`;
        case 'card':
            return `<div class="terminal-box p-6 border-cyan mb-8"><h3 class="text-xl font-bold text-cyan mb-2">Card Title</h3><p class="text-white/60 mb-4">Your content goes here.</p><div class="btn-wrapper flex justify-start mt-4"><a href="#" class="inline-block px-4 py-2 bg-cyan text-black text-xs font-bold uppercase hover:bg-white transition-colors">Action →</a></div></div>`;
        case 'title':
            return `<h2 class="text-xl font-bold text-white tracking-tighter uppercase mb-6">Section Title</h2>`;
        case 'text':
            return `<p class="text-white/80 mb-6 leading-relaxed">Click here to edit this text.</p>`;
        case 'button':
            return `<div class="btn-wrapper flex justify-start mb-6"><a href="#" class="inline-block px-6 py-3 bg-cyan text-black font-bold uppercase text-sm hover:bg-white transition-colors">Button Text</a></div>`;
        case 'table':
            return `
<div class="terminal-box p-6 border-cyan mb-8 overflow-x-auto">
    <h3 class="text-xl font-bold text-cyan mb-4">Table Title</h3>
    <table class="w-full text-left border-collapse">
        <thead>
            <tr>
                <th contenteditable="true" class="p-4 border-b border-white/20 text-cyan text-sm uppercase tracking-wider outline-none focus:bg-white/5">Header 1</th>
                <th contenteditable="true" class="p-4 border-b border-white/20 text-cyan text-sm uppercase tracking-wider outline-none focus:bg-white/5">Header 2</th>
                <th contenteditable="true" class="p-4 border-b border-white/20 text-cyan text-sm uppercase tracking-wider outline-none focus:bg-white/5">Header 3</th>
            </tr>
        </thead>
        <tbody class="text-white/80 text-sm">
            <tr>
                <td contenteditable="true" class="p-4 border-b border-white/10 outline-none focus:bg-white/5">Row 1, Col 1</td>
                <td contenteditable="true" class="p-4 border-b border-white/10 outline-none focus:bg-white/5">Row 1, Col 2</td>
                <td contenteditable="true" class="p-4 border-b border-white/10 outline-none focus:bg-white/5">Row 1, Col 3</td>
            </tr>
        </tbody>
    </table>
</div>`;
    }
    return '';
}

// --- Add Block at End ---
function addBlockAtEnd(type, cols = 2) {
    const html = createBlockHTML(type, cols);
    const temp = document.createElement('div');
    temp.innerHTML = html;
    const newEl = temp.firstElementChild;
    visualEditor.appendChild(newEl);
    initBlocks();
    syncToSource();
}

// --- Initialize on load ---
initBlocks();
syncToSource();
