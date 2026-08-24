using System;

namespace FileManager.Core.Models
{
    public class DriveOverview
    {
        public string DriveName { get; set; } = string.Empty;
        public string VolumeLabel { get; set; } = string.Empty;
        public string DriveFormat { get; set; } = string.Empty;
        public string DriveType { get; set; } = string.Empty;
        public long TotalSizeBytes { get; set; }
        public long FreeSizeBytes { get; set; }
        public long UsedSizeBytes => TotalSizeBytes - FreeSizeBytes;
        public double UsedPercentage => TotalSizeBytes > 0 ? Math.Round((double)UsedSizeBytes / TotalSizeBytes * 100.0, 2) : 0.0;
        public string TotalSizeFormatted => FormatSize(TotalSizeBytes);
        public string FreeSizeFormatted => FormatSize(FreeSizeBytes);
        public string UsedSizeFormatted => FormatSize(UsedSizeBytes);

        public static string FormatSize(long bytes)
        {
            if (bytes >= 1073741824L) // 1 GB
                return $"{(double)bytes / 1073741824L:F2} GB";
            if (bytes >= 1048576L) // 1 MB
                return $"{(double)bytes / 1048576L:F2} MB";
            if (bytes >= 1024L) // 1 KB
                return $"{(double)bytes / 1024L:F2} KB";
            return $"{bytes} Bytes";
        }
    }

    public class CategoryBreakdown
    {
        public string Category { get; set; } = string.Empty;
        public int FileCount { get; set; }
        public long TotalSizeBytes { get; set; }
        public string TotalSizeFormatted => DriveOverview.FormatSize(TotalSizeBytes);
        public double PercentageOfTotal { get; set; }
    }

    public class ExtensionBreakdown
    {
        public string Extension { get; set; } = string.Empty;
        public int FileCount { get; set; }
        public long TotalSizeBytes { get; set; }
        public string TotalSizeFormatted => DriveOverview.FormatSize(TotalSizeBytes);
    }

    public class LargestFileItem
    {
        public string FullPath { get; set; } = string.Empty;
        public string FileName { get; set; } = string.Empty;
        public long FileSizeBytes { get; set; }
        public string FormattedSize => DriveOverview.FormatSize(FileSizeBytes);
        public string Category { get; set; } = string.Empty;
        public DateTime LastModifiedTime { get; set; }
    }
}
