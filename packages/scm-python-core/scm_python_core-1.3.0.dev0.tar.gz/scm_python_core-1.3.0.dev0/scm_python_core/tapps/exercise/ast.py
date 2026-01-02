import ast, unittest
import tlog.tlogging as tl

log = tl.log

UT = unittest.TestCase()


def exercise_ast_handler():
    log.info(f"exercise_ast")
    code_str = """
\"""This is a comment for the cli_invoker function\"""
@cli_invoker(
  'idea/settings-color'
)#set idea color
def my_function():
    \"""This is a comment for the my_function function\"""
    pass
"""
    tree = ast.parse(code_str)
    function_preceding_comment = ""
    decorator_preceding_comment = ""
    decorator_comment = ""
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            # 获取函数定义前面的注释
            function_lineno = node.lineno
            decorator = node.decorator_list[0]
            decorator_comment_line = code_str.split("\n")[function_lineno - 2]
            UT.assertEqual(3, decorator.lineno)
            UT.assertEqual(
                "This is a comment for the cli_invoker function",
                decorator_preceding_comment := ast.get_docstring(tree),
            )
            UT.assertEqual(
                "set idea color",
                decorator_comment := (
                    decorator_comment_line[decorator_comment_line.find("#") + 1 :]
                    if "#" in decorator_comment_line
                    else ""
                ),
            )
            UT.assertEqual(6, function_lineno)
            UT.assertEqual(
                "This is a comment for the my_function function",
                function_preceding_comment := ast.get_docstring(node),
            )
    UT.assertEqual(
        "This is a comment for the cli_invoker function", decorator_preceding_comment
    )
    UT.assertEqual("set idea color", decorator_comment)
    UT.assertEqual(
        "This is a comment for the my_function function", function_preceding_comment
    )

    code_str = """
\"""This is a comment block
123\"""
"""
    tree = ast.parse(code_str)
    block_comment = ""
    for node in tree.body:
        if isinstance(node, ast.Expr):
            print("ast block_comment", block_comment := ast.get_docstring(tree))
    UT.assertEqual("This is a comment block\n123", block_comment)
    context = {"var_a": 1, "var_b": 2}
    code_lines: list[str] = [
        f"{var_name}={var_value}" for var_name, var_value in context.items()
    ]
    code_lines.append('context["conditional_result"] = var_a')
    code_str = "\n".join(code_lines)
    parsed_code = ast.parse(code_str, mode="exec")
    exec(compile(parsed_code, filename="<ast>", mode="exec"))
    print("ast dynamic exec and change variable value outer code", context)
    conditional_result = context["conditional_result"]
    UT.assertIsInstance(conditional_result, int)
    UT.assertTrue(conditional_result)

    # 需要解析的示例 Python 代码
    code = """
def example_function(a, b=True, c=False, d=42, e='text'):
    pass
    """

    # 使用 ast 解析代码
    tree = ast.parse(code)

    # 函数用于查找布尔类型的参数
    def find_bool_params(func_def: ast.AST):
        bool_params = []
        arg_names: list = [*func_def.args.args]
        arg_values: list = [*func_def.args.defaults]
        arg_names.reverse()
        arg_values.reverse()
        print(
            "------ find_bool_params::",
            arg_names,
            arg_values,
        )
        for arg, default in zip(arg_names, arg_values):
            print("-----", arg.arg, default.value, default.kind)
            # 检查默认值是否为 True 或 False
            if isinstance(default, ast.Constant) and isinstance(default.value, bool):
                bool_params.append(arg.arg)  # 将参数名称添加到列表中
        return bool_params

    # 查找 AST 中的函数定义
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            bool_params = find_bool_params(node)
            bool_params.reverse()
            print(f"Function '{node.name}' has boolean parameters: {bool_params}")
            UT.assertListEqual(["b", "c"], bool_params)
