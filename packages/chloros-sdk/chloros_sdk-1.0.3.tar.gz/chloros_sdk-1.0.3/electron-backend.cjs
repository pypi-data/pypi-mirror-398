const fs = require('fs').promises;
const path = require('path');
const os = require('os');
const { dialog, BrowserWindow } = require('electron');
const https = require('https');

class ChlorosBackend {
  constructor() {
    // Default project directory
    this.defaultProjectPath = path.join(os.homedir(), 'Chloros Projects');
    this.currentProject = null;
    this.mainWindow = null; // Will be set by setMainWindow()
    
    // Directory memory for file/folder dialogs
    this.lastFileDirectory = null;
    this.lastFolderDirectory = null;
    
    // Track backend readiness to suppress startup errors
    this.backendReady = false;
    this.startupTime = Date.now();
    this.STARTUP_GRACE_PERIOD = 30000; // 30 seconds
    
    // Debug mode - enable verbose logging only in development
    // Set CHLOROS_DEBUG=1 environment variable to enable debug logs
    this.debugMode = process.env.CHLOROS_DEBUG === '1' || process.argv.includes('--debug');
    
    this.initializeSettings();
    this.loadDirectoryMemory();
    this.setupSSEConnection();
    this.setupIPCHandlers();
  }
  
  // Set the main window reference (must be called after window is created)
  setMainWindow(window) {
    this.mainWindow = window;
  }
  
  // Helper method to check if we should suppress startup errors
  isInStartupGracePeriod() {
    if (this.backendReady) return false;
    const timeSinceStartup = Date.now() - this.startupTime;
    return timeSinceStartup < this.STARTUP_GRACE_PERIOD;
  }
  
  // Helper method to send progress events to UI
  sendProgressEvent(eventType, data) {
    // Send progress event to all renderer windows
    const windows = BrowserWindow.getAllWindows();
    windows.forEach(window => {
      // Safety check: Only send if window and webContents are valid
      try {
        if (window && !window.isDestroyed() && window.webContents && !window.webContents.isDestroyed()) {
          window.webContents.send('progress-event', { type: eventType, data });
        }
      } catch (error) {
        // // console.warn(`[BACKEND] ⚠️ Could not send progress event: ${error.message}`);
      }
    });
  }

  // Set up SSE connection to Flask backend for real-time events
  setupSSEConnection() {
    try {
      
      // Use fetch with streaming for SSE connection
      const fetch = require('node-fetch');
      let connectionAttempts = 0;
      const INITIAL_QUIET_ATTEMPTS = 30; // Suppress errors for first 30 attempts (~30 seconds) during startup
      
      const connectSSE = async () => {
        try {
          connectionAttempts++;
          const response = await fetch('http://localhost:5000/api/events', {
            headers: {
              'Accept': 'text/event-stream',
              'Cache-Control': 'no-cache'
            }
          });
          
          if (!response.ok) {
            throw new Error(`SSE connection failed: ${response.status}`);
          }
          
          // SSE connection established (silently)
          connectionAttempts = 0; // Reset counter on successful connection
          this.backendReady = true; // Mark backend as ready
          
          // Process the streaming response
          const reader = response.body;
          let buffer = '';
          
          reader.on('data', (chunk) => {
            buffer += chunk.toString();
            
            // Process complete messages
            const lines = buffer.split('\n');
            buffer = lines.pop(); // Keep incomplete line in buffer
            
            for (const line of lines) {
              if (line.startsWith('data: ')) {
                try {
                  const data = JSON.parse(line.slice(6));
                  this.handleSSEEvent(data);
                } catch (e) {
                  console.error('[BACKEND] SSE parse error:', e);
                }
              }
            }
          });
          
          reader.on('end', () => {
            // // console.log('[BACKEND] SSE connection ended, reconnecting...');
            setTimeout(connectSSE, 2000);
          });
          
          reader.on('error', (error) => {
            // Only log errors after initial startup period
            if (connectionAttempts > INITIAL_QUIET_ATTEMPTS) {
              console.error('[BACKEND] SSE connection error:', error);
            }
            setTimeout(connectSSE, 5000);
          });
          
        } catch (error) {
          // Never log ECONNREFUSED errors (expected during startup)
          // Only log unexpected errors after startup period
          if (error.code !== 'ECONNREFUSED' && connectionAttempts > INITIAL_QUIET_ATTEMPTS) {
            console.error('[BACKEND] Failed to establish SSE connection:', error);
          }
          setTimeout(connectSSE, 1000); // Retry faster during startup
        }
      };
      
      connectSSE();
      
    } catch (error) {
      console.error('[BACKEND] SSE setup failed:', error);
    }
  }

  // Handle SSE events from Flask backend
  handleSSEEvent(data) {
    // Don't log routine events (too noisy) - only log critical/error events
    
    if (data.type === 'import-progress') {
      // Handle nested data structure from Flask SSE events
      const eventData = data.data || data;
      // Import progress (silently forward to UI)
      
      // Forward the import-progress event to the frontend
      this.sendProgressEvent('import-progress', {
        progress: eventData.progress,
        status: eventData.status,
        source: eventData.source || 'sse'
      });
    } else if (data.type === 'ray-import-completed') {
      // Ray import completed (silently forward to UI)
      
      // Send immediate force refresh with the updated files
      this.sendProgressEvent('force-refresh-images', {
        images: data.files || [],
        timestamp: Date.now()
      });
    } else if (data.type === 'processing-progress') {
      // Handle processing progress updates from backend
      const eventData = data.data || data;
      // Processing progress (silently forward to UI)
      
      // Forward the processing-progress event to the frontend
      this.sendProgressEvent('processing-progress', eventData);
    } else if (data.type === 'target-detected') {
      // Handle target detection events
      const eventData = data.data || data;
      // Target detected (silently forward to UI)
      
      // Forward the target-detected event to the frontend
      this.sendProgressEvent('target-detected', eventData);
    } else if (data.type === 'target-batch-update') {
      // Handle batch target detection events
      const eventData = data.data || data;
      // Forward the target-batch-update event to the frontend
      this.sendProgressEvent('target-batch-update', eventData);
    } else if (data.type === 'reset-ui-state') {
      // Handle UI reset events (for project switching)
      const eventData = data.data || data;
      // Reset UI state (silently forward to UI)
      
      // Forward the reset-ui-state event to the frontend
      this.sendProgressEvent('reset-ui-state', eventData);
    } else if (data.type === 'processing-stopped') {
      // Handle processing stopped events (for button reset)
      const eventData = data.data || data;
      // Processing stopped (silently forward to UI)
      
      // Forward the processing-stopped event to the frontend
      this.sendProgressEvent('processing-stopped', eventData);
    } else if (data.type === 'processing-complete') {
      // Handle processing completion - show completion message
      // // console.log('[BACKEND] Finished processing project:', this.currentProject?.name);
      
      // Forward the processing-complete event to the frontend
      this.sendProgressEvent('processing-complete', data.data || data);
    } else if (data.type === 'login-restored') {
      // Handle login restored event (from session restoration) - silently acknowledge
    } else if (data.type === 'heartbeat') {
      // Silently ignore heartbeat events - they're just keep-alives
    } else if (data.type === 'connected') {
      // Silently ignore connected events - just initial handshake
    } else if (data.type === 'files-changed') {
      // Handle files changed event - silently forward to UI
      this.sendProgressEvent('files-changed', data.data || data);
    } else if (data.type === 'refresh-components') {
      // Handle refresh components event - silently forward to UI
      this.sendProgressEvent('refresh-components', data.data || data);
    } else if (data.type === 'direct-images-updated') {
      // Handle direct images updated event - silently forward to UI
      this.sendProgressEvent('direct-images-updated', data.data || data);
    } else {
      // Only log unknown event types in debug mode
      if (this.debugMode) {
        // // console.log('[BACKEND] ⚠️ Unknown SSE event type:', data.type);
      }
    }
  }
  
  // Helper method to create delays
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
    }

  // Setup all IPC handlers for backend API calls
  setupIPCHandlers() {
    const { ipcMain } = require('electron');
    const fetch = require('node-fetch');

    // Helper function to make API calls to Flask backend
    const callFlaskAPI = async (endpoint, method = 'GET', body = null) => {
      try {
        const options = {
          method,
          headers: { 'Content-Type': 'application/json' }
        };
        if (body) options.body = JSON.stringify(body);
        
        const response = await fetch(`http://localhost:5000${endpoint}`, options);
        return await response.json();
      } catch (error) {
        // During startup grace period, return null instead of throwing
        if (this.isInStartupGracePeriod()) {
          return null; // Silent fail during startup
        }
        // After startup, log and throw the error
        console.error(`[BACKEND] API call failed for ${endpoint}:`, error);
        throw error;
      }
    };

    // Register all IPC handlers
    ipcMain.handle('backend-get-image-list', async () => {
      return await callFlaskAPI('/api/get-image-list');
    });

    ipcMain.handle('backend-get-processing-mode', async () => {
      return await callFlaskAPI('/api/get-processing-mode');
    });

    ipcMain.handle('backend-get-viewer-index-value', async (event, imageX, imageY) => {
      return await callFlaskAPI(`/api/get-viewer-index-value?imageX=${imageX}&imageY=${imageY}`);
    });

    ipcMain.handle('backend-get-image-layers', async (event, imageName) => {
      return await callFlaskAPI(`/api/get-image-layers?image=${encodeURIComponent(imageName)}`);
    });

    ipcMain.handle('backend-get-calibration-target-polys', async (event, imageName) => {
      return await callFlaskAPI(`/api/get-calibration-target-polys?image=${encodeURIComponent(imageName)}`);
    });

    ipcMain.handle('backend-create-sandbox-image', async (event, selectedImage, selectedOption, currentIndexConfig, selectedLayer) => {
      return await callFlaskAPI('/api/create-sandbox-image', 'POST', {
        image: selectedImage,
        index_type: selectedOption,
        index_config: currentIndexConfig,
        selected_layer: selectedLayer
      });
    });

    ipcMain.handle('backend-get-viewer-index-min-max', async () => {
      return await callFlaskAPI('/api/get-viewer-index-min-max');
    });

    ipcMain.handle('backend-get-viewer-lut-gradient', async (event, index) => {
      return await callFlaskAPI(`/api/get-viewer-lut-gradient?index=${encodeURIComponent(index)}`);
    });

    ipcMain.handle('backend-get-exposure-pin-info', async () => {
      return await callFlaskAPI('/api/get-exposure-pin-info');
    });

    ipcMain.handle('backend-get-minimum-window-size', async () => {
      return await callFlaskAPI('/api/get-minimum-window-size');
    });

    ipcMain.handle('backend-get-camera-models', async () => {
      return await callFlaskAPI('/api/get-camera-models');
    });

    // User login handler - routes to Flask backend with device validation
    ipcMain.handle('remote-user-login', async (event, email, password) => {
      // Handle remote user login (silently)
      return await this.remoteUserLogin(email, password);
    });

    // User logout handler - calls Flask backend
    ipcMain.handle('user-logout', async (event, data) => {
      // Handle user logout with comprehensive credential clearing
      try {
        const { email } = data || {};
        
        // Call backend logout with email for proper cache clearing
        const response = await callFlaskAPI('/api/logout', 'POST', { email });
        
        // CRITICAL SECURITY: Clear Electron session storage and auth cache
        try {
          const { session } = require('electron');
          const defaultSession = session.defaultSession;
          
          // Clear auth cache to remove stale credentials
          await defaultSession.clearAuthCache().catch(() => {});
          
          // Clear storage data (cookies, localStorage, sessionStorage, etc.)
          await defaultSession.clearStorageData({
            storages: ['cookies', 'localstorage', 'sessionstorage'],
            origin: 'http://localhost:5000'
          }).catch(() => {});
          
        } catch (sessionError) {
          console.error('[BACKEND] 🔐 Session clearing error:', sessionError);
        }
        
        return { success: true, ...response };
      } catch (error) {
        console.error('[BACKEND] 🔐 ❌ Logout error:', error);
        return { success: false, error: error.message };
      }
    });

    // Generic API call handler for any backend method
    ipcMain.handle('backend-api-call', async (event, { method, params }) => {
      // // console.log(`[BACKEND] Generic API call: ${method}`, params);
      const endpoint = `/api/${method.replace(/_/g, '-')}`;
      return await callFlaskAPI(endpoint, 'POST', params);
    });
  }

  // Helper method to poll for Ray import completion
  startRayCompletionPolling(initialFileCount) {
    // Starting Ray completion polling (silently)

    const pollInterval = 100; // Check every 100ms for near-instant detection
    const maxPolls = 50; // Maximum 5 seconds
    let pollCount = 0;
    
    const poll = async () => {
      pollCount++;
      // Ray completion poll (silently)
      
      try {
        const response = await fetch('http://localhost:5000/api/get-image-list');
        const responseData = await response.json();
        // Ray poll response (silently)
        
        // Extract images array from response
        const currentFiles = responseData.images || responseData || [];
        const currentFileCount = Array.isArray(currentFiles) ? currentFiles.length : 0;
        
        // Check file count (silently)
        
        // If file count increased (any increase means Ray completed)
        if (currentFileCount > initialFileCount) {
          // Ray import completed (silently)
          
          // Send force refresh with updated files
          this.sendProgressEvent('force-refresh-images', {
            images: currentFiles,
            timestamp: Date.now()
          });
          
          return; // Stop polling
        }
        
        // Continue polling if not completed and within limits
        if (pollCount < maxPolls) {
          setTimeout(poll, pollInterval);
        } else {
          // Ray completion polling timed out (silently)
        }
        
      } catch (error) {
        console.error('[BACKEND] Error during Ray completion polling:', error);
        if (pollCount < maxPolls) {
          setTimeout(poll, pollInterval);
        }
      }
    };
    
    // Start polling immediately
    poll();
  }

  // AGGRESSIVE Ray polling for instant detection
  startAggressiveRayPolling() {
    // Starting aggressive Ray polling (silently)

    let pollCount = 0;
    const maxPolls = 100; // 10 seconds max
    let lastFileCount = 1; // Start with 1 (DAQ file)
    
    const poll = async () => {
      pollCount++;
      
      try {
        const response = await fetch('http://localhost:5000/api/get-image-list');
        const responseData = await response.json();
        
        // Extract images array from response
        const currentFiles = responseData.images || responseData || [];
        const currentFileCount = Array.isArray(currentFiles) ? currentFiles.length : 0;
        
        // Log every 10th poll to avoid spam (silently)
        
        // If file count increased significantly (Ray completed)
        if (currentFileCount > lastFileCount + 5) {
          // Ray completed (silently)
          
          // Send immediate force refresh with all files
          this.sendProgressEvent('force-refresh-images', {
            images: currentFiles,
            timestamp: Date.now()
          });
          
          return; // Stop polling
        }
        
        lastFileCount = currentFileCount;
      } catch (error) {
        console.error('[BACKEND] Aggressive polling error:', error);
      }
      
      if (pollCount < maxPolls) {
        setTimeout(poll, 50); // Poll every 50ms for maximum responsiveness
      } else {
        // // console.warn('[BACKEND] Aggressive Ray polling timed out.');
      }
    };
    
    // Start immediately
    poll();
  }
  
  initializeSettings() {
    // Try to load saved working directory from config file (same file Flask uses)
    const fs = require('fs');
    const configDir = path.join(os.homedir(), '.chloros');
    const configFile = path.join(configDir, 'working_directory.txt');
    
    let savedWorkingDir = null;
    if (fs.existsSync(configFile)) {
      try {
        savedWorkingDir = fs.readFileSync(configFile, 'utf8').trim();
        if (!savedWorkingDir || !fs.existsSync(savedWorkingDir)) {
          savedWorkingDir = null;
        }
      } catch (error) {
        // Silently use default
      }
    }
    
    this.settings = {
      'Working Directory': savedWorkingDir || this.defaultProjectPath,
      'Processing Mode': 'serial',
      'Camera Model': 'None'
    };

    // Ensure project directory exists
    this.ensureProjectDirectory();
  }

  async ensureProjectDirectory() {
    try {
      const workingDirectory = this.settings['Working Directory'] || this.defaultProjectPath;
      await fs.access(workingDirectory);
    } catch (error) {
      const workingDirectory = this.settings['Working Directory'] || this.defaultProjectPath;
      // // console.log('[BACKEND] Creating project directory:', workingDirectory);
      await fs.mkdir(workingDirectory, { recursive: true });
    }
  }

  // Project Management
  async newProject(projectName, template = null) {
    try {
      // Call Python backend to create the project (handles templates properly)
      const response = await fetch('http://localhost:5000/api/new-project', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: projectName,
          template: template  // Pass template to Python backend
        })
      });
      
      const data = await response.json();
      
      if (!data.success) {
        return { success: false, error: data.error || 'Failed to create project' };
      }
      
      // Update local state
      const workingDirectory = this.settings['Working Directory'] || this.defaultProjectPath;
      const projectPath = path.join(workingDirectory, projectName);
      
      this.currentProject = {
        name: projectName,
        path: projectPath
      };
      
      return { 
        success: true, 
        message: `Project "${projectName}" created successfully`
      };
      
    } catch (error) {
      console.error('[BACKEND] Error creating project:', error);
      return { success: false, error: error.message };
    }
  }

  async getProjects() {
    try {
      // Ensure project folder exists
      await this.ensureProjectDirectory();

      // Use the working directory setting
      const workingDirectory = this.settings['Working Directory'] || this.defaultProjectPath;
      const items = await fs.readdir(workingDirectory);
      const projects = [];

      for (const item of items) {
        const itemPath = path.join(workingDirectory, item);
        const stat = await fs.stat(itemPath);
        
        // Match original: directory with project.json
        if (stat.isDirectory()) {
          try {
            const configPath = path.join(itemPath, 'project.json');
            await fs.access(configPath);
            projects.push(item);  // Return just the basename like original
          } catch (error) {
            // Not a valid project directory
          }
        }
      }
      
      // Found projects (silently)
      return projects;
      
    } catch (error) {
      console.error('[BACKEND] Error getting projects:', error);
      return [];
    }
  }

  async openProject(projectName) {
    try {
      // Use the working directory setting
      const workingDirectory = this.settings['Working Directory'] || this.defaultProjectPath;
      const projectPath = path.join(workingDirectory, projectName);
      const configPath = path.join(projectPath, 'project.json');
      
      // Check if project exists
      await fs.access(projectPath);
      const configData = await fs.readFile(configPath, 'utf8');
      const projectConfig = JSON.parse(configData);
      
      this.currentProject = {
        name: projectName,
        path: projectPath,
        config: projectConfig
      };
      
      // Notify Python backend about the opened project
      try {
        const response = await fetch('http://localhost:5000/api/load-project', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            project_path: projectPath
          })
        });
        
        const data = await response.json();
        
        if (!data.success) {
          console.warn('[BACKEND] Failed to load project in Python backend:', data.error);
        }
        
      } catch (error) {
        console.error('[BACKEND] Error notifying Python backend about opened project:', error);
      }
      
      // CRITICAL: Wait for file list to be ready before dispatching events
      // Add a small delay to ensure Python backend has fully loaded the project
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Get file list to check if project has files
      let hasFiles = false;
      try {
        const fileList = await this.getImageList();
        hasFiles = fileList && fileList.length > 0;
      } catch (error) {
        console.error('[BACKEND] Error getting file list after project open:', error);
      }
      
      // Helper function to get a valid window for JavaScript injection
      const getTargetWindow = () => {
        // Try mainWindow first
        if (this.mainWindow && !this.mainWindow.isDestroyed() && this.mainWindow.webContents && !this.mainWindow.webContents.isDestroyed()) {
          return this.mainWindow;
        }
        // Fallback to first available window
        const windows = BrowserWindow.getAllWindows();
        return windows.find(w => !w.isDestroyed() && w.webContents && !w.webContents.isDestroyed());
      };
      
      // Dispatch project-changed event to the frontend UI
      try {
        const targetWindow = getTargetWindow();
        if (targetWindow) {
          targetWindow.webContents.executeJavaScript(`
            const event = new CustomEvent('project-changed', {
              detail: { projectName: '${projectName}' },
              bubbles: true,
              composed: true
            });
            document.dispatchEvent(event);
          `);
        }
      } catch (error) {
        console.error('[BACKEND] Error dispatching project-changed event:', error);
      }
      
      // CRITICAL FIX: Dispatch files-changed event to enable process button if files exist
      if (hasFiles) {
        // Helper function to dispatch events with retries
        const dispatchFilesChangedEvent = async (retries = 3) => {
          for (let attempt = 1; attempt <= retries; attempt++) {
            try {
              const targetWindow = getTargetWindow();
              if (!targetWindow) {
                if (attempt < retries) {
                  await new Promise(resolve => setTimeout(resolve, 500));
                  continue;
                }
                return false;
              }
              
              // Wait for DOM to be ready before injecting
              await targetWindow.webContents.executeJavaScript(`
                (async function() {
                  // Wait for DOM if not ready
                  if (document.readyState !== 'complete') {
                    await new Promise(resolve => {
                      if (document.readyState === 'complete') {
                        resolve();
                      } else {
                        window.addEventListener('load', resolve, { once: true });
                      }
                    });
                  }
                  
                  // Dispatch to both document and window
                  const event = new CustomEvent('files-changed', {
                    detail: { hasFiles: true },
                    bubbles: true,
                    composed: true
                  });
                  document.dispatchEvent(event);
                  window.dispatchEvent(event);
                  
                  // FAILSAFE: Directly update process button
                  const processButton = document.querySelector('process-control-button');
                  if (processButton) {
                    processButton.hasFiles = true;
                    processButton.requestUpdate();
                  }
                })();
              `);
              
              return true;
              
            } catch (error) {
              if (attempt < retries) {
                await new Promise(resolve => setTimeout(resolve, 500));
              }
            }
          }
          return false;
        };
        
        // Execute with retries
        await dispatchFilesChangedEvent(3);
      }
      
      // Legacy CRITICAL FIX: Dispatch files-changed event to enable process button if files exist
      try {
        // Check if project has any image files
        const hasFiles = projectConfig.files && Object.keys(projectConfig.files).length > 0;
        // Check complete (silently)
        
        if (hasFiles && this.mainWindow && this.mainWindow.webContents) {
          this.mainWindow.webContents.executeJavaScript(`
            const filesEvent = new CustomEvent('files-changed', {
              detail: { hasFiles: true },
              bubbles: true,
              composed: true
            });
            document.dispatchEvent(filesEvent);
          `);
        }
      } catch (error) {
        console.error('[BACKEND] Error dispatching files-changed event:', error);
      }
      
      return { 
        success: true, 
        message: `Project "${projectName}" opened successfully`,
        projectPath: projectPath
      };
      
    } catch (error) {
      console.error('[BACKEND] Error opening project:', error);
      return { success: false, error: 'Project not found or corrupted' };
    }
  }

  // Settings Management
  async getConfig() {
    try {
      const response = await fetch('http://localhost:5000/api/get-config');
      const data = await response.json();
      
      if (data.success && data.config) {
        // Parse the stringified config (backend returns JSON string, not object)
        const parsedConfig = typeof data.config === 'string' ? JSON.parse(data.config) : data.config;
        return parsedConfig;
      } else {
        // Silently return null if no project is loaded
        return null;
      }
    } catch (error) {
      // Only log errors if backend should be ready
      if (!this.isInStartupGracePeriod()) {
        console.error('[ELECTRON BACKEND] ❌ Error getting config:', error);
      }
      return null;
    }
  }

  async setConfig(key, value) {
    try {
      const response = await fetch('http://localhost:5000/api/set-config', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          path: key,
          value: value
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        // Config updated (silently)
        return { success: true };
      } else {
        console.error(`[ELECTRON BACKEND] ❌ Failed to update config: ${data.error}`);
        return { success: false, error: data.error };
      }
    } catch (error) {
      // Only log errors if backend should be ready
      if (!this.isInStartupGracePeriod()) {
        console.error('[ELECTRON BACKEND] ❌ Error setting config:', error);
      }
      return { success: false, error: error.message };
    }
  }

  async getWorkingDirectory() {
    // Try to fetch from backend for fresh value, but handle startup gracefully
    try {
      const response = await fetch('http://localhost:5000/api/get-working-directory');
      const data = await response.json();
      
      if (data.success && data.path) {
        // Update cache with fresh value
        this.settings['Working Directory'] = data.path;
        return data.path;
      }
    } catch (error) {
      // During startup, Flask might not be ready yet - silently use cache
      if (!this.isInStartupGracePeriod()) {
        console.error('[ELECTRON-BACKEND] Error getting working directory:', error);
      }
    }
    
    // Fallback to cached or default (normal during startup)
    return this.settings['Working Directory'] || this.defaultProjectPath;
  }

  async moveProjectToNewDirectory(newPath) {
    try {
      const response = await fetch('http://localhost:5000/api/move-project', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: newPath })
      });

      if (!response.ok) {
        return { success: false, error: `HTTP error! status: ${response.status}` };
      }

      const result = await response.json();

      // Update local settings cache with new working directory if successful
      if (result.success && result.working_directory) {
        this.settings['Working Directory'] = result.working_directory;
      }

      return result;
    } catch (error) {
      console.error('[ELECTRON-BACKEND] Move project error:', error);
      return { success: false, error: error.message };
    }
  }

  async selectWorkingDirectory() {
    try {
      const { dialog, BrowserWindow } = require('electron');
      
      // Get the focused window to make dialog modal
      const focusedWindow = BrowserWindow.getFocusedWindow();
      
      // Show folder selection dialog with correct title
      const result = await dialog.showOpenDialog(focusedWindow, {
        properties: ['openDirectory'],
        title: 'Select Working Directory',
        defaultPath: this.defaultProjectPath,
        buttonLabel: 'Select Folder'
      });
      
      if (result.canceled || !result.filePaths || result.filePaths.length === 0) {
        // // console.log('[BACKEND] Working directory selection cancelled');
        return null;
      }
      
      const selectedPath = result.filePaths[0];
      // // console.log('[BACKEND] Selected working directory:', selectedPath);
      
      // Update the working directory in the backend
      try {
        const response = await fetch('http://localhost:5000/api/set-working-directory', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ path: selectedPath })
        });
        const data = await response.json();
        // // console.log('[BACKEND] Set working directory result:', data);
      } catch (apiError) {
        console.error('[BACKEND] Error setting working directory via API:', apiError);
      }
      
      return selectedPath;
    } catch (error) {
      console.error('[BACKEND] Error selecting working directory:', error);
      return null;
    }
  }

  async openProjectsFolder() {
    try {
      const { shell } = require('electron');
      // Use the working directory setting
      const projectsFolder = this.settings['Working Directory'] || this.defaultProjectPath;

      // Create the folder if it doesn't exist
      await fs.mkdir(projectsFolder, { recursive: true });
      
      // Open the folder in the system file explorer
      await shell.openPath(projectsFolder);
      
      if (this.debugMode) {
        // // console.log('[BACKEND] Opened projects folder:', projectsFolder);
      }
      return { success: true };
    } catch (error) {
      console.error('[BACKEND] Error opening projects folder:', error);
      return { success: false, error: error.message };
    }
  }

  // File Operations
  async getImageList() {
    if (!this.currentProject) {
      return [];
    }
    
    try {
      // Don't look for files in local images directory - get them from Python backend
      const response = await fetch('http://localhost:5000/api/get-image-list');
      if (response.ok) {
        const data = await response.json();
        
        // Handle both old and new response formats
        const images = data.images || data.files || [];
        if (this.debugMode) {
          // // console.log('[BACKEND] Got images from Python backend:', images.length);
        }
        return images;
      } else {
        console.error('[BACKEND] Failed to get image list from Python backend:', response.status);
        return [];
      }
      
    } catch (error) {
      console.error('[BACKEND] Error getting image list from Python backend:', error);
      return [];
    }
  }

  // Checkbox sync method
  async syncCheckboxState(filename, calibState) {
    // // // console.log(`[BACKEND] Syncing checkbox state for ${filename}: ${calibState}`);
    
    try {
      // Call the Python backend sync_checkbox_state method
      const response = await fetch('http://localhost:5000/api/sync-checkbox-state', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          filename: filename,
          calib_state: calibState
        })
      });

      const data = await response.json();
      if (this.debugMode) {
        // // console.log('[BACKEND] Checkbox sync response:', data);
      }
      
      return data;
    } catch (error) {
      console.error('[BACKEND] Error syncing checkbox state:', error);
      return { success: false, error: error.message };
    }
  }

  // Processing Operations
  async processProject() {
    // // console.log('[BACKEND] Processing project:', this.currentProject?.name);
    
    try {
      // Call the Python backend to start processing
      const response = await fetch('http://localhost:5000/api/process-project', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({})
      });

      const data = await response.json();
      if (this.debugMode) {
        // // console.log('[BACKEND] Python backend response:', data);
      }
      
      if (data.success) {
        return { success: true, message: 'Processing started successfully' };
      } else {
        return { success: false, error: data.error || 'Processing failed to start' };
      }
    } catch (error) {
      console.error('[BACKEND] Failed to communicate with Python backend:', error);
      return { success: false, error: 'Failed to communicate with Python backend' };
    }
  }

  async interruptProject() {
    // // console.log('[BACKEND] Interrupting project processing');
    
    try {
      // Call the Python backend to interrupt processing
      const response = await fetch('http://localhost:5000/api/interrupt-project', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result = await response.json();
      // // console.log('[BACKEND] ✅ Project processing interrupted successfully');
      return result;
      
    } catch (error) {
      console.error('[BACKEND] ❌ Error interrupting project processing:', error);
      return { success: false, error: error.message };
    }
  }

  async detectExportLayers() {
    if (this.debugMode) {
      // // console.log('[BACKEND] 🔍 Detecting export layers');
    }
    
    try {
      // Call the Python backend to detect export layers
      const response = await fetch('http://localhost:5000/api/detect-export-layers', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      if (this.debugMode) {
        // // console.log('[BACKEND] ✅ Export layers detected:', data);
      }
      return data;
    } catch (error) {
      // Always show errors
      console.error('[BACKEND] ❌ Error detecting export layers:', error);
      return { success: false, error: error.message, layers_found: 0 };
    }
  }

  getProcessingProgress() {
    // Placeholder for progress tracking
    return { percentage: 0, status: 'ready', phase: 'Idle' };
  }

  async getStatus() {
    if (this.debugMode) {
      // // console.log('[BACKEND] 📊 Getting backend status');
    }
    
    try {
      // Call the Python backend status endpoint
      const response = await fetch('http://localhost:5000/api/status', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      if (this.debugMode) {
        // // console.log('[BACKEND] ✅ Status retrieved:', data);
      }
      return data;
    } catch (error) {
      // Always log errors (not debug-only)
      console.error('[BACKEND] ❌ Error getting status:', error);
      return { success: false, error: error.message, isProcessing: false };
    }
  }

  // Processing Mode Management
  async setProcessingMode(mode) {
    try {
      // Call the Python backend to set processing mode
      const response = await fetch('http://localhost:5000/api/set-processing-mode', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ mode: mode })
      });

      const data = await response.json();
      
      if (data.success) {
        return true;
      } else {
        console.error('[BACKEND] ❌ Failed to set processing mode:', data.error);
        return false;
      }
    } catch (error) {
      // Only log errors if backend should be ready
      if (!this.isInStartupGracePeriod()) {
        console.error('[BACKEND] ❌ Failed to communicate with Python backend for set_processing_mode:', error);
      }
      return false;
    }
  }

  async getProcessingMode() {
    try {
      // Call the Python backend to get processing mode
      const response = await fetch('http://localhost:5000/api/get-processing-mode', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      const data = await response.json();
      // Processing mode retrieved (silently)
      
      if (data.success) {
        return data.data || { mode: 'serial', is_licensed: false };
      } else {
        console.error('[BACKEND] ❌ Failed to get processing mode:', data.error);
        return { mode: 'serial', is_licensed: false };
      }
    } catch (error) {
      // Only log errors if backend should be ready
      if (!this.isInStartupGracePeriod()) {
        console.error('[BACKEND] ❌ Failed to communicate with Python backend for get_processing_mode:', error);
      }
      return { mode: 'serial', is_licensed: false };
    }
  }

  // User Management
  async loadUserEmail() {
    try {
      const configPath = path.join(os.homedir(), '.chloros', 'user.json');
      const data = await fs.readFile(configPath, 'utf8');
      const userConfig = JSON.parse(data);
      return userConfig.email || '';
    } catch (error) {
      return '';
    }
  }

  async saveUserEmail(email) {
    try {
      const configDir = path.join(os.homedir(), '.chloros');
      await fs.mkdir(configDir, { recursive: true });
      
      const configPath = path.join(configDir, 'user.json');
      
      // Load existing config to preserve other settings
      let userConfig = {};
      try {
        const existingData = await fs.readFile(configPath, 'utf8');
        userConfig = JSON.parse(existingData);
      } catch (error) {
        // File doesn't exist or is invalid, start with empty config
      }
      
      userConfig.email = email;
      userConfig.saved = new Date().toISOString();
      
      await fs.writeFile(configPath, JSON.stringify(userConfig, null, 2));
      return { success: true };
    } catch (error) {
      console.error('[BACKEND] Error saving user email:', error);
      return { success: false, error: error.message };
    }
  }

  async saveUserLanguage(language) {
    try {
      const configDir = path.join(os.homedir(), '.chloros');
      await fs.mkdir(configDir, { recursive: true });
      
      const configPath = path.join(configDir, 'user.json');
      
      // Load existing config to preserve other settings
      let userConfig = {};
      try {
        const existingData = await fs.readFile(configPath, 'utf8');
        userConfig = JSON.parse(existingData);
      } catch (error) {
        // File doesn't exist or is invalid, start with empty config
      }
      
      userConfig.language = language;
      userConfig.saved = new Date().toISOString();
      
      await fs.writeFile(configPath, JSON.stringify(userConfig, null, 2));
      // // console.log('[BACKEND] Saved user language:', language);
      return { success: true };
    } catch (error) {
      console.error('[BACKEND] Error saving user language:', error);
      return { success: false, error: error.message };
    }
  }

  async loadUserLanguage() {
    try {
      const configPath = path.join(os.homedir(), '.chloros', 'user.json');
      const data = await fs.readFile(configPath, 'utf8');
      const userConfig = JSON.parse(data);
      
      return userConfig.language || null;
    } catch (error) {
      // // console.log('[BACKEND] No saved user language found');
      return null;
    }
  }

  // Directory Memory Management
  async loadDirectoryMemory() {
    try {
      const configPath = path.join(os.homedir(), '.chloros', 'user.json');
      const data = await fs.readFile(configPath, 'utf8');
      const userConfig = JSON.parse(data);
      
      this.lastFileDirectory = userConfig.lastFileDirectory || null;
      this.lastFolderDirectory = userConfig.lastFolderDirectory || null;
    } catch (error) {
      // // console.log('[BACKEND] No existing directory memory found, starting fresh');
    }
  }

  async saveDirectoryMemory() {
    try {
      const configDir = path.join(os.homedir(), '.chloros');
      await fs.mkdir(configDir, { recursive: true });
      
      const configPath = path.join(configDir, 'user.json');
      
      // Load existing config to preserve other settings
      let userConfig = {};
      try {
        const existingData = await fs.readFile(configPath, 'utf8');
        userConfig = JSON.parse(existingData);
      } catch (error) {
        // File doesn't exist or is invalid, start with empty config
      }
      
      userConfig.lastFileDirectory = this.lastFileDirectory;
      userConfig.lastFolderDirectory = this.lastFolderDirectory;
      userConfig.lastUpdated = new Date().toISOString();
      
      await fs.writeFile(configPath, JSON.stringify(userConfig, null, 2));
      // Saved directory memory (silently)
    } catch (error) {
      console.error('[BACKEND] Error saving directory memory:', error);
    }
  }

  // Template Management
  async getProjectTemplates() {
    try {
      const response = await fetch('http://localhost:5000/api/project-templates', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      const templates = await response.json();
      return templates || [];
    } catch (error) {
      console.error('[ELECTRON BACKEND] Error getting project templates:', error);
      return [];
    }
  }

  async saveProjectTemplate(templateName) {
    try {
      const response = await fetch('http://localhost:5000/api/save-project-template', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          templateName: templateName
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        // // console.log(`[ELECTRON BACKEND] ✅ Project template saved: ${templateName}`);
        return { success: true };
      } else {
        console.error(`[ELECTRON BACKEND] ❌ Failed to save template: ${data.error}`);
        return { success: false, error: data.error };
      }
    } catch (error) {
      console.error('[ELECTRON BACKEND] ❌ Error saving project template:', error);
      return { success: false, error: error.message };
    }
  }

  async latexify(formula) {
    try {
      const response = await fetch('http://localhost:5000/api/latexify', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          formula: formula
        })
      });
      
      const data = await response.json();
      
      if (data.latex) {
        return data.latex;
      } else {
        console.error(`[ELECTRON BACKEND] ❌ Failed to latexify: ${data.error}`);
        return null;
      }
    } catch (error) {
      console.error('[ELECTRON BACKEND] ❌ Error latexifying formula:', error);
      return null;
    }
  }

  async getAutothreshold(imageName, indexName) {
    try {
      const response = await fetch('http://localhost:5000/api/get-autothreshold', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          image: imageName,
          index: indexName
        })
      });
      
      const data = await response.json();
      
      if (data.thresholds) {
        return data.thresholds;
      } else if (data.success === false) {
        console.error(`[ELECTRON BACKEND] ❌ Failed to get autothreshold: ${data.error}`);
        return null;
      }
      return data;
    } catch (error) {
      console.error('[ELECTRON BACKEND] ❌ Error getting autothreshold:', error);
      return null;
    }
  }

  // Utility Methods
  hasProjectLoaded() {
    return this.currentProject !== null;
  }

  getProjectStatus() {
    return {
      project_loaded: this.hasProjectLoaded(),
      project_name: this.currentProject?.name || '',
      ray_available: true // Placeholder
    };
  }

  // File operations
  async addFiles(mainWindow) {
    try {
      // Use last file directory if available, otherwise fall back to project or default path
      const defaultPath = this.lastFileDirectory || this.currentProject?.path || this.defaultProjectPath;
      
      const result = await dialog.showOpenDialog(mainWindow, {
        title: 'Select Images',
        defaultPath: defaultPath,
        filters: [
          { name: 'Supported Files', extensions: ['jpg', 'jpeg', 'raw', 'daq', 'csv'] },
          { name: 'All Files', extensions: ['*'] }
        ],
        properties: ['openFile', 'multiSelections']
      });

      if (!result.canceled && result.filePaths.length > 0) {
        // Files selected (silently)
        
        // Remember the directory for next time
        this.lastFileDirectory = path.dirname(result.filePaths[0]);
        // Remembered file directory (silently)
        
        // Save to disk for persistence across app restarts
        await this.saveDirectoryMemory();
        
        // Smart animation logic: consider both file count and processing mode
        // Premium mode: animation for >15 files (fast parallel processing)
        // Serial mode: animation for >5 files (slower sequential processing needs feedback)
        const processingMode = await this.getProcessingMode();
        const isSerialMode = processingMode?.mode === 'serial';
        const animationThreshold = isSerialMode ? 5 : 15;
        
        // Processing mode determined (silently)
        
        // ALL SIMULATION STAGES REMOVED - Flask backend via SSE now handles all progress stages
        // if (result.filePaths.length > animationThreshold) {
        //   const totalFiles = result.filePaths.length;
        //   
        //   // Step 1: Starting - REMOVED
        //   this.sendProgressEvent('import-progress', {
        //     percent: 0,
        //     progress: 'Starting',
        //     status: 'starting'
        //   });
        //   
        //   // Step 2: Analyzing - REMOVED
        //   // Step 3: Processing - REMOVED
        // }

        // Send files to Python backend for processing
        try {
          // Simulate processing each file during the Flask call
          if (result.filePaths.length > animationThreshold) {
            const totalFiles = result.filePaths.length;
            
            // Show processing progress during the actual backend call - REMOVED
            // Flask backend via Ray now handles all processing progress events
            // const processingInterval = setInterval(() => {
            //   const currentProgress = Math.min(35 + Math.random() * 40, 75);
            //   const currentFile = Math.floor((currentProgress - 35) / 40 * totalFiles);
            //   if (currentFile > 0) {
            //     this.sendProgressEvent('import-progress', {
            //       percent: currentProgress,
            //       progress: `Processing ${currentFile} / ${totalFiles}`,
            //       status: 'Processing'
            //     });
            //   }
            // }, 200);
            
            const response = await fetch('http://localhost:5000/api/add-files', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                file_paths: result.filePaths
              })
            });
            
            // clearInterval(processingInterval); // REMOVED - no longer using simulated progress
            const data = await response.json();
            
            if (data.success) {
              // Files processed successfully (silently)
              
              // Only show pairing/completion animation based on processing mode
              if (result.filePaths.length > animationThreshold) {
                // Step 4: Pairing - REMOVED - Flask backend handles pairing and transitions to "Generating"
                // const processedFiles = data.files?.length || 0;
                // this.sendProgressEvent('import-progress', {
                //   percent: 80,
                //   progress: 'Pairing',
                //   status: 'Processing'
                // });
                
                // Simulate pairing progress - REMOVED
                // for (let i = 1; i <= processedFiles; i++) {
                //   if (i % Math.max(1, Math.floor(processedFiles / 5)) === 0 || i === processedFiles) {
                //     this.sendProgressEvent('import-progress', {
                //       percent: 80 + (i / processedFiles) * 15,
                //       progress: `Pairing ${i} / ${processedFiles}`,
                //       status: 'Processing'
                //     });
                //     if (processedFiles > 10) await this.delay(30);
                //   }
                // }
                
                // Step 5: Complete - REMOVED - Flask backend handles completion with "Generating" flow
                // this.sendProgressEvent('import-progress', {
                //   percent: 100,
                //   progress: 'Complete',
                //   status: 'completed'
                // });
                
                // SPEED FIX: Immediate UI refresh to show thumbnails
                this.sendProgressEvent('images-updated', {
                  message: 'Images updated after import',
                  timestamp: Date.now()
                });
                
                // INSTANT UI: Send immediate refresh with current files
                this.sendProgressEvent('force-refresh-images', {
                  images: data.files || [],
                  timestamp: Date.now(),
                  instant: true
                });
                
                // RAY IMPORT FIX: For large batches, start IMMEDIATE aggressive polling
                if (result.filePaths.length > 10) {
                  // Large batch - starting Ray polling (silently)
                  // Start polling immediately with very short intervals
                  this.startAggressiveRayPolling();
                }
              }
              
              return data.files || [];
            } else {
              console.error('[BACKEND] Python backend error:', data.error);
              return [];
            }
          } else {
            // For small batches, just do the Flask call without progress
            const response = await fetch('http://localhost:5000/api/add-files', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                file_paths: result.filePaths
              })
            });

            const data = await response.json();
            
            // SPEED FIX: Immediate UI refresh for small batches too
            if (data.success) {
              this.sendProgressEvent('images-updated', {
                message: 'Images updated after import (small batch)',
                timestamp: Date.now()
              });
              
              // INSTANT UI: Get current file list for immediate table population (silently)
              try {
                const fileListResponse = await fetch('http://localhost:5000/api/get-image-list');
                const currentFiles = await fileListResponse.json();
                const currentImages = currentFiles.images || currentFiles || [];
                
                // Send immediate force refresh to populate table instantly
                this.sendProgressEvent('force-refresh-images', {
                  images: currentImages,
                  timestamp: Date.now(),
                  instant: true  // Flag to indicate this is the instant refresh
                });
              } catch (error) {
                console.error('[BACKEND] 🚀 INSTANT UI (small batch): Failed to get immediate file list:', error);
                // Fallback to original data
                this.sendProgressEvent('force-refresh-images', {
                  images: data.files || [],
                  timestamp: Date.now()
                });
              }
            }
            
            return data.success ? data.files || [] : [];
          }
        } catch (apiError) {
          console.error('[BACKEND] Failed to communicate with Python backend:', apiError);
          return [];
        }
      }
      
      return [];
    } catch (error) {
      console.error('[BACKEND] Error in addFiles:', error);
      return [];
    }
  }

  async removeFiles(filenames) {
    try {
      // // console.log('[BACKEND] Removing files:', filenames);
      
      // Send filenames to Python backend for removal
      const response = await fetch('http://localhost:5000/api/remove-files', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          filenames: filenames
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      // // console.log('[BACKEND] Flask response for file removal:', result);
      
      if (result.success) {
        // // console.log('[BACKEND] Successfully removed', result.removed_files?.length || 0, 'files');
        if (result.errors && result.errors.length > 0) {
          // // console.warn('[BACKEND] Removal had errors:', result.errors);
        }
        return { 
          success: true, 
          message: result.message,
          removed_files: result.removed_files,
          errors: result.errors
        };
      } else {
        console.error('[BACKEND] Flask backend returned error:', result.error);
        return { success: false, error: result.error };
      }
    } catch (fetchError) {
      console.error('[BACKEND] Error calling Flask backend for file removal:', fetchError);
      return { success: false, error: fetchError.message };
    }
  }

  async addFolder(mainWindow) {
    try {
      // Use last folder directory if available, otherwise fall back to project or default path
      const defaultPath = this.lastFolderDirectory || this.currentProject?.path || this.defaultProjectPath;
      
      const result = await dialog.showOpenDialog(mainWindow, {
        title: 'Select Folder Containing Images',
        defaultPath: defaultPath,
        properties: ['openDirectory']
      });

      if (!result.canceled && result.filePaths.length > 0) {
        const selectedFolder = result.filePaths[0];
        if (this.debugMode) {
          // // console.log('[BACKEND] Selected folder:', selectedFolder);
        }
        
        // Remember the directory for next time
        this.lastFolderDirectory = path.dirname(selectedFolder);
        if (this.debugMode) {
          // // console.log('[BACKEND] Remembered folder directory:', this.lastFolderDirectory);
        }
        
        // Save to disk for persistence across app restarts
        await this.saveDirectoryMemory();
        
        // Find all supported files in the selected folder (including subdirectories)
        const supportedExtensions = ['.jpg', '.jpeg', '.raw', '.daq', '.csv'];
        const foundFiles = [];
        
        async function scanDirectory(dirPath) {
          try {
            const entries = await fs.readdir(dirPath, { withFileTypes: true });
            
            for (const entry of entries) {
              const fullPath = path.join(dirPath, entry.name);
              
              if (entry.isDirectory()) {
                // Recursively scan subdirectories
                await scanDirectory(fullPath);
              } else if (entry.isFile()) {
                // Check if file has supported extension
                const ext = path.extname(entry.name).toLowerCase();
                if (supportedExtensions.includes(ext)) {
                  foundFiles.push(fullPath);
                }
              }
            }
          } catch (error) {
            // // console.warn('[BACKEND] Error scanning directory:', dirPath, error.message);
          }
        }
        
        await scanDirectory(selectedFolder);
        
        if (foundFiles.length === 0) {
          // // console.log('[BACKEND] No supported files found in folder:', selectedFolder);
          return [];
        }
        
        if (this.debugMode) {
          // // console.log('[BACKEND] Found', foundFiles.length, 'supported files in folder');
        }
        
        // Smart animation logic: consider both file count and processing mode
        const processingMode = await this.getProcessingMode();
        const isSerialMode = processingMode?.mode === 'serial';
        const animationThreshold = isSerialMode ? 5 : 15;
        
        // // console.log(`[BACKEND] Processing mode: ${processingMode?.mode}, threshold: ${animationThreshold}, files: ${foundFiles.length}`);
        
        // Send files to Python backend for processing
        try {
          // Prepare file paths for the backend
          const response = await fetch('http://localhost:5000/api/add-files', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              file_paths: foundFiles
            })
          });

          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }

          const result = await response.json();
          if (this.debugMode) {
            // // console.log('[BACKEND] Flask response for folder files:', result);
          }
          
          if (result.success && result.files) {
            if (this.debugMode) {
              // // console.log('[BACKEND] Successfully processed', result.files.length, 'files from folder');
            }
            return result.files;
          } else {
            console.error('[BACKEND] Flask backend returned error:', result.error);
            return [];
          }
        } catch (fetchError) {
          console.error('[BACKEND] Error calling Flask backend for folder files:', fetchError);
          
          // Fallback: return basic file info without Flask processing
          const fallbackFiles = foundFiles.map(filePath => ({
            type: 'image',
            title: path.basename(filePath),
            calib: false,
            cameraModel: 'Unknown',
            datetime: 'Unknown',
            layers: [],
            path: filePath
          }));
          
          // // console.log('[BACKEND] Using fallback file info for', fallbackFiles.length, 'files');
          return fallbackFiles;
        }
      }
      
      return [];
    } catch (error) {
      console.error('[BACKEND] Error in addFolder:', error);
      return [];
    }
  }

  async selectFolder(mainWindow) {
    try {
      // Use last folder directory if available, otherwise fall back to project or default path
      const defaultPath = this.lastFolderDirectory || this.currentProject?.path || this.defaultProjectPath;
      
      const result = await dialog.showOpenDialog(mainWindow, {
        title: 'Select Folder',
        defaultPath: defaultPath,
        properties: ['openDirectory']
      });

      if (!result.canceled && result.filePaths.length > 0) {
        if (this.debugMode) {
          // // console.log('[BACKEND] Selected folder:', result.filePaths[0]);
        }
        
        // Remember the directory for next time
        this.lastFolderDirectory = result.filePaths[0];
        if (this.debugMode) {
          // // console.log('[BACKEND] Remembered folder directory:', this.lastFolderDirectory);
        }
        
        // Save to disk for persistence across app restarts
        await this.saveDirectoryMemory();
        return { success: true, folder: result.filePaths[0] };
      }
      
      return { success: false, folder: '' };
    } catch (error) {
      console.error('[BACKEND] Error in selectFolder:', error);
      return { success: false, error: error.message };
    }
  }

  // User authentication
  // CRITICAL: Now routes through Flask backend to enforce device limits
  async remoteUserLogin(email, password) {
    return new Promise((resolve, reject) => {

      const http = require('http');
      const postData = JSON.stringify({
        email: email,
        password: password
      });

      const options = {
        hostname: 'localhost',
        port: 5000,
        path: '/api/login',
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(postData)
        },
        timeout: 30000 // 30 second timeout
      };

      const req = http.request(options, (res) => {

        let data = '';
        res.on('data', (chunk) => {
          data += chunk;
        });

        res.on('end', () => {

          try {
            const result = JSON.parse(data);

            // Handle device limit exceeded error
            if (res.statusCode === 403 && result.error_code === 'DEVICE_LIMIT_EXCEEDED') {
              // // console.log('[BACKEND] 🔐 ❌ Device limit exceeded - login rejected');
              const response = {
                success: false,
                error: result.error || 'Device limit reached',
                error_code: 'DEVICE_LIMIT_EXCEEDED',
                message: result.message || 'Device limit reached.',
                manage_url: result.manage_url
              };
              // // console.log('[BACKEND] 🔐 📤 Returning to frontend:', JSON.stringify(response));
              resolve(response);
              return;
            }

            // Handle other validation errors
            if (res.statusCode === 403) {
              // // console.log('[BACKEND] 🔐 ❌ Device validation failed');
              resolve({
                success: false,
                error: result.error || 'Device validation failed',
                error_code: result.error_code
              });
              return;
            }

            // Handle successful login
            if (res.statusCode === 200 && result.success) {
              // // console.log('[BACKEND] 🔐 ✅ Login successful, device validated');
              const user = result.user;
              
              // Flask backend provides: email, user_id, _id, token, plan_id, planID, 
              // plan_expiration, demoEndDate, subscription_level, planLevel
              // Map to frontend-expected format with all compatibility fields
              resolve({
                success: true,
                user: {
                  email: user.email || email,
                  name: user.name || 'MAPIR User',  // Flask doesn't provide name, use default
                  plan: user.subscription_level || 'standard',
                  planLevel: user.planLevel || (user.subscription_level === 'premium' ? 3 : 1),
                  expiration: user.plan_expiration || user.demoEndDate,
                  plan_expiration: user.plan_expiration || user.demoEndDate,
                  plan_id: user.plan_id || user.planID || (user.subscription_level === 'premium' ? 3 : 1),
                  subscription_level: user.subscription_level || (user.planLevel === 3 ? 'premium' : 'standard'),
                  token: user.token,
                  id: user.user_id || user._id,
                  _id: user._id || user.user_id,
                  user_id: user.user_id || user._id,
                  firstName: user.firstName || null,  // Optional fields
                  lastName: user.lastName || null,
                  projectDisplayOrder: user.projectDisplayOrder || null,
                  tos: user.tos || null,
                  planId: user.planId || user.plan_id || user.planID
                }
              });
              return;
            }

            // Handle other error cases
            // // console.log('[BACKEND] 🔐 ❌ Login failed with status:', res.statusCode);
            
            // Check if it's a 404 (route not found) or other HTTP errors
            if (res.statusCode === 404) {
              console.error('[BACKEND] 🔐 ❌ Flask /api/login endpoint not found (404)');
              resolve({
                success: false,
                error: 'Backend login endpoint not found. Please ensure the Flask backend is running with the latest code.',
                error_code: 'ENDPOINT_NOT_FOUND'
              });
            } else if (res.statusCode === 401) {
              // Unauthorized - could be invalid credentials, user deleted, or device limit
              // If logout_required is set, the frontend should clear the session
              resolve({
                success: false,
                error: result.error || 'Invalid credentials',
                error_code: result.error_code,
                logout_required: result.logout_required || false
              });
            } else {
              resolve({
                success: false,
                error: result.error || 'Login failed',
                error_code: result.error_code
              });
            }
          } catch (parseError) {
            console.error('[BACKEND] 🔐 ❌ JSON parse error:', parseError);
            console.error('[BACKEND] 🔐 ❌ Response data:', data.substring(0, 200));
            
            // Check if response is HTML (likely 404 page)
            if (data.trim().startsWith('<!') || data.includes('<html')) {
              resolve({
                success: false,
                error: 'Backend login endpoint not found (404). Please ensure the Flask backend is running with the latest code.',
                error_code: 'ENDPOINT_NOT_FOUND'
              });
            } else {
              resolve({
                success: false,
                error: 'Invalid server response. Please check backend logs.',
                error_code: 'INVALID_RESPONSE'
              });
            }
          }
        });
      });

      req.on('error', (error) => {
        // Check if Flask backend is not running
        if (error.code === 'ECONNREFUSED') {
          // Backend not ready - this is expected during startup, don't log
          resolve({
            success: false,
            error: 'Backend not ready yet. Please wait and then try again.'
          });
        } else {
          // Log unexpected connection errors
          console.error('[BACKEND] 🔐 ❌ Flask backend connection error:', error);
          resolve({
            success: false,
            error: 'Connection failed: ' + error.message
          });
        }
      });

      req.on('timeout', () => {
        console.error('[BACKEND] 🔐 ❌ Flask backend request timeout');
        req.destroy();
        resolve({
          success: false,
          error: 'Login request timed out. Please try again.'
        });
      });

      req.write(postData);
      req.end();
    });
  }

  async getUserInfo(userId, token) {
    return new Promise((resolve, reject) => {
      const options = {
        hostname: 'dynamic.cloud.mapir.camera',
        port: 443,
        path: `/users/${userId}`,
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
          'User-Agent': 'Chloros-Electron/1.0'
        }
      };

      const req = https.request(options, (res) => {
        let data = '';
        res.on('data', (chunk) => {
          data += chunk;
        });

        res.on('end', () => {
          try {
            if (res.statusCode === 200) {
              const userInfo = JSON.parse(data);
              // // console.log('[BACKEND] 🔐 Got user info:', userInfo.email);
              resolve(userInfo);
            } else {
              reject(new Error('Failed to get user info'));
            }
          } catch (parseError) {
            reject(parseError);
          }
        });
      });

      req.on('error', (error) => {
        reject(error);
      });

      req.end();
    });
  }



  getPlanLevel(planId) {
    // Convert plan ID to subscription level (matching original api.py logic)
    if (!planId) return 0; // standard
    
    const plan = planId.toString().toLowerCase();
    
    // Based on original code: if plan ID is 3, 5, 7, 8, or 86, it's premium (Chloros+)
    // Plan ID 86 = Internal/MAPIR plan (cloud infrastructure)
    if (['3', '5', '7', '8', '86', 'plus', 'premium'].includes(plan)) {
      return 3; // premium level
    }
    
    return 0; // standard level
  }

  mapPlanLevel(planLevel) {
    // Map numeric plan levels to descriptive names (matching original Chloros logic)
    const plan = planLevel.toString();
    
    switch(plan) {
      case 'standard':
      case '0':
        return 'Chloros';
      case 'plus':
      case '1':
      case '3':
      case '5':
      case '7':
      case '8':
        return 'Chloros+';
      default:
        return 'Chloros';
    }
  }
}

module.exports = ChlorosBackend;

