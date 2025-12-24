import tempfile
import git
import os
import glob
import pypandoc


def download_repo_folder(url, dirs_to_checkout, branch="main"):
    # downloads and reads all the files and returns a a dict with the paths
    with tempfile.TemporaryDirectory() as tmp_dir:
        # os.chdir(tmp_dir)
        # Initialize the repo (make sure the path is where you want to clone)
        # os.makedirs(repo_path, exist_ok=True)
        repo = git.Repo.init(tmp_dir)
        # Add remote origin
        origin = repo.create_remote("origin", url=url)
        # Configure sparse checkout
        repo.git.config("core.sparsecheckout", "true")
        # Add directories to sparse-checkout file
        sparse_checkout_path = f"{tmp_dir}/.git/info/sparse-checkout"
        with open(sparse_checkout_path, "w") as sparse_file:
            sparse_file.write("\n".join(dirs_to_checkout) + "\n")

        # Pull the specific branch
        origin.pull(branch)
        all_paths = glob.glob(f"{tmp_dir}/**", recursive=True)
        content_dict = {}
        for p in all_paths:
            if os.path.isdir(p):
                continue
            with open(p) as f:
                _p = p.replace(tmp_dir, "")
                content_dict[_p] = f.read()
        return content_dict


def filter_files(content_dict):
    content_list = []
    for path, content in content_dict.items():
        if (
            ("__init__" in path)
            or path.endswith("index.rst")
            or path.endswith(".ipynb")
        ):
            continue
        base_name = os.path.basename(path)

        if base_name.endswith(".rst"):
            content = pypandoc.convert_text(content, "rst", format="md")
        content = f"# file path: {path}\n\n\n{content}"
        base_name = base_name.replace(".rst", ".md")
        content_list.append((base_name, content))
    return content_list

"""
pallas_content = download_repo_folder(
                     url = "https://github.com/google/jax",
                     dirs_to_checkout = ["jax/experimental/pallas/ops/tpu","docs/pallas"],
                     branch="main"
                     )
pallas_content = filter_files(pallas_content)
og_pallas_str = "\n".join([x[1] for x in pallas_content])




"""
