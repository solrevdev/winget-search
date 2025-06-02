## Summary

This project provides a fast, searchable web interface for Windows Package Manager (winget) packages. It uses GitHub Actions to:

1. Automatically extract package data daily from the official winget repository
2. Build a static site with the latest package information
3. Deploy directly to GitHub Pages without any manual configuration

The entire process is automated - just push your code and GitHub Actions handles everything else!# Winget Package Web Search

A fast, modern web search interface for [Windows Package Manager (winget)](https://github.com/microsoft/winget-pkgs) packages with instant copy-to-clipboard installation commands.

## Features

- 🔍 **Instant search** - Search by package ID, name, description, publisher, or tags
- 📋 **One-click copy** - Copy `winget install` commands instantly
- 🌐 **English-only results** - Filters to show only English package descriptions
- 🔄 **Auto-updated** - Daily updates via GitHub Actions
- 🌓 **Dark mode** - Automatic theme based on system preferences
- 📱 **Mobile-friendly** - Responsive design for all devices
- ⚡ **Fast & lightweight** - No frameworks, pure vanilla JavaScript
- ⌨️ **Keyboard shortcuts** - Press `/` to search, `Esc` to clear

## Live Demo

Visit the live site: `https://YOUR_USERNAME.github.io/YOUR_REPO_NAME/`

## How It Works

1. **Data Extraction**: GitHub Actions runs daily to:
   - Clone the official [microsoft/winget-pkgs](https://github.com/microsoft/winget-pkgs) repository
   - Parse all YAML manifest files
   - Extract package metadata (filtering for English descriptions)
   - Generate a `packages.json` file with the latest versions only

2. **Search Interface**: A static HTML page that:
   - Loads the generated `packages.json`
   - Provides instant client-side search
   - Generates copy-ready `winget install` commands

3. **Deployment**: The GitHub Actions workflow:
   - Builds the site and generates `packages.json`
   - Deploys directly to GitHub Pages using the `peaceiris/actions-gh-pages` action
   - GitHub Pages automatically serves the site from the deployment
   - No manual branch management needed - it's all automated!

## Setup Instructions

### Prerequisites

- A GitHub account
- A repository for this project

### Installation

1. **Fork or clone this repository**

2. **Update the repository references**:
   - In `index.html`, replace `YOUR_USERNAME/YOUR_REPO_NAME` with your actual GitHub username and repository name
   - This appears in the footer link

3. **Enable GitHub Actions**:
   - Go to your repository's **Settings** > **Actions** > **General**
   - Under "Actions permissions", select "Allow all actions and reusable workflows"
   - Under "Workflow permissions", select "Read and write permissions"
   - **Note**: No personal access token needed! The workflow uses GitHub's built-in `GITHUB_TOKEN`

4. **Push to main branch**:
   ```bash
   git add .
   git commit -m "Initial setup"
   git push origin main
   ```

5. **Wait for the first build**:
   - Go to the **Actions** tab in your repository
   - You should see the "Build and Deploy" workflow running
   - This first run will take a few minutes as it processes ~30,000+ packages

6. **GitHub Pages will be automatically configured**:
   - The workflow handles everything automatically
   - Once the workflow completes, go to **Settings** > **Pages**
   - You should see "Your site is live at https://YOUR_USERNAME.github.io/YOUR_REPO_NAME/"
   - Under "Build and deployment" > "Source", it will show **GitHub Actions**
   - No manual configuration needed!

7. **Access your site**:
   - Your site will be available at `https://YOUR_USERNAME.github.io/YOUR_REPO_NAME/`
   - It may take a few minutes for GitHub Pages to activate after the first deployment

## Customization

### Modify Search Behavior

Edit the `showResults()` function in `index.html` to customize search logic:

```javascript
// Current implementation searches in:
// - Package ID
// - Package name  
// - Description
// - Publisher
// - Tags
```

### Change Update Schedule

Edit `.github/workflows/github_workflows_build.yml` to modify the update schedule:

```yaml
schedule:
    # Run at different time (e.g., every 6 hours)
    - cron: '0 */6 * * *'
```

### Styling

The site uses CSS custom properties for theming. Modify the `:root` variables in `index.html` to customize colors.

## Development

### Local Testing

You can test locally using either traditional pip or modern uv (recommended).

#### Option 1: Using uv (Recommended)

[uv](https://github.com/astral-sh/uv) is a fast, modern Python package manager. If you have it installed:

```bash
# Clone winget-pkgs repository first (this will take a few minutes - it's a large repo)
git clone --depth 1 https://github.com/microsoft/winget-pkgs.git

# Run the extraction script with uv (creates isolated environment automatically)
# This uses Python 3.11 as specified in .python-version
uv run extract_packages.py winget-pkgs/manifests/ packages.json

# The extraction will take a few minutes and show progress:
# Total manifest YAML files found: XXXXX
# Total valid packages found: XXXXX
# Unique packages extracted: XXXXX

# Serve the site locally
uv run python -m http.server 8000
# or just use Python directly if you have it
python3 -m http.server 8000

# Visit http://localhost:8000 in your browser
```

For a one-time run without creating a virtual environment:
```bash
# Run extraction with inline dependencies
uvx --with pyyaml --with packaging --python 3.11 \
  python extract_packages.py winget-pkgs/manifests/ packages.json
```

#### Option 2: Using pip with virtual environment

```bash
# Create a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Clone winget-pkgs repository
git clone https://github.com/microsoft/winget-pkgs.git

# Run extraction
python extract_packages.py winget-pkgs/manifests/ packages.json

# Serve locally
python -m http.server 8000
```

#### Option 3: Using pip globally (not recommended)

```bash
# Install Python dependencies
pip install -r requirements.txt

# Clone winget-pkgs and run extraction
git clone https://github.com/microsoft/winget-pkgs.git
python extract_packages.py winget-pkgs/manifests/ packages.json

# Serve locally
python -m http.server 8000
```

After starting the server, open `http://localhost:8000` in your browser.

### Project Structure

```
├── .github/
│   └── workflows/
│       ├── github_workflows_build.yml    # Main build workflow (automated deployment)
│       └── github_workflows_pages_deploy.yml  # Manual trigger for re-deployment
├── extract_packages.py    # Package extraction script
├── index.html            # Search interface
├── packages.json         # Generated package data (not in source)
├── requirements.txt      # Python dependencies (pip)
├── pyproject.toml        # Modern Python project config (uv)
├── .python-version       # Python version for uv
├── LICENSE              # MIT License
└── README.md            # This file
```

**Note about workflows**: The main workflow (`github_workflows_build.yml`) handles everything automatically. The second workflow (`github_workflows_pages_deploy.yml`) is just a utility for forcing a re-deployment if ever needed.

## Technical Details

### Package Extraction

The extraction script (`extract_packages.py`):
- Parses winget manifest YAML files
- Filters for English-only descriptions (`.locale.en-US.yaml` files)
- Deduplicates packages, keeping only the latest version
- Uses proper semantic versioning comparison
- Outputs a structured JSON with metadata

### Performance

- Initial load: ~5-10MB JSON file containing ~30,000+ packages
- Search is performed client-side for instant results
- Results are limited to 100 items for performance
- Debounced search input (300ms) for smooth typing

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Ideas for Improvement

- Add package categories/sections
- Implement fuzzy search
- Add sorting options (by name, downloads, date)
- Show package icons/logos
- Add "copy as PowerShell" option
- Implement package details modal
- Add search history
- Export search results

## Summary

This project provides a fast, searchable web interface for Windows Package Manager (winget) packages. It uses GitHub Actions to:

1. Automatically extract package data daily from the official winget repository
2. Build a static site with the latest package information  
3. Deploy directly to GitHub Pages without any manual configuration

The entire process is automated - just push your code and GitHub Actions handles everything else!

## License

This project is open source and available under the [MIT License](LICENSE).

## Credits

- Package data from [microsoft/winget-pkgs](https://github.com/microsoft/winget-pkgs)
- Automated deployment using [GitHub Actions](https://github.com/features/actions) and [GitHub Pages](https://pages.github.com/)
- [peaceiris/actions-gh-pages](https://github.com/peaceiris/actions-gh-pages) for seamless deployment

## Troubleshooting

### GitHub Pages not updating (shows old content)

This is a common issue, especially with custom domains. Try these solutions:

1. **Check GitHub Pages status**:
   - Go to Settings > Pages
   - Look for "Your site is live at..." message
   - Check the "Last deployed" timestamp
   - If it's old, the deployment isn't being detected

2. **Force a rebuild**:
   - Run the "Trigger Pages Deploy" workflow manually from the Actions tab
   - Or make a small change to any file in the gh-pages branch

3. **Clear CDN cache** (for custom domains):
   - Custom domains use GitHub's CDN which can cache aggressively
   - Wait 10-15 minutes for cache to expire
   - Try accessing with `?v=timestamp` to bypass cache: `https://yourdomain.com/winget-search/?v=123`

4. **Check deployment source**:
   - In Settings > Pages, try switching between "Deploy from branch" and "GitHub Actions"
   - If using "Deploy from branch", ensure it's set to `gh-pages` branch and `/ (root)`

5. **Verify files in gh-pages branch**:
   - Check that the new files are actually in the gh-pages branch
   - Look for the `:root` CSS variables in index.html
   - Ensure there's a `.nojekyll` file (prevents Jekyll processing)

6. **Browser cache**:
   - Hard refresh: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
   - Open in incognito/private mode
   - Check browser DevTools > Network tab with "Disable cache" checked

### GitHub Pages not showing or wrong deployment source

- The workflow automatically configures GitHub Pages to use "GitHub Actions" as the source
- If Pages shows "Deploy from a branch" instead, the site should still work
- You can manually switch to "GitHub Actions" if needed, but it's not required
- The `peaceiris/actions-gh-pages@v4` action handles the deployment regardless of the Pages setting

### Python version mismatch

- The project uses Python 3.11 (as specified in `.python-version` and GitHub Actions)
- If you have a different Python version locally, `uv` will automatically download and use Python 3.11
- If you prefer to use your system Python (3.12+), it should work fine, but test thoroughly

### Build fails with "packages.json not created"

- Check the Python error output in the Actions log
- Ensure the winget-pkgs repository structure hasn't changed

### Site shows "Failed to load package data"

- Check if the GitHub Actions workflow completed successfully
- Verify that GitHub Pages is enabled (Settings > Pages)
- Check that the site URL is correct: `https://YOUR_USERNAME.github.io/YOUR_REPO_NAME/`
- Look at the browser console for any errors
- The workflow creates everything automatically, so no manual branch management is needed

### Search returns no results

- Open browser console and check for JavaScript errors
- Verify `packages.json` is loading correctly
- Check if the JSON structure matches what the JavaScript expects

### Updates not reflecting

- The workflow runs daily at 2 AM UTC
- You can manually trigger it from the Actions tab using "Run workflow"
- Check the workflow run logs for any errors