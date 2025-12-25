#!/bin/sh
set -e

cat > .hea-config.cfg <<EOF
[DEFAULT]
Registry=${HEASERVER_REGISTRY_URL:-http://heaserver-registry:8080}
MessageBrokerEnabled=${HEA_MESSAGE_BROKER_ENABLED:-true}
EncryptionKeyFile=/run/secrets/hea_encryption_key

[MessageBroker]
Hostname = ${RABBITMQ_HOSTNAME:-rabbitmq}
Port = ${RABBITMQ_AMQP_PORT:-5672}
Username = ${RABBITMQ_USERNAME:-guest}
Password = ${RABBITMQ_PASSWORD:-guest}
PublishQueuePersistencePath = ${HEA_MESSAGE_BROKER_QUEUE_PATH}
EOF

exec heaserver-buckets -f .hea-config.cfg -b ${HEASERVER_BUCKETS_URL:-http://localhost:8080}


