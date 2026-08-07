using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using Microsoft.Data.Sqlite;
using FileManager.Core.Models;

namespace FileManager.Core.Services
{
    public class DuplicateFinder
    {
        // Calculate fast partial MD5 hash (first 8KB of file content)
        public string CalculatePartialMD5(string filePath, int bytesToRead = 8192)
        {
            try
            {
                if (string.IsNullOrEmpty(filePath) || !File.Exists(filePath))
                    return string.Empty;

                using (var md5 = MD5.Create())
                {
                    using (var stream = new FileStream(filePath, FileMode.Open, FileAccess.Read, FileShare.ReadWrite))
                    {
                        byte[] buffer = new byte[bytesToRead];
                        int bytesRead = stream.Read(buffer, 0, bytesToRead);
                        if (bytesRead <= 0) return string.Empty;

                        var hash = md5.ComputeHash(buffer, 0, bytesRead);
                        return BitConverter.ToString(hash).Replace("-", "").ToLowerInvariant();
                    }
                }
            }
            catch
            {
                return string.Empty; // Skip locked or inaccessible files
            }
        }

        // Find duplicates instantly using SQLite candidate filtering (GROUP BY FileSizeBytes HAVING COUNT(*) > 1) and 8KB partial hashing
        public Dictionary<string, List<FileItem>> FindDuplicatesFromDatabase(string dbPath = "files.db")
        {
            var duplicatesGroup = new Dictionary<string, List<FileItem>>();
            if (!File.Exists(dbPath)) return duplicatesGroup;

            try
            {
                var candidateGroups = new Dictionary<long, List<FileItem>>();

                using (var conn = new SqliteConnection($"Data Source={dbPath}"))
                {
                    conn.Open();

                    var query = @"
                        SELECT FullPath, FileName, FileSizeBytes, Extension
                        FROM Files
                        WHERE FileSizeBytes > 0 AND FileSizeBytes IN (
                            SELECT FileSizeBytes
                            FROM Files
                            WHERE FileSizeBytes > 0
                            GROUP BY FileSizeBytes
                            HAVING COUNT(*) > 1
                        );";

                    using (var cmd = new SqliteCommand(query, conn))
                    using (var reader = cmd.ExecuteReader())
                    {
                        while (reader.Read())
                        {
                            var item = new FileItem
                            {
                                FullPath = reader.GetString(0),
                                FileName = reader.GetString(1),
                                FileSizeBytes = reader.GetInt64(2),
                                Extension = reader.GetString(3)
                            };

                            if (!candidateGroups.ContainsKey(item.FileSizeBytes))
                            {
                                candidateGroups[item.FileSizeBytes] = new List<FileItem>();
                            }
                            candidateGroups[item.FileSizeBytes].Add(item);
                        }
                    }
                }

                foreach (var group in candidateGroups)
                {
                    var hashGroups = new Dictionary<string, List<FileItem>>();

                    foreach (var file in group.Value)
                    {
                        string hash = CalculatePartialMD5(file.FullPath);
                        if (string.IsNullOrEmpty(hash)) continue;

                        if (!hashGroups.ContainsKey(hash))
                        {
                            hashGroups[hash] = new List<FileItem>();
                        }
                        hashGroups[hash].Add(file);
                    }

                    foreach (var hashEntry in hashGroups.Where(h => h.Value.Count > 1))
                    {
                        duplicatesGroup[hashEntry.Key] = hashEntry.Value;
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error querying duplicate candidates: {ex.Message}");
            }

            return duplicatesGroup;
        }

        // Find duplicates from in-memory list using partial 8KB hashing
        public Dictionary<string, List<FileItem>> FindDuplicates(List<FileItem> files)
        {
            var duplicatesGroup = new Dictionary<string, List<FileItem>>();
            if (files == null || files.Count == 0) return duplicatesGroup;

            var sizeGroups = files.Where(f => f.FileSizeBytes > 0)
                                  .GroupBy(f => f.FileSizeBytes)
                                  .Where(g => g.Count() > 1);

            foreach (var group in sizeGroups)
            {
                var hashGroups = new Dictionary<string, List<FileItem>>();

                foreach (var file in group)
                {
                    string hash = CalculatePartialMD5(file.FullPath);
                    if (string.IsNullOrEmpty(hash)) continue;

                    if (!hashGroups.ContainsKey(hash))
                    {
                        hashGroups[hash] = new List<FileItem>();
                    }
                    hashGroups[hash].Add(file);
                }

                foreach (var hashEntry in hashGroups.Where(h => h.Value.Count > 1))
                {
                    duplicatesGroup[hashEntry.Key] = hashEntry.Value;
                }
            }

            return duplicatesGroup;
        }
    }
}