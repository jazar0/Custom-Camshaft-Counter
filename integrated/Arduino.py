import serial
import time

class Arduino:

    def __init__(self, iPort, ibSimulate):
        self.commPort = iPort
        self.simulate = ibSimulate
        if not ibSimulate:
            print("Connecting")
            self.Arduino_Serial = serial.Serial(iPort, 115200)
        self.lineBufferCount = []
        self.lineBuffer = []
        self.bufferSize = 128
        self.grbl_out = ''
        self.g_count = 0
        self.verbose = False
        self.l_count = 0

    def connect(self):
        print("Starting GRBL")
        if self.simulate:
            print("Simulating")
            return
        else:
            while self.Arduino_Serial.in_waiting < 1:
                pass  # Wait for the response
            line = self.Arduino_Serial.readline()
            line = line.decode("utf-8", "replace")
        print("Connected: {}".format(line))

    def write(self, iText):
        # print(">{}".format(iText))
        # iText = iText + "\n"
        if self.simulate:
            return

        self.l_count = self.l_count + 1
        self.lineBufferCount.append(len(iText) + 1)
        self.lineBuffer.append(iText)
        self.grbl_out = ""
        #print("Buffer ({}) of Size({})".format(sum(self.lineBufferCount), self.bufferSize))
        while sum(self.lineBufferCount) > self.bufferSize or self.Arduino_Serial.inWaiting():
            out_temp = self.Arduino_Serial.readline().strip()  # Wait for grbl response
            out_temp = out_temp.decode("utf-8", "replace")
            #print("Waiting, out_temp = {}".format(out_temp))

            if out_temp.find('ok') < 0 and out_temp.find('error') < 0:
                print("  Debug: ", out_temp)  # Debug response
                if "Idle" in out_temp:
                    if "Pn:Z" in out_temp:
                        print("Z limit On")
                    else:
                        print("Z limit Off")
            else:
                self.grbl_out += out_temp
                self.g_count += 1  # Iterate g-code counter
                self.grbl_out += str(self.g_count);  # Add line finished indicator
                del self.lineBufferCount[0]  # Delete the block character count corresponding to the last 'ok'
                del self.lineBuffer[0]
        if self.verbose:
            print("SND: " + str(self.l_count) + " : " + iText)
        self.Arduino_Serial.write(str.encode(iText + "\n"))
        if self.verbose:
            print("BUF:", str(sum(self.lineBufferCount)), "REC:", self.grbl_out)
            print("BUF: {}".format(self.lineBufferCount))
            print("BUF: {}".format(self.lineBuffer))
            print("")

    def waitReady(self):
        if self.simulate:
            return

        while self.running():
            pass

    # Waits for arduino to start running
    def waitRunning(self):
        if self.simulate:
            return

        while not self.running():
            pass

    def running(self):
        if self.simulate:
            return True

        self.Arduino_Serial.flush()  # Get rid of any bytes
        self.Arduino_Serial.write(str.encode('y.'))  # Request Data
        while self.Arduino_Serial.in_waiting < 1:
            pass  # Wait for the response
        line = self.Arduino_Serial.readline()
        line = line.decode("utf-8", "replace")
        if line[0] == '0':
            return False
        else:
            return True

    def readLine(self):
        if self.simulate:
            return

        time.sleep(0.000)
        obLineRead = False
        if self.Arduino_Serial.in_waiting > 0:
            line = self.Arduino_Serial.readline()
            line = line.decode("utf-8", "replace")
            if len(line) > 2:
                line = line[:len(line) - 2]
            print("line: {}".format(line))
            obLineRead = True
        return obLineRead

    def read(self):
        if self.simulate:
            return

        time.sleep(0.005)
        self.Arduino_Serial.flush()  # Get rid of any bytes
        self.Arduino_Serial.write(str.encode('x.'))  # Request Data
        while self.Arduino_Serial.in_waiting < 1:
            pass  # Wait for the response
        line = self.Arduino_Serial.readline()
        # print(line)
        # line = "s    20   100   400        1000        2537        2530 0 0 1"
        line = line.decode("utf-8", "replace")
        if (len(line) > 2):
            line = line[0:len(line) - 1]
            print(line)
        stopped = True
        return stopped
