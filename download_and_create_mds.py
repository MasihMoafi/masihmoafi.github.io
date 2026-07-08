#!/usr/bin/env python3
import urllib.request
import os

projects = {
    'a-modular-kingdom': {
        'title': 'A-Modular-Kingdom',
        'meta': 'Production-ready AI infrastructure with RAG and MCP integration.',
        'url': 'https://raw.githubusercontent.com/MasihMoafi/A-Modular-Kingdom/main/README.md'
    },
    'financial-market-analysis': {
        'title': 'Financial Market Analysis',
        'meta': 'Time-series analysis with transformers and reinforcement learning for financial market prediction.',
        'url': 'https://raw.githubusercontent.com/MasihMoafi/Financial-Market-Analysis/main/README.md'
    },
    'amr-parsing-summarization': {
        'title': 'AMR Parsing & Summarization',
        'meta': 'Abstract Meaning Representation parsing for advanced text summarization.',
        'url': 'https://raw.githubusercontent.com/MasihMoafi/AMR-Parsing-Summarization/main/README.md'
    }
}

def create_local_project_pages():
    print("Downloading and creating local project markdown pages...")

    # 1. Handle remote readmes
    for slug, info in projects.items():
        try:
            print(f"Fetching README for {info['title']}...")
            req = urllib.request.Request(
                info['url'],
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            with urllib.request.urlopen(req) as response:
                readme_content = response.read().decode('utf-8')

            filename = f"{slug}.md"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"---\n")
                f.write(f"layout: post\n")
                f.write(f"title: \"{info['title']}\"\n")
                f.write(f"meta: \"{info['meta']}\"\n")
                f.write(f"---\n\n")

                # Strip Jekyll metadata frontmatter if the readme itself has it (to avoid double frontmatter)
                if readme_content.startswith('---'):
                    parts = readme_content.split('---', 2)
                    if len(parts) >= 3:
                        readme_content = parts[2]
                f.write(readme_content)
            print(f"Created {filename} successfully.")
        except Exception as e:
            print(f"Failed to fetch {info['title']}: {e}")

    # 2. Handle local Voice-commander readme
    local_vc_readme = '/home/masih/Desktop/f/p/Voice-commander/README.md'
    if os.path.exists(local_vc_readme):
        try:
            print("Reading local Voice Commander README...")
            with open(local_vc_readme, 'r', encoding='utf-8') as f:
                vc_content = f.read()

            # Strip local frontmatter if it has one
            if vc_content.startswith('---'):
                parts = vc_content.split('---', 2)
                if len(parts) >= 3:
                    vc_content = parts[2]

            with open('voice-commander.md', 'w', encoding='utf-8') as f:
                f.write(f"---\n")
                f.write(f"layout: post\n")
                f.write(f"title: \"Voice Commander\"\n")
                f.write(f"meta: \"Local voice transcription with AI-powered refinement for developers.\"\n")
                f.write(f"---\n\n")
                f.write(vc_content)
            print("Created voice-commander.md successfully.")
        except Exception as e:
            print(f"Failed to read local Voice Commander readme: {e}")
    else:
        print("Local Voice Commander readme not found!")

if __name__ == '__main__':
    create_local_project_pages()
