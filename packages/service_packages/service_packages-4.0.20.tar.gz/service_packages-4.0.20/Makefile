CODE_DIRS = src
.PHONY: build patch upload

# Default target
help:
	@echo "Available targets:"
	@echo "  build       - build package"
	@echo "  patch       - update version"
	@echo "  upload      - upload to pypi repository"

build:
	@echo "Build package..."
	rm -rf dist; uv build .

patch:
	@echo "Patch version..."
	uv version --bump patch

upload:
	@echo "Upload to pypi repository..."
	uv publish