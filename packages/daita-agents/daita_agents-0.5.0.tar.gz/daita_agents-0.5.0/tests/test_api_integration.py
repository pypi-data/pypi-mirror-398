#!/usr/bin/env python3
"""
Integration test for API upload functionality.

Tests the multipart upload in the API router to ensure it works with the
new S3CodeStorage improvements.
"""

import os
import sys
import tempfile
import asyncio
from pathlib import Path

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.routers.package_upload import _multipart_upload_to_s3, _store_package_in_managed_s3
import boto3
from datetime import datetime, timezone


def create_test_package(size_mb: int = 1) -> Path:
    """Create a test package of specified size."""
    temp_file = Path(tempfile.mktemp(suffix='.zip'))
    
    # Write random data
    chunk_size = 1024 * 1024  # 1MB chunks
    with open(temp_file, 'wb') as f:
        for _ in range(size_mb):
            f.write(os.urandom(chunk_size))
    
    return temp_file


async def test_api_multipart_upload():
    """Test API multipart upload functionality."""
    print(" Testing API multipart upload functionality...")
    
    # Set environment
    bucket_name = os.getenv('DAITA_MANAGED_CODE_BUCKET', 'daita-user-packages-production')
    region = os.getenv('DAITA_AWS_REGION', 'us-east-1')
    
    # Create large test package (>100MB to trigger multipart)
    test_package = create_test_package(120)  # 120MB
    
    try:
        print(f"    Created {test_package.stat().st_size / 1024 / 1024:.1f}MB test package")
        
        # Test the API multipart upload function
        upload_id = f"api-test-{int(datetime.now().timestamp())}"
        
        # Read package content (as the API would)
        with open(test_package, 'rb') as f:
            package_content = bytes(f.read())
        
        # Call API storage function
        result = await _store_package_in_managed_s3(
            upload_id=upload_id,
            project_name='api-integration-test',
            environment='testing',
            organization_id=999,
            package_content=package_content,
            package_hash='test-hash-123'
        )
        
        print(f" API multipart upload completed")
        print(f"   S3 Key: {result['key']}")
        print(f"   Method: {result.get('upload_method', 'unknown')}")
        
        # Verify upload by downloading
        s3_client = boto3.client('s3', region_name=region)
        
        response = s3_client.head_object(
            Bucket=result['bucket'],
            Key=result['key']
        )
        
        if response['ContentLength'] == len(package_content):
            print(f" Upload verification successful ({response['ContentLength']} bytes)")
        else:
            print(f" Size mismatch: expected {len(package_content)}, got {response['ContentLength']}")
            return False
        
        # Cleanup
        s3_client.delete_object(
            Bucket=result['bucket'],
            Key=result['key']
        )
        print(f" Cleanup completed")
        
        return True
        
    except Exception as e:
        print(f" API integration test failed: {e}")
        return False
    finally:
        test_package.unlink()


async def test_api_standard_upload():
    """Test API standard upload for smaller packages."""
    print(" Testing API standard upload functionality...")
    
    # Create small test package (<100MB)
    test_package = create_test_package(5)  # 5MB
    
    try:
        print(f"    Created {test_package.stat().st_size / 1024 / 1024:.1f}MB test package")
        
        upload_id = f"api-std-test-{int(datetime.now().timestamp())}"
        
        # Read package content
        with open(test_package, 'rb') as f:
            package_content = bytes(f.read())
        
        # Call API storage function
        result = await _store_package_in_managed_s3(
            upload_id=upload_id,
            project_name='api-std-test',
            environment='testing',
            organization_id=999,
            package_content=package_content,
            package_hash='test-hash-456'
        )
        
        print(f" API standard upload completed")
        print(f"   Method: {result.get('upload_method', 'unknown')}")
        
        # Cleanup
        s3_client = boto3.client('s3', region_name=result['region'])
        s3_client.delete_object(
            Bucket=result['bucket'],
            Key=result['key']
        )
        
        return True
        
    except Exception as e:
        print(f" API standard upload test failed: {e}")
        return False
    finally:
        test_package.unlink()


async def main():
    """Run integration tests."""
    print(" Running API Integration Tests")
    print("=" * 50)
    
    # Set environment variables
    if not os.getenv('DAITA_MANAGED_CODE_BUCKET'):
        os.environ['DAITA_MANAGED_CODE_BUCKET'] = 'daita-user-packages-production'
    if not os.getenv('DAITA_AWS_REGION'):
        os.environ['DAITA_AWS_REGION'] = 'us-east-1'
    
    tests = [
        ("API Standard Upload", test_api_standard_upload),
        ("API Multipart Upload", test_api_multipart_upload),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*15} {test_name} {'='*15}")
        try:
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f" Test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*50)
    print(" API INTEGRATION TEST RESULTS")
    print("="*50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = " PASS" if success else " FAIL"
        print(f"{status} {test_name}")
    
    print("-" * 50)
    print(f" Results: {passed}/{total} tests passed")
    
    if passed == total:
        print(" All API integration tests passed!")
        return 0
    else:
        print(f"  {total - passed} test(s) failed.")
        return 1


if __name__ == '__main__':
    result = asyncio.run(main())
    sys.exit(result)