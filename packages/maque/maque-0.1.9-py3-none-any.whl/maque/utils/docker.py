import os
from glob import glob
try:
    from maque import probar
except ImportError:
    probar = lambda x: x  # fallback
from typing import List


def save_docker_images(filedir='.', skip_exists=True, use_stream=False):
    import docker
    from docker.models.images import Image
    client = docker.from_env()
    images_list: List[Image] = client.images.list()
    exist_image_ids = []
    for i in glob(os.path.join(filedir, "*")):
        prefix, filename = os.path.split(i)
        token_list = filename.split(',')
        if len(token_list) > 1:
            exist_image_ids.append(token_list[-1])
    for image in probar(images_list):
        image: Image
        if image.tags:
            if image.id.split(':')[-1] in exist_image_ids and skip_exists:
                print(f"\n image: {image.id} exists, skipping")
            else:
                save_simgle_image(image, filedir, use_stream)


def save_simgle_image(image, filedir='.', use_stream=False):
    image_id = image.id.split(':')[-1]
    filename = f"{image.tags[0].replace('/', '#').replace(':', '@')},{image_id}"
    filepath = os.path.join(filedir, filename)

    if use_stream:
        print(f"\n saving image [{image.tags[0]}] to:", filepath)
        with open(filepath, 'wb') as f:
            for chunk in image.save(named=True):
                f.write(chunk)
    else:
        filepath += ".gz"
        print(f"\n saving image [{image.tags[0]}] to:", filepath)
        image_name = image.tags[0]
        os.system(f"docker save {image_name} | gzip > {filepath}")


def add_tag_to_files(filedir='.'):
    from docker.models.images import Image
    import docker
    client = docker.from_env()
    images_list: List[Image] = client.images.list()
    image_ids_map = dict([[image.id.split(':')[1], str(idx)] for idx, image in enumerate(images_list)])
    file_image_ids = [[i.split('/')[-1], i] for i in glob(os.path.join(filedir, "*"))]
    for file_image_id, filename in file_image_ids:
        str_image_idx = image_ids_map.get(file_image_id)
        if str_image_idx:
            image = images_list[int(str_image_idx)]
            prefix, file_id_name = os.path.split(filename)
            os.rename(filename,
                      str(os.path.join(prefix, f"{image.tags[0].replace('/', '#').replace(':', '@')},{file_id_name}")))


def load_docker_images(filename_pattern="./*", skip_exists=True):
    from docker.models.images import Image
    import docker
    client = docker.from_env()
    images_list: List[Image] = client.images.list()
    exist_image_ids = [image.id.split(":")[-1] for image in images_list]

    for filename in probar(glob(filename_pattern)):
        filename: str
        file_name = os.path.split(filename)[-1]
        file_image_id = file_name.split(',')[1]
        if file_image_id in exist_image_ids and skip_exists:
            print(f"\n image id: {file_image_id} exists, skipping")
        else:
            if filename.endswith('.gz'):
                os.system(f"gunzip -c {filename}| docker load")
            else:
                os.system(f"docker load -i {filename}")


def find_by_pid(pid: int):
    command = f"""\
    dockerid=`cat /proc/{pid}/cgroup | grep -oPm1 .*/docker/.* | sed -e 's/.*docker\///'`
    shortid=`echo $dockerid |cut -c1-12`
    echo $shortid
    docker ps |grep $shortid
    """
    os.system(command)


if __name__ == "__main__":
    filedir = "/path/to/docker/backup"
    save_docker_images(filedir, use_stream=False)
    # load_dir_images(f"{filedir}/*")
