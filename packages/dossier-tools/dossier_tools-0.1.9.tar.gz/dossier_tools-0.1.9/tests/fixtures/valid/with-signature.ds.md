---
schema_version: "1.0.0"
name: "signed-dossier"
title: "Signed Dossier"
version: "1.0.0"
status: "stable"
objective: "A dossier with an Ed25519 signature for testing signature validation"
checksum:
  algorithm: "sha256"
  hash: "055310a723d3158528be356949541e30779c36606e82834b9ac532c8c5e2992d"
authors:
  - name: "Test Signer"
    email: "test@example.com"
signature:
  algorithm: "ed25519"
  public_key: "MCowBQYDK2VwAyEAExample="
  signature: "ExampleSignatureBase64=="
  key_id: "test-key-2024"
  signed_by: "Test Signer <test@example.com>"
  timestamp: "2024-01-15T12:00:00Z"
---

# Signed Dossier

This dossier has a signature.
