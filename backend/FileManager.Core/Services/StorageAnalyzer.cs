using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Microsoft.Data.Sqlite;
using FileManager.Core.Models;

namespace FileManager.Core.Services
{
    public class StorageAnalyzer
    {
        private readonly string _dbPath;

        public StorageAnalyzer(string dbPath = "files.db")
        {
            _dbPath = dbPath;
        }

        /// <summary>
        /// Reads all active system drives using System.IO.DriveInfo.
        /// </summary>
        public List<DriveOverview> GetDriveOverviews()
        {
            var driveOverviews = new List<DriveOverview>();
            try
            {
                var drives = DriveInfo.GetDrives();
                foreach (var drive in drives)
                {
                    try
                    {
                        if (drive.IsReady)
                        {
                            driveOverviews.Add(new DriveOverview
                            {
                                DriveName = drive.Name,
                                VolumeLabel = string.IsNullOrWhiteSpace(drive.VolumeLabel) ? "Local Disk" : drive.VolumeLabel,
                                DriveFormat = drive.DriveFormat,
                                DriveType = drive.DriveType.ToString(),
                                TotalSizeBytes = drive.TotalSize,
                                FreeSizeBytes = drive.AvailableFreeSpace
                            });
                        }
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine($"[StorageAnalyzer] Could not read drive {drive.Name}: {ex.Message}");
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[StorageAnalyzer] Error retrieving system drives: {ex.Message}");
            }

            return driveOverviews;
        }

        /// <summary>
        /// Queries SQLite Files table and aggregates SUM(FileSizeBytes) and COUNT(*) grouped by Category.
        /// </summary>
        public List<CategoryBreakdown> GetCategoryBreakdown(string? driveLetter = null)
        {
            var categoryMap = new Dictionary<string, (int FileCount, long TotalSizeBytes)>();

            if (!File.Exists(_dbPath))
                return new List<CategoryBreakdown>();

            try
            {
                using (var conn = new SqliteConnection($"Data Source={_dbPath}"))
                {
                    conn.Open();

                    string whereClause = string.Empty;
                    string drivePattern = string.Empty;

                    if (!string.IsNullOrWhiteSpace(driveLetter))
                    {
                        drivePattern = FormatDrivePattern(driveLetter);
                        whereClause = "WHERE FullPath LIKE @drivePattern";
                    }

                    string query = $@"
                        SELECT Extension, COUNT(*) as FileCount, SUM(FileSizeBytes) as TotalSizeBytes
                        FROM Files
                        {whereClause}
                        GROUP BY Extension;";

                    using (var cmd = new SqliteCommand(query, conn))
                    {
                        if (!string.IsNullOrEmpty(whereClause))
                        {
                            cmd.Parameters.AddWithValue("@drivePattern", drivePattern);
                        }

                        using (var reader = cmd.ExecuteReader())
                        {
                            while (reader.Read())
                            {
                                string ext = reader.IsDBNull(0) ? string.Empty : reader.GetString(0);
                                int count = reader.GetInt32(1);
                                long size = reader.IsDBNull(2) ? 0L : reader.GetInt64(2);

                                string category = GetCategoryFromExtension(ext);

                                if (!categoryMap.ContainsKey(category))
                                {
                                    categoryMap[category] = (0, 0L);
                                }

                                var current = categoryMap[category];
                                categoryMap[category] = (current.FileCount + count, current.TotalSizeBytes + size);
                            }
                        }
                    }
                }

                long overallSizeBytes = categoryMap.Values.Sum(v => v.TotalSizeBytes);

                var breakdown = categoryMap.Select(kv => new CategoryBreakdown
                {
                    Category = kv.Key,
                    FileCount = kv.Value.FileCount,
                    TotalSizeBytes = kv.Value.TotalSizeBytes,
                    PercentageOfTotal = overallSizeBytes > 0 ? Math.Round((double)kv.Value.TotalSizeBytes / overallSizeBytes * 100.0, 2) : 0.0
                }).OrderByDescending(c => c.TotalSizeBytes).ToList();

                return breakdown;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[StorageAnalyzer] Error in GetCategoryBreakdown: {ex.Message}");
                return new List<CategoryBreakdown>();
            }
        }

        /// <summary>
        /// Aggregates SUM(FileSizeBytes) and COUNT(*) grouped by Extension ordered by total size descending.
        /// </summary>
        public List<ExtensionBreakdown> GetExtensionBreakdown(string? driveLetter = null, int top = 10)
        {
            var result = new List<ExtensionBreakdown>();

            if (!File.Exists(_dbPath))
                return result;

            try
            {
                using (var conn = new SqliteConnection($"Data Source={_dbPath}"))
                {
                    conn.Open();

                    string whereClause = string.Empty;
                    string drivePattern = string.Empty;

                    if (!string.IsNullOrWhiteSpace(driveLetter))
                    {
                        drivePattern = FormatDrivePattern(driveLetter);
                        whereClause = "WHERE FullPath LIKE @drivePattern";
                    }

                    string query = $@"
                        SELECT Extension, COUNT(*) as FileCount, SUM(FileSizeBytes) as TotalSizeBytes
                        FROM Files
                        {whereClause}
                        GROUP BY Extension
                        ORDER BY TotalSizeBytes DESC
                        LIMIT @top;";

                    using (var cmd = new SqliteCommand(query, conn))
                    {
                        if (!string.IsNullOrEmpty(whereClause))
                        {
                            cmd.Parameters.AddWithValue("@drivePattern", drivePattern);
                        }
                        cmd.Parameters.AddWithValue("@top", top);

                        using (var reader = cmd.ExecuteReader())
                        {
                            while (reader.Read())
                            {
                                string ext = reader.IsDBNull(0) ? "[No Ext]" : reader.GetString(0);
                                if (string.IsNullOrWhiteSpace(ext)) ext = "[No Ext]";

                                int count = reader.GetInt32(1);
                                long size = reader.IsDBNull(2) ? 0L : reader.GetInt64(2);

                                result.Add(new ExtensionBreakdown
                                {
                                    Extension = ext,
                                    FileCount = count,
                                    TotalSizeBytes = size
                                });
                            }
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[StorageAnalyzer] Error in GetExtensionBreakdown: {ex.Message}");
            }

            return result;
        }

        /// <summary>
        /// Retrieves top largest indexed files with path, size (formatted in MB/GB), category, and last modified date.
        /// </summary>
        public List<LargestFileItem> GetLargestFiles(string? driveLetter = null, int limit = 20)
        {
            var result = new List<LargestFileItem>();

            if (!File.Exists(_dbPath))
                return result;

            try
            {
                using (var conn = new SqliteConnection($"Data Source={_dbPath}"))
                {
                    conn.Open();

                    string whereClause = string.Empty;
                    string drivePattern = string.Empty;

                    if (!string.IsNullOrWhiteSpace(driveLetter))
                    {
                        drivePattern = FormatDrivePattern(driveLetter);
                        whereClause = "WHERE FullPath LIKE @drivePattern";
                    }

                    string query = $@"
                        SELECT FullPath, FileName, FileSizeBytes, Extension, LastModifiedTime
                        FROM Files
                        {whereClause}
                        ORDER BY FileSizeBytes DESC
                        LIMIT @limit;";

                    using (var cmd = new SqliteCommand(query, conn))
                    {
                        if (!string.IsNullOrEmpty(whereClause))
                        {
                            cmd.Parameters.AddWithValue("@drivePattern", drivePattern);
                        }
                        cmd.Parameters.AddWithValue("@limit", limit);

                        using (var reader = cmd.ExecuteReader())
                        {
                            while (reader.Read())
                            {
                                string fullPath = reader.GetString(0);
                                string fileName = reader.GetString(1);
                                long fileSizeBytes = reader.GetInt64(2);
                                string ext = reader.IsDBNull(3) ? string.Empty : reader.GetString(3);
                                string lastModStr = reader.IsDBNull(4) ? string.Empty : reader.GetString(4);

                                DateTime lastModified = DateTime.TryParse(lastModStr, out var dt) ? dt : DateTime.MinValue;

                                result.Add(new LargestFileItem
                                {
                                    FullPath = fullPath,
                                    FileName = fileName,
                                    FileSizeBytes = fileSizeBytes,
                                    Category = GetCategoryFromExtension(ext),
                                    LastModifiedTime = lastModified
                                });
                            }
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[StorageAnalyzer] Error in GetLargestFiles: {ex.Message}");
            }

            return result;
        }

        public static string GetCategoryFromExtension(string extension)
        {
            if (string.IsNullOrWhiteSpace(extension)) return "Other";
            string ext = extension.Trim().ToLowerInvariant();
            if (!ext.StartsWith(".")) ext = "." + ext;

            switch (ext)
            {
                case ".pdf": case ".docx": case ".doc": case ".txt": case ".xlsx": case ".pptx": case ".csv":
                case ".rtf": case ".odt": case ".ods": case ".odp":
                    return "Documents";

                case ".jpg": case ".jpeg": case ".png": case ".gif": case ".svg": case ".webp":
                case ".bmp": case ".ico": case ".tiff":
                    return "Images";

                case ".mp4": case ".mkv": case ".avi": case ".mov": case ".flv": case ".wmv": case ".webm":
                    return "Videos";

                case ".mp3": case ".wav": case ".flac": case ".aac": case ".ogg": case ".m4a": case ".wma":
                    return "Audio";

                case ".zip": case ".rar": case ".7z": case ".tar": case ".gz": case ".bz2": case ".iso":
                    return "Archives";

                case ".cs": case ".js": case ".ts": case ".py": case ".html": case ".css": case ".json":
                case ".cpp": case ".c": case ".h": case ".java": case ".pyw": case ".sh": case ".ps1":
                    return "Source Code";

                case ".exe": case ".msi": case ".apk": case ".app": case ".bat": case ".cmd":
                    return "Executable/Apps";

                default:
                    return "Other";
            }
        }

        private static string FormatDrivePattern(string driveLetter)
        {
            string clean = driveLetter.Trim().TrimEnd('\\', '/').TrimEnd(':');
            return $"{clean}:%";
        }
    }
}
