from libfptr10 import IFptr
from .ord_core import Core


class Fn:
    fn_state = {
        0: "FNS_INITIAL",
        1: "FNS_CONFIGURED",
        3: "FNS_FISCAL_MODE",
        7: "FNS_POSTFISCAL_MODE",
        15: "FNS_ACCESS_ARCHIVE"
    }

    ffd_version = {
        0: "FFD_UNKNOWN",
        100: "FFD_1_0",
        105: "FFD_1_0_5",
        110: "FFD_1_1",
        120: "FFD_1_2"
    }

    tax_mode = {
        1: "OSN",
        2: "USN_INCOME",
        4: "USN_INCOME_OUTCOME",
        16: "ESN",
        32: "PATENT",
    }

    receipt_type = {
        0: "CLOSED",
        1: "SELL",
        2: "SELL_RETURN",
        7: "SELL_CORRECTION",
        8: "SELL_RETURN_CORRECTION",
        4: "BUY",
        5: "BUY_RETURN",
        9: "BUY_CORRECTION",
        10: "BUY_RETURN_CORRECTION"
    }

    doc_type = {
        1: "REGISTRATION",
        2: "OPEN_SHIFT",
        3: "RECEIPT",
        4: "BSO",
        5: "CLOSE_SHIFT",
        6: "CLOSE_FN",
        7: "OPERATOR_CONFIRMATION",
        11: "REREGISTRATION",
        21: "EXCHANGE_STATUS",
        31: "CORRECTION",
        41: "BSO_CORRECTION"
    }

    def __init__(self, core):
        self.core = core
        if self.core.is_opened() == 0:
            if not self.core.open_connect():
                return None
        self.fptr = core.fptr

    def get_status_fn(self):
        """
        Получение статуса фискального накопителя
        :return: fn_state
        :rtype: str
        """
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_FN_DATA_TYPE, IFptr.LIBFPTR_FNDT_FN_INFO)
        self.fptr.fnQueryData()

        fn_state = self.fn_state.get(self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_FN_STATE))

        return fn_state

    def get_info_last_receipt(self):
        """
        Запрос информации о последнем чеке
        :return: last_receipt_info
        :rtype: dict
        """
        last_receipt_info = {
            "receipt_number": "",
            "receipt_type": "",
            "receipt_sum": "",
            "fiscal_sign": "",
            "date_time": ""
        }

        self.fptr.setParam(IFptr.LIBFPTR_PARAM_FN_DATA_TYPE, IFptr.LIBFPTR_FNDT_LAST_RECEIPT)
        self.fptr.fnQueryData()

        receipt_number = self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_DOCUMENT_NUMBER)
        last_receipt_info.update({"receipt_number": receipt_number})

        receipt_type = self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE)
        last_receipt_info.update({"receipt_type": self.receipt_type.get(receipt_type)})

        receipt_sum = self.fptr.getParamDouble(IFptr.LIBFPTR_PARAM_RECEIPT_SUM)
        last_receipt_info.update({"receipt_sum": receipt_sum})

        fiscal_sign = self.fptr.getParamString(IFptr.LIBFPTR_PARAM_FISCAL_SIGN)
        last_receipt_info.update({"fiscal_sign": fiscal_sign})

        date_time = self.fptr.getParamDateTime(IFptr.LIBFPTR_PARAM_DATE_TIME)
        last_receipt_info.update({"date_time": date_time.strftime("%Y-%m-%d %H:%M:%S")})

        return last_receipt_info

    def get_info_last_doc(self):
        """
        Запрос информации о последнем фискальном документе
        :return: last_doc_info
        :rtype: dict
        """
        last_doc_info = {
            "document_number": "",
            "receipt_type": "",
            "fiscal_sign": "",
            "date_time": ""
        }

        self.fptr.setParam(IFptr.LIBFPTR_PARAM_FN_DATA_TYPE, IFptr.LIBFPTR_FNDT_LAST_DOCUMENT)
        self.fptr.fnQueryData()

        document_number = self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_DOCUMENT_NUMBER)
        last_doc_info.update({"document_number": document_number})

        receipt_type = self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE)
        last_doc_info.update({"receipt_type": self.receipt_type.get(receipt_type)})

        fiscal_sign = self.fptr.getParamString(IFptr.LIBFPTR_PARAM_FISCAL_SIGN)
        last_doc_info.update({"fiscal_sign": fiscal_sign})

        date_time = self.fptr.getParamDateTime(IFptr.LIBFPTR_PARAM_DATE_TIME)
        last_doc_info.update({"date_time": date_time.strftime("%Y-%m-%d %H:%M:%S")})

        return last_doc_info

    def get_version_ffd(self):
        """
        Запрос версий ФФД
        :return:version_ffd
        :rtype:dict
        """
        version_ffd = {
            "device_ffd_version": "",
            "fn_ffd_version": "",
            "max_fn_ffd_version": "",
            "ffd_version": "",
            "max_ffd_version": "",
            "min_ffd_version": ""
        }

        self.fptr.setParam(IFptr.LIBFPTR_PARAM_FN_DATA_TYPE, IFptr.LIBFPTR_FNDT_FFD_VERSIONS)
        self.fptr.fnQueryData()

        device_ffd_version = self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_DEVICE_FFD_VERSION)
        version_ffd.update({"device_ffd_version": self.ffd_version.get(device_ffd_version)})

        fn_ffd_version = self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_FN_FFD_VERSION)
        version_ffd.update({"fn_ffd_version": self.ffd_version.get(fn_ffd_version)})

        max_fn_ffd_version = self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_FN_MAX_FFD_VERSION)
        version_ffd.update({"max_fn_ffd_version": self.ffd_version.get(max_fn_ffd_version)})

        ffd_version = self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_FFD_VERSION)
        version_ffd.update({"ffd_version": self.ffd_version.get(ffd_version)})

        max_ffd_version = self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_DEVICE_MAX_FFD_VERSION)
        version_ffd.update({"max_ffd_version": self.ffd_version.get(max_ffd_version)})

        min_ffd_version = self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_DEVICE_MIN_FFD_VERSION)
        version_ffd.update({"document_number": self.ffd_version.get(min_ffd_version)})

        return version_ffd

    def get_info_doc(self, number_doc):
        """
        Запрос информации о документе
        :return: info_doc
        :rtype: dict
        """
        info_doc = {
            "document_type": "",
            "document_number": "",
            "has_ofd_ticket": "",
            "date_time": "",
            "fiscal_sign": ""
        }

        self.fptr.setParam(IFptr.LIBFPTR_PARAM_FN_DATA_TYPE, IFptr.LIBFPTR_FNDT_DOCUMENT_BY_NUMBER)
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_DOCUMENT_NUMBER, number_doc)
        self.fptr.fnQueryData()

        document_type = self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_FN_DOCUMENT_TYPE)
        info_doc.update({"document_type": self.doc_type.get(document_type)})

        document_number = self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_DOCUMENT_NUMBER)
        info_doc.update({"document_number": document_number})

        has_ofd_ticket = self.fptr.getParamBool(IFptr.LIBFPTR_PARAM_HAS_OFD_TICKET)
        info_doc.update({"has_ofd_ticket": has_ofd_ticket})

        fiscal_sign = self.fptr.getParamString(IFptr.LIBFPTR_PARAM_FISCAL_SIGN)
        info_doc.update({"fiscal_sign": fiscal_sign})

        date_time = self.fptr.getParamDateTime(IFptr.LIBFPTR_PARAM_DATE_TIME)
        info_doc.update({"date_time": date_time.strftime("%Y-%m-%d %H:%M:%S")})

        return info_doc

    def get_ticket_ofd(self, number_doc):
        """
        Запрос квитанции ОФД
        :return: ticket_ofd
        :rtype:
        """
        ticket_ofd = {
            "document_number": "",
            "date_time": "",
            "ofd_fiscal_sign": "",
        }

        self.fptr.setParam(IFptr.LIBFPTR_PARAM_FN_DATA_TYPE, IFptr.LIBFPTR_FNDT_TICKET_BY_DOC_NUMBER)
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_DOCUMENT_NUMBER, number_doc)
        self.fptr.fnQueryData()

        document_number = self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_DOCUMENT_NUMBER)
        ticket_ofd.update({"document_number": document_number})

        date_time = self.fptr.getParamDateTime(IFptr.LIBFPTR_PARAM_DATE_TIME)
        ticket_ofd.update({"date_time": date_time.strftime("%Y-%m-%d %H:%M:%S")})

        ofd_fiscal_sign = self.fptr.getParamByteArray(IFptr.LIBFPTR_PARAM_OFD_FISCAL_SIGN)
        ticket_ofd.update({"ofd_fiscal_sign": ofd_fiscal_sign})

        return ticket_ofd

    def get_ofd_document_by_number(self, number_doc):
        """
        Метод чтения документа из ФН в виде TLV-структур
        :param number_doc: номер документа
        :return: array
        """
        tags = []

        self.fptr.setParam(IFptr.LIBFPTR_PARAM_RECORDS_TYPE, IFptr.LIBFPTR_RT_FN_DOCUMENT_TLVS)
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_DOCUMENT_NUMBER, number_doc)
        self.fptr.beginReadRecords()
        records_id = self.fptr.getParamString(IFptr.LIBFPTR_PARAM_RECORDS_ID)

        while self._readNextRecord(records_id) == IFptr.LIBFPTR_OK:
            tag = {
                "tag_value": self.fptr.getParamByteArray(IFptr.LIBFPTR_PARAM_TAG_VALUE),
                "tag_number": self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_TAG_NUMBER),
                "tag_name": self.fptr.getParamString(IFptr.LIBFPTR_PARAM_TAG_NAME),
                "tag_type": self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_TAG_TYPE),
            }
            tags.append(tag)

        self.fptr.setParam(IFptr.LIBFPTR_PARAM_RECORDS_ID, records_id)
        self.fptr.endReadRecords()

        return tags

    def get_fn_error(self):
        """
        Запрос ошибок ФН и ОФД
        :return:
        """
        fn_error_info = {
            "network": {
                "error": "",
                "error_text": ""
            },
            "ofd": {
                "error": "",
                "error_text": ""
            },
            "fn": {
                "error": "",
                "error_text": ""
            }
        }

        self.fptr.setParam(IFptr.LIBFPTR_PARAM_FN_DATA_TYPE, IFptr.LIBFPTR_FNDT_ERRORS)
        self.fptr.fnQueryData()

        network_error = self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_NETWORK_ERROR)
        network_error_text = self.fptr.getParamString(IFptr.LIBFPTR_PARAM_NETWORK_ERROR_TEXT)

        network = fn_error_info.get("network")
        network.update({"error": network_error})
        network.update({"error_text": network_error_text})

        ofd_error = self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_OFD_ERROR)
        ofd_error_text = self.fptr.getParamString(IFptr.LIBFPTR_PARAM_OFD_ERROR_TEXT)

        ofd = fn_error_info.get("ofd")
        ofd.update({"error": ofd_error})
        ofd.update({"error_text": ofd_error_text})

        fn_error = self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_FN_ERROR)
        fn_error_text = self.fptr.getParamString(IFptr.LIBFPTR_PARAM_FN_ERROR_TEXT)

        fn = fn_error_info.get("fn")
        fn.update({"error": fn_error})
        fn.update({"error_text": fn_error_text})

        return fn_error_info

    def get_exchange_status(self):
        """
        Запрос статуса информационного обмена
        :return:
        """
        fn_exchange_info = {
            "exchange_status": "",
            "unsent_count": "",
            "first_unsent_number": "",
            "ofd_message_read": "",
            "date_time": "",
        }

        self.fptr.setParam(IFptr.LIBFPTR_PARAM_FN_DATA_TYPE, IFptr.LIBFPTR_FNDT_OFD_EXCHANGE_STATUS)
        self.fptr.fnQueryData()

        exchange_status = self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_OFD_EXCHANGE_STATUS)
        unsent_count = self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_DOCUMENTS_COUNT)
        first_unsent_number = self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_DOCUMENT_NUMBER)
        ofd_message_read = self.fptr.getParamBool(IFptr.LIBFPTR_PARAM_OFD_MESSAGE_READ)
        date_time = self.fptr.getParamDateTime(IFptr.LIBFPTR_PARAM_DATE_TIME)

        fn_exchange_info.update({"exchange_status": exchange_status})
        fn_exchange_info.update({"unsent_count": unsent_count})
        fn_exchange_info.update({"first_unsent_number": first_unsent_number})
        fn_exchange_info.update({"ofd_message_read": ofd_message_read})
        fn_exchange_info.update({"date_time": date_time.strftime("%Y-%m-%d %H:%M:%S")})

        return fn_exchange_info

    def get_registration_number(self):
        """
        Запрос РНМ
        :return:registrationNumber
        """
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_FN_DATA_TYPE, IFptr.LIBFPTR_FNDT_REG_INFO)
        self.fptr.fnQueryData()

        registration_number = self.fptr.getParamString(1037)

        return registration_number

        # Вспомогательная функция чтения следующей записи

    def _readNextRecord(self, recordsID):
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_RECORDS_ID, recordsID)
        return self.fptr.readNextRecord()
