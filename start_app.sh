#!/bin/bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
DEFAULT_TAG="hello_app"
DEFAULT_PORT=5000
DEFAULT_APP_NAME="Docker Learning App"
DEFAULT_APP_VERSION="1.0"
DEFAULT_ENV="development"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

get_user_input(){
    local prompt="$1"
    local default="$2"
    local input 
    read -p "$prompt [$default]: " input
    echo "${input:-$default}"
}

build_image() {
    local tag="$1"  
    log_info "Building image: $1"
    docker build -t $tag . 
    log_success "Image built successfully!"
}

run_container() {
    local port="$1"  
    local tag="$2"   
    local app_name="$3"
    local app_version="$4"
    local env="$5"
    log_info "Container running on port $port..."
    container_id=$(
        docker run -d -p $port:5000 \
        -e APP_NAME="$app_name" \
        -e APP_VERSION="$app_version" \
        -e ENV="$env" \
        $tag
    )
    log_success "Container started! Access it on http://localhost:$port..."
}

start_app() {
    local tag="$1"   
    local port="$2"
    local app_name="$3"
    local app_version="$4"
    local env="$5"
    build_image $tag
    run_container $port $tag $app_name $app_version $env
    log_success "App is now running!"
}

main() {
    local tag=$(get_user_input "Enter container name" "hello-app")
    local port=$(get_user_input "Enter port number" "5000")
    local app_name=$(get_user_input "Enter app name" "my-app")
    local app_version=$(get_user_input "Enter app version" "1.0")
    local env=$(get_user_input "Enter environment name" "development")
    start_app $tag $port $app_name $app_version $env
}

main