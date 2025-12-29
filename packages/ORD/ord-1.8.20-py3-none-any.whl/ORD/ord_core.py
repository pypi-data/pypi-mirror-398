import threading

from libfptr10 import IFptr


class SingletonMeta(type):
    """
    В Python класс Одиночка можно реализовать по-разному. Возможные способы
    включают себя базовый класс, декоратор, метакласс. Мы воспользуемся
    метаклассом, поскольку он лучше всего подходит для этой цели.
    """
    _instances = {}
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    cls._instances[cls] = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Core(metaclass=SingletonMeta):
    casher_info = {
        'name': 'СИС. АДМИНИСТРАТОР',
        'inn': ''
    }

    def __init__(self, path: str = ''):
        """
        Инициализация драйвера:
        Настройка драйвера
        """
        self.fptr = IFptr(path)

        self.version = self.fptr.version()

        settings = {
            IFptr.LIBFPTR_SETTING_MODEL: IFptr.LIBFPTR_MODEL_ATOL_AUTO,
            IFptr.LIBFPTR_SETTING_PORT: IFptr.LIBFPTR_PORT_USB,
            IFptr.LIBFPTR_SETTING_USB_DEVICE_PATH: 'auto',
            IFptr.LIBFPTR_SETTING_OFD_CHANNEL: IFptr.LIBFPTR_OFD_CHANNEL_AUTO
        }

        self.fptr.setSettings(settings)

    def _set_casher(self):
        """
        Регистрация кассира

        Рекомендуется вызывать данный метод перед каждой
        фискальной операцией (открытие чека, печать отчета, ...).
        :return: status
        :rtype: bool
        """
        status = False

        self.fptr.setParam(1021, self.casher_info.get('name'))
        self.fptr.setParam(1203, self.casher_info.get('inn'))

        if self.fptr.operatorLogin() < 0:
            self._error_log()
        else:
            status = True

        return status

    def open_connect(self):
        """
        Открытие соединение с кассой
        :returns: status
        :rtype: bool
        """
        status = False
        if self.fptr.open() < 0:
            self._error_log()
        else:
            status = True

        return status

    def close_connect(self):
        """
        Закрытие соединения с кассой
        :returns: status
        :rtype: bool
        """
        status = False
        if self.fptr.close() < 0:
            self._error_log()
        else:
            status = True

        return status

    def is_opened(self):
        """
        Получение состояния соединения с кассой
        Результат метода не отражает текущее состояние подключения - если с ККТ
        была разорвана связь, то метод все также будет возвращать true, но методы,
        выполняющие какие-либо операции над ККТ,
        будут возвращать ошибку LIBFPTR_ERROR_NO_CONNECTION
        :returns: self.fptr.isOpened()
        :rtype: int
        """
        return self.fptr.isOpened()

    def get_version_driver(self):
        """
        Получение версии драйвера
        :returns: self.version
        :rtype: str
        """
        return self.version

    def get_current_datetime(self):
        """
        Текущие дата и время ККТ
        :returns: date_time
        :rtype: str
        """
        self.fptr.setParam(IFptr.LIBFPTR_PARAM_DATA_TYPE, IFptr.LIBFPTR_DT_DATE_TIME)
        self.fptr.queryData()

        date_time = self.fptr.getParamDateTime(IFptr.LIBFPTR_PARAM_DATE_TIME).strftime('%Y-%m-%d %H:%M:%S')

        return date_time

    def get_setting(self):
        """
        Получение настроек кассы
        :returns: setting_cash
        :rtype: dict
        """
        setting_cash = self.fptr.getSettings()

        return setting_cash

    def _check_document_close(self):
        """
        Проверка закрытия документа

        В ряде ситуаций (окончание бумаги, потеря связи с
        ККТ в момент регистрации документа) состояние документа остается неизвестным.
        Он может закрыться в ФН (что является необратимой операцией), но не напечататься на чековой ленте.
        Данный метод сверяет счетчики ККТ с сохраненными до закрытия документа копиями и вычисляет,
        закрылся ли он, а также проверяет состояние печати документа.
        :returns: status
        :rtype: bool
        """
        status = True

        while self.fptr.checkDocumentClosed() < 0:
            # Не удалось проверить состояние документа.
            # Вывести пользователю текст ошибки, попросить
            # устранить неполадку и повторить запрос
            self._error_log()
            status = False
            continue

        # if not self.fptr.getParamBool(IFptr.LIBFPTR_PARAM_DOCUMENT_CLOSED):
        #     # Документ не закрылся.
        #     # Требуется его отменить (если это чек) и сформировать заново
        #     self.fptr.cancelReceipt()
        #     return status

        if not self.fptr.getParamBool(IFptr.LIBFPTR_PARAM_DOCUMENT_PRINTED):
            # Можно сразу вызвать метод допечатывания документа,
            # он завершится с ошибкой, если это невозможно
            while self.fptr.continuePrint() < 0:
                # Если не удалось допечатать документ,
                # показать пользователю ошибку и попробовать еще раз.
                self._error_log()
                status = False
                continue

        return status

    def reboot(self):
        """
        Перезагрузка ККТ
        :return:
        """
        status = False

        if self.fptr.deviceReboot() < 0:
            self._error_log()
        else:
            status = True

        return status

    def _error_log(self):
        """
        Логирование ошибок
        Каждый метод драйвера возвращает индикатор результата выполнения.
        Этот индикатор может принимать значения 0 и -1.
        В случае если индикатор неравен 0, выполнение метода завершилось с ошибкой и
        есть возможность получить подробности о ней.
        Для этого у драйвера можно запросить код последней ошибки (метод errorCode()) и
        её текстовое описание (метод errorDescription()).
        Драйвер хранит информацию об ошибке до следующего вызова метода - после него информация об ошибке обновляется.
        Для явного сброса информации о последней ошибке нужно использовать метод resetError().
        """
        error_msg = '{} [{}]'.format(self.fptr.errorCode(), self.fptr.errorDescription())
        self.fptr.logWrite("FiscalPrinter", IFptr.LIBFPTR_LOG_ERROR, error_msg)

    def info_log(self, msg):
        """
        Логирование нотификаций
        :param msg:
        :return:
        """
        self.fptr.logWrite("FiscalPrinter", IFptr.LIBFPTR_LOG_INFO, msg)

    def __del__(self):
        if self.is_opened() == 1:
            self.close_connect()
