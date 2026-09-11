import os, json, shutil
import posixpath

from merge_utils import (
    merge_translated_csv_into_txt,
    line_level_dual_lang_translation_merger,
    TranslationValidationError,
)

def merge_translation_files(raw_folder: str, translation_folder: str, pretranslation_folder, resource_folder: str):
    with open(os.path.join(pretranslation_folder, "index.json"), encoding="utf-8") as f:
        translation_file_index = json.load(f)

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

    # 加载人名字典
    name_dict = {}
    if os.path.exists("name_dictionary.json"):
        with open("name_dictionary.json", "r", encoding="utf-8") as f:
            name_dict = json.load(f)

    checked_files = 0
    failed_files = 0
    error_count = 0
    for file in sorted(os.listdir(raw_folder)):
        if not file.endswith(".txt") and not file.startswith("adv_"):
            continue
        translation_file_path = translation_file_index.get(file)
        if translation_file_path is None:
            continue

        checked_files += 1
        dest_resource_path = posixpath.join(resource_folder, file)
        
        try:
            with open(translation_file_path, "r", encoding="utf-8") as f:
                csv = f.read()
            with open(posixpath.join(raw_folder, file), "r", encoding="utf-8") as f:
                txt = f.read()
            merged_txt = merge_translated_csv_into_txt(
                csv, txt, line_level_dual_lang_translation_merger, name_dict
            )
            with open(dest_resource_path, "w", encoding="utf-8") as f:
                f.write(merged_txt)
        except Exception as e:
            failed_files += 1
            errors = e.errors if isinstance(e, TranslationValidationError) else [str(e) or type(e).__name__]
            error_count += len(errors)
            print(f"\nValidation failed: {dest_resource_path}")
            print(f"CSV: {translation_file_path}")
            for error in errors:
                print(f"  {error}")

    print(
        f"\nChecked {checked_files} translated files: "
        f"{checked_files - failed_files} succeeded, {failed_files} failed, "
        f"{error_count} error(s)."
    )

if __name__ == "__main__":
    raw_folder = "./raw"
    translation_folder = "./gakuen-adapted-translation-data"
    pretranslation_folder = "./GakumasPreTranslation"
    generic_translation_source_folder = "./gakumas-generic-strings-translation/translated"
    generic_translation_dest_folder = "./local-files/genericTrans"
    resource_folder = "./local-files/resource"
    master_translation_source_folder = "./gakumas-master-translation/data"
    master_translation_dest_folder = "./local-files/masterTrans"

    merge_translation_files(raw_folder, translation_folder, pretranslation_folder, resource_folder)
    shutil.copy(
        f"{pretranslation_folder}/etc/localization.json",
        f"./local-files/localization.json",
    )
    if os.path.exists(generic_translation_dest_folder):
        shutil.rmtree(generic_translation_dest_folder)
    shutil.copytree(generic_translation_source_folder, generic_translation_dest_folder)

    if os.path.exists(master_translation_dest_folder):
        shutil.rmtree(master_translation_dest_folder)
    shutil.copytree(master_translation_source_folder, master_translation_dest_folder)
