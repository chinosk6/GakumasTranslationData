# GakumasTranslationData

- [gakuen-imas-localify](https://github.com/chinosk6/gakuen-imas-localify) 的翻译示例仓库

## Files and Folder Structure

- `./raw`: Raw game resource file (.txt). Not included in the repository
- `./gakuen-adapted-translation-data`: translation files
- `./GakumasPreTranslation`: pretranslation files, if no translation files are found, these files will be used
- `./local-files/localization.json`: localization strings. expected to be copied from `./GakumasPreTranslation/etc/localization.json`
- `./local-files/generic.json`: Other tracked strings
- `./local-files/genericTrans`: Same as `generic.json`. The folder/file name can be customized to distinguish translated content

## How to build resource

1. ensure submodules are pulled and are up to date
2. create a symbol link or put resource file (.txt communication scripts files) in the `./raw` folder
3. run `make build-resource` to build resource

## Optional

Top layer app will the version.txt content to change every time to release the file.
