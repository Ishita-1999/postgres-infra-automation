from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator, conint
import re
from datetime import datetime
import uvicorn

app = FastAPI()

# Valid AWS EC2 instance types
VALID_INSTANCE_TYPES = [
    "t2.micro", "t2.small", "t2.medium",
    "t3.micro", "t3.small", "t3.medium",
    "m5.large", "m5.xlarge", "m5.2xlarge",
    # Add more valid instance types as needed
]

class PostgreSQLSetup(BaseModel):
    postgres_version: str
    instance_type: str
    num_replicas: int
    max_connections: conint(ge=1)
    shared_buffers: str

    @validator('instance_type')
    def check_instance_type(cls, v):
        if v not in VALID_INSTANCE_TYPES:
            raise ValueError(
                f"Invalid instance type: '{v}'. Valid types are: {', '.join(VALID_INSTANCE_TYPES)}"
            )
        return v

    @validator('shared_buffers')
    def check_shared_buffers(cls, v):
        if not re.match(r'^\d+(MB|GB)$', v):
            raise ValueError("Invalid format for shared_buffers. Use formats like '256MB' or '1GB'.")
        return v

    @validator('postgres_version')
    def check_postgres_version(cls, v):
        if not re.match(r'^\d+\.\d+$', v):
            raise ValueError("PostgreSQL version must be in the format X.YY.ZZ (e.g., 14.10.20).")
        return v

def generate_timestamped_filename(base_name: str, extension: str) -> str:
    """Generate a timestamped filename with the specified extension."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{base_name}_{timestamp}.{extension}"

def generate_replica_resources(num_replicas: int, instance_type: str) -> str:
    """Generate Terraform resources for replicas."""
    resources = ""
    for i in range(num_replicas):
        resources += f"""
resource "aws_instance" "replica_{i+1}" {{
  ami           = "ami-12345678"  # Replace with a valid PostgreSQL AMI
  instance_type = "{instance_type}"
  tags = {{
    Name = "ReplicaPostgres{i+1}"
  }}
}}
"""
    return resources

@app.post("/generate")
async def generate_all(config: PostgreSQLSetup):
    """Generate both Terraform configuration and Ansible playbook."""
    try:
        # Generate Terraform configuration
        terraform_filename = generate_timestamped_filename('main', 'tf')
        with open(f'{terraform_filename}', 'w') as f:
            f.write(f"""
provider "aws" {{
  region = "us-east-1"
}}

resource "aws_instance" "primary" {{
  ami           = "ami-12345678"  # Replace with a valid PostgreSQL AMI
  instance_type = "{config.instance_type}"
  tags = {{
    Name = "PrimaryPostgres"
  }}
}}

{generate_replica_resources(config.num_replicas, config.instance_type)}

output "primary_ip" {{
  value = aws_instance.primary.public_ip
}}
""")

        # Generate Ansible playbook
        ansible_filename = generate_timestamped_filename('playbook', 'yml')
        with open(f'{ansible_filename}', 'w') as f:
            f.write(f"""
- hosts: all
  become: yes
  tasks:
    - name: Install PostgreSQL
      apt:
        name: postgresql-{config.postgres_version}
        state: present

    - name: Configure PostgreSQL
      template:
        src: pg_hba.conf.j2
        dest: /etc/postgresql/{config.postgres_version}/main/pg_hba.conf
      notify: restart postgresql

    - name: Set max_connections and shared_buffers
      lineinfile:
        path: /etc/postgresql/{config.postgres_version}/main/postgresql.conf
        regexp: '^{{ item.key }}'
        line: '{{ item.key }} = {{ item.value }}'
      with_items:
        - {{ 'max_connections: ' + str(config.max_connections) }}
        - {{ 'shared_buffers: ' + config.shared_buffers }}

  handlers:
    - name: restart postgresql
      service:
        name: postgresql
        state: restarted
""")
        
        return {
            "message": "Terraform and Ansible files generated successfully.",
            "terraform_file": terraform_filename,
            "ansible_file": ansible_filename
        }

    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom exception handler to return only the error message."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

# Entry point for running the app
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
