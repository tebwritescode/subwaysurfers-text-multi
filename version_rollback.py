#!/usr/bin/env python3
"""
Version rollback utility for Subway Surfers Text-to-Video Generator
Allows quick rollback to previous stable versions when testing goes wrong
"""

import os
import sys
import shutil
from datetime import datetime

# Version snapshots with their key characteristics
VERSION_SNAPSHOTS = {
    "1.0.11": {
        "description": "Last stable before caption timing work",
        "features": [
            "Multi-section video processing",
            "No text truncation",
            "Basic progress tracking",
            "Source video filtering (>50MB)"
        ],
        "known_issues": ["Caption timing drift", "STT words don't match original"],
        "cleantext": "enabled_with_placeholders",
        "progress_updates": "enabled",
        "word_alignment": False
    },
    
    "1.1.0": {
        "description": "Original text with STT timing alignment",
        "features": [
            "Uses original text for captions",
            "Word alignment algorithm",
            "STT only for timing"
        ],
        "known_issues": ["Still has timing drift"],
        "cleantext": "enabled_with_placeholders",
        "progress_updates": "disabled",
        "word_alignment": True
    },
    
    "1.1.1": {
        "description": "Single text cleaning at pipeline start",
        "features": [
            "Text cleaned once at beginning",
            "Consistent text throughout pipeline"
        ],
        "known_issues": ["Timing drift persists"],
        "cleantext": "enabled_with_placeholders",
        "progress_updates": "disabled",
        "word_alignment": True
    },
    
    "1.1.2": {
        "description": "TESTING - Cleantext disabled",
        "features": [
            "Text cleaning completely disabled",
            "Progress bars re-enabled",
            "Testing to isolate timing issues"
        ],
        "known_issues": ["Testing version"],
        "cleantext": "disabled",
        "progress_updates": "enabled",
        "word_alignment": True
    }
}

def create_backup(version):
    """Create a backup of current code state before rollback"""
    backup_dir = f"backups/backup_{version}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    files_to_backup = [
        "version.py",
        "cleantext.py",
        "videomaker.py",
        "sub.py",
        "text_splitter.py",
        "word_aligner.py"
    ]
    
    for file in files_to_backup:
        if os.path.exists(file):
            shutil.copy2(file, backup_dir)
    
    print(f"✅ Created backup in {backup_dir}")
    return backup_dir

def rollback_to_version(target_version):
    """
    Rollback to a specific version configuration
    This doesn't change the actual code but configures the behavior
    """
    if target_version not in VERSION_SNAPSHOTS:
        print(f"❌ Unknown version: {target_version}")
        print(f"Available versions: {', '.join(VERSION_SNAPSHOTS.keys())}")
        return False
    
    snapshot = VERSION_SNAPSHOTS[target_version]
    print(f"\n🔄 Rolling back to version {target_version}")
    print(f"Description: {snapshot['description']}")
    
    # Update version.py
    with open("version.py", "r") as f:
        content = f.read()
    
    content = re.sub(r'__version__ = "[^"]*"', f'__version__ = "{target_version}"', content)
    
    with open("version.py", "w") as f:
        f.write(content)
    
    # Configure cleantext
    if snapshot["cleantext"] == "disabled":
        # Already configured in 1.1.2
        print("✅ Text cleaning: DISABLED")
    else:
        # Re-enable cleantext
        with open("cleantext.py", "r") as f:
            content = f.read()
        
        content = content.replace("cleantext = cleantext_disabled", "cleantext = cleantext_original")
        
        with open("cleantext.py", "w") as f:
            f.write(content)
        print("✅ Text cleaning: ENABLED")
    
    # Configure progress updates
    if snapshot["progress_updates"] == "disabled":
        print("✅ Progress updates: DISABLED (for timing accuracy)")
    else:
        print("✅ Progress updates: ENABLED")
    
    # Word alignment status
    if snapshot["word_alignment"]:
        print("✅ Word alignment: ENABLED (original text with STT timing)")
    else:
        print("✅ Word alignment: DISABLED (using STT words directly)")
    
    print(f"\n✅ Rolled back to version {target_version}")
    print("\n⚠️  Please restart the Flask server for changes to take effect!")
    
    return True

def show_version_history():
    """Display version history and current status"""
    print("\n📊 VERSION HISTORY")
    print("=" * 80)
    
    for version, snapshot in VERSION_SNAPSHOTS.items():
        print(f"\nVersion {version}: {snapshot['description']}")
        print("Features:")
        for feature in snapshot['features']:
            print(f"  ✓ {feature}")
        if snapshot['known_issues']:
            print("Known Issues:")
            for issue in snapshot['known_issues']:
                print(f"  ⚠ {issue}")
        print("-" * 40)

def main():
    """Main rollback utility"""
    if len(sys.argv) < 2:
        print("Usage: python version_rollback.py <command> [version]")
        print("\nCommands:")
        print("  history    - Show version history")
        print("  rollback   - Rollback to a specific version")
        print("  current    - Show current version")
        print("\nExample: python version_rollback.py rollback 1.0.11")
        return
    
    command = sys.argv[1].lower()
    
    if command == "history":
        show_version_history()
    
    elif command == "current":
        try:
            from version import __version__
            print(f"\n📌 Current version: {__version__}")
            if __version__ in VERSION_SNAPSHOTS:
                snapshot = VERSION_SNAPSHOTS[__version__]
                print(f"Description: {snapshot['description']}")
        except:
            print("❌ Could not read current version")
    
    elif command == "rollback":
        if len(sys.argv) < 3:
            print("❌ Please specify a version to rollback to")
            print(f"Available versions: {', '.join(VERSION_SNAPSHOTS.keys())}")
            return
        
        target_version = sys.argv[2]
        
        # Create backup first
        try:
            from version import __version__
            backup_dir = create_backup(__version__)
        except:
            backup_dir = create_backup("unknown")
        
        # Perform rollback
        if rollback_to_version(target_version):
            print(f"\n💾 Backup saved to: {backup_dir}")
    
    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    import re
    main()