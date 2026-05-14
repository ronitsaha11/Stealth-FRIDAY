#!/usr/bin/env python3
"""
GitHub Profile Statistics Automation Script
Fetches and displays comprehensive statistics for any GitHub profile
"""

import requests
import json
import sys
from datetime import datetime
from collections import Counter
import time

class GitHubStats:
    def __init__(self, username, token=None):
        """
        Initialize GitHub Stats fetcher
        
        Args:
            username (str): GitHub username
            token (str, optional): GitHub Personal Access Token for higher rate limits
        """
        self.username = username
        self.token = token
        self.base_url = "https://api.github.com"
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
        }
        if token:
            self.headers['Authorization'] = f'token {token}'
        
        self.user_data = None
        self.repos_data = []
        self.languages = Counter()
        self.total_stars = 0
        self.total_forks = 0
        self.total_watchers = 0
        self.total_size = 0
    
    def fetch_user_profile(self):
        """Fetch basic user profile information"""
        print(f"🔍 Fetching profile for @{self.username}...")
        
        url = f"{self.base_url}/users/{self.username}"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            self.user_data = response.json()
            print("✅ Profile data fetched successfully")
            return True
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching user profile: {e}")
            return False
    
    def fetch_repositories(self):
        """Fetch all repositories for the user"""
        print(f"📦 Fetching repositories...")
        
        page = 1
        per_page = 100
        
        while True:
            url = f"{self.base_url}/users/{self.username}/repos"
            params = {
                'page': page,
                'per_page': per_page,
                'sort': 'updated',
                'direction': 'desc'
            }
            
            try:
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
                response.raise_for_status()
                repos = response.json()
                
                if not repos:
                    break
                
                self.repos_data.extend(repos)
                print(f"   Fetched page {page} ({len(repos)} repos)")
                page += 1
                
                # Respect rate limits
                time.sleep(0.5)
                
            except requests.exceptions.RequestException as e:
                print(f"❌ Error fetching repositories: {e}")
                break
        
        print(f"✅ Total repositories fetched: {len(self.repos_data)}")
        return len(self.repos_data) > 0
    
    def fetch_repository_languages(self):
        """Fetch languages used across all repositories"""
        print(f"🔤 Analyzing languages used...")
        
        for i, repo in enumerate(self.repos_data, 1):
            if i % 10 == 0:
                print(f"   Analyzed {i}/{len(self.repos_data)} repositories")
            
            url = repo['languages_url']
            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()
                languages = response.json()
                
                for lang, bytes_count in languages.items():
                    self.languages[lang] += bytes_count
                
                # Respect rate limits
                time.sleep(0.3)
                
            except requests.exceptions.RequestException:
                continue
        
        print(f"✅ Language analysis complete")
    
    def calculate_statistics(self):
        """Calculate various statistics from repository data"""
        print(f"📊 Calculating statistics...")
        
        for repo in self.repos_data:
            self.total_stars += repo.get('stargazers_count', 0)
            self.total_forks += repo.get('forks_count', 0)
            self.total_watchers += repo.get('watchers_count', 0)
            self.total_size += repo.get('size', 0)
        
        print(f"✅ Statistics calculated")
    
    def display_profile_info(self):
        """Display basic profile information"""
        if not self.user_data:
            return
        
        print("\n" + "=" * 70)
        print(f"👤 GITHUB PROFILE: @{self.username}")
        print("=" * 70)
        
        print(f"\n📋 Basic Information:")
        print(f"   Name: {self.user_data.get('name', 'N/A')}")
        print(f"   Bio: {self.user_data.get('bio', 'N/A')}")
        print(f"   Company: {self.user_data.get('company', 'N/A')}")
        print(f"   Location: {self.user_data.get('location', 'N/A')}")
        print(f"   Email: {self.user_data.get('email', 'N/A')}")
        print(f"   Blog: {self.user_data.get('blog', 'N/A')}")
        print(f"   Twitter: {self.user_data.get('twitter_username', 'N/A')}")
        
        print(f"\n📅 Account Details:")
        created_at = datetime.strptime(self.user_data['created_at'], '%Y-%m-%dT%H:%M:%SZ')
        updated_at = datetime.strptime(self.user_data['updated_at'], '%Y-%m-%dT%H:%M:%SZ')
        account_age = (datetime.now() - created_at).days
        
        print(f"   Created: {created_at.strftime('%B %d, %Y')}")
        print(f"   Updated: {updated_at.strftime('%B %d, %Y')}")
        print(f"   Account Age: {account_age} days ({account_age // 365} years)")
        
        print(f"\n👥 Social Stats:")
        print(f"   Followers: {self.user_data.get('followers', 0):,}")
        print(f"   Following: {self.user_data.get('following', 0):,}")
        print(f"   Public Repos: {self.user_data.get('public_repos', 0):,}")
        print(f"   Public Gists: {self.user_data.get('public_gists', 0):,}")
    
    def display_repository_stats(self):
        """Display repository statistics"""
        if not self.repos_data:
            return
        
        print("\n" + "=" * 70)
        print("📦 REPOSITORY STATISTICS")
        print("=" * 70)
        
        print(f"\n📊 Overall Stats:")
        print(f"   Total Repositories: {len(self.repos_data):,}")
        print(f"   Total Stars Received: ⭐ {self.total_stars:,}")
        print(f"   Total Forks: 🍴 {self.total_forks:,}")
        print(f"   Total Watchers: 👁️  {self.total_watchers:,}")
        print(f"   Total Size: {self.total_size / 1024:.2f} MB")
        
        # Repository types
        public_repos = sum(1 for repo in self.repos_data if not repo.get('private', False))
        forked_repos = sum(1 for repo in self.repos_data if repo.get('fork', False))
        original_repos = len(self.repos_data) - forked_repos
        archived_repos = sum(1 for repo in self.repos_data if repo.get('archived', False))
        
        print(f"\n📂 Repository Types:")
        print(f"   Public: {public_repos:,}")
        print(f"   Original: {original_repos:,}")
        print(f"   Forked: {forked_repos:,}")
        print(f"   Archived: {archived_repos:,}")
        
        # Top repositories by stars
        top_starred = sorted(self.repos_data, key=lambda x: x.get('stargazers_count', 0), reverse=True)[:10]
        
        if top_starred and top_starred[0].get('stargazers_count', 0) > 0:
            print(f"\n⭐ Top 10 Most Starred Repositories:")
            for i, repo in enumerate(top_starred, 1):
                stars = repo.get('stargazers_count', 0)
                if stars > 0:
                    print(f"   {i:2d}. {repo['name']:<30} ⭐ {stars:,}")
        
        # Most forked repositories
        top_forked = sorted(self.repos_data, key=lambda x: x.get('forks_count', 0), reverse=True)[:5]
        
        if top_forked and top_forked[0].get('forks_count', 0) > 0:
            print(f"\n🍴 Top 5 Most Forked Repositories:")
            for i, repo in enumerate(top_forked, 1):
                forks = repo.get('forks_count', 0)
                if forks > 0:
                    print(f"   {i}. {repo['name']:<30} 🍴 {forks:,}")
        
        # Recently updated repositories
        recent_repos = sorted(self.repos_data, key=lambda x: x.get('updated_at', ''), reverse=True)[:5]
        
        print(f"\n🔄 Recently Updated Repositories:")
        for i, repo in enumerate(recent_repos, 1):
            updated = datetime.strptime(repo['updated_at'], '%Y-%m-%dT%H:%M:%SZ')
            days_ago = (datetime.now() - updated).days
            print(f"   {i}. {repo['name']:<30} ({days_ago} days ago)")
    
    def display_language_stats(self):
        """Display programming language statistics"""
        if not self.languages:
            return
        
        print("\n" + "=" * 70)
        print("🔤 PROGRAMMING LANGUAGES")
        print("=" * 70)
        
        total_bytes = sum(self.languages.values())
        
        print(f"\n📊 Language Distribution:")
        
        # Sort languages by usage
        sorted_languages = self.languages.most_common(15)
        
        for i, (lang, bytes_count) in enumerate(sorted_languages, 1):
            percentage = (bytes_count / total_bytes) * 100
            bar_length = int(percentage / 2)
            bar = '█' * bar_length
            print(f"   {i:2d}. {lang:<20} {bar:<50} {percentage:5.2f}%")
        
        print(f"\n   Total Languages Used: {len(self.languages)}")
    
    def display_contribution_insights(self):
        """Display contribution insights"""
        print("\n" + "=" * 70)
        print("💡 CONTRIBUTION INSIGHTS")
        print("=" * 70)
        
        if not self.repos_data:
            return
        
        # License analysis
        licenses = Counter()
        for repo in self.repos_data:
            license_info = repo.get('license')
            if license_info:
                licenses[license_info.get('name', 'Unknown')] += 1
            else:
                licenses['No License'] += 1
        
        print(f"\n📜 License Distribution:")
        for license_name, count in licenses.most_common(10):
            print(f"   {license_name:<30} {count:,} repos")
        
        # Topics analysis
        all_topics = []
        for repo in self.repos_data:
            topics = repo.get('topics', [])
            all_topics.extend(topics)
        
        if all_topics:
            topic_counter = Counter(all_topics)
            print(f"\n🏷️  Top 15 Repository Topics:")
            for i, (topic, count) in enumerate(topic_counter.most_common(15), 1):
                print(f"   {i:2d}. {topic:<30} {count:,} repos")
        
        # Has issues/wiki/projects enabled
        has_issues = sum(1 for repo in self.repos_data if repo.get('has_issues', False))
        has_wiki = sum(1 for repo in self.repos_data if repo.get('has_wiki', False))
        has_projects = sum(1 for repo in self.repos_data if repo.get('has_projects', False))
        has_downloads = sum(1 for repo in self.repos_data if repo.get('has_downloads', False))
        
        print(f"\n⚙️  Repository Features:")
        print(f"   Issues Enabled: {has_issues:,} repos")
        print(f"   Wiki Enabled: {has_wiki:,} repos")
        print(f"   Projects Enabled: {has_projects:,} repos")
        print(f"   Downloads Enabled: {has_downloads:,} repos")
    
    def check_rate_limit(self):
        """Check GitHub API rate limit"""
        url = f"{self.base_url}/rate_limit"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            core = data['resources']['core']
            remaining = core['remaining']
            limit = core['limit']
            reset_time = datetime.fromtimestamp(core['reset'])
            
            print(f"\n⚡ API Rate Limit:")
            print(f"   Remaining: {remaining}/{limit}")
            print(f"   Resets at: {reset_time.strftime('%H:%M:%S')}")
            
            if remaining < 10:
                print(f"   ⚠️  Warning: Low rate limit remaining!")
        except requests.exceptions.RequestException as e:
            print(f"❌ Error checking rate limit: {e}")
    
    def export_to_json(self, filename=None):
        """Export all statistics to JSON file"""
        if filename is None:
            filename = f"{self.username}_github_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        export_data = {
            'username': self.username,
            'generated_at': datetime.now().isoformat(),
            'profile': self.user_data,
            'statistics': {
                'total_repos': len(self.repos_data),
                'total_stars': self.total_stars,
                'total_forks': self.total_forks,
                'total_watchers': self.total_watchers,
                'total_size_kb': self.total_size,
            },
            'languages': dict(self.languages),
            'repositories': self.repos_data
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Statistics exported to: {filename}")
            return True
        except Exception as e:
            print(f"❌ Error exporting to JSON: {e}")
            return False
    
    def run_full_analysis(self, export_json=False):
        """Run complete analysis and display all statistics"""
        print("\n" + "=" * 70)
        print("🚀 GITHUB PROFILE STATISTICS ANALYZER")
        print("=" * 70)
        print(f"Target: @{self.username}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        # Check rate limit first
        self.check_rate_limit()
        
        # Fetch all data
        if not self.fetch_user_profile():
            return False
        
        if not self.fetch_repositories():
            print("⚠️  No repositories found or error fetching repositories")
        
        if self.repos_data:
            self.fetch_repository_languages()
            self.calculate_statistics()
        
        # Display all statistics
        self.display_profile_info()
        self.display_repository_stats()
        self.display_language_stats()
        self.display_contribution_insights()
        
        # Check rate limit after analysis
        self.check_rate_limit()
        
        # Export if requested
        if export_json:
            self.export_to_json()
        
        print("\n" + "=" * 70)
        print("✅ Analysis Complete!")
        print("=" * 70)
        
        return True


def main():
    """Main execution function"""
    print("🚀 GitHub Profile Statistics Automation Script")
    print("=" * 70)
    
    # Get username from command line or prompt
    if len(sys.argv) > 1:
        username = sys.argv[1]
    else:
        username = input("Enter GitHub username: ").strip()
    
    if not username:
        print("❌ Error: Username is required")
        sys.exit(1)
    
    # Optional: Get GitHub token for higher rate limits
    token = None
    if len(sys.argv) > 2:
        token = sys.argv[2]
    else:
        print("\n💡 Tip: Provide a GitHub Personal Access Token for higher rate limits")
        print("   Usage: python github_stats.py <username> <token>")
        print("   Or set GITHUB_TOKEN environment variable")
        
        import os
        token = os.environ.get('GITHUB_TOKEN')
        if token:
            print("   ✅ Using token from GITHUB_TOKEN environment variable")
    
    # Ask about JSON export
    export_json = False
    if len(sys.argv) > 3 and sys.argv[3].lower() in ['--export', '-e', 'export']:
        export_json = True
    else:
        response = input("\nExport statistics to JSON? (y/n): ").strip().lower()
        export_json = response in ['y', 'yes']
    
    # Create analyzer and run
    analyzer = GitHubStats(username, token)
    success = analyzer.run_full_analysis(export_json=export_json)
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
