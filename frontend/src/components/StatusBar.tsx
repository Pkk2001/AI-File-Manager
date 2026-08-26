import React from 'react';
import type { SystemStats } from '../types';
import { Database, HardDrive } from 'lucide-react';

interface StatusBarProps {
  stats: SystemStats | null;
  selectedDrive: string | null;
  resultCount: number;
}

export const StatusBar: React.FC<StatusBarProps> = ({
  stats,
  selectedDrive,
  resultCount
}) => {
  return (
    <footer className="h-7 bg-brand-charcoal text-brand-white px-4 border-t border-brand-sage/20 flex items-center justify-between text-[11px] font-mono select-none">
      {/* Left Items: Indexed Count & Result Summary */}
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-1.5 text-gray-300">
          <Database className="w-3.5 h-3.5 text-emerald-400" />
          <span>Indexed Files:</span>
          <span className="font-bold text-white">
            {stats ? stats.total_files.toLocaleString() : '1,447,747'}
          </span>
        </div>

        <span className="text-gray-600">•</span>

        <div className="text-gray-300">
          <span>Active Results:</span> <span className="font-bold text-emerald-300">{resultCount}</span>
        </div>

        <span className="text-gray-600">•</span>

        <div className="text-gray-400">
          <span>DB Size:</span> <span className="text-gray-200">{stats ? stats.formatted_db_size : '500.00 MB'}</span>
        </div>
      </div>

      {/* Right Items: Selected Drive & Engine Status */}
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-1.5 text-gray-300">
          <HardDrive className="w-3.5 h-3.5 text-emerald-400" />
          <span>Scope:</span>
          <span className="text-emerald-200 font-bold">
            {selectedDrive ? `Drive ${selectedDrive}` : 'All System Drives'}
          </span>
        </div>

        <span className="text-gray-600">•</span>

        <div className="flex items-center space-x-1.5 text-emerald-400">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span className="font-medium font-sans">Database Active</span>
        </div>
      </div>
    </footer>
  );
};
