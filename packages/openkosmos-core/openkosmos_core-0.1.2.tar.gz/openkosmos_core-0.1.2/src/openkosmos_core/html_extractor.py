from types import SimpleNamespace as T

import yaml
from parsel import Selector


class HtmlExtractor:

    def __init__(self, template):
        self.__template = template

    def __extract(self, current, parent_bean, beans, kid):
        node = current.xpath(kid["xpath"])
        name = kid.get("name")
        bean_name = kid.get("bean")
        kids = kid.get("kids")
        p_bean = parent_bean

        if name is not None:
            if parent_bean is not None:
                parent_bean[name] = node.get()
            elif name is not None:
                beans.get(bean_name)[name] = node.get()

        if kids is not None:
            if bean_name is not None and name is None:
                for n in node:
                    p_bean = dict()
                    for k in kid["kids"]:
                        self.__extract(n, p_bean, beans, k)
                    beans.get(bean_name).append(p_bean)
            else:
                for k in kid["kids"]:
                    self.__extract(node, p_bean, beans, k)

    def __create_extractor(self, content):
        selector = Selector(text=content)
        beans = dict()
        for b in self.__template["beans"]:
            if b.get("type") == "list":
                beans[b["name"]] = []
            else:
                beans[b["name"]] = dict()
        return T(selector=selector, beans=beans)

    def extract(self, content):
        extractor = self.__create_extractor(content)
        for kid in self.__template["template"]:
            self.__extract(extractor.selector, None, extractor.beans, kid)
        return extractor.beans

    @classmethod
    def test(cls, templatefile, contentfile):
        with open(templatefile) as tf:
            template = yaml.load(tf, Loader=yaml.FullLoader)
            with open(contentfile, "r", encoding="utf8") as ff:
                return HtmlExtractor(template).extract(str(ff.read()))
