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

## Setup Instructions

### 1. Push to Main Branch

- Push your code and workflow to the main branch.
- The GitHub Actions workflow will run, generate `packages.json`, and deploy the site to the `gh-pages` branch (creating it if it doesn't exist).

### 2. Enable GitHub Pages on gh-pages Branch

- Go to your repository’s **Settings** > **Pages**.
- In the **Source** dropdown, select:
  - **Branch:** `gh-pages`
  - **Folder:** `/ (root)`
- Click **Save**.

- After saving, your GitHub Pages site will be published from the `gh-pages` branch at the root folder.

### 3. Wait for Deployment

- After the workflow runs and you configure Pages, your site will be live at the URL shown in the Pages settings.

## Credits

- Data: [microsoft/winget-pkgs](https://github.com/microsoft/winget-pkgs)
