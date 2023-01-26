.PHONY: init, run

init:
	pip3 install -r "requirements.txt"
	python3 -m spacy download en_core_web_sm

run:
	python3 scraper.py