# SCM-PYTHON CORE 开发

## 插件开发规范

1. package name start with 'scm-python-'
1. the python code should be in folder 'scm_python_', The folder name and the plugin name should be similar.
1. the inner module name should be in "lib, tapps, tutils"
1. the sample see [Shao/scm-python-jira](https://de.vicp.net:58443/Shao/scm-python-jira)

## 插件使用规范

1. pip install scm-python-any-plugin, then the plugin will be loader automatically
1. or update ~/any-host-name/etc/install.runtime.yaml, add the plugin python code folder name into "python/exteral_lib" 