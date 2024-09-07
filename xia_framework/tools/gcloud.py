import subprocess


class CliGCloud:
    @classmethod
    def get_gcp_billing_account(cls):
        get_billing_cmd = f"gcloud billing accounts list --filter='open=true' --format='value(ACCOUNT_ID)' --limit=1"
        r = subprocess.run(get_billing_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        billing_account = r.stdout.strip() if "ERROR" not in r.stderr else None
        return billing_account

    @classmethod
    def create_gcp_project(cls, project_name: str, exists_ok: bool = True):
        check_project_cmd = f"gcloud projects list --filter='{project_name}' --format='value(projectId)'"
        r = subprocess.run(check_project_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        if project_name in r.stdout:
            if exists_ok:
                print(f"Project {project_name} already exists, skip")
            else:
                raise ValueError(f"Project {project_name} already exists")
        else:
            create_proj_cmd = f"gcloud projects create {project_name} --name='{project_name}'"
            r = subprocess.run(create_proj_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
            if "ERROR" not in r.stderr:
                print(f"Project {project_name} created successfully")
            else:
                raise Exception(r.stderr)

    @classmethod
    def link_gcp_billing_project(cls, project_name: str, billing_account: str):
        check_billing_cmd = f"gcloud billing projects describe {project_name} --format='value(billingEnabled)'"
        r = subprocess.run(check_billing_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        if "true" not in str(r.stdout).lower():
            link_billing_cmd = f"gcloud billing projects link {project_name} --billing-account={billing_account}"
            r = subprocess.run(link_billing_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
            if "ERROR" not in r.stderr:
                print(f"Billing Account {billing_account} linked successfully in Cosmos Project {project_name}")
            else:
                raise Exception(r.stderr)

    @classmethod
    def create_gcs_bucket(cls, project_name: str, bucket_name: str, bucket_region: str):
        create_bucket_cmd = (f"gcloud storage buckets create gs://{bucket_name} "
                             f"--uniform-bucket-level-access "
                             f"--location {bucket_region} "
                             f"--project {project_name} ")
        r = subprocess.run(create_bucket_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        if "ERROR" not in r.stderr:
            print(f"Cosmos Bucket {bucket_name} created successfully in {bucket_region}")
        elif "you already own it" in r.stderr:
            print(f"Cosmos Bucket {bucket_name} already exists, skip")
        else:
            raise Exception(r.stderr)

    @classmethod
    def activate_gcp_service(cls, project_name: str, service_name: str):
        enable_api_cmd = f"gcloud services enable {service_name}.googleapis.com --project {project_name}"
        r = subprocess.run(enable_api_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        if "ERROR" not in r.stderr:
            print(f"Service {service_name} enabled successfully in Cosmos Project {project_name}")
        else:
            raise Exception(r.stderr)