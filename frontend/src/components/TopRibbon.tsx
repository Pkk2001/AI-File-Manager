import React from 'react';
import type { ActiveTab, SearchMode } from '../types';
import {
  Search,
  Copy,
  PieChart,
  HardDrive,
  FolderPlus,
  RefreshCw,
  Image as ImageIcon,
  FileText,
  Square,
  Loader2
} from 'lucide-react';

interface TopRibbonProps {
  activeTab: ActiveTab;
  setActiveTab: (tab: ActiveTab) => void;
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  searchMode: SearchMode;
  setSearchMode: (mode: SearchMode) => void;
  onSearchSubmit: () => void;
  onRefresh: () => void;
  onScanDrive: () => void;
  onCancelScan: () => void;
  isScanning: boolean;
  scanCount: number;
  scanElapsedTime: number;
  isLoading: boolean;
}

export const TopRibbon: React.FC<TopRibbonProps> = ({
  activeTab,
  setActiveTab,
  searchQuery,
  setSearchQuery,
  searchMode,
  setSearchMode,
  onSearchSubmit,
  onRefresh,
  onScanDrive,
  onCancelScan,
  isScanning,
  scanCount,
  scanElapsedTime,
  isLoading
}) => {
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      if (isLoading || isScanning) return;
      onSearchSubmit();
    }
  };

  const formatElapsed = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}s`;
  };

  return (
    <div className="bg-brand-darkGreen text-brand-white border-b border-brand-sage/30 select-none shadow-md flex flex-col">
      {/* Native Desktop Window Header & Tabs Bar */}
      <div
        className="h-10 flex items-center justify-between px-3 pt-1 border-b border-emerald-950/40"
        style={{ WebkitAppRegion: 'drag' } as React.CSSProperties}
      >
        {/* App Title & Tabs */}
        <div className="flex items-center space-x-6" style={{ WebkitAppRegion: 'no-drag' } as React.CSSProperties}>
          <div className="flex items-center space-x-2 text-sm font-bold tracking-tight text-emerald-100 mr-2">
            <HardDrive className="w-4 h-4 text-emerald-400" />
            <span>AI FILE MANAGER</span>
          </div>

          <div className="flex space-x-1">
            <button
              onClick={() => setActiveTab('search')}
              className={`flex items-center space-x-2 px-3 py-1.5 rounded-t-md text-xs font-semibold transition-all ${activeTab === 'search'
                ? 'bg-brand-cream text-brand-darkGreen shadow-inner'
                : 'text-emerald-100/70 hover:text-white hover:bg-white/10'
                }`}
            >
              <Search className="w-3.5 h-3.5" />
              <span>SCAN / SEARCH</span>
            </button>

            <button
              onClick={() => setActiveTab('duplicates')}
              className={`flex items-center space-x-2 px-3 py-1.5 rounded-t-md text-xs font-semibold transition-all ${activeTab === 'duplicates'
                ? 'bg-brand-cream text-brand-darkGreen shadow-inner'
                : 'text-emerald-100/70 hover:text-white hover:bg-white/10'
                }`}
            >
              <Copy className="w-3.5 h-3.5" />
              <span>DUPLICATES</span>
            </button>

            <button
              onClick={() => setActiveTab('storage')}
              className={`flex items-center space-x-2 px-3 py-1.5 rounded-t-md text-xs font-semibold transition-all ${activeTab === 'storage'
                ? 'bg-brand-cream text-brand-darkGreen shadow-inner'
                : 'text-emerald-100/70 hover:text-white hover:bg-white/10'
                }`}
            >
              <PieChart className="w-3.5 h-3.5" />
              <span>STORAGE ANALYZER</span>
            </button>
          </div>
        </div>

        {/* Engine Status Badge */}
        <div className="flex items-center space-x-2 pr-28 text-xs" style={{ WebkitAppRegion: 'no-drag' } as React.CSSProperties}>
          <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-950/60 border border-emerald-500/30 text-emerald-200 text-[11px] font-sans font-medium">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            Ready
          </span>
        </div>
      </div>

      {/* Ribbon Action Bar */}
      <div className="p-2.5 bg-emerald-950/40 flex items-center justify-between gap-4">
        {/* Left Action Buttons */}
        <div className="flex items-center space-x-2">
          {isScanning ? (
            <button
              onClick={onCancelScan}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-red-600 hover:bg-red-700 text-white text-xs font-bold transition-all shadow-md active:scale-95 animate-pulse"
              title="Immediately cancel running drive scan process"
            >
              <Square className="w-3.5 h-3.5 fill-current" />
              <span>Stop / Cancel Scan</span>
            </button>
          ) : (
            <button
              onClick={onScanDrive}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-brand-sage hover:bg-emerald-600 text-white text-xs font-medium transition-all shadow-sm active:scale-95"
            >
              <HardDrive className="w-3.5 h-3.5" />
              <span>Scan Drive</span>
            </button>
          )}

          <button
            onClick={onScanDrive}
            disabled={isScanning}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-emerald-900/60 hover:bg-emerald-900 border border-emerald-700/40 text-emerald-100 text-xs font-medium transition-all active:scale-95 disabled:opacity-40"
          >
            <FolderPlus className="w-3.5 h-3.5" />
            <span>Scan Folder</span>
          </button>

          <button
            onClick={onRefresh}
            disabled={isLoading || isScanning}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-emerald-900/60 hover:bg-emerald-900 border border-emerald-700/40 text-emerald-100 text-xs font-medium transition-all active:scale-95 disabled:opacity-40"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>

        {/* Center Search Bar & Mode Selector */}
        <div className="flex-1 max-w-2xl flex items-center space-x-2">
          <div className="relative flex-1">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={
                searchMode === 'image'
                  ? "Describe an image to find (e.g., 'white sports car', 'sunset beach')..."
                  : "Search files by name, type, or query (e.g., 'large pdfs in C:')..."
              }
              className="w-full bg-brand-charcoal text-brand-white text-xs placeholder-gray-400 px-3 py-1.5 pl-8 rounded border border-brand-sage/40 focus:outline-none focus:border-emerald-400 transition-colors shadow-inner"
            />
            <Search className="w-3.5 h-3.5 text-gray-400 absolute left-2.5 top-2" />
          </div>

          <button
            onClick={onSearchSubmit}
            disabled={isLoading || isScanning}
            className="px-4 py-1.5 bg-brand-sage hover:bg-emerald-600 text-white text-xs font-semibold rounded shadow transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-1.5"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Searching...</span>
              </>
            ) : (
              <span>Search</span>
            )}
          </button>

          {/* Mode Toggle Pill */}
          <div className="bg-brand-charcoal p-0.5 rounded border border-brand-sage/40 flex items-center">
            <button
              onClick={() => setSearchMode('text')}
              className={`flex items-center space-x-1 px-2.5 py-1 rounded text-[11px] font-semibold transition-all ${searchMode === 'text'
                ? 'bg-brand-sage text-white shadow'
                : 'text-gray-400 hover:text-white'
                }`}
              title="Search files by name, extension, or natural language query"
            >
              <FileText className="w-3 h-3" />
              <span>Files & Text</span>
            </button>

            <button
              onClick={() => setSearchMode('image')}
              className={`flex items-center space-x-1 px-2.5 py-1 rounded text-[11px] font-semibold transition-all ${searchMode === 'image'
                ? 'bg-brand-sage text-white shadow'
                : 'text-gray-400 hover:text-white'
                }`}
              title="Semantic Image Search using Vision AI"
            >
              <ImageIcon className="w-3 h-3" />
              <span>Image Vision</span>
            </button>
          </div>
        </div>
      </div>

      {/* Animated Scan Progress Bar (when scanning) */}
      {isScanning && (
        <div className="bg-emerald-950 px-4 py-1.5 border-t border-emerald-800/40 flex items-center justify-between text-xs font-mono text-emerald-200">
          <div className="flex items-center space-x-3">
            <Loader2 className="w-3.5 h-3.5 animate-spin text-emerald-400" />
            <span className="font-bold">Indexing File System...</span>
            <span className="text-gray-400">Scanned: <strong className="text-white">{scanCount.toLocaleString()}</strong> files</span>
          </div>

          <div className="flex items-center space-x-4">
            <span className="text-gray-400">Elapsed: <strong className="text-emerald-300">{formatElapsed(scanElapsedTime)}</strong></span>
            <div className="w-36 h-2 bg-gray-800 rounded-full overflow-hidden border border-emerald-600/30">
              <div className="h-full bg-emerald-400 animate-pulse rounded-full w-2/3"></div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
