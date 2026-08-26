const { app, BrowserWindow, ipcMain, shell } = require('electron');
const path = require('path');
const fs = require('fs');
const { execFile, spawn } = require('child_process');

// Explicit Path Resolution
const projectRoot = path.resolve(__dirname, '..', '..');
const pythonScript = path.join(projectRoot, 'ai_engine', 'ipc_backend.py');
const imageSearchScript = path.join(projectRoot, 'ai_engine', 'image_search.py');

// Explicit Python venv binary resolution
const venvPython = path.resolve(projectRoot, 'ai_engine', 'venv', 'Scripts', 'python.exe');
const pythonBin = fs.existsSync(venvPython) ? venvPython : 'python';

// Explicit Database path resolution
const coreDbPath = path.resolve(projectRoot, 'backend', 'FileManager.Core', 'files.db');
const rootDbPath = path.resolve(projectRoot, 'files.db');
const resolvedDbPath = fs.existsSync(coreDbPath) ? coreDbPath : rootDbPath;

console.log(`[INIT] Electron Backend Configuration:`);
console.log(` - Project Root: ${projectRoot}`);
console.log(` - Python Binary: ${pythonBin}`);
console.log(` - IPC Backend Script: ${pythonScript}`);
console.log(` - Image Search Script: ${imageSearchScript}`);
console.log(` - Database Path: ${resolvedDbPath}`);

// Active Scan & Search Process Trackers
let activeScanProcess = null;
let activeImageSearchProcess = null;

function runPythonBackend(action, args = []) {
  return new Promise((resolve) => {
    const cmdArgs = [pythonScript, action, '--db_path', resolvedDbPath, ...args];
    console.log(`[IPC EXEC] ${pythonBin} ${cmdArgs.join(' ')}`);

    execFile(pythonBin, cmdArgs, { cwd: projectRoot, maxBuffer: 10 * 1024 * 1024 }, (error, stdout, stderr) => {
      if (stderr && stderr.trim()) {
        console.error(`[PYTHON STDERR ${action}]: ${stderr.trim()}`);
      }

      if (error) {
        console.error(`[ERROR EXEC ${action}]: ${error.message}`);
        return resolve({ error: error.message, results: [] });
      }

      try {
        const data = JSON.parse(stdout);
        resolve(data);
      } catch (e) {
        console.error(`[JSON PARSE ERROR ${action}]:`, e);
        console.error(`[RAW STDOUT ${action}]:`, stdout);
        resolve({ error: 'Failed to parse JSON response from Python backend', results: [] });
      }
    });
  });
}

function createWindow() {
  const mainWindow = new BrowserWindow({
    width: 1300,
    height: 850,
    minWidth: 1200,
    minHeight: 800,
    titleBarStyle: 'hiddenInset',
    titleBarOverlay: {
      color: '#1f493d',
      symbolColor: '#ffffff',
      height: 38,
    },
    backgroundColor: '#1f493d',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.cjs'),
    },
  });

  const devServerUrl = process.env.VITE_DEV_SERVER_URL || 'http://localhost:5173';
  const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;

  if (isDev) {
    mainWindow.loadURL(devServerUrl).catch(() => {
      setTimeout(() => {
        mainWindow.loadURL(devServerUrl);
      }, 1000);
    });
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
  }
}

// IPC Handlers
ipcMain.handle('get-drives', async () => {
  return await runPythonBackend('drives');
});

ipcMain.handle('search-files', async (event, { query, mode, drive }) => {
  // 1. CLIP Semantic Image Search
  if (mode === 'clip' || mode === 'image') {
    if (activeImageSearchProcess) {
      console.log(`[CLIP KILL] Terminating previous pending image search process...`);
      try {
        activeImageSearchProcess.kill('SIGKILL');
      } catch (e) {
        console.error(`[CLIP KILL ERROR]:`, e);
      }
      activeImageSearchProcess = null;
    }

    const cmdArgs = [imageSearchScript, '--query', query || '', '--top_k', '25', '--json', '--db_path', resolvedDbPath];
    if (drive && drive.toLowerCase() !== 'all') {
      cmdArgs.push('--drive', drive);
    }
    console.log(`[CLIP EXEC] ${pythonBin} ${cmdArgs.join(' ')}`);

    return new Promise((resolve) => {
      const child = execFile(pythonBin, cmdArgs, { cwd: projectRoot, maxBuffer: 50 * 1024 * 1024, timeout: 30000 }, (error, stdout, stderr) => {
        if (activeImageSearchProcess === child) {
          activeImageSearchProcess = null;
        }

        if (stderr && stderr.trim()) {
          console.error(`[CLIP STDERR]: ${stderr.trim()}`);
        }
        if (stdout && stdout.trim()) {
          console.log(`[CLIP STDOUT LENGTH]: ${stdout.length} bytes`);
        }

        if (error) {
          if (error.killed || error.signal === 'SIGKILL' || child.killed) {
            console.log(`[CLIP CANCELLED] Subprocess was killed or aborted.`);
            return resolve({ query, mode: 'clip', count: 0, results: [], cancelled: true });
          }
          console.error(`[CLIP SUBPROCESS ERROR / TIMEOUT]: ${error.message}`);
          return resolve({ query, mode: 'clip', count: 0, results: [], error: error.message });
        }

        try {
          let raw = (stdout || '').trim();
          const match = raw.match(/\{[\s\S]*\}/);
          if (match) {
            raw = match[0];
          }
          const data = JSON.parse(raw);
          console.log(`[CLIP SUCCESS] Returned ${data.results ? data.results.length : 0} matching image cards.`);
          resolve(data);
        } catch (e) {
          console.error(`[CLIP JSON PARSE ERROR]: ${e.message}`);
          console.error(`[CLIP RAW STDOUT]:`, stdout);
          resolve({ query, mode: 'clip', count: 0, results: [], error: 'Failed to parse JSON results' });
        }
      });
      activeImageSearchProcess = child;
    });
  }

  // 2. Text / Ollama Mode
  const args = [];
  if (query) args.push('--query', query);
  if (mode) args.push('--mode', mode);
  if (drive) args.push('--drive', drive);
  return await runPythonBackend('search', args);
});

ipcMain.handle('get-storage-analysis', async (event, { drive }) => {
  const args = [];
  if (drive) args.push('--drive', drive);
  return await runPythonBackend('storage', args);
});

ipcMain.handle('get-duplicates', async () => {
  return await runPythonBackend('duplicates');
});

ipcMain.handle('get-stats', async () => {
  return await runPythonBackend('stats');
});

// Drive Scan & Cancellation Handlers
ipcMain.handle('scan-drive', (event, { drive }) => {
  return new Promise((resolve) => {
    const targetDrive = drive || 'C:';
    const scannerPath = path.resolve(projectRoot, 'backend', 'FileManager.Core', 'bin', 'Debug', 'net9.0', 'FileManager.Core.exe');

    let cmd = 'dotnet';
    let args = ['run', '--project', path.resolve(projectRoot, 'backend', 'FileManager.Core'), '--', '--scan', targetDrive];

    if (fs.existsSync(scannerPath)) {
      cmd = scannerPath;
      args = ['--scan', targetDrive];
    }

    console.log(`[SCAN START] ${cmd} ${args.join(' ')}`);

    const child = spawn(cmd, args, { cwd: projectRoot });
    activeScanProcess = child;

    child.stdout.on('data', (data) => {
      const msg = data.toString();
      event.sender.send('scan-progress', { output: msg, drive: targetDrive });
    });

    child.stderr.on('data', (data) => {
      console.error(`[SCAN STDERR]: ${data.toString()}`);
    });

    child.on('close', (code) => {
      console.log(`[SCAN COMPLETE] Exit code: ${code}`);
      activeScanProcess = null;
      resolve({ success: code === 0, cancelled: false });
    });

    child.on('error', (err) => {
      console.error(`[SCAN ERROR]:`, err);
      activeScanProcess = null;
      resolve({ success: false, error: err.message });
    });
  });
});

ipcMain.handle('cancel-active-scan', () => {
  if (activeScanProcess && activeScanProcess.pid) {
    const pid = activeScanProcess.pid;
    console.log(`[SCAN CANCEL] Terminating active scan process tree (PID: ${pid})...`);
    try {
      execFile('taskkill', ['/pid', pid.toString(), '/f', '/t'], (err) => {
        if (err) console.error(`[TASKKILL ERROR]: ${err.message}`);
      });
      activeScanProcess.kill('SIGTERM');
    } catch (e) {
      console.error(`[SCAN KILL ERROR]:`, e);
    }
    activeScanProcess = null;
    return { cancelled: true };
  }
  return { cancelled: false };
});

ipcMain.handle('open-path', async (event, filePath) => {
  if (!filePath) return false;
  try {
    const res = await shell.openPath(filePath);
    if (res) {
      shell.showItemInFolder(filePath);
    }
    return true;
  } catch (err) {
    console.error('Error opening path:', err);
    return false;
  }
});

ipcMain.handle('open-folder', async (event, filePath) => {
  if (!filePath) return false;
  try {
    shell.showItemInFolder(filePath);
    return true;
  } catch (err) {
    console.error('Error opening folder:', err);
    return false;
  }
});

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
