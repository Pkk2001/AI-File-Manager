import React, { useState, useEffect, useCallback, useRef } from 'react';
import type { ActiveTab, SearchMode, DriveInfo, FileResultItem, StorageAnalysisData, DuplicateData, SystemStats } from './types';
import { TopRibbon } from './components/TopRibbon';
import { LeftDriveTree } from './components/LeftDriveTree';
import { SearchResultsView } from './components/SearchResultsView';
import { StorageAnalyzerView } from './components/StorageAnalyzerView';
import { DuplicateView } from './components/DuplicateView';
import { StatusBar } from './components/StatusBar';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<ActiveTab>('search');
  const [searchMode, setSearchMode] = useState<SearchMode>('text');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedDrive, setSelectedDrive] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Scan & Progress States
  const [isScanning, setIsScanning] = useState<boolean>(false);
  const [scanCount, setScanCount] = useState<number>(0);
  const [scanElapsedTime, setScanElapsedTime] = useState<number>(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Data States
  const [drives, setDrives] = useState<DriveInfo[]>([]);
  const [searchResults, setSearchResults] = useState<FileResultItem[]>([]);
  const [storageData, setStorageData] = useState<StorageAnalysisData | null>(null);
  const [duplicateData, setDuplicateData] = useState<DuplicateData | null>(null);
  const [systemStats, setSystemStats] = useState<SystemStats | null>(null);

  // Check if running in Electron environment
  const isElectron = !!window.electronAPI;

  // Load Initial Drives and Stats
  const loadSystemInfo = useCallback(async () => {
    if (isElectron && window.electronAPI) {
      try {
        const driveList = await window.electronAPI.getDrives();
        setDrives(driveList || []);

        const stats = await window.electronAPI.getStats();
        setSystemStats(stats);
      } catch (err) {
        console.error('Error loading system drives/stats:', err);
      }
    } else {
      // Mock Fallback for Browser Preview
      setDrives([
        { drive: 'C:\\', label: 'Windows OS', format: 'NTFS', total: 512000000000, used: 380000000000, free: 132000000000, used_pct: 74.2 },
        { drive: 'D:\\', label: 'Data Disk', format: 'NTFS', total: 1024000000000, used: 640000000000, free: 384000000000, used_pct: 62.5 },
        { drive: 'F:\\', label: 'New Volume', format: 'NTFS', total: 107374182400, used: 86237000000, free: 21137182400, used_pct: 80.3 },
      ]);
      setSystemStats({
        total_files: 1447747,
        db_size: 524283904,
        formatted_db_size: '500.00 MB',
        db_path: 'F:\\AI-File-Manager\\files.db'
      });
    }
  }, [isElectron]);

  // Execute Search
  const executeSearch = useCallback(async () => {
    setIsLoading(true);
    if (isElectron && window.electronAPI) {
      try {
        const res = await window.electronAPI.searchFiles({
          query: searchQuery,
          mode: searchMode,
          drive: selectedDrive || undefined,
        });
        if (res.cancelled) {
          console.log('Search response was cancelled (superseded by another query).');
          return;
        }
        if (res.error) {
          console.error('Search error from backend:', res.error);
          alert(`Search Error: ${res.error}`);
          setSearchResults([]);
        } else {
          setSearchResults(res.results || []);
        }
      } catch (err: any) {
        console.error('Error executing search:', err);
        alert(`Search Failed: ${err.message || err}`);
        setSearchResults([]);
      }
    } else {
      // Browser Mock Results
      if (searchMode === 'image') {
        setSearchResults([
          { name: 'white_supercar_ferrari.jpg', path: 'F:\\Images\\Supercars\\white_supercar_ferrari.jpg', size: 2450000, formatted_size: '2.34 MB', extension: '.jpg', category: 'Images', modified: '2026-08-01', score: 96.5 },
          { name: 'porsche_911_gt3_white.jpg', path: 'F:\\Images\\Supercars\\porsche_911_gt3_white.jpg', size: 3120000, formatted_size: '2.98 MB', extension: '.jpg', category: 'Images', modified: '2026-08-05', score: 92.1 },
          { name: 'lamborghini_huracan_white.png', path: 'C:\\Users\\prabh\\Pictures\\lamborghini_huracan_white.png', size: 4180000, formatted_size: '3.99 MB', extension: '.png', category: 'Images', modified: '2026-08-12', score: 89.4 },
        ]);
      } else {
        setSearchResults([
          { name: 'Inception.2010.1080p.mkv', path: 'F:\\Videos\\Inception.2010.1080p.mkv', size: 1986560000, formatted_size: '1.85 GB', extension: '.mkv', category: 'Videos', modified: '2026-08-01', score: 100 },
          { name: 'minecraft_save.zip', path: 'C:\\Users\\prabh\\Downloads\\minecraft_save.zip', size: 45200000, formatted_size: '43.10 MB', extension: '.zip', category: 'Archives', modified: '2026-08-10', score: 98.5 },
        ]);
      }
    }
    setIsLoading(false);
  }, [isElectron, searchQuery, searchMode, selectedDrive]);

  // Execute Storage Analysis
  const loadStorageAnalysis = useCallback(async () => {
    setIsLoading(true);
    if (isElectron && window.electronAPI) {
      try {
        const res = await window.electronAPI.getStorageAnalysis({
          drive: selectedDrive || undefined
        });
        setStorageData(res);
      } catch (err) {
        console.error('Error loading storage analysis:', err);
      }
    } else {
      setStorageData({
        drives: drives,
        categories: [
          { category: 'Other', count: 111328, size: 56210000000, formatted_size: '52.35 GB', percentage: 69.2 },
          { category: 'Videos', count: 95, size: 12550000000, formatted_size: '11.69 GB', percentage: 15.4 },
          { category: 'Executable/Apps', count: 439, size: 5850000000, formatted_size: '5.45 GB', percentage: 7.2 },
          { category: 'Archives', count: 232, size: 4050000000, formatted_size: '3.78 GB', percentage: 5.0 },
          { category: 'Source Code', count: 95976, size: 1015000000, formatted_size: '968.31 MB', percentage: 1.2 },
        ],
        top_extensions: [
          { extension: '.bsa', count: 80, size: 17985600000, formatted_size: '16.75 GB' },
          { extension: '.mp4', count: 71, size: 12391000000, formatted_size: '11.54 GB' },
        ],
        largest_files: [
          { name: 'resources.assets.resS', path: 'F:\\Albion\\game\\Albion-Online_Data\\resources.assets.resS', size: 3038674944, formatted_size: '2.83 GB', category: 'Other', modified: '2026-08-01', extension: '.resS', score: 100 },
        ]
      });
    }
    setIsLoading(false);
  }, [isElectron, selectedDrive, drives]);

  // Load Duplicates
  const loadDuplicates = useCallback(async () => {
    setIsLoading(true);
    if (isElectron && window.electronAPI) {
      try {
        const res = await window.electronAPI.getDuplicates();
        setDuplicateData(res);
      } catch (err) {
        console.error('Error loading duplicates:', err);
      }
    } else {
      setDuplicateData({
        groups: [
          {
            hash: 'a1b2c3d4e5',
            size: 3261137,
            formatted_size: '3.11 MB',
            count: 2,
            waste_bytes: 3261137,
            formatted_waste: '3.11 MB',
            files: [
              { name: 'Minecraft_Screenshot_1.png', path: 'C:\\Users\\prabh\\Videos\\Captures\\Minecraft_Screenshot_1.png', size: 3261137, formatted_size: '3.11 MB', extension: '.png', category: 'Images', modified: '2026-08-05', score: 100 },
              { name: 'Minecraft_Screenshot_Copy.png', path: 'D:\\Backups\\Minecraft_Screenshot_Copy.png', size: 3261137, formatted_size: '3.11 MB', extension: '.png', category: 'Images', modified: '2026-08-05', score: 100 },
            ]
          }
        ],
        total_waste_bytes: 3261137,
        formatted_waste: '3.11 MB'
      });
    }
    setIsLoading(false);
  }, [isElectron]);

  // Handle Scan Drive Start & Progress
  const handleScanDrive = async () => {
    setIsScanning(true);
    setScanCount(0);
    setScanElapsedTime(0);

    timerRef.current = setInterval(() => {
      setScanElapsedTime(prev => prev + 1);
    }, 1000);

    if (isElectron && window.electronAPI) {
      try {
        const res = await window.electronAPI.scanDrive(selectedDrive || 'C:');
        if (res.success || res.cancelled) {
          loadSystemInfo();
        }
      } catch (err) {
        console.error('Error during drive scan:', err);
      }
    } else {
      // Mock Browser Scan
      setTimeout(() => {
        setIsScanning(false);
      }, 5000);
    }

    if (timerRef.current) clearInterval(timerRef.current);
    setIsScanning(false);
  };

  // Handle Cancel Active Scan
  const handleCancelScan = async () => {
    if (isElectron && window.electronAPI) {
      try {
        await window.electronAPI.cancelActiveScan();
      } catch (err) {
        console.error('Error cancelling active scan:', err);
      }
    }
    if (timerRef.current) clearInterval(timerRef.current);
    setIsScanning(false);
  };

  // Register Scan Progress Listener
  useEffect(() => {
    if (isElectron && window.electronAPI) {
      const removeListener = window.electronAPI.onScanProgress(() => {
        setScanCount(prev => prev + 125);
      });
      return () => {
        removeListener();
      };
    }
  }, [isElectron]);

  // Initialize System Info
  useEffect(() => {
    loadSystemInfo();
  }, [loadSystemInfo]);

  // Trigger search / data load on tab change or drive select
  useEffect(() => {
    if (activeTab === 'search') {
      executeSearch();
    } else if (activeTab === 'storage') {
      loadStorageAnalysis();
    } else if (activeTab === 'duplicates') {
      loadDuplicates();
    }
  }, [activeTab, selectedDrive, executeSearch, loadStorageAnalysis, loadDuplicates]);

  // Shell Handlers
  const handleOpenPath = (path: string) => {
    if (isElectron && window.electronAPI) {
      window.electronAPI.openPath(path);
    } else {
      alert(`Opening path: ${path}`);
    }
  };

  const handleOpenFolder = (path: string) => {
    if (isElectron && window.electronAPI) {
      window.electronAPI.openFolder(path);
    } else {
      alert(`Showing folder for: ${path}`);
    }
  };

  return (
    <div className="min-h-screen bg-brand-cream flex flex-col font-sans overflow-hidden">
      {/* Top Ribbon Navigation & Controls */}
      <TopRibbon
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        searchMode={searchMode}
        setSearchMode={setSearchMode}
        onSearchSubmit={executeSearch}
        onRefresh={() => {
          if (activeTab === 'search') executeSearch();
          else if (activeTab === 'storage') loadStorageAnalysis();
          else if (activeTab === 'duplicates') loadDuplicates();
        }}
        onScanDrive={handleScanDrive}
        onCancelScan={handleCancelScan}
        isScanning={isScanning}
        scanCount={scanCount}
        scanElapsedTime={scanElapsedTime}
        isLoading={isLoading}
      />

      {/* Main Container Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Drive Tree Panel */}
        <LeftDriveTree
          drives={drives}
          selectedDrive={selectedDrive}
          onSelectDrive={setSelectedDrive}
        />

        {/* View Component based on Active Tab */}
        {activeTab === 'search' && (
          <SearchResultsView
            results={searchResults}
            searchMode={searchMode}
            onOpenPath={handleOpenPath}
            onOpenFolder={handleOpenFolder}
            isLoading={isLoading}
          />
        )}

        {activeTab === 'storage' && (
          <StorageAnalyzerView
            data={storageData}
            onOpenPath={handleOpenPath}
            onOpenFolder={handleOpenFolder}
            isLoading={isLoading}
          />
        )}

        {activeTab === 'duplicates' && (
          <DuplicateView
            data={duplicateData}
            onOpenPath={handleOpenPath}
            onOpenFolder={handleOpenFolder}
            isLoading={isLoading}
          />
        )}
      </div>

      {/* Bottom Status Bar */}
      <StatusBar
        stats={systemStats}
        selectedDrive={selectedDrive}
        resultCount={searchResults.length}
      />
    </div>
  );
};

export default App;
