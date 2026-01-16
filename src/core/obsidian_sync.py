"""
Obsidian Sync - Bidirectional sync with Obsidian markdown files
"""
import os
import re
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime


class ObsidianSync:
    """Handles synchronization with Obsidian vault"""
    
    def __init__(self, vault_path: Optional[str] = None):
        self.vault_path = Path(vault_path) if vault_path else Path.home() / "Documents" / "Obsidian"
        self.tasks_folder = self.vault_path / "Tasks"
        self.rough_notes_folder = self.vault_path / "Rough Notes"
        
        self.tasks_folder.mkdir(parents=True, exist_ok=True)
        self.rough_notes_folder.mkdir(parents=True, exist_ok=True)
        
        self.categories = {
            "personal": "Personal.md",
            "trabajo": "Trabajo.md",
            "universidad": "Universidad.md",
            "salud": "Salud.md",
            "proyectos": "Proyectos.md"
        }
        
        self._ensure_category_files()
    
    def _ensure_category_files(self):
        """Create category files if they don't exist"""
        for category, filename in self.categories.items():
            file_path = self.tasks_folder / filename
            if not file_path.exists():
                self._create_category_file(file_path, category)
    
    def _create_category_file(self, path: Path, category: str):
        """Create a new category file with template"""
        template = f"""# {category.title()}

## Pendiente


## En Progreso


## Completado

"""
        path.write_text(template, encoding='utf-8')
    
    def read_all_tasks(self) -> List[Dict]:
        """Read all tasks from Obsidian files"""
        tasks = []
        
        for category, filename in self.categories.items():
            file_path = self.tasks_folder / filename
            if file_path.exists():
                tasks.extend(self._parse_tasks_file(file_path, category))
        
        return tasks
    
    def _parse_tasks_file(self, file_path: Path, category: str) -> List[Dict]:
        """Parse a single task file"""
        tasks = []
        content = file_path.read_text(encoding='utf-8')
        
        task_pattern = r'- \[([ xX])\] (.+?)(?:\s*\[deadline: (\d{4}-\d{2}-\d{2})\])?(?:\s*\[priority: (\w+)\])?$'
        
        lines = content.split('\n')
        current_status = 'pendiente'
        
        for line in lines:
            if '## Pendiente' in line:
                current_status = 'pendiente'
            elif '## En Progreso' in line:
                current_status = 'en_progreso'
            elif '## Completado' in line:
                current_status = 'completado'
            
            match = re.match(task_pattern, line.strip())
            if match:
                checkbox, title, deadline, priority = match.groups()
                status = 'completado' if checkbox.lower() == 'x' else current_status
                
                tasks.append({
                    'title': title.strip(),
                    'category': category,
                    'status': status,
                    'deadline': deadline,
                    'priority': priority or 'media'
                })
        
        return tasks
    
    def add_task(self, title: str, category: str, status: str = "pendiente", 
                 deadline: Optional[str] = None, priority: str = "media"):
        """Add a task to the appropriate Obsidian file"""
        filename = self.categories.get(category.lower(), "Personal.md")
        file_path = self.tasks_folder / filename
        
        if not file_path.exists():
            self._create_category_file(file_path, category)
        
        content = file_path.read_text(encoding='utf-8')
        
        checkbox = 'x' if status == 'completado' else ' '
        task_line = f"- [{checkbox}] {title}"
        if deadline:
            task_line += f" [deadline: {deadline}]"
        if priority != 'media':
            task_line += f" [priority: {priority}]"
        task_line += "\n"
        
        status_map = {
            'pendiente': '## Pendiente',
            'en_progreso': '## En Progreso',
            'completado': '## Completado'
        }
        section_header = status_map.get(status, '## Pendiente')
        
        if section_header in content:
            idx = content.find(section_header) + len(section_header)
            while idx < len(content) and content[idx] != '\n':
                idx += 1
            idx += 1
            content = content[:idx] + task_line + content[idx:]
        else:
            content += f"\n{section_header}\n{task_line}"
        
        file_path.write_text(content, encoding='utf-8')
    
    def update_task(self, old_title: str, category: str, **kwargs):
        """Update a task in the Obsidian file"""
        filename = self.categories.get(category.lower(), "Personal.md")
        file_path = self.tasks_folder / filename
        
        if not file_path.exists():
            return
        
        content = file_path.read_text(encoding='utf-8')
        lines = content.split('\n')
        new_lines = []
        
        for line in lines:
            if f"- [" in line and old_title in line:
                match = re.match(
                    r'- \[([ xX])\] (.+?)(?:\s*\[deadline: (\d{4}-\d{2}-\d{2})\])?(?:\s*\[priority: (\w+)\])?$',
                    line.strip()
                )
                if match:
                    checkbox, title, deadline, priority = match.groups()
                    
                    new_title = kwargs.get('title', old_title)
                    new_status = kwargs.get('status')
                    new_deadline = kwargs.get('deadline', deadline)
                    new_priority = kwargs.get('priority', priority or 'media')
                    
                    if new_status == 'completado':
                        checkbox = 'x'
                    elif new_status:
                        checkbox = ' '
                    
                    new_line = f"- [{checkbox}] {new_title}"
                    if new_deadline:
                        new_line += f" [deadline: {new_deadline}]"
                    if new_priority and new_priority != 'media':
                        new_line += f" [priority: {new_priority}]"
                    
                    new_lines.append(new_line)
                    continue
            
            new_lines.append(line)
        
        file_path.write_text('\n'.join(new_lines), encoding='utf-8')
    
    def delete_task(self, title: str, category: str):
        """Remove a task from the Obsidian file"""
        filename = self.categories.get(category.lower(), "Personal.md")
        file_path = self.tasks_folder / filename
        
        if not file_path.exists():
            return
        
        content = file_path.read_text(encoding='utf-8')
        lines = content.split('\n')
        new_lines = [line for line in lines if not (f"- [" in line and title in line)]
        
        file_path.write_text('\n'.join(new_lines), encoding='utf-8')
    
    def save_quick_note(self, title: str, content: str) -> str:
        """Save a quick note to Rough Notes folder"""
        safe_title = re.sub(r'[^\w\s-]', '', title)
        safe_title = re.sub(r'\s+', '_', safe_title)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_title}_{timestamp}.md"
        
        file_path = self.rough_notes_folder / filename
        
        note_content = f"""# {title}

Created: {datetime.now().strftime("%Y-%m-%d %H:%M")}

---

{content}
"""
        file_path.write_text(note_content, encoding='utf-8')
        return str(file_path)
    
    def get_quick_notes(self) -> List[Dict]:
        """Get all quick notes from Rough Notes folder"""
        notes = []
        
        for file_path in self.rough_notes_folder.glob("*.md"):
            content = file_path.read_text(encoding='utf-8')
            
            title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
            title = title_match.group(1) if title_match else file_path.stem
            
            notes.append({
                'title': title,
                'file_path': str(file_path),
                'modified': datetime.fromtimestamp(file_path.stat().st_mtime)
            })
        
        return sorted(notes, key=lambda x: x['modified'], reverse=True)
