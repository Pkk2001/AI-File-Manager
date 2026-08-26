import React from 'react';
import type { StorageAnalysisData } from '../types';
import { HardDrive, PieChart, BarChart2, AlertCircle, FolderOpen, ExternalLink } from 'lucide-react';

interface StorageAnalyzerViewProps {
  data: StorageAnalysisData | null;
  onOpenPath: (path: string) => void;
  onOpenFolder: (path: string) => void;
  isLoading: boolean;
}

export const StorageAnalyzerView: React.FC<StorageAnalyzerViewProps> = ({
  data,
  onOpenPath,
  onOpenFolder,
  isLoading
}) => {
  if (isLoading || !data) {
    return (
      <div className="flex-1 bg-brand-cream p-8 flex items-center justify-center">
        <div className="text-center space-y-3">
          <PieChart className="w-10 h-10 text-brand-sage animate-spin mx-auto" />
          <p className="text-sm font-semibold text-brand-darkGreen">Analyzing Drive Storage Distribution & Large Files...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 bg-brand-cream overflow-y-auto p-6 space-y-6">
      {/* 1. Drive Overview Cards */}
      <div className="space-y-3">
        <h2 className="text-xs font-bold uppercase tracking-wider text-brand-darkGreen flex items-center gap-2">
          <HardDrive className="w-4 h-4 text-brand-sage" />
          System Drives & Volume Capacity
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {data.drives.map((d) => (
            <div key={d.drive} className="bg-white rounded-xl p-4 border border-brand-sage/20 shadow-sm space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <HardDrive className="w-5 h-5 text-brand-darkGreen" />
                  <div>
                    <h3 className="text-xs font-bold text-brand-darkGreen font-mono">{d.drive} {d.label}</h3>
                    <span className="text-[10px] text-gray-400 font-mono">{d.format}</span>
                  </div>
                </div>
                <span className="text-xs font-bold font-mono text-brand-sage">{d.used_pct}%</span>
              </div>

              <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                <div 
                  className={`h-full rounded-full ${d.used_pct > 85 ? 'bg-amber-500' : 'bg-brand-sage'}`} 
                  style={{ width: `${Math.min(100, Math.max(5, d.used_pct))}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 2. Category Storage Breakdown & Top Extensions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Category Breakdown (2 cols) */}
        <div className="lg:col-span-2 bg-white rounded-xl p-5 border border-brand-sage/20 shadow-sm space-y-4">
          <h2 className="text-xs font-bold uppercase tracking-wider text-brand-darkGreen flex items-center gap-2">
            <PieChart className="w-4 h-4 text-brand-sage" />
            Category Storage Distribution
          </h2>

          <div className="space-y-3">
            {data.categories.map((c) => (
              <div key={c.category} className="space-y-1">
                <div className="flex items-center justify-between text-xs font-medium">
                  <span className="text-brand-darkGreen font-semibold">{c.category} ({c.count.toLocaleString()} files)</span>
                  <span className="text-gray-600 font-mono">{c.formatted_size} ({c.percentage}%)</span>
                </div>
                <div className="w-full h-2.5 bg-gray-100 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-brand-darkGreen rounded-full transition-all"
                    style={{ width: `${Math.min(100, Math.max(2, c.percentage))}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Top Extensions (1 col) */}
        <div className="bg-white rounded-xl p-5 border border-brand-sage/20 shadow-sm space-y-4">
          <h2 className="text-xs font-bold uppercase tracking-wider text-brand-darkGreen flex items-center gap-2">
            <BarChart2 className="w-4 h-4 text-brand-sage" />
            Top Extensions
          </h2>

          <div className="space-y-2 font-mono text-xs">
            {data.top_extensions.slice(0, 8).map((ext, idx) => (
              <div key={idx} className="flex items-center justify-between py-1.5 border-b border-gray-100 last:border-0">
                <span className="font-bold text-brand-sage">{ext.extension}</span>
                <span className="text-gray-500">{ext.count.toLocaleString()} files</span>
                <span className="font-semibold text-brand-charcoal">{ext.formatted_size}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 3. Top Space-Hogging Largest Files */}
      <div className="bg-white rounded-xl p-5 border border-brand-sage/20 shadow-sm space-y-4">
        <h2 className="text-xs font-bold uppercase tracking-wider text-brand-darkGreen flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-amber-600" />
          Top Space-Hogging Largest Files
        </h2>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-brand-cream text-brand-darkGreen font-semibold uppercase text-[11px]">
              <tr>
                <th className="px-3 py-2">Rank</th>
                <th className="px-3 py-2">Size</th>
                <th className="px-3 py-2">Category</th>
                <th className="px-3 py-2">File Name</th>
                <th className="px-3 py-2">Full Path</th>
                <th className="px-3 py-2 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data.largest_files.map((file, idx) => (
                <tr key={idx} className="hover:bg-brand-cream/50 transition-colors">
                  <td className="px-3 py-2 font-bold text-brand-sage">#{idx + 1}</td>
                  <td className="px-3 py-2 font-bold text-brand-darkGreen">{file.formatted_size}</td>
                  <td className="px-3 py-2 font-sans">{file.category}</td>
                  <td className="px-3 py-2 font-semibold text-brand-charcoal truncate max-w-xs">{file.name}</td>
                  <td className="px-3 py-2 text-gray-500 truncate max-w-sm text-[11px]" title={file.path}>{file.path}</td>
                  <td className="px-3 py-2 text-right space-x-1 font-sans">
                    <button
                      onClick={() => onOpenPath(file.path)}
                      className="p-1 rounded text-brand-sage hover:bg-brand-sage hover:text-white"
                      title="Open File"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => onOpenFolder(file.path)}
                      className="p-1 rounded text-amber-600 hover:bg-amber-600 hover:text-white"
                      title="Show in Folder"
                    >
                      <FolderOpen className="w-3.5 h-3.5" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
