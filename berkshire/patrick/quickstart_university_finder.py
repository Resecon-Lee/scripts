"""
Quick Start Script for University Contact Finder
Simple interactive setup and test run
"""

import os
import sys
from pathlib import Path

def create_env_file():
    """Interactive setup for .env file"""
    print("\n" + "="*60)
    print("University Contact Finder - Quick Setup")
    print("="*60)

    env_path = Path(".env")

    if env_path.exists():
        print("\n✅ .env file already exists!")
        response = input("Do you want to reconfigure it? (y/N): ")
        if response.lower() != 'y':
            return

    print("\nLet's set up your API keys.")
    print("\nRecommended: Perplexity (has built-in web search)")
    print("Get your key at: https://www.perplexity.ai/settings/api")
    print("Free tier: $5 credit\n")

    provider = input("Which provider do you want to use?\n1. Perplexity (recommended)\n2. OpenAI\n3. Anthropic Claude\n4. Ollama (free, local)\nChoice (1-4): ").strip()

    env_content = "# API Keys for University Contact Finder\n\n"

    if provider == "1":
        api_key = input("\nEnter your Perplexity API key: ").strip()
        env_content += f"PERPLEXITY_API_KEY={api_key}\n"
        print("\n✅ Perplexity configured!")

    elif provider == "2":
        api_key = input("\nEnter your OpenAI API key: ").strip()
        env_content += f"OPENAI_API_KEY={api_key}\n"

        print("\nOpenAI needs a search API. Recommended: Tavily")
        print("Get your key at: https://tavily.com (1,000 free searches/month)")
        search_key = input("\nEnter your Tavily API key: ").strip()
        env_content += f"TAVILY_API_KEY={search_key}\n"
        print("\n✅ OpenAI + Tavily configured!")

    elif provider == "3":
        api_key = input("\nEnter your Anthropic API key: ").strip()
        env_content += f"ANTHROPIC_API_KEY={api_key}\n"

        print("\nClaude needs a search API. Recommended: Tavily")
        print("Get your key at: https://tavily.com (1,000 free searches/month)")
        search_key = input("\nEnter your Tavily API key: ").strip()
        env_content += f"TAVILY_API_KEY={search_key}\n"
        print("\n✅ Claude + Tavily configured!")

    elif provider == "4":
        print("\n✅ Ollama selected (no API key needed for LLM)")
        print("Make sure Ollama is running: ollama serve")
        print("And you have a model pulled: ollama pull llama3.1:8b")

        print("\nOllama needs a search API. Recommended: Tavily")
        print("Get your key at: https://tavily.com (1,000 free searches/month)")
        search_key = input("\nEnter your Tavily API key (or press Enter to skip): ").strip()
        if search_key:
            env_content += f"TAVILY_API_KEY={search_key}\n"
        print("\n✅ Ollama configured!")
    else:
        print("❌ Invalid choice")
        return

    # Write .env file
    with open(env_path, 'w') as f:
        f.write(env_content)

    print(f"\n✅ Configuration saved to {env_path}")


def create_sample_excel():
    """Create a sample Excel file for testing"""
    try:
        import pandas as pd

        sample_file = Path("sample_universities.xlsx")

        if sample_file.exists():
            print(f"\n✅ {sample_file} already exists!")
            return str(sample_file)

        # Create sample with a few universities
        df = pd.DataFrame({
            'University': [
                'Harvard University',
                'Stanford University',
                'MIT'
            ]
        })

        df.to_excel(sample_file, index=False)
        print(f"\n✅ Created sample file: {sample_file}")
        print("   Contains 3 universities for testing")
        return str(sample_file)

    except ImportError:
        print("\n⚠️  pandas not installed. Creating CSV instead...")
        sample_file = Path("sample_universities.csv")
        with open(sample_file, 'w') as f:
            f.write("University\n")
            f.write("Harvard University\n")
            f.write("Stanford University\n")
            f.write("MIT\n")
        print(f"✅ Created sample file: {sample_file}")
        return str(sample_file)


def check_dependencies():
    """Check if required packages are installed"""
    print("\n" + "="*60)
    print("Checking Dependencies...")
    print("="*60)

    required = {
        'pandas': 'pandas',
        'openpyxl': 'openpyxl',
        'requests': 'requests',
        'dotenv': 'python-dotenv',
    }

    optional = {
        'openai': 'openai',
        'anthropic': 'anthropic',
    }

    missing = []

    for module, package in required.items():
        try:
            __import__(module if module != 'dotenv' else 'dotenv')
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - MISSING (required)")
            missing.append(package)

    for module, package in optional.items():
        try:
            __import__(module)
            print(f"✅ {package} (optional)")
        except ImportError:
            print(f"⚠️  {package} - not installed (optional)")

    if missing:
        print(f"\n❌ Missing required packages!")
        print(f"\nInstall them with:")
        print(f"pip install {' '.join(missing)}")
        return False

    print("\n✅ All required dependencies installed!")
    return True


def run_test():
    """Run a test with the sample file"""
    print("\n" + "="*60)
    print("Ready to Test!")
    print("="*60)

    response = input("\nDo you want to run a test with sample universities? (Y/n): ")
    if response.lower() == 'n':
        print("\n📝 To run manually:")
        print("python university_contact_finder.py sample_universities.xlsx results.xlsx")
        return

    # Determine provider from .env
    provider = "perplexity"
    search_api = "perplexity"

    env_path = Path(".env")
    if env_path.exists():
        with open(env_path) as f:
            content = f.read()
            if "OPENAI_API_KEY" in content:
                provider = "openai"
                search_api = "tavily"
            elif "ANTHROPIC_API_KEY" in content:
                provider = "anthropic"
                search_api = "tavily"
            elif "TAVILY_API_KEY" in content and "PERPLEXITY_API_KEY" not in content:
                provider = "ollama"
                search_api = "tavily"

    print(f"\n🚀 Running test with {provider}...")
    print("   Processing 3 sample universities...")
    print("   This may take 10-30 seconds...\n")

    # Import and run
    try:
        from university_contact_finder import UniversityContactFinder

        finder = UniversityContactFinder(
            provider=provider,
            search_api=search_api,
            rate_limit_delay=1.0
        )

        finder.process_excel(
            input_file="sample_universities.xlsx",
            output_file="sample_results.xlsx",
            max_universities=3
        )

        print("\n" + "="*60)
        print("✅ Test Complete!")
        print("="*60)
        print(f"\n📄 Results saved to: sample_results.xlsx")
        print("\nOpen the file to see the extracted contact information!")
        print("\nTo process your own universities:")
        print("python university_contact_finder.py your_file.xlsx output.xlsx")

    except Exception as e:
        print(f"\n❌ Error during test: {str(e)}")
        print("\nPlease check:")
        print("1. Your API keys in .env are correct")
        print("2. You have internet connection")
        print("3. Your API has available credits")


def main():
    """Main setup flow"""
    print("\n🎓 University Contact Finder - Quick Start\n")

    # Check dependencies
    if not check_dependencies():
        print("\n❌ Please install missing dependencies first:")
        print("pip install -r requirements_university_finder.txt")
        return

    # Setup .env
    create_env_file()

    # Create sample file
    create_sample_excel()

    # Run test
    run_test()

    print("\n" + "="*60)
    print("Setup Complete! 🎉")
    print("="*60)
    print("\nFor more options, see: UNIVERSITY_FINDER_README.md")
    print("For help: python university_contact_finder.py --help\n")


if __name__ == "__main__":
    main()
