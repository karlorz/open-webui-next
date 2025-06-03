# Code Interpreter File Storage Plan

## ✅ IMPLEMENTATION STATUS: CORE SYSTEM COMPLETE + FOCUSED SCOPE + MESSAGE-BASED DESIGN

### 🎯 CURRENT STATE SUMMARY

**✅ FULLY IMPLEMENTED FEATURES:**

- Smart file linking system with symlinks/copying fallback
- Bidirectional path translation (`/mnt/data` ↔ `data/uploads/{message_id}`)
- Message-specific workspace isolation (updated from chat-based)
- Auto-prepare functionality for message-attached files
- Docker environment compatibility
- Dynamic prompt enhancement with message file information
- Jupyter Gateway execution engine (server-based)

**✅ UPDATED SCOPE FEATURES:**

- Modified default prompt: Files saved only when user requests Excel, CSV, or PDF formats
- Image handling via existing cache system (unchanged)
- Jupyter Gateway focus (Pyodide unchanged)
- Message-level file scanning instead of chat-level scanning

**🔄 REMAINING TASKS:**

- User-requested file detection (Excel, CSV, PDF only)
- Format-specific download API
- Targeted frontend download UI

## ✅ IMPLEMENTED SOLUTION: Smart File Linking + Selective Saving + Message Isolation

### Overview

The core file management system is **FULLY IMPLEMENTED** and working with **ENHANCED SELECTIVITY** and **MESSAGE-BASED ISOLATION**. Files are handled through a **request-driven system** that distinguishes between:

- **Input files**: ✅ Symlinked from main storage (auto-prepared from specific message)
- **Output files**: 🔄 Created only when user explicitly requests Excel, CSV, PDF formats
- **Images**: ✅ Auto-handled via existing cache system (matplotlib plots)

### 🔑 Updated Design Principles

#### 1. Message-Based File Isolation ✅ IMPLEMENTED

**New workspace structure:**

```
data/uploads/{message_id}/        # Message-specific workspace
├── input_file1.csv              # Files attached to this message
├── input_file2.xlsx             # Files attached to this message
└── generated_output.pdf         # Files created during execution
```

**Benefits of message-based approach:**

- ✅ **Precise File Access**: Only files from the specific message are available
- ✅ **Better Security**: No cross-message file access
- ✅ **Cleaner Workspaces**: Each execution gets isolated environment
- ✅ **Simplified Scanning**: Direct message file lookup instead of chat scanning
- ✅ **Improved Performance**: No need to scan entire chat history

#### 2. Request-Driven File Persistence ✅ IMPLEMENTED

**Modified default code interpreter prompt:**

```
"Save and persist output only if the user requests the format in Excel, CSV, or PDF file formats in the '/mnt/data' directory."
```

**Benefits of this approach:**

- ✅ **Reduced Storage Overhead**: Only save files when explicitly requested
- ✅ **Clear User Intent**: Files saved match user expectations
- ✅ **Format-Specific**: Focus on business-ready formats (Excel, CSV, PDF)
- ✅ **Existing Image System**: Leverage current matplotlib cache for plots
- ✅ **No Breaking Changes**: Maintains all existing functionality

#### 3. Jupyter Gateway Focused Architecture ✅ IMPLEMENTED

**Single execution engine focus:**

1. **✅ Jupyter/Enterprise Gateway**: Full server-based execution with file system access
2. **❌ Pyodide Modifications**: Browser-based engine remains unchanged
3. **✅ Image Cache Integration**: Existing matplotlib/plot handling preserved
4. **✅ Path Translation**: Same `/mnt/data` ↔ `data/uploads/{message_id}` system

### ✅ CONFIRMED TECHNICAL IMPLEMENTATION

#### Enhanced Message-Based File Strategy ✅ IMPLEMENTED

**Core Strategy:**

1. **✅ Message Workspace Isolation**: Each message gets `data/uploads/{message_id}/` directory
2. **✅ Message File Linking**: Symlink/copy files attached to specific message
3. **✅ Path Translation**: `/mnt/data` ↔ `data/uploads/{message_id}` (bidirectional)
4. **🔄 Selective Output Tracking**: Monitor only Excel, CSV, PDF files when requested (NEEDED)
5. **✅ Image Cache System**: Matplotlib plots handled via existing cache system
6. **✅ Result Path Cleanup**: Translate paths back to `/mnt/data` in results

#### Message-Based File Detection ✅ IMPLEMENTED

**New file scanning approach:**

```python
# Get files from specific message instead of scanning entire chat
def get_attached_files_from_message(message_id: str, chat_id: str) -> List[Dict[str, Any]]:
    """Get attached files from a specific message ID."""
    # Direct message lookup - no chat scanning needed
    message = get_message_by_id(message_id, chat_id)
    return message.get("files", [])

# Updated workspace preparation
async def auto_prepare_message_files(
    attached_files: List[Dict[str, Any]],
    workspace_id: str,  # Now uses message_id
    data_dir: str = "data"
) -> Dict[str, Any]:
    """Prepare files attached to a specific message."""
    # Create message-specific workspace
    workspace_data_dir = os.path.join(data_dir, "uploads", workspace_id)
    # Process only files from this message
```

### ✅ UPDATED WORKFLOW EXAMPLE

```
1. ✅ User uploads "data.csv" → data/uploads/abc123_data.csv (Files table)
2. ✅ User starts chat with file attached to specific message (msg_456)
3. ✅ LLM generates code: "Please save the analysis as an Excel file to /mnt/data/"
4. ✅ Code interpreter triggered:
   a. ✅ Message file scan: Get files from message msg_456 only
   b. ✅ Auto-prepare: symlink data.csv to data/uploads/msg_456/data.csv
   c. ✅ Code analysis: Detects Excel format request
   d. ✅ Path replacement: /mnt/data → data/uploads/msg_456 in code
   e. ✅ Execute in Jupyter Gateway kernel
   f. 🔄 Monitor workspace for .xlsx/.csv/.pdf files (NEEDED)
   g. 🔄 Register outputs: analysis.xlsx → downloadable file (NEEDED)
   h. ✅ Path replacement: data/uploads/msg_456 → /mnt/data in results
5. ✅ User sees: "Saved analysis to /mnt/data/analysis.xlsx"
6. 🔄 Download UI: Shows "analysis.xlsx" available for download (NEEDED)
```

## 🔄 REMAINING IMPLEMENTATION TASKS

### Phase 1: User-Requested File Detection (HIGH PRIORITY)

**NEEDED**: RequestedFileTracker class for Excel, CSV, PDF detection

- Smart detection based on code content and file extensions
- Before/after execution state comparison
- Integration with existing EnterpriseGatewayCodeExecutor
- Message-specific workspace monitoring

**Target**: Enhance existing `EnterpriseGatewayCodeExecutor.run()` method

### Phase 2: Format-Specific Download API (HIGH PRIORITY)

**NEEDED**: REST endpoints for requested file formats only

- `/api/v1/downloads/code-execution/{message_id}/files` (Excel, CSV, PDF only)
- Security validation for allowed file types
- Format filtering and metadata
- Message-based file organization

**Target**: New `backend/open_webui/routers/downloads.py` module

### Phase 3: Targeted Frontend Integration (MEDIUM PRIORITY)

**NEEDED**: UI components for requested file downloads

- Format-specific icons and handling
- Detection of file format requests in code
- Integration with existing CodeBlock component
- Message-specific file listing

**Target**: Enhance existing `CodeBlock.svelte` with requested files panel

## ✅ CONFIRMED BENEFITS OF MESSAGE-BASED APPROACH

✅ **Precise File Access**: Only files from specific message are available  
✅ **Better Security**: No cross-message contamination  
✅ **Cleaner Workspaces**: Each execution starts fresh  
✅ **Simplified Logic**: Direct message lookup instead of chat scanning  
✅ **Performance Optimized**: No need to scan entire chat history  
✅ **Clear Isolation**: Message-level workspace boundaries  
✅ **Reduced Complexity**: Eliminates chat-level file management  
✅ **Format Consistency**: Excel, CSV, PDF are business-standard formats  
✅ **Existing Image System**: Leverage proven matplotlib cache system  
✅ **Single Engine Focus**: Jupyter Gateway only, no Pyodide changes  
✅ **Path Transparency**: Users see familiar `/mnt/data` paths consistently

## 🔍 INTEGRATION WITH EXISTING SYSTEMS

### Message-Based File Handling (Enhanced) ✅

- **Message File Access**: Direct lookup from message metadata
- **Message Workspaces**: Isolated `data/uploads/{message_id}/` directories
- **Path Translation**: Same `/mnt/data` system but message-scoped
- **Security Model**: Message-level workspace isolation

### Current Image Handling (Unchanged) ✅

- **Matplotlib Plots**: Auto-captured via existing cache system
- **Display Integration**: Images already shown in chat interface
- **Base64 Encoding**: Proven system for plot visualization
- **No Modification Needed**: Image system works perfectly as-is

### Execution Engine (Focused) ✅

- **Jupyter Gateway**: Primary execution environment for file operations
- **Pyodide**: Remains unchanged, no modifications planned
- **Code Translation**: Message-based path replacement system
- **Result Processing**: Same bidirectional path cleanup

## ✅ FINAL STATUS SUMMARY

**✅ CORE SYSTEM: FULLY OPERATIONAL + MESSAGE-BASED ISOLATION**

- Message-specific file preparation and access system complete
- Path translation working seamlessly with message workspaces
- Message isolation and security implemented
- Request-driven file saving strategy implemented
- Single engine focus (Jupyter Gateway) confirmed

**🔄 MISSING COMPONENTS: TARGETED OUTPUT HANDLING**

- User-requested file detection (Excel, CSV, PDF only)
- Format-specific download API with message organization
- Targeted frontend download interface

**📊 COMPLETION STATUS: ~85% COMPLETE**

- Major infrastructure: ✅ DONE (now message-based)
- Enhanced scope definition: ✅ DONE
- Remaining work: Format-specific file detection and download UI
- Implementation effort: ~1-2 weeks for remaining focused features

**🎯 STRATEGIC ADVANTAGES:**

- **Message Isolation**: Each code execution is completely isolated
- **Precise File Access**: Only relevant files are available
- **Simplified Architecture**: No chat-level file scanning complexity
- **Better Performance**: Direct message file lookup
- **Enhanced Security**: Message-level workspace boundaries
- **Proven Foundation**: Build on existing robust message-based system
- **Single Engine**: Jupyter Gateway focus simplifies implementation
- **Image System Preserved**: Leverage existing matplotlib cache system

The message-based approach significantly improves file isolation and simplifies the architecture while delivering exactly what users need: downloadable business files (Excel, CSV, PDF) when they explicitly request them, with complete workspace isolation per message.
