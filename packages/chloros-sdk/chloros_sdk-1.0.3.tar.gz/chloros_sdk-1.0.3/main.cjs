const { app, BrowserWindow, ipcMain, dialog, shell, screen } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');
const https = require('https');
const querystring = require('querystring');
const fs = require('fs').promises;

// Import the Electron backend
const ElectronBackend = require('./electron-backend.cjs');

// ========================================
// SELF-HEALING GPU RECOVERY SYSTEM
// ========================================
// Automatically tries to fix GPU issues before disabling GPU
const pathModule = require('path');
const fsSync = require('fs');

// Get user data path before app is ready
let userDataPath;
try {
  userDataPath = app.getPath('userData');
} catch (err) {
  // Fallback if userData path not available yet
  userDataPath = pathModule.join(require('os').homedir(), '.chloros');
}

const gpuCrashFlagPath = pathModule.join(userDataPath, 'gpu-crash-detected.flag');
const gpuRecoveryAttemptPath = pathModule.join(userDataPath, 'gpu-recovery-attempt.flag');

// GPU crash flag paths (silent - only log on errors)

// Don't set environment variables early - they can interfere with renderer initialization
// Just use command-line switches which Chromium handles better

let gpuDisabled = false;
let gpuRecoveryMode = false;

// ========================================
// SYSTEM RESTART DETECTION
// ========================================
// Detect if system was restarted since GPU crash - fresh start means we can try GPU again
const { execSync, spawnSync } = require('child_process');

function getSystemUptimeSeconds() {
  try {
    if (process.platform === 'win32') {
      // Windows: Get system uptime
      // Use os.uptime() instead of WMI to avoid "Invalid namespace" errors
      const os = require('os');
      return os.uptime();
    } else if (process.platform === 'linux') {
      // Linux: Read /proc/uptime
      const uptime = execSync('cat /proc/uptime', { encoding: 'utf8', timeout: 1000 });
      return parseFloat(uptime.split(' ')[0]);
    } else if (process.platform === 'darwin') {
      // macOS: Use sysctl
      const uptime = execSync('sysctl -n kern.boottime', { encoding: 'utf8', timeout: 1000 });
      const bootTime = parseInt(uptime.match(/sec = (\d+)/)[1]);
      return Math.floor(Date.now() / 1000) - bootTime;
    }
  } catch (error) {
    // If we can't detect uptime, assume no restart (conservative approach)
    return null;
  }
  return null;
}

function wasSystemRestartedSinceFile(filePath) {
  try {
    if (!fsSync.existsSync(filePath)) {
      return false;
    }
    
    const fileStats = fsSync.statSync(filePath);
    const fileAgeSeconds = Math.floor((Date.now() - fileStats.mtimeMs) / 1000);
    const systemUptimeSeconds = getSystemUptimeSeconds();
    
    if (systemUptimeSeconds === null) {
      // Can't determine uptime - be conservative and keep flags
      return false;
    }
    
    // If file is older than system uptime, system was restarted since file was created
    return fileAgeSeconds > systemUptimeSeconds;
  } catch (error) {
    return false;
  }
}

// Check if system was restarted since GPU crash flags were created
const systemRestartedSinceCrash = wasSystemRestartedSinceFile(gpuCrashFlagPath);
if (systemRestartedSinceCrash) {
  // System was restarted - clear flags and give GPU a fresh chance
  try {
    if (fsSync.existsSync(gpuCrashFlagPath)) {
      fsSync.unlinkSync(gpuCrashFlagPath);
    }
    if (fsSync.existsSync(gpuRecoveryAttemptPath)) {
      fsSync.unlinkSync(gpuRecoveryAttemptPath);
    }
    // Silent success - GPU will be enabled normally
  } catch (err) {
    // Ignore cleanup errors - just proceed
  }
}

// ========================================
// PROACTIVE VRAM DETECTION
// ========================================
// Detect systems with insufficient VRAM and skip GPU entirely to prevent crashes

function detectVRAM() {
  try {
    // Silently detect VRAM - all errors suppressed
    
    if (process.platform === 'win32') {
      // Windows: Use Registry instead of WMI to avoid console errors
      try {
        // GPU class GUID in registry: {4d36e968-e325-11ce-bfc1-08002be10318}
        // Try reading from Display adapter registry keys
        const gpuRegPath = 'HKLM\\SYSTEM\\CurrentControlSet\\Control\\Class\\{4d36e968-e325-11ce-bfc1-08002be10318}\\0000';
        
        // CRITICAL: Check for Intel HD Graphics (known problematic)
        try {
          const gpuNameResult = spawnSync('reg', [
            'query',
            gpuRegPath,
            '/v',
            'DriverDesc'
          ], {
            encoding: 'utf8',
            timeout: 2000,
            windowsHide: true,
            stdio: ['ignore', 'pipe', 'ignore']
          });
          
          if (gpuNameResult.status === 0 && gpuNameResult.stdout) {
            const gpuName = gpuNameResult.stdout.toLowerCase();
            if (gpuName.includes('intel') && gpuName.includes('hd graphics')) {
              // // console.log('⚠️ Intel HD Graphics detected - known to have driver issues');
              // // console.log('   Forcing GPU disable regardless of VRAM amount');
              return -1; // Special value: force disable
            }
          }
        } catch (err) {
          // Continue with normal detection
        }
        
        // Continue with normal VRAM detection
        // (gpuRegPath already defined above)
        
        // Try multiple possible registry values for VRAM
        const vramKeys = [
          'HardwareInformation.qwMemorySize',
          'HardwareInformation.MemorySize', 
          'HardwareInformation.AdapterRAM'
        ];
        
        for (const key of vramKeys) {
          try {
            const result = spawnSync('reg', [
              'query',
              gpuRegPath,
              '/v',
              key
            ], {
              encoding: 'utf8',
              timeout: 5000,
              windowsHide: true,
              stdio: ['ignore', 'pipe', 'ignore']
            });
            
            if (result.status === 0 && result.stdout) {
              // Parse registry output
              // Format: "    HardwareInformation.qwMemorySize    REG_QWORD    0x100000000"
              const match = result.stdout.match(/REG_(?:QWORD|DWORD)\s+(?:0x)?([0-9a-fA-F]+)/);
              if (match) {
                const vramBytes = parseInt(match[1], 16);
                if (!isNaN(vramBytes) && vramBytes > 0) {
                  const vramMB = Math.floor(vramBytes / (1024 * 1024));
                  // VRAM detected from registry
                  return vramMB;
                }
              }
            }
          } catch (err) {
            // Try next key
            continue;
          }
        }
        
        // Fallback: Try querying multiple GPU adapters (0001, 0002, etc.)
        for (let i = 1; i <= 3; i++) {
          const adapterNum = i.toString().padStart(4, '0');
          const altPath = `HKLM\\SYSTEM\\CurrentControlSet\\Control\\Class\\{4d36e968-e325-11ce-bfc1-08002be10318}\\${adapterNum}`;
          
          try {
            const result = spawnSync('reg', [
              'query',
              altPath,
              '/v',
              'HardwareInformation.qwMemorySize'
            ], {
              encoding: 'utf8',
              timeout: 5000,
              windowsHide: true,
              stdio: ['ignore', 'pipe', 'ignore']
            });
            
            if (result.status === 0 && result.stdout) {
              const match = result.stdout.match(/REG_(?:QWORD|DWORD)\s+(?:0x)?([0-9a-fA-F]+)/);
              if (match) {
                const vramBytes = parseInt(match[1], 16);
                if (!isNaN(vramBytes) && vramBytes > 0) {
                  const vramMB = Math.floor(vramBytes / (1024 * 1024));
                  // VRAM detected from adapter registry
                  return vramMB;
                }
              }
            }
          } catch (err) {
            // Try next adapter
            continue;
          }
        }
        
      } catch (regError) {
        // Registry query failed - proceed without VRAM info
      }
      
      return null; // Could not detect VRAM via registry
    } else if (process.platform === 'linux') {
      // Linux: Try lspci or nvidia-smi
      try {
        const lspciOutput = execSync('lspci | grep -i vga', { 
          encoding: 'utf8', 
          timeout: 5000 
        });
        // // console.log(`   ℹ️ GPU detected on Linux: ${lspciOutput.trim()}`);
        
        // Try nvidia-smi for NVIDIA GPUs
        try {
          const nvidiaOutput = execSync(
            'nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits',
            { encoding: 'utf8', timeout: 5000 }
          );
          const vramMB = parseInt(nvidiaOutput.trim(), 10);
          if (!isNaN(vramMB) && vramMB > 0) {
            // // console.log(`   ✅ Detected VRAM via nvidia-smi: ${vramMB}MB`);
            return vramMB;
          }
        } catch (nvError) {
          // // console.log('   ℹ️ nvidia-smi not available (non-NVIDIA GPU)');
        }
      } catch (lspciError) {
        // // console.log('   ⚠️ Could not detect GPU on Linux');
      }
    } else if (process.platform === 'darwin') {
      // macOS: Use system_profiler
      try {
        const macOutput = execSync(
          'system_profiler SPDisplaysDataType | grep "VRAM"',
          { encoding: 'utf8', timeout: 5000 }
        );
        const match = macOutput.match(/(\d+)\s*MB/);
        if (match) {
          const vramMB = parseInt(match[1], 10);
          // // console.log(`   ✅ Detected VRAM on macOS: ${vramMB}MB`);
          return vramMB;
        }
      } catch (macError) {
        // // console.log('   ⚠️ Could not detect VRAM on macOS');
      }
    }
    
    return null; // VRAM detection failed - proceed with GPU and reactive crash handling
    
  } catch (error) {
    // // console.log('   ⚠️ VRAM detection error:', error.message);
    return null;
  }
}

// Detect VRAM and disable GPU proactively if insufficient
const detectedVRAM = detectVRAM();
const MIN_VRAM_MB = 256; // Minimum 256MB VRAM recommended for Electron GPU acceleration

// Check for Intel HD Graphics (returns -1) OR low VRAM
if (detectedVRAM !== null && (detectedVRAM < MIN_VRAM_MB || detectedVRAM === -1)) {
  if (detectedVRAM === -1) {
    // // console.log(`🚨 INTEL HD GRAPHICS DETECTED (known driver issues)`);
    // // console.log('   Forcing MAXIMUM GPU disable for stability');
  } else {
    // // console.log(`🚨 INSUFFICIENT VRAM DETECTED (${detectedVRAM}MB < ${MIN_VRAM_MB}MB minimum)`);
    // // console.log('   Proactively disabling GPU to prevent crashes');
  }
  // // console.log('   This system will run in CPU-only mode for stability');
  
  gpuDisabled = true;
  
  // ULTRA-NUCLEAR OPTION: Maximum GPU disable for Intel HD Graphics
  app.disableHardwareAcceleration();
  
  // GPU DISABLE - Prevent ALL GPU/OpenGL initialization
  app.commandLine.appendSwitch('disable-gpu');
  app.commandLine.appendSwitch('disable-gpu-compositing');
  app.commandLine.appendSwitch('in-process-gpu');  // CRITICAL: Prevent separate GPU process from spawning
  app.commandLine.appendSwitch('disable-webgl');   // Disable WebGL (prevents GLES3/GLES2 contexts)
  app.commandLine.appendSwitch('disable-webgl2');
  app.commandLine.appendSwitch('disable-software-rasterizer');  // Force software rendering OFF (use CPU)
  app.commandLine.appendSwitch('disable-accelerated-2d-canvas');  // Disable 2D canvas acceleration
  app.commandLine.appendSwitch('disable-accelerated-video-decode');  // Disable video decode acceleration
  app.commandLine.appendSwitch('disable-gl-drawing-for-tests');  // Disable ALL OpenGL drawing
  app.commandLine.appendSwitch('use-gl', 'disabled');  // ULTRA-NUCLEAR: Completely disable OpenGL (no SwiftShader, no ANGLE)
  
  // Additional stability flags to prevent cascading failures
  app.commandLine.appendSwitch('disable-features', 'VizDisplayCompositor,Vulkan,UseSkiaRenderer,HardwareMediaKeyHandling');  // ABSOLUTE NUCLEAR: Bypass Skia renderer
  app.commandLine.appendSwitch('disable-gpu-rasterization');  // Force CPU rasterization
  app.commandLine.appendSwitch('disable-direct-composition');  // Disable Windows direct composition
  app.commandLine.appendSwitch('disable-gpu-sandbox');  // Disable GPU sandbox (can cause issues)
  app.commandLine.appendSwitch('disable-gpu-watchdog');  // Disable GPU watchdog
  app.commandLine.appendSwitch('disable-gpu-driver-bug-workarounds');  // Skip buggy driver workarounds
  
  // ABSOLUTE LAST RESORT FLAGS - for Intel HD Graphics 620
  app.commandLine.appendSwitch('disable-3d-apis');  // Disable ALL 3D APIs
  app.commandLine.appendSwitch('disable-vulkan');  // Extra Vulkan disable
  app.commandLine.appendSwitch('disable-dawn');  // Disable WebGPU Dawn
  app.commandLine.appendSwitch('num-raster-threads', '1');  // Single-thread rasterization
  app.commandLine.appendSwitch('enable-low-end-device-mode');  // Low-end device optimizations
  app.commandLine.appendSwitch('disable-backing-store-limit');  // No backing store limit
  
  // // console.log('ℹ️  ABSOLUTE MAXIMUM GPU disable active - pure CPU rendering with Skia bypass');
  
  // // console.log('✅ GPU disabled proactively - app will run in stable CPU mode');
  
  // Create flag to indicate low VRAM mode (for diagnostics)
  try {
    if (!fsSync.existsSync(userDataPath)) {
      fsSync.mkdirSync(userDataPath, { recursive: true });
    }
    const lowVramFlagPath = pathModule.join(userDataPath, 'low-vram-mode.flag');
    fsSync.writeFileSync(lowVramFlagPath, `Low VRAM detected: ${detectedVRAM}MB (${new Date().toISOString()})`);
    // // console.log('   📝 Low VRAM flag created for diagnostics');
  } catch (err) {
    console.error('   ⚠️ Could not create low VRAM flag:', err);
  }
}

// Check GPU crash history (only if GPU wasn't already disabled by low VRAM detection)
// Note: If system was restarted, flags were already cleared above, so this won't trigger
const hadCrash = fsSync.existsSync(gpuCrashFlagPath);

// Silently check crash flags

if (hadCrash && !gpuDisabled) {
  // GPU crashed in previous session (before restart) - disable GPU for this session only
  // After user restarts their system, flags will be cleared and GPU will be tried again fresh
  
  app.disableHardwareAcceleration();
  
  // ULTRA-NUCLEAR OPTION: Maximum GPU disable (same as Intel HD Graphics fix)
  // This MUST happen before app.whenReady()
  
  // GPU DISABLE - Prevent ALL GPU/OpenGL initialization
  app.commandLine.appendSwitch('disable-gpu');
  app.commandLine.appendSwitch('disable-gpu-compositing');
  app.commandLine.appendSwitch('in-process-gpu');  // CRITICAL: Prevent separate GPU process from spawning
  app.commandLine.appendSwitch('disable-webgl');   // Disable WebGL (prevents GLES3/GLES2 contexts)
  app.commandLine.appendSwitch('disable-webgl2');
  app.commandLine.appendSwitch('disable-software-rasterizer');  // Force software rendering OFF (use CPU)
  app.commandLine.appendSwitch('disable-accelerated-2d-canvas');  // Disable 2D canvas acceleration
  app.commandLine.appendSwitch('disable-accelerated-video-decode');  // Disable video decode acceleration
  app.commandLine.appendSwitch('disable-gl-drawing-for-tests');  // Disable ALL OpenGL drawing
  app.commandLine.appendSwitch('use-gl', 'disabled');  // ULTRA-NUCLEAR: Completely disable OpenGL (no SwiftShader, no ANGLE)
  
  // Additional stability flags to prevent cascading failures
  app.commandLine.appendSwitch('disable-features', 'VizDisplayCompositor,Vulkan,UseSkiaRenderer,HardwareMediaKeyHandling');  // ABSOLUTE NUCLEAR: Bypass Skia renderer
  app.commandLine.appendSwitch('disable-gpu-rasterization');  // Force CPU rasterization
  app.commandLine.appendSwitch('disable-direct-composition');  // Disable Windows direct composition
  app.commandLine.appendSwitch('disable-gpu-sandbox');  // Disable GPU sandbox (can cause issues)
  app.commandLine.appendSwitch('disable-gpu-watchdog');  // Disable GPU watchdog
  app.commandLine.appendSwitch('disable-gpu-driver-bug-workarounds');  // Skip buggy driver workarounds
  
  // ABSOLUTE LAST RESORT FLAGS - for Intel HD Graphics 620
  app.commandLine.appendSwitch('disable-3d-apis');  // Disable ALL 3D APIs
  app.commandLine.appendSwitch('disable-vulkan');  // Extra Vulkan disable
  app.commandLine.appendSwitch('disable-dawn');  // Disable WebGPU Dawn
  app.commandLine.appendSwitch('num-raster-threads', '1');  // Single-thread rasterization
  app.commandLine.appendSwitch('enable-low-end-device-mode');  // Low-end device optimizations
  app.commandLine.appendSwitch('disable-backing-store-limit');  // No backing store limit
  
  // // console.log('ℹ️  ABSOLUTE MAXIMUM GPU disable active - pure CPU rendering with Skia bypass');
  
  gpuDisabled = true;
  
  // // console.log('✅ GPU disabled - using CPU rendering');
  
} else if (!gpuDisabled) {
  // No crashes and sufficient VRAM - normal operation with MINIMAL GPU flags (let Chromium auto-detect)
  // Silent - GPU enabled with hardware acceleration
  
  // MINIMAL FLAGS - Let Chromium/Electron auto-detect best configuration
  // Only disable GPU sandbox for compatibility (common practice)
  app.commandLine.appendSwitch('disable-gpu-sandbox');
}

// ========================================
// SUPPRESS DEVTOOLS CONSOLE WARNINGS
// ========================================
// Suppress Chrome DevTools Protocol errors (like Autofill.enable failures)
// These are harmless but clutter the console
app.commandLine.appendSwitch('log-level', '3'); // Only show fatal errors
// Note: User can still see all logs in DevTools itself

// Track critical GPU failures during this session
let criticalGpuFailureDetected = false;
let emergencyRestartInProgress = false; // Prevent multiple restart attempts

// Listen for GPU launch failures and crashes
let gpuFailureCount = 0;
const maxGpuFailures = 2; // Allow 2 failures before emergency shutdown

// Listen for child process errors (catches GPU process launch failures early)
app.on('child-process-gone', (event, details) => {
  if (details.type === 'GPU' && !gpuDisabled && !emergencyRestartInProgress) {
    console.error('❌ GPU child process failed:', details);
    // // console.log('🚨 CRITICAL: GPU process launch/initialization failed');
    // // console.log('   This indicates broken GPU drivers - forcing immediate GPU disable');
    
    criticalGpuFailureDetected = true;
    gpuFailureCount++;
    emergencyRestartInProgress = true; // Block any further restart attempts
    
    // Mark crash flag - GPU will be disabled until system restart
    try {
      if (!fsSync.existsSync(userDataPath)) {
        fsSync.mkdirSync(userDataPath, { recursive: true });
      }
      fsSync.writeFileSync(gpuCrashFlagPath, `GPU CRASH: ${new Date().toISOString()}`);
      // No recovery-attempt flag - simplified logic now
    } catch (err) {
      console.error('Failed to create GPU crash flag:', err);
    }
    
    // Trigger immediate emergency restart (don't wait for multiple failures)
    // // console.log('💀 EMERGENCY: Critical GPU failure detected - restarting app NOW with GPU disabled');
    // // console.log('   App will relaunch IMMEDIATELY...');
    
    // CRITICAL: Ensure flag is written to disk BEFORE spawning
    try {
      // Synchronously verify flag exists
      if (fsSync.existsSync(gpuCrashFlagPath)) {
        // Crash flag verified - ready to restart
      }
    } catch (err) {
      console.error('Error verifying crash flag:', err);
    }
    
    // // console.log('🔄 Spawning new instance (flags will be read on startup)...');
    
    // Spawn a new instance manually (app.relaunch doesn't work during crashes)
    const { spawn } = require('child_process');
    const exePath = process.execPath;
    // // console.log('   Executable path:', exePath);
    
    // DON'T pass GPU flags - the spawned instance will read crash flags and disable GPU during init
    const args = process.argv.slice(1);
    // // console.log('   Launch args:', args);
    
    // Spawn detached process that continues after parent exits
    const child = spawn(exePath, args, {
      detached: true,
      stdio: 'inherit', // Inherit all stdio to see what happens
      windowsHide: false // Don't hide window so we can see if it starts
    });
    child.unref(); // Allow parent to exit independently
    
    // // console.log('🔚 New instance spawned (PID:', child.pid, ') - will read crash flags on startup');
    // // console.log('   Crash flags will force GPU disable in the new instance');
    
    // Exit IMMEDIATELY - don't wait, or the child's cleanup will kill us during the delay
    // // console.log('💀 Exiting current instance NOW...');
    process.exit(0);
  }
});

// Listen for GPU crashes
app.on('gpu-process-crashed', (event, killed) => {
  console.error('❌ GPU process crashed!', { killed });
  
  if (!gpuDisabled && !criticalGpuFailureDetected) {
    // // console.log('🚨 Recording GPU crash - will attempt recovery on next launch');
    try {
      if (!fsSync.existsSync(userDataPath)) {
        fsSync.mkdirSync(userDataPath, { recursive: true });
      }
      fsSync.writeFileSync(gpuCrashFlagPath, new Date().toISOString());
    } catch (err) {
      console.error('Failed to create GPU crash flag:', err);
    }
  }
});

// Track app start time to detect early crashes
const appStartTime = Date.now();

// Listen for renderer crashes
app.on('render-process-gone', (event, webContents, details) => {
  // Ignore renderer crashes if emergency restart is already in progress
  if (emergencyRestartInProgress) {
    // // console.log('⏭️ Ignoring renderer crash - emergency restart already in progress');
    return;
  }
  
  console.error('❌ Renderer process crashed!', details);
  
  const timeSinceStart = Date.now() - appStartTime;
  const isEarlyCrash = timeSinceStart < 10000; // Crash within 10 seconds of launch
  
  if (!gpuDisabled && !criticalGpuFailureDetected) {
    // If renderer crashes within 10 seconds AND we're in GPU recovery mode, this is critical
    if (isEarlyCrash && gpuRecoveryMode) {
      // // console.log('💀 CRITICAL: Renderer crashed during GPU recovery (within 10s of launch)');
      // // console.log('   This indicates GPU drivers are too broken to fix - forcing GPU disable');
      
      criticalGpuFailureDetected = true;
      gpuFailureCount++;
      emergencyRestartInProgress = true; // Block any further restart attempts
      
      // Mark both flags to skip recovery next time
      try {
        if (!fsSync.existsSync(userDataPath)) {
          fsSync.mkdirSync(userDataPath, { recursive: true });
        }
        fsSync.writeFileSync(gpuCrashFlagPath, `CRITICAL EARLY CRASH: ${new Date().toISOString()}`);
        fsSync.writeFileSync(gpuRecoveryAttemptPath, `SKIPPED - EARLY CRASH: ${new Date().toISOString()}`);
        // // console.log('💀 Critical failure flags created - GPU will be disabled on restart');
      } catch (err) {
        console.error('Failed to create critical GPU failure flags:', err);
      }
      
      // Emergency restart with GPU disabled - IMMEDIATE
      // // console.log('🔄 EMERGENCY RESTART: Spawning new instance with GPU disabled...');
      
      // CRITICAL: Ensure flags are written to disk BEFORE spawning
      // // console.log('✍️ Ensuring crash flags are written to disk...');
      try {
        // Synchronously verify flags exist
        if (fsSync.existsSync(gpuCrashFlagPath)) {
          // // console.log('   ✅ Crash flag verified on disk');
        }
        if (fsSync.existsSync(gpuRecoveryAttemptPath)) {
          // // console.log('   ✅ Recovery flag verified on disk');
        }
      } catch (err) {
        console.error('   ❌ Error verifying flags:', err);
      }
      
      // Spawn a new instance manually (app.relaunch doesn't work during crashes)
      const { spawn } = require('child_process');
      const exePath = process.execPath;
      // // console.log('   Executable path:', exePath);
      
      // DON'T pass GPU flags - the spawned instance will read crash flags and disable GPU during init
      const args = process.argv.slice(1);
      // // console.log('   Launch args:', args);
      
      // Spawn detached process that continues after parent exits
      const child = spawn(exePath, args, {
        detached: true,
        stdio: ['ignore', 'inherit', 'inherit'] // Inherit stdout/stderr so we can see logs
      });
      child.unref(); // Allow parent to exit independently
      
      // // console.log('🔚 New instance spawned (PID:', child.pid, ') - will read crash flags on startup');
      // // console.log('   Crash flags will force GPU disable in the new instance');
      
      // Force immediate exit
      // // console.log('💀 Exiting current instance NOW...');
      process.exit(0);
      
    } else {
      // Normal crash recording
      // // console.log('🚨 Recording renderer crash - may be GPU related');
      try {
        if (!fsSync.existsSync(userDataPath)) {
          fsSync.mkdirSync(userDataPath, { recursive: true });
        }
        fsSync.writeFileSync(gpuCrashFlagPath, new Date().toISOString());
      } catch (err) {
        console.error('Failed to create GPU crash flag:', err);
      }
    }
  }
});

// GPU recovery system configured

// Helper function to safely send IPC messages (prevents "Render frame disposed" errors)
function safeSend(sender, channel, data) {
  try {
    if (sender && !sender.isDestroyed()) {
      sender.send(channel, data);
    }
  } catch (error) {
    // // console.warn(`⚠️ Could not send IPC message on channel "${channel}":`, error.message);
  }
}

// Helper function to safely send debug console messages
function safeDebugSend(message) {
  try {
    // Send to debug console window
    if (debugConsoleWindow && !debugConsoleWindow.isDestroyed() && 
        debugConsoleWindow.webContents && !debugConsoleWindow.webContents.isDestroyed()) {
      debugConsoleWindow.webContents.send('backend-debug-output', message);
    }
    
    // Also send to main window for the log sidebar
    if (mainWindow && !mainWindow.isDestroyed() && 
        mainWindow.webContents && !mainWindow.webContents.isDestroyed()) {
      mainWindow.webContents.send('backend-debug-output', message);
    }
  } catch (error) {
    // Silent fail - debug console is optional
  }
}

// Keep a global reference of the window objects
let splashWindow = null;
let mainWindow = null;
let debugConsoleWindow = null;
let pythonProcess = null;
let io = null;
let backend = null;
let backendProcess = null;

// Function to cleanup all Chloros processes (except current one)
async function cleanupNuitkaTempFolders() {
  const fs = require('fs');
  const path = require('path');
  
  try {
    const tempDir = process.env.TEMP || process.env.TMP || 'C:\\Users\\MAPIR\\AppData\\Local\\Temp';
    // Silently clean up Nuitka temp folders
    
    // Find all onefile-* folders
    const folders = fs.readdirSync(tempDir, { withFileTypes: true })
      .filter(dirent => dirent.isDirectory() && dirent.name.includes('onefile'))
      .map(dirent => path.join(tempDir, dirent.name));
    
    // Silently clean Nuitka temp folders
    
    // Delete each folder
    let cleaned = 0;
    for (const folder of folders) {
      try {
        fs.rmSync(folder, { recursive: true, force: true });
        cleaned++;
        // // console.log(`✅ Deleted: ${folder}`);
      } catch (err) {
        // // console.log(`⚠️ Could not delete ${folder}: ${err.message}`);
      }
    }
    
    // Cleanup completed silently
  } catch (err) {
    // // console.log(`⚠️ Error during Nuitka temp cleanup: ${err.message}`);
  }
}

async function cleanupAllChlorosProcesses() {
  const { spawn } = require('child_process');
  const currentPid = process.pid;
  
  // Silently perform comprehensive cleanup
  
  return new Promise((resolve) => {
    // Get all Chloros and chloros-backend processes
    const tasklist = spawn('tasklist', ['/FO', 'CSV', '/NH'], { windowsHide: true });
    let tasklistOutput = '';
    
    tasklist.stdout.on('data', (data) => {
      tasklistOutput += data.toString();
    });
    
    tasklist.on('close', () => {
      const lines = tasklistOutput.split('\n');
      const pidsToKill = new Set();
      
      // Parse tasklist output and find Chloros processes
      lines.forEach(line => {
        if (line.includes('Chloros.exe') || 
            line.includes('chloros-backend.exe') || 
            line.includes('chloros-backend-safe.exe')) {
          const parts = line.split(',');
          if (parts.length >= 2) {
            const pidStr = parts[1].replace(/"/g, '').trim();
            const pid = parseInt(pidStr);
            if (pid && pid !== currentPid && !isNaN(pid)) {
              pidsToKill.add(pid);
            }
          }
        }
      });
      
      if (pidsToKill.size === 0) {
        resolve(); // No processes to clean up
        return;
      }
      
      // // console.log(`🔍 Found ${pidsToKill.size} Chloros processes to clean up: ${Array.from(pidsToKill).join(', ')}`);
      
      // Kill each PID
      let killPromises = Array.from(pidsToKill).map(pid => {
        return new Promise((resolvePid) => {
          const kill = spawn('taskkill', ['/F', '/PID', pid.toString()], { windowsHide: true });
          kill.on('close', (code) => {
            // // console.log(`🗡️ Killed Chloros PID ${pid} (exit code: ${code})`);
            resolvePid();
          });
          kill.on('error', () => {
            // // console.log(`⚠️ Could not kill Chloros PID ${pid} (may already be dead)`);
            resolvePid();
          });
        });
      });
      
      Promise.all(killPromises).then(() => {
        resolve(); // Cleanup completed
      });
    });
    
    tasklist.on('error', (error) => {
      // // console.warn('⚠️ Could not run tasklist, proceeding anyway:', error.message);
      resolve();
    });
  });
}

// Function to kill processes using port 5000
async function killProcessesOnPort(port) {
  const { spawn } = require('child_process');
  
  // Cleaning up processes on port (silent)
  
  return new Promise((resolve) => {
    // Use netstat to find processes using the port, then kill them
    const netstat = spawn('netstat', ['-ano'], { windowsHide: true });
    let netstatOutput = '';
    
    netstat.stdout.on('data', (data) => {
      netstatOutput += data.toString();
    });
    
    netstat.on('close', () => {
      const lines = netstatOutput.split('\n');
      const pidsToKill = new Set();
      
      // Find PIDs using the port
      lines.forEach(line => {
        if (line.includes(`:${port} `) && line.includes('LISTENING')) {
          const parts = line.trim().split(/\s+/);
          const pid = parts[parts.length - 1];
          if (pid && pid !== '0' && !isNaN(pid)) {
            pidsToKill.add(pid);
          }
        }
      });
      
      if (pidsToKill.size === 0) {
        // No processes found on port (silent)
        resolve();
        return;
      }
      
      // // console.log(`🔍 Found ${pidsToKill.size} processes on port ${port}: ${Array.from(pidsToKill).join(', ')}`);
      
      // Kill each PID
      let killPromises = Array.from(pidsToKill).map(pid => {
        return new Promise((resolvePid) => {
          const kill = spawn('taskkill', ['/F', '/PID', pid], { windowsHide: true });
          kill.on('close', (code) => {
            // // console.log(`🗡️ Killed PID ${pid} (exit code: ${code})`);
            resolvePid();
          });
          kill.on('error', () => {
            // // console.log(`⚠️ Could not kill PID ${pid} (may already be dead)`);
            resolvePid();
          });
        });
      });
      
      Promise.all(killPromises).then(() => {
        // // console.log(`✅ Port ${port} cleanup completed`);
        resolve();
      });
    });
    
    netstat.on('error', (error) => {
      // // console.warn('⚠️ Could not run netstat, proceeding anyway:', error.message);
      resolve();
    });
  });
}

// Function to check if backend is already running
function checkIfBackendRunning() {
  return new Promise((resolve) => {
    const http = require('http');
    const options = {
      hostname: 'localhost',
      port: 5000,
      path: '/api/status',
      method: 'GET',
      timeout: 1000
    };

    const req = http.request(options, (res) => {
      resolve(res.statusCode === 200);
    });

    req.on('error', () => resolve(false));
    req.on('timeout', () => resolve(false));
    req.setTimeout(1000);
    req.end();
  });
}

const isDev = process.argv.includes('--dev');
const PYTHON_SERVER_PORT = 3001;

// Window state management
let windowStateFile;

async function loadWindowState() {
  try {
    const data = await fs.readFile(windowStateFile, 'utf8');
    const state = JSON.parse(data);
    
    // Validate the state and ensure it's within screen bounds
    const displays = screen.getAllDisplays();
    const validDisplay = displays.find(display => {
      const { x, y, width, height } = display.bounds;
      return state.x >= x && state.y >= y && 
             state.x < x + width && state.y < y + height;
    });
    
    if (validDisplay && state.width > 0 && state.height > 0) {
      // Loaded window state silently
      return state;
    } else {
      // // console.log('🪟 Invalid window state, using defaults');
      return null;
    }
  } catch (error) {
    // // console.log('🪟 No previous window state found, using defaults');
    return null;
  }
}

async function saveWindowState(window) {
  try {
    const bounds = window.getBounds();
    const state = {
      x: bounds.x,
      y: bounds.y,
      width: bounds.width,
      height: bounds.height,
      isMaximized: window.isMaximized(),
      isMinimized: window.isMinimized(),
      lastSaved: new Date().toISOString()
    };
    
    await fs.writeFile(windowStateFile, JSON.stringify(state, null, 2));
    // Window state saved silently
  } catch (error) {
    console.error('🪟 Failed to save window state:', error);
  }
}

// Backend will be initialized in app.whenReady()

// IPC Handlers for PyWebView API compatibility
// Project Management
ipcMain.handle('new-project', async (event, projectName, template) => {
  return await backend.newProject(projectName, template);
});

ipcMain.handle('get-projects', async (event) => {
  return await backend.getProjects();
});

ipcMain.handle('open-project', async (event, projectName) => {
  return await backend.openProject(projectName);
});

ipcMain.handle('has-project-loaded', async (event) => {
  return backend.hasProjectLoaded();
});

ipcMain.handle('get-project-status', async (event) => {
  return backend.getProjectStatus();
});

ipcMain.handle('open-projects-folder', async (event) => {
  return await backend.openProjectsFolder();
});

ipcMain.handle('get-project-templates', async (event) => {
  return await backend.getProjectTemplates();
});

ipcMain.handle('save-project-template', async (event, templateName) => {
  return backend.saveProjectTemplate(templateName);
});

ipcMain.handle('latexify', async (event, formula) => {
  return backend.latexify(formula);
});

ipcMain.handle('get-autothreshold', async (event, imageName, indexName) => {
  return backend.getAutothreshold(imageName, indexName);
});

// File Management
ipcMain.handle('get-image-list', async (event) => {
  return await backend.getImageList();
});

ipcMain.handle('add-files', async (event) => {
  return await backend.addFiles(mainWindow);
});

ipcMain.handle('add-folder', async (event) => {
  return await backend.addFolder(mainWindow);
});

ipcMain.handle('handle-drag', async (event, paths) => {
  return await backend.handleDrag(paths);
});

ipcMain.handle('remove-files', async (event, filePaths) => {
  return await backend.removeFiles(filePaths);
});

ipcMain.handle('select-folder', async (event) => {
  return await backend.selectFolder(mainWindow);
});

ipcMain.handle('sync-checkbox-state', async (event, filename, calibState) => {
  return await backend.syncCheckboxState(filename, calibState);
});

ipcMain.handle('clear-jpg-cache', async (event, filename) => {
  return await backend.clearJpgCache(filename);
});

ipcMain.handle('clear-thumbnail-cache', async (event, filename) => {
  return await backend.clearThumbnailCache(filename);
});

ipcMain.handle('get-scan-data', async (event, filename) => {
  return await backend.getScanData(filename);
});

// Processing
ipcMain.handle('process-project', async (event) => {
  return await backend.processProject();
});

ipcMain.handle('interrupt-project', async (event) => {
  return await backend.interruptProject();
});

ipcMain.handle('detect-export-layers', async (event) => {
  return await backend.detectExportLayers();
});

ipcMain.handle('get-processing-progress', async (event) => {
  return backend.getProcessingProgress();
});

ipcMain.handle('get-status', async (event) => {
  return await backend.getStatus();
});

ipcMain.handle('set-processing-mode', async (event, mode) => {
  return await backend.setProcessingMode(mode);
});

ipcMain.handle('get-processing-mode', async (event) => {
  return await backend.getProcessingMode();
});

// User Management
ipcMain.handle('load-user-email', async (event) => {
  return await backend.loadUserEmail();
});

ipcMain.handle('save-user-email', async (event, email) => {
  return await backend.saveUserEmail(email);
});

ipcMain.handle('load-user-language', async (event) => {
  return await backend.loadUserLanguage();
});

ipcMain.handle('save-user-language', async (event, language) => {
  return await backend.saveUserLanguage(language);
});

// NOTE: remote-user-login and user-logout handlers are now registered in electron-backend.cjs setupIPCHandlers()
// to ensure proper routing through Flask backend with device validation

// Settings
ipcMain.handle('get-config', async (event) => {
  return backend.getConfig();
});

ipcMain.handle('set-config', async (event, key, value) => {
  return backend.setConfig(key, value);
});

ipcMain.handle('get-working-directory', async (event) => {
  return await backend.getWorkingDirectory();
});

ipcMain.handle('select-working-directory', async (event) => {
  return await backend.selectWorkingDirectory();
});

ipcMain.handle('move-project', async (event, newPath) => {
  return await backend.moveProjectToNewDirectory(newPath);
});

ipcMain.handle('get-minimum-window-size', async (event) => {
  return { width: 800, height: 600 };
});

// Flask API calls (for image viewer and other Python backend operations)
ipcMain.handle('flask-api-call', async (event, endpoint, data) => {
  return new Promise((resolve, reject) => {
    const postData = JSON.stringify(data);
    
    const options = {
      hostname: 'localhost',
      port: 5000,
      path: `/api/${endpoint}`,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData)
      }
    };

    const req = http.request(options, (res) => {
      let responseData = '';
      
      res.on('data', (chunk) => {
        responseData += chunk;
      });
      
      res.on('end', () => {
        try {
          const result = JSON.parse(responseData);
          resolve(result);
        } catch (parseError) {
          console.error(`[IPC] Failed to parse Flask API response for ${endpoint}:`, parseError);
          resolve({ success: false, error: 'Invalid response format' });
        }
      });
    });

    req.on('error', (error) => {
      console.error(`[IPC] Flask API call to ${endpoint} failed:`, error);
      resolve({ success: false, error: error.message });
    });

    req.write(postData);
    req.end();
  });
});

// Window controls (both handle and on for compatibility)
ipcMain.handle('minimize-window', async (event) => {
  const window = BrowserWindow.fromWebContents(event.sender);
  if (window) window.minimize();
});

ipcMain.handle('maximize-window', async (event) => {
  const window = BrowserWindow.fromWebContents(event.sender);
  if (window) {
    if (window.isMaximized()) {
      window.unmaximize();
    } else {
      window.maximize();
    }
  }
});

ipcMain.handle('close-window', async (event) => {
  const window = BrowserWindow.fromWebContents(event.sender);
  if (window) window.close();
});

ipcMain.handle('toggle-maximize', async (event) => {
  const window = BrowserWindow.fromWebContents(event.sender);
  if (window) {
    if (window.isMaximized()) {
      window.unmaximize();
    } else {
      window.maximize();
    }
  }
});

// IPC handler for manual port cleanup
ipcMain.handle('cleanup-port-5000', async () => {
  // // console.log('🧹 Manual port 5000 cleanup requested');
  await killProcessesOnPort(5000);
  return { success: true, message: 'Port 5000 cleaned up successfully' };
});

// Debug console handlers
ipcMain.handle('restart-backend', async () => {
  // // console.log('🔄 Backend restart requested from debug console');
  try {
    // Kill existing backend
    if (backendProcess) {
      // // console.log('🛑 Killing existing backend process...');
      backendProcess.kill('SIGTERM');
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    // Kill any processes on port 5000
    await killProcessesOnPort(5000);
    
    // Restart backend
    await startBackend();
    
    // Send success message to debug console
    safeDebugSend({
      type: 'info',
      message: 'Backend restarted successfully'
    });
    
    return { success: true, message: 'Backend restarted successfully' };
  } catch (error) {
    console.error('Failed to restart backend:', error);
    throw error;
  }
});

ipcMain.handle('kill-all-processes', async () => {
  // // console.log('💀 Kill all processes requested from debug console');
  try {
    // Kill backend process
    if (backendProcess) {
      // // console.log('🛑 Killing backend process...');
      backendProcess.kill('SIGTERM');
      backendProcess = null;
    }
    
    // Kill processes on port 5000
    await killProcessesOnPort(5000);
    
    // Send success message to debug console
    safeDebugSend({
        type: 'warning',
        message: 'All processes killed successfully'
      });
    
    return { success: true, message: 'All processes killed successfully' };
  } catch (error) {
    console.error('Failed to kill processes:', error);
    throw error;
  }
});

ipcMain.handle('check-backend-status', async () => {
  // // console.log('🔍 Backend status check requested from debug console');
  try {
    const isProcessRunning = backendProcess !== null && !backendProcess.killed;
    
    // Try to ping the backend API using http module
    let isApiResponding = false;
    let apiError = null;
    
    try {
      const http = require('http');
      const checkApi = () => new Promise((resolve, reject) => {
        const req = http.get('http://localhost:5000/api/status', (res) => {
          resolve(res.statusCode === 200);
        });
        req.on('error', reject);
        req.setTimeout(5000, () => {
          req.destroy();
          reject(new Error('Timeout'));
        });
      });
      
      isApiResponding = await checkApi();
    } catch (error) {
      apiError = error.message;
    }
    
    const status = {
      processRunning: isProcessRunning,
      apiResponding: isApiResponding,
      error: apiError
    };
    
    // Send status to debug console
    if (debugConsoleWindow && !debugConsoleWindow.isDestroyed()) {
      const statusMessage = `Backend Status:\n` +
        `  Process Running: ${isProcessRunning}\n` +
        `  API Responding: ${isApiResponding}\n` +
        (apiError ? `  Error: ${apiError}` : '');
      
      safeDebugSend({
        type: isApiResponding ? 'success' : 'error',
        message: statusMessage
      });
    }
    
    return { success: true, status };
  } catch (error) {
    console.error('Failed to check backend status:', error);
    throw error;
  }
});

// Test IPC handler to verify IPC is working
ipcMain.handle('test-ipc', async () => {
  // // console.log('✅ [MAIN] TEST-IPC handler called successfully!');
  return { success: true, message: 'IPC is working!' };
});

// Update system IPC handlers
ipcMain.handle('start-update', async (event, installerUrl) => {
  // // console.log('═══════════════════════════════════════');
  // // console.log('🔄 [MAIN] START-UPDATE IPC HANDLER CALLED!');
  // // console.log('🔄 Update requested from UI');
  // // console.log('📥 Installer URL:', installerUrl);
  // // console.log('═══════════════════════════════════════');
  
  if (!installerUrl) {
    console.error('❌ No installer URL provided');
    return { success: false, error: 'No installer URL provided' };
  }
  
  try {
    const https = require('https');
    const http = require('http');
    const fs = require('fs');
    const path = require('path');
    const os = require('os');
    const { spawn } = require('child_process');
    
    // // console.log('📥 Downloading installer from:', installerUrl);
    
    // For Google Drive, add confirmation parameter to bypass virus scan page for large files
    let finalInstallerUrl = installerUrl;
    if (installerUrl.includes('drive.google.com')) {
      if (installerUrl.includes('?')) {
        finalInstallerUrl = installerUrl + '&confirm=t';
      } else {
        finalInstallerUrl = installerUrl + '?confirm=t';
      }
      // // console.log('🔄 Added Google Drive confirmation parameter');
      // // console.log('📥 Final URL:', finalInstallerUrl);
    }
    
    // Download installer to temp directory
    const tempDir = os.tmpdir();
    // Use a consistent filename regardless of what Google Drive sends
    const installerPath = path.join(tempDir, 'Chloros-Update-Installer.exe');
    
    // Delete any existing installer file first
    if (fs.existsSync(installerPath)) {
      // // console.log('🗑️ Removing existing installer file...');
      try {
        fs.unlinkSync(installerPath);
        // // console.log('✅ Old installer removed');
      } catch (err) {
        // // console.warn('⚠️ Could not remove old installer:', err.message);
      }
    }
    
    // Start download asynchronously - don't wait for it
    const downloadPromise = new Promise((resolve) => {
      const file = fs.createWriteStream(installerPath);
      
      const protocol = finalInstallerUrl.startsWith('https') ? https : http;
      
      // Set timeout for download (10 minutes for large file)
      const DOWNLOAD_TIMEOUT = 10 * 60 * 1000; // 10 minutes
      
      let downloadedBytes = 0;
      let totalBytes = 0;
      let lastProgressTime = Date.now();
      let lastDownloadedBytes = 0;
      
      const request = protocol.get(finalInstallerUrl, (response) => {
        // Handle ALL redirect types (301, 302, 303, 307, 308) - Google Drive uses 303
        if (response.statusCode === 301 || response.statusCode === 302 || 
            response.statusCode === 303 || response.statusCode === 307 || 
            response.statusCode === 308) {
          const redirectUrl = response.headers.location;
          // Following redirect silently
          
          const redirectProtocol = redirectUrl.startsWith('https') ? https : http;
          
          redirectProtocol.get(redirectUrl, (redirectResponse) => {
            if (redirectResponse.statusCode !== 200) {
              console.error('❌ Redirect failed with status:', redirectResponse.statusCode);
              fs.unlink(installerPath, () => {});
              safeSend(event.sender, 'update-error', { error: `HTTP ${redirectResponse.statusCode}` });
              resolve({ success: false, error: `HTTP ${redirectResponse.statusCode}` });
              return;
            }
            
            // Get total file size from Content-Length header
            totalBytes = parseInt(redirectResponse.headers['content-length'] || '0', 10);
            // // console.log('📊 Total file size:', totalBytes, 'bytes', `(${(totalBytes / 1024 / 1024).toFixed(2)} MB)`);
            // // console.log('📊 Content-Type:', redirectResponse.headers['content-type']);
            
            // Check if we're getting HTML instead of the actual file (common Google Drive issue)
            if (redirectResponse.headers['content-type']?.includes('text/html')) {
              // // console.log('⚠️ Received HTML - this is Google Drive virus scan page');
              // // console.log('📄 Parsing HTML to extract real download link...');
              
              // Collect HTML response
              let htmlData = '';
              redirectResponse.on('data', (chunk) => {
                htmlData += chunk.toString();
              });
              
              redirectResponse.on('end', () => {
                // Log the HTML for debugging
                // // console.log('📄 HTML Response Length:', htmlData.length);
                // // console.log('📄 HTML Preview (first 1000 chars):', htmlData.substring(0, 1000));
                // // console.log('📄 HTML Preview (last 500 chars):', htmlData.substring(htmlData.length - 500));
                
                // Extract hidden form input values from Google Drive's HTML
                // Google Drive uses: <input type="hidden" name="confirm" value="t">
                const confirmMatch = htmlData.match(/<input[^>]*name=["']confirm["'][^>]*value=["']([^"']+)["']/i);
                const uuidMatch = htmlData.match(/<input[^>]*name=["']uuid["'][^>]*value=["']([^"']+)["']/i);
                const formActionMatch = htmlData.match(/<form[^>]*action=["']([^"']+)["']/i);
                
                // // console.log('🔍 Confirm match result:', confirmMatch);
                // // console.log('🔍 UUID match result:', uuidMatch);
                // // console.log('🔍 Form action match:', formActionMatch);
                
                if (confirmMatch && uuidMatch) {
                  const confirmCode = confirmMatch[1];
                  const uuid = uuidMatch[1];
                  const fileIdMatch = finalInstallerUrl.match(/[?&]id=([^&]+)/);
                  
                  if (fileIdMatch) {
                    const fileId = fileIdMatch[1];
                    // Use drive.usercontent.google.com as that's what the form action uses
                    const realDownloadUrl = `https://drive.usercontent.google.com/download?id=${fileId}&export=download&confirm=${confirmCode}&uuid=${uuid}`;
                    
                    // // console.log('✅ Found confirmation code:', confirmCode);
                    // // console.log('✅ Found UUID:', uuid);
                    // // console.log('🔄 Retrying with real download URL:', realDownloadUrl);
                    
                    // Retry download with the real URL
                    https.get(realDownloadUrl, (finalResponse) => {
                      if (finalResponse.statusCode !== 200) {
                        console.error('❌ Final download failed:', finalResponse.statusCode);
                        fs.unlink(installerPath, () => {});
                        safeSend(event.sender, 'update-error', { error: `HTTP ${finalResponse.statusCode}` });
                        resolve({ success: false, error: `HTTP ${finalResponse.statusCode}` });
                        return;
                      }
                      
                      totalBytes = parseInt(finalResponse.headers['content-length'] || '0', 10);
                      // // console.log('✅ Real download started! Size:', totalBytes, 'bytes');
                      
                      finalResponse.on('data', (chunk) => {
                        downloadedBytes += chunk.length;
                        const now = Date.now();
                        if (now - lastProgressTime >= 500) {
                          const progress = totalBytes > 0 ? (downloadedBytes / totalBytes) * 100 : 0;
                          const bytesPerSecond = (downloadedBytes - lastDownloadedBytes) / ((now - lastProgressTime) / 1000);
                          const speedMBps = (bytesPerSecond / 1024 / 1024).toFixed(2);
                          
                          const progressData = {
                            percent: progress,
                            downloadedMB: downloadedBytes / 1024 / 1024,
                            totalMB: totalBytes / 1024 / 1024,
                            speed: `${speedMBps} MB/s`
                          };
                          
                          // // console.log('📊 [MAIN] Sending update-progress:', progressData.percent.toFixed(1) + '%');
                          safeSend(event.sender, 'update-progress', progressData);
                          
                          lastProgressTime = now;
                          lastDownloadedBytes = downloadedBytes;
                        }
                      });
                      
                      finalResponse.pipe(file);
                      
                      file.on('finish', () => {
                        file.close();
                        // // console.log('✅ Download complete!');
                        // // console.log('📊 Verifying downloaded file...');
                        // // console.log('  Path:', installerPath);
                        // // console.log('  Size:', fs.statSync(installerPath).size, 'bytes');
                        // // console.log('  Exists:', fs.existsSync(installerPath));
                        
                        // Wait for file to be fully released before spawning (fixes EBUSY error)
                        setTimeout(() => {
                          // // console.log('🚀 Attempting to start installer...');
                          // // console.log('  Command:', installerPath);
                          // // console.log('  Args: (showing UI for user visibility)');
                          
                          try {
                            // Start installer with UI (no /S flag) so user can see progress
                            // runAfterFinish:true in package.json will auto-launch app when done
                            const installerProcess = spawn(installerPath, [], {
                              detached: true,
                              shell: true,
                              stdio: 'ignore'
                            });
                            
                            installerProcess.on('error', (err) => {
                              console.error('❌ Installer process error:', err);
                              safeSend(event.sender, 'update-error', { error: `Failed to start installer: ${err.message}` });
                            });
                            
                            installerProcess.unref();
                            
                            // // console.log('✅ Installer spawned successfully!');
                            // // console.log('  Process PID:', installerProcess.pid);
                            // // console.log('  Installer will show UI with progress');
                            // // console.log('  App will auto-launch when installation completes');
                            // // console.log('  Quitting app in 2 seconds to allow installer to start...');
                            
                            setTimeout(() => {
                              // // console.log('👋 Quitting application for update...');
                              app.quit();
                            }, 2000);
                          } catch (err) {
                            console.error('❌ Exception while starting installer:', err);
                            console.error('  Error name:', err.name);
                            console.error('  Error message:', err.message);
                            console.error('  Error stack:', err.stack);
                            safeSend(event.sender, 'update-error', { error: `Failed to start installer: ${err.message}` });
                          }
                        }, 1500); // Wait 1.5 seconds for file to be fully released
                        
                        resolve({ success: true });
                      });
                      
                      file.on('error', (err) => {
                        console.error('❌ File write error:', err);
                        fs.unlink(installerPath, () => {});
                        safeSend(event.sender, 'update-error', { error: err.message });
                        resolve({ success: false, error: err.message });
                      });
                    }).on('error', (err) => {
                      console.error('❌ Final download error:', err);
                      fs.unlink(installerPath, () => {});
                      safeSend(event.sender, 'update-error', { error: err.message });
                      resolve({ success: false, error: err.message });
                    });
                  } else {
                    console.error('❌ Could not extract file ID');
                    fs.unlink(installerPath, () => {});
                    safeSend(event.sender, 'update-error', { error: 'Could not parse download link' });
                    resolve({ success: false, error: 'Could not parse download link' });
                  }
                } else {
                  console.error('❌ Could not find confirmation code in HTML');
                  console.error('❌ HTML preview:', htmlData.substring(0, 500));
                  fs.unlink(installerPath, () => {});
                  safeSend(event.sender, 'update-error', { error: 'Could not extract download link from Google Drive page' });
                  resolve({ success: false, error: 'Could not extract download link' });
                }
              });
              
              return;
            }
            
            // Track download progress
            redirectResponse.on('data', (chunk) => {
              downloadedBytes += chunk.length;
              
              // Send progress update every 500ms
              const now = Date.now();
              if (now - lastProgressTime >= 500) {
                const progress = totalBytes > 0 ? (downloadedBytes / totalBytes) * 100 : 0;
                const bytesPerSecond = (downloadedBytes - lastDownloadedBytes) / ((now - lastProgressTime) / 1000);
                const speedMBps = (bytesPerSecond / 1024 / 1024).toFixed(2);
                
                const progressData = {
                  percent: progress,
                  downloadedMB: downloadedBytes / 1024 / 1024,
                  totalMB: totalBytes / 1024 / 1024,
                  speed: `${speedMBps} MB/s`
                };
                
                // // console.log('📊 [MAIN] Sending update-progress to renderer:', progressData);
                safeSend(event.sender, 'update-progress', progressData);
                
                lastProgressTime = now;
                lastDownloadedBytes = downloadedBytes;
              }
            });
            
            redirectResponse.pipe(file);
            
            file.on('finish', () => {
              file.close();
              // // console.log('✅ Installer downloaded successfully');
              // // console.log('📊 Verifying downloaded file...');
              // // console.log('  Path:', installerPath);
              // // console.log('  Size:', fs.statSync(installerPath).size, 'bytes');
              // // console.log('  Exists:', fs.existsSync(installerPath));
              
              // Wait for file to be fully released before spawning (fixes EBUSY error)
              setTimeout(() => {
                // // console.log('🚀 Attempting to start installer...');
                // // console.log('  Command:', installerPath);
                // // console.log('  Args: (showing UI for user visibility)');
                
                try {
                  // Start installer with UI (no /S flag) so user can see progress
                  // runAfterFinish:true in package.json will auto-launch app when done
                  const installerProcess = spawn(installerPath, [], {
                    detached: true,
                    shell: true,
                    stdio: 'ignore'
                  });
                  
                  installerProcess.on('error', (err) => {
                    console.error('❌ Installer process error:', err);
                    safeSend(event.sender, 'update-error', { error: `Failed to start installer: ${err.message}` });
                  });
                  
                  installerProcess.unref();
                  
                  // // console.log('✅ Installer spawned successfully!');
                  // // console.log('  Process PID:', installerProcess.pid);
                  // // console.log('  Installer will show UI with progress');
                  // // console.log('  App will auto-launch when installation completes');
                  // // console.log('  Quitting app in 2 seconds to allow installer to start...');
                  
                  setTimeout(() => {
                    // // console.log('👋 Quitting application for update...');
                    app.quit();
                  }, 2000);
                } catch (err) {
                  console.error('❌ Exception while starting installer:', err);
                  console.error('  Error name:', err.name);
                  console.error('  Error message:', err.message);
                  console.error('  Error stack:', err.stack);
                  safeSend(event.sender, 'update-error', { error: `Failed to start installer: ${err.message}` });
                }
              }, 1500); // Wait 1.5 seconds for file to be fully released
              
              resolve({ success: true, message: 'Update started' });
            });
            
            file.on('error', (err) => {
              console.error('❌ File write error:', err);
              fs.unlink(installerPath, () => {});
              safeSend(event.sender, 'update-error', { error: `File write error: ${err.message}` });
              resolve({ success: false, error: err.message });
            });
          }).on('error', (err) => {
            console.error('❌ Redirect download error:', err);
            fs.unlink(installerPath, () => {});
            safeSend(event.sender, 'update-error', { error: `Download error: ${err.message}` });
            resolve({ success: false, error: err.message });
          });
        } else if (response.statusCode === 200) {
          // Direct download (no redirect)
          // // console.log('✅ Direct download started (200 OK)');
          
          // Get total file size from Content-Length header
          totalBytes = parseInt(response.headers['content-length'] || '0', 10);
          // // console.log('📊 Total file size:', totalBytes, 'bytes', `(${(totalBytes / 1024 / 1024).toFixed(2)} MB)`);
          // // console.log('📊 Content-Type:', response.headers['content-type']);
          
          // Check if we're getting HTML instead of the actual file (common Google Drive issue)
          if (response.headers['content-type']?.includes('text/html')) {
            // // console.log('⚠️ Received HTML - this is Google Drive virus scan page (direct)');
            // // console.log('📄 Parsing HTML to extract real download link...');
            
            let htmlData = '';
            response.on('data', (chunk) => {
              htmlData += chunk.toString();
            });
            
            response.on('end', () => {
              // Log the HTML for debugging
              // // console.log('📄 HTML Response Length (direct):', htmlData.length);
              // // console.log('📄 HTML Preview (first 1000 chars):', htmlData.substring(0, 1000));
              // // console.log('📄 HTML Preview (last 500 chars):', htmlData.substring(htmlData.length - 500));
              
              // Extract hidden form input values from Google Drive's HTML
              const confirmMatch = htmlData.match(/<input[^>]*name=["']confirm["'][^>]*value=["']([^"']+)["']/i);
              const uuidMatch = htmlData.match(/<input[^>]*name=["']uuid["'][^>]*value=["']([^"']+)["']/i);
              const formActionMatch = htmlData.match(/<form[^>]*action=["']([^"']+)["']/i);
              
              // // console.log('🔍 Confirm match result (direct):', confirmMatch);
              // // console.log('🔍 UUID match result (direct):', uuidMatch);
              // // console.log('🔍 Form action match (direct):', formActionMatch);
              
              if (confirmMatch && uuidMatch) {
                const confirmCode = confirmMatch[1];
                const uuid = uuidMatch[1];
                const fileIdMatch = finalInstallerUrl.match(/[?&]id=([^&]+)/);
                
                if (fileIdMatch) {
                  const fileId = fileIdMatch[1];
                  const realDownloadUrl = `https://drive.usercontent.google.com/download?id=${fileId}&export=download&confirm=${confirmCode}&uuid=${uuid}`;
                  
                  // // console.log('✅ Found confirmation code:', confirmCode);
                  // // console.log('✅ Found UUID:', uuid);
                  // // console.log('🔄 Retrying with real download URL:', realDownloadUrl);
                  
                  https.get(realDownloadUrl, (finalResponse) => {
                    if (finalResponse.statusCode !== 200) {
                      console.error('❌ Final download failed:', finalResponse.statusCode);
                      fs.unlink(installerPath, () => {});
                      safeSend(event.sender, 'update-error', { error: `HTTP ${finalResponse.statusCode}` });
                      resolve({ success: false, error: `HTTP ${finalResponse.statusCode}` });
                      return;
                    }
                    
                    totalBytes = parseInt(finalResponse.headers['content-length'] || '0', 10);
                    // // console.log('✅ Real download started! Size:', totalBytes, 'bytes');
                    
                    finalResponse.on('data', (chunk) => {
                      downloadedBytes += chunk.length;
                      const now = Date.now();
                      if (now - lastProgressTime >= 500) {
                        const progress = totalBytes > 0 ? (downloadedBytes / totalBytes) * 100 : 0;
                        const bytesPerSecond = (downloadedBytes - lastDownloadedBytes) / ((now - lastProgressTime) / 1000);
                        const speedMBps = (bytesPerSecond / 1024 / 1024).toFixed(2);
                        
                        const progressData = {
                          percent: progress,
                          downloadedMB: downloadedBytes / 1024 / 1024,
                          totalMB: totalBytes / 1024 / 1024,
                          speed: `${speedMBps} MB/s`
                        };
                        
                        // // console.log('📊 [MAIN] Sending update-progress:', progressData.percent.toFixed(1) + '%');
                        safeSend(event.sender, 'update-progress', progressData);
                        
                        lastProgressTime = now;
                        lastDownloadedBytes = downloadedBytes;
                      }
                    });
                    
                    finalResponse.pipe(file);
                    
                    file.on('finish', () => {
                      file.close();
                      // // console.log('✅ Download complete!');
                      // // console.log('📊 Verifying downloaded file...');
                      // // console.log('  Path:', installerPath);
                      // // console.log('  Size:', fs.statSync(installerPath).size, 'bytes');
                      // // console.log('  Exists:', fs.existsSync(installerPath));
                      
                      // Wait for file to be fully released before spawning (fixes EBUSY error)
                      setTimeout(() => {
                        // // console.log('🚀 Attempting to start installer...');
                        // // console.log('  Command:', installerPath);
                        // // console.log('  Args: (showing UI for user visibility)');
                        
                        try {
                          // Start installer with UI (no /S flag) so user can see progress
                          // runAfterFinish:true in package.json will auto-launch app when done
                          const installerProcess = spawn(installerPath, [], {
                            detached: true,
                            shell: true,
                            stdio: 'ignore'
                          });
                          
                          installerProcess.on('error', (err) => {
                            console.error('❌ Installer process error:', err);
                            safeSend(event.sender, 'update-error', { error: `Failed to start installer: ${err.message}` });
                          });
                          
                          installerProcess.unref();
                          
                          // // console.log('✅ Installer spawned successfully!');
                          // // console.log('  Process PID:', installerProcess.pid);
                          // // console.log('  Installer will show UI with progress');
                          // // console.log('  App will auto-launch when installation completes');
                          // // console.log('  Quitting app in 2 seconds to allow installer to start...');
                          
                          setTimeout(() => {
                            // // console.log('👋 Quitting application for update...');
                            app.quit();
                          }, 2000);
                        } catch (err) {
                          console.error('❌ Exception while starting installer:', err);
                          console.error('  Error name:', err.name);
                          console.error('  Error message:', err.message);
                          console.error('  Error stack:', err.stack);
                          safeSend(event.sender, 'update-error', { error: `Failed to start installer: ${err.message}` });
                        }
                      }, 1500); // Wait 1.5 seconds for file to be fully released
                      
                      resolve({ success: true });
                    });
                    
                    file.on('error', (err) => {
                      console.error('❌ File write error:', err);
                      fs.unlink(installerPath, () => {});
                      safeSend(event.sender, 'update-error', { error: err.message });
                      resolve({ success: false, error: err.message });
                    });
                  }).on('error', (err) => {
                    console.error('❌ Final download error:', err);
                    fs.unlink(installerPath, () => {});
                    safeSend(event.sender, 'update-error', { error: err.message });
                    resolve({ success: false, error: err.message });
                  });
                } else {
                  console.error('❌ Could not extract file ID');
                  fs.unlink(installerPath, () => {});
                  safeSend(event.sender, 'update-error', { error: 'Could not parse download link' });
                  resolve({ success: false, error: 'Could not parse download link' });
                }
              } else {
                console.error('❌ Could not find confirmation code in HTML');
                console.error('❌ HTML preview:', htmlData.substring(0, 500));
                fs.unlink(installerPath, () => {});
                safeSend(event.sender, 'update-error', { error: 'Could not extract download link from Google Drive page' });
                resolve({ success: false, error: 'Could not extract download link' });
              }
            });
            
            return;
          }
          
          // Track download progress
          response.on('data', (chunk) => {
            downloadedBytes += chunk.length;
            
            // Send progress update every 500ms
            const now = Date.now();
            if (now - lastProgressTime >= 500) {
              const progress = totalBytes > 0 ? (downloadedBytes / totalBytes) * 100 : 0;
              const bytesPerSecond = (downloadedBytes - lastDownloadedBytes) / ((now - lastProgressTime) / 1000);
              const speedMBps = (bytesPerSecond / 1024 / 1024).toFixed(2);
              
              const progressData = {
                percent: progress,
                downloadedMB: downloadedBytes / 1024 / 1024,
                totalMB: totalBytes / 1024 / 1024,
                speed: `${speedMBps} MB/s`
              };
              
              // // console.log('📊 [MAIN] Sending update-progress to renderer (direct):', progressData);
              safeSend(event.sender, 'update-progress', progressData);
              
              lastProgressTime = now;
              lastDownloadedBytes = downloadedBytes;
            }
          });
          
          response.pipe(file);
          
          file.on('finish', () => {
            file.close();
            // // console.log('✅ Installer downloaded successfully');
            // // console.log('📊 Verifying downloaded file...');
            // // console.log('  Path:', installerPath);
            // // console.log('  Size:', fs.statSync(installerPath).size, 'bytes');
            // // console.log('  Exists:', fs.existsSync(installerPath));
            
            // Wait for file to be fully released before spawning (fixes EBUSY error)
            setTimeout(() => {
              // // console.log('🚀 Attempting to start installer...');
              // // console.log('  Command:', installerPath);
              // // console.log('  Args: (showing UI for user visibility)');
              
              try {
                // Start installer with UI (no /S flag) so user can see progress
                // runAfterFinish:true in package.json will auto-launch app when done
                const installerProcess = spawn(installerPath, [], {
                  detached: true,
                  shell: true,
                  stdio: 'ignore'
                });
                
                installerProcess.on('error', (err) => {
                  console.error('❌ Installer process error:', err);
                  safeSend(event.sender, 'update-error', { error: `Failed to start installer: ${err.message}` });
                });
                
                installerProcess.unref();
                
                // // console.log('✅ Installer spawned successfully!');
                // // console.log('  Process PID:', installerProcess.pid);
                // // console.log('  Installer will show UI with progress');
                // // console.log('  App will auto-launch when installation completes');
                // // console.log('  Quitting app in 2 seconds to allow installer to start...');
                
                setTimeout(() => {
                  // // console.log('👋 Quitting application for update...');
                  app.quit();
                }, 2000);
              } catch (err) {
                console.error('❌ Exception while starting installer:', err);
                console.error('  Error name:', err.name);
                console.error('  Error message:', err.message);
                console.error('  Error stack:', err.stack);
                safeSend(event.sender, 'update-error', { error: `Failed to start installer: ${err.message}` });
              }
            }, 1500); // Wait 1.5 seconds for file to be fully released
            
            resolve({ success: true, message: 'Update started' });
          });
          
          file.on('error', (err) => {
            console.error('❌ File write error:', err);
            fs.unlink(installerPath, () => {});
            safeSend(event.sender, 'update-error', { error: `File write error: ${err.message}` });
            resolve({ success: false, error: err.message });
          });
        } else {
          console.error('❌ Unexpected HTTP status:', response.statusCode);
          safeSend(event.sender, 'update-error', { error: `HTTP ${response.statusCode}` });
          resolve({ success: false, error: `HTTP ${response.statusCode}` });
        }
      }).on('error', (err) => {
        console.error('❌ Download error:', err);
        fs.unlink(installerPath, () => {});
        safeSend(event.sender, 'update-error', { error: `Download error: ${err.message}` });
        resolve({ success: false, error: err.message });
      });
      
      // Set timeout on the request
      request.setTimeout(DOWNLOAD_TIMEOUT, () => {
        console.error('❌ Download timeout after', DOWNLOAD_TIMEOUT / 1000, 'seconds');
        request.abort();
        fs.unlink(installerPath, () => {});
        safeSend(event.sender, 'update-error', { error: 'Download timeout - please check your internet connection' });
        resolve({ success: false, error: 'Download timeout - please check your internet connection' });
      });
    });
    
    // Don't wait for download to complete - return immediately so renderer can show progress
    // // console.log('✅ Download started, returning control to renderer');
    downloadPromise.catch(err => {
      console.error('❌ Background download failed:', err);
    });
    
    return { success: true, message: 'Download started' };
  } catch (error) {
    console.error('❌ Update failed:', error);
    return { success: false, error: error.message };
  }
});

ipcMain.handle('get-app-version', async (event) => {
  return app.getVersion();
});

// Fetch from main process to avoid CORS/403 issues
// IPC handler to get installer file size (avoids CORS/403 from renderer)
ipcMain.handle('get-installer-size', async (event, url) => {
  // // console.log('📏 [MAIN] Getting installer size from:', url);
  try {
    const https = require('https');
    const http = require('http');
    
    return new Promise((resolve) => {
      // Add timeout to prevent hanging
      const timeoutMs = 30000; // 30 seconds
      const timeoutId = setTimeout(() => {
        console.error('❌ [MAIN] Size fetch timeout');
        resolve({ success: false, error: 'Request timeout' });
      }, timeoutMs);
      
      const protocol = url.startsWith('https') ? https : http;
      
      const options = {
        method: 'HEAD',
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        },
        timeout: timeoutMs
      };
      
      const handleResponse = (response) => {
        clearTimeout(timeoutId);
        const contentLength = response.headers['content-length'];
        if (contentLength) {
          const sizeBytes = parseInt(contentLength, 10);
          const sizeGB = (sizeBytes / (1024 ** 3)).toFixed(2);
          // // console.log(`✅ [MAIN] Installer size: ${sizeBytes} bytes (${sizeGB} GB)`);
          resolve({ success: true, sizeBytes });
        } else {
          // // console.warn('⚠️ [MAIN] No content-length header found');
          resolve({ success: false, error: 'No content-length header' });
        }
      };
      
      const handleError = (err) => {
        clearTimeout(timeoutId);
        console.error('❌ [MAIN] Size fetch error:', err);
        // Ensure error message is a string
        const errorMsg = err && err.message ? err.message : 'Unknown error';
        resolve({ success: false, error: errorMsg });
      };
      
      const request = protocol.request(url, options, (response) => {
        // Handle redirects
        if (response.statusCode >= 300 && response.statusCode < 400 && response.headers.location) {
          const redirectUrl = response.headers.location;
          // Following redirect silently
          
          const redirectRequest = protocol.request(redirectUrl, options, handleResponse);
          redirectRequest.on('error', handleError);
          redirectRequest.on('timeout', () => {
            redirectRequest.destroy();
            handleError(new Error('Redirect request timeout'));
          });
          redirectRequest.end();
        } else {
          handleResponse(response);
        }
      });
      
      request.on('error', handleError);
      request.on('timeout', () => {
        request.destroy();
        handleError(new Error('Request timeout'));
      });
      request.end();
    });
  } catch (error) {
    console.error('❌ [MAIN] Exception in get-installer-size:', error);
    // Ensure error message is a string
    const errorMsg = error && error.message ? error.message : 'Unknown error';
    return { success: false, error: errorMsg };
  }
});

ipcMain.handle('fetch-version-file', async (event, url) => {
  // Silently fetching version file
  try{
    const https = require('https');
    const http = require('http');
    
    return new Promise((resolve, reject) => {
      const protocol = url.startsWith('https') ? https : http;
      
      const options = {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
          'Accept': 'text/plain,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
          'Accept-Language': 'en-US,en;q=0.9'
        }
      };
      
      // Helper function to determine if error is network-related
      const isNetworkError = (err) => {
        const networkErrorCodes = ['ENOTFOUND', 'ECONNREFUSED', 'ECONNRESET', 'ETIMEDOUT', 'EHOSTUNREACH', 'ENETUNREACH'];
        return networkErrorCodes.includes(err.code);
      };
      
      protocol.get(url, options, (response) => {
        // Handle redirects (301, 302, 303, 307, 308)
        if (response.statusCode === 301 || response.statusCode === 302 || response.statusCode === 303 || response.statusCode === 307 || response.statusCode === 308) {
          const redirectUrl = response.headers.location;
          // Following redirect silently
          protocol.get(redirectUrl, options, (redirectResponse) => {
            let data = '';
            redirectResponse.on('data', (chunk) => {
              data += chunk;
            });
            redirectResponse.on('end', () => {
              // Version file fetched successfully
              resolve({ success: true, data: data.trim() });
            });
          }).on('error', (err) => {
            // Only log non-network errors (network errors are expected when offline)
            if (!isNetworkError(err)) {
              console.error('❌ [MAIN] Redirect fetch failed:', err);
            }
            resolve({ success: false, error: err.message });
          });
        } else if (response.statusCode === 200) {
          let data = '';
          response.on('data', (chunk) => {
            data += chunk;
          });
          response.on('end', () => {
            // Version file fetched successfully
            resolve({ success: true, data: data.trim() });
          });
        } else {
          // Only log unexpected status codes (not 404, which is common for missing update files)
          if (response.statusCode !== 404) {
            console.error('❌ [MAIN] Fetch failed with status:', response.statusCode);
          }
          resolve({ success: false, error: `HTTP ${response.statusCode}` });
        }
      }).on('error', (err) => {
        // Only log non-network errors (network errors are expected when offline)
        if (!isNetworkError(err)) {
          console.error('❌ [MAIN] Fetch error:', err);
        }
        resolve({ success: false, error: err.message });
      });
    });
  } catch (error) {
    // Only log unexpected exceptions (not network-related)
    console.error('❌ [MAIN] Exception during fetch:', error);
    return { success: false, error: error.message };
  }
});

// Add send-based handlers for direct IPC calls
ipcMain.on('minimize-window', (event) => {
  const window = BrowserWindow.fromWebContents(event.sender);
  if (window) {
    // // console.log('🟡 Minimize window via IPC send');
    window.minimize();
  }
});

ipcMain.on('maximize-window', (event) => {
  const window = BrowserWindow.fromWebContents(event.sender);
  if (window) {
    // // console.log('🔵 Maximize/restore window via IPC send');
    if (window.isMaximized()) {
      window.unmaximize();
    } else {
      window.maximize();
    }
  }
});

ipcMain.on('close-window', (event) => {
  const window = BrowserWindow.fromWebContents(event.sender);
  if (window) {
    // // console.log('🔴 Close window via IPC send');
    window.close();
  }
});

// File dialogs
ipcMain.handle('show-open-dialog', async (event, options) => {
  const window = BrowserWindow.fromWebContents(event.sender);
  return await dialog.showOpenDialog(window, options);
});

ipcMain.handle('show-save-dialog', async (event, options) => {
  const window = BrowserWindow.fromWebContents(event.sender);
  return await dialog.showSaveDialog(window, options);
});

ipcMain.handle('show-message-box', async (event, options) => {
  const window = BrowserWindow.fromWebContents(event.sender);
  return await dialog.showMessageBox(window, options);
});

function createSplashWindow() {
  // Prevent creating multiple splash windows
  if (splashWindow && !splashWindow.isDestroyed()) {
    // // console.log('⚠️ Splash window already exists');
    return;
  }
  
  // Creating splash window
  splashWindow = new BrowserWindow({
    width: 200,
    height: 200,
    frame: false,
    alwaysOnTop: true,
    transparent: true,
    show: false, // Don't show until ready
    icon: path.join(__dirname, 'ui', 'corn_logo_single_256.ico'), // Set application icon
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: true,
      sandbox: false
    }
  });

  // Load splash.html
  splashWindow.loadFile('renderer/splash.html').then(() => {
    splashWindow.show(); // Splash loaded successfully
    splashWindow.center();
  }).catch(async error => {
    console.error('❌ Failed to load splash.html:', error);
    // Fallback: create main window immediately
    await createMainWindow();
    return;
  });

  splashWindow.on('closed', () => {
    // Splash window closed
    splashWindow = null;
  });

  // Add error handling
  splashWindow.webContents.on('did-fail-load', async (event, errorCode, errorDescription) => {
    console.error('❌ Splash window failed to load:', errorCode, errorDescription);
    await createMainWindow();
  });

  // Show splash for 3 seconds then create main window
  setTimeout(async () => {
    await createMainWindow(); // Splash timeout reached
  }, 3000);
}

function findBackendExecutable() {
  const possiblePaths = [
    path.join(process.resourcesPath, 'backend', 'chloros-backend-safe.exe'),
    path.join(process.resourcesPath, 'backend', 'chloros-backend.exe'),
    path.join(__dirname, 'chloros-backend-safe.exe'),
    path.join(__dirname, 'chloros-backend.exe'),
    path.join(process.cwd(), 'chloros-backend-safe.exe'),
    path.join(process.cwd(), 'chloros-backend.exe')
  ];
  
  for (const exePath of possiblePaths) {
    try {
      if (require('fs').existsSync(exePath)) {
        // // console.log(`✅ Found backend executable at: ${exePath}`);
        return exePath;
      }
    } catch (error) {
      // // console.log(`❌ Error checking path ${exePath}:`, error.message);
    }
  }
  
  return null; // Backend executable not found
}

async function startBackend() {
  try {
    // Starting backend process (silent)
    
    // Send debug message
    safeDebugSend({
        type: 'info',
        message: 'Starting backend process...'
      });
    
    // FIRST: Check if backend is already running (like CLI does)
    // If a backend is already running (e.g., from CLI or another Electron instance),
    // just use it instead of killing it and starting a new one
    const existingBackend = await checkIfBackendRunning();
    if (existingBackend) {
      // // console.log('✅ Backend already running - using existing backend');
      safeDebugSend({
          type: 'success',
          message: '✅ Backend already running - using existing backend (like CLI does)'
        });
      
      // Notify main window that backend is ready
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send('backend-ready');
        // // console.log('✅ Sent backend-ready message to main window');
      }
      
      // Don't set backendProcess - we're using an external backend
      // This means we won't try to kill it when closing
      return;
    }
    
    const backendPath = findBackendExecutable();
    if (!backendPath) {
      // No compiled backend found - starting Python dev backend
      safeDebugSend({
          type: 'info',
          message: 'No compiled backend found, starting Python dev backend...'
        });
      
      // CRITICAL: Kill ALL Python processes to ensure fresh code load
      // Then clean up port 5000 BEFORE starting Python backend
      try {
        await new Promise((resolve) => {
          const killPython = spawn('powershell', ['-Command', 'Stop-Process -Name python -Force -ErrorAction SilentlyContinue'], { windowsHide: true });
          killPython.on('close', () => {
            resolve(); // Python processes killed
          });
          // Timeout after 2 seconds
          setTimeout(resolve, 2000);
        });
      } catch (err) {
        // // console.log('⚠️ Error killing Python processes:', err.message);
      }
      
      // Silently clean up port 5000
      await killProcessesOnPort(5000);
      
      // Delete .pyc files to ensure fresh Python code load (silently)
      try {
        // Use same logic as backend startup for workspace root
        const workspaceRoot = app.isPackaged 
          ? path.join(__dirname, '..', '..', '..', '..', '..') 
          : __dirname;
        await new Promise((resolve) => {
          const deletePyc = spawn('powershell', ['-Command', `Get-ChildItem -Path "${workspaceRoot}" -Include *.pyc,__pycache__ -Recurse -Force | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue`], { windowsHide: true });
          deletePyc.on('close', () => {
            resolve(); // Python bytecode cache cleared
          });
          // Timeout after 3 seconds
          setTimeout(resolve, 3000);
        });
      } catch (err) {
        // // console.log('⚠️ Error clearing .pyc files:', err.message);
      }
      
      // Backend cleanup completed, starting Python backend
      
      // Start Python backend in development mode
      // In dev mode (npm start), __dirname is already the project root
      // In packaged mode: app → resources → Chloros-win32-x64 → dist2 → chloros-electron-app → mapirlab
      const workspaceRoot = app.isPackaged 
        ? path.join(__dirname, '..', '..', '..', '..', '..') 
        : __dirname;
      // Starting Python backend (silently)
      const pythonBackend = spawn('python', ['backend_server.py'], {
        stdio: ['ignore', 'pipe', 'pipe'],
        cwd: workspaceRoot,
        env: {
          ...process.env,
          PYTHONIOENCODING: 'utf-8',
          PYTHONUNBUFFERED: '1'
        }
      });
      
      backendProcess = pythonBackend;
      
      // Forward Python stdout to debug console (only errors/warnings)
      pythonBackend.stdout.on('data', (data) => {
        const message = data.toString();
        // Only log errors, warnings, and critical messages (not verbose startup info)
        if (message.includes('❌') || message.includes('⚠️') || message.includes('ERROR') || message.includes('WARNING')) {
          // // console.log('[PYTHON]', message);
        }
        safeDebugSend({
          type: 'info',
          message: message.trim()
        });
      });
      
      // Forward Python stderr to debug console (filter out Ray SIGTERM message)
      pythonBackend.stderr.on('data', (data) => {
        const message = data.toString();
        
        // Filter out Ray's SIGTERM handler warning (harmless informational message)
        if (message.includes('SIGTERM handler is not set because current thread is not the main thread')) {
          return; // Skip this message
        }
        
        console.error('[PYTHON ERROR]', message);
        safeDebugSend({
          type: 'error',
          message: message.trim()
        });
      });
      
      pythonBackend.on('error', (error) => {
        console.error('❌ Failed to start Python backend:', error);
        safeDebugSend({
          type: 'error',
          message: `❌ Failed to start Python backend: ${error.message}`
        });
      });
      
      pythonBackend.on('close', (code) => {
        // // console.log(`Python backend exited with code ${code}`);
        safeDebugSend({
          type: 'info',
          message: `Backend process exited with code ${code}`
        });
      });
      
      return; // Python dev backend started - exit early, don't try to spawn compiled backend
    }
    
    // Comprehensive cleanup of all Chloros processes
    await cleanupAllChlorosProcesses();
    
    // Clean up port 5000 before starting backend with timeout
    // // console.log('🧹 Starting port cleanup with 5s timeout...');
    try {
      await Promise.race([
        killProcessesOnPort(5000),
        new Promise((_, reject) => setTimeout(() => reject(new Error('Port cleanup timeout')), 5000))
      ]);
      // // console.log('✅ Port cleanup completed or timed out, continuing...');
    } catch (error) {
      // // console.log('⚠️ Port cleanup timed out, proceeding with backend startup anyway:', error.message);
    }
    
    safeDebugSend({
        type: 'info',
        message: '🧹 All Chloros processes and port 5000 cleaned up, starting backend...'
      });
    
    // Wait a moment for processes to fully terminate
    // // console.log('⏳ Waiting 2 seconds before spawning backend...');
    await new Promise(resolve => setTimeout(resolve, 2000));
    // // console.log('✅ Wait completed, proceeding to spawn backend...');
    
        // CRITICAL FIX: Set working directory for standalone Nuitka backend
        // Standalone mode needs to run from its own directory to find dependencies
        const backendDir = path.dirname(backendPath);
        // // console.log(`📁 Backend directory: ${backendDir}`);
        // // console.log(`🚀 About to spawn backend: ${backendPath}`);
        // // console.log(`🚀 Working directory will be: ${backendDir}`);
        
        // Start the backend process
        // // console.log(`🚀 Calling spawn() now...`);
        backendProcess = spawn(backendPath, [], {
          stdio: ['ignore', 'pipe', 'pipe'],
          cwd: backendDir, // CRITICAL: Set working directory for standalone mode
          maxBuffer: 50 * 1024 * 1024, // 50MB buffer for stdout/stderr
          env: {
            ...process.env,
            PYTHONIOENCODING: 'utf-8',
            PYTHONUTF8: '1',
            LC_ALL: 'en_US.UTF-8',
            CHLOROS_DEBUG: '1',
            CHLOROS_VERBOSE: '1',
            CHLOROS_NO_AUTO_PROCESSING: '1',
            CHLOROS_NO_AUTO_PROJECT: '1',
            CHLOROS_MANUAL_MODE: '1',
            // Ray optimization for faster startup
            RAY_DISABLE_IMPORT_WARNING: '1',
            RAY_DISABLE_RUNTIME_METRICS: '1',
            RAY_LOG_TO_STDERR: '0',
            RAY_OBJECT_STORE_ALLOW_SLOW_STORAGE: '1',
            RAY_ENABLE_WINDOWS_OR_OSX_CLUSTER: '0',
            RAY_DISABLE_TELEMETRY: '1',
            // Python optimization
            PYTHONOPTIMIZE: '2',
            PYTHONDONTWRITEBYTECODE: '1',
            PYTHONUNBUFFERED: '1',
            // Numba optimization  
            NUMBA_DISABLE_JIT: '0',
            NUMBA_CACHE_DIR: process.env.TEMP || 'C:\\temp',
            // Threading optimization
            OMP_NUM_THREADS: '4',
            OPENBLAS_NUM_THREADS: '4',
            MKL_NUM_THREADS: '4'
          }
        });
    
    if (backendProcess && backendProcess.pid) {
      // // console.log(`🚀 Backend process started with PID: ${backendProcess.pid}`);
    } else {
      console.error(`❌ Backend process spawn() returned but no PID!`);
      console.error(`❌ backendProcess:`, backendProcess);
    }
    
    // Add error event listener for spawn failures
    backendProcess.on('error', (error) => {
      console.error(`❌ Backend process spawn error:`, error);
      safeDebugSend({
          type: 'error',
          message: `❌ Backend spawn error: ${error.message}`
        });
    });
    
    // Forward backend output to debug console
    backendProcess.stdout.on('data', (data) => {
      const output = data.toString();
      // // console.log('[BACKEND]', output);
      
      safeDebugSend({
          type: 'info',
          message: `[BACKEND] ${output}`
        });
    });
    
    backendProcess.stderr.on('data', (data) => {
      const output = data.toString();
      
      // Filter out Ray's SIGTERM handler warning (harmless informational message)
      if (output.includes('SIGTERM handler is not set because current thread is not the main thread')) {
        return; // Skip this message
      }
      
      console.error('[BACKEND ERROR]', output);
      
      safeDebugSend({
          type: 'error',
          message: `[BACKEND ERROR] ${output}`
        });
    });
    
        backendProcess.on('close', (code) => {
          // // console.log(`🔚 Backend process closed with code: ${code}`);
          
          if (debugConsoleWindow && !debugConsoleWindow.isDestroyed()) {
            let message = `🔚 Backend process closed with code: ${code}`;
            if (code !== 0) {
              message += ' (Port 5000 may be in use - try closing other applications using this port)';
            }
            safeDebugSend({
              type: code === 0 ? 'success' : 'error',
              message: message
            });
          }
          
          backendProcess = null;
        });
    
    // Send success message
    safeDebugSend({
        type: 'success',
        message: `✅ Backend process started successfully (PID: ${backendProcess.pid})`
      });
    
  } catch (error) {
    console.error('❌ Failed to start backend:', error);
    
    safeDebugSend({
        type: 'error',
        message: `❌ Failed to start backend: ${error.message}`
      });
  }
}

function createDebugConsoleWindow() {
  debugConsoleWindow = new BrowserWindow({
    width: 800,
    height: 600,
    x: 100,
    y: 100,
    title: 'Chloros Debug Console',
    icon: path.join(__dirname, 'ui', 'corn_logo_single_256.ico'),
    backgroundColor: '#1e1e1e',
    alwaysOnTop: false,
    show: true,
    skipTaskbar: false,
    webPreferences: {
      nodeIntegration: true, // Keep enabled for debug console only
      contextIsolation: false, // Keep disabled for debug console only
      webSecurity: true, // Enable security
      sandbox: false
    }
  });
  
  // Explicitly ensure window is not always on top
  debugConsoleWindow.setAlwaysOnTop(false);
  
  // Allow closing debug console
  debugConsoleWindow.on('close', () => {
    debugConsoleWindow = null;
  });

  // Use minimal, bulletproof HTML that can't crash
  const debugHtml = `<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Chloros Debug Console</title>
    <style>
        * {
            box-sizing: border-box;
        }
        html, body { 
            margin: 0;
            padding: 0;
            width: 100%;
            height: 100%;
            overflow: hidden;
        }
        body { 
            font-family: 'Courier New', monospace; 
            background: #1e1e1e; 
            color: #ffffff; 
            padding: 20px; 
            font-size: 12px;
            display: flex;
            flex-direction: column;
        }
        .header {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
            flex-shrink: 0;
        }
        .btn {
            padding: 8px 16px;
            background: #007acc;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            font-weight: bold;
        }
        .btn:hover { background: #005a9e; }
        .btn:active { background: #004578; }
        #output {
            background: #2d2d2d;
            border: 1px solid #555;
            padding: 15px;
            flex: 1;
            overflow-y: auto;
            overflow-x: hidden;
            white-space: pre-wrap;
            word-wrap: break-word;
            font-family: 'Courier New', monospace;
            font-size: 11px;
            line-height: 1.4;
            min-height: 0;
        }
        .log-info { color: #ffffff; }
        .log-success { color: #4CAF50; font-weight: bold; }
        .log-warning { color: #FF9800; font-weight: bold; }
        .log-error { color: #F44336; font-weight: bold; }
        .log-processing { color: #2196F3; font-weight: bold; background: rgba(33, 150, 243, 0.1); }
        .timestamp { color: #888; font-size: 10px; }
    </style>
</head>
<body>
    <div class="header">
        <button class="btn" onclick="copyLog()">Copy</button>
        <button class="btn" onclick="clearOutput()">Clear</button>
        <button class="btn" onclick="restartBackend()">Restart Backend</button>
        <button class="btn" onclick="killAllProcesses()">Kill All</button>
        <button class="btn" onclick="checkBackendStatus()">Check Status</button>
    </div>
    <div id="output"></div>

    <script>
        const { ipcRenderer } = require('electron');
        
        function addLogLine(type, message) {
            const output = document.getElementById('output');
            if (!output) return;
            
            const timestamp = new Date().toLocaleTimeString();
            const line = document.createElement('div');
            line.innerHTML = '<span class="timestamp">[' + timestamp + ']</span> ' + escapeHtml(message);
            line.className = 'log-' + type;
            output.appendChild(line);
            output.scrollTop = output.scrollHeight;
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        async function copyLog() {
            try {
                const output = document.getElementById('output');
                
                // Read ALL text from the output div at once (same as manual Ctrl+C)
                const text = output.innerText || output.textContent;
                const lineCount = text.split('\\n').length;
                const sizeKB = Math.round(text.length / 1024);
                
                // Use Electron's clipboard module - NO SIZE LIMITS!
                const { clipboard } = require('electron');
                clipboard.writeText(text);
                
                addLogLine('success', '✅ Copied ' + lineCount + ' lines (' + sizeKB + ' KB) to clipboard');
            } catch (error) {
                addLogLine('error', '❌ Copy failed: ' + error.message);
            }
        }
        
        function clearOutput() {
            document.getElementById('output').innerHTML = '';
            addLogLine('info', 'Debug console cleared');
        }
        
        async function restartBackend() {
            addLogLine('warning', 'Requesting backend restart...');
            try {
                await ipcRenderer.invoke('restart-backend');
            } catch (error) {
                addLogLine('error', 'Failed to restart backend: ' + error.message);
            }
        }
        
        async function killAllProcesses() {
            addLogLine('warning', 'Requesting process cleanup...');
            try {
                await ipcRenderer.invoke('kill-all-processes');
            } catch (error) {
                addLogLine('error', 'Failed to kill processes: ' + error.message);
            }
        }
        
        async function checkBackendStatus() {
            addLogLine('info', 'Checking backend status...');
            try {
                await ipcRenderer.invoke('check-backend-status');
            } catch (error) {
                addLogLine('error', 'Failed to check status: ' + error.message);
            }
        }
        
        // Listen for backend debug output
        ipcRenderer.on('backend-debug-output', (event, data) => {
            addLogLine(data.type, data.message);
        });
        
        // Initial messages
        addLogLine('success', 'Debug console initialized');
        addLogLine('info', 'Waiting for backend messages...');
    </script>
</body>
</html>`;
    
  // Load the debug console HTML
  debugConsoleWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(debugHtml)}`);
}

async function createMainWindow() {
  // Prevent creating multiple main windows
  if (mainWindow && !mainWindow.isDestroyed()) {
    // // console.log('⚠️ Main window already exists, focusing it');
    mainWindow.focus();
    return;
  }
  
  try {
    // Load saved window state
    const savedState = await loadWindowState();
    
    // Set default dimensions and position
    const defaultWidth = 1200;
    const defaultHeight = 640;
    const primaryDisplay = screen.getPrimaryDisplay();
    const { width: screenWidth, height: screenHeight } = primaryDisplay.workAreaSize;
    
    // Calculate centered position as fallback
    const defaultX = Math.round((screenWidth - defaultWidth) / 2);
    const defaultY = Math.round((screenHeight - defaultHeight) / 2);
    
    // Use saved state or defaults
    const windowOptions = {
      width: savedState?.width || defaultWidth,
      height: savedState?.height || defaultHeight,
      x: savedState?.x ?? defaultX,
      y: savedState?.y ?? defaultY,
      frame: false, // Frameless window
      show: false, // Don't show until ready
      title: 'Chloros', // Set proper application title
      icon: path.join(__dirname, 'ui', 'corn_logo_single_256.ico'), // Set application icon
      webPreferences: {
        nodeIntegration: false, // Disable for security
        contextIsolation: true, // Enable for security - use contextBridge in preload
        enableRemoteModule: false, // Disable for security
        webSecurity: true, // Enable web security
        allowRunningInsecureContent: false, // Disable insecure content
        preload: path.join(__dirname, 'preload.js'),
        // Additional stability flags to prevent renderer crashes
        sandbox: false, // Keep disabled for compatibility with native modules
        backgroundThrottling: false, // Don't throttle background
        devTools: true // Allow DevTools in development
      },
      backgroundColor: '#000000' // Match your original black background
    };
    
    mainWindow = new BrowserWindow(windowOptions);
    
    // DevTools can be manually opened with Ctrl+Shift+I when needed
    // Note: Chrome autofill errors are normal/harmless when DevTools is open
    
    // Restore maximized state if it was maximized before
    if (savedState?.isMaximized) {
      mainWindow.maximize();
    }
    
    // Main window created successfully (silently)
    
    // Close splash window if it exists
    if (splashWindow && !splashWindow.isDestroyed()) {
      splashWindow.close();
      splashWindow = null;
      // Splash window closed
    }
    
    // Show the main window immediately
    mainWindow.show();
    mainWindow.focus();
    // Main window shown and focused
    
    // Create debug console window (HIDDEN - logs now shown in main UI sidebar)
    // createDebugConsoleWindow();
    
  } catch (error) {
    console.error('Failed to create main window:', error);
    return;
  }

  // Load the Chloros UI directly for now (Flask backend can be added later)
  // Silently loading UI from main HTML file
  
  // Use absolute path that works in both dev and packaged modes
  const htmlFile = path.join(__dirname, 'ui', 'main.html');
  
  // IMPORTANT: Wait for window to be fully initialized before loading HTML
  // This prevents GPU context errors from interfering with file loading
  // Increased to 1000ms to ensure GPU context errors have fully settled
  setTimeout(() => {
    // Window ready, now loading HTML (waited 1s for GPU context to settle)
    
    // Retry mechanism for UI loading (network service may need to restart)
    let retryCount = 0;
    const maxRetries = 3;
    
    const loadUI = () => {
      mainWindow.loadFile(htmlFile).then(() => {
        // UI loaded successfully (silent)
      
        // Close splash window after successful load
        if (splashWindow && !splashWindow.isDestroyed()) {
          splashWindow.close();
          splashWindow = null;
          // Splash window closed after UI load
        }
      }).catch(error => {
        console.error(`❌ Failed to load UI file (attempt ${retryCount + 1}/${maxRetries}):`, error);
        console.error('❌ Error details:', error.message);
        console.error('❌ Tried to load:', htmlFile);
        console.error('❌ __dirname:', __dirname);
        console.error('❌ CWD:', process.cwd());
        
        // Retry if network service crashed and we haven't exhausted retries
        if (retryCount < maxRetries) {
          retryCount++;
          // // console.log(`⏳ Retrying UI load in 2 seconds (network service may be restarting)...`);
          setTimeout(loadUI, 2000); // Wait 2s for network service to restart
          return;
        }
        
        // All retries exhausted - load fallback HTML
        console.error('❌ All UI load retries exhausted, showing fallback');
        const fallbackHtml = `
        <!DOCTYPE html>
        <html>
        <head>
            <title>Chloros</title>
            <style>
                body { 
                    background: #1e1e1e; 
                    color: white; 
                    font-family: Arial, sans-serif; 
                    padding: 20px;
                    margin: 0;
                }
                .error { color: #ff6b6b; }
                .info { color: #4ecdc4; }
            </style>
        </head>
        <body>
            <h1 class="info">Chloros Application</h1>
            <p class="error">Failed to load main UI file: ui/main.html</p>
            <p>Error: ${error.message}</p>
            <p>Please check that the UI files are properly included in the build.</p>
        </body>
        </html>`;
        
        mainWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(fallbackHtml)}`);
      });
    };
    
    // Start the UI loading with retry mechanism
    loadUI();
  }, 1000); // Wait 1000ms (1 second) for window to be fully initialized and GPU context to settle

  // Show main window when ready and close splash
  mainWindow.once('ready-to-show', () => {
    // Main window ready-to-show event fired
    if (splashWindow) {
      // Closing splash window
      splashWindow.close();
    }
    // Showing and focusing main window
    mainWindow.show();
    mainWindow.focus();
  });

  // Add additional event handlers for debugging
  mainWindow.webContents.once('did-finish-load', () => {
    // Main window did-finish-load event fired (silently)
    // Ensure window is shown even if ready-to-show doesn't fire
    if (!mainWindow.isVisible()) {
      // Window not visible, forcing show
      if (splashWindow) {
        splashWindow.close();
      }
      mainWindow.show();
      mainWindow.focus();
    }
  });

  // Save window state when it changes
  let saveTimeout;
  const debouncedSave = () => {
    if (saveTimeout) clearTimeout(saveTimeout);
    saveTimeout = setTimeout(() => {
      if (mainWindow && !mainWindow.isDestroyed()) {
        saveWindowState(mainWindow);
      }
    }, 500); // Debounce saves to avoid too frequent writes
  };

  // Listen for window state changes
  mainWindow.on('resize', debouncedSave);
  mainWindow.on('move', debouncedSave);
  mainWindow.on('maximize', debouncedSave);
  mainWindow.on('unmaximize', debouncedSave);
  
  // Save final state before closing
  mainWindow.on('close', () => {
    if (saveTimeout) clearTimeout(saveTimeout);
    if (mainWindow && !mainWindow.isDestroyed()) {
      // Use synchronous save for close event to ensure it completes
      try {
        const bounds = mainWindow.getBounds();
        const state = {
          x: bounds.x,
          y: bounds.y,
          width: bounds.width,
          height: bounds.height,
          isMaximized: mainWindow.isMaximized(),
          isMinimized: mainWindow.isMinimized(),
          lastSaved: new Date().toISOString()
        };
        
        require('fs').writeFileSync(windowStateFile, JSON.stringify(state, null, 2));
        // Final window state saved silently
      } catch (error) {
        console.error('🪟 Failed to save final window state:', error);
      }
    }
  });

  mainWindow.on('closed', () => {
    // // console.log('🪟 Main window closed');
    
    // Close debug console when main window closes
    if (debugConsoleWindow && !debugConsoleWindow.isDestroyed()) {
      debugConsoleWindow.close();
      debugConsoleWindow = null;
      // // console.log('🌟 Debug console closed with main window');
    }
    
    mainWindow = null;
  });

  // Listen for maximize/restore events to update button state
  mainWindow.on('maximize', () => {
    // // console.log('🪟 Window maximized');
    if (mainWindow && !mainWindow.isDestroyed() && mainWindow.webContents && !mainWindow.webContents.isDestroyed()) {
      mainWindow.webContents.send('window-state-changed', { isMaximized: true });
    }
  });

  mainWindow.on('unmaximize', () => {
    // // console.log('🪟 Window restored');
    if (mainWindow && !mainWindow.isDestroyed() && mainWindow.webContents && !mainWindow.webContents.isDestroyed()) {
      mainWindow.webContents.send('window-state-changed', { isMaximized: false });
    }
  });

  // Add error handling
  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
    // Suppress ERR_ABORTED (-3) - this is normal during navigation/reloads
    if (errorCode !== -3) {
      console.error('Main window failed to load:', errorCode, errorDescription);
    }
  });

  // Open external links in default browser
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });
}

function startPythonServer() {
  // Skip Python server - use original Chloros backend
  // // console.log('Using original Chloros backend - no separate Python server needed');
}

// Express server removed - using Flask backend directly

// Duplicate IPC handlers removed - using the ones defined above

// App event handlers
// IMPORTANT: Do cleanup BEFORE single-instance check to clear stale locks
// Silently clean up any stale locks

// Kill any existing Chloros processes first (synchronous approximation)
try {
  const { execSync } = require('child_process');
  const currentPid = process.pid;
  
  // Kill chloros-backend.exe processes
  try {
    const backends = execSync('tasklist /FI "IMAGENAME eq chloros-backend.exe" /FO CSV /NH 2>nul', { 
      encoding: 'utf-8', 
      timeout: 2000,
      windowsHide: true,
      stdio: ['pipe', 'pipe', 'ignore']  // Suppress stderr completely
    });
    if (backends && !backends.includes('INFO: No tasks')) {
      // // console.log('🗡️ Found existing backend processes, killing them...');
      execSync('taskkill /F /IM chloros-backend.exe 2>nul', { 
        timeout: 2000,
        windowsHide: true,
        stdio: ['pipe', 'pipe', 'ignore']
      });
      // // console.log('✅ Killed existing backend processes');
    }
  } catch (e) {
    // No backends running, that's fine
  }
  
  // Kill Chloros.exe processes except this one
  try {
    const apps = execSync('tasklist /FI "IMAGENAME eq Chloros.exe" /FO CSV /NH 2>nul', { 
      encoding: 'utf-8', 
      timeout: 2000,
      windowsHide: true,
      stdio: ['pipe', 'pipe', 'ignore']  // Suppress stderr completely
    });
    if (apps && !apps.includes('INFO: No tasks')) {
      // // console.log('🗡️ Found existing Chloros processes, killing them (except current PID)...');
      // Get all PIDs and kill except current
      const lines = apps.split('\n');
      lines.forEach(line => {
        const match = line.match(/"Chloros.exe","(\d+)"/);
        if (match && match[1] !== String(currentPid)) {
          try {
            execSync(`taskkill /F /PID ${match[1]} 2>nul`, { 
              timeout: 1000,
              windowsHide: true,
              stdio: ['pipe', 'pipe', 'ignore']
            });
            // // console.log(`✅ Killed stale Chloros process PID ${match[1]}`);
          } catch (e) {
            // Already dead, ignore
          }
        }
      });
    }
  } catch (e) {
    // No apps running, that's fine
  }
  
  // Pre-launch cleanup completed
} catch (error) {
  // // console.log('⚠️ Pre-launch cleanup had issues (continuing anyway):', error.message);
}

// Now request single instance lock (after cleanup)
const gotTheLock = app.requestSingleInstanceLock();

if (!gotTheLock) {
  // Another instance is STILL running after cleanup - probably legitimately running
  // // console.log('⚠️ Another instance is legitimately running, quitting...');
  hasSingleInstanceLock = false;
  app.quit();
  // Exit immediately to prevent any further initialization
  process.exit(0);
} else {
  hasSingleInstanceLock = true; // This is the primary instance
  
  // This is the first instance, handle second-instance attempts
  app.on('second-instance', (event, commandLine, workingDirectory) => {
    // // console.log('⚠️ Second instance attempted, focusing existing window');
    // Focus the existing main window if it exists
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });
}

// Quit when all windows are closed (standard Electron behavior on Windows)
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.whenReady().then(async () => {
  // Starting Chloros Electron Application
  
  // ========================================
  // CATASTROPHIC FAILURE HANDLER
  // ========================================
  // Safety net: If app crashes within 5 seconds and no event handlers fire,
  // force a restart with GPU disabled. This handles edge cases on very low VRAM systems.
  let appStableTimerFired = false;
  let catastrophicFailureHandled = false;
  
  const catastrophicFailureTimer = setTimeout(() => {
    appStableTimerFired = true;
    // App stable - catastrophic failure handler disabled
  }, 5000);
  
  // DON'T auto-clear GPU crash flags - if GPU crashes, it's proven unreliable
  // User can manually delete flags if they want to test GPU again
  if (gpuDisabled || gpuRecoveryMode) {
    // // console.log('ℹ️  GPU crash flags will persist - GPU has proven unstable on this system');
  } else {
    // // console.log('✅ No GPU crash flags present - GPU is stable');
  }
  
  // Monitor for unexpected exit
  process.on('exit', (code) => {
    if (!appStableTimerFired && !catastrophicFailureHandled && !emergencyRestartInProgress) {
      // // console.log('💀 CATASTROPHIC FAILURE: App exiting within 5 seconds of startup');
      // // console.log(`   Exit code: ${code}`);
      // // console.log('   Event handlers may have failed - forcing restart with GPU disabled');
      
      catastrophicFailureHandled = true;
      
      // Create both crash flags to ensure GPU is disabled on restart
      try {
        if (!fsSync.existsSync(userDataPath)) {
          fsSync.mkdirSync(userDataPath, { recursive: true });
        }
        fsSync.writeFileSync(gpuCrashFlagPath, `CATASTROPHIC FAILURE: ${new Date().toISOString()}`);
        fsSync.writeFileSync(gpuRecoveryAttemptPath, `SKIPPED - CATASTROPHIC: ${new Date().toISOString()}`);
        // // console.log('   💀 Emergency crash flags created');
      } catch (err) {
        console.error('   ⚠️ Could not create emergency flags:', err);
      }
      
      // Spawn new instance - this must be synchronous
      try {
        const exePath = process.execPath;
        const args = process.argv.slice(1);
        
        // Use spawnSync for synchronous spawning during exit
        const { spawnSync } = require('child_process');
        spawnSync(exePath, args, {
          detached: true,
          stdio: 'ignore',
          windowsHide: false
        });
        
        // // console.log('   🔄 Emergency restart spawned');
      } catch (spawnErr) {
        console.error('   ❌ Emergency spawn failed:', spawnErr);
      }
    }
  });
  
  // Immediate cleanup on startup to prevent multiple instances
  // Silently cleaning up any stale processes
  await cleanupAllChlorosProcesses();
  await cleanupNuitkaTempFolders();
  
  // CRITICAL: Clear ALL Electron caches to force fresh HTML/JS loads and recover from crashes
  // Silently clearing caches in background
  
  // Run comprehensive cache clearing in background, don't block startup
  (async () => {
    try {
      const session = require('electron').session;
      const defaultSession = session.defaultSession;
      
      // 1. Clear HTTP cache with timeout
      await Promise.race([
        defaultSession.clearCache(),
        new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), 3000))
      ]).catch(() => {});
      
      // 2. Clear GPU/code cache (critical for crash recovery)
      await Promise.race([
        defaultSession.clearCodeCaches({ urls: [] }), // Empty array clears ALL code caches
        new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), 3000))
      ]).catch(() => {});
      
      // 3. Clear storage data with timeout
      await Promise.race([
        defaultSession.clearStorageData({
          storages: ['appcache', 'cookies', 'filesystem', 'indexdb', 'localstorage', 'websql', 'serviceworkers', 'cachestorage']
        }),
        new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), 3000))
      ]).catch(() => {});
      
      // 4. Clear auth cache (can cause issues after crashes)
      await Promise.race([
        defaultSession.clearAuthCache(),
        new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), 1000))
      ]).catch(() => {});
      
      // Cache clearing completed silently
    } catch (error) {
      console.error('⚠️ Cache clearing failed:', error.message);
      // // console.log('  ℹ️ App will continue startup despite cache clearing failure');
    }
  })();
  
  // Don't wait for cache clearing - continue startup immediately
  
  // DISABLED: Automatic GPU cache clearing (was causing GPU initialization failures)
  // Only clear caches in GPU recovery mode, not on every boot
  
  // Enhanced GPU recovery and flag management
  if (gpuRecoveryMode) {
    // In recovery mode - aggressively clear ALL GPU caches to fix driver corruption
    // // console.log('🔧 GPU RECOVERY MODE: Performing comprehensive GPU cache clear...');
    (async () => {
      try {
        const session = require('electron').session;
        const defaultSession = session.defaultSession;
        const os = require('os');
        const pathModule = require('path');
        const fsModule = require('fs');
        
        // 1. Clear Electron GPU caches
        // // console.log('   🗑️ Clearing Electron GPU shader cache...');
        await defaultSession.clearCodeCaches({ urls: [] }).catch(() => {});
        
        // // console.log('   🗑️ Clearing Electron GPU data...');
        await defaultSession.clearStorageData({
          storages: ['shadercache', 'gpucache']
        }).catch(() => {});
        
        // 2. Clear Windows DirectX shader cache (this is often the culprit!)
        // // console.log('   🗑️ Clearing DirectX shader cache...');
        const localAppData = process.env.LOCALAPPDATA || pathModule.join(os.homedir(), 'AppData', 'Local');
        const d3dCachePath = pathModule.join(localAppData, 'D3DSCache');
        
        try {
          if (fsModule.existsSync(d3dCachePath)) {
            // Delete all files in D3DSCache
            const files = fsModule.readdirSync(d3dCachePath);
            for (const file of files) {
              try {
                fsModule.unlinkSync(pathModule.join(d3dCachePath, file));
              } catch (e) {
                // Continue even if some files are locked
              }
            }
            // // console.log('      ✅ DirectX shader cache cleared');
          }
        } catch (err) {
          // // console.log('      ⚠️ Could not clear DirectX cache:', err.message);
        }
        
        // 3. Clear GPU vendor caches (NVIDIA/AMD/Intel)
        // // console.log('   🗑️ Clearing GPU vendor caches...');
        const vendorCaches = [
          pathModule.join(localAppData, 'NVIDIA', 'DXCache'),
          pathModule.join(localAppData, 'NVIDIA', 'GLCache'),
          pathModule.join(localAppData, 'NVIDIA', 'ComputeCache'),
          pathModule.join(localAppData, 'AMD', 'DXCache'),
          pathModule.join(localAppData, 'Intel', 'DXCache'),
        ];
        
        for (const cachePath of vendorCaches) {
          try {
            if (fsModule.existsSync(cachePath)) {
              const files = fsModule.readdirSync(cachePath);
              for (const file of files) {
                try {
                  fsModule.unlinkSync(pathModule.join(cachePath, file));
                } catch (e) {
                  // Continue
                }
              }
            }
          } catch (err) {
            // Silent fail - vendor cache is optional
          }
        }
        // // console.log('      ✅ GPU vendor caches cleared');
        
        // 4. Clear OpenGL cache files
        // // console.log('   🗑️ Clearing OpenGL cache...');
        const tempDir = os.tmpdir();
        try {
          const tempFiles = fsModule.readdirSync(tempDir);
          for (const file of tempFiles) {
            if (file.includes('_gl.cache') || file.includes('mesa_shader')) {
              try {
                fsModule.unlinkSync(pathModule.join(tempDir, file));
              } catch (e) {
                // Continue
              }
            }
          }
          // // console.log('      ✅ OpenGL cache cleared');
        } catch (err) {
          // // console.log('      ⚠️ Could not clear OpenGL cache:', err.message);
        }
        
        // 5. Clear Electron's GPU cache directory
        // // console.log('   🗑️ Clearing Electron GPU cache directory...');
        const electronGpuCache = pathModule.join(app.getPath('userData'), 'GPUCache');
        try {
          if (fsModule.existsSync(electronGpuCache)) {
            const files = fsModule.readdirSync(electronGpuCache);
            for (const file of files) {
              try {
                fsModule.unlinkSync(pathModule.join(electronGpuCache, file));
              } catch (e) {
                // Continue
              }
            }
            // // console.log('      ✅ Electron GPU cache directory cleared');
          }
        } catch (err) {
          // // console.log('      ⚠️ Could not clear Electron GPU cache:', err.message);
        }
        
        // // console.log('✅ COMPREHENSIVE GPU CACHE CLEAR COMPLETED!');
        // // console.log('   - DirectX shader cache: cleared');
        // // console.log('   - GPU vendor caches: cleared');
        // // console.log('   - OpenGL cache: cleared');
        // // console.log('   - Electron GPU cache: cleared');
        // // console.log('   GPU should now work perfectly!');
        // // console.log('');
        // // console.log('ℹ️  Crash flags will remain until manually deleted');
        // // console.log('   To test GPU again, delete these files:');
        // // console.log('   - ' + gpuCrashFlagPath);
        // // console.log('   - ' + gpuRecoveryAttemptPath);
        
      } catch (err) {
        console.error('⚠️ GPU recovery failed:', err);
      }
    })();
    
  } else if (gpuDisabled) {
    // GPU disabled mode - flags will remain permanent
    // // console.log('ℹ️  GPU permanently disabled due to previous crash');
    // // console.log('   Crash flags will remain until manually deleted');
    // // console.log('   To test GPU again, delete these files and restart:');
    // // console.log('   - ' + gpuCrashFlagPath);
    // // console.log('   - ' + gpuRecoveryAttemptPath);
  }
  
  // Initialize window state file path now that app is ready
  windowStateFile = path.join(app.getPath('userData'), 'window-state.json');
  
  // Set app icon globally to prevent default Electron icon from showing
  if (process.platform === 'win32') {
    app.setAppUserModelId('com.mapirlab.chloros');
    // App User Model ID set for Windows taskbar grouping
    // and the executable's embedded icon, not app.setIcon() (which doesn't exist on Windows)
  }
  
  // Initialize backend
  backend = new ElectronBackend();
  // Backend initialized silently
  
  // Start the actual Python backend process after a short delay
  // Use a flag to prevent double-starting the backend
  let backendStarted = false;
  const tryStartBackend = (retryCount = 0) => {
    if (backendStarted) {
      // // console.log('⚠️ Backend already started, skipping duplicate call');
      return;
    }
    
    // Start backend after max 3 retries (6 seconds) even if debug console isn't ready
    // Debug console is optional and shouldn't block backend startup
    if (debugConsoleWindow && !debugConsoleWindow.isDestroyed()) {
      // // console.log('🔧 Debug console ready, starting backend...');
      backendStarted = true;
      startBackend();
    } else if (retryCount >= 3) {
      // Starting backend without debug console (optional feature)
      backendStarted = true;
      startBackend();
    } else {
      // Debug console not ready, retrying silently
      setTimeout(() => tryStartBackend(retryCount + 1), 2000);
    }
  };
  
  setTimeout(tryStartBackend, 2000); // Give debug console time to initialize
  
  try {
    // Create splash window first
    createSplashWindow();
    
    // Application initialized
  } catch (error) {
    console.error('Failed to initialize application:', error);
    app.quit();
  }

  app.on('activate', async () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createSplashWindow();
    }
  });
}).catch(error => {
  console.error('Failed to start application:', error);
  app.quit();
});

// Add process error handling
process.on('uncaughtException', (error) => {
  console.error('Uncaught Exception:', error);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
});

app.on('window-all-closed', async () => {
  // Clean up ALL Chloros processes comprehensively using PowerShell
  // // console.log('[CLEANUP] Window closed - performing comprehensive cleanup...');
  
  try {
    const { execSync } = require('child_process');
    
    // Use PowerShell to forcefully kill all backend processes (more reliable than taskkill)
    const psCommand = `Get-Process | Where-Object { $_.ProcessName -like 'chloros-backend*' } | Stop-Process -Force 2>$null`;
    
    try {
      execSync(`powershell -Command "${psCommand}"`, { 
        timeout: 5000, 
        windowsHide: true,
        stdio: ['pipe', 'pipe', 'ignore']  // Suppress stderr completely
      });
      // // console.log('[CLEANUP] ✅ Killed all backend processes using PowerShell');
    } catch (err) {
      // Ignore error if no processes found
      // // console.log('[CLEANUP] No backend processes to kill (or already dead)');
    }
    
    backendProcess = null;
  } catch (err) {
    console.error('[CLEANUP] Error during comprehensive cleanup:', err);
  }
  
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  // Clean up ALL Chloros processes comprehensively using PowerShell
  // // console.log('[CLEANUP] Before quit - performing comprehensive cleanup...');
  
  // DON'T clear GPU crash flags on exit - once GPU is proven broken, keep it disabled
  // User can manually clear flags if they fix their GPU drivers
  
  try {
    const { execSync } = require('child_process');
    
    // Use PowerShell to forcefully kill all backend processes (more reliable than taskkill)
    const psCommand = `Get-Process | Where-Object { $_.ProcessName -like 'chloros-backend*' } | Stop-Process -Force 2>$null`;
    
    try {
      execSync(`powershell -Command "${psCommand}"`, { 
        timeout: 5000, 
        windowsHide: true,
        stdio: ['pipe', 'pipe', 'ignore']  // Suppress stderr completely
      });
      // // console.log('[CLEANUP] ✅ Before quit - Killed all backend processes using PowerShell');
    } catch (err) {
      // // console.log('[CLEANUP] Before quit - No backend processes to kill (or already dead)');
    }
    
    backendProcess = null;
  } catch (err) {
    console.error('[CLEANUP] Before quit - Error during comprehensive cleanup:', err);
  }
});

// Security: Prevent new window creation
app.on('web-contents-created', (event, contents) => {
  contents.on('new-window', (event, navigationUrl) => {
    event.preventDefault();
    shell.openExternal(navigationUrl);
  });
});
