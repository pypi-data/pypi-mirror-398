"""
maix.comm.modbus module
"""
from __future__ import annotations
import maix._maix.err
import typing
__all__: list[str] = ['MasterRTU', 'MasterTCP', 'Mode', 'RequestType', 'Slave', 'set_master_debug']
class MasterRTU:
    def __init__(self, device: str = '', baudrate: int = 115200) -> None:
        ...
    def read_coils(self, slave_id: int, addr: int, size: int, timeout_ms: int = -1, device: str = '', baudrate: int = -1) -> list[int]:
        """
        Reads coils from the Modbus device.
        This function reads a specified number of coils starting from a given address.
        It includes timeout settings to define how long to wait for a response.
        
        Args:
          - slave_id: The RTU slave address.
          - addr: The starting address for reading coils.
          - size: The number of coils to read.
          - timeout_ms: The timeout duration for waiting to receive a request.
        - A value of -1 makes the function block indefinitely until a request
        is received.
        - A value of 0 makes it non-blocking, returning immediately without
        waiting for a request.
        - A positive value specifies the maximum time (in milliseconds) to wait
        for a request before timing out.
          - device: The UART device to use. An empty string ("") indicates that the
        default device from the constructor will be used.
          - baudrate: The UART baud rate. A value of -1 signifies that the default baud rate
        from the constructor will be applied.
        
        
        Returns: std::vector<uint8_t>/list[int] A vector containing the read coil values.
        """
    def read_discrete_input(self, slave_id: int, addr: int, size: int, timeout_ms: int = -1, device: str = '', baudrate: int = -1) -> list[int]:
        """
        Reads discrete inputs from the Modbus device.
        This function reads a specified number of discrete inputs starting from a given address.
        
        Args:
          - slave_id: The RTU slave address.
          - addr: The starting address for reading discrete inputs.
          - size: The number of discrete inputs to read.
          - timeout_ms: The timeout duration for the write operation.
        - A value of -1 makes the function block until the write is complete.
        - A value of 0 makes it non-blocking.
        - A positive value specifies the maximum time (in milliseconds) to wait.
          - device: The UART device to use. An empty string ("") indicates that the
        default device from the constructor will be used.
          - baudrate: The UART baud rate. A value of -1 signifies that the default baud rate
        from the constructor will be applied.
        
        
        Returns: std::vector<uint8_t>/list[int] A vector containing the read discrete input values.
        """
    def read_holding_registers(self, slave_id: int, addr: int, size: int, timeout_ms: int = -1, device: str = '', baudrate: int = -1) -> list[int]:
        """
        Reads holding registers from the Modbus device.
        This function reads a specified number of holding registers starting from a given address.
        
        Args:
          - slave_id: The RTU slave address.
          - addr: The starting address for reading holding registers.
          - size: The number of holding registers to read.
          - timeout_ms: The timeout duration for the write operation.
        - A value of -1 makes the function block until the write is complete.
        - A value of 0 makes it non-blocking.
        - A positive value specifies the maximum time (in milliseconds) to wait.
          - device: The UART device to use. An empty string ("") indicates that the
        default device from the constructor will be used.
          - baudrate: The UART baud rate. A value of -1 signifies that the default baud rate
        from the constructor will be applied.
        
        
        Returns: std::vector<uint16_t>/list[int] A vector containing the read holding register values.
        """
    def read_input_registers(self, slave_id: int, addr: int, size: int, timeout_ms: int = -1, device: str = '', baudrate: int = -1) -> list[int]:
        """
        Reads input registers from the Modbus device.
        This function reads a specified number of input registers starting from a given address.
        
        Args:
          - slave_id: The RTU slave address.
          - addr: The starting address for reading input registers.
          - size: The number of input registers to read.
          - timeout_ms: The timeout duration for the write operation.
        - A value of -1 makes the function block until the write is complete.
        - A value of 0 makes it non-blocking.
        - A positive value specifies the maximum time (in milliseconds) to wait.
          - device: The UART device to use. An empty string ("") indicates that the
        default device from the constructor will be used.
          - baudrate: The UART baud rate. A value of -1 signifies that the default baud rate
        from the constructor will be applied.
        
        
        Returns: std::vector<uint16_t>/list[int] A vector containing the read input register values.
        """
    def write_coils(self, slave_id: int, data: list[int], addr: int, timeout_ms: int = -1, device: str = '', baudrate: int = -1) -> int:
        """
        Writes values to coils on the Modbus device.
        This function writes the specified data to the coils starting from a given address.
        
        Args:
          - slave_id: The RTU slave address.
          - data: A vector containing the coil values to write.
          - addr: The starting address for writing coils.
          - timeout_ms: The timeout duration for the write operation.
        - A value of -1 makes the function block until the write is complete.
        - A value of 0 makes it non-blocking.
        - A positive value specifies the maximum time (in milliseconds) to wait.
          - device: The UART device to use. An empty string ("") indicates that the
        default device from the constructor will be used.
          - baudrate: The UART baud rate. A value of -1 signifies that the default baud rate
        from the constructor will be applied.
        
        
        Returns: int Returns the number of bytes written on success, or a value less than 0 on failure.
        """
    def write_holding_registers(self, slave_id: int, data: list[int], addr: int, timeout_ms: int = -1, device: str = '', baudrate: int = -1) -> int:
        """
        Writes values to holding registers on the Modbus device.
        This function writes the specified data to the holding registers starting from a given address.
        
        Args:
          - slave_id: The RTU slave address.
          - data: A vector containing the values to write to holding registers.
          - addr: The starting address for writing holding registers.
          - timeout_ms: The timeout duration for the write operation.
        - A value of -1 makes the function block until the write is complete.
        - A value of 0 makes it non-blocking.
        - A positive value specifies the maximum time (in milliseconds) to wait.
          - device: The UART device to use. An empty string ("") indicates that the
        default device from the constructor will be used.
          - baudrate: The UART baud rate. A value of -1 signifies that the default baud rate
        from the constructor will be applied.
        
        
        Returns: int Returns the number of bytes written on success, or a value less than 0 on failure.
        """
class MasterTCP:
    def __init__(self, port: int = 502) -> None:
        ...
    def read_coils(self, ip: str, addr: int, size: int, timeout_ms: int = -1, port: int = -1) -> list[int]:
        """
        Reads coils from the Modbus device.
        This function reads a specified number of coils starting from a given address.
        It includes timeout settings to define how long to wait for a response.
        
        Args:
          - ip: The TCP IP address.
          - addr: The starting address for reading coils.
          - size: The number of coils to read.
          - timeout_ms: The timeout duration for waiting to receive a request.
        - A value of -1 makes the function block indefinitely until a request
        is received.
        - A value of 0 makes it non-blocking, returning immediately without
        waiting for a request.
        - A positive value specifies the maximum time (in milliseconds) to wait
        for a request before timing out.
          - port: The TCP port. A value of -1 signifies that the default port
        from the constructor will be applied.
        
        
        Returns: std::vector<uint8_t>/list[int] A vector containing the read coil values.
        """
    def read_discrete_input(self, ip: str, addr: int, size: int, timeout_ms: int = -1, port: int = -1) -> list[int]:
        """
        Reads discrete inputs from the Modbus device.
        This function reads a specified number of discrete inputs starting from a given address.
        
        Args:
          - ip: The TCP IP address.
          - addr: The starting address for reading discrete inputs.
          - size: The number of discrete inputs to read.
          - timeout_ms: The timeout duration for the write operation.
        - A value of -1 makes the function block until the write is complete.
        - A value of 0 makes it non-blocking.
        - A positive value specifies the maximum time (in milliseconds) to wait.
          - port: The TCP port. A value of -1 signifies that the default port
        from the constructor will be applied.
        
        
        Returns: std::vector<uint8_t>/list[int] A vector containing the read discrete input values.
        """
    def read_holding_registers(self, ip: str, addr: int, size: int, timeout_ms: int = -1, port: int = -1) -> list[int]:
        """
        Reads holding registers from the Modbus device.
        This function reads a specified number of holding registers starting from a given address.
        
        Args:
          - ip: The TCP IP address.
          - addr: The starting address for reading holding registers.
          - size: The number of holding registers to read.
          - timeout_ms: The timeout duration for the write operation.
        - A value of -1 makes the function block until the write is complete.
        - A value of 0 makes it non-blocking.
        - A positive value specifies the maximum time (in milliseconds) to wait.
          - port: The TCP port. A value of -1 signifies that the default port
        from the constructor will be applied.
        
        
        Returns: std::vector<uint16_t>/list[int] A vector containing the read holding register values.
        """
    def read_input_registers(self, ip: str, addr: int, size: int, timeout_ms: int = -1, port: int = -1) -> list[int]:
        """
        Reads input registers from the Modbus device.
        This function reads a specified number of input registers starting from a given address.
        
        Args:
          - ip: The TCP IP address.
          - addr: The starting address for reading input registers.
          - size: The number of input registers to read.
          - timeout_ms: The timeout duration for the write operation.
        - A value of -1 makes the function block until the write is complete.
        - A value of 0 makes it non-blocking.
        - A positive value specifies the maximum time (in milliseconds) to wait.
          - port: The TCP port. A value of -1 signifies that the default port
        from the constructor will be applied.
        
        
        Returns: std::vector<uint16_t>/list[int] A vector containing the read input register values.
        """
    def write_coils(self, ip: str, data: list[int], addr: int, timeout_ms: int = -1, port: int = -1) -> int:
        """
        Writes values to coils on the Modbus device.
        This function writes the specified data to the coils starting from a given address.
        
        Args:
          - ip: The TCP IP address.
          - data: A vector containing the coil values to write.
          - addr: The starting address for writing coils.
          - timeout_ms: The timeout duration for the write operation.
        - A value of -1 makes the function block until the write is complete.
        - A value of 0 makes it non-blocking.
        - A positive value specifies the maximum time (in milliseconds) to wait.
          - port: The TCP port. A value of -1 signifies that the default port
        from the constructor will be applied.
        
        
        Returns: int Returns the number of bytes written on success, or a value less than 0 on failure.
        """
    def write_holding_registers(self, ip: str, data: list[int], addr: int, timeout_ms: int = -1, port: int = -1) -> int:
        """
        Writes values to holding registers on the Modbus device.
        This function writes the specified data to the holding registers starting from a given address.
        
        Args:
          - ip: The TCP IP address.
          - data: A vector containing the values to write to holding registers.
          - addr: The starting address for writing holding registers.
          - timeout_ms: The timeout duration for the write operation.
        - A value of -1 makes the function block until the write is complete.
        - A value of 0 makes it non-blocking.
        - A positive value specifies the maximum time (in milliseconds) to wait.
          - port: The TCP port. A value of -1 signifies that the default port
        from the constructor will be applied.
        
        
        Returns: int Returns the number of bytes written on success, or a value less than 0 on failure.
        """
class Mode:
    """
    Members:
    
      RTU
    
      TCP
    """
    RTU: typing.ClassVar[Mode]  # value = <Mode.RTU: 0>
    TCP: typing.ClassVar[Mode]  # value = <Mode.TCP: 1>
    __members__: typing.ClassVar[dict[str, Mode]]  # value = {'RTU': <Mode.RTU: 0>, 'TCP': <Mode.TCP: 1>}
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    def __init__(self, value: int) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, state: int) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class RequestType:
    """
    Members:
    
      READ_COILS
    
      READ_DISCRETE_INPUTS
    
      READ_HOLDING_REGISTERS
    
      READ_INPUT_REGISTERS
    
      WRITE_SINGLE_COIL
    
      WRITE_SINGLE_REGISTER
    
      DIAGNOSTICS
    
      GET_COMM_EVENT_COUNTER
    
      WRITE_MULTIPLE_COILS
    
      WRITE_MULTIPLE_REGISTERS
    
      REPORT_SERVER_ID
    
      MASK_WRITE_REGISTER
    
      READ_WRITE_MULTIPLE_REGISTERS
    
      READ_DEVICE_IDENTIFICATION
    
      UNKNOWN
    """
    DIAGNOSTICS: typing.ClassVar[RequestType]  # value = <RequestType.DIAGNOSTICS: 8>
    GET_COMM_EVENT_COUNTER: typing.ClassVar[RequestType]  # value = <RequestType.GET_COMM_EVENT_COUNTER: 11>
    MASK_WRITE_REGISTER: typing.ClassVar[RequestType]  # value = <RequestType.MASK_WRITE_REGISTER: 22>
    READ_COILS: typing.ClassVar[RequestType]  # value = <RequestType.READ_COILS: 1>
    READ_DEVICE_IDENTIFICATION: typing.ClassVar[RequestType]  # value = <RequestType.READ_DEVICE_IDENTIFICATION: 43>
    READ_DISCRETE_INPUTS: typing.ClassVar[RequestType]  # value = <RequestType.READ_DISCRETE_INPUTS: 2>
    READ_HOLDING_REGISTERS: typing.ClassVar[RequestType]  # value = <RequestType.READ_HOLDING_REGISTERS: 3>
    READ_INPUT_REGISTERS: typing.ClassVar[RequestType]  # value = <RequestType.READ_INPUT_REGISTERS: 4>
    READ_WRITE_MULTIPLE_REGISTERS: typing.ClassVar[RequestType]  # value = <RequestType.READ_WRITE_MULTIPLE_REGISTERS: 23>
    REPORT_SERVER_ID: typing.ClassVar[RequestType]  # value = <RequestType.REPORT_SERVER_ID: 17>
    UNKNOWN: typing.ClassVar[RequestType]  # value = <RequestType.UNKNOWN: 255>
    WRITE_MULTIPLE_COILS: typing.ClassVar[RequestType]  # value = <RequestType.WRITE_MULTIPLE_COILS: 15>
    WRITE_MULTIPLE_REGISTERS: typing.ClassVar[RequestType]  # value = <RequestType.WRITE_MULTIPLE_REGISTERS: 16>
    WRITE_SINGLE_COIL: typing.ClassVar[RequestType]  # value = <RequestType.WRITE_SINGLE_COIL: 5>
    WRITE_SINGLE_REGISTER: typing.ClassVar[RequestType]  # value = <RequestType.WRITE_SINGLE_REGISTER: 6>
    __members__: typing.ClassVar[dict[str, RequestType]]  # value = {'READ_COILS': <RequestType.READ_COILS: 1>, 'READ_DISCRETE_INPUTS': <RequestType.READ_DISCRETE_INPUTS: 2>, 'READ_HOLDING_REGISTERS': <RequestType.READ_HOLDING_REGISTERS: 3>, 'READ_INPUT_REGISTERS': <RequestType.READ_INPUT_REGISTERS: 4>, 'WRITE_SINGLE_COIL': <RequestType.WRITE_SINGLE_COIL: 5>, 'WRITE_SINGLE_REGISTER': <RequestType.WRITE_SINGLE_REGISTER: 6>, 'DIAGNOSTICS': <RequestType.DIAGNOSTICS: 8>, 'GET_COMM_EVENT_COUNTER': <RequestType.GET_COMM_EVENT_COUNTER: 11>, 'WRITE_MULTIPLE_COILS': <RequestType.WRITE_MULTIPLE_COILS: 15>, 'WRITE_MULTIPLE_REGISTERS': <RequestType.WRITE_MULTIPLE_REGISTERS: 16>, 'REPORT_SERVER_ID': <RequestType.REPORT_SERVER_ID: 17>, 'MASK_WRITE_REGISTER': <RequestType.MASK_WRITE_REGISTER: 22>, 'READ_WRITE_MULTIPLE_REGISTERS': <RequestType.READ_WRITE_MULTIPLE_REGISTERS: 23>, 'READ_DEVICE_IDENTIFICATION': <RequestType.READ_DEVICE_IDENTIFICATION: 43>, 'UNKNOWN': <RequestType.UNKNOWN: 255>}
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    def __init__(self, value: int) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, state: int) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class Slave:
    def __init__(self, mode: Mode, ip_or_device: str, coils_start: int = 0, coils_size: int = 0, discrete_start: int = 0, discrete_size: int = 0, holding_start: int = 0, holding_size: int = 0, input_start: int = 0, input_size: int = 0, rtu_baud: int = 115200, rtu_slave: int = 1, tcp_port: int = 502, debug: bool = False) -> None:
        ...
    def coils(self, data: list[int] = [], index: int = 0) -> list[int]:
        """
        Reads from or writes to coils.
        This function can be used to either read data from coils or write data to them.
        If the `data` parameter is empty, the function performs a read operation.
        If `data` is not empty, the function writes the contents of `data` to the coils
        starting at the specified index.
        
        Args:
          - data: A vector of data to be written. If empty, a read operation is performed.
        If not empty, the data will overwrite the coils from `index`.
          - index: The starting index for writing data. This parameter is ignored during read operations.
        
        
        Returns: std::vector<uint16_t> When the read operation is successful, return all data in the coils as a list.
        When the write operation is successful, return a non-empty list; when it fails, return an empty list.
        """
    def discrete_input(self, data: list[int] = [], index: int = 0) -> list[int]:
        """
        Reads from or writes to discrete input.
        This function can be used to either read data from discrete input or write data to them.
        If the `data` parameter is empty, the function performs a read operation.
        If `data` is not empty, the function writes the contents of `data` to the discrete input
        starting at the specified index.
        
        Args:
          - data: A vector of data to be written. If empty, a read operation is performed.
        If not empty, the data will overwrite the discrete input from `index`.
          - index: The starting index for writing data. This parameter is ignored during read operations.
        
        
        Returns: std::vector<uint16_t> When the read operation is successful, return all data in the discrete input as a list.
        When the write operation is successful, return a non-empty list; when it fails, return an empty list.
        """
    def holding_registers(self, data: list[int] = [], index: int = 0) -> list[int]:
        """
        Reads from or writes to holding registers.
        This function can be used to either read data from holding registers or write data to them.
        If the `data` parameter is empty, the function performs a read operation.
        If `data` is not empty, the function writes the contents of `data` to the holding registers
        starting at the specified index.
        
        Args:
          - data: A vector of data to be written. If empty, a read operation is performed.
        If not empty, the data will overwrite the holding registers from `index`.
          - index: The starting index for writing data. This parameter is ignored during read operations.
        
        
        Returns: std::vector<uint16_t> When the read operation is successful, return all data in the holding registers as a list.
        When the write operation is successful, return a non-empty list; when it fails, return an empty list.
        """
    def input_registers(self, data: list[int] = [], index: int = 0) -> list[int]:
        """
        Reads from or writes to input registers.
        This function can be used to either read data from input registers or write data to them.
        If the `data` parameter is empty, the function performs a read operation.
        If `data` is not empty, the function writes the contents of `data` to the input registers
        starting at the specified index.
        
        Args:
          - data: A vector of data to be written. If empty, a read operation is performed.
        If not empty, the data will overwrite the input registers from `index`.
          - index: The starting index for writing data. This parameter is ignored during read operations.
        
        
        Returns: std::vector<uint16_t> When the read operation is successful, return all data in the input registers as a list.
        When the write operation is successful, return a non-empty list; when it fails, return an empty list.
        """
    def receive(self, timeout_ms: int = -1) -> maix._maix.err.Err:
        """
        Receives a Modbus request
        This function is used to receive a Modbus request from the client. The behavior of the function
        depends on the parameter `timeout_ms` provided, which dictates how long the function will wait
        for a request before returning.
        
        Args:
          - timeout_ms: Timeout setting
        -1   Block indefinitely until a request is received
        0    Non-blocking mode; function returns immediately, regardless of whether a request is received
        >0   Blocking mode; function will wait for the specified number of milliseconds for a request
        
        
        Returns: maix::err::Err type, @see maix::err::Err
        """
    def receive_and_reply(self, timeout_ms: int = -1) -> RequestType:
        """
        Receives a request from the client and sends a response.
        This function combines the operations of receiving a request and sending a corresponding
        response in a single call. It waits for a specified duration (defined by the `timeout_ms`
        parameter) to receive a request from the client. Upon successful receipt of the request,
        it processes the request and prepares the necessary data to be sent back to the client.
        
        Args:
          - timeout_ms: The timeout duration for waiting to receive a request.
        - A value of -1 makes the function block indefinitely until a request
        is received.
        - A value of 0 makes it non-blocking, returning immediately without
        waiting for a request.
        - A positive value specifies the maximum time (in milliseconds) to wait
        for a request before timing out.
        
        
        Returns: RequestType The type of the Modbus request that has been received.
        """
    def reply(self) -> maix._maix.err.Err:
        """
        Processes the request and returns the corresponding data.
        This function handles the requests received from the client. It retrieves any data that the client
        needs to write to the registers and updates the registers accordingly. Additionally, it retrieves
        the requested data from the registers and sends it back to the client in the response.
        This function is essential for managing read and write operations in a Modbus Slave context.
        
        Returns: maix::err::Err type, @see maix::err::Err
        """
    def request_type(self) -> RequestType:
        """
        Gets the type of the Modbus request that was successfully received
        This function can be used to retrieve the type of the request received after a successful
        call to `receive()`. The return value indicates the type of the Modbus request, allowing
        the user to understand and process the received request appropriately.
        
        Returns: RequestType The type of the Modbus request that has been received.
        """
def set_master_debug(debug: bool) -> None:
    """
    Set the master debug ON/OFF
    
    Args:
      - debug: True(ON) or False(OFF)
    """
