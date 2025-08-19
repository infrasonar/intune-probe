from libprobe.probe import Probe
from lib.check.devices import check_devices
from lib.version import __version__ as version


if __name__ == '__main__':
    checks = {
        'devices': check_devices,
    }

    probe = Probe("intune", version, checks)
    probe.start()
