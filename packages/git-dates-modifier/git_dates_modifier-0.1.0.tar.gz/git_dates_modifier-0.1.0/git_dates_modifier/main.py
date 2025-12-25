#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Git Dates Modifier
Modify commit dates based on commit message matching, supporting 
separate modification of author date and commit date.
"""
import sys
import os
import subprocess
from datetime import datetime


# Check dependencies
def check_dependencies():
    try:
        import git_filter_repo as fr
        return fr
    except ImportError:
        print("❌ Error: Dependency package 'git-filter-repo' not found.")
        print("💡 Please run: pip install git-filter-repo")
        sys.exit(1)


# ==========================================
# 1. Environment and Utility Functions
# ==========================================
def setup_environment(repo_path):
    abs_path = os.path.abspath(repo_path)
    git_dir = os.path.join(abs_path, ".git")

    if not os.path.exists(git_dir):
        print(f"❌ Error: .git folder not found in {abs_path}")
        print("💡 Please run this script from the repository root directory!")
        sys.exit(1)

    os.chdir(abs_path)
    os.environ["GIT_DIR"] = git_dir
    os.environ["GIT_WORK_TREE"] = abs_path
    print(f"🔒 Environment locked: {abs_path}")


def get_commits():
    """Get commit list (including AuthorDate and CommitterDate)"""
    # %H=SHA, %ai=AuthorDate, %ci=CommiterDate, %B=Body
    cmd = ["git", "log", "--reverse",
           "--format=%H%x09%ai%x09%ci%x09%B%n__END_COMMIT__"]
    try:
        result = subprocess.run(cmd, capture_output=True,
                                check=True, encoding="utf-8", errors="replace")
    except subprocess.CalledProcessError as e:
        print(f"❌ Git log failed: {e}")
        sys.exit(1)

    commits = []
    for block in result.stdout.split("\n__END_COMMIT__\n"):
        if not block.strip():
            continue
        parts = block.split("\t", 3)
        if len(parts) >= 4:
            commits.append({
                "sha": parts[0],
                "auth_date": parts[1],
                "comm_date": parts[2],
                "message": parts[3].strip(),
                "subject": parts[3].strip().split('\n')[0][:50]
            })
    return commits


def parse_date(date_str):
    """Parse date string"""
    if not date_str.strip():
        return None
    s = date_str.strip().replace("/", "-").replace("T", " ")
    try:
        dt = datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
        ts = int(dt.timestamp())
        # Get local timezone
        offset = datetime.now().astimezone().strftime("%z")
        return f"{ts} {offset}"
    except ValueError:
        return None


def get_now_formatted():
    dt = datetime.now()
    ts = int(dt.timestamp())
    offset = dt.astimezone().strftime("%z")
    return f"{ts} {offset}"


def format_timestamp_for_display(timestamp_str):
    """Convert timestamp string to readable format"""
    if not timestamp_str:
        return "N/A"
    try:
        # Extract timestamp part (before space)
        ts = int(timestamp_str.split()[0])
        dt = datetime.fromtimestamp(ts)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return timestamp_str


# ==========================================
# 2. Preview Function
# ==========================================
def show_preview(commits, mapping):
    """Display preview of all planned changes"""
    print("\n" + "=" * 80)
    print("📋 PREVIEW - Planned Changes")
    print("=" * 80)

    changes_count = 0
    for c in commits:
        if c['message'] in mapping:
            changes = mapping[c['message']]
            print(f"\n🔹 Commit: [{c['sha'][:7]}] {c['subject']}")

            # Show Author Date changes
            if "author_date" in changes:
                new_auth_display = format_timestamp_for_display(
                    changes["author_date"].decode('utf-8'))
                print(
                    f"   👤 Author Date:    {c['auth_date']} → {new_auth_display}")
                changes_count += 1

            # Show Committer Date changes
            if "committer_date" in changes:
                new_comm_display = format_timestamp_for_display(
                    changes["committer_date"].decode('utf-8'))
                print(
                    f"   💾 Committer Date: {c['comm_date']} → {new_comm_display}")
                changes_count += 1

    print("\n" + "-" * 80)
    print(
        f"📊 Summary: {len(mapping)} commits will be modified ({changes_count} total changes)")
    print("=" * 80)

    return changes_count > 0


# ==========================================
# 3. Main Logic
# ==========================================
def main():
    fr = check_dependencies()

    repo_path = os.getcwd()
    setup_environment(repo_path)

    commits = get_commits()
    print(f"📄 Read {len(commits)} commits\n")

    # Store modification plan: Key=Message, Value=Dict(author_bytes, committer_bytes)
    mapping = {}

    print("👇 Operation Guide:")
    print("   - Enter 'now' to use current time")
    print("   - Press Enter to keep original")
    print("   - Format: 2025-10-24 11:22:33\n")

    for c in commits:
        print("=" * 60)
        print(f"[{c['sha'][:7]}] {c['subject']}")
        print(f"   👤 Original Author Date:    {c['auth_date']}")
        print(f"   💾 Original Committer Date: {c['comm_date']}")
        print("-" * 60)

        # 1. Ask for Author Date
        new_auth = input("   👉 New Author Date    (Enter to skip): ").strip()

        # 2. Ask for Committer Date
        new_comm = input("   👉 New Committer Date (Enter to skip): ").strip()

        # Prepare data entry
        entry = {}

        # Handle Author
        if new_auth:
            val = None
            if new_auth == 'now':
                val = get_now_formatted()
            else:
                val = parse_date(new_auth)

            if val:
                entry["author_date"] = val.encode('utf-8')

        # Handle Committer
        if new_comm:
            val = None
            if new_comm == 'now':
                val = get_now_formatted()
            else:
                val = parse_date(new_comm)

            if val:
                entry["committer_date"] = val.encode('utf-8')

        # If any changes, add to mapping
        if entry:
            mapping[c['message']] = entry
            changes = []
            if "author_date" in entry:
                changes.append("Author")
            if "committer_date" in entry:
                changes.append("Committer")
            print(f"   ✅ Planned changes: {', '.join(changes)}")
        else:
            print("   ⚪ No changes")

        print()

    if not mapping:
        print("No modifications made, exiting.")
        return

    # Show preview before execution
    show_preview(commits, mapping)

    print("\n⚠️  WARNING: This will rewrite Git history!")
    print("   Make sure you have a backup or understand the consequences.")
    print()

    confirm = input(
        "🚀 Do you want to proceed with these changes? (y/N) > ").lower().strip()
    if confirm != 'y':
        print("\nCancelled.")
        return

    print("\n🚀 Executing changes...")
    print("-------------------------------------------------")

    # ==========================================
    # 4. Callback Function
    # ==========================================
    def separate_date_callback(commit, metadata):
        # Decode message for matching
        try:
            msg = commit.message.decode('utf-8').strip()
        except:
            msg = commit.message.decode('latin-1').strip()

        if msg in mapping:
            changes = mapping[msg]
            log_parts = []

            # Independently modify Author Date
            if "author_date" in changes:
                commit.author_date = changes["author_date"]
                log_parts.append("Author")

            # Independently modify Committer Date
            if "committer_date" in changes:
                commit.committer_date = changes["committer_date"]
                log_parts.append("Committer")

            # Real-time output log
            sys.stdout.write(
                f"🚀 MATCHED [{msg[:20]}...]: {', '.join(log_parts)}\n")
            sys.stdout.flush()

    # ==========================================
    # 5. Execute Filter
    # ==========================================
    args = fr.FilteringOptions.parse_args(['--force'])
    filter_obj = fr.RepoFilter(args, commit_callback=separate_date_callback)

    try:
        filter_obj.run()
        print("-------------------------------------------------")
        print("\n✅ Execution complete!")
        print("\n🔎 Verify results (check CommitDate column):")
        print("   git log --format=fuller --date=iso")
        print("\n📤 Push changes:")
        print("   git push --force --all")
    except Exception as e:
        print(f"\n❌ Execution error: {e}")


if __name__ == "__main__":
    main()
