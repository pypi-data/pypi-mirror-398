#!/bin/bash
# scripts/build.sh

# Exit on error
set -e

VERSION=$1

if [ -z "$VERSION" ]; then
    echo "Error: Version argument is required (e.g., v1.10.1)"
    exit 1
fi

echo "🚀 Starting build for sing-box version: $VERSION"

# Cleanup previous builds
rm -rf sing-box-tmp
mkdir -p src/sing_box_bin/bin

# Clone repo
echo "📥 Cloning sing-box..."
git clone https://github.com/SagerNet/sing-box sing-box-tmp --depth 1 --branch "$VERSION"
cd sing-box-tmp

# Build configuration
TAGS="with_quic,with_wireguard,with_clash_api,with_gvisor"
export CGO_ENABLED=0
# Read version internally from the go module to ensure consistency
INTERNAL_VERSION=$(go run ./cmd/internal/read_tag)

PARAMS=(-v -trimpath -ldflags "-X 'github.com/sagernet/sing-box/constant.Version=$INTERNAL_VERSION' -s -w -buildid=")
MAIN_PARAMS=("${PARAMS[@]}" -tags "$TAGS")
MAIN="./cmd/sing-box"

# --- Linux Build ---
echo "🔨 Building for Linux (AMD64)..."
export GOOS=linux
export GOARCH=amd64
go build "${MAIN_PARAMS[@]}" -o sing-box-linux-amd64 "$MAIN"
mv sing-box-linux-amd64 ../src/sing_box_bin/bin/

# --- Windows Build ---
echo "🔨 Building for Windows (AMD64)..."
export GOOS=windows
export GOARCH=amd64
go build "${MAIN_PARAMS[@]}" -o sing-box-windows-amd64.exe "$MAIN"
mv sing-box-windows-amd64.exe ../src/sing_box_bin/bin/

# Cleanup
cd ..
rm -rf sing-box-tmp

echo "✅ Build completed! Binaries are in src/sing_box_bin/bin/"
ls -lh src/sing_box_bin/bin/
