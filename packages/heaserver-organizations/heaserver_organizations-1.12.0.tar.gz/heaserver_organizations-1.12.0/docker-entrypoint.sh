#!/bin/sh
set -e

cat > .hea-config.cfg <<EOF
[DEFAULT]
Registry=${HEASERVER_REGISTRY_URL:-http://heaserver-registry:8080}
EncryptionKeyFile=/run/secrets/hea_encryption_key

[MongoDB]
ConnectionString=mongodb://${MONGO_HEA_USERNAME}:${MONGO_HEA_PASSWORD}@${MONGO_HOSTNAME}:27017/${MONGO_HEA_DATABASE}?authSource=${MONGO_HEA_AUTH_SOURCE:-admin}&tls=${MONGO_USE_TLS:-false}

[MessageBroker]
Hostname = ${RABBITMQ_HOSTNAME:-rabbitmq}
Port = ${RABBITMQ_AMQP_PORT:-5672}
Username = ${RABBITMQ_USERNAME:-guest}
Password = ${RABBITMQ_PASSWORD:-guest}
EOF

exec heaserver-organizations -f .hea-config.cfg -b ${HEASERVER_ORGANIZATIONS_URL:-http://localhost:8087}
