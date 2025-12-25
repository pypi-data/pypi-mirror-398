# DOSBox wrapper
import os
from pathlib import Path
import time
import shutil
import subprocess

import click

from .gtslogs import GtslogsArchiveFolder
from .utils import rmdir


@click.command()
@click.option("-d", "--dosbox", default="DOSBoxPortable.exe")
@click.option("-j", "--job", type=int, default=None)
@click.option(
    "-p", "--path", type=click.Path(file_okay=False, dir_okay=True), default=None
)
@click.option("--suffix", default="l20export")
def logger20(dosbox, job, path, suffix):
    # Constants
    conf_template = Path(__file__).parent / "logger20_dosbox.conf"
    mount_cdrive_folder = Path(__file__).parent / "logger20_image"

    gtslogs = GtslogsArchiveFolder()

    if job:
        print(f"--job {job}")
        job = gtslogs.job(job)
        # print(f"-> job {job}")
        working_folder = Path(job.path)
        # print(f"-> working_folder {working_folder}")
    elif path:
        print(f"--path {path}")
        working_folder = Path(str(path))
    else:
        print("error: you need to specify either --job or --path")
    dosbox_exe = Path(str(dosbox))
    assert working_folder.is_dir()
    # assert dosbox_exe.is_file()

    dosbox_logger20_folder = Path(r"c:\devapps\temp\logger20_dosbox")
    print(f"dosbox_logger20_folder: {dosbox_logger20_folder}")

    if dosbox_logger20_folder.is_dir():
        print(f"Removing {dosbox_logger20_folder} and contents...")
        try:
            rmdir(dosbox_logger20_folder)
        except:
            n = 1
            while Path(dosbox_logger20_folder).is_dir():
                dosbox_logger20_folder = Path(str(dosbox_logger20_folder) + f"{n}")
    if not dosbox_logger20_folder.parent.is_dir():
        dosbox_logger20_folder.parent.mkdir(parents=True)

    # print(f"Creating empty {dosbox_logger20_folder}")
    # dosbox_logger20_folder.mkdir(parents=True, exist_ok=True)
    logger20_project_template = dosbox_logger20_folder / "LOGGER20" / "PROJECTS" / "TMP"
    logger20_project_path = dosbox_logger20_folder / "LOGGER20" / "PROJECTS" / "WRK"
    conf = dosbox_logger20_folder / "dosbox.conf"

    print(f"Copying template from {mount_cdrive_folder} to {dosbox_logger20_folder}")
    shutil.copytree(mount_cdrive_folder, dosbox_logger20_folder)

    # Step 2. Create a blank project in tempdrive\logger20\projects\XYZ
    print(
        f"Copying template project dir from {logger20_project_template} to {logger20_project_path}"
    )
    shutil.copytree(logger20_project_template, logger20_project_path)

    # Step 3. Copy contents of project folder
    print(f"Copying contents of working folder {working_folder}")
    for fn in working_folder.glob("*.*"):
        if not str(fn).lower().endswith(".las"):
            print(f"  {fn} {logger20_project_path}")
            shutil.copy2(fn, logger20_project_path)

    # Step 4. Create temporary DOSBox conf file

    with open(conf_template, "r") as template_file:
        template = template_file.read()

    with open(conf, "w") as conf_file:
        conf_contents = template.format(
            c_drive=str(dosbox_logger20_folder),
            relative_project_path=os.sep.join(logger20_project_path.parts[-3:]),
        )
        conf_file.write(conf_contents)

    # Step 5. Run DOSBox and block
    cmd = str(dosbox_exe) + " -conf " + str(conf)
    dbox_init = subprocess.run(cmd, shell=False)
    print("Waiting for DOSBox to close...")
    n = 0
    wait = 0.1
    while True:
        n += 1
        p = subprocess.run("tasklist", stdout=subprocess.PIPE, shell=False)
        # proc_names = [p.name() for p in psutil.process_iter()]
        proc_names = [
            l.split()[0].decode("ascii")
            for l in p.stdout.splitlines()
            if len(l.split()) > 0
        ]
        dosbox_exes = [p for p in proc_names if "dosbox" in p.lower()]
        if len(dosbox_exes) == 0:
            print("... did not find active dosbox program, you must have finished!")
            break
        if n % 10 == 0:
            print("**** use Ctrl+C to force quit if Logger20 has crashed ****")
        else:
            print(".", end="")
        time.sleep(wait)

    # Step 6. When finished, copy any new LAS files back to project folder.
    print("Looking at LAS files in Logger20 temporary project folder:")
    las_fns = [Path(f) for f in logger20_project_path.glob("*.las")]
    for las_fn in las_fns:
        new_las_fn = las_fn.stem + f"_{suffix}.las"
        print(f"copying {new_las_fn}")
        shutil.copy(las_fn, working_folder / new_las_fn)

    shutil.rmtree(str(dosbox_logger20_folder))
