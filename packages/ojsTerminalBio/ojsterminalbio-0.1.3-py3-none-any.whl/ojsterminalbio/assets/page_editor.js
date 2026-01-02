const visualEditor = document.getElementById('visualEditor');
const sourceEditor = document.getElementById('sourceEditor');
const textEditor = document.getElementById('textEditor');
const hiddenContent = document.getElementById('hiddenContent');
const titleInput = document.getElementById('titleInput');
const slugInput = document.getElementById('slugInput');
const elementSettings = document.getElementById('elementSettings');
const linkInputDiv = document.getElementById('linkInput');
const linkUrl = document.getElementById('linkUrl');
const addButtonSection = document.getElementById('addButtonSection');
let selectedElement = null;
let draggedBlock = null;
let insertPosition = null;

// --- Auto-Slug ---
titleInput.addEventListener('input', () => {
    if (!slugInput.dataset.manual) {
        slugInput.value = titleInput.value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
    }
});
slugInput.addEventListener('input', () => { slugInput.dataset.manual = 'true'; });

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
        <button type="button" class="insert-btn" onclick="insertAtPosition(${position}, 'skills')" style="margin-left:4px;">+ Skills</button>
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
    textEditor.value = selectedElement.innerText;

    // Show link input - always visible now
    const isButton = selectedElement.tagName === 'A';
    const isCard = selectedElement.classList.contains('terminal-box');

    if (isButton) {
        linkUrl.value = selectedElement.getAttribute('href') || '';
        document.getElementById('buttonStyleSection').style.display = 'block';
    } else if (isCard) {
        // Check if card is wrapped in a link
        const parentLink = selectedElement.parentElement;
        if (parentLink && parentLink.tagName === 'A') {
            linkUrl.value = parentLink.getAttribute('href') || '';
        } else {
            linkUrl.value = '';
        }
        document.getElementById('buttonStyleSection').style.display = 'none';
    } else {
        linkUrl.value = '';
        document.getElementById('buttonStyleSection').style.display = 'none';
    }

    // Show "Add Action Button" for cards (terminal-box)
    if (isCard) {
        addButtonSection.style.display = 'block';
    } else {
        addButtonSection.style.display = 'none';
    }

    // Show "Add Tag" for all cards (terminal-box)
    if (isCard) {
        document.getElementById('addTagSection').style.display = 'block';
    } else {
        document.getElementById('addTagSection').style.display = 'none';
    }

    // Show grid move if parent is a grid
    const parent = selectedElement.parentElement;
    if (parent && parent.classList.contains('grid')) {
        document.getElementById('gridMoveSection').style.display = 'block';
    } else {
        document.getElementById('gridMoveSection').style.display = 'none';
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

function formatTableHead() {
    const table = getSelectedTable();
    if (!table) return;
    // Just toggle header visibility or style? For now let's just sync
    syncToSource();
}

function hideSettings() {
    elementSettings.style.display = 'none';
    if (selectedElement) selectedElement.classList.remove('selected-element');
    selectedElement = null;
}

// --- Add Action Button to Card ---
function addActionButton() {
    if (!selectedElement || !selectedElement.classList.contains('terminal-box')) return;

    // Check if already has a button wrapper
    let wrapper = selectedElement.querySelector('.btn-wrapper');
    if (!wrapper) {
        wrapper = document.createElement('div');
        wrapper.className = 'btn-wrapper flex justify-start mt-4';
        selectedElement.appendChild(wrapper);
    }

    const btn = document.createElement('a');
    btn.href = '#';
    btn.className = 'inline-block px-4 py-2 bg-cyan text-black text-xs font-bold uppercase hover:bg-white transition-colors mr-2';
    btn.textContent = 'Action →';
    wrapper.appendChild(btn);

    syncToSource();
}

let currentTagColor = 'cyan';

// --- Add Tag ---
function addTag() {
    if (!selectedElement || !selectedElement.classList.contains('terminal-box')) return;

    const input = document.getElementById('newTagInput');
    const tagText = input.value.trim();
    if (!tagText) return;

    // Find flex-wrap container
    let container = selectedElement.querySelector('.flex-wrap');
    if (!container) {
        container = document.createElement('div');
        container.className = 'flex flex-wrap gap-2';
        selectedElement.appendChild(container);
    }

    const tag = document.createElement('span');
    tag.className = `px-3 py-1 m-1 bg-${currentTagColor}/20 text-${currentTagColor} text-xs rounded-full border border-${currentTagColor}/30`;
    tag.textContent = tagText;
    container.appendChild(tag);

    input.value = '';
    syncToSource();
}

function addTagWithColor(color) {
    currentTagColor = color;
    addTag();
}

// --- Text Editor Sync ---
textEditor.addEventListener('input', () => {
    if (selectedElement) {
        // Preserve child elements for cards
        if (selectedElement.classList.contains('terminal-box')) {
            // Don't overwrite - just update the first text node
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
    selectedElement.classList.remove('text-cyan', 'text-pink', 'text-green', 'text-red', 'text-yellow', 'text-white', 'text-white/60', 'text-white/80');
    selectedElement.classList.add('text-' + color);
    if (selectedElement.classList.contains('terminal-box')) {
        selectedElement.classList.remove('border-cyan', 'border-pink', 'border-green', 'border-red', 'border-yellow');
        selectedElement.classList.add('border-' + color);
    }
    syncToSource();
}

// --- Background Color ---
function setBgColor(bg) {
    if (!selectedElement) return;
    // For cards with terminal-box, we need to handle it specially
    const el = selectedElement;

    // Remove existing bg classes
    el.classList.forEach(c => {
        if (c.startsWith('bg-') && c !== 'bg-gradient-to-r') {
            el.classList.remove(c);
        }
    });

    // Add new bg class
    el.classList.add(bg);

    // For terminal-box, also set inline style as fallback
    if (el.classList.contains('terminal-box')) {
        if (bg === 'bg-cyan/20') el.style.backgroundColor = 'rgba(0,243,255,0.2)';
        else if (bg === 'bg-pink/20') el.style.backgroundColor = 'rgba(255,0,85,0.2)';
        else if (bg === 'bg-green/20') el.style.backgroundColor = 'rgba(0,255,136,0.2)';
        else if (bg === 'bg-white/10') el.style.backgroundColor = 'rgba(255,255,255,0.1)';
        else if (bg === 'bg-black') el.style.backgroundColor = '#000';
        else if (bg === 'bg-transparent') el.style.backgroundColor = 'transparent';
    }

    syncToSource();
}

// --- Border Color ---
function setBorderColor(color) {
    if (!selectedElement) return;
    const el = selectedElement;

    // Remove existing border color classes
    el.classList.remove('border-cyan', 'border-pink', 'border-green', 'border-red', 'border-yellow', 'border-white', 'border-transparent');

    if (color === 'transparent') {
        el.classList.add('border-transparent');
        el.style.borderColor = 'transparent';
    } else {
        el.classList.add('border-' + color);
        // Set inline style as fallback
        const colors = {
            cyan: '#00f3ff',
            pink: '#ff0055',
            green: '#00ff88',
            yellow: '#ffcc00',
            white: '#ffffff'
        };
        if (colors[color]) {
            el.style.borderColor = colors[color];
        }
    }

    syncToSource();
}

// --- Move in Grid ---
function moveInGrid(direction) {
    if (!selectedElement) return;
    const parent = selectedElement.parentElement;
    if (!parent || !parent.classList.contains('grid')) return;

    const siblings = Array.from(parent.children);
    const idx = siblings.indexOf(selectedElement);

    if (direction === 'left' && idx > 0) {
        parent.insertBefore(selectedElement, siblings[idx - 1]);
    } else if (direction === 'right' && idx < siblings.length - 1) {
        parent.insertBefore(siblings[idx + 1], selectedElement);
    }
    syncToSource();
}

// --- Size ---
function setSize(size) {
    if (!selectedElement) return;
    selectedElement.classList.remove('text-xs', 'text-sm', 'text-base', 'text-lg', 'text-xl', 'text-2xl', 'text-3xl');
    selectedElement.classList.add(size);
    syncToSource();
}

// --- Style ---
function toggleStyle(style) {
    if (!selectedElement) return;
    selectedElement.classList.toggle(style);
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
            // Already wrapped, update href
            if (url) {
                parent.setAttribute('href', url);
            } else {
                // Remove wrapper if URL is empty
                parent.replaceWith(selectedElement);
            }
        } else if (url) {
            // Wrap in new link
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

// --- Button Shape ---
function setButtonShape(shape) {
    if (!selectedElement || selectedElement.tagName !== 'A') return;
    selectedElement.classList.remove('rounded-none', 'rounded', 'rounded-md', 'rounded-lg', 'rounded-xl', 'rounded-full');
    selectedElement.classList.add(shape);
    syncToSource();
}

// --- Button Padding ---
function setButtonPadding(padding) {
    if (!selectedElement || selectedElement.tagName !== 'A') return;
    // Remove existing padding classes
    const classes = selectedElement.className.split(' ').filter(c => !c.startsWith('px-') && !c.startsWith('py-'));
    selectedElement.className = classes.join(' ') + ' ' + padding;
    syncToSource();
}

// --- Button Background ---
function setButtonBg(bg) {
    if (!selectedElement || selectedElement.tagName !== 'A') return;
    selectedElement.classList.remove('bg-cyan', 'bg-pink', 'bg-green', 'bg-red', 'bg-yellow', 'bg-white', 'bg-transparent', 'bg-black');
    selectedElement.classList.add(bg);
    // If transparent, add border and change text color
    if (bg === 'bg-transparent') {
        selectedElement.classList.remove('text-black');
        selectedElement.classList.add('text-cyan', 'border', 'border-cyan');
    } else {
        selectedElement.classList.remove('border', 'border-cyan', 'text-cyan');
        selectedElement.classList.add('text-black');
    }
    syncToSource();
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
        case 'skills':
            return `<div class="terminal-box p-6 border-cyan mb-8"><h3 class="text-xl font-bold text-cyan mb-4">Research Interests</h3><div class="flex flex-wrap gap-2"><span class="px-3 py-1 bg-cyan/20 text-cyan text-xs rounded-full border border-cyan/30">Machine Learning</span><span class="px-3 py-1 bg-pink/20 text-pink text-xs rounded-full border border-pink/30">NLP</span><span class="px-3 py-1 bg-green/20 text-green text-xs rounded-full border border-green/30">Computer Vision</span><span class="px-3 py-1 bg-yellow/20 text-yellow text-xs rounded-full border border-yellow/30">Data Mining</span></div></div>`;
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
            <tr>
                <td contenteditable="true" class="p-4 border-b border-white/10 outline-none focus:bg-white/5">Row 2, Col 1</td>
                <td contenteditable="true" class="p-4 border-b border-white/10 outline-none focus:bg-white/5">Row 2, Col 2</td>
                <td contenteditable="true" class="p-4 border-b border-white/10 outline-none focus:bg-white/5">Row 2, Col 3</td>
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
