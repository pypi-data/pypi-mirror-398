.PHONY: docker-build docker-up docker-down docker-test cookbook-up pkg tag release

docker-build:
	docker compose -f dockerfiles/docker-compose.yml build

docker-up:
	docker compose -f dockerfiles/docker-compose.yml up

docker-down:
	docker compose -f dockerfiles/docker-compose.yml down

docker-test:
	docker compose -f dockerfiles/docker-compose.yml run --rm weather-app pytest -q -c tests/pytest.ini

cookbook-up:
	docker compose -f dockerfiles/docker-compose.yml up --build

# ---- Packaging (runs in Docker; writes to ./dist) ----

# Usage:
#   make pkg          # clean + build + twine check
#   make pkg CLEAN=0  # skip cleaning dist/build/*.egg-info
pkg:
	@clean="$${CLEAN:-1}"; \
		if [ "$$clean" != "0" ]; then rm -rf dist build *.egg-info; fi; \
		echo "Building package"; \
		docker compose -f dockerfiles/docker-compose.yml run --rm weather-app sh -lc "python -m pip install -q build && python -m build"; \
		docker compose -f dockerfiles/docker-compose.yml run --rm weather-app sh -lc "python -m pip install -q twine && python -m twine check dist/*"

# ---- Release (locally triggered; CI does build/release/publish) ----

# Create and push a release tag, after validating it's newer than existing tags.
# Usage:
#   make release VERSION=0.1.0
release:
	@version="$${VERSION:-}"; \
		if [ -z "$$version" ]; then \
			echo "Missing VERSION (example: make release VERSION=0.1.0)"; \
			exit 2; \
		fi; \
		branch="$$(git rev-parse --abbrev-ref HEAD)"; \
		if [ "$$branch" != "main" ]; then \
			echo "Refusing to release from branch '$$branch' (must be on 'main')."; \
			exit 1; \
		fi; \
		case "$$version" in \
			[0-9]*.[0-9]*.[0-9]*) ;; \
			*) echo "Invalid VERSION=$$version (expected X.Y.Z)"; exit 2 ;; \
		esac; \
		if ! git diff --quiet || ! git diff --cached --quiet; then \
			echo "Working tree not clean; commit or stash changes before releasing."; \
			exit 1; \
		fi; \
		git fetch --tags origin >/dev/null 2>&1 || true; \
		latest="$$(git tag -l 'v*' --sort=-v:refname | head -n1 | sed 's/^v//')"; \
		parse() { IFS='.' read -r a b c <<EOF\n$$1\nEOF\n; echo $$((a*1000000 + b*1000 + c)); }; \
		if [ -n "$$latest" ]; then \
			if [ "$$(parse "$$version")" -le "$$(parse "$$latest")" ]; then \
				echo "Refusing to release $$version: latest existing is $$latest"; \
				exit 1; \
			fi; \
		fi; \
		tag="v$$version"; \
		if git rev-parse -q --verify "refs/tags/$$tag" >/dev/null; then \
			echo "Tag already exists: $$tag"; \
			exit 1; \
		fi; \
		echo "Creating annotated tag $$tag"; \
		git tag -a "$$tag" -m "Release $$tag"; \
		echo "Pushing $$tag to origin (triggers GitHub Actions release pipeline)"; \
		git push origin "$$tag"

# Alias for muscle memory.
tag: release
