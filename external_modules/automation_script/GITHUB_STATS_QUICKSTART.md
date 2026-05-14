# GitHub Stats - Quick Start Guide

Get started with the GitHub Profile Statistics script in under 5 minutes!

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install requests
```

### 2. Run Your First Analysis

```bash
python github_stats.py torvalds
```

That's it! You'll see comprehensive statistics for Linus Torvalds' GitHub profile.

## 📊 What You'll See

The script displays:

- ✅ **Profile Info**: Name, bio, location, followers, following
- ✅ **Repository Stats**: Total repos, stars, forks, watchers
- ✅ **Top Repositories**: Most starred and forked projects
- ✅ **Languages**: Programming languages used with percentages
- ✅ **Insights**: License distribution, topics, repository features
- ✅ **Rate Limits**: API usage monitoring

## 🎯 Common Use Cases

### Analyze Your Own Profile

```bash
python github_stats.py YOUR_USERNAME
```

### Analyze Any Public Profile

```bash
python github_stats.py octocat
python github_stats.py gvanrossum
python github_stats.py dhh
```

### Export to JSON

```bash
python github_stats.py torvalds
# When prompted: Export statistics to JSON? (y/n): y
```

### Use with GitHub Token (Recommended)

Get higher rate limits (5,000 vs 60 requests/hour):

```bash
# Set token as environment variable
export GITHUB_TOKEN=ghp_your_token_here

# Run analysis
python github_stats.py torvalds
```

## 🔑 Getting a GitHub Token (Optional but Recommended)

1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Name it: "GitHub Stats Script"
4. No scopes needed for public data
5. Click "Generate token"
6. Copy the token

Then use it:

```bash
export GITHUB_TOKEN=ghp_your_token_here
python github_stats.py username
```

## 📝 Example Output

```
🚀 GITHUB PROFILE STATISTICS ANALYZER
======================================================================
Target: @torvalds
Time: 2024-01-15 10:30:00
======================================================================

⚡ API Rate Limit:
   Remaining: 59/60
   Resets at: 11:30:00

🔍 Fetching profile for @torvalds...
✅ Profile data fetched successfully
📦 Fetching repositories...
   Fetched page 1 (6 repos)
✅ Total repositories fetched: 6

======================================================================
👤 GITHUB PROFILE: @torvalds
======================================================================

📋 Basic Information:
   Name: Linus Torvalds
   Location: Portland, OR
   Company: Linux Foundation
   Followers: 185,234
   Following: 0
   Public Repos: 6

📊 Overall Stats:
   Total Repositories: 6
   Total Stars Received: ⭐ 175,432
   Total Forks: 🍴 51,234

🔤 PROGRAMMING LANGUAGES
   1. C                     ████████████████████████████████ 85.34%
   2. Assembly              ████                              8.23%
   3. Shell                 ██                                3.45%
```

## 🎓 Try the Examples

Run the example script to see different usage patterns:

```bash
python github_stats_example.py
```

Choose from:
1. Basic Usage
2. With Token
3. Export to JSON
4. Custom Analysis
5. Compare Users
6. Language Focus

## ⚡ Performance Tips

- **Use a token**: 83x faster rate limits
- **Small profiles** (< 10 repos): ~10 seconds
- **Large profiles** (100+ repos): 2-5 minutes
- **Very large profiles** (500+ repos): 10-20 minutes

## 🛠️ Troubleshooting

### "Rate limit exceeded"
```bash
# Wait 1 hour or use a token
export GITHUB_TOKEN=your_token
python github_stats.py username
```

### "User not found"
- Check spelling of username
- Ensure profile is public

### "Timeout error"
- Check internet connection
- Try again later

## 📚 Full Documentation

For complete documentation, see: `github_stats_README.md`

## 🎯 Next Steps

1. ✅ Analyze your own profile
2. ✅ Get a GitHub token for better performance
3. ✅ Export statistics to JSON
4. ✅ Try the example scripts
5. ✅ Compare multiple users

## 💡 Pro Tips

- **Automate**: Add to cron for daily stats
- **Compare**: Analyze multiple profiles to compare
- **Export**: Save JSON for historical tracking
- **Token**: Always use a token for large profiles
- **Monitor**: Watch your rate limits

## 🤝 Need Help?

- Read the full README: `github_stats_README.md`
- Check examples: `github_stats_example.py`
- Review the code: `github_stats.py`

---

**Happy Analyzing! 🚀**
