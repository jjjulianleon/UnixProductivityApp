"""
Obsidian Sync - Bidirectional sync with Obsidian markdown files
Uses the actual paths defined in constants.py
"""
import os
import re
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from src.utils.constants import OBSIDIAN_VAULT_PATHS, OBSIDIAN_ROUGH_NOTES


class ObsidianSync:
    """Handles synchronization with Obsidian vault using actual paths"""
    
    def __init__(self):
        self.vault_paths = OBSIDIAN_VAULT_PATHS
        self.rough_notes_folder = OBSIDIAN_ROUGH_NOTES
        
        # Ensure rough notes folder exists
        self.rough_notes_folder.mkdir(parents=True, exist_ok=True)
    
    def read_all_tasks(self) -> List[Dict]:
        """Read all tasks from all Obsidian category files"""
        tasks = []
        
        for category, file_path in self.vault_paths.items():
            if file_path.exists():
                category_tasks = self._parse_tasks_file(file_path, category)
                tasks.extend(category_tasks)
        
        return tasks
    
    def _parse_tasks_file(self, file_path: Path, category: str) -> List[Dict]:
        """Parse tasks from a single Obsidian file"""
        tasks = []
        
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception:
            return tasks
        
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Basic task pattern
            basic_match = re.match(r'^- \[([ xX])\] (.+)$', line)
            
            if not basic_match:
                continue
            
            checkbox, raw_text = basic_match.groups()
            is_completed = checkbox.lower() == 'x'
            
            # Clean the title - extract metadata and clean
            title = raw_text.strip()
            deadline = None
            priority = 'media'
            status = 'completado' if is_completed else 'pendiente'
            
            # Extract (en progreso) status
            if '(en progreso)' in title.lower():
                status = 'en progreso' if not is_completed else 'completado'
                title = re.sub(r'\s*\(en progreso\)', '', title, flags=re.IGNORECASE)
            
            # Extract [deadline: YYYY-MM-DD]
            deadline_match = re.search(r'\[deadline:\s*(\d{4}-\d{2}-\d{2})\]', title)
            if deadline_match:
                deadline = deadline_match.group(1)
                title = re.sub(r'\s*\[deadline:\s*\d{4}-\d{2}-\d{2}\]', '', title)
            
            # Extract deadline from emoji format: 📅 YYYY-MM-DD
            emoji_deadline = re.search(r'[📅🗓️]\s*(\d{4}-\d{2}-\d{2})', title)
            if emoji_deadline and not deadline:
                deadline = emoji_deadline.group(1)
                title = re.sub(r'\s*[📅🗓️]\s*\d{4}-\d{2}-\d{2}', '', title)
            
            # Extract [priority: xxx]
            priority_match = re.search(r'\[priority:\s*(\w+)\]', title, re.IGNORECASE)
            if priority_match:
                priority = priority_match.group(1).lower()
                title = re.sub(r'\s*\[priority:\s*\w+\]', '', title, flags=re.IGNORECASE)
            
            # Remove completion markers: ✅ YYYY-MM-DD or (completado: YYYY-MM-DD)
            title = re.sub(r'\s*✅\s*\d{4}-\d{2}-\d{2}', '', title)
            title = re.sub(r'\s*\(completado:\s*\d{4}-\d{2}-\d{2}\)', '', title)
            
            # Remove | separator if present (for descriptions)
            description = ''
            if ' | ' in title:
                parts = title.split(' | ', 1)
                title = parts[0].strip()
                description = parts[1].strip() if len(parts) > 1 else ''
            
            # Final cleanup
            title = title.strip()
            
            if title:
                tasks.append({
                    'title': title,
                    'description': description,
                    'category': category,
                    'status': status,
                    'deadline': deadline,
                    'priority': priority
                })
        
        return tasks
    
    def add_task(self, title: str, category: str, status: str = "pendiente", 
                 deadline: Optional[str] = None, priority: str = "media"):
        """Add a task to the appropriate Obsidian file"""
        file_path = self.vault_paths.get(category)
        if not file_path:
            return
        
        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create file if doesn't exist
        if not file_path.exists():
            file_path.write_text(f"# Pendientes {category}\n\n", encoding='utf-8')
        
        content = file_path.read_text(encoding='utf-8')
        
        # Build task line
        checkbox = 'x' if status == 'completado' else ' '
        task_line = f"- [{checkbox}] {title}"
        if deadline:
            task_line += f" [deadline: {deadline}]"
        if priority and priority != 'media':
            task_line += f" [priority: {priority}]"
        if status == 'completado':
            task_line += f" (completado: {datetime.now().strftime('%Y-%m-%d')})"
        elif status == 'en progreso':
            task_line += " (en progreso)"
        task_line += "\n"
        
        # Add at the end
        content += task_line
        file_path.write_text(content, encoding='utf-8')
    
    def update_task(self, old_title: str, category: str, **kwargs):
        """Update a task in the Obsidian file"""
        file_path = self.vault_paths.get(category)
        if not file_path or not file_path.exists():
            return
        
        content = file_path.read_text(encoding='utf-8')
        lines = content.split('\n')
        new_lines = []
        
        for line in lines:
            if f"- [" in line and old_title in line:
                # Found the task to update
                new_title = kwargs.get('title', old_title)
                new_status = kwargs.get('status')
                new_deadline = kwargs.get('deadline')
                new_priority = kwargs.get('priority', 'media')
                
                checkbox = 'x' if new_status == 'completado' else ' '
                new_line = f"- [{checkbox}] {new_title}"
                
                if new_deadline:
                    new_line += f" [deadline: {new_deadline}]"
                if new_priority and new_priority != 'media':
                    new_line += f" [priority: {new_priority}]"
                if new_status == 'completado':
                    new_line += f" (completado: {datetime.now().strftime('%Y-%m-%d')})"
                elif new_status == 'en progreso':
                    new_line += " (en progreso)"
                
                new_lines.append(new_line)
            else:
                new_lines.append(line)
        
        file_path.write_text('\n'.join(new_lines), encoding='utf-8')
    
    def delete_task(self, title: str, category: str):
        """Remove a task from the Obsidian file"""
        file_path = self.vault_paths.get(category)
        if not file_path or not file_path.exists():
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
        
        if not self.rough_notes_folder.exists():
            return notes
        
        for file_path in self.rough_notes_folder.glob("*.md"):
            try:
                content = file_path.read_text(encoding='utf-8')
                
                title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
                title = title_match.group(1) if title_match else file_path.stem
                
                notes.append({
                    'title': title,
                    'file_path': str(file_path),
                    'modified': datetime.fromtimestamp(file_path.stat().st_mtime)
                })
            except Exception:
                continue
        
        return sorted(notes, key=lambda x: x['modified'], reverse=True)
        
    def update_quick_note(self, file_path: str, title: str, content: str) -> bool:
        """Update existing quick note"""
        if not file_path or not os.path.exists(file_path):
            return False
            
        try:
            # Read creation time if possible
            created_line = f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            existing_content = Path(file_path).read_text(encoding='utf-8')
            match = re.search(r'Created: \d{4}-\d{2}-\d{2} \d{2}:\d{2}', existing_content)
            if match:
                created_line = match.group(0)

            # Overwrite content
            note_content = f"""# {title}

{created_line}
Updated: {datetime.now().strftime("%Y-%m-%d %H:%M")}

---

{content}
"""
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(note_content)
                
            return True
        except Exception as e:
            print(f"Error updating note: {e}")
            return False
