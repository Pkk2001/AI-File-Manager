using System;
using System.Collections.Generic;
using System.IO;
using FileManager.Core.Models;

namespace FileManager.Core.Services
{
    public class FileScanner
    {
        public List<FileItem> ScanDirectory(string path)
        {
            var fileItems = new List<FileItem>();

            if (string.IsNullOrWhiteSpace(path) || !Directory.Exists(path))
            {
                return fileItems;
            }

            try
            {
                SafeScan(path, fileItems);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error scanning directory: {ex.Message}");
            }

            return fileItems;
        }

        private void SafeScan(string currentPath, List<FileItem> fileItems)
        {
            try
            {
                // Process files in the current directory
                string[] files = Directory.GetFiles(currentPath);
                foreach (var filePath in files)
                {
                    try
                    {
                        var fileInfo = new FileInfo(filePath);
                        fileItems.Add(new FileItem
                        {
                            FileName = fileInfo.Name,
                            FullPath = fileInfo.FullName,
                            FileSizeBytes = fileInfo.Length,
                            Extension = fileInfo.Extension,
                            CreationTime = fileInfo.CreationTime,
                            LastModifiedTime = fileInfo.LastWriteTime
                        });
                    }
                    catch
                    {
                        // Ignore files that are locked or inaccessible
                    }
                }

                // Recursively process subdirectories
                string[] directories = Directory.GetDirectories(currentPath);
                foreach (var dirPath in directories)
                {
                    try
                    {
                        SafeScan(dirPath, fileItems);
                    }
                    catch
                    {
                        // Ignore directories that cannot be accessed
                    }
                }
            }
            catch
            {
                // Ignore directory-level errors (e.g. access denied on subfolders)
            }
        }
    }
}
