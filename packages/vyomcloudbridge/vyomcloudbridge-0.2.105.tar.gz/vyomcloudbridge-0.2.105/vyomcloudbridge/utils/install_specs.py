from vyomcloudbridge.constants import install_variable

class InstallSpecs:
    @property
    def install_type(self) -> str:
        return install_variable.INSTALL_TYPE

    @property
    def is_lite_install(self) -> bool:
        return self.install_type == "lite"

    @property
    def is_full_install(self) -> bool:
        return self.install_type == "full"
