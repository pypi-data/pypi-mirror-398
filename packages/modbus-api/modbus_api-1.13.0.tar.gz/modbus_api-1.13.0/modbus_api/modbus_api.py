# pylint: skip-file

"""封装Modbus读写方法."""
import logging
import os
import pathlib
import struct
from logging.handlers import TimedRotatingFileHandler
from typing import Union, List

from modbus_tk import modbus_tcp
from modbus_tk import defines as cst

from modbus_api.exception import PLCConnectError, PLCReadError, PLCWriteError


class ModbusApi:
    """ModbusApi class."""
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"


    def __init__(self, plc_ip: str, port: int = 502, plc_name: str = "", save_log: bool = False):
        """ModbusApi 构造方法.

        Args:
            plc_ip: plc ip address.
            port: port number.
            plc_name: plc name.
            save_log: whether save log or not.
        """
        logging.basicConfig(level=logging.INFO, encoding="UTF-8", format=self.LOG_FORMAT)

        self.save_log = save_log
        self.plc_ip = plc_ip
        self.port = port
        self.logger = logging.getLogger(__name__)
        self.plc_name = plc_name if plc_name else self.plc_ip

        self.client = modbus_tcp.TcpMaster(host=plc_ip, port=port)
        self._connection_state = False

        self._file_handler = None  # 保存日志的处理器
        self._initial_log_config()

    def _initial_log_config(self):
        """日志配置."""
        if self.save_log:
            self._create_log_dir()
            self.logger.addHandler(self.file_handler)  # handler_passive 日志保存到统一文件

    @staticmethod
    def _create_log_dir():
        """判断log目录是否存在, 不存在就创建."""
        log_dir = pathlib.Path(f"{os.getcwd()}/log")
        if not log_dir.exists():
            os.mkdir(log_dir)

    @property
    def file_handler(self) -> TimedRotatingFileHandler:
        """设置保存日志的处理器, 每隔 24h 自动生成一个日志文件.

        Returns:
            TimedRotatingFileHandler: 返回 TimedRotatingFileHandler 日志处理器.
        """
        if self._file_handler is None:
            self._file_handler = TimedRotatingFileHandler(
                f"{os.getcwd()}/log/plc_{self.plc_name}.log",
                when="D", interval=1, backupCount=10, encoding="UTF-8"
            )
            self._file_handler.namer = self._custom_log_name
            self._file_handler.setFormatter(logging.Formatter(self.LOG_FORMAT))
        return self._file_handler

    def _custom_log_name(self, log_path: str):
        """自定义新生成的日志名称.

        Args:
            log_path: 原始的日志文件路径.

        Returns:
            str: 新生成的自定义日志文件路径.
        """
        _, suffix, date_str, *__ = log_path.split(".")
        new_log_path = f"{os.getcwd()}/log/plc_{self.plc_name}_{date_str}.{suffix}"
        return new_log_path

    @property
    def ip(self):
        """获取plc ip."""
        return self.plc_ip

    @property
    def open_state(self) -> bool:
        """Return the connection state of the PLC.

        Returns:
            bool: True if the connection is open, False otherwise.
        """
        return self._connection_state

    def communication_open(self) -> bool:
        """Open the connection to the PLC.

        Returns:
            bool: True if the connection is open, False otherwise.

        Raises:
            PLCConnectError: If the connection is not open.
        """
        try:
            if not self._connection_state:
                self.client.open()
            self._connection_state = True
            return True
        except Exception as e:
            self.logger.error("Error connecting to PLC: %s", e)
            raise PLCConnectError(f"Error connecting to PLC: {e}") from e

    def communication_close(self):
        """Close the connection to the PLC."""
        if self._connection_state:
            self.client.close()
            self._connection_state = False
            self.logger.info("Closed connection to PLC")

    def read_bool(self, address: int, bit_index: int, save_log: bool = True) -> bool:
        """Read a specific boolean bit from the PLC at a given address.

        Args:
            address: The address to read from.
            bit_index: The index of the bit within the address to read.
            save_log: Whether to save the log or not.

        Returns:
            bool: The value of the specified bit.
        """
        try:
            registers = self.client.execute(
                slave=1, function_code=cst.READ_HOLDING_REGISTERS, starting_address=address, quantity_of_x=1
            )
            value = (registers[0] & (1 << bit_index)) != 0
            if save_log:
                self.logger.info("读取 bool 地址 %s 值为: %s, bit 位是: %s", address, value, bit_index)
            return value
        except Exception as e:
            self.logger.error("读取保持寄存器时出错: %s", str(e))
            raise PLCReadError(f"读取保持寄存器时出错: {e}") from e

    def read_int(self, address: int, save_log: bool = True) -> int:
        """Read an integer value from the PLC.
        Args:
            address: The address to read from.
            save_log: Whether to save the log or not.

        Returns:
            int: The value read from the PLC.
        """
        try:
            registers = self.client.execute(
                slave=1, function_code=cst.READ_HOLDING_REGISTERS, starting_address=address, quantity_of_x=1
            )
            int_value = registers[0]
            if save_log:
                self.logger.info("读取 int 地址 %s 值为: %s", address, int_value)
            return int_value
        except Exception as e:
            self.logger.error("读取输入寄存器时出错: %s", str(e))
            raise PLCReadError(f"读取输入寄存器时出错: {e}") from e

    def read_real(self, address: int, save_log: bool = True) -> float:
        """Read a real value from the PLC.

        Args:
            address: 地址.
            save_log: 是否保存日志, 默认保存.

        Returns:
            float: The real value read from the PLC.

        Raises:
            PLCReadError: If the read fails.
        """
        try:
            registers = self.client.execute(
                slave=1, function_code=cst.READ_HOLDING_REGISTERS, starting_address=address, quantity_of_x=2
            )
            high_byte, low_byte = registers[1], registers[0]
            packed_data = struct.pack('>HH', high_byte, low_byte)  # >HH: 大端序2个16位无符号整数
            real_value = struct.unpack('>f', packed_data)[0]  # >f: 大端序32位浮点

            if save_log:
                self.logger.info("读取 real 地址 %s 值为: %s", address, real_value)
            return real_value

        except Exception as e:
            self.logger.error("读取输入寄存器时出错: %s", str(e))
            raise PLCReadError(f"读取输入寄存器时出错: {e}") from e

    def read_str(self, address: int, size: int, save_log: bool = True) -> str:
        """Read a string value from the PLC.

        Args:
            address: The address to read from.
            size: 字节个数.
            save_log: Whether to save the log or not.

        Returns:
            str: The value read from the PLC.
        """
        try:
            results = self.client.execute(1, cst.READ_HOLDING_REGISTERS, address, quantity_of_x=size // 2)
            byte_data = b"".join(struct.pack(">H", result) for result in results[::-1])[::-1]
            byte_data = byte_data.split(b"\x00")[0]  # 提取第一个null字节之前的部分
            value_str = byte_data.decode("UTF-8").strip("\x00")
            if save_log:
                self.logger.info("读取 str 地址 %s 值为: %s, 字节个数为: %s", address, value_str, size)
            return value_str
        except Exception as e:
            self.logger.error("读取输入寄存器时出错: %s", str(e))
            raise PLCReadError(f"读取输入寄存器时出错: {e}") from e

    def write_bool(self, address: int, bit_index: int, value: bool, save_log: bool = True):
        """Write a specific boolean bit to the PLC at a given address.

        Args:
            address: The address to write to.
            bit_index: The index of the bit within the address to write.
            value: The boolean value to write.
            save_log: Whether to save the log or not.
        """
        try:
            coils = self.client.execute(
                slave=1, function_code=cst.READ_HOLDING_REGISTERS, starting_address=address, quantity_of_x=1
            )
            current_value = coils[0]
            if value:
                new_value = current_value | (1 << bit_index)
            else:
                new_value = current_value & ~(1 << bit_index)
            self.client.execute(
                slave=1, function_code=cst.WRITE_SINGLE_REGISTER, starting_address=address, output_value=new_value)
            if save_log:
                self.logger.info("向 bool 地址 %s 写入值 %s, bit 位是: %s", address, value, bit_index)
        except Exception as e:
            self.logger.error("写入保持寄存器时出错: %s", str(e))
            raise PLCWriteError(f"写入保持寄存器时出错: {e}") from e

    def write_int(self, address: int, value: Union[int, List[int]], save_log: bool = True):
        """Write an integer value to the PLC.

        Args:
            address: The address to write to.
            value: The integer value or list of integer values to write.
            save_log: Whether to save the log or not.
        """
        if isinstance(value, int):
            value = [value]
        try:
            self.client.execute(
                slave=1, function_code=cst.WRITE_MULTIPLE_REGISTERS, starting_address=address, output_value=value
            )
            if save_log:
                self.logger.info("向 int 地址 %s 写入值 %s", address, value)
        except Exception as e:
            self.logger.error("写入输入寄存器时出错: %s", str(e))
            raise PLCWriteError(f"写入输入寄存器时出错: {e}") from e

    def write_str(self, address: int, value: str, size: int, save_log: bool = True):
        """将字符串写入PLC的保持寄存器

        参数:
            address: 起始寄存器地址.
            value: 要写入的字符串.
            size: 字节大小.
            save_log: 是否保存日志.
        """
        try:
            byte_data = value.encode("UTF-8")
            byte_data_length = len(byte_data)
            registers = []
            for i in range(0, size, 2):
                # 获取两个字节(不足补0)
                byte2 = byte_data[i] if i < byte_data_length else 0x00
                byte1 = byte_data[i + 1] if (i + 1) < byte_data_length else 0x00
                # 组合成16位寄存器值
                register_value = (byte1 << 8) | byte2
                registers.append(register_value)

            self.client.execute(
                slave=1, function_code=cst.WRITE_MULTIPLE_REGISTERS, starting_address=address, output_value=registers
            )

            if save_log:
                self.logger.info("成功写入字符串 '%s' 到地址 %d", value, address)

        except Exception as e:
            self.logger.error("写入字符串时出错: %s", str(e))
            raise PLCWriteError(f"写入字符串到保持寄存器时出错: {e}") from e

    def read_multiple(self, start_address: int, end_address: int, save_log: bool = True) -> list:
        """读取连续多个字节.

        Args:
            start_address: 开始地址.
            end_address: 结束地址.
            save_log: Whether to save the log or not.

        Returns:
            list: 返回连续的值列表.
        """
        try:
            byte_size = int(end_address) - int(start_address)
            if byte_size > 200:
                raise PLCReadError(f"一次最多读 200 个字节, 目前要读的字节个数是: {byte_size}")

            count_num = byte_size // 2
            results = self.client.execute(1, cst.READ_HOLDING_REGISTERS, start_address, quantity_of_x=count_num)
            if save_log:
                self.logger.info("从 %s 到 %s 读取成功, 数据个数是 %s", start_address, end_address, len(results))
            return list(results)
        except Exception as e:
            self.logger.error("读取输入寄存器时出错: %s", str(e))
            raise PLCReadError(f"读取输入寄存器时出错: {e}") from e

    def write_multiple(self, start_address: int,  end_address: int, values: list, save_log: bool = True):
        """写连续多个 byte 值.

        参数:
            start_address: 起始寄存器地址.
            end_address: 结束地址.
            values: 要写入的值列表.
            save_log: 是否保存日志.
        """
        try:
            byte_size = int(end_address) - int(start_address)
            if byte_size != len(values):
                raise PLCWriteError("要写的 byte 个数和要写入值个数不匹配!")
            self.client.execute(
                slave=1, function_code=cst.WRITE_MULTIPLE_REGISTERS, starting_address=start_address, output_value=values
            )
            if save_log:
                self.logger.info("从 %s 开始连续写 %s 个值成功", start_address, len(values))

        except Exception as e:
            self.logger.error("写入连续值时出错: %s", str(e))
            raise PLCWriteError(f"写入连续值到保持寄存器时出错: {e}") from e

    # pylint: disable=R0913, R0917
    def execute_read(
            self, data_type: str, address: int, size: int = 1, bit_index: int = 0, save_log: bool = True
    ) -> Union[int, str, bool]:
        """Execute read function based on data_type.

        Args:
            data_type: The data type to read.
            address: The address to read from.
            size: 字节个数.
            bit_index: The index of the bit within the address to read.
            save_log: Whether to save the log or not.

        Returns:
            Union[int, str, bool]: The value read from the PLC.
        """
        address = int(address)
        if data_type == "bool":
            return self.read_bool(address, bit_index, save_log)
        if data_type == "int":
            return self.read_int(address, save_log)
        if data_type in  ["str", "string"]:
            return self.read_str(address, size, save_log)
        if data_type == "real":
            return self.read_real(address, save_log)

        raise ValueError(f"Invalid data type: {data_type}")

    # pylint: disable=R0913, R0917
    def execute_write(
            self, data_type: str, address: int, value: Union[bool, int, float, str],
            bit_index: int = 0, save_log: bool = True, **kwargs
    ):
        """Execute write function based on data_type.

        Args:
            data_type: The data type to write.
            address: The address to write to.
            value: The value to write.
            bit_index: The index of the bit within the address to write.
            save_log: Whether to save the log or not.

        Raises:
            KeyError: Write str must be input size.
        """
        address = int(address)
        if data_type == "bool":
            self.write_bool(address, bit_index, value, save_log)
        elif data_type == "int":
            self.write_int(address, value, save_log)
        elif data_type in ["str", "string"]:
            size = kwargs.get("size")
            if size is None:
                raise KeyError("写入字符串时必须要传入字节个数")
            self.write_str(address, value, size, save_log)
        else:
            raise ValueError(f"Invalid data type: {data_type}")
