from fbnconfig import Deployment, drive, scheduler

"""
An example configuration for defining various entities.
The script configures the following entities:
- Folder
- File
- Image
- Job
- Schedule

For more information on these resources, please refer to their dedicated examples.
"""


def configure(env):
    client_folder = drive.FolderResource(id="base_folder", name="example_folder", parent=drive.root)
    files_folder = drive.FolderResource(id="files", name="files", parent=client_folder)

    content = """
    Lorem ipsum dolor sit amet, consectetur adipiscing elit. Phasellus non lobortis dolor. In sed neque
    pretium, mattis elit at, accumsan dolor. Donec tellus leo, sodales ac blandit eget, maximus et.
    """

    file = drive.FileResource(id="file1", folder=files_folder, name="mydata.txt", content=content)
    version = 32

    image = scheduler.ImageResource(
        id="img1",
        source_image="docker.io/alpine:latest",
        dest_name="mixed-example",
        dest_tag=f"v{version}",
    )

    job = scheduler.JobResource(
        id="job1",
        scope="sc1",
        code="mixed-job",
        image=image,
        name="Example job",
        description="Example job description",
    )

    schedule = scheduler.ScheduleResource(
        id="sch1",
        name="Example Schedule",
        scope="sc1",
        code="cd1",
        job=job,
        expression="0 50 4 * * ? *",
        timezone="Europe/London",
        description="Example shcedule description",
    )

    return Deployment("mixed_example", [client_folder, files_folder, file, image, job, schedule])
