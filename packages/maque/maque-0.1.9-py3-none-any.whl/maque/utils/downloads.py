import os


def download_model(repo_id, download_dir=None, backend="huggingface", token=None, repo_type="model", use_mirror=True):
    """根据指定的 backend 下载模型或数据集，支持 Hugging Face 和 ModelScope，支持私有仓库模型下载.

    Args:
        repo_id (str): 模型或数据集仓库名称.
        download_dir (str, optional): 下载的本地目录，默认为 None.
        backend (str): 指定下载源，"huggingface" 或 "modelscope".
        token (str, optional): 访问私有仓库的身份验证令牌，默认为 None.
        repo_type (str): 仓库类型，可选值为 "model" 或 "dataset"，默认为 "model".
        use_mirror (bool): 是否使用镜像下载模型，默认为 True.
    """
    # 如果没有指定 download_dir，默认为当前目录下的 repo_id 文件夹
    if download_dir is None:
        download_dir = os.path.join(os.getcwd(), repo_id)

    if backend == "huggingface":
        if use_mirror:
            os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
            print(f"使用镜像下载模型: {repo_id}")
        from huggingface_hub import snapshot_download as hf_snapshot_download

        print(f"从 Hugging Face 下载{'模型' if repo_type == 'model' else '数据集'}: {repo_id}")
        if token:
            from huggingface_hub import HfApi

            api = HfApi(token=token)
            local_dir = api.snapshot_download(repo_id=repo_id, local_dir=download_dir, token=token, repo_type=repo_type)
        else:
            local_dir = hf_snapshot_download(repo_id=repo_id, local_dir=download_dir, token=token, repo_type=repo_type)
    elif backend == "modelscope":
        from modelscope.hub.snapshot_download import snapshot_download as ms_snapshot_download

        if token:
            from modelscope import HubApi

            api = HubApi()
            api.login(access_token=token)
        print(f"从 ModelScope 下载模型: {repo_id}")
        local_dir = ms_snapshot_download(model_id=repo_id, local_dir=download_dir)
    else:
        raise ValueError(f"不支持的 backend: {backend}")

    print(f"模型文件已下载到: {local_dir}")
    return local_dir


if __name__ == "__main__":
    download_model("SWHL/ChineseOCRBench", repo_type="dataset")
