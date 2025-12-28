.PHONY: all help lint build local-install upload clean sign run-script docs

all:
	@$(MAKE) clean
	@$(MAKE) local-install
	@$(MAKE) run-script

clean:
	@echo "Cleaning..."
	@rm -rf build dist *.egg-info
	@echo -e "\nDone!"

distclean: clean
	@echo "Cleaning Everything..."
	@rm -rf .mypy_cache .ropeproject .pytest_cache
	@echo -e "\nDone!"

docs:
	@echo -e "Generating docs...\n"
	@$(MAKE) -C docs html
	@echo -e "\nDone!"

help:
	@echo -e "\nAvailable targets:"
	@echo "  build"
	@echo "  clean"
	@echo "  distclean"
	@echo "  docs"
	@echo "  help"
	@echo "  lint"
	@echo "  local-install"
	@echo "  run-script"
	@echo "  sign"
	@echo "  stubs"
	@echo "  upload"
	@echo

lint:
	@echo -e "Linting...\n"
	@flake8 --statistics --show-source --color=always --max-line-length=100 --ignore=D401 \
		--per-file-ignores=__init__.py:F401 \
		--exclude .tox,.git,*staticfiles*,build,locale,docs,tools,venv,.venv,*migrations*,*.pyc,*.pyi,__pycache__,test_*.py \
		.
	@echo -e "\nDone!"

stubs: lint
	@echo -e "Generating stubs...\n"
	@stubgen --include-docstrings --include-private -p vim_eof_comment -o .
	@echo -e "\nDone!"
	@echo -e "\nRunning isort...\n"
	@isort vim_eof_comment
	@echo -e "\nDone!"
	@echo -e "\nLinting with mypy...\n"
	@mypy vim_eof_comment
	@echo -e "\nDone!"

build: stubs
	@echo -e "Building...\n"
	@python3 -m build &> /dev/null
	@echo -e "\nDone!"

sign: build
	@echo -e "Signing build...\n"
	@pypi-attestations sign dist/*
	@echo -e "\nDone!"

local-install: build
	@echo -e "Installing locally...\n"
	@python3 -m pip install .
	@echo -e "\nDone!"

run-script:
	@echo -e "Running vim-eof-comment...\n"
	@vim-eof-comment -e py,pyi,Makefile -n -v .
	@echo -e "\nDone!"

upload: sign
	@echo -e "Uploading to PyPI...\n"
	@twine upload dist/*
	@echo -e "\nDone!"

# vim: set ts=4 sts=4 sw=0 noet ai si sta:
