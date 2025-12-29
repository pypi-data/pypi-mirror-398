"""File Organizer - Organize files by extension."""

import os
import shutil
import argparse


class FileOrganizer:
    def __init__(self, directory: str):
        if not os.path.isdir(directory):
            raise ValueError(f"{directory} is not a valid directory.")
        self.directory = directory

    def organize(self) -> None:
        for filename in os.listdir(self.directory):
            file_path = os.path.join(self.directory, filename)

            if os.path.isfile(file_path):
                ext = os.path.splitext(filename)[1].lower().strip(".")
                if not ext:
                    ext = "no_extension"

                target_dir = os.path.join(self.directory, ext)
                os.makedirs(target_dir, exist_ok=True)

                shutil.move(file_path, os.path.join(target_dir, filename))
                print(f"Moved: {filename} -> {target_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Organize files by extension.")
    parser.add_argument("directory", help="Path to the directory to organize")
    args = parser.parse_args()

    organizer = FileOrganizer(args.directory)
    organizer.organize()


if __name__ == "__main__":
    main()
