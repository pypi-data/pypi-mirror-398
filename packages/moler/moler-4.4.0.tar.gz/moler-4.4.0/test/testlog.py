from moler.config import load_config
from moler.device import DeviceFactory
import logging


def test_listen_syslog():
        # syslog
        config = {
            'LOGGER': {
                'PATH': '/home/ute/Temp/syslog_analyzer',  # Put your path to logs here
                #'RAW_LOG': True,
                'DATE_FORMAT': '%d %H:%M:%S',
                'LOG_ROTATION': {
                    'KIND': 'size',
                    'INTERVAL': 5242880,
                    'BACKUP_COUNT': 10
                }
            },
            'DEVICES': {
                'SYSLOG_DEV': {
                    'DEVICE_CLASS': 'moler.device.unixlocal.UnixLocal',
                },
            },
        }
        # Config can be loaded from dict or from yaml file:
        load_config(config=config, config_type='dict')
        dev = DeviceFactory.get_device("SYSLOG_DEV")
        dev.disable_logging()
        dev.goto_state("UNIX_LOCAL")

        # import sys
        # logging.basicConfig(
        #     level=logging.DEBUG,
        #     format='%(asctime)s |%(name)40s |%(message)s',
        #     datefmt='%H:%M:%S',
        #     stream=sys.stdout,
        # )

        cmd = dev.get_cmd(cmd_name="ls", cmd_params={'path': "/home/ute/auto", "options": "-l"})
        ret = cmd()
        print(f"ls ret={ret}")

if __name__ == '__main__':
    test_listen_syslog()
