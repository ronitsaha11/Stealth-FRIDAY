#!/usr/bin/env python3
"""
GitHub Stats - Example Usage
Demonstrates different ways to use the GitHubStats class
"""

from github_stats import GitHubStats
import os

def example_basic_usage():
    """Example 1: Basic usage without token"""
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Basic Usage (No Token)")
    print("=" * 70)
    
    username = "torvalds"  # Example: Linus Torvalds
    analyzer = GitHubStats(username)
    analyzer.run_full_analysis(export_json=False)


def example_with_token():
    """Example 2: Using GitHub token for higher rate limits"""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Using GitHub Token")
    print("=" * 70)
    
    username = "gvanrossum"  # Example: Guido van Rossum
    token = os.environ.get('GITHUB_TOKEN')  # Get token from environment
    
    if not token:
        print("⚠️  No GITHUB_TOKEN found in environment variables")
        print("   Set it with: export GITHUB_TOKEN=your_token_here")
        return
    
    analyzer = GitHubStats(username, token)
    analyzer.run_full_analysis(export_json=False)


def example_with_export():
    """Example 3: Export statistics to JSON"""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Export to JSON")
    print("=" * 70)
    
    username = "dhh"  # Example: David Heinemeier Hansson
    token = os.environ.get('GITHUB_TOKEN')
    
    analyzer = GitHubStats(username, token)
    analyzer.run_full_analysis(export_json=True)


def example_custom_analysis():
    """Example 4: Custom analysis - fetch specific data only"""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Custom Analysis")
    print("=" * 70)
    
    username = "octocat"  # GitHub's mascot account
    token = os.environ.get('GITHUB_TOKEN')
    
    analyzer = GitHubStats(username, token)
    
    # Fetch only profile and repositories
    if analyzer.fetch_user_profile():
        analyzer.fetch_repositories()
        analyzer.calculate_statistics()
        
        # Display only specific sections
        analyzer.display_profile_info()
        analyzer.display_repository_stats()
        
        # Custom output
        print(f"\n📊 Quick Summary:")
        print(f"   Username: @{username}")
        print(f"   Total Stars: ⭐ {analyzer.total_stars:,}")
        print(f"   Total Repos: 📦 {len(analyzer.repos_data):,}")


def example_compare_users():
    """Example 5: Compare multiple users"""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Compare Multiple Users")
    print("=" * 70)
    
    usernames = ["torvalds", "gvanrossum", "dhh"]
    token = os.environ.get('GITHUB_TOKEN')
    
    results = []
    
    for username in usernames:
        print(f"\n🔍 Analyzing @{username}...")
        analyzer = GitHubStats(username, token)
        
        if analyzer.fetch_user_profile() and analyzer.fetch_repositories():
            analyzer.calculate_statistics()
            results.append({
                'username': username,
                'followers': analyzer.user_data.get('followers', 0),
                'repos': len(analyzer.repos_data),
                'stars': analyzer.total_stars,
                'forks': analyzer.total_forks
            })
    
    # Display comparison
    print("\n" + "=" * 70)
    print("📊 COMPARISON RESULTS")
    print("=" * 70)
    print(f"\n{'Username':<20} {'Followers':<12} {'Repos':<10} {'Stars':<12} {'Forks':<10}")
    print("-" * 70)
    
    for result in results:
        print(f"{result['username']:<20} {result['followers']:<12,} {result['repos']:<10,} "
              f"{result['stars']:<12,} {result['forks']:<10,}")


def example_language_focus():
    """Example 6: Focus on language statistics"""
    print("\n" + "=" * 70)
    print("EXAMPLE 6: Language-Focused Analysis")
    print("=" * 70)
    
    username = "sindresorhus"  # Known for JavaScript projects
    token = os.environ.get('GITHUB_TOKEN')
    
    analyzer = GitHubStats(username, token)
    
    if analyzer.fetch_user_profile() and analyzer.fetch_repositories():
        analyzer.fetch_repository_languages()
        
        # Display only language stats
        analyzer.display_language_stats()
        
        # Additional custom language analysis
        if analyzer.languages:
            print(f"\n🎯 Language Insights:")
            total_bytes = sum(analyzer.languages.values())
            primary_lang = analyzer.languages.most_common(1)[0]
            print(f"   Primary Language: {primary_lang[0]}")
            print(f"   Language Diversity: {len(analyzer.languages)} languages")
            print(f"   Total Code Size: {total_bytes / 1024 / 1024:.2f} MB")


def main():
    """Run all examples"""
    print("🚀 GitHub Stats - Example Usage Demonstrations")
    print("=" * 70)
    print("\nThis script demonstrates various ways to use the GitHubStats class")
    print("\n💡 Tip: Set GITHUB_TOKEN environment variable for better results:")
    print("   export GITHUB_TOKEN=your_token_here")
    
    examples = [
        ("Basic Usage", example_basic_usage),
        ("With Token", example_with_token),
        ("Export to JSON", example_with_export),
        ("Custom Analysis", example_custom_analysis),
        ("Compare Users", example_compare_users),
        ("Language Focus", example_language_focus)
    ]
    
    print("\n📋 Available Examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"   {i}. {name}")
    
    print("\n" + "=" * 70)
    choice = input("\nSelect example to run (1-6, or 'all' for all examples): ").strip()
    
    if choice.lower() == 'all':
        for name, func in examples:
            try:
                func()
                input("\nPress Enter to continue to next example...")
            except KeyboardInterrupt:
                print("\n\n⚠️  Skipping to next example...")
            except Exception as e:
                print(f"\n❌ Error in {name}: {e}")
    elif choice.isdigit() and 1 <= int(choice) <= len(examples):
        name, func = examples[int(choice) - 1]
        try:
            func()
        except Exception as e:
            print(f"\n❌ Error: {e}")
    else:
        print("❌ Invalid choice")


if __name__ == "__main__":
    main()
