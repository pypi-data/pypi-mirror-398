from typing import Dict, Generator
from xml.etree import ElementTree as ET

from .base import Translator
from .html_translator import HtmlToJsonTranslator, HTMLTranslator
from .json_translator import JSONImageInfoTranslator, JSONTranslator

"""
Translator は インターネット出願ソフトのXMLを特定の形式に変換するための基底クラスです。
変換元は、複数のXMLをマージしたものを想定している。
namespace, doctype がマージしたxmlに含まれるていれば
xsl が決まり、Translator に与えられる。
xsl は マージしたxmlの namespace, doctype だけを対象とする必要はなく、
全体を参照してもよい。
"""

translator_config = [
    ### A163 日本語特許出願関連
    # {
    #    ### 願書のhtml
    #    "namespace": "http://www.jpo.go.jp",
    #    "doctype": "pat-app-doc",
    #    "xsl": "html/pat-appd.xsl",
    #    "translated_doctype": "application-for-printing",
    #    "translator": HTMLTranslator,
    # },
    # {
    #    ### 明細書のhtml
    #    "namespace": "",
    #    "doctype": "application-body",
    #    "xsl": "html/application-body.xsl",
    #    "translated_doctype": "description-for-printing",
    #    "translator": HTMLTranslator,
    # },
    {
        ### 願書 テキストブロック SSG用
        "namespace": "http://www.jpo.go.jp",
        "doctype": "pat-app-doc",
        "xsl": "text-blocks/pat-appd.xsl",
        "extra_args": {
            "force_list": ["blocks", "figure"],
        },
        "translated_doctype": "pat-appd-text-blocks",
        "translator": JSONTranslator,
    },
    {
        ### 明細書 テキストブロック SSG用
        "namespace": "",
        "doctype": "application-body",
        "xsl": "text-blocks/application-body.xsl",
        "extra_args": {
            "force_list": ["blocks", "figure"],
        },
        "translated_doctype": "application-body-text-blocks",
        "translator": JSONTranslator,
    },
    {
        ### 願書のフルテキスト. 検索用
        "namespace": "http://www.jpo.go.jp",
        "doctype": "pat-app-doc",
        "xsl": "html/pat-appd.xsl",
        "extra_args": {
            "json_key": "ApplicationFullText",
        },
        "translated_doctype": "pat-appd-full-text",
        "translator": HtmlToJsonTranslator,
    },
    {
        ### 願書の特定項目テキスト. 検索用
        "namespace": "http://www.jpo.go.jp",
        "doctype": "pat-app-doc",
        "xsl": "xml/pat-appd.xsl",
        "extra_args": {
            "force_list": ["Inventors", "Applicants", "Agents"],
        },
        "translated_doctype": "pat-appd-text",
        "translator": JSONTranslator,
    },
    {
        ### 書誌情報の各項目のテキスト. 検索用
        "namespace": "",
        "doctype": "procedure-params",
        "xsl": "xml/bibliographic.xsl",
        "extra_args": {"force_list": None},
        "translated_doctype": "bibliographic-text",
        "translator": JSONTranslator,
    },
    {
        ### 明細書の各項目のテキスト. 検索用
        "namespace": "",
        "doctype": "application-body",
        "xsl": "xml/application-body.xsl",
        "extra_args": {"force_list": None},
        "translated_doctype": "application-body-text",
        "translator": JSONTranslator,
    },
    {
        ### 画像情報
        "namespace": "",
        "doctype": "images",
        "xsl": "xml/images.xsl",
        "extra_args": {
            "force_list": [],
        },
        "translated_doctype": "images-info",
        "translator": JSONImageInfoTranslator,
    },
]


def get_translators(src_xml_path: str) -> Generator[Translator, None, None]:
    src_xml_string = open(src_xml_path, "r").read()
    root = ET.fromstring(src_xml_string)
    for config in translator_config:
        if config["namespace"]:
            search_tag = f"{{{config['namespace']}}}{config['doctype']}"
        else:
            search_tag = config["doctype"]
        if root.find(search_tag) is not None:
            translator_cls = config["translator"]
            args = {
                "xsl_path": config["xsl"],
                "xml_string": src_xml_string,
                "translated_doctype": config["translated_doctype"],
            }

            if "extra_args" in config:
                args = {**args, **config["extra_args"]}

            translator = translator_cls(**args)

            yield translator


### 辞書だけど、オブジェクトにしたほうが良いかも
### trobj の extension kind ns を参照してファイル名を呼び出し側のヒントに使えるように。
### trobj.translate(document_path, params={...})
xsl_config2: Dict[str, str] = {
    "{http://www.jpo.go.jp}foreign-language-body": [
        {
            "xsl": "html/foreign-language-body.xsl",
            "extension": "html",
            "kind": "for-printing",
            "ns": "http://www.jpo.go.jp",
        },
        {  # each field's text
            "xsl": "xml/foreign-language-body.xsl",
            "extension": "json",
            "kind": "fields-text",
            "ns": None,
        },
        {  # images info
            "xsl": "xml/images.xsl",
            "extension": "json",
            "kind": "images-info",
            "ns": None,
        },
    ],
    "{http://www.jpo.go.jp}pat-rspns": [
        {
            "xsl": "html/pat-rspn.xsl",
            "extension": "html",
            "kind": "for-printing",
            "ns": "http://www.jpo.go.jp",
        },
        {
            "xsl": "xml/pat-rspn.xsl",
            "extension": "json",
            "kind": "fields-text",
            "ns": "http://www.jpo.go.jp",
        },
        {  # each fields's text as blocks
            "xsl": "xml/text-blocks-aaaaa.xsl",
            "extension": "json",
            "kind": "text-blocks",
            "ns": None,
        },
    ],
    "{http://www.jpo.go.jp}pat-amnd": [
        {
            "xsl": "html/pat-amnd.xsl",
            "extension": "html",
            "kind": "for-printing",
            "ns": "http://www.jpo.go.jp",
        },
        {
            "xsl": "xml/pat-amnd.xsl",
            "extension": "json",
            "kind": "fields-text",
            "ns": "http://www.jpo.go.jp",
        },
        {  # each fields's text as blocks
            "xsl": "xml/text-blocks-aaaaa.xsl",
            "extension": "json",
            "kind": "text-blocks",
            "ns": None,
        },
    ],
    "{http://www.jpo.go.jp}cpy-notice-pat-exam": [
        {
            "xsl": "html/cpy-ntc-pat-e.xsl",
            "extension": "html",
            "kind": "for-printing",
            "ns": "http://www.jpo.go.jp",
        },
        {
            "xsl": "xml/cpy-ntc-pat-e.xsl",
            "extension": "json",
            "kind": "fields-text",
            "ns": "http://www.jpo.go.jp",
        },
        {  # each fields's text as blocks
            "xsl": "xml/text-blocks-aaaaa.xsl",
            "extension": "json",
            "kind": "text-blocks",
            "ns": None,
        },
    ],
    "{http://www.jpo.go.jp}cpy-notice-pat-exam-rn": [
        {
            "xsl": "html/cpy-ntc-pat-e-rn.xsl",
            "extension": "html",
            "kind": "for-printing",
            "ns": "http://www.jpo.go.jp",
        },
        {
            "xsl": "xml/cpy-ntc-pat-e-rn.xsl",
            "extension": "json",
            "kind": "fields-text",
            "ns": "http://www.jpo.go.jp",
        },
        {  # each fields's text as blocks
            "xsl": "xml/text-blocks-aaaaa.xsl",
            "extension": "json",
            "kind": "text-blocks",
            "ns": None,
        },
    ],
}
