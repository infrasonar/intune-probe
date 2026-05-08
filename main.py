from libprobe.probe import Probe
from lib.check.devices import CheckDevices
from lib.version import __version__ as version


if __name__ == '__main__':
    checks = (
        CheckDevices,
    )

    probe = Probe("intune", version, checks)
    probe.start()
