"""Utility functions for MLP training."""
# import re
# import warnings
# from pathlib import Path

# from thkit.io import download_rawtext


#####ANCHOR Build graph data
class Xyz2GraphData:
    """Convert XYZ file to graph data format used in MLP training."""

    @staticmethod
    def build_graph_sevenn(
        files: list[str],
        outfile: str = "graph_atoms.pt",
        outdir: str = ".",
        num_cores: int = 1,
        cutoff: float = 5.0,
        **ase_kwargs,
    ):
        ### https://github.com/MDIL-SNU/SevenNet/blob/main/sevenn/main/sevenn_graph_build.py
        ### sevenn/scripts/graph_build.py/build_sevennet_graph_dataset
        """Build SevenNet graph dataset from source files.

        Args:
            files (list[str]): List of input data files. Supported formats: extxyz, and other formats defined in function `SevenNetGraphDataset.file_to_graph_list()`.
            outfile (str, optional): Name of the output file. Defaults to "graph_atoms.pt".
            outdir (str, optional): Output directory. Defaults to ".".
            num_cores (int, optional): Number of CPU cores for parallel processing. Defaults to 1.
            cutoff (float, optional): Cutoff distance for neighbor search. Defaults to 5.0.
            **ase_kwargs: Additional keyword arguments for ASE's `read()` function
        """
        from sevenn.train.graph_dataset import SevenNetGraphDataset

        _ = SevenNetGraphDataset(
            cutoff=cutoff,
            root=outdir,
            files=files,
            processed_name=outfile,
            process_num_cores=num_cores,
            **ase_kwargs,
        )
        return

    @staticmethod
    def build_graph_mace():
        # To be implemented
        pass


#####ANCHOR training tools
def suggest_num_epochs(
    dataset_size: int,
    batch_size: int,
    num_grad_updates: int = 300000,
) -> int:
    """Suggest number of epochs for training. Based on [MACE's setting](https://github.com/ACEsuit/mace?tab=readme-ov-file#training).

    Args:
        dataset_size (int): Number of samples in the dataset.
        batch_size (int): Batch size.
        num_grad_updates (int, optional): Maximum number of updates of model weights & biases. Defaults to 300000.
    """
    num_epochs = (num_grad_updates * batch_size) / dataset_size
    return int(num_epochs)


### ANCHOR: MACE data
# def read_log_MACE_train(log_file: str, output_file: str = '') -> dict:
#     """Read MACE log file, and extract learning curve."""
#     with open(log_file) as f:
#         lines = f.readlines()
#     lines = [line for line in lines if "INFO: Epoch" in line]
#     lines = [line.split("INFO:")[1].strip() for line in lines]
#     ### Extract numbers from each string in the list
#     number_strings = [re.findall(r"[-+]?\d*\.\d+|\d+", s) for s in lines]
#     numbers = [[float(num) for num in sublist] for sublist in number_strings]
#     ### Extract column-names
#     columns = [lines[0].split(sep)[0].strip() for sep in number_strings[0]]
#     columns = [col.split(" ")[-1].replace("=", "") for col in columns]
#     ### Output
#     numbers.insert(0, columns)
#     if output_file:
#         with open(output_file, "w") as f:
#             for row in numbers:
#                 f.write(" ".join(map(str, row)) + "\n")
#     else:
#         return numbers


# def get_all_mace_args_offline():
#     """Retrieve all MACE arguments from installed version."""
#     try:
#         mm = __import__("mace")
#         version = mm.__version__
#         mace_path = mm.__path__[0]

#         with Path(f"{mace_path}/tools/arg_parser.py").open() as f:
#             text = f.read()

#         pattern = r"add_argument[^,]+"  #  r"args\.[^\s]+"
#         args = re.findall(pattern, text)  # search all subtext
#         refine_args = [re.search(r'--[^"]+', arg).group(0) for arg in args]
#         args = [arg.replace("--", "") for arg in refine_args]
#         args = list(set(args))
#     except Exception as e:
#         warnings.warn(f"Failed to retrieve MACE arguments from installed version. Error: {e}")
#         args, version = [], "unknown"
#     return args, version


# def get_all_mace_args_online():
#     """Retrieve all MACE arguments from source codes."""
#     ### Retrieve arguments
#     try:
#         text = download_rawtext(
#             url="https://raw.githubusercontent.com/ACEsuit/mace/develop/mace/tools/arg_parser.py"
#         )
#         pattern = r"add_argument[^,]+"  #  r"args\.[^\s]+"
#         args = re.findall(pattern, text)  # search all subtext
#         refine_args = [re.search(r'--[^"]+', arg).group(0) for arg in args]
#         args = [arg.replace("--", "") for arg in refine_args]
#         args = list(set(args))

#         ### Retrieve version
#         text = download_rawtext(
#             url="https://raw.githubusercontent.com/ACEsuit/mace/develop/mace/__version__.py"
#         )
#         version = re.search(r"__version__ = \"([^\"]+)\"", text).group(1)
#     except Exception as e:
#         warnings.warn(f"Failed to retrieve MACE arguments from. Error: {e}")
#         args, version = [], "unknown"
#     return args, version


# def revise_mace_cli_args(input_args: dict):
#     """Check if the input arguments are valid for MACE CLI."""
#     ### Define supported arguments
#     notuse_args = [
#         "train_file",
#         "valid_file",
#         "output",
#     ]
#     # try:
#     #     mace_args, version = get_all_mace_args_offline()  #  get_all_mace_args_online()
#     # except Exception:
#     #     mace_args, version = get_all_mace_args_online()

#     mace_args, version = get_all_mace_args_offline()

#     revised_dict = {
#         arg: val for arg, val in input_args.items() if (arg in mace_args and arg not in notuse_args)
#     }

#     ### Set but not supported arguments
#     unsupported_args = [arg for arg in input_args if arg not in mace_args]
#     if unsupported_args:
#         warnings.warn(
#             f"The following keywords are not arguments of the current MACE-CLI ({version}): \n\n{unsupported_args}. \n\nAll supported arguments are: \n\n{mace_args} \n\nPlease check the MACE version on running machine and update the arguments. See more at: https://raw.githubusercontent.com/ACEsuit/mace/develop/mace/tools/arg_parser.py \n"
#         )
#     ### Set and supported, but not implemented arguments
#     bad_args = [arg for arg in notuse_args if (arg in input_args and arg in mace_args)]
#     if bad_args:
#         warnings.warn(
#             f"These following keywords are not implemented in the current version of `alff`: \n\n{bad_args}. \n\nAll unimplemented arguments are: \n\n{notuse_args}\n"
#         )
#     return revised_dict
