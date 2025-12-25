import logging

from django_datadog_logger.formatters import datadog

from itoutils.django.commands import get_current_command_info

logger = logging.getLogger(__name__)


class DataDogJSONFormatter(datadog.DataDogJSONFormatter):
    # We don't want those information in our logs
    LOG_KEYS_TO_REMOVE = ["usr.name", "usr.email", "usr.session_key"]

    def json_record(self, message, extra, record):
        log_entry_dict = super().json_record(message, extra, record)
        for log_key in self.LOG_KEYS_TO_REMOVE:
            if log_key in log_entry_dict:
                del log_entry_dict[log_key]
        if (command_info := get_current_command_info()) is not None:
            log_entry_dict["command.run_uid"] = command_info.run_uid
            log_entry_dict["command.name"] = command_info.name
            log_entry_dict["command.wet_run"] = command_info.wet_run
        return log_entry_dict
