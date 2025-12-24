# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Module for interfacing with the qBraid Quantum Jobs proxy for Amazon Braket.

"""

import logging
import os
import subprocess
from importlib.metadata import PackageNotFoundError, distribution
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


def _check_proxy_braket() -> tuple[bool, bool]:
    """
    Determine the braket proxy state by checking that amazon-braket-sdk,
    boto3, and botocore are installed and that botocore is the qBraid fork.

    Returns:
        tuple[bool, bool]: A tuple of two booleans indicating whether qBraid
                           Quantum Jobs are supported and enabled, respectively.

    """
    packages = ["amazon-braket-sdk", "boto3", "botocore"]

    supported = True
    enabled = False

    botocore_data: dict[str, Any] = {}
    for package in packages:
        try:
            dist = distribution(package)
            if package == "botocore":
                botocore_data = dist.metadata.json
        except PackageNotFoundError:
            return False, False

    homepage = botocore_data.get("Home-page", "")
    if "github.com/qBraid/botocore" in homepage:
        enabled = True

    return supported, enabled


def aws_configure(
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
    region: Optional[str] = None,
) -> None:
    """
    Initializes AWS configuration and credentials files with placeholder values.

    This function ensures the existence of AWS config and credentials files in the user's home
    directory. If these files do not already exist, it creates them and populates them with
    placeholder values for the AWS access key and secret access key. While AWS credentials are not
    required when submitting quantum tasks through qBraid, Amazon Braket requires these files to be
    present to prevent configuration errors.
    """
    aws_dir = Path.home() / ".aws"
    config_path = aws_dir / "config"
    credentials_path = aws_dir / "credentials"
    aws_access_key_id = aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID", "MYACCESSKEY")
    aws_secret_access_key = aws_secret_access_key or os.getenv(
        "AWS_SECRET_ACCESS_KEY", "MYSECRETKEY"
    )
    region = region or os.getenv("AWS_REGION", "us-east-1")

    aws_dir.mkdir(exist_ok=True)
    if not config_path.exists():
        config_content = f"[default]\nregion = {region}\noutput = json\n"
        config_path.write_text(config_content)
    if not credentials_path.exists():
        credentials_content = (
            f"[default]\n"
            f"aws_access_key_id = {aws_access_key_id}\n"
            f"aws_secret_access_key = {aws_secret_access_key}\n"
        )
        credentials_path.write_text(credentials_content)


def enable_braket(python_exe: str) -> None:
    """Enables quantum jobs by installing qBraid/botocore package."""
    try:
        aws_configure()
        subprocess.check_call([python_exe, "-m", "pip", "install", "--upgrade", "boto3"])
        subprocess.check_call([python_exe, "-m", "pip", "uninstall", "botocore", "-y", "--quiet"])
        subprocess.check_call(
            [python_exe, "-m", "pip", "install", "git+https://github.com/qBraid/botocore.git"]
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as err:
        logger.error("Error enabling quantum jobs: %s", err)


def disable_braket(python_exe: str) -> None:
    """Disables quantum jobs by installing boto/botocore package."""
    try:
        subprocess.check_call(
            [python_exe, "-m", "pip", "install", "botocore", "--force-reinstall"],
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as err:
        logger.error("Error disabling quantum jobs: %s", err)


def add_braket(python_exe: str) -> None:
    """Adds quantum jobs functionality by installing Amazon Braket SDK."""
    try:
        subprocess.check_call([python_exe, "-m", "pip", "install", "amazon-braket-sdk"])
        enable_braket(python_exe)
    except (subprocess.CalledProcessError, FileNotFoundError) as err:
        logger.error("Error adding quantum jobs: %s", err)
