from ovos_PHAL.service import PHAL, on_ready, on_error, on_stopping

from ovos_utils import wait_for_exit_signal
from ovos_utils.log import init_service_logger


def main(ready_hook=on_ready, error_hook=on_error, stopping_hook=on_stopping):
    # config read from mycroft.conf
    # "PHAL": {
    #     "ovos-PHAL-plugin-display-manager-ipc": {"enabled": true},
    #     "ovos-PHAL-plugin-mk1": {"enabled": True}
    # }
    init_service_logger("PHAL")
    phal = PHAL(on_error=error_hook, on_ready=ready_hook, on_stopping=stopping_hook)
    phal.start()
    wait_for_exit_signal()
    phal.shutdown()
    
    
if __name__ == "__main__":
    main()
