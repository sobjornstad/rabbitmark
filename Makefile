.PHONY: ui publish

all: ui

ui:
	scripts/make-forms.sh

publish:
	scripts/publish.sh