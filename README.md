# PostgreSQL Setup Automation API

## Overview

This project provides an API to automate the setup of a PostgreSQL primary-read-replica architecture using Terraform and Ansible. Users can configure various parameters such as PostgreSQL version, instance type, number of replicas, and key settings like `max_connections` and `shared_buffers`. The API dynamically generates the necessary Terraform configuration and Ansible playbook files, enabling a streamlined deployment process.

## Features

- **Dynamic Terraform Code Generation**: Generate AWS infrastructure as code to provision PostgreSQL instances.
- **Ansible Playbook Generation**: Create an Ansible playbook for installing and configuring PostgreSQL.
- **Input Validation**: Ensure that user inputs conform to predefined formats and values.
- **Error Handling**: Provides clear error messages for incorrect input.

## Technologies Used

- **FastAPI**: Web framework for building APIs.
- **Pydantic**: Data validation and settings management using Python type annotations.
- **Terraform**: Infrastructure as code for provisioning cloud resources.
- **Ansible**: Configuration management and application deployment tool.

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/postgresql-setup-api.git
   cd postgresql-setup-api
   pip install -r requirements.txt
   python3 app.py

2. **Test API**:
   ```bash
   curl -X POST http://localhost:8001/generate -H "Content-Type: application/json" -d '{"postgres_version": "14.10","instance_type": "t2.micro","num_replicas": 2,"max_connections": 100,"shared_buffers": "256MB"}'


**Expected Response**:

{
    "message": "Terraform and Ansible files generated successfully.",
    "terraform_file": "main_20231019120000.tf",
    "ansible_file": "playbook_20231019120000.yml"
}
