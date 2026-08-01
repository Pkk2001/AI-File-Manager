using System;
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
            
            // Testing path
            string testPath = @"C:\Users\prabh\Downloads"; 

            if (!System.IO.Directory.Exists(testPath))
            {
                testPath = AppDomain.CurrentDomain.BaseDirectory;
            }

            Console.WriteLine($"Scanning folder: {testPath} ...");
            var startTime = DateTime.Now;

            var scannedFiles = scanner.ScanDirectory(testPath);

            var endTime = DateTime.Now;
            var duration = (endTime - startTime).TotalSeconds;

            Console.WriteLine($"\n[SUCCESS] Scan Completed!");
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
                Console.WriteLine($"File: {file.FileName} | Size: {file.FileSizeBytes / 1024 / 1024} MB | Ext: {file.Extension}");
                count++;
                if (count >= 5) break;
            }

            Console.WriteLine("Checking for duplicate files...");
            var dupFinder = new DuplicateFinder();
            var duplicates = dupFinder.FindDuplicates(scannedFiles);

            Console.WriteLine($"\n[RESULT] Duplicate Groups Found: {duplicates.Count}");
            foreach (var group in duplicates)
            {
                Console.WriteLine($"\n--- Duplicate Hash Group: {group.Key} ---");
                foreach (var file in group.Value)
                {
                    Console.WriteLine($" -> {file.FileName} ({file.FilePath})");
                }
            }
        }
    }
}
