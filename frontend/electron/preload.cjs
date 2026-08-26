const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  platform: process.platform,
  getDrives: () => ipcRenderer.invoke('get-drives'),
  searchFiles: (params) => ipcRenderer.invoke('search-files', params || {}),
  getStorageAnalysis: (params) => ipcRenderer.invoke('get-storage-analysis', params || {}),
  getDuplicates: () => ipcRenderer.invoke('get-duplicates'),
  getStats: () => ipcRenderer.invoke('get-stats'),
  openPath: (filePath) => ipcRenderer.invoke('open-path', filePath),
  openFolder: (filePath) => ipcRenderer.invoke('open-folder', filePath),
  scanDrive: (drive) => ipcRenderer.invoke('scan-drive', { drive }),
  cancelActiveScan: () => ipcRenderer.invoke('cancel-active-scan'),
  onScanProgress: (callback) => {
    const handler = (event, data) => callback(data);
    ipcRenderer.on('scan-progress', handler);
    return () => ipcRenderer.removeListener('scan-progress', handler);
  },
});
