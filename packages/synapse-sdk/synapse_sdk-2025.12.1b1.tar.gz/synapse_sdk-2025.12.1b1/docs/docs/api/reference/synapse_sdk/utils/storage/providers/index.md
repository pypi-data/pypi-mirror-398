---
sidebar_label: providers
title: synapse_sdk.utils.storage.providers
---

Storage providers module.

This module exports all built-in storage providers. Import specific
providers directly for better control over dependencies.

Note: Providers are imported lazily via registry to avoid
loading optional dependencies (boto3, gcsfs, paramiko) at import time.
Direct imports are available for explicit usage.

