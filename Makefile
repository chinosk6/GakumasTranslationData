update-localization:
	cd GakumasPreTranslation && pnpm install && pnpm ts-node main.ts

merge:
	pip install -r requirements.txt && python merge.py

build-resource: update-localization merge

