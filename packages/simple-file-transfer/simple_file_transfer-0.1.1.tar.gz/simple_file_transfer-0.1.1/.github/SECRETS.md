# GitHub Secrets Configuration

To enable the full CI/CD pipeline, you need to configure the following secrets in your GitHub repository settings.

## Required Secrets

### For PyPI Publishing

1. **`PYPI_API_TOKEN`** (Required for release workflow)
   - Go to https://pypi.org/manage/account/token/
   - Create a new API token
   - Scope: "Entire account" or specific to this project
   - Copy the token (starts with `pypi-`)
   - Add to GitHub: Settings → Secrets and variables → Actions → New repository secret
   - Name: `PYPI_API_TOKEN`
   - Value: Your PyPI token

### For Docker Hub Publishing (Optional)

2. **`DOCKER_USERNAME`** (Optional - for Docker image publishing)
   - Your Docker Hub username
   - Add to GitHub secrets

3. **`DOCKER_PASSWORD`** (Optional - for Docker image publishing)
   - Your Docker Hub password or access token
   - Recommended: Use an access token instead of password
   - Create token at: https://hub.docker.com/settings/security
   - Add to GitHub secrets

## How to Add Secrets

1. Go to your GitHub repository
2. Click on **Settings**
3. In the left sidebar, click **Secrets and variables** → **Actions**
4. Click **New repository secret**
5. Enter the secret name and value
6. Click **Add secret**

## Testing Without Secrets

If you don't want to publish to PyPI or Docker Hub yet:

1. The **CI workflow** will run without any secrets (tests, linting, Docker build)
2. The **Release workflow** will fail at the publishing steps without secrets
3. You can comment out the `build-and-publish` and `docker-publish` jobs in `.github/workflows/release.yml` to test version bumping only

## Security Notes

- Never commit secrets to your repository
- Use GitHub secrets for sensitive data
- Rotate tokens periodically
- Use scoped tokens when possible (project-specific instead of account-wide)
- For Docker, prefer access tokens over passwords

## Workflow Permissions

Make sure your GitHub Actions have the necessary permissions:

1. Go to Settings → Actions → General
2. Under "Workflow permissions", select:
   - ✅ Read and write permissions
   - ✅ Allow GitHub Actions to create and approve pull requests

This allows the release workflow to push version bump commits and create tags.
