#!/bin/sh
set -e

cat > .hea-config.cfg <<EOF
[DEFAULT]
Registry=${HEASERVER_REGISTRY_URL:-http://heaserver-registry:8080}
MessageBrokerEnabled=${HEA_MESSAGE_BROKER_ENABLED:-true}
EncryptionKeyFile=/run/secrets/hea_encryption_key

[MessageBroker]
Hostname = ${RABBITMQ_HOSTNAME:-rabbitmq}
Port = 5672
Username = ${RABBITMQ_USERNAME:-guest}
Password = ${RABBITMQ_PASSWORD:-guest}

[MongoDB]
ConnectionString=mongodb://${MONGO_HEA_USERNAME}:${MONGO_HEA_PASSWORD}@${MONGO_HOSTNAME}:27017/${MONGO_HEA_DATABASE}?authSource=${MONGO_HEA_AUTH_SOURCE:-admin}&tls=${MONGO_USE_TLS:-false}

[Opensearch]
Hostname=${OPENSEARCH_HOSTNAME:-http://localhost}
Port=${OPENSEARCH_PORT:-9200}
UseSSL=${OPENSEARCH_USE_SSL:-false}
VerifyCerts=${OPENSEARCH_VERIFY_CERTS:-false}
Index=${OPENSEARCH_INDEX}
EOF

exec heaserver-accounts -f .hea-config.cfg -b ${HEASERVER_ACCOUNTS_URL}
