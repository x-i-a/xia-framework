import subprocess


class Singularity:
    @classmethod
    def bigbang(cls, **kwargs):
        """Bigbang of different topology

        Args:
            **kwargs: Bigbang parameters
        """


class GcpSingularity:
    @classmethod
    def bigbang(cls, cosmos_project: str, cosmos_bucket_name: str, cosmos_bucket_region: str, **kwargs):
        """GCP Bigbang. Handle project will be defined and Terraform will be saved in the given bucket

        Args:
            cosmos_project: cosmos project to be created
            cosmos_bucket_name: state file of the cosmos to be saved in this bucket
            cosmos_bucket_region: bucket should be located in this region

        """
        # Step 0: Get billing account
        get_billing_cmd = f"gcloud billing accounts list --filter='open=true' --format='value(ACCOUNT_ID)' --limit=1"
        r = subprocess.run(get_billing_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        billing_account = r.stdout if "ERROR" not in r.stderr else None
        print(f"GCP Billing Account detected: {billing_account}")
        # Step 1: Create project
        check_project_cmd = f"gcloud projects list --filter='{cosmos_project}' --format='value(projectId)'"
        r = subprocess.run(check_project_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        if cosmos_project in r.stdout:
            print(f"Cosmos Project {cosmos_project} already exists, skip")
        else:
            create_proj_cmd = f"gcloud projects create {cosmos_project} --name='{cosmos_project}'"
            r = subprocess.run(create_proj_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
            if "ERROR" not in r.stderr:
                print(f"Cosmos Project {cosmos_project} created successfully")
            else:
                raise Exception(r.stderr)
        # Step 2: Activate API services
        for service in ["cloudresourcemanager", "iam", "cloudbilling", "storage"]:
            enable_api_cmd = f"gcloud services enable {service}.googleapis.com --project {cosmos_project}"
            r = subprocess.run(enable_api_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
            if "ERROR" not in r.stderr:
                print(f"Service {service} enabled successfully in Cosmos Project {cosmos_project}")
            else:
                raise Exception(r.stderr)
        # Step 3: Create Bucket for saving terraform state files
        create_bucket_cmd = (f"gcloud storage buckets create {cosmos_bucket_name} "
                             f"--location {cosmos_bucket_region} "
                             f"--project {cosmos_project} ")
        r = subprocess.run(create_bucket_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        if "ERROR" not in r.stderr:
            print(f"Cosmos Bucket {cosmos_bucket_name} created successfully in {cosmos_bucket_region}")
        else:
            raise Exception(r.stderr)
