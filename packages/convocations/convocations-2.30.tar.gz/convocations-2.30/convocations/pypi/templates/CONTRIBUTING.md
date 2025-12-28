# {{ name }}

# contributing

## getting your development environment setup

```bash
git clone ...
cd /path/to/{{ name }}
make uv
make setup
```

## running integration tests

```bash
cd /path/to/{{ name }}
source bin/activate
make test
```

## building

builds an sdist for distribution to code artifact, pypi, etc.

```bash
cd /path/to/{{ name }}
make build
```

## lint

lint your code

```bash
cd /path/to/{{ name }}
make lint
```

## publish

publish code to repository like code artifact or pypi.  
upload will be done by `twine`.   

```bash
cd /path/to/{{ name }}
make publish
```

