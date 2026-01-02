push:
	sed -i '' '3s/.*/version = "$(version)"/' pyproject.toml
	python3 -m build
	python3 -m twine upload --repository pypi dist/techtrash_musubitraining-$(version)*