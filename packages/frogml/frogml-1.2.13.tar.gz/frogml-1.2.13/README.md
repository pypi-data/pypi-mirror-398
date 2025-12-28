# Frogml

Frogml is an end-to-end production ML platform designed to allow data scientists to build, deploy, and monitor their models in production with minimal engineering friction.
Frogml Core contains all the objects and tools necessary to use the Frogml Platform

## Table of contents:

- [Overview](#overview)
- [Working with Artifactory](#Working-with-Artifactory)
- [Upload ML model to Artifactory](#Upload-ML-model-to-Artifactory)
- [Local Development Setup](#local-development-setup)

## Overview

JFrog ML Storage is a smart python client library providing a simple and efficient method of storing and downloading models, model data and datasets from the JFrog platform, utilizing the advanced capabilities of the JFrog platform.

## Working with Artifactory

FrogML Storage Library support is available from Artifactory version 7.84.x.

To be able to use FrogML Storage with Artifactory, you should authenticate the frogml storage client against Artifactory.
JFrog implements a credentials provider chain. It sequentially checks each place where you can set the credentials to authenticate with FrogML, and then selects the first one you set.

### Upload ML model to Artifactory

You can upload a model to a FrogML repository using the upload_model_version() function. 
You can upload a single file or an entire folder.
This function uses checksum upload, assigning a SHA2 value to each model for retrieval from storage. If the binary content cannot be reused, the smart upload mechanism performs regular upload instead.
After uploading the model, FrogML generates a file named model-info.json which contains the model name and its related files and dependencies.

The version parameter is optional. If not specified, Artifactory will set the version as the timestamp of the time you uploaded the model in your time zone, in UTC format:  yyyy-MM-dd-HH-mm-ss.
Additionally, you can add properties to the model in Artifactory to categorize and label it.
The function upload_model_version returns an instance of FrogMlModelVersion, which includes the model's name, version, and namespace.

## Local Development Setup

To install FrogML locally with development dependencies, you must authenticate with **Repo21** (a private JFrog repository) to fetch the `QwakBentoML` dependency.
### 1. Generate Credentials
1. Log in to **Repo 21** via JFrog Okta.
2. Go to **User Profile** (top right) → **Set Me Up**.
3. Select **PyPI** and choose the repository `artifactory-pypi-virtual`.
4. Click **Generate Token & Create Instructions**. Your **username** and **token** will be displayed there.

### 2. Configure Poetry
Choose **one** of the following methods to authenticate:

#### Option A: Global Configuration
Run the following command to persist your credentials:
```bash
poetry config http-basic.jfrog <your_username> <your_token>
```

#### Option B: Environment Variables
Export the credentials as environment variables:
```bash
export POETRY_HTTP_BASIC_JFROG_USERNAME=<your_username>
export POETRY_HTTP_BASIC_JFROG_PASSWORD=<your_token>
```
