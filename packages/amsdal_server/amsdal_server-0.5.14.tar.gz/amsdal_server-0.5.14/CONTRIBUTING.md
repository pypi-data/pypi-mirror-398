# Setup local env

## Setup python

1. setup uv:
```
curl -LsSf https://astral.sh/uv/install.sh | sh
```
Or upgrade if uv is already installed:
`uv self update`

2. Reload terminal/reconnect via ssh
3. Install python: `uv python install 3.12`
4. Pin python version: `uv python pin 3.12`

## Setup tools: Hatchling

1. `uv tool install hatch`
Note:
To upgrade hatch and other tools use: `uv tool upgrade --all`.

If you have installed hatch via other tools, make sure it's updated via:
`hatch self update`

## Create env
1. `hatch env prune` - to remove auto-created env
2. `hatch env create` - to create default
3. `hatch run sync` - to sync uv.lock
4. `hatch run lock-upgrade` - to upgrade uv.lock. Run it each new release of dependencies. 

# Release notes

The general flow is the following:

1. create a topic branch and make your changes there
2. run `hatch run change-logs create -c "Added a cool feature!" cool-feature.added.md`
3. It will create a `./release_notes/cool-feature.added.md` file. Do not forget to commit this file.
4. That's it.

These newly created change logs will be available on docs.amsdal.com in the next release.

Note, the `cool-feature.added.md` file name contains several parts separated by `.`:

1. `cool-feature` - the code of this change. Keep it short, simple, and unique.
2. `added` - it's a type of change. See all available types below.

The supported types of changes:

- `added`
- `removed`
- `changed`
- `deprecated`
- `security`
- `fixed`
- `performance`

For example, if your changes related to `performance` optimizations use `performance` type, e.g. 
`hatch run change-logs create -c "Optimized SQL JOIN statement."  sql-join.performance.md`

# Release

Before performing the release, you need to update the release version in the `__about__.py` file, which is located at `/src/amsdal/__about__.py`.

Next, you need to merge the latest changes into the main branch. To do release:

1. Switch to the `main` branch on your local computer.
2. Pull the latest changes from the remote repository.
3. Run the `release.sh` script located in the `scripts` folder.
4. When running the script, you need to specify the following arguments: the `release_date` and the new release version `release_version`.

Example:

``` bash
   bash ./scripts/release.sh 01-01-24 0.1.25
```
The script will perform the following actions:
1. Creates a new brunch in release/01-01-24 format.
2. Update the changelog.
3. Commit the changes and push.


After running the script, you need to create a pull request, review all changes, and then merge the `release branch` into the `main` branch. This action will trigger the CI/CD pipeline, which will check the version changes, create the necessary tags, and push them to the `main` branch. After that, CI/CD processes will be triggered to perform the release
