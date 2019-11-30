.PHONY: test deploy-docs

dist: graphene_resolver/* pyproject.toml
	poetry build

docs/_build/html/.git:
	git worktree add -f --checkout docs/_build/html gh-pages
	
docs: docs/* docs/_build/html/.git
	poetry run $(MAKE) -C docs html

test:
	poetry run pytest --cov=graphene_resolver -vv

deploy-docs: docs
	cd docs/_build/html ; git add --all && git commit -m 'docs: build' -m '[skip ci]' && git push
