# MongoDB X.509 Certificate Authentication Guide

This guide explains how to set up and use X.509 certificate authentication for MongoDB access in the IATP registry.

## Overview

X.509 certificate authentication provides a secure way to authenticate to MongoDB without using passwords or API keys. It uses SSL/TLS certificates for both encryption and authentication.

## Prerequisites

1. **MongoDB Atlas Cluster** with X.509 authentication enabled
2. **Certificate file** (.pem) containing both the certificate and private key
3. **Certificate user** created in MongoDB's `$external` database

## Setup Steps

### 1. Obtain Your X.509 Certificate

If you've already created a certificate-based user via MongoDB Atlas UI:

```bash
# Your certificate file should contain both the certificate and private key
# It typically looks like this:
#
# -----BEGIN CERTIFICATE-----
# [certificate content]
# -----END CERTIFICATE-----
# -----BEGIN PRIVATE KEY-----
# [private key content]
# -----END PRIVATE KEY-----
```

### 2. Configure Environment Variable

Set the path to your certificate file:

```bash
export MONGODB_X509_CERT_FILE="/path/to/your/certificate.pem"
```

For permanent configuration, add to your `.env` file:

```env
MONGODB_X509_CERT_FILE=/path/to/your/certificate.pem
```

### 3. Verify Certificate Setup

Extract the certificate subject (this should match your MongoDB user):

```bash
openssl x509 -in /path/to/your/certificate.pem -noout -subject
```

Example output:
```
subject=CN=myapp,OU=myteam,O=mycompany,L=city,ST=state,C=US
```

### 4. Test the Connection

Run the test script to verify authentication:

```bash
cd traia-centralized-backend
uv run python tests/test_mongodb_registry/test_mongodb_x509_auth.py
```

## Authentication Priority

The registries support multiple authentication methods with the following priority:

1. **X.509 Certificate** (if `MONGODB_X509_CERT_FILE` is set)
2. **Username/Password** (if `MONGODB_USER` and `MONGODB_PASSWORD` are set)
3. **Connection String** (if `MONGODB_CONNECTION_STRING` is set)

## Security Best Practices

### Certificate File Protection

1. **Restrict file permissions**:
   ```bash
   chmod 600 /path/to/your/certificate.pem
   ```

2. **Store securely**:
   - Never commit certificate files to version control
   - Use secure secret management systems for production
   - Consider using environment-specific certificates

### Certificate Management

1. **Rotation**: Plan for certificate rotation before expiration
2. **Monitoring**: Set up alerts for certificate expiration
3. **Backup**: Keep secure backups of certificates

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Verify the certificate user exists in MongoDB's `$external` database
   - Check certificate hasn't expired: `openssl x509 -in cert.pem -noout -dates`
   - Ensure certificate was issued by the correct CA

2. **Connection Refused**
   - Verify MongoDB cluster allows connections from your IP
   - Check that TLS is enabled on the cluster

3. **Invalid Certificate Format**
   - Ensure the .pem file contains both certificate and private key
   - Verify no extra whitespace or formatting issues

### Debug Commands

```bash
# Check certificate validity
openssl x509 -in cert.pem -noout -text

# Verify private key matches certificate
openssl x509 -noout -modulus -in cert.pem | openssl md5
openssl rsa -noout -modulus -in cert.pem | openssl md5

# Test SSL connection to MongoDB
openssl s_client -connect your-cluster.mongodb.net:27017 -CAfile cert.pem
```

## Integration with IATP Services

### Using with Registry API

The registry automatically detects and uses X.509 authentication when configured:

```python
from traia_iatp.registry.mongodb_registry import UtilityAgentRegistry

# No need to pass credentials - uses MONGODB_X509_CERT_FILE automatically
registry = UtilityAgentRegistry()
```

### Docker Deployment

When deploying in Docker, mount the certificate file:

```yaml
# docker-compose.yml
services:
  api:
    environment:
      - MONGODB_X509_CERT_FILE=/certs/mongodb.pem
    volumes:
      - ./certs/mongodb.pem:/certs/mongodb.pem:ro
```

### Kubernetes Deployment

Use Kubernetes secrets for certificate management:

```yaml
# Create secret
kubectl create secret generic mongodb-cert --from-file=mongodb.pem=/path/to/cert.pem

# Mount in deployment
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      containers:
      - name: app
        env:
        - name: MONGODB_X509_CERT_FILE
          value: /certs/mongodb.pem
        volumeMounts:
        - name: mongodb-cert
          mountPath: /certs
          readOnly: true
      volumes:
      - name: mongodb-cert
        secret:
          secretName: mongodb-cert
```

## Migration from Username/Password

To migrate from username/password to X.509 certificate authentication:

1. Create certificate-based user in MongoDB Atlas
2. Update environment configuration:
   ```bash
   # Remove or comment out
   # MONGODB_USER=...
   # MONGODB_PASSWORD=...
   
   # Add
   MONGODB_X509_CERT_FILE=/path/to/cert.pem
   ```
3. Test with `test_mongodb_x509_auth.py`:
   ```bash
   uv run python tests/test_mongodb_registry/test_mongodb_x509_auth.py
   ```

## Support

For issues with X.509 authentication:
1. Check MongoDB Atlas documentation
2. Verify certificate configuration with `test_mongodb_x509_auth.py`
3. Review MongoDB connection logs in Atlas UI 