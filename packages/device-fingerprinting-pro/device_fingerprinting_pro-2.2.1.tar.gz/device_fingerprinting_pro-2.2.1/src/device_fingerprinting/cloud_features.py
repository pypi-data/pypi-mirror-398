"""
Cloud and distributed features for device fingerprinting.

Enables secure cloud storage, multi-device management, and distributed verification.
This module provides a more robust and production-ready implementation for interacting
with cloud storage providers like AWS S3 and Azure Blob Storage. It also includes
enhancements for distributed verification and multi-device management.
"""

import os
import json
import time
import base64
import hashlib
import logging
from typing import Dict, Any, List, Optional

from .backends import StorageBackend
from .crypto import AESGCMEncryptor, ScryptKDF

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class CloudStorageBackend(StorageBackend):
    """
    Secure cloud storage backend with enhanced encryption and provider support.

    Supports AWS S3 and Azure Blob Storage with robust client-side encryption.
    """

    def __init__(
        self,
        provider: str = "aws",
        encryption_key: Optional[bytes] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.provider = provider.lower()
        self.config = config or {}
        self.client: Any = None
        self.bucket_name: Optional[str] = self.config.get("bucket_name")
        self.container_name: Optional[str] = self.config.get("container_name")
        self.available: bool = False

        if not encryption_key:
            raise ValueError("An encryption key is required for CloudStorageBackend.")

        # Use Scrypt for key derivation to add resistance against brute-force attacks
        salt = self.config.get("kdf_salt", os.urandom(16))
        self.kdf = ScryptKDF(salt=salt)
        self.derived_key = self.kdf.derive_key(encryption_key)
        self.encryptor = AESGCMEncryptor(self.derived_key)

        self._init_cloud_client()

    def _init_cloud_client(self) -> None:
        """Initialize cloud storage client based on the provider."""
        try:
            if self.provider == "aws":
                import boto3

                if not self.bucket_name:
                    self.bucket_name = "device-fingerprints-secure-bucket"
                self.client = boto3.client(
                    "s3",
                    aws_access_key_id=self.config.get("aws_access_key_id"),
                    aws_secret_access_key=self.config.get("aws_secret_access_key"),
                    region_name=self.config.get("aws_region", "us-east-1"),
                )
                self.available = True
                logging.info("AWS S3 client initialized successfully.")
            elif self.provider == "azure":
                from azure.storage.blob import BlobServiceClient

                if not self.container_name:
                    self.container_name = "device-fingerprints-secure-container"
                connection_string = self.config.get("azure_connection_string")
                if not connection_string:
                    raise ValueError("Azure connection string is required.")
                self.client = BlobServiceClient.from_connection_string(connection_string)
                self.available = True
                logging.info("Azure Blob Storage client initialized successfully.")
            else:
                logging.warning(f"Unsupported cloud provider: {self.provider}")
                self.available = False
        except ImportError as e:
            logging.error(f"Failed to import cloud SDK for {self.provider}: {e}")
            self.available = False
        except Exception as e:
            logging.error(f"Failed to initialize cloud client for {self.provider}: {e}")
            self.available = False

    def _encrypt_data(self, data: Dict[str, Any]) -> bytes:
        """Encrypt data before storing it in the cloud."""
        json_data = json.dumps(data, sort_keys=True).encode("utf-8")
        return self.encryptor.encrypt(json_data)

    def _decrypt_data(self, encrypted_data: bytes) -> Dict[str, Any]:
        """Decrypt data retrieved from the cloud."""
        decrypted_data = self.encryptor.decrypt(encrypted_data)
        return json.loads(decrypted_data)

    def store(self, key: str, data: Dict[str, Any]) -> bool:
        """Store encrypted data in the configured cloud storage."""
        if not self.available:
            logging.error("Cloud storage is not available.")
            return False

        try:
            encrypted_data = self._encrypt_data(data)
            object_key = f"fingerprints/{key}.enc"

            if self.provider == "aws":
                self.client.put_object(
                    Bucket=self.bucket_name,
                    Key=object_key,
                    Body=encrypted_data,
                    ServerSideEncryption="AES256",
                )
            elif self.provider == "azure":
                blob_client = self.client.get_blob_client(
                    container=self.container_name, blob=object_key
                )
                blob_client.upload_blob(encrypted_data, overwrite=True)

            logging.info(f"Successfully stored data for key: {key}")
            return True
        except Exception as e:
            logging.error(f"Failed to store data for key {key}: {e}")
            return False

    def load(self, key: str) -> Optional[Dict[str, Any]]:
        """Load and decrypt data from the configured cloud storage."""
        if not self.available:
            logging.error("Cloud storage is not available.")
            return None

        try:
            object_key = f"fingerprints/{key}.enc"
            encrypted_data = None

            if self.provider == "aws":
                response = self.client.get_object(Bucket=self.bucket_name, Key=object_key)
                encrypted_data = response["Body"].read()
            elif self.provider == "azure":
                blob_client = self.client.get_blob_client(
                    container=self.container_name, blob=object_key
                )
                encrypted_data = blob_client.download_blob().readall()

            if encrypted_data:
                decrypted_data = self._decrypt_data(encrypted_data)
                logging.info(f"Successfully loaded data for key: {key}")
                return decrypted_data
            return None
        except Exception as e:
            logging.error(f"Failed to load data for key {key}: {e}")
            return None


class DistributedVerification:
    """
    Distributed verification system for device fingerprints.

    Enables multi-node verification and consensus for high-security scenarios.
    """

    def __init__(
        self, nodes: List[str], consensus_threshold: float = 0.67, timeout: int = 10
    ) -> None:
        """
        Initialize distributed verification.

        Args:
            nodes: List of verification node URLs.
            consensus_threshold: Minimum agreement ratio (0.0-1.0).
            timeout: Request timeout in seconds.
        """
        if not (0 < consensus_threshold <= 1.0):
            raise ValueError("Consensus threshold must be between 0 and 1.")
        self.nodes = nodes
        self.consensus_threshold = consensus_threshold
        self.timeout = timeout

    def verify_distributed(self, fingerprint: str, binding_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify a fingerprint across multiple nodes and reach consensus.

        Returns:
            A dictionary with verification results and consensus information.
        """
        import concurrent.futures

        node_results: List[Dict[str, Any]] = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.nodes)) as executor:
            future_to_node = {
                executor.submit(self._verify_with_node, node, fingerprint, binding_data): node
                for node in self.nodes
            }
            for future in concurrent.futures.as_completed(future_to_node):
                node_url = future_to_node[future]
                try:
                    result = future.get()
                    node_results.append(
                        {"node": node_url, "result": result, "timestamp": time.time()}
                    )
                except Exception as e:
                    logging.warning(f"Node {node_url} failed verification: {e}")
                    node_results.append(
                        {"node": node_url, "error": str(e), "timestamp": time.time()}
                    )

        valid_results = [r for r in node_results if "result" in r and r["result"]]
        if not valid_results:
            return {"consensus": False, "error": "No valid responses from nodes."}

        positive_votes = sum(1 for r in valid_results if r["result"].get("valid", False))
        consensus_ratio = positive_votes / len(valid_results)

        has_consensus = consensus_ratio >= self.consensus_threshold

        return {
            "consensus": has_consensus,
            "consensus_ratio": consensus_ratio,
            "positive_votes": positive_votes,
            "total_votes": len(valid_results),
            "node_results": node_results,
            "verification_timestamp": time.time(),
        }

    def _verify_with_node(
        self, node_url: str, fingerprint: str, binding_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send a verification request to a single node."""
        import requests

        payload = {
            "fingerprint": fingerprint,
            "binding_data": binding_data,
            "timestamp": time.time(),
        }

        response = requests.post(
            f"{node_url.rstrip('/')}/verify",
            json=payload,
            timeout=self.timeout,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            verify=True,  # Explicitly enable TLS certificate verification
        )

        response.raise_for_status()
        return response.json()


class MultiDeviceManager:
    """
    Manager for multiple device fingerprints and cross-device verification.

    Useful for users with multiple devices or for handling device upgrades.
    """

    def __init__(self, storage_backend: StorageBackend) -> None:
        self.storage = storage_backend

    def register_device(
        self, user_id: str, device_id: str, fingerprint_data: Dict[str, Any]
    ) -> bool:
        """Register a new device for a user."""
        user_record = self.storage.load(f"user_{user_id}") or {"devices": {}}

        user_record["devices"][device_id] = {
            "fingerprint_data": fingerprint_data,
            "registration_time": time.time(),
            "last_seen": time.time(),
            "status": "active",
        }

        return self.storage.store(f"user_{user_id}", user_record)

    def get_user_devices(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all devices registered to a user."""
        user_record = self.storage.load(f"user_{user_id}")
        if not user_record or "devices" not in user_record:
            return []

        devices = []
        for device_id, device_info in user_record["devices"].items():
            device_info["device_id"] = device_id
            devices.append(device_info)
        return devices

    def verify_cross_device(
        self, user_id: str, current_fingerprint_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Verify the current device against a user's known devices.

        Returns similarity scores and a recommendation.
        """
        user_devices = self.get_user_devices(user_id)

        if not user_devices:
            return {"status": "no_known_devices", "recommendation": "require_full_verification"}

        similarities = []
        for device in user_devices:
            similarity = self._calculate_device_similarity(
                current_fingerprint_data, device["fingerprint_data"]
            )
            similarities.append(
                {
                    "device_id": device["device_id"],
                    "similarity": similarity,
                    "last_seen": device.get("last_seen"),
                }
            )

        best_match = max(similarities, key=lambda x: x["similarity"])

        if best_match["similarity"] > 0.9:
            status = "known_device"
        elif best_match["similarity"] > 0.6:
            status = "similar_device"
        else:
            status = "new_device"

        return {
            "status": status,
            "best_match": best_match,
            "all_similarities": similarities,
            "recommendation": self._get_verification_recommendation(status),
        }

    def _calculate_device_similarity(
        self, fp1_data: Dict[str, Any], fp2_data: Dict[str, Any]
    ) -> float:
        """Calculate a similarity score between two device fingerprints."""
        if not fp1_data or not fp2_data:
            return 0.0

        # Define weights for different attributes
        weights = {
            "platform_details": 0.3,
            "cpu_details": 0.25,
            "memory_details": 0.15,
            "display_details": 0.1,
            "hardware_identifiers": 0.2,
        }

        total_score = 0.0

        # Compare platform details
        if fp1_data.get("platform_details") == fp2_data.get("platform_details"):
            total_score += weights["platform_details"]

        # Compare CPU details
        cpu1 = fp1_data.get("cpu_details", {})
        cpu2 = fp2_data.get("cpu_details", {})
        if cpu1.get("model") == cpu2.get("model") and cpu1.get("architecture") == cpu2.get(
            "architecture"
        ):
            total_score += weights["cpu_details"]

        # Compare memory
        mem1 = fp1_data.get("memory_details", {}).get("total_gb", 0)
        mem2 = fp2_data.get("memory_details", {}).get("total_gb", 0)
        if abs(mem1 - mem2) <= 2:  # Allow for minor variations
            total_score += weights["memory_details"]

        # Compare display details
        disp1 = fp1_data.get("display_details", [{}])[0].get("resolution")
        disp2 = fp2_data.get("display_details", [{}])[0].get("resolution")
        if disp1 == disp2:
            total_score += weights["display_details"]

        # Compare hardware identifiers (if available)
        id1 = set(fp1_data.get("hardware_identifiers", {}).values())
        id2 = set(fp2_data.get("hardware_identifiers", {}).values())
        if id1 and id1 == id2:
            total_score += weights["hardware_identifiers"]

        return round(total_score, 4)

    def _get_verification_recommendation(self, status: str) -> str:
        """Generate a verification recommendation based on the device similarity status."""
        if status == "known_device":
            return "allow_immediate"
        elif status == "similar_device":
            return "request_secondary_authentication"
        else:
            return "require_full_verification"
