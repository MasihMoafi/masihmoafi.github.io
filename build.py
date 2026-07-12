#!/usr/bin/env python3
import os
import re
import subprocess
import shutil

def parse_frontmatter(content):
    """Parses Jekyll YAML frontmatter from string content."""
    fm_match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', content, re.DOTALL)
    if not fm_match:
        return {}, content
    
    fm_text, body = fm_match.groups()
    metadata = {}
    for line in fm_text.split('\n'):
        if ':' in line:
            key, val = line.split(':', 1)
            metadata[key.strip()] = val.strip().strip('"').strip("'")
    return metadata, body

def compile_content(layout_name, content, page_meta={}):
    layout_path = f'_layouts/{layout_name}.html'
    if not os.path.exists(layout_path):
        return content
    
    with open(layout_path, 'r', encoding='utf-8') as f:
        layout_content = f.read()
        
    layout_fm, layout_body = parse_frontmatter(layout_content)
    rendered = layout_body.replace('{{ content }}', content)
    
    for key, val in page_meta.items():
        rendered = rendered.replace(f'{{{{ page.{key} }}}}', val)
        
    parent_layout = layout_fm.get('layout')
    if parent_layout and parent_layout != 'none':
        return compile_content(parent_layout, rendered, page_meta)
        
    return rendered

def render_layout(layout_name, content, page_meta={}):
    rendered = compile_content(layout_name, content, page_meta)
    
    title = page_meta.get('title', '')
    meta_desc = page_meta.get('meta', '')
    title_tag = f"{title} | Masih Moafi" if title and title != "Home" else "Masih Moafi | AI/ML Engineer"
    desc_tag = meta_desc if meta_desc else "Masih Moafi - AI/ML Engineer building practical AI tools"
    
    rendered = re.sub(r'{%\s*if\s+page\.title\s*%}.*?{%\s*endif\s*%}', title_tag, rendered, flags=re.DOTALL)
    rendered = re.sub(r'{%\s*if\s+page\.description\s*%}.*?{%\s*endif\s*%}', desc_tag, rendered, flags=re.DOTALL)
    rendered = re.sub(r'{%\s*if\s+page\.meta\s*%}.*?{%\s*endif\s*%}', meta_desc, rendered, flags=re.DOTALL)
    
    rendered = rendered.replace('{{ site.title }}', 'Masih Moafi')
    rendered = rendered.replace('{{ site.description }}', 'Masih Moafi - AI/ML Engineer building practical AI tools')
    rendered = rendered.replace("{{ 'now' | date: \"%Y\" }}", '2026')
    
    rendered = rendered.replace("{{ '/styles.css' | relative_url }}", 'styles.css')
    rendered = rendered.replace("{{ '/' | relative_url }}", 'index.html')
    rendered = rendered.replace("{{ '/#projects' | relative_url }}", 'index.html#projects')
    rendered = rendered.replace("{{ '/#contact' | relative_url }}", 'index.html#contact')
    rendered = rendered.replace("{{ '/assets/images/image1.png' | relative_url }}", 'assets/images/image1.png')
    
    return rendered

def convert_obsidian_assets(content, vault_dir):
    """Converts Obsidian double-bracket image wiki-links to markdown links and copies files."""
    # 1. Match ![[image.png]] or ![[image.png|300]]
    def repl_wiki_img(match):
        link_text = match.group(1)
        parts = link_text.split('|')
        img_name = parts[0].strip()
        
        # Search for this image in the Obsidian vault
        src_img_path = os.path.join(vault_dir, img_name)
        if not os.path.exists(src_img_path):
            for root, dirs, files in os.walk(vault_dir):
                if img_name in files:
                    src_img_path = os.path.join(root, img_name)
                    break
                    
        if os.path.exists(src_img_path):
            dest_img_path = os.path.join('visuals', img_name)
            os.makedirs('visuals', exist_ok=True)
            shutil.copy2(src_img_path, dest_img_path)
            print(f"  Copied wiki asset: {img_name} -> {dest_img_path}")
            return f"![{img_name}](visuals/{img_name})"
        else:
            print(f"  Warning: Asset not found in vault: {img_name}")
            return f"![{img_name}](visuals/{img_name})"

    content = re.sub(r'!\[\[(.*?)\]\]', repl_wiki_img, content)

    # 2. Match standard markdown images ![]() pointing to local relative paths in vault
    def repl_std_img(match):
        alt = match.group(1)
        img_path = match.group(2)
        
        # We only process local/relative images, not web URLs
        if img_path.startswith(('http://', 'https://', 'ftp://', 'mailto:')):
            return match.group(0)
            
        img_name = os.path.basename(img_path)
        
        # Search for this image in the Obsidian vault
        src_img_path = os.path.join(vault_dir, img_path)
        if not os.path.exists(src_img_path):
            # Try absolute path or search
            for root, dirs, files in os.walk(vault_dir):
                if img_name in files:
                    src_img_path = os.path.join(root, img_name)
                    break
                    
        if os.path.exists(src_img_path):
            dest_img_path = os.path.join('visuals', img_name)
            os.makedirs('visuals', exist_ok=True)
            shutil.copy2(src_img_path, dest_img_path)
            print(f"  Copied standard asset: {img_name} -> {dest_img_path}")
            return f"![{alt}](visuals/{img_name})"
        else:
            print(f"  Warning: Asset not found in vault: {img_name}")
            return f"![{alt}](visuals/{img_name})"

    content = re.sub(r'!\[(.*?)\]\((.*?)\)', repl_std_img, content)
    return content

def sync_obsidian_posts():
    obsidian_blog_dir = '/home/masih/Desktop/f/o/Main Vault/blog'
    vault_dir = '/home/masih/Desktop/f/o/Main Vault'
    
    if not os.path.exists(obsidian_blog_dir):
        print(f"Obsidian blog directory not found at {obsidian_blog_dir}. Skipping sync.")
        return
        
    print(f"Syncing blog posts from Obsidian Vault: {obsidian_blog_dir}...")
    active_posts = set()
    for filename in os.listdir(obsidian_blog_dir):
        if filename.endswith('.md'):
            src_path = os.path.join(obsidian_blog_dir, filename)
            title = filename[:-3] # remove .md
            slug = title.lower().replace(' ', '-').replace('_', '-')
            slug = re.sub(r'[^a-z0-9\-]', '', slug)
            dest_filename = f"{slug}.md"
            active_posts.add(dest_filename)
            active_posts.add(f"{slug}.html")
            
            with open(src_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Convert Obsidian double-bracket attachments and copy assets
            content = convert_obsidian_assets(content, vault_dir)
            
            # Add Jekyll Frontmatter if not already present
            if not content.strip().startswith('---'):
                # Extract first non-empty lines for snippet description
                snippet = ""
                lines = [l.strip() for l in content.split('\n') if l.strip() and not l.strip().startswith('#') and not l.strip().startswith('!')]
                if lines:
                    snippet = " ".join(lines[:2])
                    snippet = (snippet[:150] + '...') if len(snippet) > 150 else snippet
                    snippet = snippet.replace('"', '\\"')
                
                frontmatter = f"---\nlayout: post\ntitle: \"{title}\"\nmeta: \"{snippet}\"\n---\n\n"
                content = frontmatter + content
            
            with open(dest_filename, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"-> Synced & updated: {dest_filename}")

    # Remove stale posts not present in active_posts
    SPECIAL_FILES = {'index.html', 'index.jekyll.html', 'README.md', 'language.md'}
    for name in os.listdir('.'):
        if (name.endswith('.md') or name.endswith('.html')) and name not in SPECIAL_FILES:
            if name not in active_posts:
                print(f"🧹 Deleting stale post file: {name}")
                try:
                    os.remove(name)
                except Exception as e:
                    print(f"Error removing {name}: {e}")

def build_site():
    print("Building site locally...")
    
    # 0. Sync Obsidian posts first
    sync_obsidian_posts()
    
    # 1. Compile all .jekyll.html templates to .html files
    for filename in os.listdir('.'):
        if filename.endswith('.jekyll.html'):
            slug = filename[:-12] # remove .jekyll.html
            print(f"Compiling template {filename} to {slug}.html...")
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            fm, body = parse_frontmatter(content)
            layout = fm.get('layout', 'default')
            compiled = render_layout(layout, body, fm)
            with open(f"{slug}.html", 'w', encoding='utf-8') as f:
                f.write(compiled)
            print(f"-> {slug}.html compiled.")
            
    # Inject dynamic blog list into index.html
    index_path = 'index.html'
    if os.path.exists(index_path):
        with open(index_path, 'r', encoding='utf-8') as f:
            index_html = f.read()
            
        EXCLUDED_BLOG_POSTS = {'README.md', 'language.md', 'eyes-wide-shut.md', 'voice-commander.md', 'financial-market-analysis.md', 'amr-parsing-summarization.md'}
        blog_html = []
        categories = set()
        for filename in sorted(os.listdir('.')):
            if filename.endswith('.md') and filename not in EXCLUDED_BLOG_POSTS:
                slug = filename[:-3]
                with open(filename, 'r', encoding='utf-8') as f:
                    md_content = f.read()
                fm, _ = parse_frontmatter(md_content)
                title = fm.get('title') or fm.get('name') or slug.replace('-', ' ').title()
                if title.startswith('[') and title.endswith(']'):
                    title = title[1:-1]
                meta = fm.get('meta', '')
                category = fm.get('category', 'Uncategorized')
                categories.add(category)
                
                card = f"""
        <div class="project-card blog-card" data-category="{category}">
            <div class="project-header">
                <h3 class="hover-chromatic"><a href="{slug}.html">{title}</a></h3>
                <span class="project-stars tag">{category}</span>
            </div>
            <p class="project-description">{meta}</p>
            <a href="{slug}.html" class="project-link">Read Post &rarr;</a>
        </div>"""
                blog_html.append(card)

        # Build tabs HTML
        tabs_html = ['<div class="tabs" id="blog-tabs">']
        tabs_html.append('<button class="tab-btn active" onclick="filterBlogPosts(\'All\')">All</button>')
        for cat in sorted(list(categories)):
            tabs_html.append(f'<button class="tab-btn" onclick="filterBlogPosts(\'{cat}\')">{cat}</button>')
        tabs_html.append('</div>')
        tabs_content = "\n".join(tabs_html)

        blog_content = "\n".join(blog_html) if blog_html else '        <p style="color:var(--text-muted); padding: 1rem 0;">No learning trajectories published yet. Add a .md file inside your Obsidian blog folder to sync.</p>'
        
        injection = tabs_content + '\n<div class="project-grid" id="blog-posts-list">\n' + blog_content + '\n</div>'
        # The index.jekyll.html is modified to have <div id="blog-posts-container"><!-- Dyn content injected by build.py --></div>
        index_html = index_html.replace('<!-- Dyn content injected by build.py -->', injection)
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_html)
    
    # 2. Compile all .md files in the root folder to .html files (except README.md and language.md)
    for filename in os.listdir('.'):
        if filename.endswith('.md') and filename != 'README.md' and filename != 'language.md':
            slug = filename[:-3] # remove .md extension
            print(f"Compiling {filename} to {slug}.html...")
            with open(filename, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            fm, body = parse_frontmatter(md_content)
            if 'title' not in fm:
                title_val = fm.get('name') or slug.replace('-', ' ').title()
                if title_val.startswith('[') and title_val.endswith(']'):
                    title_val = title_val[1:-1]
                fm['title'] = title_val
            layout = fm.get('layout', 'post')
            
            # Compile Markdown body to HTML using pandoc with KaTeX math rendering support
            try:
                process = subprocess.Popen(
                    ['pandoc', '-f', 'markdown-yaml_metadata_block', '-t', 'html', '--katex'],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, stderr = process.communicate(input=body)
                if process.returncode != 0:
                    print(f"Pandoc error: {stderr}")
                    html_body = body # fallback
                else:
                    html_body = stdout
            except Exception as e:
                print(f"Failed to run pandoc: {e}")
                html_body = body # fallback
                
            compiled = render_layout(layout, html_body, fm)
            with open(f"{slug}.html", 'w', encoding='utf-8') as f:
                f.write(compiled)
            print(f"-> {slug}.html compiled.")

if __name__ == '__main__':
    build_site()
    print("Build complete!")
