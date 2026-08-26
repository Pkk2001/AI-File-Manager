export type ActiveTab = 'search' | 'duplicates' | 'storage';
export type SearchMode = 'text' | 'image';

export interface DriveInfo {
  drive: string;
  label: string;
  format: string;
  total: number;
  used: number;
  free: number;
  used_pct: number;
}

export interface FileResultItem {
  name: string;
  path: string;
  size: number;
  formatted_size: string;
  extension: string;
  category: string;
  modified: string;
  score: number;
}

export interface CategoryBreakdown {
  category: string;
  count: number;
  size: number;
  formatted_size: string;
  percentage: number;
}

export interface ExtensionBreakdown {
  extension: string;
  count: number;
  size: number;
  formatted_size: string;
}

export interface StorageAnalysisData {
  drives: DriveInfo[];
  categories: CategoryBreakdown[];
  top_extensions: ExtensionBreakdown[];
  largest_files: FileResultItem[];
}

export interface DuplicateGroup {
  hash: string;
  size: number;
  formatted_size: string;
  count: number;
  waste_bytes: number;
  formatted_waste: string;
  files: FileResultItem[];
}

export interface DuplicateData {
  groups: DuplicateGroup[];
  total_waste_bytes: number;
  formatted_waste: string;
}

export interface SystemStats {
  total_files: number;
  db_size: number;
  formatted_db_size: string;
  db_path: string;
}

declare global {
  interface Window {
    electronAPI?: {
      platform: string;
      getDrives: () => Promise<DriveInfo[]>;
      searchFiles: (params: { query?: string; mode?: SearchMode; drive?: string }) => Promise<{ count: number; results: FileResultItem[]; error?: string; cancelled?: boolean }>;
      getStorageAnalysis: (params: { drive?: string }) => Promise<StorageAnalysisData>;
      getDuplicates: () => Promise<DuplicateData>;
      getStats: () => Promise<SystemStats>;
      openPath: (filePath: string) => Promise<boolean>;
      openFolder: (filePath: string) => Promise<boolean>;
      scanDrive: (drive?: string) => Promise<{ success: boolean; cancelled?: boolean; error?: string }>;
      cancelActiveScan: () => Promise<{ cancelled: boolean }>;
      onScanProgress: (callback: (data: { output: string; drive: string }) => void) => () => void;
    };
  }
}
