"""
File Organization Utility
Automatically organize files by type, date, or custom rules
"""

import os
from typing import Dict, List, Optional, Callable
from datetime import datetime
import shutil

__all__ = [
    'organize_by_extension',
    'organize_by_date',
    'organize_by_size',
    'organize_by_name_pattern',
    'create_folder_structure',
    'move_files_safely',
    'get_file_categories',
    'scan_directory',
    'undo_organization',
    'organize_ext',
    'organize_date',
    'organize_size',
    'organize_pattern',
]


# File type categories
FILE_CATEGORIES = {
    'Images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.ico'],
    'Videos': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'],
    'Audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'],
    'Documents': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.pages'],
    'Spreadsheets': ['.xls', '.xlsx', '.csv', '.ods', '.numbers'],
    'Presentations': ['.ppt', '.pptx', '.key', '.odp'],
    'Archives': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'],
    'Code': ['.py', '.js', '.java', '.cpp', '.c', '.html', '.css', '.php', '.rb', '.go'],
    'Executables': ['.exe', '.app', '.dmg', '.deb', '.rpm'],
    'Others': []
}


def get_file_categories() -> Dict[str, List[str]]:
    """
    Get predefined file categories.
    
    Returns:
        dict: File categories with extensions
    
    Examples:
        >>> from ilovetools.automation import get_file_categories
        
        >>> categories = get_file_categories()
        >>> print(categories['Images'])
        ['.jpg', '.jpeg', '.png', ...]
    """
    return FILE_CATEGORIES.copy()


def scan_directory(
    directory: str,
    recursive: bool = False,
    include_hidden: bool = False
) -> Dict[str, List[str]]:
    """
    Scan directory and categorize files.
    
    Args:
        directory: Directory path to scan
        recursive: Scan subdirectories
        include_hidden: Include hidden files
    
    Returns:
        dict: Categorized file paths
    
    Examples:
        >>> from ilovetools.automation import scan_directory
        
        >>> files = scan_directory('/path/to/folder')
        >>> print(files['Images'])
        ['/path/to/folder/photo.jpg', ...]
    """
    if not os.path.exists(directory):
        raise ValueError(f"Directory does not exist: {directory}")
    
    categorized = {category: [] for category in FILE_CATEGORIES.keys()}
    
    if recursive:
        for root, dirs, files in os.walk(directory):
            if not include_hidden:
                files = [f for f in files if not f.startswith('.')]
                dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                filepath = os.path.join(root, file)
                ext = os.path.splitext(file)[1].lower()
                
                categorized_flag = False
                for category, extensions in FILE_CATEGORIES.items():
                    if ext in extensions:
                        categorized[category].append(filepath)
                        categorized_flag = True
                        break
                
                if not categorized_flag:
                    categorized['Others'].append(filepath)
    else:
        files = os.listdir(directory)
        if not include_hidden:
            files = [f for f in files if not f.startswith('.')]
        
        for file in files:
            filepath = os.path.join(directory, file)
            if os.path.isfile(filepath):
                ext = os.path.splitext(file)[1].lower()
                
                categorized_flag = False
                for category, extensions in FILE_CATEGORIES.items():
                    if ext in extensions:
                        categorized[category].append(filepath)
                        categorized_flag = True
                        break
                
                if not categorized_flag:
                    categorized['Others'].append(filepath)
    
    return categorized


def create_folder_structure(
    base_directory: str,
    folders: List[str],
    dry_run: bool = False
) -> Dict[str, str]:
    """
    Create folder structure for organization.
    
    Args:
        base_directory: Base directory path
        folders: List of folder names to create
        dry_run: Preview without creating
    
    Returns:
        dict: Created folder paths
    
    Examples:
        >>> from ilovetools.automation import create_folder_structure
        
        >>> folders = create_folder_structure(
        ...     '/path/to/organize',
        ...     ['Images', 'Videos', 'Documents']
        ... )
        >>> print(folders)
        {'Images': '/path/to/organize/Images', ...}
    """
    created = {}
    
    for folder in folders:
        folder_path = os.path.join(base_directory, folder)
        created[folder] = folder_path
        
        if not dry_run:
            os.makedirs(folder_path, exist_ok=True)
    
    return created


def move_files_safely(
    files: List[str],
    destination: str,
    dry_run: bool = False,
    overwrite: bool = False
) -> Dict[str, str]:
    """
    Move files safely with conflict handling.
    
    Args:
        files: List of file paths to move
        destination: Destination directory
        dry_run: Preview without moving
        overwrite: Overwrite existing files
    
    Returns:
        dict: Moved file mappings (old -> new)
    
    Examples:
        >>> from ilovetools.automation import move_files_safely
        
        >>> moved = move_files_safely(
        ...     ['/path/file1.jpg', '/path/file2.jpg'],
        ...     '/path/Images',
        ...     dry_run=True
        ... )
        >>> print(moved)
        {'/path/file1.jpg': '/path/Images/file1.jpg', ...}
    """
    moved = {}
    
    for filepath in files:
        if not os.path.exists(filepath):
            continue
        
        filename = os.path.basename(filepath)
        dest_path = os.path.join(destination, filename)
        
        # Handle conflicts
        if os.path.exists(dest_path) and not overwrite:
            base, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(dest_path):
                new_filename = f"{base}_{counter}{ext}"
                dest_path = os.path.join(destination, new_filename)
                counter += 1
        
        moved[filepath] = dest_path
        
        if not dry_run:
            shutil.move(filepath, dest_path)
    
    return moved


def organize_by_extension(
    directory: str,
    dry_run: bool = False,
    recursive: bool = False,
    custom_categories: Optional[Dict[str, List[str]]] = None
) -> Dict[str, Dict[str, str]]:
    """
    Organize files by extension into categorized folders.
    
    Alias: organize_ext()
    
    Args:
        directory: Directory to organize
        dry_run: Preview without organizing
        recursive: Include subdirectories
        custom_categories: Custom file categories
    
    Returns:
        dict: Organization results
    
    Examples:
        >>> from ilovetools.automation import organize_ext
        
        >>> result = organize_ext('/path/to/messy', dry_run=True)
        >>> print(result['Images'])
        {'/path/photo.jpg': '/path/Images/photo.jpg', ...}
    """
    categories = custom_categories or FILE_CATEGORIES
    
    # Scan directory
    categorized = scan_directory(directory, recursive=recursive)
    
    # Create folder structure
    folders_to_create = [cat for cat, files in categorized.items() if files]
    folder_paths = create_folder_structure(directory, folders_to_create, dry_run)
    
    # Move files
    results = {}
    for category, files in categorized.items():
        if files and category in folder_paths:
            moved = move_files_safely(files, folder_paths[category], dry_run)
            results[category] = moved
    
    return results


# Alias
organize_ext = organize_by_extension


def organize_by_date(
    directory: str,
    date_format: str = '%Y-%m',
    dry_run: bool = False,
    use_modified_date: bool = True
) -> Dict[str, Dict[str, str]]:
    """
    Organize files by date into folders.
    
    Alias: organize_date()
    
    Args:
        directory: Directory to organize
        date_format: Date format for folder names (%Y-%m, %Y, %Y-%m-%d)
        dry_run: Preview without organizing
        use_modified_date: Use modified date (else creation date)
    
    Returns:
        dict: Organization results
    
    Examples:
        >>> from ilovetools.automation import organize_date
        
        >>> result = organize_date('/path/to/photos', date_format='%Y-%m')
        >>> print(result.keys())
        dict_keys(['2024-01', '2024-02', ...])
    """
    if not os.path.exists(directory):
        raise ValueError(f"Directory does not exist: {directory}")
    
    # Scan files
    files = []
    for item in os.listdir(directory):
        filepath = os.path.join(directory, item)
        if os.path.isfile(filepath):
            files.append(filepath)
    
    # Group by date
    date_groups = {}
    for filepath in files:
        if use_modified_date:
            timestamp = os.path.getmtime(filepath)
        else:
            timestamp = os.path.getctime(filepath)
        
        date_obj = datetime.fromtimestamp(timestamp)
        date_str = date_obj.strftime(date_format)
        
        if date_str not in date_groups:
            date_groups[date_str] = []
        date_groups[date_str].append(filepath)
    
    # Create folders and move files
    results = {}
    for date_str, file_list in date_groups.items():
        folder_path = os.path.join(directory, date_str)
        
        if not dry_run:
            os.makedirs(folder_path, exist_ok=True)
        
        moved = move_files_safely(file_list, folder_path, dry_run)
        results[date_str] = moved
    
    return results


# Alias
organize_date = organize_by_date


def organize_by_size(
    directory: str,
    size_ranges: Optional[Dict[str, tuple]] = None,
    dry_run: bool = False
) -> Dict[str, Dict[str, str]]:
    """
    Organize files by size into folders.
    
    Alias: organize_size()
    
    Args:
        directory: Directory to organize
        size_ranges: Custom size ranges in bytes
        dry_run: Preview without organizing
    
    Returns:
        dict: Organization results
    
    Examples:
        >>> from ilovetools.automation import organize_size
        
        >>> result = organize_size('/path/to/files')
        >>> print(result.keys())
        dict_keys(['Small', 'Medium', 'Large', 'Huge'])
    """
    if not os.path.exists(directory):
        raise ValueError(f"Directory does not exist: {directory}")
    
    # Default size ranges (in bytes)
    if size_ranges is None:
        size_ranges = {
            'Small': (0, 1024 * 1024),  # 0-1MB
            'Medium': (1024 * 1024, 10 * 1024 * 1024),  # 1-10MB
            'Large': (10 * 1024 * 1024, 100 * 1024 * 1024),  # 10-100MB
            'Huge': (100 * 1024 * 1024, float('inf'))  # 100MB+
        }
    
    # Scan files
    files = []
    for item in os.listdir(directory):
        filepath = os.path.join(directory, item)
        if os.path.isfile(filepath):
            files.append(filepath)
    
    # Group by size
    size_groups = {category: [] for category in size_ranges.keys()}
    
    for filepath in files:
        file_size = os.path.getsize(filepath)
        
        for category, (min_size, max_size) in size_ranges.items():
            if min_size <= file_size < max_size:
                size_groups[category].append(filepath)
                break
    
    # Create folders and move files
    results = {}
    for category, file_list in size_groups.items():
        if file_list:
            folder_path = os.path.join(directory, category)
            
            if not dry_run:
                os.makedirs(folder_path, exist_ok=True)
            
            moved = move_files_safely(file_list, folder_path, dry_run)
            results[category] = moved
    
    return results


# Alias
organize_size = organize_by_size


def organize_by_name_pattern(
    directory: str,
    patterns: Dict[str, Callable[[str], bool]],
    dry_run: bool = False
) -> Dict[str, Dict[str, str]]:
    """
    Organize files by name patterns.
    
    Alias: organize_pattern()
    
    Args:
        directory: Directory to organize
        patterns: Dict of folder_name -> pattern_function
        dry_run: Preview without organizing
    
    Returns:
        dict: Organization results
    
    Examples:
        >>> from ilovetools.automation import organize_pattern
        
        >>> patterns = {
        ...     'Work': lambda name: 'work' in name.lower(),
        ...     'Personal': lambda name: 'personal' in name.lower(),
        ... }
        >>> result = organize_pattern('/path/to/files', patterns)
    """
    if not os.path.exists(directory):
        raise ValueError(f"Directory does not exist: {directory}")
    
    # Scan files
    files = []
    for item in os.listdir(directory):
        filepath = os.path.join(directory, item)
        if os.path.isfile(filepath):
            files.append(filepath)
    
    # Group by pattern
    pattern_groups = {category: [] for category in patterns.keys()}
    pattern_groups['Unmatched'] = []
    
    for filepath in files:
        filename = os.path.basename(filepath)
        matched = False
        
        for category, pattern_func in patterns.items():
            if pattern_func(filename):
                pattern_groups[category].append(filepath)
                matched = True
                break
        
        if not matched:
            pattern_groups['Unmatched'].append(filepath)
    
    # Create folders and move files
    results = {}
    for category, file_list in pattern_groups.items():
        if file_list:
            folder_path = os.path.join(directory, category)
            
            if not dry_run:
                os.makedirs(folder_path, exist_ok=True)
            
            moved = move_files_safely(file_list, folder_path, dry_run)
            results[category] = moved
    
    return results


# Alias
organize_pattern = organize_by_name_pattern


def undo_organization(
    organization_result: Dict[str, Dict[str, str]],
    dry_run: bool = False
) -> Dict[str, str]:
    """
    Undo file organization by moving files back.
    
    Args:
        organization_result: Result from organize functions
        dry_run: Preview without undoing
    
    Returns:
        dict: Restored file mappings
    
    Examples:
        >>> from ilovetools.automation import organize_ext, undo_organization
        
        >>> result = organize_ext('/path/to/files')
        >>> # Undo if needed
        >>> restored = undo_organization(result)
    """
    restored = {}
    
    for category, file_mappings in organization_result.items():
        for old_path, new_path in file_mappings.items():
            if os.path.exists(new_path):
                restored[new_path] = old_path
                
                if not dry_run:
                    # Create parent directory if needed
                    os.makedirs(os.path.dirname(old_path), exist_ok=True)
                    shutil.move(new_path, old_path)
    
    return restored
