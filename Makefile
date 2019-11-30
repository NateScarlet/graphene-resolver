.PHONY: test

dist: graphene_resolver/* pyproject.toml
	poetry build

test:
	poetry run pytest --cov=graphene_resolver -vv
