import re
import __main__
from dataclasses import dataclass
import pkgutil
from io import TextIOWrapper
import urllib.request
import ssl
import json
from pathlib import Path
from typing import Literal, Callable, ClassVar, TypedDict
from collections import Counter


class Env(TypedDict):
    dev__user__admin__login: str
    dev__user__admin__password: str
    dev__user__regmn__login: str
    dev__user__regmn__password: str
    dev__app__domain: str
    dev__app__isso_url: str
    dev__app__client_id: str
    dev__app__client_secret: str


class Paths(TypedDict):
    path: str
    autotest: str
    tests: str
    params: str
    swagger: str
    swagger_endpoints: str
    swagger_schemas: str
    browser: str
    browser_pages: str
    browser_components: str
    params_api: str
    params_ui: str
    tests_test_api: str
    tests_test_ui: str


class Page(TypedDict):
    name: str
    url: str
    components: list[str]


@dataclass
class Config:
    """
    - UI: bool True if you need to generate UI tests else False
    - API: ClassVar[str] = path to API tests in JSON format
    - PATHS: ClassVar[Paths] It is recommended not to change the file and directory generation paths
    - ENV: ClassVar[Env] The environment parameters on the basis of which tests are carried out, as an example, the parameters for authorization through isso with two different users are left. For the script, it is important that the key name between logical blocks contains two underscores
    - PAGES: ClassVar[list[Page]] Description of pages, consists of the page name, URL, and the component being used. A template will be used as an example
    """
    UI: bool = False
    API: ClassVar[str] = ""
    PATHS: ClassVar[Paths] = {
        "path": f'{Path(__main__.__file__).parent}/'.replace("\\", "/"),
        "autotest": "autotest/",
        "swagger": "autotest/swagger/",
        "swagger_endpoints": "autotest/swagger/endpoints/",
        "swagger_schemas": "autotest/swagger/schemas/",
        "browser": "autotest/browser/",
        "browser_pages": "autotest/browser/pages/",
        "browser_components": "autotest/browser/components/",
        "params": "autotest/params/",
        "params_api": "autotest/params/api/",
        "params_ui": "autotest/params/ui/",
        "tests": "autotest/tests/",
        "tests_test_api": "autotest/tests/test_api/",
        "tests_test_ui": "autotest/tests/test_ui/"
    }
    ENV: ClassVar[Env] = {
        "dev__user__admin__login": "",
        "dev__user__admin__password": "",
        "dev__user__regmn__login": "",
        "dev__user__regmn__password": "",
        "dev__app__domain": "",
        "dev__app__isso_url": "",
        "dev__app__client_id": "",
        "dev__app__client_secret": ""
    }
    PAGES: ClassVar[list[Page]] = [
        {
            "name": "authorization_page",
            "url": "",
            "components": [
                "authorization_page_modal_isso",
                "authorization_page_modal_auth",
            ]
        },
        {
            "name": "main_page",
            "url": "",
            "components": [
                "header",
                "footer",
                "main_page_main_info",
                "main_page_tools",
                "main_page_main_news",
                "main_page_useful_info",
                "main_page_offers",
            ]
        },
        {
            "name": "buildings_page",
            "url": "buildings/",
            "components": [
                "header",
                "footer",
                "buttons",
                "filter_header",
                "filter_body",
                "workspace_header",
                "workspace_table_tools",
                "workspace_table_header",
                "workspace_table_body",
                "workspace_table_footer",
                "layers",
                "map"
            ]
        },
        {
            "name": "building_card_page",
            "url": "buildings/{id}",
            "components": [
                "header",
                "footer",
                "buttons",
                "workspace_header",
                "workspace_header_statistics",
                "workspace_header_navigation",
                "building_card_page_workspace_housing",
                "building_card_page_workspace_complex",
                "layers",
                "comments",
                "map"
            ]
        },
        {
            "name": "projects_page",
            "url": "projects/",
            "components": [
                "header",
                "footer",
                "buttons",
                "filter_header",
                "filter_body",
                "workspace_header",
                "workspace_header_tools",
                "workspace_table_tools",
                "workspace_table_header",
                "workspace_table_body",
                "modal_create_edit_project",
                "layers",
                "map"
            ]
        },
        {
            "name": "project_card_page",
            "url": "project/{id}",
            "components": [
                "header",
                "footer",
                "buttons",
                "filter_header",
                "filter_body",
                "workspace_header",
                "workspace_header_tools",
                "workspace_header_statistics",
                "workspace_table_tools",
                "workspace_table_header",
                "workspace_table_body",
                "modal_create_edit_project",
                "layers",
                "comments",
                "map"
            ]
        },
        {
            "name": "polygon_create_edit_card_page",
            "url": "create/polygon/{id}",
            "components": [
                "header",
                "footer",
                "buttons",
                "workspace_header",
                "workspace_body",
                "workspace_footer",
                "layers",
                "comments",
                "map"
            ]
        },
        {
            "name": "polygons_page",
            "url": "polygons/",
            "components": [
                "header",
                "footer",
                "buttons",
                "filter_header",
                "filter_body",
                "workspace_header",
                "workspace_table_tools",
                "workspace_table_header",
                "workspace_table_body",
                "workspace_table_footer",
                "layers",
                "map"
            ]
        },
        {
            "name": "polygon_card_page",
            "url": "polygon/{id}",
            "components": [
                "header",
                "footer",
                "buttons",
                "workspace_header",
                "workspace_header_statistics",
                "workspace_header_navigation",
                "polygon_card_page_workspace_basic",
                "polygon_card_page_workspace_technical_specifications",
                "polygon_card_page_workspace_geodata",
                "layers",
                "map"
            ]
        },
        {
            "name": "sites_page",
            "url": "sites/",
            "components": [
                "header",
                "footer",
                "buttons",
                "filter_header",
                "filter_body",
                "workspace_header",
                "workspace_table_tools",
                "workspace_table_header",
                "workspace_table_body",
                "workspace_table_footer",
                "layers",
                "map"
            ]
        },
        {
            "name": "site_card_page",
            "url": "site/{id}",
            "components": [
                "header",
                "footer",
                "buttons",
                "workspace_header",
                "workspace_header_navigation",
                "site_card_page_workspace_basic",
                "site_card_page_workspace_tb_section",
                "site_card_page_workspace_bm_section",
                "site_card_page_workspace_site_kpi",
                "site_card_page_workspace_bigdata_section",
                "layers",
                "comments",
                "map"
            ]
        },
        {
            "name": "houses_page",
            "url": "houses/",
            "components": [
                "header",
                "footer",
                "buttons",
                "filter_header",
                "filter_body",
                "layers",
                "map",
                "settings",
                "download"
            ]
        },
        {
            "name": "house_card_page",
            "url": "houses/{id}",
            "components": [
                "header",
                "footer",
                "buttons",
                "filter_header",
                "filter_body",
                "layers",
                "map",
                "comments",
                "settings",
                "download",
                "workspace_header",
                "workspace_header_navigation",
                "house_card_page_workspace_house",
                "house_card_page_workspace_complex",
                "house_card_page_workspace_geodata",
            ]
        }
    ]


@dataclass
class Parameter:
    param: Literal["path", "query"] = None
    alias: str = None
    type: str = None

    def __post_init__(self):
        self.param = self.set_param(self.param)
        self.alias = self.set_alias(self.alias)
        self.name = self.set_name(self.alias)
        self.type = self.set_type(self.type)

    def set_param(self, attr: dict):
        return attr["in"]
    
    def set_alias(self, attr: dict):
        return attr["name"]
    
    def set_name(self, attr: str):
        return attr.replace(".", "_")
    
    def set_type(self, attr: dict):
        return Text.to_python_type(attr["schema"]["type"])


@dataclass
class Props:
    name: str = None
    type: str = None
    schema: str = None

    def __post_init__(self):
        self.schema = self.set_schema(self.schema)
        self.type = self.set_type(self.type)

    def set_schema(self, attr: dict):
        if (schema := Text.find(attr, '$ref')) != None:
            return schema.split('/')[-1]

    def set_type(self, attr: dict):
        return ' | '.join(
            [Text.to_python_type(_.get("type")) if _.get("type") != None and _.get("items") == None else
            _.get("$ref").split('/')[-1] if _.get("type") == None and _.get("$ref") != None else 
            f'{Text.to_python_type(_.get("type"))}[{Text.to_python_type(_.get("items").get("type"))}]' if _.get("type") != None and _.get("items").get("type") != None else
            f'{Text.to_python_type(_.get("type"))}[{_.get("items").get("$ref").split('/')[-1]}]' if _.get("type") != None and _.get("items").get("$ref") != None else None for _ in attr.get("oneOf", [attr])] + 
            ['None' for _ in attr.get("oneOf", [attr]) if _.get("nullable") == True]
        )
    

@dataclass
class Schema:
    status: str = None
    name: str = None
    body_type: Literal["request", "response"] = None
    content_type: str = None
    properties: list[Props] = None

    def __post_init__(self):
        self.content_type = self.set_content_type(self.content_type)
        self.name = self.set_name(self.name)

    def set_name(self, attr: dict):
        if isinstance(attr, str):
            return attr
        return name.split('/')[-1] if (name := Text.find(attr, '$ref')) != None else None
    
    def set_content_type(self, attr: dict):
        if self.content_type != None:
            return ''.join(content_type.keys()) if (content_type := Text.find(attr, 'content')) != None else None


@dataclass   
class Method:
    name: str = None
    tag: str = None
    schemas: list[Schema] = None
    parameters: list[Parameter] = None

    def __post_init__(self):
        self.tag = self.set_tag(self.tag)

    def set_tag(self, attr: dict):
        return attr["tags"][0]


@dataclass
class Endpoint:
    endpoint: str = None
    name: str = None
    methods: list[Method] = None

    def __post_init__(self):
        self.name = self.set_name(self.name)

    def set_name(self, attr: str):
        return attr.replace("/api/v1/", "").replace("/", "_").replace("{", "").replace("}", "")
              

class Parsing:

    def __init__(self):
        self.__context = ssl.create_default_context()
        self.__context.check_hostname = False
        self.__context.verify_mode = ssl.CERT_NONE
        self.__open_api = json.loads(urllib.request.urlopen(url=urllib.request.Request(Config.API), context=self.__context).read().decode('UTF-8'))

    @property
    def environments(self) -> dict:
        def add_dict_env(env_dict: dict, env_list: list, env_str: str):
            """
            Создать список с переменными окружения 
                - env_dict: словарь для добавления новых переменных
                - env_list: список ключей для создания вложенности
                - env_str: имя переменной окружения
            """
            if len(env_list) != 1:
                env_dict.setdefault(env_list[0], {})
                add_dict_env(env_dict[env_list[0]], env_list[1:], env_str)
            else:
                env_dict.setdefault(env_list[0], env_str)
        if self.__dict__.get('_environments') == None:
            self._environments = {}
            for name_env in Config.ENV:
                add_dict_env(self._environments, name_env.split('__'), name_env.upper())           
        return self._environments
  
    @property
    def endpoints(self) -> list[Endpoint]:
        # print(self.__open_api)
        if self.__dict__.get('_endpoints') == None:
            self._endpoints = [
                Endpoint(
                    endpoint=endpoint,
                    name=endpoint,
                    methods=[
                        Method(
                            name=method,
                            tag=method_values,
                            parameters=[
                                Parameter(
                                    alias=parameter,
                                    param=parameter,
                                    type=parameter
                                ) for parameter in method_values.get("parameters")
                            ] if method_values.get("parameters") != None else None,
                            schemas=[__ for _ in [[
                                Schema(
                                    body_type="response",
                                    content_type=method_values.get("responses")[status],
                                    status=status,
                                    name=method_values.get("responses")[status],
                                    properties=[
                                        Props(
                                            name=props,
                                            type=props_values,
                                            schema=props_values
                                        ) for props, props_values in Text.find(method_values.get("responses")[status], "properties").items()
                                    ] if Text.find(method_values.get("responses")[status], '$ref') == None and Text.find(method_values.get("responses")[status], "properties") != None else None
                                ) for status in method_values.get("responses")
                            ] if method_values.get("responses") != None else []] + [[
                                Schema(
                                    body_type="request",
                                    content_type=method_values.get("requestBody"),
                                    name=method_values.get("requestBody"),
                                    properties=[
                                        Props(
                                            name=props,
                                            type=props_values,
                                            schema=props_values
                                        ) for props, props_values in Text.find(method_values.get("requestBody"), "properties").items()
                                    ] if Text.find(method_values.get("requestBody"), '$ref') == None and Text.find(method_values.get("requestBody"), "properties") != None else None
                                )
                            ] if method_values.get("requestBody") != None else []] for __ in _]
                        ) for method, method_values in endpoint_values.items()]
                ) for endpoint, endpoint_values in self.__open_api["paths"].items()]
        return self._endpoints

    @property
    def schemas(self) -> list[Schema]:
        if self.__dict__.get('_schemas') == None:
            self._schemas = [
                Schema(
                    name=schema,
                    properties=[
                        Props(
                            name=props,
                            type=props_values,
                            schema=props_values
                        ) for props, props_values in schema_values.get("properties").items()
                    ] if schema_values.get("properties") != None else None
                ) for schema, schema_values in self.__open_api["components"]["schemas"].items()]
        return self._schemas

    @property
    def tags(self) -> list:
        if self.__dict__.get('_tags') == None:
            self._tags = list(set([__.tag for _ in self.endpoints for __ in _.methods]))
        return self._tags
    

class Text:

    @classmethod
    def to_comment_line(cls, text: str) -> str:
        return f'# {"=" * int((79 - len(text)) / 2)} {text} {"=" * int((79 - len(text)) / 2)}\n'

    @classmethod
    def to_python_type(cls, text: str) -> str:
        return {
            "string": "str",
            "number": "float",
            "array": "list",
            "integer": "int",
            "boolean": "bool",
            "object": "dict"
        }.get(text)
    
    @classmethod
    def find(cls, data: dict, text: str) -> str | dict | None:
        for _ in data:
            if _ == text:
                return data[_]
            if isinstance(data[_], dict):
                if (__ := cls.find(data[_], text)) != None:
                    return __

    @classmethod
    def to_snake_case(cls, text: str) -> str:
        """Преобразует текст в snake_case"""
        text = re.sub(r'[\s-]+', '_', text)  # Заменяем пробелы и дефисы на подчеркивания
        text = re.sub(r'([a-z])([A-Z])', r'\1_\2', text)  # Вставляем подчеркивания между строчными и прописными буквами
        text = re.sub(r'_+', '_', text)  # Заменяем несколько подчеркиваний на одно
        return text.strip().lower()  # Приводим к нижнему регистру и убираем пробелы по краям

    @classmethod
    def to_camel_case(cls, text: str) -> str:
        """Преобразует текст в camelCase"""
        text = re.sub(r'[\s\-_]+', ' ', text)  # Заменяем пробелы, дефисы, подчеркивания на пробелы  
        text = text.strip().split()  # Разбиваем на слова   
        text = ''.join([_.capitalize() for _ in text])  # Объединяем слова с заглавной буквой
        return text


class Matrix:

    @classmethod
    def packing(cls, lines: str):
        return [[_.splitlines(keepends=True) for _ in re.split(r'(?<=\n)\n(?=[^\n])', line)] for line in re.split(r'(?<=\n)\n{2}(?=[^\n])', lines)]

    @classmethod
    def unpacking(cls, lines: list, types: Literal["str", "list"] = "list", filters: Callable = lambda _: _):
        flag_1, flag_2, last = True, True, ''
        def auto_replace(line: str):
            nonlocal flag_1, flag_2, last
            while line.count('\n') > 0:
                line = line.replace('\n', '')
            if any([
                line[:1] == '#' and flag_1,
                line[:5] == '    @' and last[:5] != '    @' and flag_1,
                line[:10] == '    class ' and flag_1,
                line[:8] == '    def ' and last[:5] != '    @' and flag_1,
                line[:14] == '    async def ' and last[:5] != '    @' and flag_1,
                line[:10] == '    PARAM_' and flag_1
            ]):
                last, flag_1, flag_2 = line, False, True
                return '\n' + line + '\n'
            elif any([
                line[:1] == '@' and last[:1] != '@' and flag_2,
                line[:6] == 'class ' and last[:1] != '@' and flag_2,
                line[:4] == 'def ' and flag_2,
                line[:10] == 'async def ' and flag_2
            ]):
                last, flag_1, flag_2 = line, True, False
                return '\n\n' + line + '\n'
            else:
                last, flag_1, flag_2 = line, True, True
                return line + '\n'
        def auto_unpacking(lines: list[str]):
            __ = []
            for line in lines:
                if isinstance(line, list):
                    __.extend(auto_unpacking(line))
                else:
                    if line.strip() and filters(line): 
                        __.append(auto_replace(line)) 
            return __
        if types == "list":
            return auto_unpacking(lines)
        elif types == "str":
            return ''.join(auto_unpacking(lines)).strip() + '\n'

    @classmethod
    def find_point(cls, lines: list, key: str, point: list = None):
        if point == None:
            point = []
        if isinstance(lines, list):
            for _, line in enumerate(lines):
                if (__ := cls.find_point(line, key, point + [_])) is not None:
                    return __
        elif key in lines:
            return point


class File:

    LIBS = [name for path, name, _ in pkgutil.iter_modules() if 'Python3'in str(path)]

    def __init__(self, file: TextIOWrapper):
        self.__file = file

    @property
    def depends(self) -> list:
        if self.__dict__.get('_depends') == None:
            self._depends = []
        return self.__dict__.get('_depends')
    
    @depends.setter
    def depends(self, lines: list[str]):
        def check(line: str):
            return all([
                line not in ['# Стандартная библиотека\n', '# Установленные библиотеки\n', '# Локальные импорты\n'],
                line[0] != '@',
                line[:4] != 'def ',
                line[:5] != 'from ',
                line[:6] != 'class ',
                line[:6] != 'async ',
                line[:7] != 'import ',
                line[:5] != '     ',
                line[:5] != '    @',
                line[:8] != '    def ',
                line[:10] != '    class ',
                line[:10] != '    async ',
                line[:11] != '    return ',
            ])
        lines = Matrix.packing(Matrix.unpacking(lines, types="str"))
        if (point := Matrix.find_point(lines, 'class ')) != None:
            lines = lines[:point[0]]
        elif (point := Matrix.find_point(lines, 'def ')) != None:
            lines = lines[:point[0]]
        self._depends = Matrix.packing(Matrix.unpacking(lines, types="str", filters=check))
            
    @property
    def imports(self) -> list:
        if self.__dict__.get('_imports') == None:
            if (point := Matrix.find_point(self.lines, 'import')) != None:
                self._imports = [self.lines[point[0]]]
        return [[
            sorted(list(filter(lambda _: 'from' not in _, ___))) +
            sorted(list(filter(lambda _: 'from' in _, ___)))
            for __ in self.__dict__.get('_imports', []) for ___ in __
        ]]

    @imports.setter
    def imports(self, lines: list[str]):
        if (lines := list(filter(lambda _: 'import ' in _ and _[0] != ' ' in _, Matrix.unpacking(self.imports + lines)))) == []:
            self._imports = lines
        else:
            __ = [
                ['# Стандартная библиотека\n'],
                ['# Установленные библиотеки\n'],
                ['# Локальные импорты\n']
            ]
            for _ in list(set(lines)):
                if _.split()[1] in self.LIBS:
                    __[0].append(_)
                elif Config.PATHS['autotest'][:-1] in _:
                    __[2].append(_)
                elif '#' not in _:
                    __[1].append(_)
            self._imports = [[_ for _ in __ if len(_) > 1]]

    @property
    def classes(self) -> list:
        if self.__dict__.get('_classes') == None:
            if (point := Matrix.find_point(self.lines, 'class ')) != None:
                self._classes = self.lines[point[0]:]
        return [[
            _[0],
            *sorted(list(filter(lambda __: Matrix.find_point(__, ' class') != None, _[1:])), 
                key=lambda __: re.findall(r'\s(\w+)[^\w\s]', __[Matrix.find_point(__, 'class')[0]])[0]),
            *sorted(list(filter(lambda __: Matrix.find_point(__, ' def') != None, _[1:])),
                key=lambda __: re.findall(r'\s(\w+)[^\w\s]', __[Matrix.find_point(__, 'def')[0]])[0]),
            *sorted(list(filter(lambda __: Matrix.find_point(__, ' PARAM_') != None, _[1:])),
                key=lambda __: re.findall(r'\s(\w+)[^\w\s]', __[Matrix.find_point(__, 'PARAM_')[0]])[0])
        ] for _ in self.__dict__.get('_classes', [])]

    @classes.setter
    def classes(self, lines: list):
        if Matrix.find_point(lines, 'class ') != None:
            for lines in Matrix.packing(Matrix.unpacking(lines, types="str"))[Matrix.find_point(Matrix.packing(Matrix.unpacking(lines, types="str")), 'class ')[0]:]:
                name = re.findall(r'\s(\w+)[^\w\s]', ''.join([_ for _ in lines[0] if 'class' in _]))[0]
                point = Matrix.find_point([[_[0]] for _ in self.classes], name)
                if point == None:
                    self._classes = self.__dict__.get('_classes', []) + [lines]
                else:
                    for line in lines[1:]:
                        _name: str = re.findall(r'\s(\w+)[^\w\s]', ''.join(line))[0]
                        _point = Matrix.find_point(self._classes[point[0]], _name)
                        if _point == None:
                            self._classes[point[0]] += [line]
                        elif (not _name.islower() and not _name.isupper()) or (_name == '__init__' and Matrix.find_point(self._classes[point[0]], '__init__(self, client:') != None):
                            self._classes[point[0]][_point[0]] = line

    @property
    def funcs(self) -> list:
        if self.__dict__.get('_funcs') == None:
            if Matrix.find_point(self.lines, 'class ') == None:
                point = [point[0] for point in [Matrix.find_point(self.lines, 'def '), Matrix.find_point(self.lines, 'async def ')] if point != None]
                if len(point) != 0:
                    self._funcs = self.lines[min(point):]
        return self.__dict__.get('_funcs', [])

    @funcs.setter
    def funcs(self, lines: list):
        if Matrix.find_point(lines, 'class ') == None:
            lines = Matrix.packing(Matrix.unpacking(lines, types='str'))
            point = [point[0] for point in [Matrix.find_point(lines, 'def '), Matrix.find_point(lines, 'async def ')] if point != None]
            if len(point) != 0:
                self._funcs = lines[min(point):]

    @property
    def lines(self) -> list:
        if self.__dict__.get('_lines') == None:
            self.__file.seek(0)
            if (lines := self.__file.readlines()) != []:
                self._lines = Matrix.packing(Matrix.unpacking(lines, types="str"))
        return self.__dict__.get('_lines', [])

    @lines.setter
    def lines(self, lines: list):
        self.imports = lines
        self.depends = lines
        self.classes = lines
        self.funcs = lines
        self.__file.truncate(0)
        self.__file.write('\n\n'.join([
            line for line in
            [
                Matrix.unpacking(self.imports, types="str"),
                Matrix.unpacking(self.depends, types="str"),
                Matrix.unpacking(self.classes, types="str"),
                Matrix.unpacking(self.funcs, types="str")
            ] if line != '\n'
        ]))


class Creator:

    PARSING = Parsing()

    def __init__(self, path: str, mode: Literal["+a", "+w"], name: Literal["blank_client", "blank_page", "endpoints", "environments", "gitignore", "schemas", "pytest", "pages", "param_env", "params_api", "params_ui", "readme", "requirements", "conftest_api", "conftest_ui", "tests_api", "tests_ui"]):
        self.__path = path
        self.__mode = mode
        self.__name = name

    def __call__(self, func):
        def wrapper(wrapper_self, *args, **kwds):
            LINES = {
                "endpoints": [{"lines": lines, "file_name": f'{Text.to_snake_case(file_name)}_endpoints.py', "file_path": ""} for lines, file_name in zip([list(filter(lambda _: len([__ for __ in _.methods if __.tag == tag]) != 0, Creator.PARSING.endpoints)) for tag in Creator.PARSING.tags], Creator.PARSING.tags)],
                "blank_client": [{"lines": {"tags": Creator.PARSING.tags, "environments": Creator.PARSING.environments}, "file_name": "blank_client.py", "file_path": ""}],
                "blank_page": [{"lines": {"pages": Config.PAGES, "environments": Creator.PARSING.environments}, "file_name": "blank_page.py", "file_path": ""}],
                "components": [{"lines": line, "file_name": f'component_{line.lower()}.py', "file_path": ""} for line, count in Counter([__ for _ in Config.PAGES for __ in _["components"]]).items() if count > 1],
                "conftest": [{"lines": {"environments": Creator.PARSING.environments}, "file_name": "conftest.py", "file_path": ""}],
                "conftest_ui": [{"lines": {"environments": Creator.PARSING.environments}, "file_name": "conftest.py", "file_path": ""}],
                "environments": [{"lines": {"environments": environment, "file_name": file_name}, "file_name": file_name, "file_path": ""} for environment, file_name in [(Config.ENV, name) for name in [".env", ".env.example"]]],
                "gitignore": [{"lines": [], "file_name": ".gitignore", "file_path": ""}],
                "readme": [{"lines": [], "file_name": "README.md", "file_path": ""}],
                "pages": [{"lines": {"page": line, "components": [___ for ___, count in Counter([__ for _ in Config.PAGES for __ in _["components"]]).items() if count > 1]}, "file_name": f'{line["name"].lower()}.py', "file_path": ""} for line in Config.PAGES],
                "param_env": [{"lines": {"environments": Creator.PARSING.environments}, "file_name": "param_env.py", "file_path": ""}],
                "params_api": [{"lines": lines, "file_name": f'param_{Text.to_snake_case(file_name)}_api.py', "file_path": ""} for lines, file_name in zip([list(filter(lambda _: len([__ for __ in _.methods if __.tag == tag]) != 0, Creator.PARSING.endpoints)) for tag in Creator.PARSING.tags], Creator.PARSING.tags)],
                "params_ui": [{"lines": lines, "file_name": f'param_{Text.to_snake_case(lines["name"])}.py', "file_path": ""} for lines in Config.PAGES],
                "pytest": [{"lines": {"api": Creator.PARSING.tags, "ui": Config.PAGES}, "file_name": "pytest.ini", "file_path": ""}],
                "requirements": [{"lines": [], "file_name": "requirements.txt", "file_path": ""}],
                "schemas": [{"lines": schema, "file_name": f'{Text.to_snake_case(schema.name)}.py', "file_path": ""} for schema in Creator.PARSING.schemas],
                "tests_api": [{"lines": line, "file_name": f'test_{line.name}.py', "file_path": f'test_{Text.to_snake_case(line.methods[0].tag)}/'} for line in Creator.PARSING.endpoints],
                "tests_ui": [{"lines": {"component": component, "name": line["name"], "url": line["url"]}, "file_name": f'test_{Text.to_snake_case(line["name"] + '_' + component.replace(f'{line["name"]}_', ''))}.py', "file_path": f'test_{Text.to_snake_case(line["name"])}/'} for line in Config.PAGES for component in line["components"]]
            }
            for line in LINES[self.__name]:
                Path(f'{Config.PATHS["path"]}{self.__path}{line["file_path"]}').mkdir(exist_ok=True, parents=True)
                with open(f'{Config.PATHS["path"]}{self.__path}{line["file_path"]}{line["file_name"]}', self.__mode, encoding="UTF-8") as file:
                    file = File(file)
                    file.lines = func(wrapper_self, line["lines"], *args, **kwds)
        return wrapper


class Create:

    @classmethod
    @Creator(path=Config.PATHS["tests"], mode="+w", name="conftest")
    def conftest_api(cls, lines: Literal["environments"]):
        return [
            'import pytest',
            'from httpx import AsyncClient',
            'from dotenv import load_dotenv',
            f'from {Config.PATHS["swagger"].replace("/", ".")}blank_client import BlankClient',
            'load_dotenv()',
            '@pytest.fixture(scope="session")',
            'def environments():',
            f'    return {lines["environments"]}',
            '@pytest.fixture(scope="session", autouse=True)',
            'async def token(environments):',
            '    async with AsyncClient(verify=False) as client:',
            '        client = BlankClient(client)',
            '        await client.create_token(environments)',
            '@pytest.fixture(scope="function")',
            'async def client():',
            '    async with AsyncClient(verify=False) as client:',
            '        client = BlankClient(client)',
            '        yield client'
        ]
    
    # устарел
    @classmethod
    @Creator(path=Config.PATHS["tests_test_ui"], mode="+w", name="conftest_ui")
    def conftest_ui_old(cls, *args):
        return [
            'import pytest',
            'import allure',
            'import random',
            'import shutil',
            'import os',
            'from pathlib import Path',
            'from playwright.async_api import async_playwright, Browser, BrowserContext',
            f'from {Config.PATHS["browser"].replace("/", ".")}blank_page import BlankPage',
            f'from {Config.PATHS["swagger"].replace("/", ".")}blank_client import BlankClient',
            '@pytest.fixture(scope="session")',
            'async def browser():',
            '    async with async_playwright() as _:',
            '        browser = await _.chromium.launch(',
            '        args=[',
            '            \'--disable-gpu\',',
            '            \'--disable-dev-shm-usage\',',
            '            \'--disable-setuid-sandbox\',',
            '            \'--no-first-run\',',
            '            \'--no-sandbox\',',
            '            \'--no-zygote\',',
            '            \'--disable-web-security\',',
            '            \'--disable-features=VizDisplayCompositor\',',
            '            \'--disable-background-timer-throttling\',',
            '            \'--disable-renderer-backgrounding\',',
            '            \'--disable-backgrounding-occluded-windows\'',
            '        ],',
            '        # headless=False,',
            '        # slow_mo=500',
            '        )',
            '        yield browser',
            '        await browser.close()',
            '@pytest.fixture(scope="function")',
            'async def context(browser: Browser, request: pytest.FixtureRequest, environments):',
            '    contexts = {}',
            '    for stand in environments:',
            '        users = environments[stand]["user"]',
            '        app = environments[stand]["app"]',
            '        contexts.setdefault(stand, {}).setdefault(',
            '            \'unknown\',', 
            '            await browser.new_context(',
            '                viewport={\'width\': 1920, \'height\': 1080},',
            '                base_url=os.environ[app["domain"]],',
            '                record_video_dir=f\'{Path(__file__).parent.parent.parent}\\\\videos\\\\{request.node.name}//\',',
            '                ignore_https_errors=True,',
            '                java_script_enabled=True,',
            '                bypass_csp=True',
            '            )',
            '        )',
            '        for user in users:',
            '            if Path(f\'{Path(__file__).parent.parent.parent}\\\\auth\\\\{stand}_{user}.json\').exists():',
            '                contexts.setdefault(stand, {}).setdefault(',
            '                    user,',
            '                    await browser.new_context(',
            '                        viewport={\'width\': 1920, \'height\': 1080},',
            '                        base_url=os.environ[app["domain"]],',
            '                        storage_state=f\'{Path(__file__).parent.parent.parent}\\\\auth\\\\{stand}_{user}.json\',',
            '                        record_video_dir=f\'{Path(__file__).parent.parent.parent}\\\\videos\\\\{request.node.name}//\',',
            '                        ignore_https_errors=True,',
            '                        java_script_enabled=True,',
            '                        bypass_csp=True',
            '                    )',
            '                )',
            '    yield contexts',
            '    for stand in contexts:',
            '        for context in contexts[stand]:',
            '            await contexts[stand][context].close()',
            '@pytest.fixture(scope="function")',
            'async def page(context: BrowserContext, request: pytest.FixtureRequest):',
            '    page = BlankPage(context)',
            '    yield page',
            '    if \'auth\' in request.node.name:',
            '        await page._page.context.storage_state(',
            '            path=f\'{Path(__file__).parent.parent.parent}\\\\auth\\\\{page._domain}_{page._client}.json\'',
            '        )',
            '    await page.close()',
            '@pytest.hookimpl(tryfirst=True, hookwrapper=True)',
            'def pytest_runtest_makereport(item: pytest.Item):',
            '    """Получаем отчет о выполнении теста и удаляем видео успешных тестов"""',
            '    def replace(lines: list, params: dict):',
            '        _ = []',
            '        def recursion(line: str, params: dict):',
            '            for param in params:',
            '                if isinstance(params[param], dict):',
            '                    return recursion(line, params[param])',
            '                line = line.replace("{" + param + "}", str(params[param]))',
            '                return line',
            '            for line in lines:',
            '                line = recursion(line, params)[8:]',
            '                if "{" not in line and "}" not in line:',
            '                    _.append(line)',
            '            return _',
            '    outcome = yield',
            '    report = outcome.get_result()',
            '    if report.when == "setup":',
            '        doc = replace(item.function.__doc__.strip().split(\'\n\'), {"id": item.callspec.id} | item.callspec.params)',
            '        allure.dynamic.title(doc[0])',
            '        allure.dynamic.description("\n".join(doc[2:]))',
            '    if report.when == "call" and report.outcome == "passed":',
            '        shutil.rmtree(Path(f\'{Path(__file__).parent.parent.parent}\\\\videos\\\\{item.name}\\\\\'))'
        ]

    @classmethod
    @Creator(path=Config.PATHS["tests_test_ui"], mode="+w", name="conftest_ui")
    def conftest_ui(cls, lines: Literal["environments"]):
        return [
            'import pytest',
            'import allure',
            'import shutil',
            'import os',
            'from pathlib import Path',
            'from playwright.async_api import async_playwright, Browser',
            f'from {Config.PATHS["browser"].replace("/", ".")}blank_page import BlankPage',
            f'from {Config.PATHS["swagger"].replace("/", ".")}blank_client import BlankClient',
            '@pytest.fixture(scope="session")',
            'async def browser():',
            '    async with async_playwright() as _:',
            '        browser = await _.chromium.launch(',
            '            args=[',
            '                \'--disable-gpu\',',
            '                \'--disable-dev-shm-usage\',',
            '                \'--disable-setuid-sandbox\',',
            '                \'--no-first-run\',',
            '                \'--no-sandbox\',',
            '                \'--no-zygote\',',
            '                \'--disable-web-security\',',
            '                \'--disable-features=VizDisplayCompositor\',',
            '                \'--disable-background-timer-throttling\',',
            '                \'--disable-renderer-backgrounding\',',
            '                \'--disable-backgrounding-occluded-windows\'',
            '            ],',
            '            # headless=False,',
            '            # slow_mo=500',
            '        )',
            '        yield browser',
            '        await browser.close()',
            '@pytest.fixture(scope="function")',
            'async def page(browser: Browser, request: pytest.FixtureRequest, environments):',
            '    params = request.node.name.split(\'[\')[-1].replace(\']\', \'\').split(\'-\')',
            f'    domain, user = set(params) & {set(lines["environments"])}, set(params) & {set(lines["environments"][list(lines["environments"])[0]]["user"])}',
            '    domain = \'\'.join(domain) if len(domain) != 0 else \'dev\'',
            '    user = \'\'.join(user) if len(user) != 0 else \'admin\'',
            '    path = f\'{Path(__file__).parent.parent.parent}\\\\auth\\\\{domain}_{user}.json\'',
            '    Path(path).parent.mkdir(parents=True, exist_ok=True)',
            '    context = await browser.new_context(',
            '        viewport={\'width\': 1920, \'height\': 1080},',
            '        base_url=os.environ[environments["dev"]["app"]["domain"]],',
            '        storage_state=path if Path(path).exists() and \'auth\' not in request.node.name else None,',
            '        record_video_dir=f\'{Path(__file__).parent.parent.parent}\\\\videos\\\\{request.node.name}\\\\\',',
            '        ignore_https_errors=True,',
            '        java_script_enabled=True,',
            '        bypass_csp=True',
            '    )',
            '    page = await context.new_page()',
            '    yield BlankPage(page)',
            '    if \'auth\' in request.node.name:',
            '        await page.context.storage_state(path=path)',
            '    await page.close()',
            '    await context.close()',
            '@pytest.hookimpl(tryfirst=True, hookwrapper=True)',
            'def pytest_runtest_makereport(item: pytest.Item):',
            '    """Получаем отчет о выполнении теста и удаляем видео успешных тестов"""',
            '    def replace(lines: list, params: dict):',
            '        _ = []',
            '        def recursion(line: str, params: dict):',
            '            for param in params:',
            '                if isinstance(params[param], dict):',
            '                    return recursion(line, params[param])',
            '                return line.replace("{" + param + "}", str(params[param]))',
            '            for line in lines:',
            '                line = recursion(line, params)[8:]',
            '                if "{" not in line and "}" not in line:',
            '                    _.append(line)',
            '            return _',
            '    outcome = yield',
            '    report = outcome.get_result()',
            '    if report.when == "setup" and (doc := item.function.__doc__) != None:',
            '        doc = replace(doc.strip().split(\'\n\'), {"id": item.callspec.id} | item.callspec.params)',
            '        allure.dynamic.title(doc[0])',
            '        allure.dynamic.description("\n".join(doc[2:]))',
            '    if report.when == "call" and report.outcome == "passed":',
            '        shutil.rmtree(Path(f\'{Path(__file__).parent.parent.parent}\\\\videos\\\\{item.name}\\\\\'))'
        ]

    @classmethod
    @Creator(path="", mode="+w", name="pytest")
    def pytest(cls, lines: dict[Literal["api", "ui"], list[str | Page]]):
        return [
            '[pytest]',
            'pythonpath = . ',
            f'testspath = {Config.PATHS["tests"]}',
            'disable_test_id_escaping_and_forfeit_all_rights_to_community_support = True',
            'max_asyncio_tasks = 8',
            # 'asyncio_default_fixture_loop_scope = function',
            'addopts = ',
            '    -m \'regression\'',
            '    -p no:pytest_asyncio',
            # '    -p no:pytest-xdist',
            f'    --alluredir={Config.PATHS["path"]}{Config.PATHS["autotest"]}results',
            '    --clean-alluredir',
            'markers = ',
            '    regression: регресс тесты',
            '    api: api тесты',
            '    ui: ui тесты',
            [f'    api_{Text.to_snake_case(line)}: api тесты {line}' for line in lines["api"]],
            [f'    ui_{Text.to_snake_case(line["name"])}: ui тесты {line["name"]}' for line in lines["ui"]]
        ]

    @classmethod
    @Creator(path="", mode="+w", name="readme")
    def readme(cls, *args):
            return [
                f'# Autotest (первый запуск, настройка для Windows)',
                f'- устанавливаем vscode',
                f'- устанавляваем python>=3.12',
                f'- клонируем репозиторий',
                f'- создаем витруальное окружение со всеми зависимостями',
                f'```',
                f'pip install --upgrade pip',
                f'cd {Config.PATHS["path"].split("/")[-2]}',
                f'python -m venv .venv',
                r'.venv\Scripts\activate.ps1',
                f'pip install -r requirements.txt',
                '$env:PLAYWRIGHT_DOWNLOAD_HOST="https://nexus-cache.services.mts.ru/repository/raw-playwright.azureedge.net-proxy"',
                '$env:NODE_TLS_REJECT_UNAUTHORIZED=0',
                'playwright install',
                f'```',
                f'- открываем палитру команд (ctrl+shift+p)',
                f'- выбираем настройку тестов (configure tests)',
                f'- выбираем pytest',
                f'- выбираем {Config.PATHS["path"].split("/")[-2]}',
                f'- запускаем тесты через вкладку тестирование',
                '# Дополнительно (настройка .env)',
                '- на основании шаблона .env.example создать файл .env',
                '- заполнить данные о пользователях',
                '    - admin - role_id (1,2,10,11,14,15,16,20,21,22,23)',
                '    - regmn - role_id (3,4,5,6,7,11,17,18,19) region_id (02b50159-88e5-448c-935b-81f7cd8c0401, 087d56f0-fa0b-4dca-8163-f51880039387, 3ff456b7-98e3-4087-9fd9-9b60d3e40c0f, 46c2c07d-523d-430f-a6d9-6bd142858ad5, 5f476894-1f72-4940-8220-16b758167432, f58338d4-d8fe-4c75-9cfd-f12dc2725b63)',
                '- данные о стенде получить из https://ocean.mts.ru/tenant/ac20b856-b7d9-49a1-a54d-178288f059b9/spaces/coffers-dev/iam/871a3c57-fa4b-43e5-bf7b-02b161738add?clientId=coffers-dev&stand=isso-dev.mts.ru'
            ]

    @classmethod
    @Creator(path="", mode="+w", name="requirements")
    def requirements(cls, *args):
            return sorted([
                'pytest>=8.4.2',
                'pytest-playwright>=0.7.1',
                'pydantic>=2.12.3',
                'opencv-python>=4.12.0.88',
                'pytest-asyncio-cooperative>=0.40.0',
                'httpx>=0.28.1',
                'allure-pytest>=2.15.0',
                'python-dotenv>=1.2.1'
            ])

    @classmethod
    @Creator(path="", mode="+w", name="gitignore")
    def gitignore(cls, *args):
            return sorted([
                'sandbox',
                '.env',
                '.venv',
                '.pytest_cache',
                '__pycache__',
                'auth\n',
                'screenshots',
                'allure-results',
                'videos'
            ])

    @classmethod
    @Creator(path="", mode="+w", name="environments")
    def environments(cls, lines: dict[Literal["environments", "file_name"]]):
        return [
            [Text.to_comment_line(translation),
            sorted([f'{key.upper()}=\'{value if lines["file_name"] == ".env" else ""}\'' for key, value in lines["environments"].items() if section in key])] for section, translation in [("user", "ПОЛЬЗОВАТЕЛИ"), ("app", "СТЕНДЫ")]
        ]

    @classmethod
    @Creator(path=Config.PATHS["swagger"], mode="+w", name="blank_client")
    def blank_client(cls, lines: dict[Literal["tags", "environments"]]):
        return [
            'import os\n',
            'from typing import Literal\n',
            'from httpx import AsyncClient\n',
            [f'from {Config.PATHS["swagger_endpoints"].replace("/", ".")}{Text.to_snake_case(tag)}_endpoints import {Text.to_camel_case(tag)}\n' for tag in lines["tags"]],
            'class BlankClient:\n',
            '    TOKEN = {}\n',
            '    def __init__(self, client: AsyncClient):\n',
            '        self.__client = client\n',
            '    async def create_token(self, environment: dict):\n',
            '        data = {"grant_type": "password", "username": None, "password": None, "client_id": None, "client_secret": None}\n',
            '        for stand in environment:\n',
            '            users = environment[stand]["user"]\n',
            '            app = environment[stand]["app"]\n',
            '            for user in users:\n',
            '                data["username"] = os.environ[users[user]["login"]]\n',
            '                data["password"] = os.environ[users[user]["password"]]\n',
            '                data["client_id"] = os.environ[app["client_id"]]\n',
            '                data["client_secret"] = os.environ[app["client_secret"]]\n',
            '                response = await self.__client.post(os.environ[app["isso_url"]], data=data)\n',
            '                BlankClient.TOKEN.setdefault(stand, {}).setdefault(user, {}).setdefault("token", response.json()["access_token"])\n',
            '                BlankClient.TOKEN.setdefault(stand, {}).setdefault(user, {}).setdefault("domain", os.environ[app["domain"]])\n\n\n',
            f'    def set_token(self, client: Literal{list(lines["environments"][list(lines["environments"])[0]]["user"])} = "{list(lines["environments"][list(lines["environments"])[0]]["user"])[0]}", domain: Literal{list(lines["environments"])} = "{list(lines["environments"])[0]}"):\n',
            '        self.__client.base_url = BlankClient.TOKEN[domain][client]["domain"]\n',
            '        self.__client.headers = {"Authorization": f\'Bearer {BlankClient.TOKEN[domain][client]["token"]}\'}\n',
            [f'        self.{Text.to_snake_case(tag)} = {Text.to_camel_case(tag)}(self.__client)\n' for tag in lines["tags"]]
        ]

    @classmethod
    @Creator(path=Config.PATHS["swagger_endpoints"], mode="+a", name="endpoints")
    def endpoints(cls, lines: list[Endpoint]):
        return [
            'from httpx import AsyncClient\n',
            'from pydantic import BaseModel, Field\n',
            [f'from {Config.PATHS["swagger_schemas"].replace("/", ".")}{Text.to_snake_case(schema.name)} import {schema.name}\n'  for line in lines for method in line.methods for schema in method.schemas if schema.name != None],
            f'class {Text.to_camel_case(lines[0].methods[0].tag)}:\n',
            '    def __init__(self, client):\n',
            [f'        self.{Text.to_snake_case(line.name)} = Endpoint{Text.to_camel_case(line.name)}(client)\n' for line in lines],
            [[f'class Endpoint{Text.to_camel_case(line.name)}:\n',
            [[f'    class {method.name.capitalize() + "Params"}(BaseModel):\n',
            [f'        {parameter.name}: {parameter.type} = Field(None, alias=\'{parameter.alias}\')\n' for parameter in list(filter(lambda _: _.param == "query", method.parameters))]] for method in line.methods if method.parameters != None and len(list(filter(lambda _: _.param == "query", method.parameters))) != 0],
            [[f'    class {method.name.capitalize()}RequestBody(BaseModel):\n',
            [f'        {props.name}: {props.type} = None\n' for props in schema.properties]] for method in line.methods for schema in method.schemas if schema.name == None and schema.properties != None and schema.body_type == "request"],
            [[f'    class {method.name.capitalize()}Status{schema.status}(BaseModel):\n',
            [f'        {props.name}: {props.type}\n' for props in schema.properties]] for method in line.methods for schema in method.schemas if schema.name == None and schema.properties != None and schema.body_type != "request"],
            '    def __init__(self, client: AsyncClient):\n', 
            '        self.__client = client\n',
            f'        self.__url = \'{line.endpoint}\'\n',
            [f'        self.body_{method.name} = {request[0].name}()\n' if request[0].name != None else f'        self.body_{method.name} = Endpoint{Text.to_camel_case(line.name)}.{method.name.capitalize()}RequestBody()\n' for method in line.methods if len(request := list(filter(lambda _: _.body_type == 'request' , method.schemas))) != 0],
            [f'        self.params = Endpoint{Text.to_camel_case(line.name)}.{method.name.capitalize() + "Params"}()\n' for method in line.methods if method.parameters != None and len(list(filter(lambda _: _.param == "query", method.parameters))) != 0],
            [
            [f'    async def {method.name}(self{', ' + ', '.join([f'{parameter.name}: {parameter.type}' for parameter in list(filter(lambda _: _.param == "path", method.parameters))]) if method.parameters != None and len(list(filter(lambda _: _.param == "path", method.parameters))) != 0 else ''}):\n',
            f'        response = await self.__client.{method.name}(\n',
            [f'            self.__url{'.replace(' + '.replace('.join([f'\'{{{parameter.name}}}\', str({parameter.name}))' for parameter in list(filter(lambda _: _.param == "path", method.parameters))]) if method.parameters != None and len(list(filter(lambda _: _.param == "path", method.parameters))) != 0 else ''},\n',],
            [f'            headers={{\'Content-Type\': \'{schema.content_type}\'}},\n' for schema in list(filter(lambda _: _.body_type == "response" and 200 <= int(_.status) < 300 , method.schemas)) if schema.content_type != None],
            [f'            data = self.body_{method.name}.model_dump_json(),\n'] if len(request := list(filter(lambda _: _.body_type == 'request' , method.schemas))) != 0 else [],
            [f'            params = self.params.model_dump(exclude_none=True, by_alias=True),\n'] if method.parameters != None and len(list(filter(lambda _: _.param == "query", method.parameters))) != 0 else [],
            f'        )\n',
            [[f'        if response.status_code == {schema.status}:\n',
            f'            self.response_status_{schema.status} = Endpoint{Text.to_camel_case(line.name)}.{method.name.capitalize() + "Status" + schema.status}(**response.json())\n' if schema.name == None else f'            self.response_status_{schema.status} = {schema.name}(**response.json())\n',] for schema in method.schemas if schema.status != None and (schema.name != None or schema.properties != None)],
            f'        return response\n'] for method in line.methods]] for line in lines]
        ]

    @classmethod
    @Creator(path=Config.PATHS["swagger_schemas"], mode="+w", name="schemas")
    def schemas(cls, lines: Schema):
        return [
            'from pydantic import BaseModel\n',
            [f'from {Config.PATHS["swagger_schemas"].replace("/", ".")}{Text.to_snake_case(props.schema)} import {props.schema}\n' for props in list(filter(lambda _: _.schema != None, lines.properties))],
            f'class {lines.name}(BaseModel):\n',
            [f'    {props.name}: {props.type} = None\n' for props in lines.properties]
        ]

    @classmethod
    @Creator(path=Config.PATHS["params"], mode="+w", name="param_env")
    def param_env(cls, lines: Literal["environments"]):
        return [
            'import pytest',
            'from dataclasses import dataclass',
            '@dataclass',
            'class ParamEnv:',
            '    PARAM_USERS: tuple = (',
            '        "user",',
            '        [',
            [[
            '            pytest.param(',
            f'                "{user}",',
            f'                id="{user}",',
            f'            ),'] for user in lines["environments"][list(lines["environments"])[0]]["user"]],
            '        ]',
            '    )',
            '    PARAM_URLS: tuple = (',
            '        "url",',
            '        [',
            [['            pytest.param(',
            f'                "{url}",',
            f'                id="{url}",',
            '            ),'] for url in lines["environments"]],
            '        ]',
            '    )',
        ]

    @classmethod
    @Creator(path=Config.PATHS["params_api"], mode="+a", name="params_api")
    def params_api(cls, lines: list[Endpoint]):
        return [
            'import pytest',
            'from dataclasses import dataclass',
            [['@dataclass',
            f'class Param{Text.to_camel_case(line.name)}:',
            [[f'    PARAM_{method.name.upper()}_STATUS_{schema.status}: tuple = (',
            '        "param",',
            '        [',
            '            pytest.param(',
            '                {"sandbox": "sandbox"},',
            '                #  marks=pytest.mark.skip(reason="sandbox"),',
            '                id="sandbox"',
            '            )',
            '        ]',
            '    )'] for method in line.methods for schema in method.schemas if schema.status != None]] for line in lines]
        ]

    @classmethod
    @Creator(path=Config.PATHS["tests_test_api"], mode="+a", name="tests_api")
    def tests_api(cls, lines: Endpoint):
        return [
            'import pytest',
            f'from {Config.PATHS["params"].replace("/", ".")}param_env import ParamEnv',
            f'from {Config.PATHS["swagger"].replace("/", ".")}blank_client import BlankClient',
            f'from {Config.PATHS["params_api"].replace("/", ".")}param_{Text.to_snake_case(lines.methods[0].tag)}_api import Param{Text.to_camel_case(lines.name)}',
            [f'@pytest.mark.api_{Text.to_snake_case(lines.methods[0].tag)}',              
            '@pytest.mark.api',       
            '@pytest.mark.regression',
            f'class Test{Text.to_camel_case(lines.name)}:',
            [[f'    @pytest.mark.asyncio_cooperative',
            f'    @pytest.mark.parametrize(*Param{Text.to_camel_case(lines.name)}.PARAM_{method.name.upper()}_STATUS_{schema.status})',
            f'    @pytest.mark.parametrize(*ParamEnv.PARAM_USERS)',
            f'    async def test_{Text.to_snake_case(method.tag)}_{method.name}_status_{schema.status}(',
            f'        self,',
            f'        client: BlankClient,',
            f'        user,',
            f'        param',
            f'    ):',
            f'        client.set_token(client=user)',
            f'        pass'] for method in lines.methods for schema in method.schemas if schema.status != None]]
        ]

    @classmethod
    @Creator(path=Config.PATHS["browser_pages"], mode="+a", name="pages")
    def pages(cls, lines: dict[Literal["page", "components"], Page | str]):
        return [
            'from playwright.async_api import Page, expect',
            [f'from {Config.PATHS["browser_components"].replace("/", ".")}component_{Text.to_snake_case(line)} import Component{Text.to_camel_case(line)}' for line in lines["page"]["components"] if line in lines["components"]],
            f'class {Text.to_camel_case(lines["page"]["name"])}:',
            '    def __init__(self, page: Page):',
            [f'        self.{Text.to_snake_case(line.replace(f'{lines["page"]["name"]}_', ''))} = {Text.to_camel_case(line.replace(f'{lines["page"]["name"]}_', ''))}(page)' for line in lines["page"]["components"]],
            [[f'class {Text.to_camel_case(line)}(Component{Text.to_camel_case(line)}):' if line in lines["components"] else f'class {Text.to_camel_case(line.replace(f'{lines["page"]["name"]}_', ''))}:',
            '    def __init__(self, page: Page):',
            '        super().__init__(page)' if line in lines["components"] else '        pass'] for line in lines["page"]["components"]]
        ]

    @classmethod
    @Creator(path=Config.PATHS["browser_components"], mode="+a", name="components")
    def components(cls, lines: str):
        return [
            'from playwright.async_api import Page, expect',
            [f'class Component{Text.to_camel_case(lines)}:',
            '    def __init__(self, page: Page):',
            '        pass']
        ]

    # устарела
    @classmethod
    @Creator(path=Config.PATHS["browser"], mode="+w", name="blank_page")
    def blank_page_old(cls, lines: dict[Literal["pages", "environments"], list[Page]]):
        return [
            'from typing import Dict, Type, Literal',
            'from playwright.async_api import Page, BrowserContext',
            [f'from {Config.PATHS["browser_pages"].replace("/", ".")}{Text.to_snake_case(line["name"])} import {Text.to_camel_case(line["name"])}' for line in lines["pages"]],
            'class BlankPage:',
            f'    DOMAIN = Literal{list(lines["environments"])}',
            f'    CLIENT = Literal{list(lines["environments"][list(lines["environments"])[0]]["user"]) + ["unknown"]}',
            '    def __init__(self, contexts: Dict[str, Type[BrowserContext]]):',
            '        self._contexts = contexts',
            '    async def close(self):',
            '        await self._page.close()',
            '    async def go_back(self):',
            '        await self._page.go_back()',
            '    async def reload(self):',
            '        await self._page.reload()',
            [[f'    async def go_to_{Text.to_snake_case(line["name"])}_page(self, domain: DOMAIN = \'{list(lines["environments"])[0]}\', client: CLIENT = \'{list(lines["environments"][list(lines["environments"])[0]]["user"])[0]}\'):',
            '        self._domain, self._client = domain, client' if line["name"] == "authorization" else '',
            '        self._page: Page = await self._contexts[domain]["unknown"].new_page()' if line["name"] == "authorization" else '        self._page: Page = await self._contexts[domain][client].new_page()',
            f'        await self._page.goto(url=\'{line["url"]}\', timeout=300000)',
            [f'        self.{Text.to_snake_case(dependence)} = {Text.to_camel_case(dependence)}(self._page)' for dependence in line["dependencies"]]] for line in lines["pages"]]
        ]

    @classmethod
    @Creator(path=Config.PATHS["browser"], mode="+w", name="blank_page")
    def blank_page(cls, lines: dict[Literal["pages", "environments"], list[Page]]):
        return [
            'from typing import Literal',
            'from playwright.async_api import Page',
            [f'from {Config.PATHS["browser_pages"].replace("/", ".")}{Text.to_snake_case(line["name"])} import {Text.to_camel_case(line["name"])}' for line in lines["pages"]],
            'class BlankPage:',
            f'    URLS = Literal{sorted(list(set(line["url"] for line in lines["pages"])))}',
            '    def __init__(self, page: Page):',
            '        self._page = page',
            '    async def close(self):',
            '        await self._page.close()',
            '    async def go_back(self):',
            '        await self._page.go_back()',
            '    async def reload(self):',
            '        await self._page.reload()',
            [f'    async def go_to(self, *, url: URLS = "", **kwargs):',
            '        for key, value in kwargs.items():',
            '            url = url.replace(f\'{key}\', str(value))',
            '        await self._page.goto(url=url, timeout=300000)',
            [f'        self.{Text.to_snake_case(line["name"]).replace('_page', '')} = {Text.to_camel_case(line["name"])}(self._page)' for line in lines["pages"]]]
        ]

    @classmethod
    @Creator(path=Config.PATHS["tests_test_ui"], mode="+a", name="tests_ui")
    def tests_ui(cls, lines: Literal["component", "name", "url"]):
        return [
            'import pytest',
            f'from {Config.PATHS["params"].replace("/", ".")}param_env import ParamEnv',
            f'from {Config.PATHS["browser"].replace("/", ".")}blank_page import BlankPage',
            f'from {Config.PATHS["params_ui"].replace("/", ".")}param_{Text.to_snake_case(lines["name"])} import Param{Text.to_camel_case(lines["name"] + '_' + lines["component"].replace(f'{lines["name"]}_', ''))}',
            f'@pytest.mark.ui_{Text.to_snake_case(lines["name"])}',              
            '@pytest.mark.ui',       
            '@pytest.mark.regression',
            f'class Test{Text.to_camel_case(lines["name"] + '_' + lines["component"].replace(f'{lines["name"]}_', ''))}:',
            '    @pytest.mark.asyncio_cooperative',
            f'    @pytest.mark.parametrize(*Param{Text.to_camel_case(lines["name"] + '_' + lines["component"].replace(f'{lines["name"]}_', ''))}.PARAM_{lines["component"].replace(f'{lines["name"]}_', '').upper()})',
            '    @pytest.mark.parametrize(*ParamEnv.PARAM_USERS)',
            f'    async def test_{Text.to_snake_case(lines["name"] + '_' + lines["component"])}(self, page: BlankPage, user, param):',
            f'        # await page.go_to(url={Text.to_snake_case(lines["url"])})',
            '        pass'
        ]

    @classmethod
    @Creator(path=Config.PATHS["params_ui"], mode="+a", name="params_ui")
    def params_ui(cls, lines: Page):
        return [
            'import pytest',
            'from dataclasses import dataclass',
            [['@dataclass',
            f'class Param{Text.to_camel_case(lines["name"] + '_' + line.replace(f'{lines["name"]}_', ''))}:',
            f'    PARAM_{line.replace(f'{lines["name"]}_', '').upper()}: tuple = (',
            '        "param",',
            '        [',
            '            pytest.param(',
            '                {"sandbox": "sandbox"},',
            '                #  marks=pytest.mark.skip(reason="sandbox"),',
            '                id="sandbox"',
            '            )',
            '        ]',
            '    )'] for line in lines["components"]]
        ]


@dataclass
class FastTest:
    configuration = Config

    @classmethod
    def create_api(cls):
        Create.endpoints()
        Create.environments()
        Create.gitignore()
        Create.readme()
        Create.pytest()
        Create.requirements()
        Create.schemas()
        Create.blank_client()
        Create.conftest_api()
        Create.param_env()
        Create.params_api()
        Create.tests_api()

    @classmethod
    def create_ui(self):
        if Config.UI:
            Create.environments()
            Create.gitignore()
            Create.readme()
            Create.pytest()
            Create.requirements()
            Create.tests_ui()
            Create.pages()
            Create.components()
            Create.blank_page()
            Create.tests_ui()
            Create.params_ui()
            Create.conftest_ui()
