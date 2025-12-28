---
schema_version: "1.0.0"
name: "full-featured-dossier"
title: "Full Featured Dossier"
version: "1.2.3"
status: "stable"
objective: "A dossier with all optional fields populated for comprehensive testing"
checksum:
  algorithm: "sha256"
  hash: "e77d563c6ddfe89c6e8c60ca9990dafacf6b9d11e1d3104b8fd5625d6f3a8d31"
risk_level: "medium"
requires_approval: true
risk_factors:
  - "modifies_files"
  - "network_access"
destructive_operations:
  - "Overwrites configuration files in /etc"
category:
  - "devops"
  - "deployment"
tags:
  - "docker"
  - "kubernetes"
estimated_duration:
  min_minutes: 5
  max_minutes: 15
authors:
  - name: "Test Author"
    email: "test@example.com"
license: "MIT"
---

# Full Featured Dossier

This dossier has all the bells and whistles.

## Steps

1. Do something
2. Do something else
