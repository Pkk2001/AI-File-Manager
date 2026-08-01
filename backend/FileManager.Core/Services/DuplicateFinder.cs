using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using FileManager.Core.Models;

namespace FileManager.Core.Services
{
    public class DuplicateFinder
    {
        // Calculate MD5 hash for content comparison
        public string CalculateMD5(string filePath)
        {
            try
            {
                using (var md5 = MD5.Create())
                {
                    using (var stream = File.OpenRead(filePath))
                    {
                        var hash = md5.ComputeHash(stream);
                        return BitConverter.ToString(hash).Replace("-", "").ToLowerInvariant();
                    }
                }
            }
            catch
            {
                return string.Empty; // Skip if file is locked
            }
        }

        // Find duplicates from scanned files list
        public Dictionary<string, List<FileItem>> FindDuplicates(List<FileItem> files)
        {
            var duplicatesGroup = new Dictionary<string, List<FileItem>>();

            // 1. Group files by Size first (optimization: different sizes can never be duplicates)
            var sizeGroups = files.Where(f => f.FileSizeBytes > 0)
                                  .GroupBy(f => f.FileSizeBytes)
                                  .Where(g => g.Count() > 1);

            foreach (var group in sizeGroups)
            {
                var hashGroups = new Dictionary<string, List<FileItem>>();

                foreach (var file in group)
                {
                    string hash = CalculateMD5(file.FilePath);
                    if (string.IsNullOrEmpty(hash)) continue;

                    if (!hashGroups.ContainsKey(hash))
                    {
                        hashGroups[hash] = new List<FileItem>();
                    }
                    hashGroups[hash].Add(file);
                }

                // Keep only groups that have more than 1 file with the exact same hash
                foreach (var hashEntry in hashGroups.Where(h => h.Value.Count > 1))
                {
                    duplicatesGroup[hashEntry.Key] = hashEntry.Value;
                }
            }

            return duplicatesGroup;
        }
    }
}