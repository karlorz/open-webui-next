# Code Interpreter Auto-Prepare Feature

## Overview

The auto-prepare feature automatically detects and prepares files attached to chat messages for use in the Jupyter code interpreter environment. This feature helps identify and resolve filesystem access issues by ensuring files are available when code execution begins.

## How It Works

### Automatic Detection

When code execution is triggered in a chat with the code interpreter enabled, the system:

1. **Scans Chat Messages**: Searches through all messages in the chat to find attached files
2. **Extracts File Metadata**: Collects file IDs, names, and other metadata from message attachments
3. **Creates Symlinks**: Automatically creates symbolic links in the Jupyter data directory pointing to the uploaded files
4. **Deduplicates**: Avoids creating duplicate links for the same file ID

### File Preparation Process

```python
# Before code execution:
chat_files = get_attached_files_from_chat(chat_id)
prepared_files = await auto_prepare_chat_files(chat_id, data_dir)

# Files are now available in the Jupyter environment at:
# /data/filename.ext -> points to actual uploaded file
```

### Directory Structure

```
Jupyter Environment:
├── data/
│   ├── data.csv -> symlink to uploaded file
│   ├── report.pdf -> symlink to uploaded file
│   └── analysis.py -> symlink to uploaded file
└── ... (other directories)

Backend Storage:
├── uploads/
│   ├── file_id_123 (actual data.csv)
│   ├── file_id_456 (actual report.pdf)
│   └── file_id_789 (actual analysis.py)
└── ... (other files)
```

## Benefits

### 1. Immediate File Availability

- Files are ready before code execution begins
- No need for manual file upload or preparation steps
- Seamless user experience

### 2. Filesystem Issue Detection

- Helps identify permission problems early
- Reveals symlink support issues
- Exposes path resolution problems

### 3. Testing and Debugging

- Provides clear visibility into file preparation process
- Logs all operations for troubleshooting
- Maintains relative paths for portability

## Implementation Details

### Key Functions

#### `auto_prepare_chat_files(chat_id, data_dir)`

Main function that prepares files for a specific chat:

- **chat_id**: The chat identifier to search for attached files
- **data_dir**: Target directory in Jupyter environment (usually "data")
- **Returns**: List of successfully prepared file paths

#### `execute_code_jupyter()` (Enhanced)

Modified to automatically call auto-prepare when chat_id is provided:

- Calls `auto_prepare_chat_files()` before executing code
- Continues execution even if file preparation fails
- Logs preparation results for debugging

### File Safety Features

#### Filename Sanitization

```python
safe_filename = "".join(c for c in file_name if c.isalnum() or c in "._- ").strip()
```

#### Duplicate Handling

- Removes existing symlinks before creating new ones
- Tracks processed file IDs to avoid duplicates
- Uses relative paths for better portability

#### Error Handling

- Graceful failure when source files don't exist
- Continues with other files if one fails
- Logs all errors for debugging

## Integration Points

### Middleware Integration

The feature integrates with the existing middleware at the code execution point:

```python
# In middleware.py, around line 2060:
output = await execute_code_jupyter(
    # ... existing parameters ...
    chat_id=metadata.get("chat_id", ""),  # Auto-prepare trigger
    data_dir="data"
)
```

### Chat Message Processing

Files are detected from chat message metadata:

```python
metadata = message_data.get("metadata", {})
files = metadata.get("files", [])
for file_info in files:
    file_id = file_info.get("id")
    file_name = file_info.get("name", f"file_{file_id}")
    # Process file...
```

## Configuration

### Environment Variables

The feature respects existing configuration:

- `UPLOAD_DIR`: Source directory for uploaded files
- Code interpreter settings (engine, URLs, auth, timeouts)

### Default Behavior

- **Enabled**: Automatically when `chat_id` is provided to `execute_code_jupyter()`
- **Directory**: Uses "data" as the default target directory
- **Logging**: Logs operations at INFO level for prepared files

## Error Scenarios and Handling

### Common Issues

#### 1. Missing Source Files

```
WARNING: Source file not found: /path/to/uploads/file_id_123
```

**Cause**: File was deleted or moved from upload directory
**Handling**: Logs warning and continues with other files

#### 2. Permission Errors

```
ERROR: Failed to create symlink for filename.ext: [Errno 13] Permission denied
```

**Cause**: Insufficient permissions to create symlinks
**Handling**: Logs error and continues with other files

#### 3. Symlink Support

```
ERROR: Failed to create symlink for filename.ext: [Errno 38] Function not implemented
```

**Cause**: Filesystem doesn't support symlinks (rare on modern systems)
**Handling**: Logs error and continues with other files

### Debugging Steps

1. **Check Logs**: Look for auto-prepare messages in the application logs
2. **Verify Upload Directory**: Ensure `UPLOAD_DIR` contains the expected files
3. **Test Permissions**: Verify the process can create files in the data directory
4. **Check Symlink Support**: Test manual symlink creation in the environment

## Testing

### Unit Tests

Use the provided test script to verify functionality:

```bash
python test_auto_prepare.py
```

### Manual Testing

1. Upload files to a chat
2. Enable code interpreter
3. Execute code that references uploaded files
4. Check logs for auto-prepare messages
5. Verify files are accessible in code

### Expected Behavior

- Files appear in `/data/` directory
- Code can read files using original filenames
- Symlinks point to correct source files
- No duplicate preparations for same files

## Troubleshooting

### File Not Found in Code

1. Check if file was uploaded to the chat
2. Verify the filename matches exactly
3. Look for auto-prepare log messages
4. Check if symlink was created successfully

### Permission Denied Errors

1. Verify process permissions
2. Check directory ownership
3. Test manual symlink creation
4. Review filesystem mount options

### Performance Considerations

- File preparation happens once per code execution
- Uses symlinks (minimal disk space overhead)
- Relative paths for portability
- Efficient deduplication of repeated files

## Future Enhancements

### Potential Improvements

1. **File Caching**: Cache prepared files across multiple executions
2. **Cleanup**: Automatic cleanup of old symlinks
3. **File Watching**: Monitor for file changes and update symlinks
4. **Advanced Filtering**: Option to filter files by type or size
5. **Custom Mapping**: User-defined file name mappings

### Integration Opportunities

1. **Database Tracking**: Store preparation status in database
2. **User Notifications**: Inform users about file preparation status
3. **Analytics**: Track which files are most commonly used
4. **Bulk Operations**: Prepare multiple chats at once
