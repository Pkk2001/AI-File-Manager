using System;
using FileManager.Core.Services;

namespace FileManager.Core
{
    class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine("========================================");
            Console.WriteLine(" AI File Manager - Core C# Scanner Test ");
            Console.WriteLine("========================================\n");

            var scanner = new FileScanner();
            
            // Testing with a sample path (You can change this path to any test folder on your PC)
            string testPath = @"C:\Users\prabh\Downloads"; 

            Console.WriteLine($"Scanning folder: {testPath} ...");
            var startTime = DateTime.Now;

            var scannedFiles = scanner.ScanDirectory(testPath);

            var endTime = DateTime.Now;
            var duration = (endTime - startTime).TotalSeconds;

            Console.WriteLine($"\n[SUCCESS] Scan Completed!");
            Console.WriteLine($"Total Files Found: {scannedFiles.Count}");
            Console.WriteLine($"Time Taken: {duration:F2} seconds\n");

            // Print top 5 scanned files as a preview
            Console.WriteLine("--- Preview First 5 Files ---");
            int count = 0;
            foreach (var file in scannedFiles)
            {
                Console.WriteLine($"File: {file.FileName} | Size: {file.FileSizeBytes / 1024 / 1024} MB | Ext: {file.Extension}");
                count++;
                if (count >= 5) break;
            }
        }
    }
}