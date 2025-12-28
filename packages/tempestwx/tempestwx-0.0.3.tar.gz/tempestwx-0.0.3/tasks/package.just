# run package tasks
[group('package')]
package: package-build

# build python package
[group('package')]
package-build: clean-build
	uv build --no-sources
