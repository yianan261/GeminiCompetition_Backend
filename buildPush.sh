build_and_push() {
    local dockerfile=$1
    local tag=$2

    docker buildx build --platform linux/amd64 . -f $dockerfile -t $tag &
    docker_pid=$!

    wait $docker_pid

    docker push $tag
}

build_and_push "api_service/Dockerfile" "us-west2-docker.pkg.dev/gemini-trip/gemini-trip/api_service"