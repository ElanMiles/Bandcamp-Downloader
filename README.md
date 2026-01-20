# Bandcamp Downloader

A desktop application for downloading music from Bandcamp with support for multiple audio formats.

## Description

Bandcamp Downloader is a simple tool that allows you to download albums and tracks from Bandcamp. It provides a graphical interface with options for selecting audio format, quality, and various download settings.

## Requirements

- Windows 7/8/10/11
- FFmpeg (required for audio conversion)

## FFmpeg Installation

1. Download FFmpeg from https://ffmpeg.org/download.html
2. Extract the archive
3. Add FFmpeg to system PATH or specify the path in application Settings tab

## How to Use

### Basic Download

1. Open the application
2. Paste Bandcamp album or track URL into the URL field
3. Click Browse and select download folder
4. Choose audio format (MP3, FLAC, WAV, etc.)
5. Select quality (128, 192, 256, 320 kbps)
6. Click Start Download

### Settings Tab

- Embed album artwork in audio file
- Embed metadata (artist, album, track info)
- Create subfolder for each album
- Keep original file after conversion
- Add track number to filename
- Custom filename template
- Custom FFmpeg path

### History Tab

View all previous downloads with timestamps and status.

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

## Troubleshooting

### FFmpeg not found error

Install FFmpeg and add it to system PATH, or specify the full path to ffmpeg.exe in the Settings tab.

### Download fails

- Check if the URL is correct
- Check your internet connection
- Some tracks may not be available for download
