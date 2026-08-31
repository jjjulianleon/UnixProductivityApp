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
    
    def __init__(self, vault_paths: Optional[Dict[str, Path]] = None,
                 rough_notes_folder: Optional[Path] = None):
        """Sin argumentos usa el vault real; los tests inyectan rutas temporales.

        Se inyecta en vez de depender de $UNIDEX_OBSIDIAN_VAULT porque
        constants.py resuelve las rutas al importarse: si otro modulo importa
        src antes, la variable de entorno ya no cambia nada y los tests
        acabarian escribiendo en el vault de verdad.
        """
        self.vault_paths = vault_paths if vault_paths is not None else OBSIDIAN_VAULT_PATHS
        self.rough_notes_folder = rough_notes_folder or OBSIDIAN_ROUGH_NOTES

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
    
    DESC_INDENT = "  "

    def _parse_tasks_file(self, file_path: Path, category: str) -> List[Dict]:
        """Parse tasks from a single Obsidian file"""
        try:
            lines = file_path.read_text(encoding='utf-8').split('\n')
        except Exception:
            return []

        tasks = []
        index = 0
        while index < len(lines):
            task = self._parse_task_line(lines[index])
            if not task:
                index += 1
                continue

            index += 1
            # La descripcion multilinea va indentada debajo de la tarea; si la
            # tarea traia el formato "titulo | descripcion" ese gana.
            block, index = self._take_description_block(lines, index)
            if block and not task['description']:
                task['description'] = block

            task['category'] = category
            tasks.append(task)

        return tasks

    @classmethod
    def _take_description_block(cls, lines: List[str], index: int) -> tuple:
        """Consume las lineas indentadas que siguen a una tarea. Devuelve (texto, indice)"""
        collected = []
        while index < len(lines):
            line = lines[index]
            # Se acaba en cuanto aparece algo sin indentar, una linea en blanco
            # o una subtarea (que es una tarea por derecho propio).
            if not line.strip() or not line[:1].isspace() or cls._parse_task_line(line):
                break
            collected.append(line.strip())
            index += 1
        return '\n'.join(collected), index

    @staticmethod
    def _parse_task_line(line: str) -> Optional[Dict]:
        """Descompone una linea "- [ ] ..." en sus campos, o None si no lo es.

        Es el unico sitio que sabe leer el formato: leer, actualizar y borrar
        pasan por aqui, para que los tres entiendan lo mismo por "titulo".
        """
        basic_match = re.match(r'^- \[([ xX])\] (.+)$', line.strip())
        if not basic_match:
            return None

        checkbox, raw_text = basic_match.groups()
        is_completed = checkbox.lower() == 'x'

        title = raw_text.strip()
        deadline = None
        priority = 'media'
        status = 'completado' if is_completed else 'pendiente'

        # (en progreso)
        if '(en progreso)' in title.lower():
            status = 'en progreso' if not is_completed else 'completado'
            title = re.sub(r'\s*\(en progreso\)', '', title, flags=re.IGNORECASE)

        # [deadline: YYYY-MM-DD]
        deadline_match = re.search(r'\[deadline:\s*(\d{4}-\d{2}-\d{2})\]', title)
        if deadline_match:
            deadline = deadline_match.group(1)
            title = re.sub(r'\s*\[deadline:\s*\d{4}-\d{2}-\d{2}\]', '', title)

        # Formato emoji de Obsidian Tasks: 📅 YYYY-MM-DD
        emoji_deadline = re.search(r'[📅🗓️]\s*(\d{4}-\d{2}-\d{2})', title)
        if emoji_deadline and not deadline:
            deadline = emoji_deadline.group(1)
            title = re.sub(r'\s*[📅🗓️]\s*\d{4}-\d{2}-\d{2}', '', title)

        # [priority: xxx]
        priority_match = re.search(r'\[priority:\s*(\w+)\]', title, re.IGNORECASE)
        if priority_match:
            priority = priority_match.group(1).lower()
            title = re.sub(r'\s*\[priority:\s*\w+\]', '', title, flags=re.IGNORECASE)

        # Marcas de completado
        title = re.sub(r'\s*✅\s*\d{4}-\d{2}-\d{2}', '', title)
        title = re.sub(r'\s*\(completado:\s*\d{4}-\d{2}-\d{2}\)', '', title)

        # "titulo | descripcion"
        description = ''
        if ' | ' in title:
            # Formato antiguo, escrito a mano: "titulo | descripcion"
            title, description = (part.strip() for part in title.split(' | ', 1))

        title = title.strip()
        if not title:
            return None

        return {
            'title': title,
            'description': description,
            'status': status,
            'deadline': deadline,
            'priority': priority,
        }

    @staticmethod
    def _task_line(title: str, status: str = "pendiente", deadline: Optional[str] = None,
                   priority: str = "media", description: str = "") -> str:
        """Compone la linea markdown. Contrapartida exacta de _parse_task_line."""
        line = f"- [{'x' if status == 'completado' else ' '}] {title}"
        if deadline:
            line += f" [deadline: {deadline}]"
        if priority and priority != 'media':
            line += f" [priority: {priority}]"
        if status == 'completado':
            line += f" (completado: {datetime.now().strftime('%Y-%m-%d')})"
        elif status == 'en progreso':
            line += " (en progreso)"
        return line

    @classmethod
    def _task_block(cls, title: str, status: str = "pendiente", deadline: Optional[str] = None,
                    priority: str = "media", description: str = "") -> List[str]:
        """La tarea y, debajo, su descripcion indentada. Contrapartida del parser.

        Se indenta en vez de meterlo todo en una linea porque estos archivos se
        leen y editan en Obsidian: un "\\n" literal en medio de la tarea es
        ilegible.
        """
        block = [cls._task_line(title, status, deadline, priority)]
        if description and description.strip():
            block += [cls.DESC_INDENT + part.strip()
                      for part in description.strip().replace('\r\n', '\n').split('\n')]
        return block

    def add_task(self, title: str, category: str, status: str = "pendiente",
                 deadline: Optional[str] = None, priority: str = "media",
                 description: str = ""):
        """Add a task to the appropriate Obsidian file"""
        file_path = self.vault_paths.get(category)
        if not file_path:
            return

        file_path.parent.mkdir(parents=True, exist_ok=True)
        if not file_path.exists():
            file_path.write_text(f"# Pendientes {category}\n\n", encoding='utf-8')

        content = file_path.read_text(encoding='utf-8')
        # Si el archivo del usuario no terminaba en salto de linea, la tarea
        # nueva se pegaba al final de la ultima linea existente.
        if content and not content.endswith('\n'):
            content += '\n'

        content += '\n'.join(self._task_block(title, status, deadline, priority,
                                              description)) + '\n'
        file_path.write_text(content, encoding='utf-8')

    def update_task(self, old_title: str, category: str, **kwargs):
        """Update a task in the Obsidian file"""
        file_path = self.vault_paths.get(category)
        if not file_path or not file_path.exists():
            return

        lines = file_path.read_text(encoding='utf-8').split('\n')
        result = []
        index = 0
        while index < len(lines):
            task = self._parse_task_line(lines[index])
            # Comparacion por titulo exacto: con "old_title in line" actualizar
            # "Estudiar" reescribia tambien "Estudiar calculo".
            if not task or task['title'] != old_title:
                result.append(lines[index])
                index += 1
                continue

            index += 1
            block_desc, index = self._take_description_block(lines, index)
            current_desc = task['description'] or block_desc

            result += self._task_block(
                kwargs.get('title', task['title']),
                kwargs.get('status', task['status']),
                kwargs.get('deadline', task['deadline']),
                kwargs.get('priority', task['priority']),
                kwargs.get('description', current_desc),
            )

        file_path.write_text('\n'.join(result), encoding='utf-8')

    def delete_task(self, title: str, category: str):
        """Remove a task from the Obsidian file"""
        file_path = self.vault_paths.get(category)
        if not file_path or not file_path.exists():
            return

        lines = file_path.read_text(encoding='utf-8').split('\n')
        kept = []
        index = 0
        while index < len(lines):
            task = self._parse_task_line(lines[index])
            # Idem: "title in line" borraba toda tarea cuyo texto contuviera
            # el titulo, no solo la que se pidio borrar.
            if task and task['title'] == title:
                index += 1
                _, index = self._take_description_block(lines, index)  # y su descripcion
                continue
            kept.append(lines[index])
            index += 1

        file_path.write_text('\n'.join(kept), encoding='utf-8')

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
