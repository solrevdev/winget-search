# Winget Package Web Search

A simple web search for [microsoft/winget-pkgs](https://github.com/microsoft/winget-pkgs) with copy-paste friendly install commands.

## Features

- Search by package id or name.
- Copy `winget install -e --id` command for any package.
- Data auto-updated using GitHub Actions.

## Usage

1. Visit the site (hosted on GitHub Pages).
2. Type to search for a package (e.g. "chrome remote desktop").
3. Click "Copy" to copy the install command.

## Setup (for maintainers)

1. Fork or clone this repo.
2. Push to your own GitHub repo.
3. Enable "GitHub Pages" in repo settings, using the `gh-pages` branch.

The GitHub Action will:
- Clone microsoft/winget-pkgs
- Extract package info into `packages.json`
- Deploy the site and data to GitHub Pages!

## Credits

- Data: [microsoft/winget-pkgs](https://github.com/microsoft/winget-pkgs)
- Site template by [solrevdev](https://github.com/solrevdev)