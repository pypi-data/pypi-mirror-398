#!/usr/bin/env python3
"""
AgentBay SDK - Context File Operations Example

This example demonstrates comprehensive file management within contexts:
- Uploading files using presigned URLs
- Downloading files using presigned URLs
- Listing files in a context
- Deleting specific files
- Batch file operations
- Error handling and edge cases

Expected Output:
    ======================================================================
    Context File Operations Examples
    ======================================================================

    Example 1: Context Setup and File Preparation
    ======================================================================
    📦 Setting up test context...
    ✅ Created context: file-test-context-1701234567 (SdkCtx-xxxxx)
    📝 Creating test files locally...
    ✅ Created local test file: sample.txt (156 bytes)
    ✅ Created local test file: data.json (2048 bytes)
    ✅ Created local test file: config.yaml (512 bytes)

    Example 2: File Upload Operations
    ======================================================================
    🔼 Uploading files to context...
    ✅ Uploaded sample.txt (156 bytes) in 0.42s
    ✅ Uploaded data.json (2048 bytes) in 0.38s
    ✅ Uploaded config.yaml (512 bytes) in 0.35s
    📊 Upload summary: 3/3 files uploaded successfully

    Example 3: File Listing and Metadata
    ======================================================================
    📋 Listing files in context...
    ✅ Retrieved file list (3 files):
     1. sample.txt (156 bytes)
     2. data.json (2048 bytes)
     3. config.yaml (512 bytes)

    Example 4: File Download Operations
    ======================================================================
    🔽 Downloading files from context...
    ✅ Downloaded sample.txt (156 bytes) in 0.28s
    ✅ Downloaded data.json (2048 bytes) in 0.31s
    ✅ Downloaded config.yaml (512 bytes) in 0.35s
    📊 Download summary: 3/3 files downloaded successfully

    Example 5: File Content Verification
    ======================================================================
    🔍 Verifying file contents...
    ✅ sample.txt content verified
    ✅ data.json content verified
    ✅ config.yaml content verified
    📊 Content verification: 3/3 files verified

    Example 6: Selective File Deletion
    ======================================================================
    🗑️ Deleting specific files...
    ✅ Deleted file: config.yaml
    ✅ Attempted to delete non-existent file: nonexistent.txt (correctly failed)
    📋 Remaining files after deletion:
     1. sample.txt (156 bytes)
     2. data.json (2048 bytes)

    Example 7: Batch Operations and Cleanup
    ======================================================================
    🧹 Cleaning up remaining files...
    ✅ Deleted file: sample.txt
    ✅ Deleted file: data.json
    🧹 Deleting test context...
    ✅ Context deleted successfully

    Example 8: Error Handling and Edge Cases
    ======================================================================
    🧪 Testing error scenarios...
    ❌ Test 1: Invalid context ID - correctly rejected
    ❌ Test 2: Non-existent file path - correctly rejected
    ✅ Error handling tests completed

    ======================================================================
    ✅ All context file operations examples completed successfully!
    ======================================================================
"""

import json
import os
import tempfile
import time
import shutil
from typing import List, Tuple
import requests
import asyncio
from agentbay import AsyncAgentBay


def create_test_files(temp_dir: str) -> List[str]:
    """Create test files for upload testing"""
    test_files = []

    # Create sample.txt
    sample_txt_path = os.path.join(temp_dir, "sample.txt")
    with open(sample_txt_path, "w") as f:
        f.write("This is a sample text file for testing.\n")
        f.write("It contains multiple lines of content.\n")
        f.write("Used to verify file upload and download functionality.\n")
    test_files.append(sample_txt_path)

    # Create data.json
    data_json_path = os.path.join(temp_dir, "data.json")
    test_data = {
        "name": "Test Data",
        "version": "1.0.0",
        "timestamp": time.time(),
        "items": [
            {"id": 1, "value": "first"},
            {"id": 2, "value": "second"},
            {"id": 3, "value": "third"}
        ]
    }
    with open(data_json_path, "w") as f:
        json.dump(test_data, f, indent=2)
    test_files.append(data_json_path)

    # Create config.yaml
    config_yaml_path = os.path.join(temp_dir, "config.yaml")
    with open(config_yaml_path, "w") as f:
        f.write("# Test Configuration File\n")
        f.write("database:\n")
        f.write("  host: localhost\n")
        f.write("  port: 5432\n")
        f.write("  name: test_db\n")
        f.write("\n")
        f.write("logging:\n")
        f.write("  level: INFO\n")
        f.write("  file: app.log\n")
    test_files.append(config_yaml_path)

    return test_files


async def example_1_context_setup(agent_bay: AsyncAgentBay) -> Tuple:
    """Example 1: Set up test context and create local test files"""
    print("\n" + "="*70)
    print("Example 1: Context Setup and File Preparation")
    print("="*70)

    print("📦 Setting up test context...")

    # Create a test context
    timestamp = int(time.time())
    context_name = f"file-test-context-{timestamp}"
    context_result = await agent_bay.context.create(context_name)

    if not context_result.success:
        print(f"❌ Failed to create context: {context_result.error_message}")
        return None, None, None

    context = context_result.context
    print(f"✅ Created context: {context.name} ({context.id})")

    # Create temporary directory for test files
    temp_dir = tempfile.mkdtemp(prefix="agentbay_file_test_")
    print("📝 Creating test files locally...")

    # Create test files
    test_files = create_test_files(temp_dir)

    for file_path in test_files:
        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)
        print(f"✅ Created local test file: {file_name} ({file_size} bytes)")

    return context, temp_dir, test_files


async def example_2_file_upload(agent_bay: AsyncAgentBay, context, test_files: List[str]):
    """Example 2: Upload files to context using presigned URLs"""
    print("\n" + "="*70)
    print("Example 2: File Upload Operations")
    print("="*70)

    if not context or not test_files:
        print("⚠️  No context or files available for upload")
        return []

    print("🔼 Uploading files to context...")

    uploaded_files = []
    successful_uploads = 0

    for file_path in test_files:
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)

        start_time = time.time()

        try:
            # Get presigned upload URL
            upload_result = await agent_bay.context.get_file_upload_url(
                context.id, f"/{file_name}"
            )

            if not upload_result.success:
                print(f"❌ Failed to get upload URL for {file_name}: {upload_result.error_message}")
                continue

            # Upload file using the presigned URL
            with open(file_path, 'rb') as f:
                response = requests.put(upload_result.url, data=f)
                if response.status_code == 200:
                    upload_time = time.time() - start_time
                    print(f"✅ Uploaded {file_name} ({file_size} bytes) in {upload_time:.2f}s")
                    uploaded_files.append(file_name)
                    successful_uploads += 1
                else:
                    print(f"❌ Failed to upload {file_name}: HTTP {response.status_code}")

        except Exception as e:
            print(f"❌ Exception uploading {file_name}: {e}")

    print(f"📊 Upload summary: {successful_uploads}/{len(test_files)} files uploaded successfully")
    return uploaded_files


async def example_3_file_listing(agent_bay: AsyncAgentBay, context):
    """Example 3: List files in context with metadata"""
    print("\n" + "="*70)
    print("Example 3: File Listing and Metadata")
    print("="*70)

    if not context:
        print("⚠️  No context available for file listing")
        return []

    print("📋 Listing files in context...")

    try:
        # List files in the context using real API
        files_result = await agent_bay.context.list_files(context.id, "")
        
        if files_result.success:
            print(f"✅ Retrieved file list ({len(files_result.entries)} files):")
            for i, file_entry in enumerate(files_result.entries, 1):
                print(f" {i}. {file_entry.file_path} ({file_entry.size} bytes) - Modified: {file_entry.gmt_modified}")
            
            return [file_entry.file_name for file_entry in files_result.entries]
        else:
            print(f"❌ Failed to list files: {files_result.error_message}")
            return []

    except Exception as e:
        print(f"❌ Exception listing files: {e}")
        return []


async def example_4_file_download(agent_bay: AsyncAgentBay, context, file_names: List[str], download_dir: str):
    """Example 4: Download files from context using presigned URLs"""
    print("\n" + "="*70)
    print("Example 4: File Download Operations")
    print("="*70)

    if not context or not file_names:
        print("⚠️  No context or files available for download")
        return

    print("🔽 Downloading files from context...")

    successful_downloads = 0

    for file_name in file_names:
        start_time = time.time()

        try:
            # Get presigned download URL
            download_result = await agent_bay.context.get_file_download_url(
                context.id, f"/{file_name}"
            )

            if not download_result.success:
                print(f"❌ Failed to get download URL for {file_name}: {download_result.error_message}")
                continue

            # Download file using the presigned URL
            response = requests.get(download_result.url)
            if response.status_code == 200:
                content = response.content

                # Save the content to a file
                download_path = os.path.join(download_dir, file_name)
                with open(download_path, 'wb') as f:
                    f.write(content)

                download_time = time.time() - start_time
                print(f"✅ Downloaded {file_name} ({len(content)} bytes) in {download_time:.2f}s")
                successful_downloads += 1
            else:
                print(f"❌ Failed to download {file_name}: HTTP {response.status_code}")

        except Exception as e:
            print(f"❌ Exception downloading {file_name}: {e}")

    print(f"📊 Download summary: {successful_downloads}/{len(file_names)} files downloaded successfully")


async def example_5_content_verification(temp_dir: str, download_dir: str, file_names: List[str]):
    """Example 5: Verify file contents match originals"""
    print("\n" + "="*70)
    print("Example 5: File Content Verification")
    print("="*70)

    if not temp_dir or not file_names:
        print("⚠️  No files available for verification")
        return

    print("🔍 Verifying file contents...")

    verified_files = 0

    for file_name in file_names:
        original_path = os.path.join(temp_dir, file_name)
        downloaded_path = os.path.join(download_dir, file_name)

        if not os.path.exists(original_path):
            print(f"⚠️  Original file not found: {file_name}")
            continue

        if not os.path.exists(downloaded_path):
            print(f"⚠️  Downloaded file not found: {file_name}")
            continue

        # Compare the downloaded file with the original file
        with open(original_path, 'rb') as f1, open(downloaded_path, 'rb') as f2:
            original_content = f1.read()
            downloaded_content = f2.read()

            if original_content == downloaded_content:
                print(f"✅ {file_name} content verified")
                verified_files += 1
            else:
                print(f"❌ {file_name} content mismatch")

    print(f"📊 Content verification: {verified_files}/{len(file_names)} files verified")


async def example_6_selective_deletion(agent_bay: AsyncAgentBay, context):
    """Example 6: Delete specific files from context"""
    print("\n" + "="*70)
    print("Example 6: Selective File Deletion")
    print("="*70)

    if not context:
        print("⚠️  No context available for file deletion")
        return

    print("🗑️ Deleting specific files...")

    # Delete a specific file
    try:
        delete_result = await agent_bay.context.delete_file(context.id, "/config.yaml")
        if delete_result.success:
            print("✅ Deleted file: config.yaml")
        else:
            print(f"❌ Failed to delete config.yaml: {delete_result.error_message}")
    except Exception as e:
        print(f"❌ Exception deleting config.yaml: {e}")

    # Try to delete a non-existent file (should fail gracefully)
    try:
        delete_result = await agent_bay.context.delete_file(context.id, "/nonexistent.txt")
        if not delete_result.success:
            print("✅ Attempted to delete non-existent file: nonexistent.txt (correctly failed)")
        else:
            print("⚠️  Non-existent file deletion unexpectedly succeeded")
    except Exception as e:
        print(f"✅ Exception for non-existent file (expected): {str(e)[:50]}...")

    # Show remaining files
    print("📋 Remaining files after deletion:")
    try:
        files_result = await agent_bay.context.list_files(context.id, "/")
        if files_result.success:
            for i, file_entry in enumerate(files_result.entries, 1):
                print(f" {i}. {file_entry.file_path.lstrip('/')} ({file_entry.size} bytes)")
        else:
            print(f"⚠️  Failed to list remaining files: {files_result.error_message}")
    except Exception as e:
        print(f"⚠️  Exception listing remaining files: {e}")


async def example_7_cleanup(agent_bay: AsyncAgentBay, context, temp_dir: str, download_dir: str):
    """Example 7: Clean up remaining files and context"""
    print("\n" + "="*70)
    print("Example 7: Batch Operations and Cleanup")
    print("="*70)

    if not context:
        print("⚠️  No context available for cleanup")
        return

    print("🧹 Cleaning up remaining files...")

    # Get list of remaining files
    try:
        files_result = await agent_bay.context.list_files(context.id, "/")
        if files_result.success:
            deleted_files = 0
            for file_entry in files_result.entries:
                file_name = file_entry.file_path.lstrip('/')
                try:
                    delete_result = await agent_bay.context.delete_file(context.id, file_entry.file_path)
                    if delete_result.success:
                        print(f"✅ Deleted file: {file_name}")
                        deleted_files += 1
                    else:
                        print(f"❌ Failed to delete {file_name}: {delete_result.error_message}")
                except Exception as e:
                    print(f"❌ Exception deleting {file_name}: {e}")
        else:
            print(f"⚠️  Failed to list files for cleanup: {files_result.error_message}")
    except Exception as e:
        print(f"⚠️  Exception during file cleanup: {e}")

    print("🧹 Deleting test context...")

    # Delete the context
    try:
        delete_result = await agent_bay.context.delete(context)
        if delete_result.success:
            print("✅ Context deleted successfully")
        else:
            print(f"❌ Failed to delete context: {delete_result.error_message}")
    except Exception as e:
        print(f"❌ Exception deleting context: {e}")

    # Clean up temporary directories
    for directory in [temp_dir, download_dir]:
        if directory and os.path.exists(directory):
            try:
                shutil.rmtree(directory)
            except Exception as e:
                print(f"⚠️  Failed to clean up directory {directory}: {e}")


async def example_8_error_handling(agent_bay: AsyncAgentBay):
    """Example 8: Error handling and edge cases"""
    print("\n" + "="*70)
    print("Example 8: Error Handling and Edge Cases")
    print("="*70)

    print("🧪 Testing error scenarios...")

    # Test 1: Invalid context ID for file operations
    print("\n❌ Test 1: Invalid context ID")
    try:
        result = await agent_bay.context.get_file_upload_url("invalid-context-id", "/test.txt")
        if not result.success:
            print(f"   ✅ Correctly rejected invalid context ID: {result.error_message[:50]}...")
        else:
            print("   ⚠️  Invalid context ID was accepted (unexpected)")
    except Exception as e:
        print(f"   ✅ Exception caught for invalid context ID: {str(e)[:50]}...")

    # Test 2: Invalid file path
    print("\n❌ Test 2: Non-existent file download")
    try:
        # First create a valid context for testing
        context_result = await agent_bay.context.create(f"error-test-{int(time.time())}")
        if context_result.success:
            context = context_result.context
            # Try to download non-existent file
            result = await agent_bay.context.get_file_download_url(context.id, "/nonexistent.txt")
            if not result.success:
                print(f"   ✅ Correctly rejected non-existent file: {result.error_message[:50]}...")
            else:
                print("   ⚠️  Non-existent file was accepted (unexpected)")

            # Clean up test context
            await agent_bay.context.delete(context)
    except Exception as e:
        print(f"   ✅ Exception for non-existent file: {str(e)[:50]}...")

    print("\n✅ Error handling tests completed")


async def main():
    """Main function demonstrating all context file operations"""
    print("\n" + "="*70)
    print("Context File Operations Examples")
    print("="*70)
    print("\nThese examples demonstrate comprehensive file management within contexts:")
    print("- File upload and download using presigned URLs")
    print("- File listing with metadata")
    print("- Selective file deletion")
    print("- Content verification")
    print("- Batch operations and cleanup")
    print("- Error handling and edge cases")

    # Initialize AgentBay client
    agent_bay = AsyncAgentBay()

    # Variables to hold state between examples
    context = None
    temp_dir = None
    download_dir = None
    test_files = []
    uploaded_files = []

    try:
        # Example 1: Context setup
        context, temp_dir, test_files = await example_1_context_setup(agent_bay)

        if context:
            # Create download directory
            download_dir = tempfile.mkdtemp(prefix="agentbay_downloads_")

            # Example 2: File upload
            uploaded_files = await example_2_file_upload(agent_bay, context, test_files)

            # Example 3: File listing
            listed_files = await example_3_file_listing(agent_bay, context)

            # Example 4: File download
            await example_4_file_download(agent_bay, context, uploaded_files, download_dir)

            # Example 5: Content verification
            await example_5_content_verification(temp_dir, download_dir, uploaded_files)

            # Example 6: Selective deletion
            await example_6_selective_deletion(agent_bay, context)

            # Example 7: Cleanup
            await example_7_cleanup(agent_bay, context, temp_dir, download_dir)

        # Example 8: Error handling
        await example_8_error_handling(agent_bay)

        print("\n" + "="*70)
        print("✅ All context file operations examples completed successfully!")
        print("="*70)

    except Exception as e:
        print(f"\n❌ Example execution failed: {e}")
        import traceback
        traceback.print_exc()

        # Attempt cleanup if needed
        if context:
            try:
                await agent_bay.context.delete(context)
                print("🧹 Emergency cleanup: Context deleted")
            except:
                pass

        for directory in [temp_dir, download_dir]:
            if directory and os.path.exists(directory):
                try:
                    shutil.rmtree(directory)
                    print(f"🧹 Emergency cleanup: Directory {directory} removed")
                except:
                    pass


if __name__ == "__main__":
    asyncio.run(main())
