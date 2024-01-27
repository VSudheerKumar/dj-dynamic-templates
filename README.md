# dj-dynamic-templates

dj-dynamic-templates package is used for controlling mail templates dynamically using django admin panel.

It's designed to integrate seamlessly with Django projects

---

## Requirements

* Python 3.11+
* Django 5.0+
* django-markdownx 4.0.7+ (optional)


## Installation


Install using `pip`...

    pip install dj_dynamic_templates

Add `'dj_dynamic_templates'` to your `INSTALLED_APPS` setting.
```python
INSTALLED_APPS = [
    ...
    'dj_dynamic_templates',
]
```

> **_Optional_**
> 
> Install [django-markdownx](https://pypi.org/project/django-markdownx/) for better experience of template editing.
> 
> Open the hyperlink and follow the procedure provided in that document

Now migrate the changes into your database
```shell
python manage.py migrate
```
___

Now login to django admin panel and start using this package