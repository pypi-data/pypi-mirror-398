# publish - build package and publish
 

# publish to pypi
publish: release
	$(call check_private)
	$(call require_pypi_config)
	@set -e;\
	if [ "$(version)" != "$(pypi_version)" ]; then \
	  $(call verify_action,publish to PyPi);\
	  echo publishing $(project) $(version) to PyPI...;\
	  flit publish;\
	else \
	  echo $(project) $(version) is up-to-date on PyPI;\
	fi
	command -v >/dev/null devpi && devpi refresh $(project) || true

# check current pypi version 
pypi-check:
	$(call require_pypi_config)
	@echo '$(project) local=$(version) pypi=$(call check_pypi_version)'

# clean up publish generated files
publish-clean:
	rm -f .dist
	rm -rf .tox

publish-sterile:
	@:

# functions
define require_pypi_config =
$(if $(wildcard ~/.pypirc),,$(error publish failed; ~/.pypirc required))
endef

define pypi_version =
$(shell curl -s https://pypi.org/pypi/$(project)/json | jq -r '.info.version')
endef

define check_null =
$(if $(1),$(1),$(error $(2)))
endef

check_pypi_version = $(call check_null,$(pypi_version),PyPi version query failed)

define check_private = 
$(if $(shell tq < pyproject.toml '.project.classifiers' | grep Private),$(error 'Private' classifier set in pyproject.toml),)
endef
