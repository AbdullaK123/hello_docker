get_user_input(){
    local prompt="$1"
    local input 
    read -p "$prompt" input
    echo "$input"
}

build_image() {
    local tag="$1"  
    echo "Building image..."
    docker build -t $tag . 
}

run_container() {
    local port="$1"  
    local tag="$2"   
    local app_name="$3"
    local app_version="$4"
    local env="$5"
    echo "Running container..."
    docker run -d -p $port:$port \
        -e APP_NAME=$app_name \
        -e APP_VERSION=$app_version \
        -e ENV=$env \
        $tag 
}

start_app() {
    local tag="$1"   
    local port="$2"
    local app_name="$3"
    local app_version="$4"
    local env="$5"
    build_image $tag
    run_container $port $tag $app_name $app_version $env
}

main() {
    local tag="hello_app"
    local port=5000
    local app_name=$(get_user_input "Enter app name: ")
    local app_version=$(get_user_input "Enter app version: ")
    local env=$(get_user_input "Enter environment name: ")
    start_app $tag $port $app_name $app_version $env
}

main