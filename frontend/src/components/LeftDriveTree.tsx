import React from 'react';
import type { DriveInfo } from '../types';
import { HardDrive, Database, Check } from 'lucide-react';

interface LeftDriveTreeProps {
  drives: DriveInfo[];
  selectedDrive: string | null;
  onSelectDrive: (drive: string | null) => void;
}

export const LeftDriveTree: React.FC<LeftDriveTreeProps> = ({
  drives,
  selectedDrive,
  onSelectDrive,
}) => {
  return (
    <aside className="w-64 bg-brand-charcoal text-brand-white border-r border-brand-sage/20 flex flex-col justify-between select-none shadow-xl">
      {/* Drives List Section */}
      <div className="p-3 space-y-3 overflow-y-auto">
        <div className="flex items-center justify-between px-1">
          <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
            <HardDrive className="w-3.5 h-3.5 text-emerald-400" />
            SYSTEM DRIVES
          </span>

          <button
            onClick={() => onSelectDrive(null)}
            className={`text-[10px] px-2 py-0.5 rounded font-medium transition-all ${
              selectedDrive === null
                ? 'bg-brand-sage text-white font-bold shadow'
                : 'text-gray-400 hover:text-white bg-white/5 hover:bg-white/10'
            }`}
          >
            All Drives
          </button>
        </div>

        {/* Drives Items */}
        <div className="space-y-2">
          {drives.map((d) => {
            const isSelected = selectedDrive === d.drive;

            return (
              <div
                key={d.drive}
                onClick={() => onSelectDrive(isSelected ? null : d.drive)}
                className={`rounded-lg p-2.5 cursor-pointer transition-all border ${
                  isSelected
                    ? 'bg-brand-darkGreen border-emerald-500/50 shadow-md text-white'
                    : 'bg-emerald-950/20 border-brand-sage/10 hover:bg-white/5 hover:border-brand-sage/30 text-gray-200'
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center space-x-2 min-w-0">
                    <HardDrive className={`w-4 h-4 shrink-0 ${isSelected ? 'text-emerald-300' : 'text-emerald-500'}`} />
                    <span className="text-xs font-mono font-bold truncate">{d.drive} ({d.label})</span>
                  </div>

                  {isSelected && <Check className="w-3.5 h-3.5 text-emerald-300 shrink-0" />}
                </div>

                {/* Drive Usage Bar */}
                <div className="space-y-1">
                  <div className="w-full h-1.5 bg-gray-800 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${
                        d.used_pct > 85 ? 'bg-amber-500' : 'bg-brand-sage'
                      }`}
                      style={{ width: `${Math.min(100, Math.max(5, d.used_pct))}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-[10px] text-gray-400 font-mono">
                    <span>{d.used_pct}% used</span>
                    <span>{d.format}</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Scope Footer Info */}
      <div className="p-3 bg-emerald-950/60 border-t border-brand-sage/20 text-[11px] space-y-1">
        <div className="flex items-center space-x-1.5 text-emerald-300 font-semibold">
          <Database className="w-3.5 h-3.5" />
          <span>Active Scope</span>
        </div>
        <div className="text-gray-300 truncate font-mono text-[10px]">
          {selectedDrive ? `Filtered to Drive ${selectedDrive}` : 'All System Drives'}
        </div>
      </div>
    </aside>
  );
};
