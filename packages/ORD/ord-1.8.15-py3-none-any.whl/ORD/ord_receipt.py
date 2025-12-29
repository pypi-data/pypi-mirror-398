from libfptr10 import IFptr
from .ord_core import Core


class Receipt:
    """
    Формирование чека состоит из следующих операций:

        открытие чека и передача реквизитов чека
        регистрация позиций, печать нефискальных данных (текст, штрихкоды, изображения)
        регистрация итога (необязательный пункт - если регистрацию итога не провести, он автоматически расчитается из суммы всех позиций)
        регистрация налогов на чек (необязательный пункт - налоги могут быть подтянуты из позиций и суммированы)
        регистрация оплат
        закрытие чека
        проверка состояния чека

        Пример:
        {
           "document":{
              "id":"ofd_605df0bed5d8a",
              "checkoutDateTime":"2021-03-26T17:33:34+03:00",
              "docNum":"197452540",
              "docType":"SALE",
              "printReceipt":false,
              "responseURL":null,
              "email":"volodya@brandshop.ru",
              "inventPositions":[
                 {
                    "name":"Сланцы adidas Originals YEEZY Foam Runner Moon Gray/Moon Gray/Moon Gray",
                    "price":6990,
                    "quantity":"1",
                    "vatTag":1102,
                    "discSum":0,
                    "nomenclatureCode":"44 4D 03 B2 3C AF 78 CB 70 25 63 33 35 6F 7A 52 79 2C 72 3F 7A"
                 },
                 {
                    "name":"Самовывоз",
                    "price":"0.0000",
                    "quantity":"1",
                    "vatTag":1102,
                    "discSum":0,
                    "nomenclatureCode":null
                 }
              ],
              "moneyPositions":[
                 {
                    "paymentType":"CARD",
                    "sum":6990
                 }
              ]
           }
        }
    """

    tax_mode = {
        "OSN": 1,
        "USN_INCOME": 2,
        "USN_INCOME_OUTCOME": 4,
        "ESN": 16,
        "PATENT": 32,
    }

    def __init__(self, core):
        self.core = core
        if self.core.is_opened() == 0:
            if not self.core.open_connect():
                return None
        self.fptr = core.fptr

    def open_receipt(self, receipt_data):
        """
        Открытие чека и передача реквизитов чека
        Тип чека (LIBFPTR_PARAM_RECEIPT_TYPE) может принимать следующие значения:
        LIBFPTR_RT_SELL - чек прихода (продажи)
        LIBFPTR_RT_SELL_RETURN - чек возврата прихода (продажи)
        LIBFPTR_RT_SELL_CORRECTION - чек коррекции прихода
        LIBFPTR_RT_SELL_RETURN_CORRECTION - чек коррекции возврата прихода
        LIBFPTR_RT_BUY - чек расхода (покупки)
        LIBFPTR_RT_BUY_RETURN - чек возврата расхода (покупки)
        LIBFPTR_RT_BUY_CORRECTION - чек коррекции расхода
        LIBFPTR_RT_BUY_RETURN_CORRECTION - чек коррекции возврата расхода

        Чтобы чек не печатался (электронный чек), нужно установить
        параметру LIBFPTR_PARAM_RECEIPT_ELECTRONICALLY значение true.

        "id":"ofd_605df0bed5d8a",
        "checkoutDateTime":"2021-03-26T17:33:34+03:00",
        "docNum":"197452540",
        "docType":"SALE",
        "printReceipt":false,
        "responseURL":null,
        "email":"volodya@brandshop.ru",
        "taxMode": "OSN"
        """
        status = False

        if not self.core._set_casher():
            return status

        receipt_type = receipt_data.get("docType")
        receipt_print = receipt_data.get("printReceipt")
        receipt_email = receipt_data.get("email")
        receipt_tax_mode = self.tax_mode.get(receipt_data.get("taxMode"))

        if receipt_type == "SALE":
            self.fptr.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE, IFptr.LIBFPTR_RT_SELL)
        elif receipt_type == "RETURN":
            self.fptr.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_TYPE, IFptr.LIBFPTR_RT_SELL_RETURN)
        else:
            return status

        if receipt_print:
            self.fptr.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_ELECTRONICALLY, False)
        else:
            self.fptr.setParam(IFptr.LIBFPTR_PARAM_RECEIPT_ELECTRONICALLY, True)

        self.fptr.setParam(1008, receipt_email)
        self.fptr.setParam(1055, receipt_tax_mode)
        # Признак расчета в интернете
        self.fptr.setParam(1125, 1)

        if self.fptr.openReceipt() < 0:
            self.core._error_log()
        else:
            status = True

        return status

    def cancel_receipt(self):
        """
        Отмена чека
        :return: status
        :rtype: bool
        """
        status = False

        if self.fptr.cancelReceipt() < 0:
            self.core._error_log()
        else:
            status = True

        return status

    def receipt_registration(self, product):
        """
        Регистрация позиции
        Тип налога (LIBFPTR_PARAM_TAX_TYPE) может принимать следующие значения:

        LIBFPTR_TAX_VAT10 - НДС 10%;
        LIBFPTR_TAX_VAT110 - НДС рассчитанный 10/110;
        LIBFPTR_TAX_VAT0 - НДС 0%;
        LIBFPTR_TAX_NO - не облагается;
        LIBFPTR_TAX_VAT20 - НДС 20%;
        LIBFPTR_TAX_VAT120 - НДС рассчитанный 20/120;
        LIBFPTR_TAX_VAT5 - НДС 5%;
        LIBFPTR_TAX_VAT105 - НДС рассчитанный 5/105;
        LIBFPTR_TAX_VAT7 - НДС 7%;
        LIBFPTR_TAX_VAT107 - НДС рассчитанный 7/107;
        LIBFPTR_TAX_VAT22 - НДС 22%;
        LIBFPTR_TAX_VAT122 - НДС рассчитанный 22/122.

        1102	Сумма НДС чека по ставке 20%	double
        1103	Сумма НДС чека по ставке 10%	double
        1104	Сумма расчёта по чеку с НДС по ставке 0%	double
        1105	Сумма расчёта по чека без НДС	double
        1106	Сумма НДС чека по расч. ставке 20/120	double
        1107	Сумма НДС чека по расч. ставке 10/110	double

        "inventPositions":[
            {
                "name":"Сланцы adidas Originals YEEZY Foam Runner Moon Gray/Moon Gray/Moon Gray",
                "price":6990,
                "quantity":"1",
                "vatTag":1102,
                "discSum":0,
                "nomenclatureCode":"44 4D 03 B2 3C AF 78 CB 70 25 63 33 35 6F 7A 52 79 2C 72 3F 7A"
            },
            {
                "name":"Самовывоз",
                "price":"0.0000",
                "quantity":"1",
                "vatTag":1102,
                "discSum":0,
                "nomenclatureCode":null
            }
          ],
        :return: status
        :rtype: bool
        """
        status = False

        product_name = product.get("name")
        product_price = product.get("price")
        product_quantity = product.get("quantity")
        # product_tax = product.get("vatTag")
        product_nomenclature_code = product.get("nomenclatureCode")
        product_code_check = product.get("codeCheck")
        product_disc_sum = product.get("discSum")

        self.fptr.setParam(IFptr.LIBFPTR_PARAM_COMMODITY_NAME, product_name)
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_PRICE, product_price)
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_QUANTITY, product_quantity)
        # Для запроса суммы налога за чек необходимо вызвать метод queryData() с типом запроса LIBFPTR_PARAM_DATA_TYPE
        # равным LIBFPTR_DT_RECEIPT_TAX_SUM и указать тип налога LIBFPTR_PARAM_TAX_TYPE.
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_TAX_TYPE, IFptr.LIBFPTR_TAX_VAT22)
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_TAX_SUM, 78.56)

        if product_nomenclature_code:
            # Запускаем проверку КМ
            self.fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE, product_nomenclature_code)
            self.fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE_STATUS, 2)
            self.fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_PROCESSING_MODE, 0)
            self.fptr.setParam(IFptr.LIBFPTR_PARAM_MEASUREMENT_UNIT, IFptr.LIBFPTR_IU_PIECE)
            self.fptr.beginMarkingCodeValidation()

            # Дожидаемся окончания проверки и запоминаем результат
            while True:
                self.fptr.getMarkingCodeValidationStatus()
                if self.fptr.getParamBool(IFptr.LIBFPTR_PARAM_MARKING_CODE_VALIDATION_READY):
                    break

            validation_result = self.fptr.getParamInt(IFptr.LIBFPTR_PARAM_MARKING_CODE_ONLINE_VALIDATION_RESULT)

            # Подтверждаем реализацию товара с указанным КМ
            self.fptr.acceptMarkingCode()

            # Результат проверки разрешительного режима кода маркировки(Регистрация позиции с отраслевым
            # реквизитом предмета расчета (тег 1260, ФФД 1.2))
            if product_code_check:
                self.fptr.setParam(1262, '030')
                self.fptr.setParam(1263, '21.11.2023')
                self.fptr.setParam(1264, '1944')
                self.fptr.setParam(1265, product_code_check)
                self.fptr.utilFormTlv()
                industry_info = self.fptr.getParamByteArray(IFptr.LIBFPTR_PARAM_TAG_VALUE)
                self.fptr.setParam(1260, industry_info)
                self.fptr.setParam(1212, 33)

            self.fptr.setParam(IFptr.LIBFPTR_PARAM_COMMODITY_NAME, product_name)
            self.fptr.setParam(IFptr.LIBFPTR_PARAM_PRICE, product_price)
            self.fptr.setParam(IFptr.LIBFPTR_PARAM_QUANTITY, product_quantity)
            # Для запроса суммы налога за чек необходимо вызвать метод queryData() с типом запроса LIBFPTR_PARAM_DATA_TYPE
            # равным LIBFPTR_DT_RECEIPT_TAX_SUM и указать тип налога LIBFPTR_PARAM_TAX_TYPE.
            self.fptr.setParam(IFptr.LIBFPTR_PARAM_TAX_TYPE, IFptr.LIBFPTR_TAX_VAT22)
            self.fptr.setParam(IFptr.LIBFPTR_PARAM_TAX_SUM, 78.56)
            self.fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE_ONLINE_VALIDATION_RESULT, validation_result)
            self.fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE, product_nomenclature_code)
            self.fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_CODE_STATUS, 2)
            self.fptr.setParam(IFptr.LIBFPTR_PARAM_MARKING_PROCESSING_MODE, 0)
            self.fptr.setParam(IFptr.LIBFPTR_PARAM_MEASUREMENT_UNIT, IFptr.LIBFPTR_IU_PIECE)
        else:
            self.fptr.setParam(IFptr.LIBFPTR_PARAM_MEASUREMENT_UNIT, IFptr.LIBFPTR_IU_PIECE)
            self.fptr.setParam(1212, 1)

        if product_disc_sum > 0:
            self.fptr.setParam(IFptr.LIBFPTR_PARAM_INFO_DISCOUNT_SUM, product_disc_sum)

        if self.fptr.registration() < 0:
            self.core._error_log()
        else:
            status = True

        return status

    def receipt_payment(self, money_position):
        """
        Регистрация оплаты

        Способ расчета (LIBFPTR_PARAM_PAYMENT_TYPE) может принимать следующие значения:
            LIBFPTR_PT_CASH - наличными
            LIBFPTR_PT_ELECTRONICALLY - безналичными
            LIBFPTR_PT_PREPAID - предварительная оплата (аванс)
            LIBFPTR_PT_CREDIT - последующая оплата (кредит)
            LIBFPTR_PT_OTHER - иная форма оплаты (встречное предоставление)
            LIBFPTR_PT_6 - способ расчета №6
            LIBFPTR_PT_7 - способ расчета №7
            LIBFPTR_PT_8 - способ расчета №8
            LIBFPTR_PT_9 - способ расчета №9
            LIBFPTR_PT_10 - способ расчета №10

        Пример:
        "moneyPositions": {
            "paymentType": "CARD",
            "sum": 46.8
        }

        :return: status
        :rtype: bool
        """
        status = False

        sum = money_position.get("sum")

        self.fptr.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_TYPE, IFptr.LIBFPTR_PT_ELECTRONICALLY)
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_PAYMENT_SUM, sum)

        if self.fptr.payment() < 0:
            self.core._error_log()
        else:
            status = True

        return status

    def receipt_total(self, money_position):
        """
        Регистрация итога на чек

        "moneyPositions":[
            {
                "paymentType":"CARD",
                "sum":6990
            }
        ]

        :return: status
        :rtype: bool
        """
        status = False

        sum = money_position.get("sum")

        self.fptr.setParam(IFptr.LIBFPTR_PARAM_SUM, sum)

        if self.fptr.receiptTotal() < 0:
            self.core._error_log()
        else:
            status = True

        return status

    def receipt_close(self):
        """
        Закрытие чека
        :return: status
        :rtype: bool
        """
        status = False

        if self.fptr.closeReceipt() < 0:
            self.core._error_log()
        else:
            status = True

        return status
