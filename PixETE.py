#!/usr/bin/env python

'''
Control ETE gimbal. Based on code by Alan Sanchez
'''

import serial, sys, time

class PixETE(object):
        def __init__(self, port='/dev/ttyUSB1', delay=0.1, yaw_steps=28800, roll_steps=9600):
                if port is not None:
                        self.ser = serial.Serial(port=port,
                                                 baudrate=9600, bytesize=7, parity='E', stopbits=2,
                                                 timeout=None)
                else:
                        self.ser = None
                        
                self.delay = delay
                self.roll_steps = roll_steps
                self.yaw_steps = yaw_steps
                self.start = "02 "
                self.cmd = "31 "
                self.fixed_bytes ="30 32 "
                self.end   = "03"
                self.run   =      "31 30 44 34 " 
                self.reset =      "31 30 44 34 " 
                self.test_pass =  "31 30 37 38"
                self.test_fail =  "31 30 37 38"
                self.test_wait =  "31 30 37 38"
                self.test_work =  "31 30 37 38"

	   #Addresses:
                self.ADDRESS={'yaw_pos': '31 30 43 38 ', #Command dictionary
                              'yaw_speed' :'31 30 43 43 ',
                              'roll_pos': '31 30 44 43 ',
                              'roll_speed': '31 30 45 30 ', 
                              'run':'31 30 44 34 ',
                              'reset':'31 30 44 34 ',
                              'accel':'31 30 44 34 '}  

        def command_hex(self, address, ndec=None):
                '''generate a command'''

        #Fixed Messages:
                if address == 'run':
                        PixETE_run =   "02 31 31 30 44 34 30 32 32 32 30 30 03 33 33"
                        return PixETE_run
                if address == 'reset':
                        return "02 31 31 30 44 34 30 32 34 34 30 30 03 33 37"
                if address == 'test_wait':
                        return "02 31 31 30 37 38 30 32 30 30 30 30 03 32 36"
                if address == 'test_pass':
                        return "02 31 31 30 37 38 30 32 30 31 30 30 03 32 37"
                if address == 'test_fail':
                        return "02 31 31 30 37 38 30 32 30 32 30 30 03 32 38"
                if address == 'test_work':
                        return "02 31 31 30 37 38 30 32 30 33 30 30 03 32 39"

        #Data Translation:
                nhex = format(ndec, '04X') #convert dec to hex
                HLhex = nhex[2]+nhex[3]+nhex[0]+nhex[1] #swap hi and low
                shex = '%s' %HLhex #convert hex to string
                idec = [ord(i) for i in shex]#convert each charachter to ascii decimal
                ihex = [format(i,'02X') for i in idec]#convert each ascii decimal to hex
                data = '%s %s %s %s '% (ihex[0], ihex[1], ihex[2], ihex[3])
                
        #Checksum Calculation:
                ETEchk = self.cmd+self.ADDRESS[address]+self.fixed_bytes+data+self.end
                ETE = ETEchk.split(' ') #split ETEchk into a string array
                cksum = format((int(ETE[0],16)+int(ETE[1],16)+int(ETE[2],16)+int(ETE[3],16)+
                                int(ETE[4],16)+int(ETE[5],16)+int(ETE[6],16)+int(ETE[7],16)+
                                int(ETE[8],16)+int(ETE[9],16)+int(ETE[10],16)+int(ETE[11],16)),'02X')
                l = [ord(i) for i in cksum] #convert each character to ascii decimal
                o = [format(n,'02X') for n in l] #convert each ascii decimal to hex
                size = len(o)
                ck2 = ' %s' %o[size-1]
                ck1 = ' %s' %o[size-2]

		#Print PixETE commands:
                PixETE = self.start+self.cmd+self.ADDRESS[address]+self.fixed_bytes+data+self.end+ck1+ck2 
                return PixETE #Returns control command for ETE

        def command_bytes(self, address, d=None):
                '''write command to serial port'''
                hex = self.command_hex(address, d)
                if self.ser is None:
                        print("Would send: %s" % hex)
                        return
                bytes = ''
                a = hex.split(' ')
                for v in a:
                        bytes += chr(int(v, base=16))
                print("sending: %s" % hex)
                time.sleep(self.delay)
                self.ser.write(bytes)

        def position(self, roll, yaw): #specify position for roll and yaw
                '''position at given roll and yaw'''
                yaw_pos = int(yaw * self.yaw_steps / 360.0)
                roll_pos = int(roll * self.roll_steps / 360.0)
                self.command_bytes('roll_pos', roll_pos)
                self.command_bytes('yaw_pos', yaw_pos)
                self.command_bytes('run', 'run')

        def rollspeed(self, roll_speed):  #specify speed for roll and yaw
                self.command_bytes('roll_speed', roll_speed)

        def yawspeed(self, yaw_speed):  #specify speed for roll and yaw
                self.command_bytes('yaw_speed', yaw_speed)

if __name__ == '__main__':
        from argparse import ArgumentParser
        parser = ArgumentParser(description=__doc__)
        
        parser.add_argument("--port", default='/dev/ttyUSB1', help="serial port") #Used to be default=NONE
        parser.add_argument("--reset", action='store_true', help="reset jig")
        parser.add_argument("--delay", type=float, default=0.1, help='command delay')
        parser.add_argument("--yaw-steps", type=int, default=28800, help='yaw step size')
        parser.add_argument("--roll-steps", type=int, default=9600, help='roll step size')
        parser.add_argument("--test_pass" , action='store_true', help='show pass screen')
        parser.add_argument("--test_fail" , action='store_true', help='show fail screen')
        parser.add_argument("--test_work" , action='store_true', help='show work screen')
        parser.add_argument("--test_wait" , action='store_true', help='show wait screen')
        parser.add_argument("roll", type=float, default=0, nargs='?', help="roll angle (degrees)")
        parser.add_argument("yaw", type=float, default=0, nargs='?', help="yaw angle (degrees)")
        parser.add_argument("--roll_speed", type=int, default=None, help='roll speed (pulses/sec')
        parser.add_argument("--yaw_speed", type=int, default=None, help='yaw speed (pulses/sec)')

        args = parser.parse_args()

        if args.roll > 360:
                print("Roll too large")
                sys.exit(1)

        if args.yaw > 335:
                print("Yaw too large")
                sys.exit(1)

        ete = PixETE(port=args.port, delay=args.delay, yaw_steps=args.yaw_steps, roll_steps=args.roll_steps)

        if args.reset:
                print("Resetting")
                ete.command_bytes('reset')
                sys.exit(0)

        if args.test_pass:
                print("displaying pass")
                ete.command_bytes('test_pass')
                

        if args.test_fail:
                print("displaying fail")
                ete.command_bytes('test_fail')
                

        if args.test_work:
                print("displaying work")
                ete.command_bytes('test_work')
                

        if args.test_wait:
                print("displaying wait")
                ete.command_bytes('test_wait')
                

        if args.roll_speed:
            print("changing roll speed")
            ete.rollspeed(args.roll_speed)
            

        if args.yaw_speed:
            print("changing yaw speed")
            ete.yawspeed(args.yaw_speed)   
        
        ete.position(args.roll, args.yaw)

