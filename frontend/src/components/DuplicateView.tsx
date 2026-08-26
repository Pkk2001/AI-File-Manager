import React, { useState } from 'react';
import type { DuplicateData, DuplicateGroup } from '../types';
import { Copy, Trash2, FolderOpen, ExternalLink, CheckSquare, Square, Sparkles } from 'lucide-react';

interface DuplicateViewProps {
  data: DuplicateData | null;
  onOpenPath: (path: string) => void;
  onOpenFolder: (path: string) => void;
  isLoading: boolean;
}

export const DuplicateView: React.FC<DuplicateViewProps> = ({
  data,
  onOpenPath,
  onOpenFolder,
  isLoading
}) => {
  const [selectedPaths, setSelectedPaths] = useState<Record<string, boolean>>({});

  if (isLoading || !data) {
    return (
      <div className="flex-1 bg-brand-cream p-8 flex items-center justify-center">
        <div className="text-center space-y-3">
          <Copy className="w-10 h-10 text-brand-sage animate-spin mx-auto" />
          <p className="text-sm font-semibold text-brand-darkGreen">Scanning Database for Duplicate Candidates via 8KB MD5 Hashes...</p>
        </div>
      </div>
    );
  }

  const toggleSelect = (path: string) => {
    setSelectedPaths(prev => ({ ...prev, [path]: !prev[path] }));
  };

  const autoSelectDuplicates = () => {
    const newSelected: Record<string, boolean> = {};
    data.groups.forEach(group => {
      // Keep the first item (oldest/primary), select all other duplicates
      group.files.slice(1).forEach(f => {
        newSelected[f.path] = true;
      });
    });
    setSelectedPaths(newSelected);
  };

  const selectedCount = Object.values(selectedPaths).filter(Boolean).length;

  return (
    <div className="flex-1 bg-brand-cream flex flex-col overflow-hidden">
      {/* Top Banner with Reclaim Counter & Auto Select Button */}
      <div className="bg-white border-b border-brand-sage/20 p-4 flex items-center justify-between shadow-sm">
        <div className="flex items-center space-x-4">
          <div className="p-2 bg-brand-cream rounded-lg border border-brand-sage/30">
            <Copy className="w-6 h-6 text-brand-darkGreen" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-brand-darkGreen">Duplicate File Clusters Found ({data.groups.length} Groups)</h2>
            <p className="text-xs text-gray-500 font-mono">
              Potential Space Reclaim: <span className="font-bold text-emerald-700">{data.formatted_waste}</span>
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={autoSelectDuplicates}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-brand-darkGreen hover:bg-brand-sage text-white text-xs font-semibold shadow transition-all active:scale-95"
          >
            <Sparkles className="w-3.5 h-3.5 text-emerald-300" />
            <span>Auto Select Duplicates (Keep 1st)</span>
          </button>

          {selectedCount > 0 && (
            <button
              onClick={() => alert(`Simulated deletion of ${selectedCount} duplicate files.`)}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-red-600 hover:bg-red-700 text-white text-xs font-semibold shadow transition-all active:scale-95"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Clean Selected ({selectedCount})</span>
            </button>
          )}
        </div>
      </div>

      {/* Duplicate Groups List */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {data.groups.length === 0 ? (
          <div className="h-64 flex flex-col items-center justify-center space-y-2 text-gray-500">
            <Copy className="w-10 h-10 text-gray-400" />
            <p className="text-sm font-medium">No duplicate files detected in database</p>
          </div>
        ) : (
          data.groups.map((group: DuplicateGroup, gIdx: number) => (
            <div key={gIdx} className="bg-white rounded-xl border border-brand-sage/20 shadow-sm overflow-hidden space-y-0">
              {/* Group Header */}
              <div className="bg-brand-cream/80 px-4 py-2.5 border-b border-brand-sage/20 flex items-center justify-between font-mono text-xs">
                <div className="flex items-center space-x-2">
                  <span className="font-bold text-brand-darkGreen">Cluster #{gIdx + 1}</span>
                  <span className="text-gray-400">•</span>
                  <span className="text-gray-600">{group.count} Identical Files</span>
                  <span className="text-gray-400">•</span>
                  <span className="font-semibold text-brand-sage">Size: {group.formatted_size}</span>
                </div>
                <span className="text-emerald-800 font-bold bg-emerald-100 px-2 py-0.5 rounded text-[11px]">
                  Waste: {group.formatted_waste}
                </span>
              </div>

              {/* Group Items Table */}
              <table className="w-full text-left text-xs font-mono">
                <tbody className="divide-y divide-gray-100">
                  {group.files.map((file, fIdx) => {
                    const isChecked = !!selectedPaths[file.path];
                    const isOriginal = fIdx === 0;

                    return (
                      <tr key={fIdx} className={`hover:bg-brand-cream/40 transition-colors ${isChecked ? 'bg-amber-50/60' : ''}`}>
                        <td className="w-10 px-3 py-2 text-center">
                          <button onClick={() => toggleSelect(file.path)} className="text-gray-400 hover:text-brand-darkGreen">
                            {isChecked ? (
                              <CheckSquare className="w-4 h-4 text-emerald-600" />
                            ) : (
                              <Square className="w-4 h-4" />
                            )}
                          </button>
                        </td>

                        <td className="px-3 py-2 font-semibold text-brand-darkGreen">
                          {file.name}
                          {isOriginal && (
                            <span className="ml-2 text-[10px] bg-blue-100 text-blue-800 px-1.5 py-0.2 rounded font-sans">
                              Original File
                            </span>
                          )}
                        </td>

                        <td className="px-3 py-2 text-gray-500 truncate max-w-md text-[11px]" title={file.path}>
                          {file.path}
                        </td>

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
                    );
                  })}
                </tbody>
              </table>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
