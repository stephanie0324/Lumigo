PRJ_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"/..
cd ${PRJ_DIR}

# export $(grep -v '^#' ../../deploy/.env | xargs)
source "${PRJ_DIR}/deploy/.env"

REQUESTS_CA_BUNDLE=${REQUESTS_CA_BUNDLE:-/etc/ssl/certs/ca-certificates.crt}
SSL_CERT_FILE=${REQUESTS_CA_BUNDLE:-/etc/ssl/certs/ca-certificates.crt}

IMAGE_NAME=$(bash script/get-image-name.sh)

docker run \
    --name ${COMPOSE_PROJECT_NAME}\
    -p ${HOST_PORT}:7860 \
    -v ${PRJ_DIR}/app:/app \
    --rm \
    -it \
    --entrypoint bash \
    -e REQUESTS_CA_BUNDLE=${REQUESTS_CA_BUNDLE} \
    -e SSL_CERT_FILE=${SSL_CERT_FILE} \
    -e OPENAI_API_KEY="${OPENAI_API_KEY}" \
    -e MONGODB_URI="${MONGODB_URI}" \
    -e MONGODB_NAME="${MONGODB_NAME}" \
    -e COLLECTION="${COLLECTION}" \
    -e INDEX_NAME="${INDEX_NAME}" \
    -e GPU_DEVICE="${GPU_DEVICE}" \
    -v /etc/ssl/certs:/etc/ssl/certs \
    --gpus all \
    $IMAGE_NAME

