#!/bin/bash

# Deployment script for PyTorch TTS with Bark
# Supports development, staging, and production environments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
ENV="development"
GPU=false
BUILD=false
CLEAN=false

# Function to print colored messages
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check Docker and Docker Compose
check_requirements() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi

    # Check for nvidia-docker if GPU is requested
    if [ "$GPU" = true ]; then
        if ! docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi &> /dev/null; then
            print_warning "NVIDIA Docker runtime not available. Falling back to CPU."
            GPU=false
        else
            print_message "GPU support detected"
        fi
    fi
}

# Function to clean up resources
cleanup() {
    print_message "Cleaning up Docker resources..."
    docker-compose -f docker-compose.local-stack.yml down -v
    docker system prune -f
}

# Function to build images
build_images() {
    print_message "Building Docker images..."

    if [ "$GPU" = true ]; then
        print_message "Building GPU-optimized PyTorch TTS image..."
        docker build -f pytorch-tts-server/Dockerfile.gpu \
                     --build-arg TORCH_INDEX_URL=https://download.pytorch.org/whl/cu118 \
                     -t pytorch-tts:gpu \
                     pytorch-tts-server/
    else
        print_message "Building CPU-optimized PyTorch TTS image..."
        docker build -f pytorch-tts-server/Dockerfile \
                     --build-arg TORCH_INDEX_URL=https://download.pytorch.org/whl/cpu \
                     -t pytorch-tts:cpu \
                     pytorch-tts-server/
    fi

    print_message "Building Whisper ASR image..."
    docker build -f whisper-asr-server/Dockerfile \
                 -t whisper-asr:latest \
                 whisper-asr-server/

    print_message "Building main application image..."
    docker build -f Dockerfile -t subway-surfers:latest .
}

# Function to deploy development environment
deploy_development() {
    print_message "Deploying development environment with mock TTS..."

    # Use override file for development
    docker-compose -f docker-compose.local-stack.yml \
                   -f docker-compose.override.yml \
                   up -d

    print_message "Development stack deployed:"
    echo "  - Application: http://localhost:5001"
    echo "  - PyTorch TTS (mock): http://localhost:8001"
    echo "  - Whisper ASR: http://localhost:9000"
}

# Function to deploy staging environment
deploy_staging() {
    print_message "Deploying staging environment with small Bark models..."

    # Set environment for small models
    export SUNO_USE_SMALL_MODELS=true
    export SUNO_OFFLOAD_CPU=true

    docker-compose -f docker-compose.local-stack.yml up -d

    print_message "Staging stack deployed:"
    echo "  - Application: http://localhost:5001"
    echo "  - PyTorch TTS (small): http://localhost:8001"
    echo "  - AllTalk TTS: http://localhost:7851"
    echo "  - Whisper ASR: http://localhost:9000"
}

# Function to deploy production environment
deploy_production() {
    print_message "Deploying production environment..."

    if [ "$GPU" = true ]; then
        print_message "Using GPU-accelerated configuration..."
        docker-compose -f docker-compose.production.yml up -d pytorch-tts-gpu
    else
        print_message "Using CPU-only configuration..."
        docker-compose -f docker-compose.production.yml up -d pytorch-tts-cpu
    fi

    # Deploy remaining services
    docker-compose -f docker-compose.production.yml up -d

    print_message "Production stack deployed:"
    echo "  - Application: http://localhost:5001"
    echo "  - Load Balancer: http://localhost:80"
    echo "  - Grafana: http://localhost:3000"
    echo "  - Prometheus: http://localhost:9090"
}

# Function to check service health
check_health() {
    print_message "Checking service health..."

    # Wait for services to be ready
    sleep 10

    # Check PyTorch TTS
    if curl -f http://localhost:8001/health &> /dev/null; then
        echo -e "  ${GREEN}✓${NC} PyTorch TTS is healthy"
    else
        echo -e "  ${RED}✗${NC} PyTorch TTS is not responding"
    fi

    # Check Whisper ASR
    if curl -f http://localhost:9000/health &> /dev/null; then
        echo -e "  ${GREEN}✓${NC} Whisper ASR is healthy"
    else
        echo -e "  ${RED}✗${NC} Whisper ASR is not responding"
    fi

    # Check main application
    if curl -f http://localhost:5001 &> /dev/null; then
        echo -e "  ${GREEN}✓${NC} Main application is healthy"
    else
        echo -e "  ${RED}✗${NC} Main application is not responding"
    fi
}

# Function to show logs
show_logs() {
    print_message "Showing logs (Ctrl+C to exit)..."
    docker-compose -f docker-compose.local-stack.yml logs -f --tail=100
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--env)
            ENV="$2"
            shift 2
            ;;
        -g|--gpu)
            GPU=true
            shift
            ;;
        -b|--build)
            BUILD=true
            shift
            ;;
        -c|--clean)
            CLEAN=true
            shift
            ;;
        -l|--logs)
            show_logs
            exit 0
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -e, --env ENV     Environment (development|staging|production)"
            echo "  -g, --gpu         Enable GPU support"
            echo "  -b, --build       Build images before deployment"
            echo "  -c, --clean       Clean up resources before deployment"
            echo "  -l, --logs        Show service logs"
            echo "  -h, --help        Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 -e development              # Deploy development with mock"
            echo "  $0 -e staging -b                # Build and deploy staging"
            echo "  $0 -e production -g -b          # Build and deploy production with GPU"
            echo "  $0 -c -e development            # Clean and redeploy development"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Main execution
print_message "Starting PyTorch TTS deployment..."
print_message "Environment: $ENV"
print_message "GPU Support: $GPU"

# Check requirements
check_requirements

# Clean if requested
if [ "$CLEAN" = true ]; then
    cleanup
fi

# Build if requested
if [ "$BUILD" = true ]; then
    build_images
fi

# Deploy based on environment
case $ENV in
    development|dev)
        deploy_development
        ;;
    staging|stage)
        deploy_staging
        ;;
    production|prod)
        deploy_production
        ;;
    *)
        print_error "Invalid environment: $ENV"
        exit 1
        ;;
esac

# Check health
check_health

print_message "Deployment complete!"
print_message "Use '$0 -l' to view logs"