#!/bin/bash

set -euo pipefail

# Colors for terminal output
# Enable colors if: TTY detected, FORCE_COLOR=1, or TERM is set (common in Docker)
if [[ -t 1 ]] || [[ "${FORCE_COLOR:-}" == "1" ]] || [[ -n "${TERM:-}" ]]; then
	readonly RED='\033[0;31m'
	readonly YELLOW='\033[0;33m'
	readonly GREEN='\033[0;32m'
	readonly BLUE='\033[0;34m'
	readonly NC='\033[0m' # No Color
else
	readonly RED=''
	readonly YELLOW=''
	readonly GREEN=''
	readonly BLUE=''
	readonly NC=''
fi

# Get current timestamp for log messages
_timestamp() {
	date '+%Y-%m-%d %H:%M:%S'
}

# Log info message
log_info() {
	echo -e "${BLUE}[$(_timestamp)] [INFO]${NC} $*"
}

# Log success message
log_success() {
	echo -e "${GREEN}[$(_timestamp)] [SUCCESS]${NC} $*"
}

# Log warning message
log_warn() {
	echo -e "${YELLOW}[$(_timestamp)] [WARN]${NC} $*" >&2
}

# Log error message
log_error() {
	echo -e "${RED}[$(_timestamp)] [ERROR]${NC} $*" >&2
}

# Log a message without any prefix (for multi-line output)
log_plain() {
	echo -e "$*"
}

# function to handle termination signals
_term() {
	log_info "Termination signal received. Shutting down gracefully..."
	# Add any cleanup commands here
	exit 0
}
# trap termination signals
trap _term SIGTERM SIGINT

check_docker_config() {
	# Check if Docker config.json exists with valid auth credentials
	if [[ -f "$DOCKER_CONFIG/config.json" ]]; then
		# Verify the file contains auth data (not just an empty or invalid config)
		if grep -q '"auths"' "$DOCKER_CONFIG/config.json" 2>/dev/null; then
			log_info "Found Docker authentication in $DOCKER_CONFIG/config.json"
			return 0
		else
			# Return 1 silently - main script will log detailed user-facing message
			return 1
		fi
	fi
	return 1
}

# No password file reading - only environment variables supported for runtime auth

# Function to check for required environment variables
check_env_vars() {
	local required_vars=("REGISTRY_URL" "UDS_USERNAME" "UDS_PASSWORD")
	for var in "${required_vars[@]}"; do
		if [[ -z "${!var:-}" ]]; then
			log_error "Environment variable '$var' is not set."
			log_error "Please provide it via -e $var=<value>"
			exit 1
		fi
	done
}

# Function to login to registry
login_to_registry() {
	log_info "Logging in to registry: $REGISTRY_URL..."
	if ! echo "$PASSWORD" | uds zarf tools registry login "$REGISTRY_URL" --username "$UDS_USERNAME" --password-stdin; then
		log_error "Failed to login to registry."
		exit 1
	fi
	log_success "Successfully logged in to registry."
}

# function to update the grype database
update_grype_db() {
	local status_output
	status_output=$(grype db status 2>/dev/null || true)
	if echo "$status_output" | grep -q "Status:    invalid"; then
		local db_age
		db_age=$(echo "$status_output" | grep "Built:" | awk '{print $2 " " $3}')
		if [[ "$SKIP_UPDATE_VULNDB_DB" == "true" ]]; then
			log_warn "Grype vulnerability database was built on $db_age. You should update."
			return
		fi
		log_info "Updating Grype vulnerability database..."
		# Show progress with spinner
		local pid
		grype db update &> /dev/null &
		pid=$!
		local spin='-\|/'
		local i=0
		while kill -0 $pid 2>/dev/null; do
			i=$(( (i+1) % 4 ))
			printf "\r  [%c] Downloading..." "${spin:$i:1}"
			sleep 0.2
		done
		printf "\r                      \r"
		wait $pid
		if [[ $? -ne 0 ]]; then
			log_error "Failed to update Grype vulnerability database."
			exit 1
		fi
		log_success "Grype vulnerability database updated successfully."
	else
		log_info "Grype vulnerability database is up to date."
	fi
}

update_trivy_db() {
	if [[ "$SKIP_UPDATE_VULNDB_DB" == "true" ]]; then
		log_warn "Skipping Trivy database update."
		return
	fi
	log_info "Updating Trivy vulnerability database..."

	# Download main vulnerability database with spinner
	local pid
	trivy image --download-db-only --quiet &
	pid=$!
	local spin='-\|/'
	local i=0
	while kill -0 $pid 2>/dev/null; do
		i=$(( (i+1) % 4 ))
		printf "\r  [%c] Downloading vulnerability DB..." "${spin:$i:1}"
		sleep 0.2
	done
	printf "\r                                        \r"
	wait $pid
	if [[ $? -ne 0 ]]; then
		log_error "Failed to update Trivy vulnerability database."
		exit 1
	fi

	# Download Java database with spinner
	trivy image --download-java-db-only --quiet &
	pid=$!
	while kill -0 $pid 2>/dev/null; do
		i=$(( (i+1) % 4 ))
		printf "\r  [%c] Downloading Java DB..." "${spin:$i:1}"
		sleep 0.2
	done
	printf "\r                              \r"
	wait $pid
	if [[ $? -ne 0 ]]; then
		log_error "Failed to update Trivy Java database."
		exit 1
	fi

	log_success "Trivy vulnerability database updated successfully."
}

# Main script execution

# Check if Docker config.json already has authentication (baked-in during build)
if check_docker_config; then
	log_info "Using build-time Docker authentication from config.json"
	log_info "Skipping registry login..."
else
	# Check if user tried to mount a config.json (common mistake)
	if [[ -f "$DOCKER_CONFIG/config.json" ]]; then
		log_warn "A Docker config.json file is present but lacks authentication data."
		log_plain "Mounting your local ~/.docker/config.json won't work - UDS/Zarf requires"
		log_plain "credentials in a specific format or environment variables."
		log_plain ""
		log_plain "Please use one of these methods instead:"
		log_plain "  1. Build a custom image with baked-in credentials (see docs/getting-started/docker.md)"
		log_plain "  2. Provide credentials via environment variables:"
		log_plain "       -e REGISTRY_URL=\"registry.example.com\""
		log_plain "       -e UDS_USERNAME=\"your-username\""
		log_plain "       -e UDS_PASSWORD=\"your-password\""
		log_plain ""
	fi

	log_info "Performing runtime registry login with environment variables..."
	check_env_vars
	# Export PASSWORD for login function
	export PASSWORD="${UDS_PASSWORD}"
	login_to_registry
fi

# update the Grype vulnerability database
update_grype_db

# update the Trivy vulnerability database
update_trivy_db

# Execute the cve-report-aggregator with provided arguments
log_info "Starting cve-report-aggregator..."
exec cve-report-aggregator "$@"
