# encoding: utf-8
import binascii
from Crypto.Cipher import AES
class TSHeader:
    def __init__(self, sync_byte, transport_error_indicator, payload_unit_start_indicator, transport_priority, pid, transport_scrambling_control, adaptation_field, continuity_counter):
        self.sync_byte = sync_byte
        self.transport_error_indicator = transport_error_indicator
        self.payload_unit_start_indicator = payload_unit_start_indicator
        self.transport_priority = transport_priority
        self.pid = pid
        self.transport_scrambling_control = transport_scrambling_control
        self.adaptation_field = adaptation_field
        self.continuity_counter = continuity_counter
        self.has_error = False
        self.is_payload_start = False
        self.has_adaptation_field_field = False
        self.has_payload = False
class TSPacket:
    def __init__(self, header, pack_no, offset):
        self.header = header
        self.pack_no = pack_no
        self.start_offset = offset
        self.header_length = 4
        self.atf_length = 0
        self.pes_offset = 0
        self.pes_header_length = 0
        self.payload_relative_offset = 0
        self.payload_start_offset = 0
        self.payload_length = 0
        self.payload = None
class TSPesFragment:
    def __init__(self):
        self.packets = []
    def add(self, packet):
        self.packets.append(packet)
class TSStream:
    def __init__(self, data:bytes, key:bytes):
        self.data = bytearray(data)
        self.key = key
        self.packets = []
        self.videos = []
        self.audios = []
        self.PACKET_LENGTH=188
        self.SYNC_BYTE=0x47
        self.PAYLOAD_START_MASK=0x40
        self.ATF_MASK=0x30
        self.AtfReserve = 0x00
        self.ATF_PAYLOAD_ONLY = 0x01
        self.ATF_FIELD_ONLY = 0x02
        self.ATF_FIELD_FOLLOW_PAYLOAD = 0x03
    def parse_ts(self):
        byte_buf = memoryview(self.data)
        length = len(byte_buf)
        if length % self.PACKET_LENGTH != 0:
            raise Exception("not a ts package")
        pes = None
        pack_nums = length // self.PACKET_LENGTH
        for package_no in range(pack_nums):
            buffer = byte_buf[package_no*self.PACKET_LENGTH:(package_no+1)*self.PACKET_LENGTH]
            packet = self.parse_ts_packet(buffer, package_no, package_no*self.PACKET_LENGTH)
            if packet.header.pid == 0x100: # video data
                if packet.header.is_payload_start:
                    if pes is not None:
                        self.videos.append(pes)
                    pes = TSPesFragment()
                pes.add(packet)
            elif packet.header.pid == 0x101: # audio data
                if packet.header.is_payload_start:
                    if pes is not None:
                        self.audios.append(pes)
                    pes = TSPesFragment()
                pes.add(packet)
            self.packets.append(packet)
    def parse_ts_packet(self, buffer, pack_no, offset):
        if buffer[0] != self.SYNC_BYTE:
            raise Exception("Invalid ts package in :{} offset: {}".format(pack_no, offset))
        sync_byte = buffer[0]
        transport_error_indicator = 1 if (buffer[1] & 0x80) > 0 else 0
        payload_unit_start_indicator = 1 if (buffer[1] & self.PAYLOAD_START_MASK) > 0 else 0
        transport_priority = 1 if (buffer[1] & 0x20) > 0 else 0
        pid = (buffer[1] & 0x1F) << 8 | buffer[2]
        transport_scrambling_control = ((buffer[3] & 0xC0) >> 6) & 0xFF
        adaptation_field = ((buffer[3] & self.ATF_MASK) >> 4) & 0xFF
        continuity_counter = buffer[3] & 0x0F
        header = TSHeader(sync_byte, transport_error_indicator, payload_unit_start_indicator, transport_priority, pid, transport_scrambling_control, adaptation_field, continuity_counter)
        header.has_error = header.transport_error_indicator != 0
        header.is_payload_start = header.payload_unit_start_indicator != 0
        header.has_adaptation_field_field = header.adaptation_field == self.ATF_FIELD_ONLY or header.adaptation_field == self.ATF_FIELD_FOLLOW_PAYLOAD
        header.has_payload = header.adaptation_field == self.ATF_PAYLOAD_ONLY or header.adaptation_field == self.ATF_FIELD_FOLLOW_PAYLOAD
        packet = TSPacket(header, pack_no, offset)
        packet.header_length = 4
        if header.has_adaptation_field_field:
            atf_length = buffer[4] & 0xFF
            packet.header_length += 1
            packet.atf_length = int(atf_length)
        if header.is_payload_start:
            packet.pes_offset = packet.start_offset + packet.header_length + packet.atf_length
            packet.pes_header_length = int(6 + 3 + buffer[packet.header_length+packet.atf_length+8]&0xFF)
        packet.payload_relative_offset = packet.header_length + packet.atf_length + packet.pes_header_length
        packet.payload_start_offset = int(packet.start_offset + packet.payload_relative_offset)
        packet.payload_length = self.PACKET_LENGTH - packet.payload_relative_offset
        if packet.payload_length > 0:
            packet.payload = buffer[packet.payload_relative_offset:self.PACKET_LENGTH]
        return packet
class TSParser():
    PACKET_LENGTH = 188
    SYNC_BYTE = 0x47
    PAYLOAD_START_MASK = 0x40
    ATF_MASK = 0x30
    ATF_RESERVE = 0x00
    ATF_PAYLOAD_ONLY = 0x01
    ATF_FIELD_ONLY = 0x02
    ATF_FIELD_FOLLOW_PAYLOAD = 0x03
    def __init__(self, data:bytes, key:bytes,decode_func=None):
        self.key=key
        self.stream = TSStream(data, self.key)
        if decode_func:
            self.decrypt_func=decode_func
    def decrypt_func(self, content:bytes): #ECB
        decrypt = AES.new(self.key, AES.MODE_ECB)
        decrypt_data = b''# 初始化解密后的数据
        size = 16  # 每次解密的数据块大小
        for bs in range(0, len(content), size):
            be = bs + size  # 对每个数据块进行解密
            decrypt_data += decrypt.decrypt(content[bs:be])
        return decrypt_data
    def decrypt_pes(self, byte_buf:bytes, pes_fragments, key:bytes):
        for pes in pes_fragments:
            decrypted_payloads = []
            for packet in pes.packets:
                if packet.payload is None:
                    raise Exception("payload is null")
                decrypted_payloads.append(packet.payload)
            decrypted_byte_string = b''.join(decrypted_payloads)
            length = len(decrypted_byte_string)
            if length % 16 > 0:
                new_length = 16 * (length // 16)
                decrypted = self.decrypt_func(decrypted_byte_string[:new_length])
                decrypted_byte_string = decrypted + decrypted_byte_string[new_length:]
            else:
                decrypted = self.decrypt_func(decrypted_byte_string)
                decrypted_byte_string = decrypted
            # Rewrite decrypted bytes to byte_buf
            for packet in pes.packets:
                payload_length = packet.payload_length
                payload_start_offset = packet.payload_start_offset
                byte_buf[payload_start_offset:payload_start_offset+payload_length] = decrypted_byte_string[:payload_length]
                decrypted_byte_string = decrypted_byte_string[payload_length:]
    def decrypt(self):
        self.stream.parse_ts()
        self.decrypt_pes(self.stream.data, self.stream.videos, self.stream.key)
        self.decrypt_pes(self.stream.data, self.stream.audios, self.stream.key)
        return self.stream.data