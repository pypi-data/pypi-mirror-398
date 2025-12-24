/**
 * MAD Dashboard MCP Bridge
 * 
 * Client-side runtime for MCP tool registration and execution.
 * This script runs in the browser and:
 * - Establishes WebSocket connection to the MCP relay server
 * - Registers tools (both default UI tools and view-specific tools)
 * - Executes tool calls from AI agents
 * - Provides the window.DashMCP API for view-specific tool registration
 * 
 * Architecture:
 *   AI Agent → MCP Server → WebSocket → This Script → Tool Execution → Result
 */

(function() {
    'use strict';

    // ==========================================================================
    // CONFIGURATION
    // ==========================================================================
    
    const CONFIG = {
        // WebSocket reconnection settings
        reconnectDelay: 1000,      // Initial reconnect delay (ms)
        maxReconnectDelay: 30000,  // Maximum reconnect delay (ms)
        reconnectMultiplier: 1.5,  // Exponential backoff multiplier
        
        // Tool call settings
        defaultTimeout: 30000,     // Default tool execution timeout (ms)
        
        // Debug mode (set via window.DashMCP.debug = true)
        debug: false,
    };

    // ==========================================================================
    // TOOL REGISTRY
    // ==========================================================================
    
    /**
     * Registry of all tools available in this browser tab.
     * Maps tool name -> { description, inputSchema, handler, annotations }
     */
    const TOOL_REGISTRY = new Map();

    // ==========================================================================
    // SESSION MANAGEMENT
    // ==========================================================================
    
    let ws = null;
    let reconnectAttempts = 0;
    let currentReconnectDelay = CONFIG.reconnectDelay;

    /**
     * Get or create unique session ID for this browser tab.
     * Persists across page refreshes within the same tab.
     */
    function getOrCreateSid() {
        const key = 'dash_mcp_sid';
        let sid = sessionStorage.getItem(key);
        if (!sid) {
            // Generate a short, readable session ID
            sid = 'tab_' + Math.random().toString(36).slice(2, 10);
            sessionStorage.setItem(key, sid);
        }
        return sid;
    }

    const SID = getOrCreateSid();

    // ==========================================================================
    // WEBSOCKET COMMUNICATION
    // ==========================================================================
    
    /**
     * Build tool manifest for sending to server.
     */
    function buildToolManifest() {
        return Array.from(TOOL_REGISTRY.entries()).map(([name, tool]) => ({
            name,
            description: tool.description || '',
            inputSchema: tool.inputSchema || { type: 'object', properties: {} },
            annotations: tool.annotations || {},
        }));
    }

    /**
     * Send tool manifest to server.
     */
    function sendToolManifest() {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                type: 'tools',
                sid: SID,
                tools: buildToolManifest(),
            }));
            log('Sent tool manifest:', TOOL_REGISTRY.size, 'tools');
        }
    }

    /**
     * Send page update to server (when navigating).
     */
    function sendPageUpdate() {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                type: 'page_update',
                sid: SID,
                page_url: window.location.href,
                view_id: getCurrentViewId(),
            }));
        }
    }

    /**
     * Get current view ID from URL if on a view page.
     */
    function getCurrentViewId() {
        const match = window.location.pathname.match(/^\/view\/([^/]+)/);
        return match ? match[1] : null;
    }

    /**
     * Connect to WebSocket server.
     */
    async function connect() {
        const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
        const url = `${proto}://${window.location.host}/dash-mcp/ws`;
        
        log('Connecting to MCP bridge:', url);
        
        try {
            ws = new WebSocket(url);
            
            ws.onopen = () => {
                log('WebSocket connected');
                reconnectAttempts = 0;
                currentReconnectDelay = CONFIG.reconnectDelay;
                
                // Send hello with initial tools
                ws.send(JSON.stringify({
                    type: 'hello',
                    sid: SID,
                    page_url: window.location.href,
                    view_id: getCurrentViewId(),
                    tools: buildToolManifest(),
                }));
                
                // Update UI with session info
                updateSessionDisplay();
            };
            
            ws.onmessage = async (event) => {
                let msg;
                try {
                    msg = JSON.parse(event.data);
                } catch (e) {
                    log('Invalid message received:', event.data);
                    return;
                }
                
                log('Received:', msg.type);
                
                // Handle hello acknowledgment
                if (msg.type === 'hello_ack') {
                    log('Session acknowledged:', msg.sid);
                    return;
                }
                
                // Handle tool call
                if (msg.type === 'call') {
                    await handleToolCall(msg);
                    return;
                }
            };
            
            ws.onclose = (event) => {
                log('WebSocket closed:', event.code, event.reason);
                scheduleReconnect();
            };
            
            ws.onerror = (error) => {
                log('WebSocket error:', error);
            };
            
        } catch (error) {
            log('Connection error:', error);
            scheduleReconnect();
        }
    }

    /**
     * Schedule WebSocket reconnection with exponential backoff.
     */
    function scheduleReconnect() {
        reconnectAttempts++;
        const delay = Math.min(currentReconnectDelay, CONFIG.maxReconnectDelay);
        currentReconnectDelay *= CONFIG.reconnectMultiplier;
        
        log(`Reconnecting in ${delay}ms (attempt ${reconnectAttempts})`);
        setTimeout(connect, delay);
    }

    // ==========================================================================
    // TOOL CALL HANDLING
    // ==========================================================================
    
    /**
     * Handle incoming tool call from server.
     */
    async function handleToolCall(msg) {
        const { call_id, tool, args } = msg;
        
        log(`Tool call: ${tool}`, args);
        
        const entry = TOOL_REGISTRY.get(tool);
        
        try {
            if (!entry) {
                throw new Error(`Unknown tool: ${tool}`);
            }
            
            // Human-in-the-loop confirmation (if enabled)
            if (window.DashMCP?.policy?.confirmAll) {
                const confirmed = confirm(
                    `[DashMCP] Allow tool call?\n\n` +
                    `Tool: ${tool}\n\n` +
                    `Arguments:\n${JSON.stringify(args, null, 2)}`
                );
                if (!confirmed) {
                    throw new Error('User denied tool call');
                }
            } else if (!entry.annotations?.readOnly && window.DashMCP?.policy?.confirmMutations) {
                // Only confirm non-readonly tools
                const confirmed = confirm(
                    `[DashMCP] Allow mutation?\n\n` +
                    `Tool: ${tool}\n\n` +
                    `This tool may modify the UI or data.\n\n` +
                    `Arguments:\n${JSON.stringify(args, null, 2)}`
                );
                if (!confirmed) {
                    throw new Error('User denied mutation');
                }
            }
            
            // Execute the tool handler
            const result = await entry.handler(args || {});
            
            // Send result back
            sendResult(call_id, normalizeResult(result));
            
        } catch (error) {
            log(`Tool error: ${tool}:`, error);
            sendResult(call_id, {
                text: `ERROR: ${error.message || String(error)}`,
                structured: { error: true, message: error.message },
            });
        }
    }

    /**
     * Normalize tool result to { text, structured } format.
     */
    function normalizeResult(result) {
        // Already in correct format
        if (result && typeof result === 'object' && ('text' in result || 'structured' in result)) {
            return result;
        }
        
        // String -> text only
        if (typeof result === 'string') {
            return { text: result, structured: null };
        }
        
        // Object -> structured with JSON text
        return {
            text: JSON.stringify(result, null, 2),
            structured: result,
        };
    }

    /**
     * Send tool result back to server.
     */
    function sendResult(call_id, payload) {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                type: 'result',
                sid: SID,
                call_id,
                payload,
            }));
        }
    }

    // ==========================================================================
    // UI HELPERS
    // ==========================================================================
    
    /**
     * Update session display in the UI (if element exists).
     */
    function updateSessionDisplay() {
        const sidEl = document.getElementById('dash-mcp-sid');
        if (sidEl) {
            sidEl.textContent = SID;
        }
        
        const statusEl = document.getElementById('dash-mcp-status');
        if (statusEl) {
            statusEl.textContent = ws?.readyState === WebSocket.OPEN ? 'Connected' : 'Disconnected';
            statusEl.style.color = ws?.readyState === WebSocket.OPEN ? '#22c55e' : '#ef4444';
        }
    }

    /**
     * Debug logging.
     */
    function log(...args) {
        if (CONFIG.debug || window.DashMCP?.debug) {
            console.log('[DashMCP]', ...args);
        }
    }

    // ==========================================================================
    // PUBLIC API: window.DashMCP
    // ==========================================================================
    
    window.DashMCP = {
        /**
         * Session ID for this browser tab.
         */
        sid: SID,
        
        /**
         * Debug mode - set to true for verbose logging.
         */
        debug: false,
        
        /**
         * Policy settings for human-in-the-loop.
         * - confirmAll: Confirm every tool call
         * - confirmMutations: Confirm only non-readonly tools
         */
        policy: {
            confirmAll: false,
            confirmMutations: false,
        },
        
        /**
         * Register a tool that can be called by AI agents.
         * 
         * @param {string} name - Tool name (should be unique within this tab)
         * @param {object} config - Tool configuration
         * @param {string} config.description - Human-readable description
         * @param {object} config.inputSchema - JSON Schema for arguments
         * @param {object} [config.annotations] - MCP annotations (readOnly, etc.)
         * @param {function} handler - Async function that executes the tool
         * 
         * @example
         * window.DashMCP.registerTool(
         *     'getData',
         *     {
         *         description: 'Get data from the current view',
         *         inputSchema: {
         *             type: 'object',
         *             properties: {
         *                 format: { type: 'string', enum: ['json', 'csv'] }
         *             }
         *         },
         *         annotations: { readOnly: true }
         *     },
         *     async ({ format }) => {
         *         const data = await fetchViewData();
         *         return format === 'csv' ? toCsv(data) : data;
         *     }
         * );
         */
        registerTool(name, config, handler) {
            TOOL_REGISTRY.set(name, {
                description: config.description || '',
                inputSchema: config.inputSchema || { type: 'object', properties: {} },
                annotations: config.annotations || {},
                handler,
            });
            
            log(`Registered tool: ${name}`);
            sendToolManifest();
        },
        
        /**
         * Unregister a tool.
         * 
         * @param {string} name - Tool name to unregister
         */
        unregisterTool(name) {
            if (TOOL_REGISTRY.delete(name)) {
                log(`Unregistered tool: ${name}`);
                sendToolManifest();
            }
        },
        
        /**
         * Get list of registered tools.
         * 
         * @returns {string[]} Array of tool names
         */
        getTools() {
            return Array.from(TOOL_REGISTRY.keys());
        },
        
        /**
         * Check if connected to MCP relay.
         * 
         * @returns {boolean} Connection status
         */
        isConnected() {
            return ws?.readyState === WebSocket.OPEN;
        },
        
        /**
         * Force reconnect to MCP relay.
         */
        reconnect() {
            if (ws) {
                ws.close();
            }
            connect();
        },
    };

    // ==========================================================================
    // DEFAULT TOOLS (Built-in UI capabilities)
    // ==========================================================================
    
    /**
     * Register default tools that are always available.
     */
    function registerDefaultTools() {
        // Page info - read-only
        window.DashMCP.registerTool(
            'page.info',
            {
                description: 'Get information about the current page/tab including URL, title, and viewport size.',
                inputSchema: {
                    type: 'object',
                    properties: {},
                    additionalProperties: false,
                },
                annotations: { readOnly: true },
            },
            async () => ({
                url: window.location.href,
                title: document.title,
                sid: SID,
                view_id: getCurrentViewId(),
                viewport: {
                    width: window.innerWidth,
                    height: window.innerHeight,
                },
            })
        );
        
        // DOM snapshot - read-only
        window.DashMCP.registerTool(
            'page.snapshot',
            {
                description: 'Get a snapshot of the page DOM (outerHTML). Useful for understanding page structure and finding element IDs.',
                inputSchema: {
                    type: 'object',
                    properties: {
                        maxLength: {
                            type: 'number',
                            description: 'Maximum characters to return (default: 50000)',
                            default: 50000,
                        },
                        selector: {
                            type: 'string',
                            description: 'CSS selector to get specific element (default: entire page)',
                        },
                    },
                },
                annotations: { readOnly: true },
            },
            async ({ maxLength = 50000, selector } = {}) => {
                let html;
                if (selector) {
                    const el = document.querySelector(selector);
                    if (!el) {
                        return { error: `Element not found: ${selector}` };
                    }
                    html = el.outerHTML;
                } else {
                    html = document.documentElement.outerHTML;
                }
                
                const truncated = html.length > maxLength;
                return {
                    text: html.slice(0, maxLength),
                    structured: {
                        truncated,
                        originalLength: html.length,
                        returnedLength: Math.min(html.length, maxLength),
                    },
                };
            }
        );
        
        // List interactive elements - read-only
        window.DashMCP.registerTool(
            'page.elements',
            {
                description: 'List interactive elements on the page (inputs, buttons, links, dropdowns). Returns IDs and types for use with other tools.',
                inputSchema: {
                    type: 'object',
                    properties: {
                        types: {
                            type: 'array',
                            items: { type: 'string' },
                            description: 'Filter by element types (input, button, select, a). Empty = all.',
                        },
                    },
                },
                annotations: { readOnly: true },
            },
            async ({ types = [] } = {}) => {
                const selectors = types.length > 0 
                    ? types.map(t => t.toLowerCase()).join(',')
                    : 'input, button, select, textarea, a, [role="button"]';
                
                const elements = document.querySelectorAll(selectors);
                const result = [];
                
                elements.forEach((el) => {
                    const item = {
                        tag: el.tagName.toLowerCase(),
                        id: el.id || null,
                        name: el.name || null,
                        type: el.type || null,
                        value: el.value || null,
                        text: (el.textContent || '').slice(0, 100).trim(),
                        disabled: el.disabled || false,
                    };
                    
                    // Add aria-label if present
                    if (el.getAttribute('aria-label')) {
                        item.ariaLabel = el.getAttribute('aria-label');
                    }
                    
                    // Only include if it has some identifier
                    if (item.id || item.name || item.text) {
                        result.push(item);
                    }
                });
                
                return { elements: result, count: result.length };
            }
        );
        
        // Set input value - mutating
        window.DashMCP.registerTool(
            'ui.setValue',
            {
                description: 'Set the value of an input element by ID. Triggers input and change events.',
                inputSchema: {
                    type: 'object',
                    properties: {
                        id: {
                            type: 'string',
                            description: 'Element ID',
                        },
                        value: {
                            type: 'string',
                            description: 'Value to set',
                        },
                    },
                    required: ['id', 'value'],
                    additionalProperties: false,
                },
                annotations: { readOnly: false },
            },
            async ({ id, value }) => {
                const el = document.getElementById(id);
                if (!el) {
                    throw new Error(`Element not found: #${id}`);
                }
                
                // Set value
                el.value = value;
                
                // Dispatch events to trigger Dash callbacks
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
                
                return { ok: true, id, value };
            }
        );
        
        // Click element - mutating
        window.DashMCP.registerTool(
            'ui.click',
            {
                description: 'Click an element by ID.',
                inputSchema: {
                    type: 'object',
                    properties: {
                        id: {
                            type: 'string',
                            description: 'Element ID to click',
                        },
                    },
                    required: ['id'],
                    additionalProperties: false,
                },
                annotations: { readOnly: false },
            },
            async ({ id }) => {
                const el = document.getElementById(id);
                if (!el) {
                    throw new Error(`Element not found: #${id}`);
                }
                
                el.click();
                return { ok: true, id };
            }
        );
        
        // Select dropdown option - mutating
        window.DashMCP.registerTool(
            'ui.select',
            {
                description: 'Select an option in a dropdown/select element by ID.',
                inputSchema: {
                    type: 'object',
                    properties: {
                        id: {
                            type: 'string',
                            description: 'Select element ID',
                        },
                        value: {
                            type: 'string',
                            description: 'Option value to select',
                        },
                    },
                    required: ['id', 'value'],
                    additionalProperties: false,
                },
                annotations: { readOnly: false },
            },
            async ({ id, value }) => {
                const el = document.getElementById(id);
                if (!el) {
                    throw new Error(`Element not found: #${id}`);
                }
                
                // For Dash dropdowns, need to handle React state
                // Try native first
                el.value = value;
                el.dispatchEvent(new Event('change', { bubbles: true }));
                
                return { ok: true, id, value };
            }
        );
        
        // Wait for element - read-only
        window.DashMCP.registerTool(
            'ui.waitFor',
            {
                description: 'Wait for an element to appear on the page.',
                inputSchema: {
                    type: 'object',
                    properties: {
                        selector: {
                            type: 'string',
                            description: 'CSS selector to wait for',
                        },
                        timeout: {
                            type: 'number',
                            description: 'Maximum wait time in ms (default: 5000)',
                            default: 5000,
                        },
                    },
                    required: ['selector'],
                },
                annotations: { readOnly: true },
            },
            async ({ selector, timeout = 5000 }) => {
                const start = Date.now();
                
                while (Date.now() - start < timeout) {
                    const el = document.querySelector(selector);
                    if (el) {
                        return { 
                            found: true, 
                            selector,
                            waitedMs: Date.now() - start,
                        };
                    }
                    await new Promise(r => setTimeout(r, 100));
                }
                
                return { 
                    found: false, 
                    selector,
                    waitedMs: timeout,
                    error: `Element not found after ${timeout}ms`,
                };
            }
        );
        
        // Scroll to element - mutating
        window.DashMCP.registerTool(
            'ui.scrollTo',
            {
                description: 'Scroll to bring an element into view.',
                inputSchema: {
                    type: 'object',
                    properties: {
                        id: {
                            type: 'string',
                            description: 'Element ID to scroll to',
                        },
                        behavior: {
                            type: 'string',
                            enum: ['smooth', 'instant'],
                            default: 'smooth',
                        },
                    },
                    required: ['id'],
                },
                annotations: { readOnly: false },
            },
            async ({ id, behavior = 'smooth' }) => {
                const el = document.getElementById(id);
                if (!el) {
                    throw new Error(`Element not found: #${id}`);
                }
                
                el.scrollIntoView({ behavior, block: 'center' });
                return { ok: true, id };
            }
        );
        
        // Get element text - read-only
        window.DashMCP.registerTool(
            'ui.getText',
            {
                description: 'Get the text content of an element.',
                inputSchema: {
                    type: 'object',
                    properties: {
                        selector: {
                            type: 'string',
                            description: 'CSS selector for the element',
                        },
                    },
                    required: ['selector'],
                },
                annotations: { readOnly: true },
            },
            async ({ selector }) => {
                const el = document.querySelector(selector);
                if (!el) {
                    throw new Error(`Element not found: ${selector}`);
                }
                
                return { 
                    text: el.textContent?.trim() || '',
                    innerHTML: el.innerHTML?.slice(0, 5000) || '',
                };
            }
        );
        
        // Navigate - mutating
        window.DashMCP.registerTool(
            'page.navigate',
            {
                description: 'Navigate to a different page within the dashboard.',
                inputSchema: {
                    type: 'object',
                    properties: {
                        path: {
                            type: 'string',
                            description: 'Path to navigate to (e.g., "/view/my_dashboard")',
                        },
                    },
                    required: ['path'],
                },
                annotations: { readOnly: false },
            },
            async ({ path }) => {
                // Use Dash's client-side navigation if possible
                window.location.href = path;
                return { ok: true, path };
            }
        );
    }

    // ==========================================================================
    // INITIALIZATION
    // ==========================================================================
    
    /**
     * Initialize MCP bridge.
     */
    function init() {
        log('Initializing MCP Bridge, SID:', SID);
        
        // Register default tools
        registerDefaultTools();
        
        // Connect to WebSocket
        connect();
        
        // Listen for page navigation (for SPAs)
        window.addEventListener('popstate', sendPageUpdate);
        
        // Log connection info to console
        console.log(
            '%c[MCP Bridge]%c Connected. SID: %c' + SID + '%c\n' +
            'Tools namespaced as: dash.' + SID + '.<tool>\n' +
            'Use window.DashMCP.registerTool() to add custom tools.',
            'background: #3b82f6; color: white; padding: 2px 6px; border-radius: 3px;',
            'color: #6b7280;',
            'color: #3b82f6; font-weight: bold;',
            'color: #6b7280;'
        );
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();

