#!/bin/sh
set -e

cat > .hea-config.cfg <<EOF
[DEFAULT]
Registry=${HEASERVER_REGISTRY_URL:-http://heaserver-registry:8080}
MessageBrokerEnabled=${HEA_MESSAGE_BROKER_ENABLED:-true}
EncryptionKeyFile=/run/secrets/hea_encryption_key

[MongoDB]
ConnectionString=mongodb://${MONGO_HEA_USERNAME}:${MONGO_HEA_PASSWORD}@${MONGO_HOSTNAME}:27017/${MONGO_HEA_DATABASE}?authSource=${MONGO_HEA_AUTH_SOURCE:-admin}&tls=${MONGO_USE_TLS:-false}

[MessageBroker]
Hostname = ${RABBITMQ_HOSTNAME:-rabbitmq}
Port = ${RABBITMQ_AMQP_PORT:-5672}
Username = ${RABBITMQ_USERNAME:-guest}
Password = ${RABBITMQ_PASSWORD:-guest}
PublishQueuePersistencePath = ${HEA_MESSAGE_BROKER_QUEUE_PATH}

[Opensearch]
Hostname=${OPENSEARCH_HOSTNAME:-http://localhost}
Port=${OPENSEARCH_PORT:-9200}
UseSSL=${OPENSEARCH_USE_SSL:-false}
VerifyCerts=${OPENSEARCH_VERIFY_CERTS:-false}
Index=${OPENSEARCH_INDEX}
EOF

exec heaserver-folders-aws-s3 -f .hea-config.cfg -b ${HEASERVER_FOLDERS_AWS_S3_URL:-http://localhost:8080}


