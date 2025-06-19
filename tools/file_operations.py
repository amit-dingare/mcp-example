"""File operations tool for reading, writing, and listing files"""
import os
from pathlib import Path

TOOL_NAME = "file_operations"
TOOL_DESCRIPTION = "Perform file operations like read, write, list files and directories"

async def tool_function(operation: str, path: str, content: str = "") -> str:
    """Perform file operations"""
    try:
        # Validate operation
        valid_operations = ["read", "write", "list", "exists", "size", "delete"]
        if operation not in valid_operations:
            return f"❌ Invalid operation: {operation}. Valid operations: {', '.join(valid_operations)}"
        
        # Convert to Path object for better handling
        file_path = Path(path)
        
        # Security check - prevent access to sensitive system files
        resolved_path = file_path.resolve()
        current_dir = Path.cwd().resolve()
        
        # Only allow operations within current directory and subdirectories
        try:
            resolved_path.relative_to(current_dir)
        except ValueError:
            return f"❌ Security Error: Access denied to {path} (outside current directory)"
        
        if operation == "read":
            if not file_path.exists():
                return f"❌ File not found: {path}"
            
            if not file_path.is_file():
                return f"❌ Path is not a file: {path}"
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                
                # Limit output for very large files
                if len(file_content) > 10000:
                    return f"📄 File content (first 10,000 characters):\n{file_content[:10000]}\n\n... (file truncated, total size: {len(file_content)} characters)"
                else:
                    return f"📄 File content:\n{file_content}"
            
            except UnicodeDecodeError:
                return f"❌ Error: Cannot read file as text (binary file?): {path}"
        
        elif operation == "write":
            if not content:
                return f"❌ Error: No content provided for write operation"
            
            # Create parent directories if they don't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return f"✅ Successfully wrote {len(content)} characters to {path}"
        
        elif operation == "list":
            if not file_path.exists():
                return f"❌ Directory not found: {path}"
            
            if not file_path.is_dir():
                return f"❌ Path is not a directory: {path}"
            
            try:
                items = []
                for item in sorted(file_path.iterdir()):
                    if item.is_dir():
                        items.append(f"📁 {item.name}/")
                    else:
                        size = item.stat().st_size
                        if size < 1024:
                            size_str = f"{size}B"
                        elif size < 1024 * 1024:
                            size_str = f"{size/1024:.1f}KB"
                        else:
                            size_str = f"{size/(1024*1024):.1f}MB"
                        items.append(f"📄 {item.name} ({size_str})")
                
                if not items:
                    return f"📁 Directory {path} is empty"
                
                return f"📁 Contents of {path}:\n" + "\n".join(items)
            
            except PermissionError:
                return f"❌ Permission denied: {path}"
        
        elif operation == "exists":
            if file_path.exists():
                if file_path.is_file():
                    return f"✅ File exists: {path}"
                elif file_path.is_dir():
                    return f"✅ Directory exists: {path}"
                else:
                    return f"✅ Path exists (special file): {path}"
            else:
                return f"❌ Path does not exist: {path}"
        
        elif operation == "size":
            if not file_path.exists():
                return f"❌ Path not found: {path}"
            
            if file_path.is_file():
                size = file_path.stat().st_size
                if size < 1024:
                    size_str = f"{size} bytes"
                elif size < 1024 * 1024:
                    size_str = f"{size/1024:.2f} KB"
                elif size < 1024 * 1024 * 1024:
                    size_str = f"{size/(1024*1024):.2f} MB"
                else:
                    size_str = f"{size/(1024*1024*1024):.2f} GB"
                
                return f"📏 File size: {path} = {size_str}"
            
            elif file_path.is_dir():
                total_size = 0
                file_count = 0
                for item in file_path.rglob('*'):
                    if item.is_file():
                        total_size += item.stat().st_size
                        file_count += 1
                
                if total_size < 1024:
                    size_str = f"{total_size} bytes"
                elif total_size < 1024 * 1024:
                    size_str = f"{total_size/1024:.2f} KB"
                elif total_size < 1024 * 1024 * 1024:
                    size_str = f"{total_size/(1024*1024):.2f} MB"
                else:
                    size_str = f"{total_size/(1024*1024*1024):.2f} GB"
                
                return f"📏 Directory size: {path} = {size_str} ({file_count} files)"
        
        elif operation == "delete":
            if not file_path.exists():
                return f"❌ Path not found: {path}"
            
            if file_path.is_file():
                file_path.unlink()
                return f"🗑️ Successfully deleted file: {path}"
            elif file_path.is_dir():
                # Only delete if directory is empty for safety
                try:
                    file_path.rmdir()
                    return f"🗑️ Successfully deleted empty directory: {path}"
                except OSError:
                    return f"❌ Cannot delete directory (not empty): {path}. Use a file manager for non-empty directories."
            
    except PermissionError:
        return f"❌ Permission denied: {path}"
    except OSError as e:
        return f"❌ OS Error: {str(e)}"
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}"