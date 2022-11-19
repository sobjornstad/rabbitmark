.PHONY: ui

all: ui

ui:
	scripts/make-forms.sh

publish:
	scripts/publish.sh