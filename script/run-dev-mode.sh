PRJ_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"/..
cd ${PRJ_DIR}

# export $(grep -v '^#' ../../deploy/.env | xargs)
# Load environment variables safely
ENV_FILE="${PRJ_DIR}/dev/.env"
if [[ -f "$ENV_FILE" ]]; then
    # Only source if the file is safe (no '<' or '>' or invalid lines)
    if grep -q '<\|>' "$ENV_FILE"; then
        echo "ERROR: Your .env file contains invalid characters like '<' or '>'"
        exit 1
    fi
    source "$ENV_FILE"
else
    echo "ERROR: .env file not found at $ENV_FILE"
    exit 1
fi

IMAGE_NAME=$(bash script/get-image-name.sh)

docker run \
    --name ${COMPOSE_PROJECT_NAME}\
    -p ${HOST_PORT}:7860 \
    -v ${PRJ_DIR}/app:/app \
    --rm \
    -it \
    --entrypoint bash \
    -e OPENAI_API_KEY="${OPENAI_API_KEY}" \
    -e MONGODB_URI="${MONGODB_URI}" \
    -e MONGODB_NAME="${MONGODB_NAME}" \
    -e COLLECTION="${COLLECTION}" \
    -e INDEX_NAME="${INDEX_NAME}" \
    -e DEVICE="${DEVICE}" \
    -e PROJECT_ID="${PROJECT_ID}" \
    -e LOCATION="${LOCATION}" \
    -e GOOGLE_APPLICATION_CREDENTIALS="${GOOGLE_APPLICATION_CREDENTIALS}" \
    $IMAGE_NAME

