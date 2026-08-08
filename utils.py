import os


def format_size(size):

    units = ["B", "KB", "MB", "GB", "TB"]

    for unit in units:

        if size < 1024:
            return f"{size:.2f} {unit}"

        size /= 1024

    return f"{size:.2f} PB"


def calculate_wasted_space(duplicates):

    wasted_space = 0

    for file_paths in duplicates.values():

        if len(file_paths) > 1:

            try:
                file_size = os.path.getsize(file_paths[0])

                wasted_space += file_size * (len(file_paths) - 1)

            except OSError:
                continue

    return wasted_space