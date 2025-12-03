/**
 * Batch Approval and Dynamic Pagination for Telethon Admin
 * 
 * Features:
 * - Batch select/deselect media files
 * - Batch approval with progress tracking
 * - Dynamic pagination (100, 200, 500, 1000 items per page)
 * - Real-time feedback and error handling
 */

// Global state for batch operations
const batchState = {
    selectedIds: new Set(),
    itemsPerPage: {
        pending: 100,
        media: 100
    },
    currentPage: {
        pending: 1,
        media: 1
    }
};

/**
 * Load pending media with batch selection support
 */
async function loadPendingWithBatch(page = 1) {
    const limit = batchState.itemsPerPage.pending;
    const skip = (page - 1) * limit;
    
    try {
        const res = await fetchAPI(`/api/media/pending?skip=${skip}&limit=${limit}`);
        const items = res.items || [];
        const total = res.total || 0;
        
        if (items.length === 0) {
            showMessage('pendingMessage', 'No pending media', 'info');
            document.getElementById('pendingTableContainer').innerHTML = '';
            document.getElementById('pendingPagination').innerHTML = '';
            return;
        }
        
        // Clear selection when changing pages
        batchState.selectedIds.clear();
        
        // Render table with checkboxes
        const html = `
            <div style="margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <label style="margin-right: 10px;">Items per page:</label>
                    <select id="pendingItemsPerPage" onchange="changePendingItemsPerPage(this.value)" style="padding: 5px;">
                        <option value="100" ${limit === 100 ? 'selected' : ''}>100</option>
                        <option value="200" ${limit === 200 ? 'selected' : ''}>200</option>
                        <option value="500" ${limit === 500 ? 'selected' : ''}>500</option>
                        <option value="1000" ${limit === 1000 ? 'selected' : ''}>1000</option>
                    </select>
                    <span style="margin-left: 15px; color: #7f8c8d;">Showing ${skip + 1}-${Math.min(skip + limit, total)} of ${total}</span>
                </div>
                <div id="batchActions" style="display: none;">
                    <span id="selectedCount" style="margin-right: 10px; font-weight: 600; color: #667eea;">0 selected</span>
                    <button class="btn btn-success" onclick="batchApproveSelected()">Approve Selected</button>
                    <button class="btn btn-danger btn-small" onclick="clearSelection()">Clear</button>
                </div>
            </div>
            <table>
                <thead>
                    <tr>
                        <th style="width: 40px;">
                            <input type="checkbox" id="selectAll" onchange="toggleSelectAll(this.checked)">
                        </th>
                        <th>ID</th>
                        <th>File Name</th>
                        <th>Type</th>
                        <th>Channel</th>
                        <th>Message ID</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
                    ${items.map(m => `
                        <tr id="row-${m.id}" class="media-row">
                            <td>
                                <input type="checkbox" class="media-checkbox" data-id="${m.id}" onchange="toggleMediaSelection(${m.id}, this.checked)">
                            </td>
                            <td>${m.id}</td>
                            <td>${m.file_name}</td>
                            <td><span class="status-badge">${m.file_type}</span></td>
                            <td>${m.channel_username}</td>
                            <td>${m.message_id}</td>
                            <td>
                                <button class="btn btn-success btn-small" onclick="approveMedia(${m.id})">Approve</button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        
        document.getElementById('pendingTableContainer').innerHTML = html;
        
        // Render pagination
        const totalPages = Math.ceil(total / limit);
        renderDynamicPagination('pendingPagination', page, totalPages, total, skip, limit, loadPendingWithBatch);
        
        batchState.currentPage.pending = page;
    } catch (err) {
        showMessage('pendingMessage', `Error: ${err.message}`, 'error');
    }
}

/**
 * Change items per page for pending media
 */
function changePendingItemsPerPage(newLimit) {
    batchState.itemsPerPage.pending = parseInt(newLimit);
    loadPendingWithBatch(1); // Reset to page 1
}

/**
 * Toggle selection of a single media item
 */
function toggleMediaSelection(mediaId, isChecked) {
    if (isChecked) {
        batchState.selectedIds.add(mediaId);
        document.getElementById(`row-${mediaId}`).style.background = '#e3f2fd';
    } else {
        batchState.selectedIds.delete(mediaId);
        document.getElementById(`row-${mediaId}`).style.background = '';
    }
    
    updateBatchActions();
    updateSelectAllCheckbox();
}

/**
 * Toggle select all checkboxes
 */
function toggleSelectAll(isChecked) {
    const checkboxes = document.querySelectorAll('.media-checkbox');
    checkboxes.forEach(cb => {
        const mediaId = parseInt(cb.dataset.id);
        cb.checked = isChecked;
        toggleMediaSelection(mediaId, isChecked);
    });
}

/**
 * Update select all checkbox state
 */
function updateSelectAllCheckbox() {
    const checkboxes = document.querySelectorAll('.media-checkbox');
    const selectAll = document.getElementById('selectAll');
    if (!selectAll || checkboxes.length === 0) return;
    
    const allChecked = Array.from(checkboxes).every(cb => cb.checked);
    const someChecked = Array.from(checkboxes).some(cb => cb.checked);
    
    selectAll.checked = allChecked;
    selectAll.indeterminate = someChecked && !allChecked;
}

/**
 * Update batch actions visibility and counter
 */
function updateBatchActions() {
    const count = batchState.selectedIds.size;
    const batchActions = document.getElementById('batchActions');
    const selectedCount = document.getElementById('selectedCount');
    
    if (batchActions && selectedCount) {
        if (count > 0) {
            batchActions.style.display = 'block';
            selectedCount.textContent = `${count} selected`;
        } else {
            batchActions.style.display = 'none';
        }
    }
}

/**
 * Clear all selections
 */
function clearSelection() {
    batchState.selectedIds.clear();
    document.querySelectorAll('.media-checkbox').forEach(cb => cb.checked = false);
    document.querySelectorAll('.media-row').forEach(row => row.style.background = '');
    document.getElementById('selectAll').checked = false;
    updateBatchActions();
}

/**
 * Batch approve selected media files
 */
async function batchApproveSelected() {
    const selectedIds = Array.from(batchState.selectedIds);
    
    if (selectedIds.length === 0) {
        showMessage('pendingMessage', 'No items selected', 'error');
        return;
    }
    
    if (selectedIds.length > 100) {
        showMessage('pendingMessage', 'Maximum 100 items can be approved at once', 'error');
        return;
    }
    
    // Confirm action
    if (!confirm(`Approve ${selectedIds.length} media file(s)?`)) {
        return;
    }
    
    // Show progress
    const progressHtml = `
        <div id="batchProgress" style="margin: 15px 0; padding: 15px; background: #f8f9fa; border-radius: 5px;">
            <div style="margin-bottom: 10px; font-weight: 600;">Processing ${selectedIds.length} files...</div>
            <div style="background: #e9ecef; height: 20px; border-radius: 10px; overflow: hidden;">
                <div id="progressBar" style="background: #667eea; height: 100%; width: 0%; transition: width 0.3s;"></div>
            </div>
            <div id="progressText" style="margin-top: 10px; font-size: 13px; color: #7f8c8d;">Starting...</div>
        </div>
    `;
    
    showMessage('pendingMessage', progressHtml, 'info');
    
    try {
        const response = await fetchAPI('/api/media/batch-approve', 'POST', {
            media_ids: selectedIds
        });
        
        // Update progress to 100%
        document.getElementById('progressBar').style.width = '100%';
        document.getElementById('progressText').textContent = 'Complete!';
        
        // Show results
        const resultHtml = `
            <div style="margin-top: 15px;">
                <div style="font-weight: 600; margin-bottom: 10px;">Batch Approval Results:</div>
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 15px;">
                    <div style="padding: 10px; background: #d4edda; border-radius: 5px; text-align: center;">
                        <div style="font-size: 24px; font-weight: 700; color: #155724;">${response.successful}</div>
                        <div style="font-size: 12px; color: #155724;">Successful</div>
                    </div>
                    <div style="padding: 10px; background: #f8d7da; border-radius: 5px; text-align: center;">
                        <div style="font-size: 24px; font-weight: 700; color: #721c24;">${response.failed}</div>
                        <div style="font-size: 12px; color: #721c24;">Failed</div>
                    </div>
                    <div style="padding: 10px; background: #d1ecf1; border-radius: 5px; text-align: center;">
                        <div style="font-size: 24px; font-weight: 700; color: #0c5460;">${response.total}</div>
                        <div style="font-size: 12px; color: #0c5460;">Total</div>
                    </div>
                </div>
                ${response.failed > 0 ? `
                    <details style="margin-top: 10px;">
                        <summary style="cursor: pointer; font-weight: 600; color: #721c24;">View Failed Items (${response.failed})</summary>
                        <ul style="margin-top: 10px; padding-left: 20px;">
                            ${response.failed_items.map(item => `
                                <li style="margin-bottom: 5px; font-size: 13px;">
                                    <strong>ID ${item.id}:</strong> ${item.filename || 'Unknown'} - ${item.error}
                                </li>
                            `).join('')}
                        </ul>
                    </details>
                ` : ''}
            </div>
        `;
        
        showMessage('pendingMessage', progressHtml + resultHtml, 'success');
        
        // Reload data after 3 seconds
        setTimeout(() => {
            clearSelection();
            loadPendingWithBatch(batchState.currentPage.pending);
            loadDashboard();
        }, 3000);
        
    } catch (err) {
        showMessage('pendingMessage', `Batch approval failed: ${err.message}`, 'error');
    }
}

/**
 * Render dynamic pagination with page info
 */
function renderDynamicPagination(containerId, currentPage, totalPages, totalItems, skip, limit, loadFunction) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    let html = '<div style="display: flex; justify-content: center; gap: 5px; flex-wrap: wrap;">';
    
    // Previous button
    html += `<button ${currentPage === 1 ? 'disabled' : ''} onclick="${loadFunction.name}(${currentPage - 1})">← Previous</button>`;
    
    // Page numbers (show max 7 pages)
    const maxPages = 7;
    let startPage = Math.max(1, currentPage - Math.floor(maxPages / 2));
    let endPage = Math.min(totalPages, startPage + maxPages - 1);
    
    if (endPage - startPage < maxPages - 1) {
        startPage = Math.max(1, endPage - maxPages + 1);
    }
    
    if (startPage > 1) {
        html += `<button onclick="${loadFunction.name}(1)">1</button>`;
        if (startPage > 2) html += '<button disabled>...</button>';
    }
    
    for (let i = startPage; i <= endPage; i++) {
        html += `<button class="${i === currentPage ? 'active' : ''}" onclick="${loadFunction.name}(${i})">${i}</button>`;
    }
    
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) html += '<button disabled>...</button>';
        html += `<button onclick="${loadFunction.name}(${totalPages})">${totalPages}</button>`;
    }
    
    // Next button
    html += `<button ${currentPage === totalPages ? 'disabled' : ''} onclick="${loadFunction.name}(${currentPage + 1})">Next →</button>`;
    
    html += '</div>';
    
    // Page info
    const endItem = Math.min(skip + limit, totalItems);
    html += `<div class="pagination-info">Showing ${skip + 1}-${endItem} of ${totalItems} items (Page ${currentPage} of ${totalPages})</div>`;
    
    container.innerHTML = html;
}

// Export functions to global scope
window.loadPendingWithBatch = loadPendingWithBatch;
window.changePendingItemsPerPage = changePendingItemsPerPage;
window.toggleMediaSelection = toggleMediaSelection;
window.toggleSelectAll = toggleSelectAll;
window.clearSelection = clearSelection;
window.batchApproveSelected = batchApproveSelected;
