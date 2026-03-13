#!/usr/bin/env python3
import subprocess
import os
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackupSystem:
    def __init__(self, repo_path="/home/joseph/src"):
        self.repo_path = repo_path
    
    def backup_to_github(self):
        """Commit and push all changes to GitHub"""
        try:
            os.chdir(self.repo_path)
            
            # Check if there are changes
            status = subprocess.run(['git', 'status', '--porcelain'], 
                                   capture_output=True, text=True)
            
            if not status.stdout.strip():
                logger.info("No changes to backup")
                return True
            
            # Add all changes
            subprocess.run(['git', 'add', '.'], check=True)
            
            # Commit with timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            commit_msg = f"Auto-backup: {timestamp}"
            subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
            
            # Push to GitHub
            subprocess.run(['git', 'push'], check=True)
            
            logger.info(f"✅ Backup successful: {timestamp}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Backup failed: {e}")
            return False
    
    def create_local_snapshot(self):
        """Create local tar backup"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"/home/joseph/jarvis_backup_{timestamp}.tar.gz"
            
            subprocess.run([
                'tar', '-czf', backup_file,
                '--exclude=__pycache__',
                '--exclude=*.pyc',
                '--exclude=.git',
                self.repo_path
            ], check=True)
            
            logger.info(f"✅ Local snapshot created: {backup_file}")
            return backup_file
            
        except Exception as e:
            logger.error(f"❌ Snapshot failed: {e}")
            return None
    
    def restore_from_github(self):
        """Pull latest from GitHub"""
        try:
            os.chdir(self.repo_path)
            subprocess.run(['git', 'pull'], check=True)
            logger.info("✅ Restored from GitHub")
            return True
        except Exception as e:
            logger.error(f"❌ Restore failed: {e}")
            return False

# Manual backup script
if __name__ == "__main__":
    backup = BackupSystem()
    
    print("JARVIS Backup System")
    print("1. Backup to GitHub")
    print("2. Create local snapshot")
    print("3. Restore from GitHub")
    
    choice = input("\nChoice: ")
    
    if choice == "1":
        backup.backup_to_github()
    elif choice == "2":
        backup.create_local_snapshot()
    elif choice == "3":
        backup.restore_from_github()
