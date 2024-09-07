import subprocess
from xia_framework.tools import CliGCloud


class Singularity:
    @classmethod
    def get_inputs(cls, input_dict: dict) -> dict:
        """Get needed inputs of Bigbang

        Args:
            input_dict (dict): Current input dictionary

        Returns:
            Completed input dict
        """

    @classmethod
    def bigbang(cls, **kwargs):
        """Bigbang of different topology

        Args:
            **kwargs: Bigbang parameters
        """


class GcpSingularity:
    @classmethod
    def get_inputs(cls, input_dict: dict):
        if "cosmos_project" not in input_dict:
            default = input_dict['cosmos_name']
            input_dict["cosmos_project"] = input(f"Enter GCP Cosmos Project Name [{default}]: ") or default
        if "bucket_name" not in input_dict:
            default = input_dict['cosmos_name']
            input_dict["bucket_name"] = input(f"Enter Terraform bucket Name [{default}]: ") or default
        if "bucket_region" not in input_dict:
            default = "eu"
            input_dict["bucket_region"] = input(f"Enter Terraform bucket Region [{default}]: ") or default

        return input_dict

    @classmethod
    def bigbang(cls, cosmos_project: str, bucket_name: str, bucket_region: str, **kwargs):
        """GCP Bigbang. Handle project will be defined and Terraform will be saved in the given bucket

        Args:
            cosmos_project: cosmos project to be created
            bucket_name: state file of the cosmos to be saved in this bucket
            bucket_region: bucket should be located in this region

        """
        # Step 1: Get billing account
        billing_account = CliGCloud.get_gcp_billing_account()
        if not billing_account:
            raise ValueError("No billing account detected, Bigbang won't be successful")
        print(f"GCP Billing Account detected: {billing_account}")
        # Step 2: Create project
        CliGCloud.create_gcp_project(cosmos_project)
        # Step 3: Link project to billing account
        CliGCloud.link_gcp_billing_project(cosmos_project, billing_account)
        # Step 4: Activate API services
        for service in ["cloudresourcemanager", "iam", "cloudbilling", "storage"]:
            CliGCloud.activate_gcp_service(cosmos_project, service)
        # Step 5: Create Bucket for saving terraform state files
        CliGCloud.create_gcs_bucket(cosmos_project, bucket_name, bucket_region)
