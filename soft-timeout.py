import signal
import platform
import warnings
from contextlib import contextmanager
from pydantic import BaseModel, PositiveInt, ValidationError

#модель для валидации времени таймаута
class TimeoutConfig(BaseModel):
    seconds: PositiveInt #только положительные целые числа

@contextmanager
def soft_timeout(seconds: int):
    """
    Менеджер контекста для установки soft-timeout на Unix системах.
    На Windows выдает предупреждение и работает как no-op.

    Args:
       seconds: время в секундах для timeout.

    Raises:
       ValidationError: если seconds не является положительным целым числом.
       TimeoutError: если на Unix истек таймер. 
    """
    #валидация вхоного параметра через Pydantic
    try:
        config = TimeoutConfig(seconds=seconds)
    except ValidationError as e:
        raise ValidationError(f"Invalid timeout value: {e}")

    #проверяем, на какой OC работаем
    is_unix = platform.system() != "Windows"
    old_handler = None #инициализируем old_handler, чтобы избежать unbound ошибки

    #функция-обработчик сигнала SIGALRM
    def handle_timeout(signum, frame):
        raise TimeoutError("Operation timed out")

    if is_unix:
        #сохраняем старый обработчяик сигнала, если он был
        old_handler = signal.signal(signal.SIGALRM, handle_timeout)
        #устанавливаем таймер
        signal.alarm(config.seconds)
    else:
        #на Windows выдаем предупреждение, т к signal.alarm не поддерживается
        warnings.warn("Soft-timeout is not supported on Windows, running as no-op", RuntimeWarning)

    try:
        #передаем управление в блок with
        yield
    finally:
        if is_unix and old_handler is not None:
            #сбрасываем таймер
            signal.alarm(0)
            #восстанавливаем старый обработчик
            signal.signal(signal.SIGALRM, old_handler)

#пример
if __name__ == "__main__":
    import time

    try:
        #усчтанавливаем timeout на 2 сек
        with soft_timeout(2):
            print("Starting operation...")
            time.sleep(3) #симулируем выполнение долгой операции
            print("Operation completed.")
    except TimeoutError:
        print("Caught TimeoutError: operation took too long!")
    except ValidationError as e:
        print(f"Validation error: {e}")