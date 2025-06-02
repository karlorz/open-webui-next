import asyncio
import json
import logging
import os
import uuid
import shutil
from typing import Optional, List, Dict, Any

import aiohttp
import websockets
from pydantic import BaseModel

from open_webui.env import SRC_LOG_LEVELS

# Import necessary models for chat and file operations
from open_webui.models.chats import Chats
from open_webui.models.files import Files

# Import the file manager class
from open_webui.utils.code_generated_file_manager import CodeGeneratedFileManager

logger = logging.getLogger(__name__)
logger.setLevel(SRC_LOG_LEVELS["MAIN"])


def generate_dynamic_code_interpreter_prompt(
    base_prompt: str,
    attached_files: List[Dict[str, Any]] = None,
    chat_id: str = "",
) -> str:
    """
    Generate a dynamic code interpreter prompt that includes information about attached files.

    Args:
        base_prompt: The base code interpreter prompt template
        attached_files: List of file metadata dictionaries
        chat_id: Chat ID for context

    Returns:
        Enhanced prompt string with file information
    """
    if not attached_files:
        # No files attached, return the base prompt
        return base_prompt

    # Build file information section
    file_info_lines = []
    file_info_lines.append("\n#### Available Files")
    file_info_lines.append(
        "The following files are available in your `/mnt/data` directory:"
    )

    for file_info in attached_files:
        file_name = file_info.get("name", "unknown_file")
        file_type = file_info.get("type", "file")
        file_size = file_info.get("size")

        # Format file information
        if file_size:
            if file_size > 1024 * 1024:  # > 1MB
                size_str = f" ({file_size / (1024 * 1024):.1f} MB)"
            elif file_size > 1024:  # > 1KB
                size_str = f" ({file_size / 1024:.1f} KB)"
            else:
                size_str = f" ({file_size} bytes)"
        else:
            size_str = ""

        file_info_lines.append(f"- `{file_name}`{size_str}")

    file_info_lines.append("")
    file_info_lines.append(
        "You can access these files directly using their filenames in `/mnt/data/`. For example:"
    )
    file_info_lines.append("```python")
    file_info_lines.append("import pandas as pd")

    # Add example based on first file
    if attached_files:
        first_file = attached_files[0].get("name", "data.csv")
        file_ext = os.path.splitext(first_file)[1].lower()

        if file_ext in [".csv"]:
            file_info_lines.append(f"df = pd.read_csv('/mnt/data/{first_file}')")
        elif file_ext in [".xlsx", ".xls"]:
            file_info_lines.append(f"df = pd.read_excel('/mnt/data/{first_file}')")
        elif file_ext in [".json"]:
            file_info_lines.append(f"import json")
            file_info_lines.append(f"with open('/mnt/data/{first_file}', 'r') as f:")
            file_info_lines.append(f"    data = json.load(f)")
        else:
            file_info_lines.append(f"# Process {first_file}")
            file_info_lines.append(f"with open('/mnt/data/{first_file}', 'r') as f:")
            file_info_lines.append(f"    content = f.read()")

    file_info_lines.append("```")
    file_info_lines.append("")

    # Enhanced saving instruction based on the focused approach from the documentation
    file_info_lines.append(
        "**Important**: Save and persist output only if the user requests the format in Excel, CSV, or PDF file formats in the '/mnt/data' directory."
    )

    file_info_section = "\n".join(file_info_lines)

    # Combine base prompt with file information
    enhanced_prompt = base_prompt + file_info_section

    logger.debug(
        f"Generated dynamic code interpreter prompt for chat {chat_id} with {len(attached_files)} files"
    )

    return enhanced_prompt


def get_attached_files_from_chat(chat_id: str) -> List[Dict[str, Any]]:
    """
    Scan through all messages in a chat to find attached files.
    Returns a list of file metadata dictionaries.
    """
    logger.info(f"Scanning chat {chat_id} for attached files")

    try:
        # Get the chat data
        chat = Chats.get_chat_by_id(chat_id)
        if not chat:
            logger.warning(f"Chat {chat_id} not found")
            return []

        attached_files = []
        chat_data = chat.chat

        # Extract messages from chat history
        messages = chat_data.get("history", {}).get("messages", {})

        for message_id, message in messages.items():
            # Check if message has files attached
            files = message.get("files", [])

            for file_info in files:
                # Extract file metadata
                file_data = {
                    "id": file_info.get("id"),
                    "name": file_info.get("name", "unknown_file"),
                    "type": file_info.get("type", "file"),
                    "size": file_info.get("size"),
                    "url": file_info.get("url"),
                    "message_id": message_id,
                }

                # Only include files with valid IDs
                if file_data["id"]:
                    attached_files.append(file_data)
                    logger.debug(
                        f"Found attached file: {file_data['name']} (ID: {file_data['id']})"
                    )

        logger.info(f"Found {len(attached_files)} attached files in chat {chat_id}")
        return attached_files

    except Exception as e:
        logger.error(f"Error scanning chat {chat_id} for files: {str(e)}")
        return []


async def auto_prepare_chat_files(
    chat_id: str, data_dir: str = "data"
) -> Dict[str, Any]:
    """
    Automatically prepare files attached to chat messages for use in the Jupyter environment.
    Creates symbolic links in the Jupyter data directory pointing to the uploaded files.
    Falls back to copying files if symlinks don't work (e.g., Docker environments).

    Args:
        chat_id: The chat ID to prepare files for
        data_dir: Base data directory (default: "data")

    Returns:
        Dictionary with preparation results including success status, prepared files count, and any errors
    """
    logger.info(f"Auto-preparing files for chat {chat_id}")

    result = {
        "success": False,
        "chat_id": chat_id,
        "prepared_files": [],
        "skipped_files": [],
        "errors": [],
        "total_files": 0,
        "method": None,  # Will be "symlink" or "copy"
    }

    try:
        # Get attached files from chat
        attached_files = get_attached_files_from_chat(chat_id)
        result["total_files"] = len(attached_files)

        if not attached_files:
            logger.info(f"No files found in chat {chat_id}")
            result["success"] = True
            return result

        # Create chat-specific data directory
        chat_data_dir = os.path.join(data_dir, "uploads", chat_id)
        os.makedirs(chat_data_dir, exist_ok=True)
        logger.info(f"Created/verified chat data directory: {chat_data_dir}")

        # Force copy method for Docker compatibility - symlinks often fail in bind volumes
        use_symlinks = False
        method = "copy"
        result["method"] = method
        logger.info(
            f"Using {method} method for file preparation (hardcoded for Docker compatibility)"
        )

        # Track successfully processed files to avoid duplicates
        processed_file_ids = set()

        for file_info in attached_files:
            file_id = file_info["id"]
            file_name = file_info["name"]

            try:
                # Skip if already processed (deduplication)
                if file_id in processed_file_ids:
                    logger.debug(f"Skipping duplicate file {file_name} (ID: {file_id})")
                    result["skipped_files"].append(
                        {"name": file_name, "id": file_id, "reason": "duplicate"}
                    )
                    continue

                # Get file from database
                file_record = Files.get_file_by_id(file_id)
                if not file_record:
                    logger.warning(f"File record not found for ID: {file_id}")
                    result["errors"].append(
                        f"File record not found: {file_name} (ID: {file_id})"
                    )
                    continue

                # Use the actual file path from the database
                if not file_record.path:
                    logger.warning(f"File path not found in record for ID: {file_id}")
                    result["errors"].append(
                        f"File path not found: {file_name} (ID: {file_id})"
                    )
                    continue

                # Get the actual file path (handles different storage providers)
                from open_webui.storage.provider import Storage

                source_file_path = Storage.get_file(file_record.path)

                # Check if source file exists
                if not os.path.exists(source_file_path):
                    logger.warning(f"Source file not found: {source_file_path}")
                    result["errors"].append(f"Source file not found: {file_name}")
                    continue

                # Create target path in chat data directory
                target_path = os.path.join(chat_data_dir, file_name)

                # Remove existing file/symlink if it exists
                if os.path.exists(target_path) or os.path.islink(target_path):
                    if os.path.islink(target_path):
                        os.unlink(target_path)
                        logger.debug(f"Removed existing symlink: {target_path}")
                    else:
                        os.remove(target_path)
                        logger.debug(f"Removed existing file: {target_path}")

                # Copy file
                shutil.copy2(source_file_path, target_path)
                logger.info(f"Copied file: {source_file_path} -> {target_path}")

                # Record successful preparation
                result["prepared_files"].append(
                    {
                        "name": file_name,
                        "id": file_id,
                        "target_path": target_path,
                        "source_path": source_file_path,
                        "size": file_info.get("size"),
                        "type": file_info.get("type"),
                        "method": method,
                    }
                )

                processed_file_ids.add(file_id)

            except Exception as e:
                error_msg = f"Error preparing file {file_name}: {str(e)}"
                logger.error(error_msg)
                result["errors"].append(error_msg)

        # Set success if we prepared at least some files or if there were no errors
        result["success"] = (
            len(result["prepared_files"]) > 0 or len(result["errors"]) == 0
        )

        logger.info(
            f"Auto-prepare completed for chat {chat_id}: "
            f"{len(result['prepared_files'])} prepared using {method}, "
            f"{len(result['skipped_files'])} skipped, "
            f"{len(result['errors'])} errors"
        )

        return result

    except Exception as e:
        error_msg = f"Failed to auto-prepare files for chat {chat_id}: {str(e)}"
        logger.error(error_msg)
        result["errors"].append(error_msg)
        result["success"] = False
        return result


class ResultModel(BaseModel):
    """
    Execute Code Result Model
    """

    stdout: Optional[str] = ""
    stderr: Optional[str] = ""
    result: Optional[str] = ""
    files: Optional[List[Dict]] = []  # Add files attribute for generated files


class EnterpriseGatewayCodeExecutor:
    """
    Execute code in Jupyter Enterprise Gateway
    """

    def __init__(
        self,
        base_url: str,
        code: str,
        token: str = "",
        password: str = "",
        timeout: int = 60,
        kernel_name: str = "python",
        username: str = "code-interpreter",
        chat_id: str = "",
        data_dir: str = "data",
        kernel_init_code: str = "",
        user_id: str = "",
    ):
        """
        :param base_url: Enterprise Gateway server URL (e.g., "http://gateway:8888")
        :param code: Code to execute
        :param token: Authentication token (optional)
        :param password: Password (optional, not typically used with Enterprise Gateway)
        :param timeout: WebSocket timeout in seconds (default: 60s)
        :param kernel_name: Kernel name to use (default: from configuration)
        :param username: Username for the kernel (default: from configuration)
        :param chat_id: Chat ID for path replacement and auto-prepare (optional)
        :param data_dir: Base data directory path (default: "data")
        :param kernel_init_code: Kernel initialization code to run after kernel creation (optional)
        :param user_id: User ID for file registration (optional)
        """
        self.base_url = base_url
        self.original_code = code
        self.token = token
        self.password = password
        self.timeout = timeout
        self.kernel_name = kernel_name
        self.username = username
        self.chat_id = chat_id
        self.data_dir = data_dir
        self.user_id = user_id

        # Initialize file manager for tracking generated files
        self.file_manager = None
        if self.chat_id and self.user_id:
            workspace_path = os.path.join(self.data_dir, "uploads", self.chat_id)
            self.file_manager = CodeGeneratedFileManager(
                chat_id=self.chat_id,
                user_id=self.user_id,
                workspace_path=workspace_path,
            )

        # Modify code to replace /mnt/data with chat-specific path
        self.code = self._prepare_code_with_path_replacement(code)

        # Auto-prepare files for this chat before code execution
        self.prepare_result = None
        if self.chat_id:
            self._auto_prepare_needed = True
            logger.debug(f"Marked auto-prepare as needed for chat {self.chat_id}")
        else:
            self._auto_prepare_needed = False

        if self.base_url[-1] != "/":
            self.base_url += "/"

        logger.info(
            f"Initializing Enterprise Gateway connection to {self.base_url} with kernel {self.kernel_name}"
        )
        if self.chat_id:
            logger.info(f"Using chat ID {self.chat_id} for path replacement")
        self.session = aiohttp.ClientSession(trust_env=True, base_url=self.base_url)
        self.headers = {}
        self.result = ResultModel()
        self.kernel_init_code = kernel_init_code or self._get_default_init_code()

    def _get_default_init_code(self) -> str:
        """Get default kernel initialization code"""
        return """
import os
import sys
import matplotlib.pyplot as plt

# Set up Chinese font support
font_names = [
    'WenQuanYi Micro Hei',
    'Noto Sans CJK SC',
    'SimHei', 'Microsoft YaHei', 'PingFang SC', 
    'Source Han Sans SC', 'Arial Unicode MS'
]
plt.rcParams['font.sans-serif'] = font_names
plt.rcParams['axes.unicode_minus'] = False

print("Kernel initialized successfully")
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")
""".strip()

    def _prepare_code_with_path_replacement(self, code: str) -> str:
        """Replace /mnt/data with chat-specific path before execution"""
        if not self.chat_id:
            logger.debug("No chat_id provided, using code as-is")
            return code

        # Create chat-specific path
        chat_data_path = f"{self.data_dir}/uploads/{self.chat_id}"

        # Ensure the directory exists
        os.makedirs(chat_data_path, exist_ok=True)
        logger.info(f"Ensured chat data path exists: {chat_data_path}")

        # Replace /mnt/data with the chat-specific path
        modified_code = code.replace("/mnt/data", chat_data_path)

        if modified_code != code:
            logger.debug(f"Replaced '/mnt/data' with '{chat_data_path}' in code")

        return modified_code

    def _prepare_results_with_path_replacement(self, text: str) -> str:
        """Replace chat-specific paths back to /mnt/data in output for user display"""
        if not self.chat_id or not text:
            return text

        # Create chat-specific path
        chat_data_path = f"{self.data_dir}/uploads/{self.chat_id}"

        # Replace the chat-specific path back to /mnt/data for user display
        modified_text = text.replace(chat_data_path, "/mnt/data")

        if modified_text != text:
            logger.debug(f"Replaced '{chat_data_path}' back to '/mnt/data' in output")

        return modified_text

    async def _auto_prepare_files(self) -> None:
        """Auto-prepare files for this chat if needed"""
        if not self._auto_prepare_needed or not self.chat_id:
            return

        try:
            self.prepare_result = await auto_prepare_chat_files(
                self.chat_id, self.data_dir
            )
            if self.prepare_result["success"]:
                prepared_count = len(self.prepare_result["prepared_files"])
                if prepared_count > 0:
                    logger.info(
                        f"Successfully prepared {prepared_count} files for chat {self.chat_id}"
                    )
                else:
                    logger.debug(f"No files to prepare for chat {self.chat_id}")
            else:
                logger.warning(
                    f"File preparation had issues for chat {self.chat_id}: {self.prepare_result['errors']}"
                )
        except Exception as e:
            logger.error(
                f"Failed to auto-prepare files for chat {self.chat_id}: {str(e)}"
            )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self, "kernel_id") and self.kernel_id:
            try:
                async with self.session.delete(
                    f"api/kernels/{self.kernel_id}", headers=self.headers
                ) as response:
                    response.raise_for_status()
                    logger.info(f"Closed kernel {self.kernel_id}")
            except Exception as err:
                logger.exception("close kernel failed, %s", err)
        await self.session.close()

    async def run(self) -> ResultModel:
        try:
            # Auto-prepare files first if needed
            await self._auto_prepare_files()

            # Capture pre-execution state for file tracking
            if self.file_manager:
                logger.info(f"Starting file tracking for chat {self.chat_id}")
                self.file_manager.capture_pre_execution_state()
                logger.info(
                    f"Pre-execution state captured, workspace: {self.file_manager.workspace_path}"
                )

            await self.setup_auth()
            await self.init_kernel()
            await self.execute_code()

            # Capture post-execution state and register generated files
            if self.file_manager:
                logger.info("Capturing post-execution state for file tracking")
                self.file_manager.capture_post_execution_state()
                generated_files = self.file_manager.get_newly_generated_files()

                if generated_files:
                    logger.info(f"Found {len(generated_files)} newly generated files:")
                    for i, file_info in enumerate(generated_files):
                        logger.info(
                            f"  {i+1}. {file_info['name']} ({file_info['size']} bytes, {file_info['format']})"
                        )

                    # Register files to storage
                    registered_file_ids = self.file_manager.register_files_to_storage(
                        generated_files
                    )
                    logger.info(
                        f"Attempted to register {len(registered_file_ids)} files"
                    )

                    # Add file information to the result
                    if not hasattr(self.result, "files"):
                        self.result.files = []

                    for file_info, file_id in zip(generated_files, registered_file_ids):
                        if file_id:
                            file_data = {
                                "id": file_id,
                                "name": file_info["name"],
                                "url": f"/api/v1/files/{file_id}/content",  # Fixed: changed from /download to /content
                                "size": file_info["size"],
                                "format": file_info["format"],
                            }
                            self.result.files.append(file_data)
                            logger.info(f"Added file to result: {file_data}")
                        else:
                            logger.warning(
                                f"Failed to register file: {file_info['name']}"
                            )

                    logger.info(
                        f"Successfully registered {len([fid for fid in registered_file_ids if fid])} files to storage"
                    )
                else:
                    logger.info("No new files generated during execution")
            else:
                logger.warning("File manager not initialized - file tracking disabled")

        except Exception as err:
            logger.exception("execute code failed, %s", err)
            self.result.stderr = f"Error: {err}"
        return self.result

    async def setup_auth(self) -> None:
        if self.token:
            self.headers.update({"Authorization": f"token {self.token}"})
            logger.debug("Set up authorization header with token")

    async def init_kernel(self) -> None:
        payload = {
            "name": self.kernel_name,
            "env": {
                "KERNEL_USERNAME": self.username,
                "KERNEL_ID": str(uuid.uuid4()),
            },
        }

        logger.info(f"Starting {self.kernel_name} kernel for user {self.username}")
        try:
            async with self.session.post(
                url="api/kernels",
                json=payload,
                headers=self.headers,
            ) as response:
                response.raise_for_status()
                kernel_data = await response.json()
                self.kernel_id = kernel_data["id"]
                logger.info(f"Created kernel {self.kernel_id} for user {self.username}")

        except Exception as e:
            logger.error(f"Failed to create kernel: {str(e)}")
            raise

    def init_ws(self) -> tuple[str, dict]:
        ws_base = self.base_url.replace("http", "ws", 1)
        websocket_url = f"{ws_base}api/kernels/{self.kernel_id}/channels"
        logger.debug(f"Connecting to WebSocket at {websocket_url}")
        return websocket_url, self.headers

    async def execute_code(self) -> None:
        websocket_url, headers = self.init_ws()
        try:
            async with websockets.connect(
                websocket_url, additional_headers=headers
            ) as ws:
                await self.execute_in_gateway(ws)
        except websockets.exceptions.WebSocketException as e:
            logger.error(f"WebSocket error: {e}")
            self.result.stderr = f"WebSocket connection error: {e}"

    async def execute_in_gateway(self, ws) -> None:
        # Log the code that will be executed
        logger.debug(f"Original code: {self.original_code}")
        logger.debug(f"Modified code (after path replacement): {self.code}")

        # Send message using Enterprise Gateway format
        msg_id = str(uuid.uuid4())
        request = {
            "header": {
                "msg_id": msg_id,
                "msg_type": "execute_request",
                "username": self.username,
                "session": str(uuid.uuid4()),
                "version": "5.4",
            },
            "parent_header": {},
            "metadata": {},
            "content": {
                "code": self.code,
                "silent": False,
                "store_history": True,
                "user_expressions": {},
                "allow_stdin": False,
                "stop_on_error": True,
            },
            "buffers": [],
            "channel": "shell",
        }

        await ws.send(json.dumps(request))

        # Parse responses
        stdout_content, stderr_content = "", ""
        results = []

        while True:
            try:
                message = await asyncio.wait_for(ws.recv(), self.timeout)
                response = json.loads(message)

                # Check if this message is a response to our request
                if response.get("parent_header", {}).get("msg_id") != msg_id:
                    continue

                msg_type = response.get("msg_type")

                if msg_type == "stream":
                    if response["content"]["name"] == "stdout":
                        stdout_content += response["content"]["text"]
                    elif response["content"]["name"] == "stderr":
                        stderr_content += response["content"]["text"]

                elif msg_type == "execute_result":
                    if "data" in response["content"]:
                        if "text/plain" in response["content"]["data"]:
                            result_text = response["content"]["data"]["text/plain"]
                            results.append(result_text)
                        if "image/png" in response["content"]["data"]:
                            results.append(
                                f"data:image/png;base64,{response['content']['data']['image/png']}"
                            )

                elif msg_type == "display_data":
                    if "data" in response["content"]:
                        if "text/plain" in response["content"]["data"]:
                            result_text = response["content"]["data"]["text/plain"]
                            results.append(result_text)
                        if "image/png" in response["content"]["data"]:
                            results.append(
                                f"data:image/png;base64,{response['content']['data']['image/png']}"
                            )

                elif msg_type == "error":
                    error = {
                        "ename": response["content"]["ename"],
                        "evalue": response["content"]["evalue"],
                        "traceback": response["content"]["traceback"],
                    }
                    stderr_content += "\n".join(error["traceback"])

                elif msg_type == "execute_reply":
                    status = response["content"]["status"]
                    if status == "ok":
                        logger.debug("Code execution completed successfully")
                    elif status == "error":
                        logger.debug("Code execution completed with errors")
                    break

            except asyncio.TimeoutError:
                stderr_content += "\nExecution timed out."
                logger.warning(f"Execution timed out after {self.timeout}s")
                break

        # Apply path replacement to results
        self.result.stdout = self._prepare_results_with_path_replacement(
            stdout_content.strip()
        )
        self.result.stderr = self._prepare_results_with_path_replacement(
            stderr_content.strip()
        )
        self.result.result = self._prepare_results_with_path_replacement(
            "\n".join(results).strip() if results else ""
        )

        logger.info("Code execution completed")


async def execute_code_jupyter(
    base_url: str,
    code: str,
    token: str = "",
    password: str = "",
    timeout: int = 60,
    chat_id: str = "",
    data_dir: str = "data",
    kernel_init_code: str = "",
    user_id: str = "",
) -> dict:
    async with EnterpriseGatewayCodeExecutor(
        base_url,
        code,
        token,
        password,
        timeout,
        chat_id=chat_id,
        data_dir=data_dir,
        kernel_init_code=kernel_init_code,
        user_id=user_id,
    ) as executor:
        result = await executor.run()
        return result.model_dump()
