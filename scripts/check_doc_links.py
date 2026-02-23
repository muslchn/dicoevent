#!/usr/bin/env python3
"""
Documentation Link Checker

This script validates internal and external links in documentation files
to ensure all references are working correctly.
"""

import os
import re
import sys
import requests
from pathlib import Path
from urllib.parse import urljoin, urlparse

def normalize_anchor(anchor):
    """Normalize anchor text by removing emojis and special characters."""
    # Remove emojis and special Unicode characters
    normalized = re.sub(r'[^\w\s-]', '', anchor.lower())
    # Replace spaces and hyphens with single hyphens
    normalized = re.sub(r'[-\s]+', '-', normalized)
    # Remove leading/trailing hyphens
    normalized = normalized.strip('-')
    return normalized

def extract_headers(content):
    """Extract all headers and their normalized IDs from content."""
    headers = {}
    header_pattern = r'^(#{1,6})\s+(.+)$'
    
    for match in re.finditer(header_pattern, content, re.MULTILINE):
        level, title = match.groups()
        # Create ID from title (similar to GitHub's approach)
        header_id = normalize_anchor(title)
        headers[f"#{header_id}"] = title
        
        # Also track the raw header text
        raw_header = f"{'#' * len(level)} {title}"
        headers[raw_header] = title
    
    return headers

def check_internal_links(content, base_path, headers):
    """Check internal file references and anchors."""
    internal_links = re.findall(r'\[.*?\]\(([^http][^)]*)\)', content)
    broken_links = []
    
    for link in internal_links:
        # Handle anchor links
        if link.startswith('#'):
            # Check if normalized anchor exists
            normalized_link = normalize_anchor(link[1:])
            anchor_found = False
            
            # Check against all possible header formats
            for header_ref in headers.keys():
                if header_ref.startswith('#'):
                    normalized_header = normalize_anchor(header_ref[1:])
                    if normalized_header == normalized_link:
                        anchor_found = True
                        break
            
            if not anchor_found:
                broken_links.append(f"Broken anchor: {link}")
            continue
            
        # Handle file references
        if '#' in link:
            file_path, anchor = link.split('#', 1)
        else:
            file_path, anchor = link, None
            
        target_path = Path(base_path).parent / file_path
        
        if not target_path.exists():
            broken_links.append(f"Broken file reference: {link}")
        elif anchor:
            # Check if anchor exists in target file
            try:
                with open(target_path, 'r', encoding='utf-8') as f:
                    target_content = f.read()
                target_headers = extract_headers(target_content)
                
                normalized_anchor = normalize_anchor(anchor)
                anchor_found = False
                for header_ref in target_headers.keys():
                    if header_ref.startswith('#'):
                        normalized_header = normalize_anchor(header_ref[1:])
                        if normalized_header == normalized_anchor:
                            anchor_found = True
                            break
                
                if not anchor_found:
                    broken_links.append(f"Broken anchor in {file_path}: #{anchor}")
            except Exception as e:
                broken_links.append(f"Error checking {link}: {str(e)}")
                
    return broken_links

def check_external_links(content):
    """Check external URLs (basic validation only)."""
    external_links = re.findall(r'\[.*?\]\((https?://[^)]*)\)', content)
    broken_links = []
    
    # For demonstration - in production, you might want to actually test these
    # This is a simplified version that just validates URL format
    for link in external_links:
        parsed = urlparse(link)
        if not parsed.scheme or not parsed.netloc:
            broken_links.append(f"Invalid URL format: {link}")
            
    return broken_links

def check_documentation_links(doc_path):
    """Validate links in a documentation file."""
    if not doc_path.exists():
        print(f"❌ Documentation file not found: {doc_path}")
        return False
        
    with open(doc_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract headers for anchor validation
    headers = extract_headers(content)
    
    print(f"🔍 Checking links in {doc_path.name}...")
    
    # Check internal links
    internal_broken = check_internal_links(content, doc_path, headers)
    print(f"Internal links: {len(internal_broken)} issues found")
    for issue in internal_broken:
        print(f"  ⚠️  {issue}")
    
    # Check external links
    external_broken = check_external_links(content)
    print(f"External links: {len(external_broken)} issues found")
    for issue in external_broken:
        print(f"  ⚠️  {issue}")
    
    total_issues = len(internal_broken) + len(external_broken)
    
    if total_issues == 0:
        print("✅ All links appear to be valid!")
        return True
    else:
        print(f"❌ Found {total_issues} link issues")
        return False

def main():
    """Main link checking function."""
    project_root = Path(__file__).parent.parent
    docs_dir = project_root / "docs"
    
    print("🔗 Documentation Link Checker")
    print("=" * 40)
    
    # Check main README
    readme_path = project_root / "README.md"
    readme_valid = check_documentation_links(readme_path)
    
    # Check documentation files
    doc_files = list(docs_dir.glob("*.md")) if docs_dir.exists() else []
    doc_valid = True
    
    for doc_file in doc_files:
        if not check_documentation_links(doc_file):
            doc_valid = False
    
    print(f"\n📊 LINK CHECK SUMMARY:")
    print("=" * 30)
    print(f"README.md: {'✅ PASS' if readme_valid else '❌ FAIL'}")
    print(f"Documentation files: {'✅ PASS' if doc_valid else '❌ FAIL'}")
    
    overall_success = readme_valid and doc_valid
    
    if overall_success:
        print("\n🎉 All documentation links are valid!")
        sys.exit(0)
    else:
        print("\n❌ Some documentation links need attention!")
        sys.exit(1)

if __name__ == "__main__":
    main()