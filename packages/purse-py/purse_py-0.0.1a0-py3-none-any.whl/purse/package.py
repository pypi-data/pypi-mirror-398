from importlib import resources

from ethpm_types import PackageManifest

MANIFEST = PackageManifest.model_validate_json(
    resources.files(__package__).joinpath("manifest.json")
)
