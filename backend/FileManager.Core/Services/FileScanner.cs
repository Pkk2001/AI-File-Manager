using System;
using System.Collections.Generic;
using System.IO;
using System.Security;
using FileManager.Core.Models;

namespace FileManager.Core.Services
{
    public class FileScanner
    {
        private static readonly HashSet<string> RestrictedFolders = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
        {
            "$Recycle.Bin",
            "System Volume Information",
            "Config.Msi",
            "Windows",
            "ProgramData"
        };

        public List<FileItem> ScanDirectory(string path)
        {
            var fileItems = new List<FileItem>();

            if (string.IsNullOrWhiteSpace(path) || !Directory.Exists(path))
            {
                return fileItems;
            }

            SafeScan(path, fileItems);
            return fileItems;
        }

        private void SafeScan(string currentPath, List<FileItem> fileItems)
        {
            try
            {
                var currentDirInfo = new DirectoryInfo(currentPath);

                // Skip symbolic links, junction points, and restricted system folders
                if ((currentDirInfo.Attributes & FileAttributes.ReparsePoint) == FileAttributes.ReparsePoint)
                {
                    return;
                }

                if (RestrictedFolders.Contains(currentDirInfo.Name))
                {
                    return;
                }
            }
            catch (Exception)
            {
                return;
            }

            // Process files in current directory
            try
            {
                string[] files = Directory.GetFiles(currentPath);
                foreach (var filePath in files)
                {
                    try
                    {
                        var fileInfo = new FileInfo(filePath);

                        // Skip reparse point files
                        if ((fileInfo.Attributes & FileAttributes.ReparsePoint) == FileAttributes.ReparsePoint)
                        {
                            continue;
                        }

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
                    catch (UnauthorizedAccessException) { }
                    catch (PathTooLongException) { }
                    catch (FileNotFoundException) { }
                    catch (IOException) { }
                    catch (SecurityException) { }
                    catch (Exception) { }
                }
            }
            catch (UnauthorizedAccessException) { }
            catch (PathTooLongException) { }
            catch (DirectoryNotFoundException) { }
            catch (IOException) { }
            catch (SecurityException) { }
            catch (Exception) { }

            // Process subdirectories recursively
            try
            {
                string[] directories = Directory.GetDirectories(currentPath);
                foreach (var dirPath in directories)
                {
                    try
                    {
                        SafeScan(dirPath, fileItems);
                    }
                    catch (UnauthorizedAccessException) { }
                    catch (PathTooLongException) { }
                    catch (DirectoryNotFoundException) { }
                    catch (IOException) { }
                    catch (SecurityException) { }
                    catch (Exception) { }
                }
            }
            catch (UnauthorizedAccessException) { }
            catch (PathTooLongException) { }
            catch (DirectoryNotFoundException) { }
            catch (IOException) { }
            catch (SecurityException) { }
            catch (Exception) { }
        }
    }
}
