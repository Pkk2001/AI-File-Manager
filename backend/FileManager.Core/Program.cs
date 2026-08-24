using System;
using System.Collections.Generic;
using System.IO;
using FileManager.Core.Models;
using FileManager.Core.Services;

namespace FileManager.Core
{
    internal class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine("========================================");
            Console.WriteLine(" AI File Manager - Core C# Scanner Test ");
            Console.WriteLine("========================================\n");

            var scanner = new FileScanner();
            var scannedFiles = new List<FileItem>();

            var startTime = DateTime.Now;

            bool analyzeStorage = Array.Exists(args, a => a.Equals("--analyze-storage", StringComparison.OrdinalIgnoreCase));
            string? targetPath = args.FirstOrDefault(a => !a.StartsWith("--", StringComparison.OrdinalIgnoreCase));

            if (!string.IsNullOrWhiteSpace(targetPath))
            {
                Console.WriteLine($"Scanning target folder: {targetPath} ...");
                scannedFiles = scanner.ScanDirectory(targetPath);
            }
            else if (!analyzeStorage)
            {
                Console.WriteLine("No path argument specified. Fetching all available local drives...");
                var drives = DriveInfo.GetDrives();
                var targetDrives = new List<DriveInfo>();

                foreach (var drive in drives)
                {
                    try
                    {
                        if (drive.IsReady && (drive.DriveType == DriveType.Fixed || drive.DriveType == DriveType.Removable))
                        {
                            targetDrives.Add(drive);
                        }
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine($"Could not inspect drive {drive.Name}: {ex.Message}");
                    }
                }

                Console.WriteLine($"Found {targetDrives.Count} active drive(s): {string.Join(", ", targetDrives.ConvertAll(d => d.Name))}\n");

                foreach (var drive in targetDrives)
                {
                    Console.WriteLine($"Scanning drive {drive.Name} ...");
                    var driveFiles = scanner.ScanDirectory(drive.Name);
                    Console.WriteLine($" -> Drive {drive.Name}: Found {driveFiles.Count} files.");
                    scannedFiles.AddRange(driveFiles);
                }
            }

            var endTime = DateTime.Now;
            var duration = (endTime - startTime).TotalSeconds;

            Console.WriteLine($"\n[SUCCESS] Full Scan Completed!");
            Console.WriteLine($"Total Files Found: {scannedFiles.Count}");
            Console.WriteLine($"Time Taken: {duration:F2} seconds\n");

            // SQLite Database 
            Console.WriteLine("Saving metadata to SQLite Index Database...");
            var dbHelper = new DatabaseHelper();
            dbHelper.SaveFilesBulk(scannedFiles);
            Console.WriteLine("[SUCCESS] Files indexed into SQLite successfully!\n");

            Console.WriteLine("--- Preview First 5 Files ---");
            int count = 0;
            foreach (var file in scannedFiles)
            {
                Console.WriteLine($"File: {file.FileName} | Size: {file.FileSizeBytes / 1024 / 1024} MB | Ext: {file.Extension} | Path: {file.FullPath}");
                count++;
                if (count >= 5) break;
            }

            // Storage Analysis check option
            if (analyzeStorage)
            {
                Console.WriteLine("\n========================================");
                Console.WriteLine(" C# Storage Analyzer Service Statistics ");
                Console.WriteLine("========================================");

                string? driveFilter = null;
                for (int i = 0; i < args.Length - 1; i++)
                {
                    if (args[i].Equals("--drive", StringComparison.OrdinalIgnoreCase))
                    {
                        driveFilter = args[i + 1];
                        break;
                    }
                }

                var analyzer = new StorageAnalyzer();
                
                Console.WriteLine("\n--- Drive Overviews ---");
                foreach (var drive in analyzer.GetDriveOverviews())
                {
                    Console.WriteLine($"Drive: {drive.DriveName} ({drive.VolumeLabel}) | Format: {drive.DriveFormat} | Type: {drive.DriveType} | Total: {drive.TotalSizeFormatted} | Free: {drive.FreeSizeFormatted} | Used: {drive.UsedSizeFormatted} ({drive.UsedPercentage}%)");
                }

                Console.WriteLine($"\n--- Category Breakdown {(driveFilter != null ? $"[{driveFilter}]" : "[All Drives]")} ---");
                foreach (var cat in analyzer.GetCategoryBreakdown(driveFilter))
                {
                    Console.WriteLine($"Category: {cat.Category,-18} | Count: {cat.FileCount,8} | Total Size: {cat.TotalSizeFormatted,10} | Share: {cat.PercentageOfTotal,5:F2}%");
                }

                Console.WriteLine($"\n--- Top 10 Extensions {(driveFilter != null ? $"[{driveFilter}]" : "[All Drives]")} ---");
                foreach (var ext in analyzer.GetExtensionBreakdown(driveFilter, 10))
                {
                    Console.WriteLine($"Extension: {ext.Extension,-12} | Count: {ext.FileCount,8} | Total Size: {ext.TotalSizeFormatted,10}");
                }

                Console.WriteLine($"\n--- Top 10 Largest Files {(driveFilter != null ? $"[{driveFilter}]" : "[All Drives]")} ---");
                foreach (var file in analyzer.GetLargestFiles(driveFilter, 10))
                {
                    Console.WriteLine($"[{file.FormattedSize,10}] {file.FileName} ({file.Category}) -> {file.FullPath}");
                }
            }

            // Duplicate check is optional / background so main indexing finishes immediately
            bool checkDuplicates = Array.Exists(args, a => a.Equals("--check-duplicates", StringComparison.OrdinalIgnoreCase));

            if (checkDuplicates)
            {
                Console.WriteLine("\n[Background Process] Checking for duplicate files using SQLite candidate filtering and 8KB partial hashing...");
                var dupFinder = new DuplicateFinder();
                var duplicates = dupFinder.FindDuplicatesFromDatabase();

                Console.WriteLine($"\n[RESULT] Duplicate Groups Found: {duplicates.Count}");
                int dupPreviewCount = 0;
                foreach (var group in duplicates)
                {
                    Console.WriteLine($"\n--- Duplicate Hash Group: {group.Key} ---");
                    foreach (var file in group.Value)
                    {
                        Console.WriteLine($" -> {file.FileName} ({file.FullPath})");
                    }
                    dupPreviewCount++;
                    if (dupPreviewCount >= 5)
                    {
                        Console.WriteLine($"\n... and {duplicates.Count - 5} more duplicate groups.");
                        break;
                    }
                }
            }
            else
            {
                Console.WriteLine("\nDuplicate check skipped for rapid main indexing. (Pass '--check-duplicates' to execute duplicate check).");
                Console.WriteLine("Pass '--analyze-storage' to execute storage breakdown analysis.");
            }
        }
    }
}
