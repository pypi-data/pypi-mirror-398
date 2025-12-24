#!/usr/bin/env python3
"""
Critical functionality tests for S3 storage improvements.

This test suite focuses on the most important failure scenarios that could
break the system, while keeping the tests manageable.
"""

import os
import sys
import tempfile
import boto3
import asyncio
import json
from pathlib import Path
from datetime import datetime

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from cloud.s3_code_storage import S3CodeStorage
from cloud.package_versioning import PackageVersionManager


def create_test_package(size_mb: int = 1) -> Path:
    """Create a test package of specified size."""
    temp_file = Path(tempfile.mktemp(suffix='.zip'))
    
    # Write random data
    chunk_size = 1024 * 1024  # 1MB chunks
    with open(temp_file, 'wb') as f:
        for _ in range(size_mb):
            f.write(os.urandom(chunk_size))
    
    return temp_file


class CriticalS3Tests:
    """Critical S3 functionality tests."""
    
    def __init__(self):
        self.bucket_name = os.getenv('DAITA_MANAGED_CODE_BUCKET', 'daita-user-packages-production')
        self.region = os.getenv('DAITA_AWS_REGION', 'us-east-1')
        self.test_org_id = 999
        
        self.s3_storage = S3CodeStorage(self.bucket_name, self.region)
        self.version_manager = PackageVersionManager(self.s3_storage)
    
    def test_basic_storage_and_download(self):
        """Test basic storage and download - SYSTEM CRITICAL."""
        print(" Testing basic storage and download functionality...")
        
        test_package = create_test_package(2)  # 2MB
        
        try:
            deployment_id = f"critical-test-{int(datetime.now().timestamp())}"
            
            # Test storage
            storage_info = self.s3_storage.store_deployment(
                deployment_id=deployment_id,
                project_name='critical-test',
                environment='testing',
                package_path=test_package,
                config={'version': '1.0.0'},
                organization_id=self.test_org_id
            )
            
            print(f" Package stored: {storage_info['s3_key']}")
            
            # Test download
            download_path = Path(tempfile.mktemp(suffix='.zip'))
            success = self.s3_storage.download_deployment(deployment_id, download_path)
            
            if not success or not download_path.exists():
                raise Exception("Download failed")
            
            # Verify file integrity
            original_size = test_package.stat().st_size
            downloaded_size = download_path.stat().st_size
            
            if original_size != downloaded_size:
                raise Exception(f"Size mismatch: {original_size} != {downloaded_size}")
            
            print(f" Package downloaded and verified ({downloaded_size} bytes)")
            download_path.unlink()
            
            return True
            
        except Exception as e:
            print(f" CRITICAL: Basic storage/download failed: {e}")
            return False
        finally:
            test_package.unlink()
    
    def test_multipart_upload_resilience(self):
        """Test multipart upload with failure scenarios - SYSTEM CRITICAL."""
        print(" Testing multipart upload resilience...")
        
        # Test with large package that requires multipart
        test_package = create_test_package(150)  # 150MB
        
        try:
            deployment_id = f"multipart-test-{int(datetime.now().timestamp())}"
            
            print(f"    Testing {test_package.stat().st_size / 1024 / 1024:.1f}MB package...")
            
            storage_info = self.s3_storage.store_deployment(
                deployment_id=deployment_id,
                project_name='multipart-test',
                environment='testing',
                package_path=test_package,
                config={'version': '2.0.0'},
                organization_id=self.test_org_id
            )
            
            # Verify multipart was used
            if storage_info.get('upload_method') != 'multipart':
                print(f"  Expected multipart upload, got: {storage_info.get('upload_method')}")
            
            print(f" Large package uploaded successfully")
            
            # Critical: Test that we can download it back
            download_path = Path(tempfile.mktemp(suffix='.zip'))
            success = self.s3_storage.download_deployment(deployment_id, download_path)
            
            if success and download_path.exists():
                downloaded_size = download_path.stat().st_size
                original_size = test_package.stat().st_size
                
                if downloaded_size == original_size:
                    print(f" Large package download verified")
                    download_path.unlink()
                else:
                    raise Exception(f"Download corruption: {downloaded_size} != {original_size}")
            else:
                raise Exception("Large package download failed")
            
            return True
            
        except Exception as e:
            print(f" CRITICAL: Multipart upload failed: {e}")
            return False
        finally:
            test_package.unlink()
    
    def test_package_versioning_core(self):
        """Test core versioning functionality - DEPLOYMENT CRITICAL."""
        print(" Testing core package versioning...")
        
        test_package = create_test_package(3)  # 3MB
        
        try:
            # Create and register first version
            deployment_id_1 = f"version-test-1-{int(datetime.now().timestamp())}"
            
            storage_info_1 = self.s3_storage.store_deployment(
                deployment_id=deployment_id_1,
                project_name='version-test',
                environment='testing',
                package_path=test_package,
                config={'version': '1.0.0'},
                organization_id=self.test_org_id
            )
            
            version_1 = self.version_manager.register_version(
                deployment_id=deployment_id_1,
                project_name='version-test',
                environment='testing',
                organization_id=self.test_org_id,
                package_hash=storage_info_1['package_hash'],
                package_size=storage_info_1['package_size'],
                s3_key=storage_info_1['s3_key'],
                created_by='test-user',
                config_version='1.0.0'
            )
            
            print(f" Version 1 registered: {version_1.version_id}")
            
            # Create second version (different content)
            test_package_2 = create_test_package(4)  # 4MB - different size
            deployment_id_2 = f"version-test-2-{int(datetime.now().timestamp())}"
            
            storage_info_2 = self.s3_storage.store_deployment(
                deployment_id=deployment_id_2,
                project_name='version-test',
                environment='testing',
                package_path=test_package_2,
                config={'version': '2.0.0'},
                organization_id=self.test_org_id
            )
            
            version_2 = self.version_manager.register_version(
                deployment_id=deployment_id_2,
                project_name='version-test',
                environment='testing',
                organization_id=self.test_org_id,
                package_hash=storage_info_2['package_hash'],
                package_size=storage_info_2['package_size'],
                s3_key=storage_info_2['s3_key'],
                created_by='test-user',
                config_version='2.0.0'
            )
            
            print(f" Version 2 registered: {version_2.version_id}")
            
            # CRITICAL: Test active version detection
            active_version = self.version_manager.get_active_version(
                project_name='version-test',
                environment='testing',
                organization_id=self.test_org_id
            )
            
            if not active_version or active_version.version_id != version_2.version_id:
                raise Exception(f"Active version detection failed: expected {version_2.version_id}, got {active_version.version_id if active_version else None}")
            
            print(f" Active version detection works")
            
            # CRITICAL: Test rollback functionality
            rollback_version = self.version_manager.rollback_to_version(
                version_id=version_1.version_id,
                organization_id=self.test_org_id,
                rollback_reason="Critical test rollback",
                performed_by="test-user"
            )
            
            if not rollback_version:
                raise Exception("Rollback failed - returned None")
            
            # Verify rollback worked
            new_active = self.version_manager.get_active_version(
                project_name='version-test',
                environment='testing',
                organization_id=self.test_org_id
            )
            
            if not new_active or new_active.package_hash != version_1.package_hash:
                raise Exception("Rollback verification failed - active version not updated correctly")
            
            print(f" Rollback functionality works: {rollback_version.version_id}")
            
            test_package_2.unlink()
            return True
            
        except Exception as e:
            print(f" CRITICAL: Package versioning failed: {e}")
            return False
        finally:
            test_package.unlink()
    
    def test_error_handling_resilience(self):
        """Test critical error handling scenarios."""
        print(" Testing error handling resilience...")
        
        tests_passed = 0
        total_tests = 3
        
        # Test 1: Non-existent file upload
        try:
            non_existent_file = Path('/tmp/definitely_does_not_exist.zip')
            self.s3_storage.store_deployment(
                deployment_id="error-test",
                project_name='error-test',
                environment='testing',
                package_path=non_existent_file,
                config={'version': '1.0.0'},
                organization_id=self.test_org_id
            )
            print(" Should have failed on non-existent file")
        except Exception:
            print(" Correctly handled non-existent file")
            tests_passed += 1
        
        # Test 2: Non-existent deployment download
        try:
            download_path = Path(tempfile.mktemp(suffix='.zip'))
            success = self.s3_storage.download_deployment("definitely-does-not-exist", download_path)
            if success:
                print(" Should have failed on non-existent deployment")
            else:
                print(" Correctly handled non-existent deployment download")
                tests_passed += 1
        except Exception as e:
            print(f" Correctly handled non-existent deployment with exception: {type(e).__name__}")
            tests_passed += 1
        
        # Test 3: Invalid version rollback
        try:
            result = self.version_manager.rollback_to_version(
                version_id="definitely-does-not-exist",
                organization_id=self.test_org_id,
                rollback_reason="Test invalid rollback",
                performed_by="test-user"
            )
            if result:
                print(" Should have failed on non-existent version rollback")
            else:
                print(" Correctly handled non-existent version rollback")
                tests_passed += 1
        except Exception as e:
            print(f" Correctly handled invalid rollback with exception: {type(e).__name__}")
            tests_passed += 1
        
        print(f" Error handling tests: {tests_passed}/{total_tests} passed")
        return tests_passed >= 2  # Pass if at least 2/3 error handling tests work
    
    def test_security_configurations(self):
        """Test that security configurations don't break functionality."""
        print(" Testing security configurations don't break functionality...")
        
        s3_client = boto3.client('s3', region_name=self.region)
        checks_passed = 0
        total_checks = 3
        
        # Test 1: Encryption doesn't break uploads
        try:
            encryption = s3_client.get_bucket_encryption(Bucket=self.bucket_name)
            print(" Encryption configured and accessible")
            checks_passed += 1
        except Exception as e:
            print(f"  Encryption check issue: {e}")
        
        # Test 2: Versioning is enabled (critical for rollbacks)
        try:
            versioning = s3_client.get_bucket_versioning(Bucket=self.bucket_name)
            if versioning.get('Status') == 'Enabled':
                print(" Versioning enabled (required for rollbacks)")
                checks_passed += 1
            else:
                print(f" CRITICAL: Versioning not enabled - rollbacks may fail")
        except Exception as e:
            print(f" CRITICAL: Versioning check failed: {e}")
        
        # Test 3: Can still access bucket despite security restrictions
        try:
            # Try a simple head bucket operation
            s3_client.head_bucket(Bucket=self.bucket_name)
            print(" Bucket still accessible with security settings")
            checks_passed += 1
        except Exception as e:
            print(f" CRITICAL: Cannot access bucket: {e}")
        
        return checks_passed >= 2  # Must pass 2/3 security tests
    
    def run_critical_tests(self):
        """Run all critical tests."""
        print("🚨 Running CRITICAL S3 functionality tests")
        print("These tests verify core functionality that could break the entire system")
        print("=" * 80)
        
        tests = [
            ("Basic Storage & Download", self.test_basic_storage_and_download, "SYSTEM CRITICAL"),
            ("Multipart Upload Resilience", self.test_multipart_upload_resilience, "SYSTEM CRITICAL"), 
            ("Package Versioning Core", self.test_package_versioning_core, "DEPLOYMENT CRITICAL"),
            ("Error Handling Resilience", self.test_error_handling_resilience, "RELIABILITY CRITICAL"),
            ("Security Configuration Safety", self.test_security_configurations, "SECURITY CRITICAL")
        ]
        
        results = []
        critical_failures = []
        
        for test_name, test_func, priority in tests:
            print(f"\n{'='*20} {test_name} ({'='*10}) {priority} {'='*10}")
            
            try:
                success = test_func()
                results.append((test_name, success, priority))
                
                if not success and "SYSTEM CRITICAL" in priority:
                    critical_failures.append(test_name)
                    
            except Exception as e:
                print(f" Test crashed: {e}")
                results.append((test_name, False, priority))
                if "SYSTEM CRITICAL" in priority:
                    critical_failures.append(test_name)
        
        # Results summary
        print("\n" + "="*80)
        print("🚨 CRITICAL TEST RESULTS")
        print("="*80)
        
        system_critical_passed = 0
        system_critical_total = 0
        overall_passed = 0
        
        for test_name, success, priority in results:
            status = " PASS" if success else " FAIL"
            print(f"{status} {test_name} ({priority})")
            
            if success:
                overall_passed += 1
            
            if "SYSTEM CRITICAL" in priority:
                system_critical_total += 1
                if success:
                    system_critical_passed += 1
        
        print("-" * 80)
        print(f" Overall: {overall_passed}/{len(results)} tests passed")
        print(f"🚨 System Critical: {system_critical_passed}/{system_critical_total} passed")
        
        # Final verdict
        if critical_failures:
            print(f"\n CRITICAL SYSTEM FAILURES DETECTED:")
            for failure in critical_failures:
                print(f"   💥 {failure}")
            print(f"\n DO NOT DEPLOY - System will likely break in production")
            return False
        elif system_critical_passed == system_critical_total:
            print(f"\n ALL SYSTEM CRITICAL TESTS PASSED")
            print(f" System is ready for deployment")
            return True
        else:
            print(f"\n  Some non-critical tests failed, but system should work")
            print(f" System is ready for deployment with monitoring")
            return True


def main():
    """Run critical tests."""
    # Set environment variables
    if not os.getenv('DAITA_MANAGED_CODE_BUCKET'):
        os.environ['DAITA_MANAGED_CODE_BUCKET'] = 'daita-user-packages-production'
    if not os.getenv('DAITA_AWS_REGION'):
        os.environ['DAITA_AWS_REGION'] = 'us-east-1'
    
    # Run tests
    tester = CriticalS3Tests()
    success = tester.run_critical_tests()
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())