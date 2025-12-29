language: [Farsi](https://github.com/ehs22n/django-toon/blob/main/docs/README.fa.md)  -- [Arabic](https://github.com/ehs22n/django-toon/blob/main/docs/README.ar.md)



**django-toon** is a package for sending data in the **Toon** format, `which is several times faster than JSON`.


The library offers two important features for **Django**. For example, you can create `dynamic` views that can return either `JSON` or `Toon` based on the request.

# django-toon — Django Integration Guide


## Usage:

### Installation

```python
pip install "django-toon"
```
---

## Return **Toon** for all requests

#### settings.py
```python
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'django_toon.django.render.ToonRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'django_toon.django.parser.ToonParser',
    ],
}
```

## Enable dynamic mode (JSON or Toon based on headers)

```python
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
         'django_toon.django.render.DynamicRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'django_toon.django.parser.DynamicParser',
    ],
}

```

# Header Examples


**Send JSON → Receive Toon**:
```bash
Content-Type: application/json
Accept: application/x-toon
```



**Send Toon → Receive Toon**:

```bash
Content-Type: application/x-toon
Accept: application/x-toon
```

**Send Toon → Receive JSON**:

```bash
Content-Type: application/x-toon
Accept: application/json

```

---

## Per-View Configuration

### Dynamic view

#### views.py

```python
from django_toon.parser import DynamicParser
from django_toon.render import DynamicRenderer

class Index(APIView):
    parser_classes = [DynamicParser]
    renderer_classes = [DynamicRenderer]

    def get(self, request, *args, **kwargs):
        return Response({"message": "Hello django-toon"})

```

### Toon-only view

```python
from django_toon.parser import ToonParser
from django_toon.render import ToonRenderer

class Index(APIView):
    parser_classes = [ToonParser]
    renderer_classes = [ToonRenderer]

    def get(self, request, *args, **kwargs):
        return Response({"message": "Hello django-toon"})


```

---


### How to Test API:
```bash
source .venv/bin/activate
```

```bash
$ django-toon version

> 0.1.1
```

> you can use GET and POST method to test your api

```bash
$ django-toon get https://exmaple.com/
```

```bash
$ django-toon post https://exmaple.com/ --payload '{"key": "value"}'

```

# Contributing

We warmly welcome all contributions to django-toon!
Whether you have an idea for improvement, found a bug, or want to add a new feature, we would be happy to have your help.

How to contribute

For small changes, feel free to open a Pull Request directly.

For larger features or significant changes, please open an Issue first so we can discuss the approach together.

Make sure your code is clean, readable, and includes any necessary tests.

🐞 Reporting Issues

If you encounter a problem:

First check whether the issue has already been reported.

If not, please open a New Issue with:

A clear description of the problem

Steps to reproduce

Python/framework/OS versions

Any relevant logs or error messages

We do our best to respond and fix issues as quickly as possible.
--


# django-toonLicense (MIT-based Open License)
Copyright (c) 2025 django-toon Developers

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights  
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell      
copies of the Software, and to permit persons to whom the Software is         
furnished to do so, subject to the following conditions:                      

The above copyright notice and this permission notice shall be included in     
all copies or substantial portions of the Software.                           

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR    
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,      
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE   
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER        
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING       
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS 
IN THE SOFTWARE.                                                              

This project is completely free and open-source.  
There are **no costs, no licensing fees, no subscription requirements**, and  
you are free to use it in personal, educational, and commercial projects.     
