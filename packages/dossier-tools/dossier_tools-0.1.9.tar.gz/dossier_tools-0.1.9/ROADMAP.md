# Roadmap

Features planned for future releases:

## AWS KMS Signing

Sign workflows with AWS KMS keys instead of local Ed25519 keys.

```bash
pip install dossier-tools[kms]
dossier sign workflow.ds.md --kms-key-id arn:aws:kms:...
```

## Trusted Keys

Manage trusted public keys for signature verification.

```bash
dossier trust add alice.pub --name "Alice"
dossier trust list
dossier verify workflow.ds.md  # Shows VERIFIED for trusted signers
```

Keys stored in `~/.dossier/trusted-keys`.
