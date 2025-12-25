import os


def file_only_read(file_path):
    """
    修改文件权限为只读，防止被修改
    :param file_path: 文件路径
    :return: 文件内容
    """
    os.chmod(file_path, 0o444)