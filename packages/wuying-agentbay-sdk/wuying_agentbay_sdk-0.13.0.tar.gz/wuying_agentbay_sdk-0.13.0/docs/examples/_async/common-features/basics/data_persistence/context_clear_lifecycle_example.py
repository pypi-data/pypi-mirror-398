"""
Data Lifecycle Management in Context Example

This example demonstrates how to manage the complete lifecycle of file data within a Context,
including:
- Uploading files to Context storage
- Organizing files by type (temporary, cache, logs, important data)
- Implementing intelligent cleanup strategies based on file age, size, and type
- Monitoring storage usage and optimizing space
- Demonstrating before/after cleanup effects with real API calls

Business Scenario:
An application uses Context storage for various file types with different lifecycle requirements:
- Temporary files (temp/): Processing files, cleaned after 1 hour
- Cache files (cache/): API responses, cleaned when > 100MB or > 7 days old
- Log files (logs/): Application logs, kept for 30 days
- Important data (data/): User data, permanently retained
"""

import asyncio
import os
import tempfile
import time
import httpx
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from agentbay import AsyncAgentBay


async def upload_file_to_context(
    agentbay: AsyncAgentBay,
    context_id: str,
    file_path: str,
    content: str
) -> bool:
    """Upload a file to Context storage using presigned URL"""
    try:
        # Get upload URL
        url_result = await agentbay.context.get_file_upload_url(context_id, file_path)
        if not url_result.success:
            print(f"  ✗ Failed to get upload URL for {file_path}: {url_result.error_message}")
            return False

        # Upload file content (no headers - presigned URL is already signed)
        async with httpx.AsyncClient() as client:
            response = await client.put(
                url_result.url,
                content=content.encode('utf-8'),
                timeout=30.0
            )

            if response.status_code in (200, 201, 204):
                return True
            else:
                print(f"  ✗ Upload failed with status {response.status_code}")
                return False

    except Exception as e:
        print(f"  ✗ Error uploading {file_path}: {e}")
        return False


def format_size(size_bytes: int) -> str:
    """Format bytes to human-readable size"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


async def data_lifecycle_demonstration():
    """Complete data lifecycle management demonstration with real API calls"""

    api_key = os.getenv("AGENTBAY_API_KEY")
    if not api_key:
        print("Error: AGENTBAY_API_KEY environment variable not set")
        return

    agentbay = AsyncAgentBay(api_key=api_key)
    context = None

    try:
        print("="*60)
        print("Data Lifecycle Management Example")
        print("="*60)

        # Step 1: Create a working Context
        print("\n[Step 1] Creating working Context...")
        context_name = f"lifecycle-demo-{int(datetime.now().timestamp())}"
        create_result = await agentbay.context.create(context_name)

        if not create_result.success:
            print(f"Failed to create Context: {create_result.error_message}")
            return

        context = create_result.context
        context_id = create_result.context_id
        print(f"✓ Context created: {context_id}")

        # Step 2: Upload different types of files
        print("\n[Step 2] Uploading files to Context...")

        # Define files to upload with their content and metadata
        files_to_upload = [
            # Temporary files
            ("temp/processing_job_1.tmp", f"Temporary processing data\nCreated: {datetime.now()}", "temporary"),
            ("temp/processing_job_2.tmp", f"Another temp file\nCreated: {datetime.now()}", "temporary"),

            # Cache files
            ("cache/api_response_1.json", '{"data": "API response 1", "cached_at": "2024-11-20"}', "cache"),
            ("cache/api_response_2.json", '{"data": "API response 2", "cached_at": "2024-11-25"}', "cache"),
            ("cache/api_response_3.json", '{"data": "Large API response 3" * 1000}', "cache"),

            # Log files
            ("logs/app.log", f"Application log\n{datetime.now()}: System started\n{datetime.now()}: Processing request", "logs"),
            ("logs/error.log", f"Error log\n{datetime.now()}: Minor error occurred", "logs"),

            # Important data
            ("data/user_profile.json", '{"user_id": 123, "name": "Test User", "email": "test@example.com"}', "data"),
            ("data/user_settings.json", '{"theme": "dark", "language": "en"}', "data"),
        ]

        uploaded_count = 0
        for file_path, content, file_type in files_to_upload:
            success = await upload_file_to_context(agentbay, context_id, file_path, content)
            if success:
                print(f"  ✓ Uploaded: {file_path} ({file_type})")
                uploaded_count += 1
            await asyncio.sleep(0.1)  # Small delay to avoid rate limiting

        print(f"\n✓ Successfully uploaded {uploaded_count}/{len(files_to_upload)} files")

        # Wait for files to be indexed (may take a few seconds)
        print("\nWaiting for files to be indexed...")
        max_retries = 10
        retry_count = 0
        initial_files = []

        while retry_count < max_retries:
            await asyncio.sleep(3)
            list_result = await agentbay.context.list_files(context_id, "/")
            if list_result.success and len(list_result.entries) > 0:
                initial_files = list_result.entries
                print(f"✓ Found {len(initial_files)} indexed files")
                break
            retry_count += 1
            print(f"  Retry {retry_count}/{max_retries}...")

        if len(initial_files) == 0:
            print("⚠ Warning: Files uploaded but not yet visible in listing (may need more time to index)")
            print("  The example will continue, but file operations may be limited")

        # Step 3: List and analyze initial storage
        print("\n[Step 3] Initial Storage Statistics")
        print("="*60)
        total_size = sum(entry.size or 0 for entry in initial_files)

        print(f"Total Files: {len(initial_files)}")
        print(f"Total Size: {format_size(total_size)}")
        print(f"\nFiles by Type:")

        # Group by type
        by_type: Dict[str, List] = {}
        for entry in initial_files:
            file_type = entry.file_path.split('/')[0] if '/' in entry.file_path else 'root'
            if file_type not in by_type:
                by_type[file_type] = []
            by_type[file_type].append(entry)

        for file_type, entries in sorted(by_type.items()):
            type_size = sum(e.size or 0 for e in entries)
            print(f"  {file_type:10s}: {len(entries):2d} files, {format_size(type_size):>10s}")

        # Step 4: Apply cleanup strategies
        print("\n[Step 4] Applying Cleanup Strategies...")

        files_to_delete = []

        # Strategy 1: Clean temporary files (simulate age by path)
        print("\n  Strategy 1: Time-based cleanup")
        temp_files = [f for f in initial_files if f.file_path.startswith('temp/')]
        for file in temp_files:
            # In real scenario, you'd check actual file age
            # Here we'll clean files with "job_1" in name to simulate old files
            if 'job_1' in file.file_path:
                files_to_delete.append(file)
                print(f"    → {file.file_path}: Temporary file (simulated old)")

        # Strategy 2: Clean old cache files
        cache_files = [f for f in initial_files if f.file_path.startswith('cache/')]
        for file in cache_files:
            # Clean files with "response_1" or "response_3" to simulate old cache
            if 'response_1' in file.file_path or 'response_3' in file.file_path:
                files_to_delete.append(file)
                print(f"    → {file.file_path}: Old cache file (simulated)")

        # Strategy 3: Protect important data
        print("\n  Strategy 2: Type-based protection")
        data_files = [f for f in initial_files if f.file_path.startswith('data/')]
        print(f"    ✓ Protecting {len(data_files)} important data files from cleanup")

        # Step 5: Execute cleanup
        print("\n[Step 5] Executing Cleanup...")

        deleted_count = 0
        deleted_size = 0

        for file in files_to_delete:
            delete_result = await agentbay.context.delete_file(context_id, file.file_path)
            if delete_result.success:
                print(f"  ✓ Deleted: {file.file_path}")
                deleted_count += 1
                deleted_size += file.size or 0
            else:
                print(f"  ✗ Failed to delete: {file.file_path}")
            await asyncio.sleep(0.1)

        print(f"\n✓ Cleanup completed: {deleted_count} files removed")

        # Small delay to ensure deletions are processed
        await asyncio.sleep(2)

        # Step 6: Display after-cleanup statistics
        print("\n[Step 6] Post-Cleanup Storage Statistics")
        print("="*60)

        final_list_result = await agentbay.context.list_files(context_id, "/")
        if not final_list_result.success:
            print(f"Failed to list files after cleanup")
            return

        final_files = final_list_result.entries
        final_total_size = sum(entry.size or 0 for entry in final_files)

        print(f"Total Files: {len(final_files)}")
        print(f"Total Size: {format_size(final_total_size)}")
        print(f"\nFiles by Type:")

        # Group by type
        final_by_type: Dict[str, List] = {}
        for entry in final_files:
            file_type = entry.file_path.split('/')[0] if '/' in entry.file_path else 'root'
            if file_type not in final_by_type:
                final_by_type[file_type] = []
            final_by_type[file_type].append(entry)

        for file_type, entries in sorted(final_by_type.items()):
            type_size = sum(e.size or 0 for e in entries)
            print(f"  {file_type:10s}: {len(entries):2d} files, {format_size(type_size):>10s}")

        # Step 7: Show cleanup impact
        print("\n[Step 7] Cleanup Impact Analysis")
        print("="*60)

        space_saved = total_size - final_total_size
        files_removed = len(initial_files) - len(final_files)

        print(f"Files Removed: {files_removed}")
        print(f"Space Saved: {format_size(space_saved)}")
        if total_size > 0:
            reduction_pct = (space_saved / total_size * 100)
            print(f"Space Reduction: {reduction_pct:.1f}%")

        print(f"\nRemaining Files:")
        for entry in final_files:
            size_str = format_size(entry.size or 0)
            print(f"  - {entry.file_path:40s} {size_str:>10s}")

        # Step 8: Best practices summary
        print("\n[Step 8] Data Lifecycle Best Practices")
        print("="*60)
        print("✓ Upload files with organized directory structure")
        print("✓ Monitor storage usage regularly with list_files API")
        print("✓ Implement cleanup policies based on file type and age")
        print("✓ Protect critical data from automatic cleanup")
        print("✓ Use delete_file API to remove obsolete data")
        print("✓ Verify cleanup impact before and after operations")

    except Exception as e:
        print(f"\nError during data lifecycle demonstration: {e}")
        import traceback
        traceback.print_exc()
        raise

    finally:
        # Cleanup: Delete the test Context
        if context:
            print(f"\n[Cleanup] Deleting test Context...")
            try:
                delete_result = await agentbay.context.delete(context)
                if delete_result.success:
                    print(f"✓ Context deleted: {context.id}")
                else:
                    print(f"⚠ Failed to delete Context: {delete_result.error_message}")
            except Exception as e:
                print(f"⚠ Error deleting Context: {e}")

        print("\n" + "="*60)
        print("Data Lifecycle Management Example Completed")
        print("="*60)


async def main():
    """Run the data lifecycle management demonstration"""
    await data_lifecycle_demonstration()


if __name__ == "__main__":
    asyncio.run(main())
