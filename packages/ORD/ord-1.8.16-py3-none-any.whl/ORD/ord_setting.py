from libfptr10 import IFptr
from .ord_core import Core


class Setting(Core):

    def __init__(self, core):
        self.core = core
        if self.core.is_opened() == 0:
            if not self.core.open_connect():
                return None
        self.fptr = core.fptr

    def init_setting(self):
        """
        Инициализация системных таблиц
        :returns: status
        :rtype: bool
        """

        status = False

        if self.fptr.initSettings() < 0:
            self._error_log()
        else:
            status = True

        return status

    def get_device_setting_by_id(self, id_setting, type_setting):
        """
        Чтение настройки кассы
        :param id_setting:
        :param type_setting
        :return: setting_value
        :rtype: bool, int, str
        """
        setting_value = False

        self.fptr.setParam(IFptr.LIBFPTR_PARAM_SETTING_ID, id_setting)
        self.fptr.readDeviceSetting()

        if type_setting == "int":
            setting_value = self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_SETTING_VALUE)
        if type_setting == "string":
            setting_value = self.fptr.getParamString(IFptr.LIBFPTR_PARAM_SETTING_VALUE)

        return setting_value

    def set_device_setting_by_id(self, id_setting, value_setting):
        """
        Запись настройки кассы
        :param id_setting:
        :param value_setting:
        :return status
        :rtype bool
        """
        status = False
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_SETTING_ID, id_setting)
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_SETTING_VALUE, value_setting)

        if self.fptr.writeDeviceSetting() < 0:
            self._error_log()
        else:
            status = True

        return status

    def commit_setting(self):
        """
        Сохранение настроек
        :returns: status
        :rtype: bool
        """
        status = False

        if self.fptr.commitSettings() < 0:
            self._error_log()
        else:
            status = True

        return status

    def __del__(self):
        if self.is_opened() == 1:
            self.close_connect()
