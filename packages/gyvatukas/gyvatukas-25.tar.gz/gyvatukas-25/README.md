# gyvatukas
collection of python utils and prototypes. feel free to open mrs and send hate mail to dev@paulius.xyz

## usage
`pip install gyvatukas` or `poetry add gyvatukas`
```python
import gyvatukas as g

tel = '+37060000000'
is_valid, clean_tel = g.validate_lt_tel_nr(tel)
print(is_valid, clean_tel)
```

## dev
1. New code (add new features to `__init__/__all__` if/when they are "prod" worthy)
2. Build docs
3. Increment version in pyproject.toml
4. Build package (commit package + pyproject.toml + docs (clean single build commit, since docs 
   are published from master and are source of truth for the latest pypi release))
5. `poetry publish`
