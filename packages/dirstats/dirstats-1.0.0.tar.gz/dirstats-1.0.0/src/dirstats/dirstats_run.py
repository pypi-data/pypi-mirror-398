"""
Command-line utility for directory analysis with optional file filtering.

This module analyzes a given base directory and reports:
- Number of files matching the specified extensions
- Number of subdirectories containing matching files
- Aggregate size of the matching files

The tool supports analyzing all files using "*" or filtering by one or more
file extensions passed as command-line arguments. It is designed as a small,
reusable CLI utility built entirely with Python's standard library.
"""
import pathlib
import sys


def input_data()-> tuple[pathlib.Path, list[str]]:
    """
    Parse command-line input and return the base directory path
    along with optional file extension filters.

    Reads command-line arguments to obtain the base directory
    and an optional list of file extensions to be analyzed.

    Args:
        None

    Returns:
        tuple[pathlib.Path, list[str]]: A tuple containing:
            - pathlib.Path: Path object representing the base directory
              to be analyzed.
            - list[str]: List of file extensions to filter the analysis,
              or ["*"] to include all files.
    """
    filename: str
    file_extensions: list[str]
    base_path: pathlib.Path
    if len(sys.argv) == 2:
        filename = sys.argv[1]
        file_extensions = ["*"]
        base_path = pathlib.Path(filename)
        return (base_path, file_extensions)
    if len(sys.argv) >= 3:
        filename = sys.argv[1]
        file_extensions = [arg for arg in sys.argv[2:]]
        base_path = pathlib.Path(filename)
        if sys.argv[2] == "*":
            file_extensions = ["*"]
        return (base_path, file_extensions)
    
    exit("Missing 1 argument: The path of the base directory to analyze.")


def files_and_directory_paths(base_path: pathlib.Path)-> list[pathlib.PosixPath]:
    """
    Retrieve all file and directory paths under a base directory.

    Validates that the base path exists and recursively collects
    all files and subdirectories using glob patterns.

    Args:
        base_path (pathlib.Path): Base directory path to analyze.

    Returns:
        list[pathlib.PosixPath]: List of file and directory paths
            found under the base directory.
    """
    if base_path.exists():
        print("The base directory is correct.")  
    else:
        exit("The base directory is incorrect.")
    result: list[pathlib.PosixPath] = list(base_path.glob(pattern='**/*'))
    return result


def processing_and_analysis(data: list[pathlib.PosixPath], file_extensions: list[str])-> dict[str, int]:
    """
    Analyze file system paths and collect statistics based on file extensions.

    Iterates over a list of file system paths, counting files, identifying
    relevant subfolders, and calculating the cumulative size of matching files.
    Supports filtering by file extensions or analyzing all files using "*".

    Args:
        data (list[pathlib.PosixPath]): List of file and directory paths
            to be analyzed.
        file_extensions (list[str]): List of file extensions to include
            in the analysis, or ["*"] to include all files.

    Returns:
        dict[str, int]: Dictionary containing:
            - "files": Number of matching files.
            - "subfolders": Number of subfolders containing matching files.
            - "total_size": Total size in bytes of matching files.
    """
    files: int = 0
    subfolders: int = 0
    total_size: int = 0
    subfolders_cache: set[pathlib.PosixPath] = set()

    for item in data:
        if item.is_file():
            if file_extensions[0] == "*":
                files += 1
                total_size += item.stat().st_size
                continue
            elif item.name.split(".")[-1] in file_extensions:
                files += 1
                total_size += item.stat().st_size
                subfolders_cache.add(item.parent)
                continue

        if item.is_dir():
            subfolders += 1

    if file_extensions[0] != "*":
        subfolders = len(subfolders_cache)

    result: dict[str, int] = {"files": files, "subfolders":subfolders, "total_size":total_size}
    return result


def output_data(data: dict[str, int])-> None:
    """
    Display analysis results to standard output.

    Prints the number of files, subfolders, and the total directory size
    in multiple units for easier interpretation.

    Args:
        data (dict[str, int]): Dictionary containing analysis results with the
            following keys: 'files', 'subfolders', and 'total_size'.

    Returns:
        None
    """
    files: int = data["files"]
    subfolders: int = data["subfolders"]
    print(f"Number of files: {files}")
    print(f"Number of subfolders: {subfolders}")
    size: int = data['total_size']
    print(f"Total directory size: {round(size, 2)} Bytes...")
    print(f"Total directory size: {round(size / 1024, 2)} KiloBytes...")
    print(f"Total directory size: {round(size / (1024 ** 2), 2)} MegaBytes...")
    print(f"Total directory size: {round(size / (1024 ** 3), 2)} GigaBytes...")

    if files == 0 and subfolders == 0:
        print(f"Note: There are no subfolders or files in the base directory to be analyzed.")
    elif subfolders == 0:
        print(f"Note: There are no subfolders in this base directory.")
    elif files == 0:
        print(f"Note: There are no files in this base directory.")
    elif size == 0:
        print(f"The files in this base directory are empty.")



def main()-> None:
    """
    Main application workflow.

    Coordinates user input, file system traversal, data processing,
    and output generation to analyze files and directories.

    Args:
        None

    Returns:
        None
    """
    base_path: pathlib.Path
    file_extensions: list[str]
    base_path, file_extensions = input_data()
    data: list[pathlib.PosixPath] = files_and_directory_paths(base_path)
    result: dict[str, int] = processing_and_analysis(data, file_extensions)
    output_data(result)


def test()-> None:
    """
    Run doctests for the current module.

    Executes all doctest examples defined in docstrings within this module
    and reports detailed results for validation and debugging purposes.

    Args:
        None

    Returns:
        None
    """
    import doctest
    doctest.testmod(verbose=True)


if __name__ == "__main__":
    """
    Entry point of the script.

    Executes the main application logic when the file is run directly.
    This prevents the main workflow from executing on import.
    """
    #test()
    main()