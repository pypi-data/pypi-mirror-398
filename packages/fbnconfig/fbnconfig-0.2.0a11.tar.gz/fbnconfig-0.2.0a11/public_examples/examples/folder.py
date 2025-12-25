import pathlib

from fbnconfig import Deployment, drive

"""
An example configuration for LUSID Drive's folder structure.
The script configures the following entities:
- Folder
- File

and builds the following structure in drive:

    basefolder/
        subfolder/
            subfolder2/
                file.txt

where file.txt contains the content of the local file lorem-ipsum.txt

More information can be found here:
https://support.lusid.com/knowledgebase/article/KA-01672/
https://support.lusid.com/knowledgebase/article/KA-01635/
"""


def configure(env):
    f1 = drive.FolderResource(id="base_folder", name="example_directory", parent=drive.root)
    f2 = drive.FolderResource(id="sub_folder", name="subfolder", parent=f1)
    f3 = drive.FolderResource(id="sub_sub_folder", name="subfolder2", parent=f2)

    content_path = (pathlib.Path(__file__).parent.parent.resolve()
                    / pathlib.Path("./data/lorem-ipsum.txt"))
    ff = drive.FileResource(id="file1", folder=f3, name="file.txt", content_path=content_path)
    return Deployment("folder_example", [f1, f2, f3, ff])
