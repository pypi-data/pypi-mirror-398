'''
Etatherm protocol API. 

On the wire protocol is intelectual property of Etatherm s.r.o
Please no reverse engineering.
'''
from __future__ import annotations
from datetime import datetime, timedelta
from math import floor
import asyncio
import serial_asyncio


class Etatherm:
    '''Etather protocol implementation'''
    _responseDelay=4

    def __init__(self, host: str, port:int, a:int, j:int, serial: str=None, baudrate:int=None) -> None:
        self._host=host
        self._port=port
        self._serial=serial
        self._baudrate=baudrate
        self._params=None
        self.a=a
        self.j=j

    def __get_header(self, a:int,j:int):
        return b'\x10\x01'+a.to_bytes(1,'big')+j.to_bytes(1,'big')

    def __get_addr_read(self, addr:bytes, cnt:int):
        if (cnt%2!=0):
            cnt+=1
        n=cnt//2 - 1
        n=n%16
        b=(n << 4)+8
        return addr+b.to_bytes(1,'big')

    def __get_addr_write(self, addr:bytes, cnt:int):
        n=cnt-1
        n=n%16
        b=(n << 4)+0x0c
        return addr+b.to_bytes(1,'big')

    def __get_delay(self):
        return (self._responseDelay//2).to_bytes(1,'big')

    def __get_crc(self, payload: bytes):
        s=0
        x=0
        for b in payload:
            s=b + s
            x=b ^ x
        return (s%256).to_bytes(1,'big') + (x%256).to_bytes(1,'big')

    def __check_header(self, data: bytes, a: int, j:int):
        while data[0:1]==b'\xff':
            data=data[1:]

        h=data[:2]
        if h!=b'\x10\x17':
            return (None, False)
        da=data[2:3]
        dj=data[3:4]
        if int.from_bytes(da,'little')!=a or int.from_bytes(dj,'little')!=j:
            return (None, False)
        return (data,True)

    def __check_tail(self, data):
        s1=data[-4:-3]
        s2=data[-3:-2]
        if s1!=b'\x00' and s2!=b'\x00':
            return (None, False)
        addxor=data[-2:]
        crc=self.__get_crc(data[:-2])
        if crc!=addxor:
            return (None, False)
        return (data[4:-4], True)

    async def __send_read_request(self, a:int, j:int, addr: bytes, count: int) -> tuple[bytes, str | None]:
        retr=3
        error=None
        while retr>0:
            retr-=1
            open_socket=await self.__get_socket()
            reader, writer = open_socket
            try:
                out_bytes=self.__get_header(a,j)+self.__get_addr_read(addr,count)+self.__get_delay()
                out_bytes=out_bytes+self.__get_crc(out_bytes) +b'\xff\xff'
                writer.write(out_bytes)
                await asyncio.wait_for(writer.drain(), 5)
                data = await asyncio.wait_for(reader.read(1024), 5)
                error = None
                break
            except TimeoutError:
                error= "Timeout"
            except ConnectionResetError:
                error= "No connection"
            finally:
                await self.__close_socket(open_socket)

        if error is not None:
            return (None, error)

        (data, ok)=self.__check_header(data, a, j)
        if not ok:
            return (None, 'Bad header')
        (data, ok)=self.__check_tail(data)
        if not ok:
            return (None,'Bad checksum')
        return (data, None)

    async def __send_write_request(self, a:int, j:int, addr: bytes, data: bytes)->(bool, str):
        retr=3
        error=None
        while retr>0:
            retr-=1
            open_socket=await self.__get_socket()
            reader, writer =open_socket
            try:
                out_bytes=self.__get_header(a,j)+self.__get_addr_write(addr,len(data))+data
                out_bytes=out_bytes+self.__get_crc(out_bytes) +b'\xff\xff'
                writer.write(out_bytes)
                await asyncio.wait_for(writer.drain(), 5)
                data = await asyncio.wait_for(reader.read(1024), 5)
                error = None
                break
            except TimeoutError:
                error= "Timeout"
            except ConnectionResetError:
                error= "No connection"
            finally:
                await self.__close_socket(open_socket)
        if error is not None:
            return (False, error)

        (data, ok)=self.__check_header(data, a, j)
        if not ok:
            return (False,'Bad header')
        (data, ok)=self.__check_tail(data)
        if not ok:
            return (False,'Bad checksum')
        if data!=b'\x00\x00':
            return (False,'Bad response')
        return (True, None)

    async def __read_params(self) -> None:
        start=0x1100
        name_start=0x1030
        res={}
        for pos in range(1,17): 
            addr=start+(pos-1)*0x10
            (params, error)=await self.__send_read_request(self.a,self.j, addr.to_bytes(2,'big'), 4)
            if params is None:
                res[pos]=(False, "<timeout>", 5, 1)
                continue
            used=params[0] & 0x07
            used=not (used==0)
            shift = params[2] & 0x3F
            shift = shift-(64*(shift//32))
            step=(params[2] & 0xc0) >> 6
            step=step+1
            if used:
                addr=name_start+(pos-1)*8
                (name, error)=await self.__send_read_request(self.a,self.j, addr.to_bytes(2,'big'), 8)
                if name is None:
                    name=b''
                end=name.find(b'\x00')
                if end!=-1:
                    name=name[:end]
                name=name.decode("1250")
            else:
                name=""
            res[pos]={'used':used, 'name':name, 'shift':shift, 'step':step }
        self._params=res

    async def get_parameters(self)->(dict[int,dict[str,str]]|None):
        '''Read positions configuration parameters'''
        if self._params is None:
            await self.__read_params()
        if self._params is None:
            return None
        res={pos:{'name': p['name'],'min':(1+p['shift'])*p['step'], 'max':(30+p['shift'])*p['step']} for pos,p in self._params.items() if p['used']}
        return res

    async def get_current_temperatures(self)-> (dict[int,int] | None):
        '''Read actual temperatures as measured on all positions.'''
        (data, _)=await self.__send_read_request(self.a,self.j, b'\x00\x60', 16)
        if self._params is None:
            await self.__read_params()
        if data is None or len(data)!=16 or self._params is None:
            return None
        res={}
        for pos in range(1,17):
            b=data[pos-1]
            position=self._params[pos]
            if position['used']:
                res[pos]= (b+position['shift'])*position['step']
        return res
    
    def __get_toy(self, time_in:datetime)->int:
        return (time_in.minute // 15)+(time_in.hour*4)+(time_in.day*32*4)+(time_in.month*32*32*4)

    async def set_mode(self, pos:int, auto:bool) ->bool:
        '''Set heating mode.'''
        start=0x1100
        addr=start+(pos-1)*0x10+0x03
        
        (data, _)=await self.__send_read_request(self.a,self.j,addr.to_bytes(2,'big'),6)
        if data is None:
            return False
        if auto:
            data=bytes([data[0] & 0xDF]) + b'\x10\x80\x10\x80'
        else:
            data=bytes([data[0] | 0x20]) + data[1:5]        
        (success, _)=await self.__send_write_request(self.a,self.j, addr.to_bytes(2,'big'), data)

        if not success:
            return False
        return True

    async def set_temporary_temperature(self, pos:int, temperature: int, duration: int=120)-> bool:
        '''Set temporary temperature on position. :Operativní změna: '''
        start=0x1100
        addr=start+(pos-1)*0x10+0x03
        
        if self._params is None:
            await self.__read_params()
        position=self._params[pos]
        temp=(floor(temperature)//position['step']-position['shift']) & 0x1f
        (data, _)=await self.__send_read_request(self.a,self.j,addr.to_bytes(2,'big'),1)
        if data is None:
            return False
        now = datetime.now()
        start=self.__get_toy(now-timedelta(minutes=0))
        end=self.__get_toy(now+timedelta(minutes=duration+1))
        data=bytes([(data[0] & 0xC0)+temp])+start.to_bytes(2,'big')+end.to_bytes(2,'big')
        (success, _)=await self.__send_write_request(self.a,self.j, addr.to_bytes(2,'big'), data)

        if not success:
            return False
        return True

    async def get_required_temperatures(self) -> (dict[int,dict[str,any]] | None):
        '''Returns "temp" - required temperature, "flag" - 0:summer, 1:HDO, 2:temporary temperature, 3:permanent temperature, 4:scheduled '''
        (data, _)=await self.__send_read_request(self.a,self.j, b'\x00\x70', 16)
        if self._params is None:
            await self.__read_params()
        if data is None or len(data)!=16 or self._params is None:
            return None
        res={}
        for pos in range(1,17):
            b=data[pos-1] & 0x1f
            flag=data[pos-1] >> 5
            position=self._params[pos]
            if position['used']:
                res[pos]= { 'temp': (b+position['shift'])*position['step'], 'flag': flag }
        return res

    async def __get_socket(self):
        if self._host is None or self._port is None:
            if self._serial is None or self._baudrate is None:
                return None
            return await serial_asyncio.open_serial_connection(url=self._serial, baudrate=self._baudrate)

        return await asyncio.open_connection(self._host, self._port)

    async def __close_socket(self, socket_in):
        if socket_in is not None:
            socket_in[1].close()
            await socket_in[1].wait_closed()
            socket_in=None






