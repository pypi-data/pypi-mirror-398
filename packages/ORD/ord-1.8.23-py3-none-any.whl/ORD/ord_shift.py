from libfptr10 import IFptr
from .ord_core import Core


class Shift:

    def __init__(self, core):
        self.core = core
        if self.core.is_opened() == 0:
            if not self.core.open_connect():
                return None
        self.fptr = core.fptr

    def open_shift(self):
        """
        Открытие смены

        Открывать смену необязательно, т.к. она будет открыта первой фискальной операцией автоматически.
        На некоторых ККТ возможно отключить печать отчета об открытии смены
        с помощью установки параметра LIBFPTR_PARAM_REPORT_ELECTRONICALLY в true.
        Если ККТ не поддерживает такой функционал, параметр будет проигнорирован и отчет будет напечатан.
        :returns: status
        :rtype: bool
        """

        status = False

        if not self.core._set_casher():
            return status

        if self.fptr.openShift() < 0:
            self.core._error_log()
        else:
            self.core._check_document_close()
            status = True

        return status

    def close_shift(self):
        """
        Закрытие смены

        Автоматически может напечататься так же и Z-отчет.
        На некоторых ККТ возможно отключить печать отчета о закрытии смены с помощью установки
        параметра LIBFPTR_PARAM_REPORT_ELECTRONICALLY в true.
        Если ККТ не поддерживает такой функционал, параметр будет
        проигнорирован и отчет будет напечатан.
        :returns: status
        :rtype: bool
        """
        status = False

        if not self.core._set_casher():
            return status

        self.fptr.setParam(IFptr.LIBFPTR_PARAM_REPORT_TYPE, IFptr.LIBFPTR_RT_CLOSE_SHIFT)

        if self.fptr.report() < 0:
            self.core._error_log()
        else:
            self.core._check_document_close()
            status = True

        return status


    # def __del__(self):
    #     if core.is_opened() == 1:
    #         self.close_connect()
