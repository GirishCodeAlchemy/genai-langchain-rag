.PHONY: run clean docs

black:
	black .

# test:
# 	coverage run -m pytest tests && coverage html && open htmlcov/index.html

type-check:
	mypy .

