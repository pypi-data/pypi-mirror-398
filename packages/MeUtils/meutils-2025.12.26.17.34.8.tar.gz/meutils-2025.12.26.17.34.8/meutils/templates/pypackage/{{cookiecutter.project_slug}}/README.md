{% set is_open_source = cookiecutter.open_source_license != 'Not open source' -%}

{% if is_open_source %}

![image](https://img.shields.io/pypi/v/{{ cookiecutter.project_slug }}.svg) ![image](https://img.shields.io/travis/{{ cookiecutter.github_username }}/{{ cookiecutter.project_slug }}.svg) ![image](https://readthedocs.org/projects/{{ cookiecutter.project_slug | replace("_", "-") }}/badge/?version=latest)

{% endif %}

<h1 align = "center">🔥{{ cookiecutter.project_name }}🔥</h1>

---
# Install
```python
pip install -U {{cookiecutter.project_slug}}
```

# [Docs](https://yuanjie-ai.github.io/{{cookiecutter.project_slug}}/)

# Usages
```
import {{cookiecutter.project_slug}}
```

---
# TODO
