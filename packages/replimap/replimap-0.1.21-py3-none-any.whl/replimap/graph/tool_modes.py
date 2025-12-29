"""
Tool mode system for graph interactions.

Modes:
- SELECT: Default. Click shows details panel.
- TRACE: Click highlights upstream/downstream path.
- BLAST: Click shows blast radius impact.
- COST: Click shows cost breakdown.
"""

from __future__ import annotations

from enum import Enum


class ToolMode(Enum):
    """Available tool modes for graph interaction."""

    SELECT = "select"
    TRACE = "trace"
    BLAST = "blast"
    COST = "cost"


def generate_tool_palette_html() -> str:
    """Generate HTML for tool mode palette."""
    return """
    <div class="tool-palette" id="toolPalette">
        <button class="tool-btn active" data-mode="select" title="Select (show details)">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M3 3l7.07 16.97 2.51-7.39 7.39-2.51L3 3z"/>
            </svg>
        </button>
        <button class="tool-btn" data-mode="trace" title="Trace (show data flow)">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
            </svg>
        </button>
        <button class="tool-btn" data-mode="blast" title="Blast Radius (show impact)">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>
            </svg>
        </button>
    </div>
    """


def generate_tool_palette_js() -> str:
    """Generate JavaScript for tool mode switching."""
    return """
    let currentToolMode = 'select';

    // Tool palette initialization
    document.querySelectorAll('#toolPalette .tool-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('#toolPalette .tool-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            currentToolMode = this.dataset.mode;
            document.body.dataset.toolMode = currentToolMode;
            clearAllHighlights();
            updateCursor();
        });
    });

    function updateCursor() {
        const cursors = {
            'select': 'pointer',
            'trace': 'crosshair',
            'blast': 'cell',
            'cost': 'help'
        };
        document.getElementById('graph').style.cursor = cursors[currentToolMode] || 'default';
    }

    function clearAllHighlights() {
        node.classed('dimmed', false)
            .classed('highlighted', false)
            .classed('blast-affected', false)
            .classed('blast-indirect', false)
            .classed('blast-source', false)
            .classed('trace-path', false);

        link.classed('dimmed', false)
            .classed('highlighted', false)
            .classed('blast-path', false)
            .classed('trace-path', false);

        // Hide any panels
        document.getElementById('blastPanel')?.classList.remove('visible');
        document.getElementById('tracePanel')?.classList.remove('visible');
    }

    // Click handler that dispatches based on tool mode
    function handleNodeClick(event, d) {
        event.stopPropagation();

        // Summary nodes always drill down
        if (d.is_summary && d.expandable) {
            handleSummaryClick(d);
            return;
        }

        switch (currentToolMode) {
            case 'select':
                selectNode(d);
                highlightConnections(d);
                break;
            case 'trace':
                traceDataFlow(d);
                break;
            case 'blast':
                showBlastRadius(d.id);
                break;
            case 'cost':
                showCostBreakdown(d);
                break;
        }
    }

    // Highlight connections for select mode
    function highlightConnections(d) {
        const connectedNodeIds = new Set();
        connectedNodeIds.add(d.id);

        graphData.links.forEach(link => {
            const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
            const targetId = typeof link.target === 'object' ? link.target.id : link.target;
            if (sourceId === d.id) connectedNodeIds.add(targetId);
            if (targetId === d.id) connectedNodeIds.add(sourceId);
        });

        node.classed('dimmed', n => !connectedNodeIds.has(n.id));
        node.classed('highlighted', n => n.id === d.id);

        link.classed('dimmed', l => {
            const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
            const targetId = typeof l.target === 'object' ? l.target.id : l.target;
            return sourceId !== d.id && targetId !== d.id;
        });
        link.classed('highlighted', l => {
            const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
            const targetId = typeof l.target === 'object' ? l.target.id : l.target;
            return sourceId === d.id || targetId === d.id;
        });
    }

    // Trace data flow (upstream and downstream)
    function traceDataFlow(d) {
        const upstream = new Set();
        const downstream = new Set();
        const allPath = new Set([d.id]);

        // BFS upstream (who depends on this)
        let queue = [d.id];
        while (queue.length > 0) {
            const current = queue.shift();
            graphData.links.forEach(link => {
                const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
                const targetId = typeof link.target === 'object' ? link.target.id : link.target;
                // Upstream: source -> current (source depends on current)
                if (targetId === current && !upstream.has(sourceId) && sourceId !== d.id) {
                    upstream.add(sourceId);
                    allPath.add(sourceId);
                    queue.push(sourceId);
                }
            });
        }

        // BFS downstream (what this depends on)
        queue = [d.id];
        while (queue.length > 0) {
            const current = queue.shift();
            graphData.links.forEach(link => {
                const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
                const targetId = typeof link.target === 'object' ? link.target.id : link.target;
                // Downstream: current -> target (current depends on target)
                if (sourceId === current && !downstream.has(targetId) && targetId !== d.id) {
                    downstream.add(targetId);
                    allPath.add(targetId);
                    queue.push(targetId);
                }
            });
        }

        // Apply visual styling
        node.classed('dimmed', n => !allPath.has(n.id));
        node.classed('highlighted', n => n.id === d.id);
        node.classed('trace-upstream', n => upstream.has(n.id));
        node.classed('trace-downstream', n => downstream.has(n.id));

        link.classed('dimmed', l => {
            const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
            const targetId = typeof l.target === 'object' ? l.target.id : l.target;
            return !allPath.has(sourceId) || !allPath.has(targetId);
        });
        link.classed('trace-path', l => {
            const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
            const targetId = typeof l.target === 'object' ? l.target.id : l.target;
            return allPath.has(sourceId) && allPath.has(targetId);
        });

        showTracePanel(d, upstream.size, downstream.size);
    }

    function showTracePanel(d, upstreamCount, downstreamCount) {
        const panel = document.getElementById('tracePanel');
        if (!panel) return;

        panel.innerHTML = `
            <div class="trace-summary">
                <h4>&#x2194; Data Flow: ${d.name || d.id}</h4>
                <div class="trace-stats">
                    <div class="trace-stat">
                        <span class="trace-count upstream">${upstreamCount}</span>
                        <span class="trace-label">Upstream</span>
                    </div>
                    <div class="trace-stat">
                        <span class="trace-count downstream">${downstreamCount}</span>
                        <span class="trace-label">Downstream</span>
                    </div>
                </div>
            </div>
        `;
        panel.classList.add('visible');
    }

    // Blast radius visualization
    function showBlastRadius(nodeId) {
        const affected = calculateBlastRadius(nodeId);

        // Visual updates
        node.classed('blast-affected', d => affected.direct.has(d.id));
        node.classed('blast-indirect', d => affected.indirect.has(d.id));
        node.classed('blast-source', d => d.id === nodeId);
        node.classed('dimmed', d => !affected.all.has(d.id) && d.id !== nodeId);

        link.classed('blast-path', l => {
            const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
            const targetId = typeof l.target === 'object' ? l.target.id : l.target;
            return affected.all.has(sourceId) && affected.all.has(targetId);
        });
        link.classed('dimmed', l => {
            const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
            const targetId = typeof l.target === 'object' ? l.target.id : l.target;
            return !affected.all.has(sourceId) || !affected.all.has(targetId);
        });

        showBlastSummary(nodeId, affected);
    }

    function calculateBlastRadius(nodeId) {
        const direct = new Set();
        const indirect = new Set();
        const visited = new Set([nodeId]);

        // BFS to find all affected nodes
        let queue = [{ id: nodeId, depth: 0 }];

        while (queue.length > 0) {
            const { id, depth } = queue.shift();

            // Find nodes that depend on this node
            graphData.links.forEach(link => {
                const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
                const targetId = typeof link.target === 'object' ? link.target.id : link.target;

                // If this node is the target (dependency), find who depends on it
                if (targetId === id && !visited.has(sourceId)) {
                    visited.add(sourceId);

                    if (depth === 0) {
                        direct.add(sourceId);
                    } else {
                        indirect.add(sourceId);
                    }

                    // Continue traversal (limit depth to prevent infinite loops)
                    if (depth < 5) {
                        queue.push({ id: sourceId, depth: depth + 1 });
                    }
                }
            });
        }

        return {
            direct,
            indirect,
            all: new Set([...direct, ...indirect]),
        };
    }

    function showBlastSummary(nodeId, affected) {
        const panel = document.getElementById('blastPanel');
        if (!panel) return;

        const sourceNode = graphData.nodes.find(n => n.id === nodeId);
        const directNodes = [...affected.direct].map(id => graphData.nodes.find(n => n.id === id)).filter(Boolean);

        panel.innerHTML = `
            <div class="blast-summary">
                <h4>&#x1F525; Blast Radius: ${sourceNode?.name || nodeId}</h4>
                <div class="blast-stats">
                    <div class="blast-stat">
                        <span class="blast-count direct">${affected.direct.size}</span>
                        <span class="blast-label">Direct Impact</span>
                    </div>
                    <div class="blast-stat">
                        <span class="blast-count indirect">${affected.indirect.size}</span>
                        <span class="blast-label">Indirect Impact</span>
                    </div>
                </div>
                <div class="blast-list">
                    <h5>Directly Affected:</h5>
                    <ul>
                        ${directNodes.slice(0, 5).map(n => `<li>${n.name} (${n.type.replace('aws_', '')})</li>`).join('')}
                        ${directNodes.length > 5 ? `<li>...and ${directNodes.length - 5} more</li>` : ''}
                    </ul>
                </div>
            </div>
        `;
        panel.classList.add('visible');
    }

    function showCostBreakdown(d) {
        // Show cost information in details panel
        selectNode(d);

        const cost = d.cost || d.properties?.cost;
        if (cost) {
            const costInfo = document.createElement('div');
            costInfo.className = 'cost-breakdown';
            costInfo.innerHTML = `
                <h4>Cost Estimate</h4>
                <div class="cost-value">${typeof cost === 'object' ? cost.formatted : '$' + cost}/mo</div>
            `;
            document.getElementById('detail-properties').prepend(costInfo);
        }
    }
    """


def generate_tool_palette_css() -> str:
    """Generate CSS for tool palette and effects."""
    return """
    /* Tool Palette */
    .tool-palette {
        position: absolute;
        left: 20px;
        top: 50%;
        transform: translateY(-50%);
        background: rgba(30, 41, 59, 0.95);
        border-radius: 12px;
        padding: 8px;
        display: flex;
        flex-direction: column;
        gap: 4px;
        border: 1px solid #334155;
        z-index: 100;
    }

    .tool-palette .tool-btn {
        width: 40px;
        height: 40px;
        border-radius: 8px;
        background: transparent;
        border: 1px solid transparent;
        color: #94a3b8;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.2s;
    }

    .tool-palette .tool-btn:hover {
        background: #334155;
        color: #f1f5f9;
    }

    .tool-palette .tool-btn.active {
        background: #6366f1;
        border-color: #6366f1;
        color: white;
    }

    /* Trace styles */
    .node.trace-upstream circle {
        stroke: #3b82f6 !important;
        stroke-width: 3px !important;
    }

    .node.trace-downstream circle {
        stroke: #22c55e !important;
        stroke-width: 3px !important;
    }

    .link.trace-path {
        stroke: #818cf8 !important;
        stroke-width: 3px !important;
        stroke-opacity: 1 !important;
    }

    /* Blast radius styles */
    .node.blast-source circle {
        stroke: #dc2626 !important;
        stroke-width: 4px !important;
        filter: drop-shadow(0 0 12px #dc2626);
    }

    .node.blast-affected circle {
        stroke: #f97316 !important;
        stroke-width: 3px !important;
        filter: drop-shadow(0 0 6px #f97316);
    }

    .node.blast-indirect circle {
        stroke: #fbbf24 !important;
        stroke-width: 2px !important;
    }

    .link.blast-path {
        stroke: #f97316 !important;
        stroke-width: 3px !important;
        stroke-opacity: 1 !important;
    }

    /* Blast/Trace panels */
    #blastPanel, #tracePanel {
        position: absolute;
        bottom: 80px;
        left: 80px;
        background: rgba(30, 41, 59, 0.95);
        border: 2px solid #dc2626;
        border-radius: 12px;
        padding: 16px;
        width: 280px;
        display: none;
        z-index: 100;
    }

    #tracePanel {
        border-color: #6366f1;
    }

    #blastPanel.visible, #tracePanel.visible {
        display: block;
    }

    .blast-summary h4, .trace-summary h4 {
        margin: 0 0 12px 0;
        color: #f1f5f9;
        font-size: 14px;
    }

    .blast-stats, .trace-stats {
        display: flex;
        gap: 16px;
        margin-bottom: 12px;
    }

    .blast-stat, .trace-stat {
        text-align: center;
    }

    .blast-count, .trace-count {
        font-size: 24px;
        font-weight: 700;
        display: block;
    }

    .blast-count.direct, .trace-count.upstream { color: #f97316; }
    .blast-count.indirect, .trace-count.downstream { color: #fbbf24; }

    .blast-label, .trace-label {
        font-size: 11px;
        color: #94a3b8;
    }

    .blast-list h5, .trace-list h5 {
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        color: #64748b;
        margin: 0 0 6px 0;
    }

    .blast-list ul, .trace-list ul {
        margin: 0;
        padding: 0 0 0 16px;
        font-size: 12px;
        color: #94a3b8;
    }

    .blast-list li, .trace-list li {
        margin-bottom: 4px;
    }
    """
