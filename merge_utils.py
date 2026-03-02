import re, warnings
from typing import Callable, Optional, Union, Dict
from typing_extensions import Protocol
from imas_tools.story.story_csv import StoryCsv
from imas_tools.story.gakuen_parser import parse_messages

class Merger(Protocol):
    def __call__(
        self,
        original_text: str,
        translated_text: str,
        validation_original_text: Optional[str] = None,
        *,
        is_choice: bool = False,
    ) -> str: ...


def merge_translated_csv_into_txt(
    csv_text: Union[str, list[str]],
    gakuen_txt: str,
    merger: Merger,
    name_dict: Optional[Dict[str, str]] = None,
) -> str:
    story_csv = StoryCsv(csv_text)
    parsed = parse_messages(gakuen_txt)
    iterator = iter(story_csv.data)

    # 收集所有需要进行的替换操作
    replacements = []
    
    for line in parsed:
        if line["__tag__"] == "message" or line["__tag__"] == "narration":
            if line.get("text"):
                next_csv_line = next(iterator)
                new_text = merger(
                    line["text"], next_csv_line["trans"], next_csv_line["text"]
                )
                replacements.append({
                    "old": f"text={line['text']}",
                    "new": f"text={new_text}",
                    "length": len(line['text'])
                })
        elif line["__tag__"] == "title":
            if line.get("title"):
                next_csv_line = next(iterator)
                new_text = merger(
                    line["title"], next_csv_line["trans"], next_csv_line["text"]
                )
                replacements.append({
                    "old": f"title={line['title']}",
                    "new": f"title={new_text}",
                    "length": len(line['title'])
                })
        elif line["__tag__"] == "choicegroup":
            if isinstance(line["choices"], list):
                for choice in line["choices"]:
                    next_csv_line = next(iterator)
                    new_text = merger(
                        choice["text"],
                        next_csv_line["trans"],
                        next_csv_line["text"],
                        is_choice=True,
                    )
                    replacements.append({
                        "old": f"text={choice['text']}",
                        "new": f"text={new_text}",
                        "length": len(choice['text'])
                    })
            elif isinstance(line["choices"], dict):
                next_csv_line = next(iterator)
                new_text = merger(
                    line["choices"]["text"],
                    next_csv_line["trans"],
                    next_csv_line["text"],
                    is_choice=True,
                )
                replacements.append({
                    "old": f'text={line["choices"]["text"]}',
                    "new": f"text={new_text}",
                    "length": len(line["choices"]["text"])
                })
    
    # 按文本长度从长到短排序，避免短相似文本优先匹配的问题
    replacements.sort(key=lambda x: x["length"], reverse=True)
    
    # 执行替换
    # 为避免子串匹配问题（如 text=………… 匹配到 text=……………的前半部分）
    # 需要确保匹配的是完整的属性值，即后面跟的是分隔符而不是属性值的一部分
    for replacement in replacements:
        old_str = replacement["old"]
        new_str = replacement["new"]
        
        # 找到第一次出现的位置
        pos = gakuen_txt.find(old_str)
        if pos == -1:
            continue  # 未找到，跳过
            
        # 检查后面的字符是否为分隔符
        # 属性值后面通常是: 空格 ' '、右括号 ']'、右尖括号 '>'、换行 '\n'
        end_pos = pos + len(old_str)
        if end_pos < len(gakuen_txt):
            next_char = gakuen_txt[end_pos]
            # 如果后面不是分隔符，说明是部分匹配，需要继续查找
            if next_char not in [' ', ']', '>', '\n']:
                # 寻找下一个完整匹配
                found = False
                search_start = pos + 1
                while True:
                    pos = gakuen_txt.find(old_str, search_start)
                    if pos == -1:
                        break
                    end_pos = pos + len(old_str)
                    if end_pos >= len(gakuen_txt):
                        found = True
                        break
                    next_char = gakuen_txt[end_pos]
                    if next_char in [' ', ']', '>', '\n']:
                        found = True
                        break
                    search_start = pos + 1
                
                if not found:
                    continue  # 没找到完整匹配，跳过
        
        # 执行替换
        gakuen_txt = gakuen_txt[:pos] + new_str + gakuen_txt[end_pos:]
    
    # 使用人名字典替换人名
    if name_dict:
        # 按人名长度从长到短排序，避免短人名优先匹配的问题
        sorted_names = sorted(name_dict.items(), key=lambda x: len(x[0]), reverse=True)
        for jp_name, cn_name in sorted_names:
            # 匹配 name=日文名 的模式
            pattern = f"name={jp_name}"
            replacement = f"name={cn_name}"
            gakuen_txt = gakuen_txt.replace(pattern, replacement)
    
    return gakuen_txt


def trivial_translation_merger(
    original_text: str,
    translated_text: str,
    validation_original_text: Optional[str] = None,
    *,
    is_choice=False,
):
    translated_text = escape_equals(translated_text)
    if (
        validation_original_text is not None
        and validation_original_text != original_text
    ):
        raise ValueError(
            f"Original text does not match validation text: {validation_original_text} != {original_text}"
        )
    return translated_text


# <r\=はなみさき>花海咲季</r>hihihi -> 花海咲季hihihi
def remove_r_elements(input_string):
    pattern = r"<r\\=.*?>(.*?)</r>"
    cleaned_string = re.sub(pattern, r"\1", input_string)
    return (cleaned_string.replace("―", "—").replace(r"<em\=>", "")
            .replace("</em>", "").replace("<em>", ""))

# bare "=" is not allowed
# replace all bare "=" with r"\n"
def escape_equals(text):
    return re.sub(r"(?<!\\)=", r"\\=", text)


# eg <r\=はなみさき>花海咲季</r>
def line_level_dual_lang_translation_merger(
    original_text: str,
    translated_text: str,
    validation_original_text: Optional[str] = None,
    *,
    is_choice=False,
):
    if (
        validation_original_text is not None
        and validation_original_text != original_text
    ):
        raise ValueError(
            f"Original text does not match validation text: {validation_original_text} != {original_text}"
        )
    if is_choice:
        # return f"{original_text}\\n{translated_text}"
        return translated_text
    # if line level doesn't match, fallback
    if abs(len(original_text.split("\\n")) - len(translated_text.split("\\n"))) > 1:
        warnings.warn(
            f"Line level doesn't match, fallback to trivial translation merger\nOriginal text: {original_text}\nTranslated text: {translated_text}\n"
        )
        return trivial_translation_merger(
            original_text, translated_text, validation_original_text
        )

    original_text = remove_r_elements(original_text)
    translated_text = remove_r_elements(escape_equals(translated_text))
    if len(original_text.split("\\n")) < len(translated_text.split("\\n")):
        text_len = len(original_text)
        original_text = (
            original_text[0 : text_len // 2] + "\\n" + original_text[text_len // 2 :]
        )
    if len(original_text.split("\\n")) > len(translated_text.split("\\n")):
        original_text = original_text.replace("\\n", " ")
    binds = zip(original_text.split("\\n"), translated_text.split("\\n"))
    texts = []
    for item in binds:
        if any(item):
            texts.append(f"<r\\={item[0]}>{item[1]}</r>")
    return "\\r\\n".join(texts)
