#!/bin/sh
set -e

cat > .hea-config.cfg <<EOF
[DEFAULT]
Registry=${HEASERVER_REGISTRY_URL:-http://heaserver-registry:8080}
EncryptionKeyFile=/run/secrets/hea_encryption_key

[MongoDB]
ConnectionString=mongodb://${MONGO_HEA_USERNAME}:${MONGO_HEA_PASSWORD}@${MONGO_HOSTNAME}:27017/${MONGO_HEA_DATABASE}?authSource=${MONGO_HEA_AUTH_SOURCE:-admin}&tls=${MONGO_USE_TLS:-false}

[Keycloak]
Realm=${KEYCLOAK_REALM:-hea}
VerifySSL=${KEYCLOAK_VERIFY_SSL:-true}
Host=${KEYCLOAK_HOST:-https://localhost:8444}
AltHost=${KEYCLOAK_ALT_HOST}
Secret=${KEYCLOAK_ADMIN_SECRET}
SecretFile=${KEYCLOAK_ADMIN_SECRET_FILE}
Compatibility=${KEYCLOAK_COMPATIBILITY:-15}
ClientId=${KEYCLOAK_CLIENT_ID:-hea}
AdminClientId=${KEYCLOAK_ADMIN_CLIENT_ID:-admin-cli}
EOF
exec heaserver-people -f .hea-config.cfg -b ${HEASERVER_PEOPLE_URL:-http://localhost:8080}
