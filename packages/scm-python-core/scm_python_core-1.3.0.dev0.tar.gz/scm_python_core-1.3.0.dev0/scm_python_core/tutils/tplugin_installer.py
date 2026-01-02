from tutils.dynmic_module import ClassScaner
import tutils.thpe as thpe
import tio.tfile as tf
import tutils.ttemplate as ttemplate
import tutils.context_opt as tcontext
import os

SCM_PYTHON_PLUGIN_DIR = os.path.join(
    os.path.expanduser("~"), ".scm-python", "scm-python-plugins"
)


def plugin_has_been_installed(plugin_name: str) -> bool:
    for class_path in ClassScaner.class_paths:
        if plugin_name in class_path:
            return True
    return False


def generate_plugin_code_handler(plugin_name: str):
    project_folder = os.path.join(SCM_PYTHON_PLUGIN_DIR, plugin_name)
    if os.path.exists(project_folder):
        tf.remove_dirs(project_folder)
    project_folder_name = plugin_name
    package_name = plugin_name.replace("-", "_")
    context = thpe.create_env_context()
    plugin_template = {
        "new": {
            "copy": {
                package_name: f"https://de.vicp.net:58443/Shao/{plugin_name}/-/raw/main/{package_name}"
            }
        }
    }
    cloned_context = tcontext.deep_merge(
        context, {"CURRENT_FOLDER_NAME": project_folder_name}
    )
    ttemplate.handle_template_for_common_scripts(
        project_folder,
        plugin_template,
        cloned_context,
        comments="",
        allow_escape_char=True,
    )
    if not plugin_has_been_installed(plugin_name):
        append_plugin_file_name_into_yaml_handler(
            os.path.join(project_folder, package_name)
        )


def update_install_runtime_module_handler(module: str, yaml_file: str):
    context = thpe.create_env_context()
    package_name = os.path.basename(yaml_file)
    project_folder = os.path.dirname(yaml_file)
    hostname = "ub-8dev" if thpe.is_linux else "win-8001"
    url = f"https://de.vicp.net:58443/Shao/scm-python-config-files/-/raw/main/{hostname}/etc/{package_name}"
    plugin_template = {"new": {"copy": {".": url}}}
    print("---update_install_runtime_module_handler", project_folder, plugin_template)
    cloned_context = tcontext.deep_merge(context, {"CURRENT_FOLDER_NAME": module})
    ttemplate.handle_template_for_common_scripts(
        project_folder,
        plugin_template,
        cloned_context,
        comments="",
        allow_escape_char=True,
    )


def append_plugin_file_name_into_yaml_handler(project_folder_name: str):

    lines = tf.readlines(thpe.runtime_install_file, allowEmpty=True, allowStrip=False)
    updated = False
    for index, line in enumerate(lines):
        if line.startswith("python:"):
            if "external_lib:" in lines[index + 1]:
                start_index = index + 2
                while start_index < len(lines):
                    if not lines[start_index].strip().startswith("-"):
                        break
                    start_index += 1
                lines.insert(start_index, f"    - {project_folder_name}\n")
                updated = True
    if not updated:
        lines.append("python:\n")
        lines.append("  external_lib:\n")
        lines.append(f"    - {project_folder_name}\n")
    tf.writelines(thpe.runtime_install_file, lines)


def install_plugin_handler(args: list[str]):
    plugin_name_dict = {}
    for arg in args:
        plugin_name = arg.replace("--", "")
        plugin_name_dict[plugin_name] = os.path.join(SCM_PYTHON_PLUGIN_DIR, plugin_name)
        generate_plugin_code_handler(plugin_name)

    print("---install_plugin_handler", plugin_name_dict, thpe.runtime_install_file)


def update_yaml_handler(args: list[str]):
    plugin_name_dict = {}
    for arg in args:
        plugin_name = arg.replace("--", "")
        plugin_name_dict[plugin_name] = os.path.join(
            thpe.HOST_FOLDER, "etc", f"{plugin_name}.install.runtime.yaml"
        )
        update_install_runtime_module_handler(
            plugin_name, plugin_name_dict[plugin_name]
        )

    print("---update_yaml_handler", plugin_name_dict, thpe.runtime_install_file)
