#!/bin/bash
# Quick test script for GitHub Stats

echo "🧪 Testing GitHub Stats Script"
echo "================================"
echo ""

# Activate virtual environment
source venv/bin/activate

# Test with a small profile (GitHub's mascot)
echo "📊 Testing with @octocat profile..."
echo ""

# Create a simple test that doesn't require user input
python3 << 'EOF'
from github_stats import GitHubStats

print("🔍 Running automated test...")
print("")

# Test with octocat (GitHub's mascot - small profile)
analyzer = GitHubStats("octocat")

# Fetch profile
if analyzer.fetch_user_profile():
    print("✅ Profile fetch: SUCCESS")
    print(f"   Username: {analyzer.user_data.get('login')}")
    print(f"   Name: {analyzer.user_data.get('name')}")
    print(f"   Followers: {analyzer.user_data.get('followers')}")
else:
    print("❌ Profile fetch: FAILED")
    exit(1)

# Fetch repositories
if analyzer.fetch_repositories():
    print(f"✅ Repository fetch: SUCCESS ({len(analyzer.repos_data)} repos)")
else:
    print("⚠️  No repositories found")

# Calculate stats
analyzer.calculate_statistics()
print(f"✅ Statistics calculated")
print(f"   Total Stars: {analyzer.total_stars}")
print(f"   Total Forks: {analyzer.total_forks}")

print("")
print("🎉 All tests passed!")
print("")
print("📝 To run full analysis, use:")
print("   python github_stats.py octocat")

EOF

echo ""
echo "================================"
echo "✅ Test Complete!"
