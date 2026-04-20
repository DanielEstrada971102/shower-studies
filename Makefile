# ------------------------------
# Variables (defaults can be overridden by user)
# ------------------------------
MPLDTS_PATH?=../mplDTs
DTPR_PATH?=../DTPatternRecognition
ENV_DIR?=.venv
MPLDTS_VERSION?=enhancement-cacheObjects
DTPR_VERSION?=v3.4.0-beta
_GIT_MPLDTS?=git+https://github.com/INTREPID-hep/mplDTs.git@$(MPLDTS_VERSION)
_GIT_DTPR?=git+https://github.com/INTREPID-hep/DTPatternRecognition.git@$(DTPR_VERSION)


# ------------------------------
# Internal helper: check ROOT and set PYTHONPATH
# ------------------------------
check-root:
	@if ! python3 -c "import ROOT" >/dev/null 2>&1; then \
		echo "❌ ROOT not found! Please install ROOT >= 6.24 and ensure it's in PYTHONPATH."; \
		exit 1; \
	else \
		echo "✅ ROOT is available"; \
	fi

check-local-repos: clone-mpldts-if-needed clone-dtpr-if-needed

clone-mpldts-if-needed:
	@if [ ! -d "$(MPLDTS_PATH)" ]; then \
		echo "📥 Cloning mplDTs into $(MPLDTS_PATH)"; \
		git clone -b $(MPLDTS_VERSION) https://github.com/INTREPID-hep/mplDTs.git "$(MPLDTS_PATH)"; \
	else \
		echo "✅ mplDTs repo exists at $(MPLDTS_PATH)"; \
	fi

clone-dtpr-if-needed:
	@if [ ! -d "$(DTPR_PATH)" ]; then \
		echo "📥 Cloning DTPatternRecognition into $(DTPR_PATH)"; \
		git clone -b $(DTPR_VERSION) https://github.com/INTREPID-hep/DTPatternRecognition.git "$(DTPR_PATH)"; \
	else \
		echo "✅ DTPatternRecognition repo exists at $(DTPR_PATH)"; \
	fi

check-mpldts-version:
	@python3 -c "import sys; import mpldts; sys.exit(0) if mpldts.__version__ == '$(MPLDTS_VERSION)' else sys.exit(1)" >/dev/null 2>&1

reinstall-mpldts-if-needed:
	@$(MAKE) check-mpldts-version || { \
		echo "🔄 Reinstalling mplDTs to match version $(MPLDTS_VERSION)"; \
		pip uninstall -y mplDTs; \
		pip install $(_GIT_MPLDTS); \
		echo "✅ mplDTs reinstalled"; \
	}

reinstall-mpldts-dev-if-needed:
	@$(MAKE) check-mpldts-version || { \
		echo "🔄 Reinstalling mplDTs to match version $(MPLDTS_VERSION)"; \
		$(ENV_DIR)/bin/pip uninstall -y mplDTs; \
		$(ENV_DIR)/bin/pip install -e $(_GIT_MPLDTS); \
		echo "✅ mplDTs reinstalled"; \
	}

comment-mpldts-in-pyproject:
	sed -i '/mplDTs/s/^/# /' $(DTPR_PATH)/pyproject.toml

install-other-deps:
	pip install -r requirements.txt

# ------------------------------
# Targets
# ------------------------------

.PHONY: install install-local dev dev-local clean help set-path print-path-only

help:
	@echo "Available targets:"
	@echo "  install		 Install project + GitHub dependencies (non-editable, set MPLDTS_VERSION/DTPR_VERSION)"
	@echo "  install-local   Install project + local path dependencies (editable)"
	@echo "  dev-git		 Create/use a virtualenv and install GitHub deps (set MPLDTS_VERSION/DTPR_VERSION)"
	@echo "  dev-local	   Create/use a virtualenv and install local deps editable"
	@echo "				  Use ENV_DIR=<path> to override venv location (default: .venv)"
	@echo "  clean		   Remove build artifacts"
	@echo "  delete-venv	 Delete the virtual environment (if exists). Ensure to deactivate your venv first"
	@echo "  help			Show this help message"
# Install from GitHub repos (non-editable)
install: check-root
	pip install $(_GIT_DTPR)
	@$(MAKE) reinstall-mpldts-if-needed
	$(MAKE) install-other-deps
	$(MAKE) set-path

# Install using local paths (editable mode)
install-local: check-root check-local-repos
	@$(MAKE) comment-mpldts-in-pyproject
	pip install -e $(MPLDTS_PATH)
	pip install -e $(DTPR_PATH)
	$(MAKE) install-other-deps
	$(MAKE) set-path

# Development mode: create/use a venv and install GitHub deps (non-editable)
dev: check-root
	@if [ ! -d "$(ENV_DIR)" ]; then \
		echo "🔧 Creating virtual environment in $(ENV_DIR)"; \
		python3 -m venv --system-site-packages ROOT $(ENV_DIR); \
	else \
		echo "⚡ Using existing virtual environment in $(ENV_DIR)"; \
	fi
	$(ENV_DIR)/bin/pip install --upgrade pip
	$(ENV_DIR)/bin/pip install $(_GIT_DTPR)
	@$(MAKE) reinstall-mpldts-dev-if-needed
	$(ENV_DIR)/bin/pip install -r requirements.txt
	@echo "✅ Dev environment ready in $(ENV_DIR)"
	@echo "👉 Activate it with: source $(ENV_DIR)/bin/activate"
	$(MAKE) set-path

# Development mode: create/use a venv and install local deps editable
dev-local: check-root check-local-repos
	@if [ ! -d "$(ENV_DIR)" ]; then \
		echo "🔧 Creating virtual environment in $(ENV_DIR)"; \
		python3 -m venv --system-site-packages $(ENV_DIR); \
	else \
		echo "⚡ Using existing virtual environment in $(ENV_DIR)"; \
	fi
	$(ENV_DIR)/bin/pip install --upgrade pip
	@$(MAKE) comment-mpldts-in-pyproject
	$(ENV_DIR)/bin/pip install -e $(MPLDTS_PATH)
	$(ENV_DIR)/bin/pip install -e $(DTPR_PATH)
	@$(MAKE) install-other-deps
	@echo "✅ Dev environment ready in $(ENV_DIR)"
	@echo "👉 Activate it with: source $(ENV_DIR)/bin/activate"
	$(MAKE) set-path

# Clean build artifacts + optionally delete venv
clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf build dist *.egg-info __pycache__
	find . -name "__pycache__" -type d -exec rm -rf {} +

delete-venv:
	@if [ -d "$(ENV_DIR)" ]; then \
		echo "🗑️  Deleting virtual environment in $(ENV_DIR)"; \
		rm -rf $(ENV_DIR); \
	else \
		echo "⚠️  No virtual environment found in $(ENV_DIR)"; \
	fi
	$(MAKE) clean

set-path:
	@echo "👉 Ensure project root and first-level folders are in PYTHONPATH. Run:"
	@echo "   eval \"\$$($(MAKE) -s set-path-command)\""

set-path-command:
	@echo "export PYTHONPATH=\$$PYTHONPATH:$(PWD):\$$(find \"$(PWD)\" -mindepth 1 -maxdepth 1 -type d ! -name '.*' ! -name 'env' ! -name 'venv' ! -name '$(notdir $(ENV_DIR))' | paste -sd: -)"
