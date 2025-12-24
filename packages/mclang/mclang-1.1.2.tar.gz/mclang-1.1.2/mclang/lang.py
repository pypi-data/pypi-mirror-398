__all__ = [
    "Lang",
    "LANGDecoder",
    "LANGEncoder",
    "set_language",
    "get_language",
    "init",
    "translate",
    "tl",
    "dump",
    "dumps",
    "load",
    "loads",
    "open",
    "LANGDecoderError",
]

from typing import Dict, List, Optional, Union
from deep_translator import GoogleTranslator
from io import TextIOWrapper
import re
import os
import json
import locale
import builtins

__lang__ = None
__root__ = None

LANGUAGES = {
    "en_US": "en",
    "en_GB": "en",
    "de_DE": "de",
    "es_ES": "es",
    "es_MX": "es",
    "fr_FR": "fr",
    "fr_CA": "fr",
    "it_IT": "it",
    "ja_JP": "ja",
    "ko_KR": "ko",
    "pt_BR": "pt",
    "pt_PT": "pt",
    "ru_RU": "ru",
    "zh_CN": "zh-CN",
    "zh_TW": "zh-TW",
    "nl_NL": "nl",
    "bg_BG": "bg",
    "cs_CZ": "cs",
    "da_DK": "da",
    "el_GR": "el",
    "fi_FI": "fi",
    "hu_HU": "hu",
    "id_ID": "id",
    "nb_NO": "no",
    "pl_PL": "pl",
    "sk_SK": "sk",
    "sv_SE": "sv",
    "tr_TR": "tr",
    "uk_UA": "uk",
}


class LANGDecoderError(Exception):
    pass


class LangError(Exception):
    pass


class Comment:
    def __init__(self, line: int, text: str):
        self.line = line
        self.text = text


class Lang(Dict[str, str]):
    mode: str
    fp: str
    _comments: List[Comment]

    def __enter__(self) -> "Lang":
        return self

    def __exit__(self, a, b, c) -> None:
        if "w" in self.mode:
            self.save(self.fp)

    def __setitem__(self, __key: str, __value: str) -> None:
        super().__setitem__(str(__key), str(__value))

    def __getitem__(self, __key: str) -> str:
        return self.get(__key, __key)

    def format(self, s: str, *subs) -> str:
        # replace %#
        i = 1
        for rep in subs:
            s = s.replace("%" + str(i), str(rep))
            i += 1

        # replace %s
        i = 0
        regex = r"%s"
        match = re.search(regex, s)
        while match is not None:
            try:
                rep = list(subs)[i]
            except IndexError:
                try:
                    rep = list(subs)[-1]
                except IndexError:
                    rep = ""
            s = s.replace("%s", str(rep), 1)
            match = re.search(regex, s)
            i += 1

        # clean up
        s = re.sub(r"%[1-9]+", "", s)
        s = re.sub(r"%s", "", s)

        return s

    def translate(self, __key: str, *subs: str, fallback: Optional[str] = None) -> str:
        if fallback is None:
            fallback = str(__key)
        result = super().get(str(__key), str(fallback))
        # return self.format(re.sub(r'\s+', '', re.sub(r'#.*', '', result)), *subs)
        return self.format(result, *subs)

    tl = translate

    def set(self, __key: str, __value: str) -> None:
        self[__key] = __value

    @property
    def comments(self) -> List[Comment]:
        return getattr(self, "_comments", [])

    @comments.setter
    def comments(self, value: List[Comment]) -> None:
        if isinstance(value, list):
            setattr(self, "_comments", value)
        else:
            raise TypeError(
                f"Expected list but got '{value.__class__.__name__}' instead."
            )

    def _comment(self, line: int, text: str) -> "Lang":
        """
        Inserts a comment to the file at a specified line before the key/value if any

        :param line: The line to insert at
        :type line: int
        :param text: The contents of the comment
        :type text: str
        :rtype: Lang
        """

        try:
            self._comments.append(Comment(line, text))
        except AttributeError:
            self._comments = [Comment(line, text)]
        return self

    def remove_comment(self, index: int) -> "Lang":
        """
        Removes a comment at the specified index

        :param index: The line comment to remove
        :type index: int
        :rtype: Lang
        """

        try:
            del self._comments[index]
        except (AttributeError, IndexError):
            pass
        return self

    def clear_comments(self) -> "Lang":
        """
        Removes all comments from this file

        :rtype: Lang
        """
        try:
            self._comments.clear()
        except AttributeError:
            self._comments = []
        return self

    # TODO Should break up into chunks so it stays within the character limit.
    # Max: 5000
    # Use multiprocessing to speed up large files.
    def translate_language(self, target: str = "en", **kw) -> "Lang":
        """
        Returns a translated copy of your .lang file between different languages.

        :param target: The resulting language, defaults to 'en'
        :type target: str, optional
        :return: A copy of this lang in the target language
        :rtype: Lang
        """
        gt = GoogleTranslator(target=target, **kw)
        lang = self.copy()
        batchs: List[List[str]] = [[]]

        index = 0
        count = 0
        for v in lang.values():
            count += len(v)
            if count <= 5000:
                batchs[index].append(v)
            else:
                index += 1
                batchs.append([])
                batchs[index].append(v)
                count = 0

        translated = []
        for b in batchs:
            translated.extend(gt.translate_batch(b))

        for i, k in enumerate(lang.keys()):
            lang.set(k, translated[i])

        return lang

    def copy(self) -> "Lang":
        """
        Returns a copy of this language
        """
        lang = Lang(self)
        lang.comments = self.comments
        return lang

    @staticmethod
    def load(fp: TextIOWrapper, **kw) -> "Lang":
        return Lang.loads(fp.read(), **kw)

    @staticmethod
    def loads(s: Union[str, bytes, bytearray], **kw) -> "Lang":
        if not isinstance(s, (str, bytes, bytearray)):
            raise TypeError(
                f"The LANG object must be str, bytes or bytearray, not {s.__class__.__name__}"
            )
        result = LANGDecoder(**kw).decode(s)
        global __root__
        __root__ = result
        return result

    @staticmethod
    def open(fp: str, mode: str = "r") -> "Lang":
        if "r" in mode:
            with builtins.open(fp, "r", encoding="utf-8") as fd:
                lang = Lang.load(fd)
                lang.fp = fp
                lang.mode = mode
                return lang
        else:
            lang = Lang()
            lang.fp = fp
            lang.mode = mode
            return lang

    def dump(self, fd: TextIOWrapper, **kw) -> None:
        iterable = LANGEncoder(**kw).encode(self)
        fd.write(iterable)

    def dumps(self, **kw) -> str:
        return LANGEncoder(**kw).encode(self)

    def save(self, fp: str, **kw) -> None:
        with builtins.open(fp, "w", encoding="utf-8") as fd:
            self.dump(fd)


class LANGDecoder:
    def __init__(self, **kw):
        pass

    def decode(self, s: Union[str, bytes]) -> Lang:
        """
        Decode the string to Lang

        :param s: The string to decode to Lang
        :type s: str
        :return: The decoded Lang
        :rtype: Lang
        """
        if isinstance(s, bytes):
            s = s.decode("utf-8")
        remove = [r"\t", r"#.*"]
        result = Lang({})
        lines = str(s).split("\n")
        num = 0
        current_key: Optional[str] = None

        for idx, raw in enumerate(lines, start=1):
            ln = str(raw).strip().replace("\r", "")
            text = ln.lstrip("\ufeff ")

            if text.startswith("##"):  # save comments
                result._comment(num, re.sub(r"^##", "", text))
                continue
            if text == "":
                continue  # ignore empty lines
            if text.startswith("#"):
                raise LANGDecoderError(
                    f"Line: {idx} - Invalid lang file format. New line character was found while parsing key: '{text}'."
                )

            if "=" in text:
                k, v = text.split("=", 1)
                for r in remove:
                    v = re.sub(r, "", v)
                result[k] = v
                current_key = k
                num += 1
            else:
                if current_key is None:
                    raise LANGDecoderError(
                        f"Line: {idx} - Invalid lang file format. New line character was found while parsing key: '{text}'."
                    )
                cont = "\n" + text
                for r in remove:
                    cont = re.sub(r, "", cont)
                prev = result[current_key]
                result[current_key] = prev + cont

        return result


class LANGEncoder:
    def __init__(self, **kw):
        pass

    def encode(self, obj: Union[Lang, Dict[str, str]]) -> str:
        """
        Encode Lang or dict to string

        :param obj: The object to encode to string
        :type obj: Union[Lang, dict]
        :return: The encoded str
        :rtype: str
        """
        lines = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                lines.append(f"{k}={v}")
        else:
            raise TypeError(
                f"Expected dict or Lang but got '{obj.__class__.__name__}' instead."
            )

        # Comments
        if isinstance(obj, Lang):
            i = 0
            for c in obj.comments:
                lines.insert(c.line + i, f"## {c.text}")
                i += 1
        return str("\n".join(lines)) + "\n"


def set_language(lang: str) -> None:
    """
    Override the locale language

    :param lang: The lang to use
    :type lang: str
    """
    global __lang__
    __lang__ = str(lang)


def get_language() -> Optional[str]:
    """
    The configured language code

    :return: The set language code
    :rtype: str
    """
    global __lang__
    if __lang__ is None:
        __lang__ = locale.getlocale()[0]
    return __lang__


def init(path: str = "texts", default: str = "en_US") -> None:
    """
    Initilize lang file from directory path

    :param path: The path to look for lang files
    :type path: str
    :param default: The defualt lang file to use if the locale lang does not exist, defaults to 'en_US'
    :type default: str, optional
    """

    # get languages
    LANGS = os.path.join(path, "languages.json")
    if os.path.exists(LANGS):  # get list from languages.json
        with builtins.open(LANGS) as fd:
            langs = json.load(fd)
            if not isinstance(langs, list):
                raise TypeError(
                    f"Expected list but got '{langs.__class__.__name__}' insteead."
                )
    else:  # get list from dir
        langs = []
        for file in os.listdir(path):
            if file.endswith(".lang"):
                langs.append(file.replace(".lang", ""))

    # get lang file
    locale_code = get_language()
    if locale_code is None:
        locale_code = "en_US"
    if locale_code in langs:
        with builtins.open(
            os.path.join(path, locale_code + ".lang"), encoding="utf8"
        ) as fd:
            load(fd)
    else:
        fp = os.path.join(path, default + ".lang")
        if os.path.exists(fp):
            with builtins.open(fp, encoding="utf-8") as fd:
                load(fd)


def translate(key: str, *subs: str, fallback: Optional[str] = None) -> str:
    """
    Use the root translator

    :param key: The key to translate
    :type key: str
    :param subs: List of values to subsitute these can either be ordered (`%1`, `%2`, etc) or not ordered (`%s`), defaults to None
    :type subs: str, optional
    :return: The fallback text if key can't be found, defaults to key
    :rtype: str
    """

    if __root__ is None:
        raise LangError("A language file has not been loaded yet.")
    return __root__.translate(key, *subs, fallback=fallback)


tl = translate


def dump(obj: Union[Lang, Dict[str, str]], fp: TextIOWrapper, **kw) -> None:
    """
    Serialize obj as a LANG formatted stream to fp (a `.write()`-supporting file-like object)

    :param obj: _description_
    :type obj: Union[Lang, dict]
    :param fp: _description_
    :type fp: str
    """
    content = LANGEncoder(**kw).encode(obj)
    fp.write(content)


def dumps(obj: Union[Lang, Dict[str, str]], **kw) -> str:
    """
    Serialize obj to a LANG formatted str

    :param obj: _description_
    :type obj: Union[Lang, dict]
    :return: _description_
    :rtype: str
    """
    return LANGEncoder(**kw).encode(obj)


def load(fp: TextIOWrapper, **kw) -> Lang:
    """
    Deserialize fp (a `.read()`-supporting file-like object containing a LANG document) to a Python object

    :param fp: _description_
    :type fp: Union[str, bytes]
    :return: _description_
    :rtype: Lang
    """
    return loads(fp.read(), **kw)


def loads(s: str, **kw) -> Lang:
    """
    Deserialize s (a str or bytes instance containing a LANG document) to a Python object

    :param s: _description_
    :type s: Union[str, bytes, bytearray]
    :raises TypeError: _description_
    :return: _description_
    :rtype: Lang
    """
    if not isinstance(s, (str, bytes, bytearray)):
        raise TypeError(
            f"The LANG object must be str, bytes or bytearray, not {s.__class__.__name__}"
        )
    result = LANGDecoder(**kw).decode(s)
    global __root__
    __root__ = result
    return result


def open(fp: str, mode: str = "r") -> Lang:
    return Lang.open(fp, mode)
