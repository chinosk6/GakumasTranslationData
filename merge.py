import os, json, shutil
import posixpath

from merge_utils import (
    merge_translated_csv_into_txt,
    line_level_dual_lang_translation_merger,
)

def merge_translation_files(raw_folder: str, translation_folder: str, pretranslation_folder, resource_folder: str):
    translation_file_index = json.load(
        open(os.path.join(pretranslation_folder, "index.json"), encoding="utf-8")
    )

    for k in translation_file_index:
        translation_file_index[k] = posixpath.join(
            pretranslation_folder, translation_file_index[k]
        )

    # overwrite fields because of higher priority
    with open(
        os.path.join(translation_folder, "index.json"), "r", encoding="utf-8"
    ) as f:
        tmp = json.load(f)
        for k in tmp:

            translation_file_index[k] = posixpath.join(translation_folder, tmp[k])

    for file in os.listdir(raw_folder):
        if not file.endswith(".txt"):
            continue
        translation_file_path = translation_file_index.get(file)
        if translation_file_path is None:
            continue

        csv: str
        txt: str
        with open(translation_file_path, "r", encoding="utf-8") as f:
            csv = "".join(f.readlines())
        with open(posixpath.join(raw_folder, file), "r", encoding="utf-8") as f:
            txt = "".join(f.readlines())
        dest_resource_path = posixpath.join(resource_folder, file)
        
        try:
            merged_txt = merge_translated_csv_into_txt(
                csv, txt, line_level_dual_lang_translation_merger
            )
            with open(dest_resource_path, "w", encoding="utf-8") as f:
                f.write(merged_txt)
            # break
        except Exception as e:
            print(e)
            print(dest_resource_path)

if __name__ == "__main__":
    raw_folder = "./raw"
    translation_folder = "./gakuen-adapted-translation-data"
    pretranslation_folder = "./GakumasPreTranslation"
    resource_folder = "./local-files/resource"
    merge_translation_files(raw_folder, translation_folder, pretranslation_folder, resource_folder)
    shutil.copy(
        f"{pretranslation_folder}/etc/localization.json",
        f"./local-files/localization.json",
    )
