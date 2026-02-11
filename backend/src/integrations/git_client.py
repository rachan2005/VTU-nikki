"""
Git integration to extract commits as artifacts.
"""
import subprocess
from datetime import datetime, timedelta
from typing import List, Dict
import os


class GitClient:
    """Extract git commit information."""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path
        
    def get_today_commits(self, author: str = None) -> List[Dict]:
        """Get commits from today."""
        try:
            # Get today's date range
            today = datetime.now().date()
            since = today.isoformat()
            
            cmd = [
                "git", "-C", self.repo_path,
                "log",
                f"--since={since}",
                "--pretty=format:%H|%an|%ae|%ai|%s",
                "--no-merges"
            ]
            
            if author:
                cmd.extend(["--author", author])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            commits = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                    
                parts = line.split('|')
                if len(parts) >= 5:
                    commits.append({
                        "hash": parts[0][:7],
                        "author": parts[1],
                        "email": parts[2],
                        "date": parts[3],
                        "message": parts[4],
                        "uri": f"git://{parts[0][:7]}"
                    })
            
            return commits
            
        except subprocess.CalledProcessError:
            # Not a git repo or git not available
            return []
        except Exception as e:
            print(f"Error fetching git commits: {e}")
            return []
    
    def get_commit_details(self, commit_hash: str) -> Dict:
        """Get detailed info about a specific commit."""
        try:
            cmd = [
                "git", "-C", self.repo_path,
                "show",
                "--stat",
                "--pretty=format:%H|%an|%ai|%s|%b",
                commit_hash
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            lines = result.stdout.split('\n')
            header = lines[0].split('|')
            
            return {
                "hash": header[0][:7],
                "author": header[1],
                "date": header[2],
                "subject": header[3],
                "body": header[4] if len(header) > 4 else "",
                "stats": '\n'.join(lines[1:])
            }
            
        except Exception as e:
            return {"error": str(e)}
