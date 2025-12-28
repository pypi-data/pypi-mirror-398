# Changelog

All notable changes to this project will be documented in this file.

## Version v1.0.1

- Markdown clean-up
- Code improvements and cleanup
- Ignore pylint messages that cannot be prevented
- :memo: Update URL to CHANGELOG in README
- :sparkles: Run ble2wled from inside a Docker container.
- :memo: Add Docker instructions to project documentation.
- :memo: Update docker documentation
- :memo: Update links in documentation
- :memo: Fix links in introduction page
- :memo: Add tested WLED version to documentation.
- Get correct code coverage report after adjusting module to be imported.
- :memo: Adding GitHub Actions & Coverage status badges to README.
- Add tested WLED version to README.
- :white_check_mark: New unit test for main function in main.py
- Add  coverage badge to sphinx documentation
- Move coverage badge to index page

## Version v1.0.0

- Add prerequisite section and links to ESPresense, HomeAssistant and WLED projects.
- Auto-generate changelog from commit messages.
- GitHub actions now use cache and don't build package multiple times.
- Correct bash syntax in release.yml
- Remove --identity-token from twine commands in release.yml
- Clean dist cache before building new package
- Change development status to stable
- Changed git-cliff changelog template
- Always checkout main
- Use github token to commit CHANGELOG back to main
- Remove git-cliff from github action

## Version v0.1.0

- add changelog and update documentation structure
- add changelog generation steps for main and tag pushes
- update README to include documentation link
