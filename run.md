# Docker Guide: Installation, Verification, and Running Containers

This guide covers how to install Docker on different operating systems, verify the installation, and run Docker images.

## Table of Contents
1. [Docker Installation](#1-docker-installation)
   - [Windows](#windows)
   - [macOS](#macos)
   - [Linux (Ubuntu)](#linux-ubuntu)
2. [Verify Docker Installation](#2-verify-docker-installation)
3. [Running a Docker Image](#3-running-a-docker-image)
4. [Common Docker Commands](#4-common-docker-commands)

## 1. Docker Installation

### Windows
1. Download Docker Desktop for Windows from [Docker's official website](https://www.docker.com/products/docker-desktop/)
2. Run the installer and follow the installation wizard
3. Restart your computer when prompted
4. After restart, Docker Desktop will start automatically
5. You may be prompted to enable WSL 2 features - follow the instructions to enable them if needed

### macOS
1. Download Docker Desktop for Mac from [Docker's official website](https://www.docker.com/products/docker-desktop/)
2. Open the downloaded .dmg file and drag Docker.app to the Applications folder
3. Open Docker.app from your Applications folder
4. Follow the installation prompts and enter your system password when requested

### Linux (Ubuntu)
Run these commands in a terminal to install Docker Engine:

```bash
# Update the package index
sudo apt-get update

# Install required packages
sudo apt-get install -y ca-certificates curl gnupg lsb-release

# Add Docker's official GPG key
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Set up the repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start and enable Docker
sudo systemctl enable --now docker

# Add your user to the docker group (optional but recommended)
sudo usermod -aG docker $USER
```

**Note for Linux users:** After adding your user to the docker group, you'll need to log out and back in for the changes to take effect.

## 2. Verify Docker Installation

To verify that Docker is installed correctly, open a new terminal and run:

```bash
# Check Docker version
docker --version

# Verify installation with a test container
docker run --rm hello-world
```

You should see output indicating that Docker is working correctly, including a message that says "Hello from Docker!"

## 3. Running the Project with Docker

This project includes a `Dockerfile` that sets up the environment and runs the invoice matcher. Here's how to use it:

1. **Build the Docker image**:
   ```bash
   docker build -t invoice-matcher .
   ```

2. **Run the container**:
   ```bash
   docker run --rm -v "$(pwd)/data:/app/data" -v "$(pwd)/out:/app/out" invoice-matcher
   ```

   This command:
   - Builds an image named `invoice-matcher` from the Dockerfile in the current directory
   - Runs the container and removes it when done (`--rm`)
   - Mounts the local `data` directory to `/app/data` in the container
   - Mounts the local `out` directory to `/app/out` in the container for output files

3. **Verify the output**:
   After running, check the `out` directory for the generated files:
   - `matches.csv`
   - `unmatched_invoices.csv`
   - `unmatched_payments.csv`

## 4. Common Docker Commands for Development

Here are some useful commands when working with this project:

```bash
# Rebuild the image (after making changes to the code or Dockerfile)
docker build -t invoice-matcher .

# Run the container with a specific command (e.g., to get a shell)
docker run -it --rm -v "$(pwd)/data:/app/data" -v "$(pwd)/out:/app/out" invoice-matcher /bin/bash

# View running containers
docker ps

# View logs of a running container
docker logs <container_id>
```