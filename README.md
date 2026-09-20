# Bandcamp Downloader

A desktop application for downloading music from Bandcamp with support for multiple audio formats and batch downloading.

## Description

Bandcamp Downloader is a tool that allows you to download albums and tracks from Bandcamp. It provides a graphical interface with a download queue, light and dark themes, persistent settings, download history, and detailed application logging.

## Requirements

- Windows 7/8/10/11
- FFmpeg (required for audio conversion)

## FFmpeg Installation

1. Download FFmpeg from https://ffmpeg.org/download.html
2. Extract the archive
3. Add FFmpeg to system PATH or specify the path in the application Settings tab
4. Use the "Test FFmpeg" button in Settings to verify the installation

## How to Use

### Basic Download

1. Open the application
2. Paste one or more Bandcamp album or track URLs into the URL field, one per line
3. Click Browse and select a download folder
4. Click Add to Queue
5. Choose audio format (MP3, FLAC, WAV, etc.)
6. Select quality (128, 192, 256, 320 kbps)
7. Click Start Queue

### Batch Downloading

Multiple URLs can be added to the queue at once. Each item is downloaded sequentially, with individual status shown in the queue table (Queued, Downloading, Complete, Error, Cancelled). Items can be removed from the queue before starting, and the entire queue can be cleared.

### Cancelling Downloads

The Cancel button stops the current download and marks any remaining queued items as cancelled.

### Settings Tab

- Light or dark interface theme
- Embed album artwork in audio file
- Embed metadata (artist, album, track info)
- Create subfolder for each album
- Keep original file after conversion
- Add track number to filename
- Custom filename template
- Custom FFmpeg path with a built-in test tool

All settings are saved automatically and restored on the next launch.

### History Tab

View all previous downloads with timestamps, format, and status.

### Logs Tab

View real-time application logs directly in the interface. Logs are also written to a file for troubleshooting. The log file location can be opened directly from the Logs tab.

### Supported Formats

Lossy formats:
- MP3
- AAC
- OGG
- Opus
- Vorbis

Lossless formats:
- FLAC
- WAV
- ALAC
- M4A

### Filename Template Variables

- %(artist)s - Artist name
- %(album)s - Album name
- %(title)s - Track title
- %(track_number)s - Track number
- %(track_number)02d - Track number with leading zero

## Error Handling

The application includes a global error handler for both the interface and background download threads. Unexpected errors are logged and displayed in a dialog window instead of causing the application to crash silently.

## Troubleshooting

### FFmpeg not found error

Install FFmpeg and add it to system PATH, or specify the full path to ffmpeg.exe in the Settings tab. Use the Test FFmpeg button to confirm it is detected correctly.

### Download fails

- Check if the URL is correct and belongs to bandcamp.com
- Check your internet connection
- Some tracks may not be available for download
- Check the Logs tab for detailed error information

### Invalid URL warning

URLs that do not appear to be valid Bandcamp links are skipped when adding to the queue. Verify the URL format before adding it again.
