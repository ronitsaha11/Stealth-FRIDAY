# GitHub Profile Statistics Automation Script

A comprehensive Python automation script that fetches and displays detailed statistics for any GitHub profile using the GitHub REST API.

## Features

### 📊 Comprehensive Statistics

- **Profile Information**: Name, bio, location, company, social links
- **Account Details**: Creation date, account age, last update
- **Social Stats**: Followers, following, public repos, gists
- **Repository Statistics**: Total repos, stars, forks, watchers, size
- **Language Analysis**: Programming languages used with percentage distribution
- **Top Repositories**: Most starred and most forked projects
- **Recent Activity**: Recently updated repositories
- **License Distribution**: Analysis of licenses used across repositories
- **Topics Analysis**: Most common repository topics
- **Repository Features**: Issues, wiki, projects, downloads enabled

### 🚀 Key Capabilities

- ✅ Fetches all public repositories (handles pagination automatically)
- ✅ Analyzes programming languages across all repositories
- ✅ Calculates comprehensive statistics
- ✅ Beautiful formatted console output
- ✅ JSON export functionality
- ✅ Rate limit monitoring
- ✅ GitHub Personal Access Token support for higher rate limits
- ✅ Error handling and timeout protection

## Installation

### Prerequisites

- Python 3.6 or higher
- `requests` library

### Install Dependencies

```bash
pip install requests
```

Or if you're using the project's requirements.txt:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python github_stats.py <username>
```

Example:
```bash
python github_stats.py torvalds
```

### With GitHub Token (Recommended)

Using a GitHub Personal Access Token increases your API rate limit from 60 to 5,000 requests per hour.

```bash
python github_stats.py <username> <github_token>
```

Example:
```bash
python github_stats.py torvalds ghp_your_token_here
```

### Using Environment Variable

Set your GitHub token as an environment variable:

```bash
export GITHUB_TOKEN=ghp_your_token_here
python github_stats.py <username>
```

### Export to JSON

Export all statistics to a JSON file:

```bash
python github_stats.py <username> <token> --export
```

Or you'll be prompted during execution:
```
Export statistics to JSON? (y/n): y
```

### Interactive Mode

Run without arguments to be prompted for username:

```bash
python github_stats.py
```

## Output Examples

### Profile Information
```
👤 GITHUB PROFILE: @torvalds
======================================================================

📋 Basic Information:
   Name: Linus Torvalds
   Bio: N/A
   Company: Linux Foundation
   Location: Portland, OR
   Email: N/A
   Blog: N/A
   Twitter: N/A

📅 Account Details:
   Created: September 03, 2011
   Updated: January 15, 2024
   Account Age: 4512 days (12 years)

👥 Social Stats:
   Followers: 185,234
   Following: 0
   Public Repos: 6
   Public Gists: 0
```

### Repository Statistics
```
📦 REPOSITORY STATISTICS
======================================================================

📊 Overall Stats:
   Total Repositories: 6
   Total Stars Received: ⭐ 175,432
   Total Forks: 🍴 51,234
   Total Watchers: 👁️  175,432
   Total Size: 1,234.56 MB

📂 Repository Types:
   Public: 6
   Original: 5
   Forked: 1
   Archived: 0

⭐ Top 10 Most Starred Repositories:
    1. linux                          ⭐ 150,000
    2. subsurface                     ⭐ 2,345
    3. test-tlb                       ⭐ 234
```

### Language Distribution
```
🔤 PROGRAMMING LANGUAGES
======================================================================

📊 Language Distribution:
    1. C                     ████████████████████████████████████████ 85.34%
    2. Assembly              ████                                      8.23%
    3. Shell                 ██                                        3.45%
    4. Makefile              █                                         2.12%
    5. Python                                                          0.86%

   Total Languages Used: 12
```

### Contribution Insights
```
💡 CONTRIBUTION INSIGHTS
======================================================================

📜 License Distribution:
   GPL-2.0                        3 repos
   MIT                            2 repos
   No License                     1 repos

🏷️  Top 15 Repository Topics:
    1. linux                           2 repos
    2. kernel                          2 repos
    3. operating-system                1 repos

⚙️  Repository Features:
   Issues Enabled: 5 repos
   Wiki Enabled: 3 repos
   Projects Enabled: 2 repos
   Downloads Enabled: 6 repos
```

## GitHub Personal Access Token

### Why Use a Token?

- **Higher Rate Limits**: 5,000 requests/hour vs 60 requests/hour
- **Access to More Data**: Some endpoints require authentication
- **Better Performance**: Faster analysis for users with many repositories

### How to Create a Token

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Give it a descriptive name (e.g., "GitHub Stats Script")
4. Select scopes: `public_repo` (or just leave all unchecked for public data only)
5. Click "Generate token"
6. Copy the token (you won't see it again!)

### Security Best Practices

- ⚠️ **Never commit tokens to version control**
- ✅ Use environment variables: `export GITHUB_TOKEN=your_token`
- ✅ Use `.env` files (add to `.gitignore`)
- ✅ Rotate tokens regularly
- ✅ Use tokens with minimal required scopes

## JSON Export Format

The exported JSON file contains:

```json
{
  "username": "torvalds",
  "generated_at": "2024-01-15T10:30:00",
  "profile": { ... },
  "statistics": {
    "total_repos": 6,
    "total_stars": 175432,
    "total_forks": 51234,
    "total_watchers": 175432,
    "total_size_kb": 1234567
  },
  "languages": {
    "C": 12345678,
    "Assembly": 987654,
    ...
  },
  "repositories": [ ... ]
}
```

## API Rate Limits

### Without Token
- **Limit**: 60 requests per hour
- **Suitable for**: Small profiles (< 10 repositories)

### With Token
- **Limit**: 5,000 requests per hour
- **Suitable for**: Any profile size

### Rate Limit Monitoring

The script automatically checks and displays your current rate limit:

```
⚡ API Rate Limit:
   Remaining: 4,987/5,000
   Resets at: 14:30:00
```

## Error Handling

The script handles various error scenarios:

- ❌ Invalid username
- ❌ Network timeouts
- ❌ API rate limit exceeded
- ❌ Repository access errors
- ❌ JSON export failures

## Performance

### Typical Analysis Times

- **Small profile** (< 10 repos): 5-15 seconds
- **Medium profile** (10-50 repos): 30-60 seconds
- **Large profile** (50-200 repos): 2-5 minutes
- **Very large profile** (200+ repos): 5-15 minutes

*Times vary based on network speed and API rate limits*

## Limitations

- Only fetches **public** repositories
- Cannot access private repositories (even with token)
- Contribution graph data not available via REST API
- Some statistics may be cached by GitHub

## Troubleshooting

### Rate Limit Exceeded

```bash
# Wait for rate limit to reset or use a token
export GITHUB_TOKEN=your_token_here
python github_stats.py username
```

### Timeout Errors

- Check your internet connection
- Try again later
- Use a token to reduce the number of requests needed

### User Not Found

- Verify the username is correct
- Check if the profile is public

## Advanced Usage

### Analyze Multiple Users

```bash
#!/bin/bash
for user in torvalds gvanrossum dhh; do
    python github_stats.py $user $GITHUB_TOKEN --export
    sleep 5
done
```

### Automated Reporting

```bash
# Daily stats report
0 9 * * * cd /path/to/script && python github_stats.py myusername $GITHUB_TOKEN --export
```

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## License

This script is provided as-is for educational and personal use.

## Related Scripts

- `simple_url_opener.py` - URL automation script
- `system_info.py` - System information gathering
- `nmap_network_scanner.py` - Network scanning automation

## Author

Part of the Automation-Script collection

## Changelog

### Version 1.0.0
- Initial release
- Full profile statistics
- Repository analysis
- Language distribution
- JSON export
- Rate limit monitoring
