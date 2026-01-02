from fabric import Connection

from ..._utils.setup_apt_sources import setup_apt_sources
from ..._utils.cleanup_network_config import cleanup_network_config
from ..base_box_init import * 



def create_vagrant_base_box(c:Connection):
    setup_apt_sources(c)
    apt_update_and_install_base_package(c)
    setup_vagrant_user(c)
    install_kernel_dev_packages(c)
    install_vbox_guest_additions(c)
    cleanup_network_config(c)
