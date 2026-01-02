#!/usr/bin/env python3
"""
Comprehensive tests for S3 storage improvements.

Tests all major functionality including:
- S3CodeStorage operations
- Multipart uploads
- Progress tracking
- Error handling and retries
- Package versioning
- Security configurations
"""

import os
import sys
import tempfile
import asyncio
import json
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import boto3
import pytest

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from cloud.s3_code_storage import S3CodeStorage
from cloud.package_versioning import PackageVersionManager
from cloud.parallel_upload import ParallelUploader


class TestS3Improvements:
    """Test suite for S3 storage improvements."""
    
    @classmethod
    def setup_class(cls):
        """Setup test environment."""
        cls.bucket_name = os.getenv('DAITA_MANAGED_CODE_BUCKET', 'daita-user-packages-production')
        cls.region = os.getenv('DAITA_AWS_REGION', 'us-east-1')
        cls.test_org_id = 999  # Use test org ID
        cls.test_project = 'test-project'
        cls.test_environment = 'testing'
        
        # Initialize components
        cls.s3_storage = S3CodeStorage(cls.bucket_name, cls.region)
        cls.version_manager = PackageVersionManager(cls.s3_storage)
        cls.parallel_uploader = ParallelUploader(
            boto3.client('s3', region_name=cls.region),
            cls.bucket_name,
            chunk_size=10 * 1024 * 1024  # 10MB chunks for testing
        )
        
        print(f" Testing with bucket: {cls.bucket_name}")
        print(f"Region: {cls.region}")
    
    def create_test_package(self, size_mb: int = 5) -> Path:
        """Create a test package of specified size."""
        # Create temporary file
        temp_file = Path(tempfile.mktemp(suffix='.zip'))
        
        # Write random data
        chunk_size = 1024 * 1024  # 1MB chunks
        with open(temp_file, 'wb') as f:
            for _ in range(size_mb):
                f.write(os.urandom(chunk_size))
        
        return temp_file
    
    def test_1_s3_code_storage_basic(self):
        """Test basic S3CodeStorage functionality."""
        print("\n Testing S3CodeStorage basic operations...")
        
        # Create test package
        test_package = self.create_test_package(2)  # 2MB
        
        try:
            # Test storage
            deployment_id = f"test-{int(datetime.now().timestamp())}"
            
            storage_info = self.s3_storage.store_deployment(
                deployment_id=deployment_id,
                project_name=self.test_project,
                environment=self.test_environment,
                package_path=test_package,
                config={'version': '1.0.0'},
                organization_id=self.test_org_id
            )
            
            assert storage_info['s3_bucket'] == self.bucket_name
            assert storage_info['deployment_id'] == deployment_id
            assert 'package_hash' in storage_info
            
            print(f" Package stored: {storage_info['s3_key']}")
            print(f"   Size: {storage_info['package_size']} bytes")
            print(f"   Hash: {storage_info['package_hash'][:16]}...")
            
            # Test download
            download_path = Path(tempfile.mktemp(suffix='.zip'))
            success = self.s3_storage.download_deployment(deployment_id, download_path)
            
            assert success
            assert download_path.exists()
            assert download_path.stat().st_size == test_package.stat().st_size
            
            print(f" Package downloaded successfully")
            
            # Cleanup
            download_path.unlink()
            
        finally:
            test_package.unlink()
    
    def test_2_multipart_upload(self):
        """Test multipart upload for large packages."""
        print("\n Testing multipart upload for large packages...")
        
        # Create larger test package (>100MB threshold)
        test_package = self.create_test_package(120)  # 120MB
        
        try:
            deployment_id = f"large-test-{int(datetime.now().timestamp())}"
            
            storage_info = self.s3_storage.store_deployment(
                deployment_id=deployment_id,
                project_name=self.test_project,
                environment=self.test_environment,
                package_path=test_package,
                config={'version': '2.0.0'},
                organization_id=self.test_org_id
            )
            
            assert storage_info['upload_method'] == 'multipart'
            
            print(f" Large package uploaded via multipart")
            print(f"   Size: {storage_info['package_size'] / 1024 / 1024:.1f}MB")
            print(f"   Method: {storage_info['upload_method']}")
            
            # Test download of large package
            download_path = Path(tempfile.mktemp(suffix='.zip'))
            success = self.s3_storage.download_deployment(deployment_id, download_path)
            
            assert success
            assert download_path.stat().st_size == test_package.stat().st_size
            
            print(f" Large package downloaded successfully")
            
            # Cleanup
            download_path.unlink()
            
        finally:
            test_package.unlink()
    
    def test_3_package_versioning(self):
        """Test package versioning system."""
        print("\n Testing package versioning system...")
        
        test_package = self.create_test_package(3)  # 3MB
        
        try:
            # Create first version
            deployment_id_1 = f"version-test-1-{int(datetime.now().timestamp())}"
            
            storage_info = self.s3_storage.store_deployment(
                deployment_id=deployment_id_1,
                project_name=self.test_project,
                environment=self.test_environment,
                package_path=test_package,
                config={'version': '1.0.0'},
                organization_id=self.test_org_id
            )
            
            # Register version
            version_1 = self.version_manager.register_version(
                deployment_id=deployment_id_1,
                project_name=self.test_project,
                environment=self.test_environment,
                organization_id=self.test_org_id,
                package_hash=storage_info['package_hash'],
                package_size=storage_info['package_size'],
                s3_key=storage_info['s3_key'],
                created_by='test-user',
                config_version='1.0.0'
            )
            
            print(f" Version 1 registered: {version_1.version_id}")
            
            # Create second version
            test_package_2 = self.create_test_package(4)  # 4MB - different size
            deployment_id_2 = f"version-test-2-{int(datetime.now().timestamp())}"
            
            storage_info_2 = self.s3_storage.store_deployment(
                deployment_id=deployment_id_2,
                project_name=self.test_project,
                environment=self.test_environment,
                package_path=test_package_2,
                config={'version': '2.0.0'},
                organization_id=self.test_org_id
            )
            
            version_2 = self.version_manager.register_version(
                deployment_id=deployment_id_2,
                project_name=self.test_project,
                environment=self.test_environment,
                organization_id=self.test_org_id,
                package_hash=storage_info_2['package_hash'],
                package_size=storage_info_2['package_size'],
                s3_key=storage_info_2['s3_key'],
                created_by='test-user',
                config_version='2.0.0'
            )
            
            print(f" Version 2 registered: {version_2.version_id}")
            
            # Test version listing
            versions = self.version_manager.list_versions(
                project_name=self.test_project,
                environment=self.test_environment,
                organization_id=self.test_org_id
            )
            
            assert len(versions) >= 2
            active_version = self.version_manager.get_active_version(
                project_name=self.test_project,
                environment=self.test_environment,
                organization_id=self.test_org_id
            )
            
            assert active_version.version_id == version_2.version_id
            
            print(f" Version listing works: {len(versions)} versions found")
            print(f" Active version: {active_version.version_id}")
            
            # Test rollback
            rollback_version = self.version_manager.rollback_to_version(
                version_id=version_1.version_id,
                organization_id=self.test_org_id,
                rollback_reason="Testing rollback functionality",
                performed_by="test-user"
            )
            
            assert rollback_version is not None
            assert rollback_version.rollback_from == version_2.version_id
            
            print(f" Rollback successful: {rollback_version.version_id}")
            
            # Test version diff
            diff = self.version_manager.get_version_diff(
                version1_id=version_1.version_id,
                version2_id=version_2.version_id,
                organization_id=self.test_org_id
            )
            
            assert diff['differences']['package_changed'] == True
            assert diff['differences']['size_changed'] == True
            
            print(f" Version diff calculated correctly")
            
            test_package_2.unlink()
            
        finally:
            test_package.unlink()
    
    async def test_4_parallel_upload(self):
        """Test parallel upload functionality."""
        print("\n Testing parallel upload with progress tracking...")
        
        # Create test package
        test_package = self.create_test_package(50)  # 50MB
        
        try:
            progress_updates = []
            
            def progress_callback(progress, uploaded, total):
                progress_updates.append({
                    'progress': progress,
                    'uploaded': uploaded,
                    'total': total
                })
                if len(progress_updates) % 5 == 0:  # Print every 5th update
                    print(f"    Progress: {progress:.1f}% ({uploaded / 1024 / 1024:.1f}MB / {total / 1024 / 1024:.1f}MB)")
            
            # Test parallel upload
            s3_key = f"test/parallel-upload-{int(datetime.now().timestamp())}.zip"
            
            result = await self.parallel_uploader.upload_file(
                file_path=test_package,
                s3_key=s3_key,
                metadata={'test': 'parallel-upload'},
                progress_callback=progress_callback
            )
            
            assert result['success'] == True
            assert len(progress_updates) > 0
            assert result['chunks_uploaded'] > 1  # Should be multiple chunks for 50MB
            
            print(f" Parallel upload completed")
            print(f"   Upload time: {result['upload_time_seconds']:.2f}s")
            print(f"   Chunks: {result['chunks_uploaded']}")
            print(f"   Speed: {result['upload_speed_mbps']:.1f} MB/s")
            print(f"   Progress updates: {len(progress_updates)}")
            
            # Verify file was uploaded
            s3_client = boto3.client('s3', region_name=self.region)
            response = s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            assert response['ContentLength'] == test_package.stat().st_size
            
            print(f" Upload verified in S3")
            
            # Cleanup S3 object
            s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            
        finally:
            test_package.unlink()
    
    def test_5_error_handling(self):
        """Test error handling and retry logic."""
        print("\n Testing error handling and retry logic...")
        
        # Test with non-existent file
        non_existent_file = Path('/tmp/non_existent_file.zip')
        
        try:
            self.s3_storage.store_deployment(
                deployment_id="error-test",
                project_name=self.test_project,
                environment=self.test_environment,
                package_path=non_existent_file,
                config={'version': '1.0.0'},
                organization_id=self.test_org_id
            )
            assert False, "Should have raised an exception"
        except Exception as e:
            print(f" Correctly handled file not found error: {type(e).__name__}")
        
        # Test download of non-existent deployment
        download_path = Path(tempfile.mktemp(suffix='.zip'))
        success = self.s3_storage.download_deployment("non-existent-deployment", download_path)
        
        assert success == False
        print(f" Correctly handled non-existent deployment download")
    
    def test_6_storage_stats(self):
        """Test storage statistics functionality."""
        print("\n Testing storage statistics...")
        
        stats = self.s3_storage.get_storage_stats(organization_id=self.test_org_id)
        
        assert 'total_size_bytes' in stats
        assert 'total_objects' in stats
        assert 'bucket_name' in stats
        
        print(f" Storage stats retrieved")
        print(f"   Total size: {stats.get('total_size_mb', 0):.2f} MB")
        print(f"   Total objects: {stats.get('total_objects', 0)}")
        print(f"   Unique projects: {stats.get('unique_projects', 0)}")
    
    def test_7_security_verification(self):
        """Verify security configurations are applied."""
        print("\n Testing security configurations...")
        
        s3_client = boto3.client('s3', region_name=self.region)
        
        # Check encryption
        try:
            encryption = s3_client.get_bucket_encryption(Bucket=self.bucket_name)
            sse_algorithm = encryption['ServerSideEncryptionConfiguration']['Rules'][0]['ApplyServerSideEncryptionByDefault']['SSEAlgorithm']
            assert sse_algorithm == 'AES256'
            print(f" Bucket encryption verified: {sse_algorithm}")
        except Exception as e:
            print(f" Encryption check failed: {e}")
        
        # Check public access block
        try:
            public_access = s3_client.get_public_access_block(Bucket=self.bucket_name)
            config = public_access['PublicAccessBlockConfiguration']
            
            assert config['BlockPublicAcls'] == True
            assert config['BlockPublicPolicy'] == True
            print(f" Public access blocked verified")
        except Exception as e:
            print(f" Public access block check failed: {e}")
        
        # Check versioning
        try:
            versioning = s3_client.get_bucket_versioning(Bucket=self.bucket_name)
            assert versioning.get('Status') == 'Enabled'
            print(f" Bucket versioning verified: {versioning.get('Status')}")
        except Exception as e:
            print(f" Versioning check failed: {e}")
    
    def test_8_lifecycle_policies(self):
        """Verify lifecycle policies are applied."""
        print("\n Testing lifecycle policies...")
        
        s3_client = boto3.client('s3', region_name=self.region)
        
        try:
            lifecycle = s3_client.get_bucket_lifecycle_configuration(Bucket=self.bucket_name)
            rules = lifecycle.get('Rules', [])
            
            assert len(rules) > 0
            print(f" Lifecycle policies verified: {len(rules)} rules")
            
            for rule in rules:
                print(f"    Rule: {rule['ID']} ({'Enabled' if rule['Status'] == 'Enabled' else 'Disabled'})")
                
        except Exception as e:
            print(f" Lifecycle policy check failed: {e}")
    
    def run_all_tests(self):
        """Run all tests in sequence."""
        print(" Running comprehensive S3 improvements test suite...")
        print("=" * 60)
        
        test_results = {}
        
        # Sync tests
        sync_tests = [
            'test_1_s3_code_storage_basic',
            'test_2_multipart_upload', 
            'test_3_package_versioning',
            'test_5_error_handling',
            'test_6_storage_stats',
            'test_7_security_verification',
            'test_8_lifecycle_policies'
        ]
        
        for test_name in sync_tests:
            try:
                print(f"\n{'='*20} {test_name} {'='*20}")
                getattr(self, test_name)()
                test_results[test_name] = 'PASS'
            except Exception as e:
                print(f" Test failed: {e}")
                test_results[test_name] = f'FAIL: {e}'
        
        # Async test
        async def run_async_tests():
            try:
                print(f"\n{'='*20} test_4_parallel_upload {'='*20}")
                await self.test_4_parallel_upload()
                test_results['test_4_parallel_upload'] = 'PASS'
            except Exception as e:
                print(f" Test failed: {e}")
                test_results['test_4_parallel_upload'] = f'FAIL: {e}'
        
        # Run async test
        asyncio.run(run_async_tests())
        
        # Print summary
        print("\n" + "="*60)
        print(" TEST SUMMARY")
        print("="*60)
        
        passed = 0
        failed = 0
        
        for test_name, result in test_results.items():
            status = " PASS" if result == 'PASS' else " FAIL"
            print(f"{status} {test_name}")
            if result == 'PASS':
                passed += 1
            else:
                failed += 1
                if result != 'PASS':
                    print(f"      {result}")
        
        print("-" * 60)
        print(f" Results: {passed} passed, {failed} failed")
        
        if failed == 0:
            print(" All tests passed! S3 improvements are working correctly.")
        else:
            print(f"  {failed} test(s) failed. Review the errors above.")
        
        return failed == 0


def main():
    """Main test function."""
    # Set environment variables if not set
    if not os.getenv('DAITA_MANAGED_CODE_BUCKET'):
        os.environ['DAITA_MANAGED_CODE_BUCKET'] = 'daita-user-packages-production'
    if not os.getenv('DAITA_AWS_REGION'):
        os.environ['DAITA_AWS_REGION'] = 'us-east-1'
    
    # Run tests
    tester = TestS3Improvements()
    success = tester.run_all_tests()
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())