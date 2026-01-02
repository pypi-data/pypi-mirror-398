import sys, importlib, os, re, ast
import tlog.tlogging as tl
import tio.tfile as tf

log = tl.log


def is_multi_line_comment(comment_line: str):
    return "'''" in comment_line or '"""' in comment_line


def is_single_line_comment(comment_line: str):
    return len(comment_line) > 1 and comment_line[0] == "#"


def is_comment(comment_line: str):
    return is_multi_line_comment(comment_line) or is_single_line_comment(comment_line)


class DecoratedFunction:
    def __init__(
        self,
        function_name: str,
        function_args: ast.arguments,
        decorator: ast.Call,
        comment: str,
    ):
        """
        function_name: 例如 sync_folder
        decorator: 例如 Call(func=Name(id='cli_invoker', ctx=Load()), args=[Constant(value='install/sync')], keywords=[]), Function Name: sync_folder
        """
        self.function_name = function_name
        self.function_args = function_args
        self.decorator = decorator
        self.comment = comment


class DecoratedModule:
    def __init__(
        self,
        package: str,
        module_file: str,
        decorated_functions: list[DecoratedFunction],
    ):
        """
        package: 例如lib
        file: 例如code.py
        """
        file = os.path.basename(module_file)
        self.module_name = f"{package}.{file[0: len(file) - 3]}"
        self.module_abs_file = module_file
        self.decorated_functions = decorated_functions


# 创建一个访问器类来分析AST
class DecoratorVisitor(ast.NodeVisitor):
    def __init__(self, code_lines: list[str], target_decorator_name="@cli_invoker"):
        self.code_lines = code_lines
        self.target_decorator_name: str = target_decorator_name
        self.target_decorated_functions: list[DecoratedFunction] = []

    def get_non_empty_line_no(self, code_line_no: int):
        while not self.code_lines[code_line_no]:
            code_line_no = code_line_no - 1
        return code_line_no

    def get_decorator_preceding_multi_line_comment(
        self, code_line_no: int, comment_lines: list[str]
    ):
        while not is_multi_line_comment(self.code_lines[code_line_no - 1]):
            comment_lines.append(self.code_lines[code_line_no - 1])
            code_line_no = code_line_no - 1
        if is_multi_line_comment(self.code_lines[code_line_no - 1]):
            comment_lines.append(self.code_lines[code_line_no - 1])

    def get_decorator_preceding_single_line_comment(
        self, code_line_no: int, comment_lines: list[str]
    ):
        while is_single_line_comment(self.code_lines[code_line_no - 1]):
            comment_lines.append(self.code_lines[code_line_no - 1][1:])
            code_line_no = code_line_no - 1

    def get_decorator_preceding_comment(self, decorator: ast.expr) -> str:
        code_line_no = self.get_non_empty_line_no(decorator.lineno - 2)
        decorator_preceding_comment_line = self.code_lines[code_line_no]
        if is_comment(decorator_preceding_comment_line):
            comment_lines: list[str] = []
            if is_multi_line_comment(decorator_preceding_comment_line):
                comment_lines.append(decorator_preceding_comment_line)
                self.get_decorator_preceding_multi_line_comment(
                    code_line_no, comment_lines
                )
            elif is_single_line_comment(decorator_preceding_comment_line):
                # 必须要添加\n否则ast.get_docstring(ast.parse)会报错
                comment_lines.append(f'{decorator_preceding_comment_line[1:]}\n"""')
                self.get_decorator_preceding_single_line_comment(
                    code_line_no, comment_lines
                )
                comment_lines.append(f'"""')
            comment_lines.reverse()
            comment_str = "\n".join(comment_lines)
            # ast.parse会输出warning <unknown>:915: SyntaxWarning: invalid escape sequence '\c'
            # if "\\g" in comment_str:
            #     print(comment_str)
            expr = ast.parse(comment_str)
            return ast.get_docstring(expr)  # type: ignore
        return ""

    def get_decorator_comment(self, node: ast.FunctionDef) -> str:
        code_line_no = node.lineno - 2
        decorator_comment_line = self.code_lines[code_line_no]
        # 最后一个字符是\n需要排除掉
        return (
            decorator_comment_line[decorator_comment_line.find("#") + 1 :].strip()
            if "#" in decorator_comment_line
            else ""
        )

    def get_function_preceding_comment(self, node: ast.FunctionDef) -> str:
        return ast.get_docstring(node)  # type: ignore

    def visit_FunctionDef(self, node):
        if node.decorator_list:
            for decorator in node.decorator_list:
                if f"@{decorator.func.id}" == self.target_decorator_name:  # type: ignore
                    # ------ visit_FunctionDef:: ast.FunctionDef pull_vilink_handler <ast.arguments object at 0x0000023DF80EDE10>
                    # print(
                    #     "------ visit_FunctionDef:: ast.FunctionDef",
                    #     node.name,
                    #     node.args,
                    # )
                    comment_lines: list[str] = []
                    # 如果有--quiet,保险起见不解析comment
                    if not tl.QUIET:
                        if comment_line := self.get_decorator_preceding_comment(
                            decorator
                        ):
                            comment_lines.append(comment_line)
                        if comment_line := self.get_decorator_comment(node):
                            comment_lines.append(comment_line)
                        if comment_line := self.get_function_preceding_comment(node):
                            comment_lines.append(comment_line)
                    self.target_decorated_functions.append(DecoratedFunction(node.name, node.args, decorator, "\n".join(comment_lines)))  # type: ignore
                    # if 'exercise_hello_world' == node.name:
                    #     print('------', node.name, comment_lines)
                    break
        self.generic_visit(node)


class ClassScaner(object):
    scan_packages = []
    class_paths: list[str] = []
    decorator_names = "@cli"

    def __init__(self, packages=["lib"], decorator_names=["@cliInit", "@cli_invoker"]):
        self.scan_packages = packages
        self.decorator_names = decorator_names

    def scan_single_package(self, package: str) -> list[DecoratedModule]:
        values: list[DecoratedModule] = []
        for class_path in [tf.getpythonpath()] + ClassScaner.class_paths:
            package_path = os.path.abspath(
                os.path.join(class_path, *package.split("."))
            )
            for file in os.listdir(package_path):
                if not file.startswith("__") and file.endswith(".py"):
                    module_file = os.path.join(package_path, file)
                    # print("---ClassScaner", module_file)
                    with open(module_file, "r", encoding="utf8") as fs:
                        content = fs.read()
                    tree = ast.parse(content)
                    visitor = DecoratorVisitor(
                        tf.readlines(module_file, allowEmpty=True, allowStrip=True)
                    )
                    visitor.visit(tree)
                    if len(visitor.target_decorated_functions) > 0:
                        values.append(
                            DecoratedModule(
                                package, module_file, visitor.target_decorated_functions
                            )
                        )
        return values

    def scan(self):
        """
        return[(module_name,[function])]
        function=@decorator.[classname.]<func>
        """
        classes: list[DecoratedModule] = []
        for package in self.scan_packages:
            classes = classes + self.scan_single_package(package)
        return classes
