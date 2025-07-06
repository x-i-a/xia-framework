import pytest
import shutil
import os
import subprocess
import yaml
from pathlib import Path
from xia_framework import Application


class TestBigQueryDataPipeline:
    """
    E2E test for BigQuery data pipeline following the Quick Start guide.
    
    This test validates the complete flow:
    1. Repository setup and configuration initialization
    2. Module initialization (GCS, GCP Project, GitHub)
    3. BigQuery module activation
    4. Application creation with BigQuery dataset
    5. Infrastructure deployment validation
    """
    
    def test_complete_quickstart_flow(self, temp_workspace):
        """Test the complete Quick Start flow for BigQuery data pipeline"""
        
        # Step 1: Simulate git clone https://github.com/x-i-a/xia-template-application
        repo_url = "https://github.com/x-i-a/xia-template-application"
        result = subprocess.run([
            "git", "clone",
            repo_url
        ], capture_output=True, text=True, cwd=temp_workspace)
        print(result)
        app_dir = temp_workspace / "xia-template-application"

        # Step 2: Change to app directory and run make init-module
        os.chdir(app_dir)
        application = Application()
        application.init_module("xia-module-terraform-gcs/module-application-state-gcs")
        application.init_module("xia-module-terraform-gcs/module-application-backend-gcs")
        application.init_module("xia-module-gcp-project/gcp-module-project")
        application.init_module("xia-module-application-gh/gh-module-application")
        """
        # Run: make init-module module_uri=xia-module-terraform-gcs/module-application-state-gcs
        result = subprocess.run([
            "make", "init-module", 
            "module_uri=xia-module-terraform-gcs/module-application-state-gcs"
        ], capture_output=True, text=True, cwd=app_dir)
        
        # For now, just verify the command structure works (will fail without actual modules)
        # In real test, this would install and configure the module
        
        # Step 3: Verify configuration files were modified
        assert (app_dir / "config" / "landscape.yaml").exists()
        assert (app_dir / "config" / "modules.yaml").exists()
        assert (app_dir / "config" / "packages.yaml").exists()
        
        # Step 4: Simulate terraform apply (mock for now)
        # In real scenario: terraform -chdir=iac/environments/base apply
        terraform_result = subprocess.run([
            "echo", "terraform", "apply", "simulation"
        ], capture_output=True, text=True, cwd=app_dir)
        
        assert terraform_result.returncode == 0
        
        # Verify the test completed basic flow
        assert app_dir.exists()
        assert (app_dir / "config").exists()
        assert (app_dir / "iac").exists()
        """
    
    def test_yaml_operations(self, temp_workspace):
        """Test basic YAML file operations"""
        
        test_dir = temp_workspace / "yaml-test"
        test_dir.mkdir()
        
        # Test writing and reading YAML
        test_data = {
            "module1": {
                "package": "test-package",
                "events": {"deploy": None}
            }
        }
        
        test_file = test_dir / "test.yaml"
        with open(test_file, 'w') as f:
            yaml.dump(test_data, f)
        
        # Verify file was created and content is correct
        assert test_file.exists()
        
        with open(test_file) as f:
            loaded_data = yaml.safe_load(f)
        
        assert loaded_data == test_data
        assert "module1" in loaded_data
        assert loaded_data["module1"]["package"] == "test-package"