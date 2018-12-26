import time
import settings
import smbus2 as smbus

class I2CInputDevice:
    def __init__(self, onShort, onLong, onLongL):
        self.onShort = onShort
        self.onLong = onLong
        self.onLongL = onLongL

    def get_on_short_id(self):
        return self.onShort

    def get_on_long_id(self):
        return self.onLong

    def get_on_longl_id(self):
        return self.onLongL

class I2CController:

    def __init__(self):
        self.busArray = [None, smbus.SMBus(1), smbus.SMBus(2)]

class I2CWriteController(I2CController):

    def __init__(self):
        I2CController.__init__(self)

    def set_enabled(self, i2cDevice, register, pin):
        value = self.busArray[i2cDevice].read_byte(register) & ~(1 << pin)
        self.busArray[i2cDevice].write_byte(register, value)

    def set_disabled(self, i2cDevice, register, pin):
        value = self.busArray[i2cDevice].read_byte(register) | (1 << pin)
        self.busArray[i2cDevice].write_byte(register, value)

    def trigger_value(self, i2cDevice, register, pin):
        value = self.busArray[i2cDevice].read_byte(register) ^ (1 << pin)
        self.busArray[i2cDevice].write_byte(register, value)
        return value & (1 << pin)

class I2CReadController(I2CController):
    expanderState = {}
    inputDict = {}

    def __init__(self, inputsDict, callback):
        I2CController.__init__(self)
        self.callback = callback
        self.init_inputs(inputsDict)
        self.i2c_read()

    def init_inputs(self, inputsDict):
        for key in inputsDict:
            devRegKey = key[:-1]
            devRegPin = int(key[-1:])
            self.inputDict[devRegKey] = self.inputDict.get(devRegKey, 0) | (1 << devRegPin)

    def is_input_state_changed(self, mask, value):
        return (value & mask) ^ mask

    def try_to_notify(self, targetKey):
        keyForNotify = None

        for key in self.expanderState:
            if key[:3] == targetKey:
                keyForNotify = key
        if keyForNotify != None:
            self.callback(key, self.expanderState[key])
            self.expanderState.pop(key, None)

    def i2c_read(self):
        while True:
            for key in self.inputDict:
                i2cDevice = int(key[:-2])
                i2cRegister = int(key[1:])
                modifiedPins = self.is_input_state_changed(self.inputDict[key], self.busArray[i2cDevice].read_byte(i2cRegister))

                if not modifiedPins:
                    if self.expanderState:
                        self.try_to_notify(key)
                else:
                    exStKey = key + str(modifiedPins)
                    self.expanderState[exStKey] = self.expanderState.get(exStKey, 0) + 1
            time.sleep(settings.i2cReadTimeout)
