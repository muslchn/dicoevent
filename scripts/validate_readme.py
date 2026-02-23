#!/usr/bin/env python3
"""
README Validation Script

This script validates the README.md file against documentation best practices
and ensures all required sections are present and properly formatted.
"""

import os
import re
import sys
from pathlib import Path

def check_readme_completeness(readme_path):
    """Validate README completeness against best practices."""
    
    if not os.path.exists(readme_path):
        print("❌ README.md file not found!")
        return False
    
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("🔍 Validating README.md completeness...\n")
    
    # Required sections checklist
    required_sections = [
        r'# .*DicoEvent.*Professional.*Event.*Management.*Platform',
        r'## 📋 Table of Contents',
        r'## 🌟 Key Features',
        r'## 🏗️ Architecture & Technology Stack',
        r'## 📁 Project Structure',
        r'## ⚡ Quick Start Guide',
        r'## 📡 API Documentation',
        r'## 🔐 Security Implementation',
        r'## 🧪 Testing Strategy',
        r'## 📊 Monitoring & Analytics',
        r'## 🚀 Deployment Options',
        r'## 🤝 Contributing Guidelines',
        r'## 📞 Support & Community',
        r'## 📈 Roadmap & Future Enhancements',
        r'## 📄 License & Legal',
        r'## 🙏 Acknowledgments'
    ]
    
    # Best practice elements to check
    best_practice_checks = [
        (r'\[!\[.*\]\(.*\)\]\(.*\)', "Badges/Shields"),
        (r'```[a-z]*\n.*\n```', "Code blocks with syntax highlighting"),
        (r'## 🚀 Ready to Get Started', "Getting started section"),
        (r'## Project Status', "Project status indicators"),
        (r'Connect With Us', "Contact information"),
        (r'Changelog', "Version history"),
        (r'Getting Help', "Support resources"),
        (r'Show Your Support', "Community engagement")
    ]
    
    # Validation results
    section_results = []
    practice_results = []
    
    print("📋 Required Sections Check:")
    print("-" * 40)
    
    for pattern in required_sections:
        match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
        section_name = re.sub(r'[\\.#*]', '', pattern)[:50]
        status = "✅ PASS" if match else "❌ FAIL"
        section_results.append((section_name, bool(match)))
        print(f"{status} {section_name}")
    
    print("\n🔧 Best Practice Elements Check:")
    print("-" * 40)
    
    for pattern, element_name in best_practice_checks:
        match = re.search(pattern, content, re.DOTALL)
        status = "✅ PASS" if match else "❌ FAIL"
        practice_results.append((element_name, bool(match)))
        print(f"{status} {element_name}")
    
    # Overall statistics
    total_sections = len(section_results)
    passed_sections = sum(1 for _, passed in section_results if passed)
    section_coverage = (passed_sections / total_sections) * 100
    
    total_practices = len(practice_results)
    passed_practices = sum(1 for _, passed in practice_results if passed)
    practice_coverage = (passed_practices / total_practices) * 100
    
    print(f"\n📊 VALIDATION SUMMARY:")
    print("=" * 50)
    print(f"Sections Coverage: {passed_sections}/{total_sections} ({section_coverage:.1f}%)")
    print(f"Best Practices: {passed_practices}/{total_practices} ({practice_coverage:.1f}%)")
    
    # Quality metrics
    print(f"\n📏 QUALITY METRICS:")
    print("=" * 30)
    print(f"File Size: {len(content)} characters")
    print(f"Line Count: {len(content.splitlines())} lines")
    print(f"Word Count: {len(content.split())} words")
    
    # Check for common documentation anti-patterns
    print(f"\n⚠️  POTENTIAL IMPROVEMENTS:")
    print("=" * 35)
    
    anti_patterns = [
        (r'TODO|FIXME|TO DO', "Unresolved TODO/FIXME items"),
        (r'\.{3,}', "Excessive ellipsis usage"),
        (r'[!]{3,}|[?]{3,}', "Overuse of exclamation/question marks"),
        (r'http://[^ ]+', "Non-HTTPS links (security concern)")
    ]
    
    improvements_found = 0
    for pattern, description in anti_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            print(f"⚠️  Found {len(matches)} instance(s) of: {description}")
            improvements_found += 1
    
    if improvements_found == 0:
        print("✅ No obvious anti-patterns detected")
    
    # Final assessment
    overall_score = (section_coverage + practice_coverage) / 2
    
    print(f"\n🎯 OVERALL ASSESSMENT:")
    print("=" * 25)
    
    if overall_score >= 90:
        print("🏆 EXCELLENT - Comprehensive documentation meeting all best practices")
        print("   Ready for professional/enterprise use")
    elif overall_score >= 75:
        print("👍 GOOD - Well-structured documentation with minor improvements needed")
        print("   Suitable for most use cases")
    elif overall_score >= 60:
        print("⚠️  FAIR - Basic documentation present but lacking key elements")
        print("   Needs significant improvements for production use")
    else:
        print("❌ POOR - Documentation incomplete or missing critical sections")
        print("   Not suitable for distribution without major revisions")
    
    return overall_score >= 75

def main():
    """Main validation function."""
    project_root = Path(__file__).parent.parent
    readme_path = project_root / "README.md"
    
    print("📄 README.md Validation Tool")
    print("=" * 40)
    
    is_valid = check_readme_completeness(readme_path)
    
    if is_valid:
        print("\n🎉 README.md validation PASSED!")
        print("The documentation meets professional standards.")
        sys.exit(0)
    else:
        print("\n❌ README.md validation FAILED!")
        print("Please address the identified issues before submitting.")
        sys.exit(1)

if __name__ == "__main__":
    main()