.PHONY: build-LabRecallApi

build-LabRecallApi:
	python3.12 -m pip install -r requirements-lambda.txt -t "$(ARTIFACTS_DIR)"
	cp -R src/labrecall "$(ARTIFACTS_DIR)/labrecall"
