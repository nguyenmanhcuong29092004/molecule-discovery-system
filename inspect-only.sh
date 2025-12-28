#!/bin/bash

# ============================================================================
# Script: Chỉ Kiểm Tra (Không Xóa Gì Cả)
# ============================================================================

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

clear
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Docker Frontend Health Check & Inspection               ║${NC}"
echo -e "${BLUE}║   (Read-Only - No Changes Will Be Made)                   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# ============================================================================
print_section() {
    echo ""
    echo -e "${CYAN}╭─────────────────────────────────────────────────────────╮${NC}"
    echo -e "${CYAN}│ $1${NC}"
    echo -e "${CYAN}╰─────────────────────────────────────────────────────────╯${NC}"
    echo ""
}

print_ok() {
    echo -e "  ${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "  ${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "  ${RED}✗ $1${NC}"
}

print_info() {
    echo -e "  ${BLUE}ℹ $1${NC}"
}

# ============================================================================
print_section "1. DOCKER ENVIRONMENT"

echo -e "${MAGENTA}Docker Version:${NC}"
docker --version
docker-compose --version

echo ""
echo -e "${MAGENTA}Docker Daemon Status:${NC}"
if docker ps > /dev/null 2>&1; then
    print_ok "Docker daemon is running"
else
    print_error "Docker daemon is NOT running"
    exit 1
fi

# ============================================================================
print_section "2. CONTAINERS STATUS"

echo -e "${MAGENTA}All MolDB Containers:${NC}"
if docker ps -a | grep -q moldb; then
    docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.Size}}" | grep -E "NAMES|moldb"
else
    print_warning "No moldb containers found"
fi

echo ""
echo -e "${MAGENTA}Frontend Container Details:${NC}"
if docker ps -a | grep -q moldb-frontend; then
    docker ps -a --filter "name=moldb-frontend" --format "table {{.Names}}\t{{.ID}}\t{{.Status}}\t{{.Image}}\t{{.CreatedAt}}"
    
    echo ""
    container_id=$(docker ps -aq --filter "name=moldb-frontend" | head -1)
    if [ -n "$container_id" ]; then
        echo -e "${MAGENTA}Container Inspect:${NC}"
        echo "  ID: $container_id"
        echo "  State: $(docker inspect $container_id --format '{{.State.Status}}')"
        echo "  Started: $(docker inspect $container_id --format '{{.State.StartedAt}}')"
        echo "  Health: $(docker inspect $container_id --format '{{.State.Health.Status}}' 2>/dev/null || echo 'N/A')"
        echo "  Exit Code: $(docker inspect $container_id --format '{{.State.ExitCode}}')"
        echo "  Error: $(docker inspect $container_id --format '{{.State.Error}}' 2>/dev/null || echo 'None')"
    fi
else
    print_warning "Frontend container not found"
fi

# ============================================================================
print_section "3. IMAGES STATUS"

echo -e "${MAGENTA}Frontend Images:${NC}"
if docker images | grep -q "frontend"; then
    docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.Size}}\t{{.CreatedAt}}" | grep -E "REPOSITORY|frontend"
else
    print_warning "No frontend images found"
fi

echo ""
echo -e "${MAGENTA}All MolDB Images:${NC}"
docker images | grep -E "IMAGE|moldb|molecule-discovery-system" || print_warning "No moldb images"

# ============================================================================
print_section "4. VOLUMES STATUS"

echo -e "${MAGENTA}Frontend Volumes:${NC}"
if docker volume ls | grep -q "frontend"; then
    docker volume ls | grep -E "DRIVER|frontend"
    
    echo ""
    for vol in $(docker volume ls -q | grep "frontend"); do
        echo -e "${MAGENTA}Volume: $vol${NC}"
        mountpoint=$(docker volume inspect $vol --format "{{.Mountpoint}}")
        echo "  Mountpoint: $mountpoint"
        
        if [ -d "$mountpoint" ] && [ -r "$mountpoint" ]; then
            size=$(sudo du -sh "$mountpoint" 2>/dev/null | cut -f1 || echo "N/A")
            files=$(sudo find "$mountpoint" -type f 2>/dev/null | wc -l || echo "N/A")
            echo "  Size: $size"
            echo "  Files: $files"
        else
            echo "  Size: (need sudo)"
        fi
        echo ""
    done
else
    print_warning "No frontend volumes found"
fi

echo -e "${MAGENTA}All MolDB Volumes:${NC}"
docker volume ls | grep -E "DRIVER|molecule-discovery-system\|moldb" || print_warning "No moldb volumes"

# ============================================================================
print_section "5. NETWORKS STATUS"

echo -e "${MAGENTA}MolDB Networks:${NC}"
docker network ls | grep -E "NETWORK|molecule-discovery-system"

if docker network ls | grep -q molecule-discovery-system; then
    echo ""
    echo -e "${MAGENTA}Network Details:${NC}"
    network_name=$(docker network ls --filter "name=molecule-discovery-system" --format "{{.Name}}" | head -1)
    echo "  Network: $network_name"
    echo "  Connected containers:"
    docker network inspect $network_name --format '{{range .Containers}}    - {{.Name}} ({{.IPv4Address}}){{println}}{{end}}' 2>/dev/null
fi

# ============================================================================
print_section "6. PORT STATUS"

echo -e "${MAGENTA}Port Usage Check:${NC}"

# Check port 3000
echo "  Port 3000 (Frontend):"
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    print_error "IN USE"
    lsof -i :3000 -sTCP:LISTEN | grep -v "COMMAND" | while read line; do
        echo "    $line"
    done
else
    print_ok "FREE"
fi

# Check other ports
for port_num in 5432 6379 8000; do
    port_name=""
    case $port_num in
        5432) port_name="PostgreSQL" ;;
        6379) port_name="Redis" ;;
        8000) port_name="Backend" ;;
    esac
    
    echo "  Port $port_num ($port_name):"
    if lsof -Pi :$port_num -sTCP:LISTEN -t >/dev/null 2>&1; then
        process=$(lsof -i :$port_num -sTCP:LISTEN | grep -v "COMMAND" | head -1 | awk '{print $1}')
        print_info "Used by $process"
    else
        print_warning "Not in use"
    fi
done

# ============================================================================
print_section "7. LOGS ANALYSIS"

if docker ps | grep -q moldb-frontend; then
    echo -e "${MAGENTA}Frontend Container Logs (last 30 lines):${NC}"
    echo "╭─────────────────────────────────────────────────────────╮"
    docker logs --tail=30 moldb-frontend 2>&1 | sed 's/^/  │ /'
    echo "╰─────────────────────────────────────────────────────────╯"
    
    echo ""
    echo -e "${MAGENTA}Log Analysis:${NC}"
    error_count=$(docker logs moldb-frontend 2>&1 | grep -i "error" | wc -l)
    warning_count=$(docker logs moldb-frontend 2>&1 | grep -i "warn" | wc -l)
    
    echo "  Errors found: $error_count"
    echo "  Warnings found: $warning_count"
    
    if [ $error_count -gt 0 ]; then
        echo ""
        echo -e "${RED}Recent errors:${NC}"
        docker logs moldb-frontend 2>&1 | grep -i "error" | tail -5 | sed 's/^/  │ /'
    fi
    
    # Check for specific patterns
    echo ""
    echo -e "${MAGENTA}Key Log Patterns:${NC}"
    
    if docker logs moldb-frontend 2>&1 | grep -qi "VITE.*ready"; then
        print_ok "Vite dev server is ready"
    else
        print_warning "Vite dev server not ready or not found"
    fi
    
    if docker logs moldb-frontend 2>&1 | grep -qi "Local.*3000"; then
        print_ok "Server listening on port 3000"
    else
        print_warning "Port 3000 not mentioned in logs"
    fi
    
    if docker logs moldb-frontend 2>&1 | grep -qi "EADDRINUSE"; then
        print_error "Port already in use error detected"
    fi
    
    if docker logs moldb-frontend 2>&1 | grep -qi "ECONNREFUSED"; then
        print_error "Connection refused error detected"
    fi
    
elif docker ps -a | grep -q moldb-frontend; then
    echo -e "${YELLOW}Frontend container exists but not running${NC}"
    echo "Container logs (last 30 lines):"
    echo "╭─────────────────────────────────────────────────────────╮"
    docker logs --tail=30 moldb-frontend 2>&1 | sed 's/^/  │ /'
    echo "╰─────────────────────────────────────────────────────────╯"
else
    print_warning "Frontend container not found - no logs available"
fi

# ============================================================================
print_section "8. CONNECTIVITY TEST"

echo -e "${MAGENTA}Testing Internal Connectivity:${NC}"

# Test if backend is accessible
echo "  Backend API:"
if curl -sf http://localhost:8000/api/v1/health > /dev/null 2>&1; then
    print_ok "http://localhost:8000/api/v1/health is accessible"
else
    print_error "http://localhost:8000/api/v1/health is NOT accessible"
fi

# Test if frontend is accessible
echo "  Frontend:"
if curl -sf http://localhost:3000 > /dev/null 2>&1; then
    print_ok "http://localhost:3000 is accessible"
else
    print_error "http://localhost:3000 is NOT accessible"
fi

# Test from container (if running)
if docker ps | grep -q moldb-frontend; then
    echo ""
    echo -e "${MAGENTA}Testing from Frontend Container:${NC}"
    
    echo "  Can reach backend?"
    if docker-compose exec -T frontend wget -qO- http://backend:8000/api/v1/health > /dev/null 2>&1; then
        print_ok "Yes, backend is reachable"
    else
        print_error "No, cannot reach backend"
    fi
    
    echo "  Can reach postgres?"
    if docker-compose exec -T frontend ping -c 1 postgres > /dev/null 2>&1; then
        print_ok "Yes, postgres is reachable"
    else
        print_error "No, cannot reach postgres"
    fi
    
    echo "  Can reach redis?"
    if docker-compose exec -T frontend ping -c 1 redis > /dev/null 2>&1; then
        print_ok "Yes, redis is reachable"
    else
        print_error "No, cannot reach redis"
    fi
fi

# ============================================================================
print_section "9. DISK USAGE"

echo -e "${MAGENTA}Docker Disk Usage:${NC}"
docker system df

echo ""
echo -e "${MAGENTA}Detailed Breakdown:${NC}"
echo "  Images:"
docker images --format "    {{.Repository}}:{{.Tag}} = {{.Size}}" | grep -E "moldb|molecule-discovery-system" | head -5

echo ""
echo "  Containers:"
docker ps -a --format "    {{.Names}} = {{.Size}}" --size | grep moldb | head -5

# ============================================================================
print_section "10. CONFIGURATION FILES"

echo -e "${MAGENTA}Checking Configuration Files:${NC}"

# Check docker-compose.yml
if [ -f "docker-compose.yml" ]; then
    print_ok "docker-compose.yml exists"
    
    # Extract frontend config
    echo ""
    echo -e "${MAGENTA}Frontend Service Config:${NC}"
    echo "╭─────────────────────────────────────────────────────────╮"
    sed -n '/frontend:/,/^  [a-z]/p' docker-compose.yml | head -n -1 | sed 's/^/  │ /'
    echo "╰─────────────────────────────────────────────────────────╯"
else
    print_error "docker-compose.yml NOT found"
fi

echo ""
# Check frontend Dockerfile
if [ -f "docker/frontend.Dockerfile" ]; then
    print_ok "docker/frontend.Dockerfile exists"
    
    echo ""
    echo -e "${MAGENTA}Dockerfile Content:${NC}"
    echo "╭─────────────────────────────────────────────────────────╮"
    cat docker/frontend.Dockerfile | sed 's/^/  │ /'
    echo "╰─────────────────────────────────────────────────────────╯"
else
    print_error "docker/frontend.Dockerfile NOT found"
fi

# ============================================================================
print_section "11. ENVIRONMENT VARIABLES"

if docker ps | grep -q moldb-frontend; then
    echo -e "${MAGENTA}Frontend Container Environment:${NC}"
    docker-compose exec -T frontend env | grep -E "VITE|NODE|PATH" | sort | sed 's/^/  │ /'
else
    print_warning "Container not running - cannot check environment"
fi

# ============================================================================
print_section "12. SUMMARY & RECOMMENDATIONS"

echo -e "${MAGENTA}Current Status:${NC}"

# Container status
if docker ps | grep -q moldb-frontend; then
    print_ok "Frontend container is RUNNING"
elif docker ps -a | grep -q moldb-frontend; then
    print_warning "Frontend container EXISTS but NOT running"
else
    print_error "Frontend container DOES NOT exist"
fi

# Image status
if docker images | grep -q "frontend"; then
    print_ok "Frontend image exists"
else
    print_error "Frontend image NOT found"
fi

# Port status
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    if docker ps | grep -q moldb-frontend; then
        print_ok "Port 3000 is used by frontend container"
    else
        print_error "Port 3000 is used by ANOTHER process"
    fi
else
    print_warning "Port 3000 is FREE"
fi

# Connectivity
if curl -sf http://localhost:3000 > /dev/null 2>&1; then
    print_ok "Frontend is ACCESSIBLE from host"
else
    print_error "Frontend is NOT accessible from host"
fi

echo ""
echo -e "${MAGENTA}Recommendations:${NC}"

# Generate recommendations based on findings
if ! docker ps | grep -q moldb-frontend; then
    if docker ps -a | grep -q moldb-frontend; then
        echo "  • Container exists but not running - try: docker-compose up -d frontend"
    else
        echo "  • Container missing - need to create: docker-compose build frontend && docker-compose up -d frontend"
    fi
fi

if docker logs moldb-frontend 2>&1 | grep -qi "error"; then
    echo "  • Errors found in logs - check with: docker-compose logs frontend"
fi

if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1 && ! docker ps | grep -q moldb-frontend; then
    echo "  • Port 3000 blocked by another process - free it first"
fi

if ! curl -sf http://localhost:3000 > /dev/null 2>&1 && docker ps | grep -q moldb-frontend; then
    echo "  • Container running but not accessible - check Dockerfile CMD and port binding"
fi

# ============================================================================
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Inspection Complete                                      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}No changes were made to your system.${NC}"
echo ""
echo "Useful commands:"
echo "  • View logs:     docker-compose logs -f frontend"
echo "  • Restart:       docker-compose restart frontend"
echo "  • Rebuild:       docker-compose build frontend"
echo "  • Start:         docker-compose up -d frontend"
echo "  • Enter shell:   docker-compose exec frontend sh"
echo ""./inspect-only.sh