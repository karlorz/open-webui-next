import os
import logging
import uuid
from pathlib import Path
from typing import List, Dict, Optional, Set
from open_webui.models.files import Files, FileForm

log = logging.getLogger(__name__)


class CodeGeneratedFileManager:
    """Manages tracking and registration of files generated during code execution"""

    TRACKED_EXTENSIONS = {".xlsx", ".xls", ".csv", ".pdf"}

    def __init__(self, chat_id: str, user_id: str, workspace_path: str):
        self.chat_id = chat_id
        self.user_id = user_id
        self.workspace_path = Path(workspace_path)
        self.pre_execution_files: Set[str] = set()
        self.post_execution_files: Set[str] = set()
        self.generated_files: List[Dict] = []

        log.info(
            f"Initialized file manager for chat {chat_id}, user {user_id}, workspace: {workspace_path}"
        )

    def should_track_files(self, code_content: str) -> bool:
        """Determine if code execution should track output files based on content"""
        if not code_content:
            return False

        code_lower = code_content.lower()

        # Check for format-specific keywords
        format_keywords = ["excel", "csv", "pdf", ".xlsx", ".xls", ".csv", ".pdf"]
        save_keywords = ["save", "export", "write", "to_excel", "to_csv", "savefig"]

        has_format = any(keyword in code_lower for keyword in format_keywords)
        has_save_intent = any(keyword in code_lower for keyword in save_keywords)

        should_track = has_format and has_save_intent
        log.info(
            f"File tracking analysis for chat {self.chat_id}: should_track={should_track}, has_format={has_format}, has_save_intent={has_save_intent}"
        )

        return should_track

    def scan_workspace_files(self) -> Set[str]:
        """Scan workspace directory for files with tracked extensions"""
        files = set()

        if not self.workspace_path.exists():
            log.info(f"Workspace directory does not exist: {self.workspace_path}")
            return files

        try:
            for file_path in self.workspace_path.rglob("*"):
                if (
                    file_path.is_file()
                    and file_path.suffix.lower() in self.TRACKED_EXTENSIONS
                ):
                    rel_path = file_path.relative_to(self.workspace_path)
                    files.add(str(rel_path))
                    log.debug(f"Found tracked file: {rel_path}")

            log.info(
                f"Scanned workspace {self.workspace_path}, found {len(files)} tracked files"
            )
        except Exception as e:
            log.error(f"Error scanning workspace {self.workspace_path}: {e}")

        return files

    def capture_pre_execution_state(self):
        """Capture file state before code execution"""
        self.pre_execution_files = self.scan_workspace_files()
        log.info(
            f"Pre-execution state: {len(self.pre_execution_files)} files in workspace"
        )

    def capture_post_execution_state(self):
        """Capture file state after code execution"""
        self.post_execution_files = self.scan_workspace_files()
        log.info(
            f"Post-execution state: {len(self.post_execution_files)} files in workspace"
        )

    def get_newly_generated_files(self) -> List[Dict]:
        """Get files that were generated during execution"""
        new_files = self.post_execution_files - self.pre_execution_files

        log.info(
            f"File comparison: {len(self.post_execution_files)} total files, {len(new_files)} new files generated"
        )

        generated = []
        for rel_path in new_files:
            full_path = self.workspace_path / rel_path
            try:
                if full_path.exists():
                    stat = full_path.stat()
                    file_info = {
                        "name": full_path.name,
                        "path": str(rel_path),
                        "full_path": str(full_path),
                        "size": stat.st_size,
                        "format": full_path.suffix.lower(),
                        "generated_at": stat.st_mtime,
                    }
                    generated.append(file_info)
                    log.info(
                        f"Detected generated file: {file_info['name']} ({file_info['size']} bytes)"
                    )
                else:
                    log.warning(f"Generated file no longer exists: {full_path}")
            except Exception as e:
                log.error(f"Error processing generated file {rel_path}: {e}")

        self.generated_files = generated
        return generated

    def register_files_to_storage(self, file_list: List[Dict]) -> List[Optional[str]]:
        """Register generated files in the system for download"""
        if not file_list:
            log.info(f"No files to register for chat {self.chat_id}")
            return []

        registered_file_ids = []

        for file_info in file_list:
            try:
                full_path = file_info["full_path"]
                file_name = file_info["name"]

                log.info(
                    f"Attempting to register file: {file_name} ({file_info['size']} bytes)"
                )

                # Generate unique file ID
                file_id = str(uuid.uuid4())

                # Create FileForm with correct structure
                form_data = FileForm(
                    id=file_id,
                    filename=file_name,
                    path=full_path,  # Store the full path for access
                    data={},
                    meta={
                        "name": file_name,
                        "content_type": self._get_content_type(file_info["format"]),
                        "size": file_info["size"],
                        "chat_id": self.chat_id,
                        "generated_by": "code_interpreter",
                        "generated_at": file_info["generated_at"],
                        "format": file_info["format"],
                    },
                    access_control=None,
                )

                # Register file in the Files model
                result = Files.insert_new_file(
                    user_id=self.user_id, form_data=form_data
                )

                if result:
                    registered_file_ids.append(file_id)
                    log.info(
                        f"✓ Successfully registered file: {file_name} as ID {file_id}"
                    )

                    # Store metadata linking file to chat
                    self._store_chat_file_metadata(file_id, file_info)
                else:
                    log.error(
                        f"✗ Failed to register file: {file_name} - insert_new_file returned None"
                    )
                    registered_file_ids.append(None)

            except Exception as e:
                log.error(
                    f"✗ Error registering file {file_info.get('name', 'unknown')}: {e}"
                )
                registered_file_ids.append(None)

        successful_registrations = len([fid for fid in registered_file_ids if fid])
        log.info(
            f"File registration complete: {successful_registrations}/{len(file_list)} files registered successfully"
        )
        return registered_file_ids

    def _get_content_type(self, extension: str) -> str:
        """Get content type for file extension"""
        content_types = {
            ".csv": "text/csv",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".xls": "application/vnd.ms-excel",
            ".pdf": "application/pdf",
        }
        return content_types.get(extension.lower(), "application/octet-stream")

    def _store_chat_file_metadata(self, file_id: str, file_info: Dict):
        """Store metadata linking generated file to chat"""
        try:
            # This could be stored in a separate table or as metadata
            # For now, we'll use the chat system to store the relationship
            metadata = {
                "type": "generated_file",
                "file_id": file_id,
                "chat_id": self.chat_id,
                "file_info": file_info,
                "generated_by": "code_interpreter",
            }
            log.debug(f"Stored metadata for generated file {file_id}: {metadata}")
        except Exception as e:
            log.error(f"Error storing metadata for file {file_id}: {e}")
