import asyncio
import os
import time
import random
import string
import logging
from typing import Dict, List, Any, Optional

import httpx

from agentbay import AsyncAgentBay
from agentbay import Context
from agentbay import AgentBayError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ContextMonitor")

class ContextFileMonitor:
    """Context File Synchronization Monitor"""

    def __init__(self, agent_bay: AsyncAgentBay):
        self.agent_bay = agent_bay
        self.metrics = {
            "upload_times": [],      # File upload duration
            "download_times": [],    # File download duration
            "list_times": [],        # File listing duration
            "file_counts": [],       # Change in file count
            "storage_sizes": [],     # Change in storage size
            "error_counts": {}       # Error statistics
        }

    async def monitor_file_operations(self, context_id: str, file_path: str, file_content: bytes):
        """
        Monitor file operation performance (Upload/Download/List).
        
        Args:
            context_id: The context ID.
            file_path: Path where file will be stored in context.
            file_content: Content of the file to upload.
        """
        logger.info(f"Starting file operation monitoring for {file_path}...")
        
        # 1. Monitor Upload
        try:
            start_time = time.time()
            
            # Get upload URL
            url_result = await self.agent_bay.context.get_file_upload_url(context_id, file_path)
            if not url_result.success:
                raise Exception(f"Failed to get upload URL: {url_result.error_message}")
            
            upload_url = url_result.url
            
            # Perform upload
            async with httpx.AsyncClient() as client:
                response = await client.put(upload_url, content=file_content)
                response.raise_for_status()
                
            duration = time.time() - start_time
            self.metrics["upload_times"].append(duration)
            logger.info(f"Upload successful. Duration: {duration:.4f}s")
            
        except Exception as e:
            self._record_error("upload_error", str(e))
            logger.error(f"Upload failed: {e}")
            return

        # 2. Monitor List
        try:
            start_time = time.time()
            list_result = await self.agent_bay.context.list_files(context_id, "")
            duration = time.time() - start_time
            
            if list_result.success:
                self.metrics["list_times"].append(duration)
                logger.info(f"List files successful. Duration: {duration:.4f}s")
            else:
                raise Exception(f"List files failed: {list_result.error_message}")
                
        except Exception as e:
            self._record_error("list_error", str(e))
            logger.error(f"List files failed: {e}")

        # 3. Monitor Download
        try:
            start_time = time.time()
            
            # Get download URL
            url_result = await self.agent_bay.context.get_file_download_url(context_id, file_path)
            if not url_result.success:
                raise Exception(f"Failed to get download URL: {url_result.error_message}")
                
            download_url = url_result.url
            
            # Perform download
            async with httpx.AsyncClient() as client:
                response = await client.get(download_url)
                response.raise_for_status()
                downloaded_content = response.content
                
            duration = time.time() - start_time
            self.metrics["download_times"].append(duration)
            logger.info(f"Download successful. Duration: {duration:.4f}s")
            
            # Verify content
            if downloaded_content != file_content:
                raise Exception("Downloaded content does not match uploaded content")
            logger.info("Content integrity verified.")
            
        except Exception as e:
            self._record_error("download_error", str(e))
            logger.error(f"Download failed: {e}")

    async def check_file_sync_status(self, context_id: str, expected_files: List[str]):
        """
        Check file synchronization status.
        
        Args:
            context_id: The context ID.
            expected_files: List of file paths expected to exist.
        """
        logger.info("Checking file sync status...")
        try:
            result = await self.agent_bay.context.list_files(context_id, "")
            if not result.success:
                raise Exception(f"Failed to list files: {result.error_message}")
            
            existing_files = [entry.file_path for entry in result.entries]
            
            all_synced = True
            for expected in expected_files:
                # Note: file_path in entries usually starts with /
                normalized_expected = "/" + expected.lstrip("/")
                if normalized_expected not in existing_files:
                    logger.error(f"File missing: {expected}")
                    all_synced = False
            
            if all_synced:
                logger.info("All files are correctly synced.")
            else:
                self._record_error("sync_error", "Files missing in context")
                
        except Exception as e:
            self._record_error("sync_check_error", str(e))
            logger.error(f"Sync check failed: {e}")

    async def monitor_storage_usage(self, context_id: str):
        """
        Monitor storage usage statistics.
        
        Args:
            context_id: The context ID.
        """
        logger.info("Monitoring storage usage...")
        try:
            result = await self.agent_bay.context.list_files(context_id, "")
            if not result.success:
                raise Exception(f"Failed to list files: {result.error_message}")
            
            file_count = len(result.entries)
            total_size = sum(entry.size for entry in result.entries if entry.size)
            
            self.metrics["file_counts"].append(file_count)
            self.metrics["storage_sizes"].append(total_size)
            
            logger.info(f"Current Storage: {file_count} files, {total_size} bytes")
            
            # Analyze file types
            file_types = {}
            for entry in result.entries:
                ext = os.path.splitext(entry.file_name)[1]
                file_types[ext] = file_types.get(ext, 0) + 1
            
            logger.info(f"File Type Distribution: {file_types}")
            
        except Exception as e:
            self._record_error("storage_monitor_error", str(e))
            logger.error(f"Storage monitoring failed: {e}")

    async def health_check_context(self, context_id: str):
        """
        Perform Context health check.
        
        Args:
            context_id: The context ID.
        """
        logger.info("Performing context health check...")
        try:
            # Check accessibility
            result = await self.agent_bay.context.get(context_id=context_id)
            if not result.success:
                raise Exception(f"Context not accessible: {result.error_message}")
            
            logger.info(f"Context {context_id} is accessible.")
            
        except Exception as e:
            self._record_error("health_check_error", str(e))
            logger.error(f"Health check failed: {e}")

    def _record_error(self, error_type: str, message: str):
        """Record error metrics."""
        if error_type not in self.metrics["error_counts"]:
            self.metrics["error_counts"][error_type] = 0
        self.metrics["error_counts"][error_type] += 1

def create_random_content(size_kb: int) -> bytes:
    """Create random content of specified size."""
    return os.urandom(size_kb * 1024)

async def main():
    """Main monitoring flow"""
    # 1. Initialize AgentBay
    agent_bay = AsyncAgentBay()
    monitor = ContextFileMonitor(agent_bay)
    context_name = f"monitor-test-{int(time.time())}"
    context_id = None
    files_to_clean = []

    try:
        # 1. Create Test Context
        logger.info(f"Creating context: {context_name}")
        ctx_result = await agent_bay.context.create(context_name)
        if not ctx_result.success:
            raise Exception(f"Failed to create context: {ctx_result.error_message}")
        
        context_id = ctx_result.context_id
        logger.info(f"Context created with ID: {context_id}")

        # 2. Upload files and monitor performance
        test_files = {
            "small_file.txt": create_random_content(1),    # 1KB
            "medium_file.bin": create_random_content(100), # 100KB
        }

        for filename, content in test_files.items():
            await monitor.monitor_file_operations(context_id, filename, content)
            files_to_clean.append(filename)

        # 3. Check Sync Status
        await monitor.check_file_sync_status(context_id, list(test_files.keys()))

        # 4. Monitor Storage Usage
        await monitor.monitor_storage_usage(context_id)

        # 5. Health Check
        await monitor.health_check_context(context_id)
        
        # Report Metrics
        logger.info("=== Monitoring Report ===")
        logger.info(f"Upload Times: {monitor.metrics['upload_times']}")
        logger.info(f"Download Times: {monitor.metrics['download_times']}")
        logger.info(f"Errors: {monitor.metrics['error_counts']}")

    except Exception as e:
        logger.error(f"An error occurred during monitoring: {e}")
        
    finally:
        # 7. Cleanup Resources
        if context_id:
            logger.info("Cleaning up resources...")
            # Delete files
            for filename in files_to_clean:
                try:
                    await agent_bay.context.delete_file(context_id, filename)
                except Exception as e:
                    logger.warning(f"Failed to delete file {filename}: {e}")
            
            # Delete context
            try:
                # We need the context object to delete
                get_res = await agent_bay.context.get(context_id=context_id)
                if get_res.success and get_res.context:
                    await agent_bay.context.delete(get_res.context)
                    logger.info("Context deleted.")
            except Exception as e:
                logger.warning(f"Failed to delete context: {e}")

if __name__ == "__main__":
    asyncio.run(main())

