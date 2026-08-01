using System;
using System.Collections.Generic;
using Microsoft.Data.Sqlite;
using FileManager.Core.Models;

namespace FileManager.Core.Services
{
    public class DatabaseHelper
    {
        private readonly string _connectionString;

        public DatabaseHelper(string dbPath = "files.db")
        {
            _connectionString = $"Data Source={dbPath}";
            InitializeDatabase();
        }

        private void InitializeDatabase()
        {
            using (var connection = new SqliteConnection(_connectionString))
            {
                connection.Open();
                
                var createTableQuery = @"
                    CREATE TABLE IF NOT EXISTS Files (
                        FullPath TEXT PRIMARY KEY,
                        FileName TEXT NOT NULL,
                        FileSizeBytes INTEGER NOT NULL,
                        Extension TEXT NOT NULL,
                        CreationTime TEXT NOT NULL,
                        LastModifiedTime TEXT NOT NULL
                    );";

                using (var command = new SqliteCommand(createTableQuery, connection))
                {
                    command.ExecuteNonQuery();
                }
            }
        }

        public void SaveFilesBulk(List<FileItem> files)
        {
            if (files == null || files.Count == 0) return;

            using (var connection = new SqliteConnection(_connectionString))
            {
                connection.Open();

                using (var transaction = connection.BeginTransaction())
                {
                    var insertQuery = @"
                        INSERT OR REPLACE INTO Files (FullPath, FileName, FileSizeBytes, Extension, CreationTime, LastModifiedTime)
                        VALUES ($FullPath, $FileName, $FileSizeBytes, $Extension, $CreationTime, $LastModifiedTime);";

                    using (var command = new SqliteCommand(insertQuery, connection, transaction))
                    {
                        var fullPathParam = command.Parameters.Add("$FullPath", SqliteType.Text);
                        var fileNameParam = command.Parameters.Add("$FileName", SqliteType.Text);
                        var fileSizeBytesParam = command.Parameters.Add("$FileSizeBytes", SqliteType.Integer);
                        var extensionParam = command.Parameters.Add("$Extension", SqliteType.Text);
                        var creationTimeParam = command.Parameters.Add("$CreationTime", SqliteType.Text);
                        var lastModifiedTimeParam = command.Parameters.Add("$LastModifiedTime", SqliteType.Text);

                        foreach (var file in files)
                        {
                            fullPathParam.Value = file.FullPath ?? string.Empty;
                            fileNameParam.Value = file.FileName ?? string.Empty;
                            fileSizeBytesParam.Value = file.FileSizeBytes;
                            extensionParam.Value = file.Extension ?? string.Empty;
                            creationTimeParam.Value = file.CreationTime.ToString("o");
                            lastModifiedTimeParam.Value = file.LastModifiedTime.ToString("o");

                            command.ExecuteNonQuery();
                        }
                    }

                    transaction.Commit();
                }
            }
        }
    }
}
