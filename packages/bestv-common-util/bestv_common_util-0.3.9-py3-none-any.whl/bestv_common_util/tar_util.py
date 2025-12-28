import tarfile
import os


def make_tar(tar_name, src_dirs, mode='w:gz', excludes=[]):
    """
    :param tar_name:
    :param src_dirs: []
    :param mode:
    :param excludes: [] filename
    :return:
    """
    tar = tarfile.open(tar_name, mode)
    for src_dir in src_dirs:
        if os.path.isdir(src_dir):
            for root, dir, files in os.walk(src_dir):
                for filename in files:
                    if not any(item in filename for item in excludes):
                        fullpath = os.path.join(root, filename)
                        tar.add(fullpath, arcname=filename)
        elif os.path.isfile(src_dir):
            filename = os.path.basename(src_dir)
            if not any(filename in item for item in excludes):
                tar.add(src_dir, arcname=filename)
    tar.close()


def un_tar(tar_path, dist_dir, mode='r:gz'):
    """
    :param tar_path:
    :param dist_dir:
    :param mode:
    :return:
    """
    with tarfile.open(tar_path, mode) as tar:
        tar.extractall(path=dist_dir)


# make_tar('D:/mnt/data/private/model/20230619/model.tar.gz', ['D:/mnt/data/private/model/20230619'])
# un_tar('D:/mnt/data/private/model/20230607/model.tar.gz', 'D:/mnt/data/private/temp/20230607')

