class UsbDataProcessor(object):
    def __init__(self):
        ...

    def parse(self, data):
        return data.decode()

    def serialize(self, data):
        return data.encode()

    @staticmethod
    def calculate_crc(data: bytes) -> int:
        """
        Calculating CRC16
        :param data: data for calculating CRC16
        :return: value of CRC16 (2 bytes)
        """
        crc = 0xFFFF
        for byte in data:
            crc ^= (byte << 8)
            for _ in range(0, 8):
                crc = (crc << 1) ^ 0x1021 if (crc & 0x8000) else crc << 1
        return crc & 0xFFFF
