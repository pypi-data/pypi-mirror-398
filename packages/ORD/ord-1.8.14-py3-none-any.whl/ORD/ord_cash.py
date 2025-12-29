from libfptr10 import IFptr
from .ord_core import Core


class Cash:
    shift_stage = {
        0: "CLOSED",
        1: "OPENED",
        2: "EXPIRED"
    }

    fn_state = {
        0: "FNS_INITIAL",
        1: "FNS_CONFIGURED",
        3: "FNS_FISCAL_MODE",
        7: "FNS_POSTFISCAL_MODE",
        15: "FNS_ACCESS_ARCHIVE"
    }

    def __init__(self, core):
        self.core = core
        if self.core.is_opened() == 0:
            if not self.core.open_connect():
                return None
        self.fptr = core.fptr

    def get_cash_info(self):
        """
        Получение информации о ККТ

        :returns: cash_info
        :rtype: dict
        """
        cash_info = {
            "fnNo": "",
            "fnVersion": "",
            "fnCountDocInShift": "",
            "serialNo": "",
            "modelName": "",
            "modelId": "",
            "firmwareVersion": "",
            "vendorName": "АТОЛ",
            "shiftNumber": "",
            "shiftState": "",
            "shiftDateTime": "",
            "taxModes": "",
            "ffdVersion": ""
        }

        self.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_STATUS)
        self.fptr.queryData()

        serial_no = self.fptr.getParamString(IFptr.LIBFPTR_PARAM_SERIAL_NUMBER)
        model_name = self.fptr.getParamString(IFptr.LIBFPTR_PARAM_MODEL_NAME)
        model_id = self.fptr.getParamString(IFptr.LIBFPTR_PARAM_MODEL)

        cash_info.update({"serialNo": serial_no})
        cash_info.update({"modelName": model_name})
        cash_info.update({"modelId": model_id})

        self.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_UNIT_VERSION)
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_UNIT_TYPE, IFptr.LIBFPTR_UT_FIRMWARE)
        self.fptr.queryData()

        firmware_version = self.fptr.getParamString(IFptr.LIBFPTR_PARAM_UNIT_VERSION)
        cash_info.update({"firmwareVersion": firmware_version})

        self.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_SHIFT_STATE)
        self.fptr.queryData()

        shift_state = self.shift_stage.get(self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_STATE))
        shift_number = self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_SHIFT_NUMBER)
        shift_date_time = self.fptr.getParamDateTime(IFptr.LIBFPTR_PARAM_DATE_TIME)

        cash_info.update({"shiftState": shift_state})
        cash_info.update({"shiftNumber": shift_number})
        cash_info.update({"shiftDateTime": shift_date_time.strftime("%Y-%m-%d %H:%M:%S")})

        self.fptr.setParam(IFptr.LIBFPTR_PARAM_FN_DATA_TYPE, IFptr.LIBFPTR_FNDT_FN_INFO)
        self.fptr.fnQueryData()

        fn_serial = self.fptr.getParamString(IFptr.LIBFPTR_PARAM_SERIAL_NUMBER)
        fn_version = self.fptr.getParamString(IFptr.LIBFPTR_PARAM_FN_VERSION)

        cash_info.update({"fnNo": fn_serial})
        cash_info.update({"fnVersion": fn_version.strip()})

        return cash_info

    def get_uptime_cash(self):
        """
        Запрос времени работы ККТ
        :returns: uptime
        :rtype: int
        """
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_DEVICE_UPTIME)
        self.fptr.queryData()

        uptime = self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_DEVICE_UPTIME)

        return uptime

    def cash_registration(self):
        """
        Регистрация кассы

        Расчет регистрационного номера для МГМ
        ВХОД:
        1) порядковый номер зарегистрированного ККТ (дополняется лидирующими нулями до длины в 10 символов, используется ascii-коды в кодировке CP866);
        2) ИНН пользователя ККТ (дополняется лидирующими нулями до длины в 12 символов, используется ascii-коды в кодировке CP866);
        3) заводской номер ККТ (дополняется лидирующими нулями до длины в 20 символов, используется ascii-коды в кодировке CP866);

        ВЫХОД:
        1) вычисляется значение по алгоритму расчета контрольной суммы CRC16-CCITT
        2) значение переводится в десятичную систему счислений
        3) дополняется лидирующими нулями до длины строки в 6 символов

        Пример:
        порядковый номер зарегистрированного ККТ 0000000001
        ИНН пользователя ККТ 770123456789
        заводской номер ККТ 00000000000123456789

        Вычисления:
        1) CRC16-CCITT(000000000177012345678900000000000123456789) = 492D (hex)
        2) 492D (hex) = 18733 (dec)
        3) 018733

        РНМ ККТ равен 0000000001018733

        :return:
        """
        status = False

        self.fptr.setParam(IFptr.LIBFPTR_PARAM_FN_OPERATION_TYPE, IFptr.LIBFPTR_FNOP_REGISTRATION)

        self.fptr.setParam(1060, "nalog.ru")

        self.fptr.setParam(1009, "127051, г. Москва, Петровский б-р, 21")
        self.fptr.setParam(1018, "9705112246")
        self.fptr.setParam(1048, "ООО \"БШ СТОР\"")
        self.fptr.setParam(1062, IFptr.LIBFPTR_TT_OSN)
        self.fptr.setParam(1117, "volodya@brandshop.ru")
        self.fptr.setParam(1057, IFptr.LIBFPTR_AT_NONE)

        self.fptr.setParam(1187, "https://brandshop.ru")
        self.fptr.setParam(1037, "0000000001030584")
        self.fptr.setParam(1209, IFptr.LIBFPTR_FFD_UNKNOWN)
        self.fptr.setParam(1001, False)
        self.fptr.setParam(1002, False)
        self.fptr.setParam(1056, False)
        self.fptr.setParam(1108, True)
        self.fptr.setParam(1109, False)
        self.fptr.setParam(1110, False)
        self.fptr.setParam(1126, False)
        self.fptr.setParam(1193, False)

        self.fptr.setParam(1221, False)

        self.fptr.setParam(1017, "9715260691")
        self.fptr.setParam(1046, "ООО ПС СТ")

        if self.fptr.fnOperation() < 0:
            self.core._error_log()
        else:
            self.core._check_document_close()
            status = True

        return status
