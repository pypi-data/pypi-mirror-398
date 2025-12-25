"""Utilities for Active Learning workflow."""


class D3ParamMD:
    """Different packages use different names for D3 parameters.
    This class to 'return' standard D3 parameter names for different packages used for MD.
    """

    def __init__(self, d3package: str = "sevenn"):
        self.d3package: str = d3package
        self.default_cutoff: float = 50.2022
        self.default_cn_cutoff: float = 21.1671
        params = self.get_params()  # set self.param_names and self.damping_map
        ### Store params
        self.param_names = params["params"]
        self.damping_map = params["damping_map"]
        return

    def get_params(self) -> dict:
        """Return D3 parameter names according to different packages."""
        if self.d3package == "lammps":
            params = self._d3_lammps()
        elif self.d3package == "sevenn":
            params = self._d3_sevenn()
        else:
            raise ValueError(f"Unsupported D3 package: {self.d3package}")
        return params

    def check_supported_damping(self, damping: str):
        """Check if the damping method is supported in the selected package."""
        params = self.get_params()
        if damping not in params["damping_map"].keys():
            raise ValueError(
                f"Damping method '{damping}' is not supported in package '{self.d3package}'. Supported methods: {list(params['damping_map'].keys())}"
            )
        return

    def _d3_lammps(self) -> dict:
        ### https://docs.lammps.org/pair_dispersion_d3.html
        ### use lammps' D3 in sevenn: https://github.com/MDIL-SNU/SevenNet/issues/246
        """Return D3 parameters using in LAMMPS's `dispersion/d3`."""
        return {
            "params": ["damping", "functional", "cutoff", "cn_cutoff"],
            "damping_map": {
                "zero": "original",
                "zerom": "zerom",
                "bj": "bj",
                "bjm": "bjm",
            },
        }

    def _d3_sevenn(self) -> dict:
        ### https://github.com/MDIL-SNU/SevenNet/tree/main/sevenn/pair_e3gnn
        """Return D3 parameters using in SevenNet's `e3gnn`."""
        return {
            "params": ["damping", "xc", "cutoff", "cnthr"],
            "damping_map": {
                "zero": "damp_zero",
                "bj": "damp_bj",
            },
        }

    @staticmethod
    def angstrom_to_bohr(value_in_angstrom: float) -> float:
        """Convert Angstrom to Bohr."""
        value = round(value_in_angstrom / 0.52917721, ndigits=2)
        return value

    @staticmethod
    def angstrom_to_bohr2(value_in_angstrom: float) -> float:
        """Convert Angstrom to Bohr^2. To used in sevenn package."""
        value = round((value_in_angstrom / 0.52917721) ** 2, ndigits=2)
        return value


class D3ParamDFT(D3ParamMD):
    """Different packages use different names for D3 parameters.
    This class to 'return' standard D3 parameter names for different packages used for DFT.
    """

    def __init__(self, d3package: str = "sevenn"):
        super().__init__(d3package=d3package)
        self.d3package: str = d3package
        self.default_cutoff: float = 50.2022
        self.default_cn_cutoff: float = 21.1671
        params = self.get_params()  # set self.param_names and self.damping_map
        ### Store params
        self.param_names = params["params"]
        self.damping_map = params["damping_map"]
        return

    def get_params(self) -> dict:
        """Return D3 parameter names according to different packages."""
        if self.d3package == "simple-dftd3":
            params = self._d3_dftd3()
        elif self.d3package == "sevenn":
            params = self._d3_sevenn()
        else:
            raise ValueError(f"Unsupported D3 package: {self.d3package}")
        return params

    def _d3_dftd3(self) -> dict:
        ### https://github.com/dftd3/simple-dftd3/blob/main/python/dftd3/ase.py
        """Return D3 parameters using in dftd3-python."""
        return {
            "params": ["damping", "method"],
            "damping_map": {
                "zero": "d3zero",
                "zerom": "d3zerom",
                "bj": "d3bj",
                "bjm": "d3bjm",
                "op": "d3op",
            },
        }


class MLP2Lammps:
    """Convert MLP model to be used in LAMMPS."""

    def __init__(self, mlp_model: str = "sevenn"):
        self.mlp_model: str = mlp_model
        self._check_supported_model()
        return

    def convert(
        self,
        checkpoint: str,
        outfile: str = "deployed.pt",
        **kwargs,
    ):
        """Convert MLP model to LAMMPS format.

        Args:
            checkpoint (str): Path to checkpoint file of MLP model.
            outfile (str): Path to output LAMMPS potential file.
            **kwargs: Additional arguments for specific conversion methods.
        """
        if self.mlp_model == "sevenn":
            MLP2Lammps.convert_sevenn(checkpoint, outfile, **kwargs)
        elif self.mlp_model == "sevenn_mliap":
            MLP2Lammps.convert_sevenn_mliap(checkpoint, outfile, **kwargs)
        return

    def _check_supported_model(self):
        """Return supported MLP models."""
        supported_models = ["sevenn", "sevenn_mliap"]
        if self.mlp_model not in supported_models:
            raise ValueError(
                f"MLP model: {self.mlp_model} is unsupported. Available models: {supported_models}"
            )
        return

    @staticmethod
    def convert_sevenn(
        checkpoint: str,
        outfile: str = "deploy_sevenn",
        modal: str | None = None,
        use_flash: bool = False,
        parallel_type=False,
    ):
        ### https://github.com/MDIL-SNU/SevenNet/blob/main/sevenn/scripts/deploy.py
        """Args:
            checkpoint (str): Path to checkpoint file of sevenn model.
            outfile (str): Path to output LAMMPS potential file.
            parallel_type (bool): Convert to potential for run in parallel simulations.
            use_flash (bool): Use flashTP.

        Notes:
            Single mode: will generate file as "outfile.pt"
            Parallel mode: will generate files as "outfile/deployed_parallel_0.pt", "outfile/deployed_parallel_1.pt", ...
        """
        from sevenn.scripts.deploy import deploy, deploy_parallel

        if parallel_type:
            deploy_parallel(checkpoint, outfile, modal, use_flash=use_flash)
        else:
            deploy(checkpoint, outfile, modal, use_flash=use_flash)
        return

    @staticmethod
    def convert_sevenn_mliap(
        checkpoint: str,
        outfile: str = "deploy_sevenn_mliap.pt",
        modal: str | None = None,
        use_cueq: bool = False,
        use_flash: bool = False,
    ):
        ### https://github.com/MDIL-SNU/SevenNet/blob/main/sevenn/main/sevenn_get_model.py
        """Convert sevenn model to be used in LAMMPS MLIAP.

        Args:
            checkpoint (str): Path to checkpoint file of sevenn model.
            outfile (str): Path to output LAMMPS potential file.
            modal (str): Channel of multi-task model.
            use_cueq (bool): Use cueq. cuEquivariance is only supported in ML-IAP interface.
            use_flash (bool): Use flashTP.
        """
        try:
            import torch
            from sevenn.mliap import SevenNetMLIAPWrapper  # type: ignore
        except Exception as e:
            raise ImportError(
                f"Error importing SevenNetMLIAPWrapper. \n{e} \nHints: This feature requires SevenNet 0.12. And make sure installing `lammps` from conda-forge channel."
            )

        mliap_module = SevenNetMLIAPWrapper(
            model_path=checkpoint,
            modal=modal,
            use_cueq=use_cueq,
            use_flash=use_flash,
        )
        torch.save(mliap_module, outfile)
        return
