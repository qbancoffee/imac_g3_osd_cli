#!/usr/bin/python
"""
TODO:
 - Command line config loading
 - Multi mod input
 - Think about using OOP for base operation class,
   then settings have to register into a list
   => only need to define accepted settings /parms once
   Maybe have handler base <= ---handler [list] <>-- action (overide what to do with parm) => base actions
   Just thoughts
 - Tab completion for load / save?
 - Clean up console printing
"""

import os
import json
import RPi.GPIO as GPIO
from smbus import SMBus
import sys
bus = SMBus(1)

def turn_crt_on():
    write_to_ivad(0x46, 0x00, 0x00)
    write_to_ivad(0x46, 0x13, 0x0A)
    write_to_ivad(0x46, 0x00, 0xFA)
    

def write_to_ivad(address, msg_1, msg_2):
    bus.write_byte_data(address, msg_1, msg_2)

def apply_config():
    for parm in parms_list:
        write_to_ivad(0x46, parm.offset, user_config[parm.name])
class parm:
    def __init__(
            self, 
            name: str,
            offset: int, 
            min_val: int, 
            max_val: int
        ):
        self.name = name
        self.offset = offset
        self.min_val = min_val
        self.max_val = max_val

# will use number entered as index
parms_list = [
        parm("CONTRAST", 0x00, 0xB5, 0xFF),
        parm("RED DRIVE", 0x01, 0x00, 0xFF),
        parm("GREEN DRIVE", 0x02, 0x00, 0xFF),
        parm("BLUE DRIVE", 0x03, 0x00, 0xFF),
        parm("RED CUTOFF", 0x04, 0x00, 0xFF),
        parm("GREEN CUTOFF", 0x05, 0x00, 0xFF),
        parm("BLUE CUTOFF", 0x06, 0x00, 0xFF),
        parm("HORIZONTAL POSITION", 0x07, 0x80, 0xFF),
        parm("HEIGHT", 0x08, 0x80, 0xFF),
        parm("VERTICAL POSITION", 0x09, 0x00, 0x7F),
        parm("S CORRECTION", 0x0A, 0x80, 0xFF),
        parm("KEYSTONE", 0x0B, 0x00, 0xFF),
        parm("PINCUSHION", 0x0C, 0x80, 0xFF),
        parm("WIDTH", 0x0D, 0x00, 0x7F),
        parm("PINCUSHION BALANCE", 0x0E, 0x80, 0xFF),
        parm("PARALELLOGRAM", 0x0F, 0x80, 0xFF),
        parm("BRIGHTNESS DRIVE", 0x10, 0x00, 0x40),
        parm("BRIGHTNESS", 0x11, 0x00, 0x20),
        parm("ROTATION", 0x12, 0x00, 0x7F),
    ]

user_config = {
    "CONTRAST":            0xFA,
    "RED DRIVE":           0x93,
    "GREEN DRIVE":         0x93,
    "BLUE DRIVE":          0x8F,
    "RED CUTOFF":          0x90,
    "GREEN CUTOFF":        0x8B,
    "BLUE CUTOFF":         0x6D,
    "HORIZONTAL POSITION": 0x8C,
    "HEIGHT":              0xDC,
    "VERTICAL POSITION":   0x49,
    "S CORRECTION":        0x92,
    "KEYSTONE":            0xA2,
    "PINCUSHION":          0xBF,
    "WIDTH":               0x71,
    "PINCUSHION BALANCE":  0xC2,
    "PARALELLOGRAM":       0xD2,
    "BRIGHTNESS DRIVE":    0x40,
    "BRIGHTNESS":          0x09,
    "ROTATION":            0x27
}

hot_reload = False
argLoaded = False
fileLoaded = False
loadedFileName = ""

def main_loop():
    """ 
    Run the main CLI config loop.

    Implicitly makes changes to the user config attached to the crrent process.
    """
    
    global argLoaded
    global fileLoaded
    global loadedFileName
    argLoaded = False
    fileLoaded = False
    loadedFileName = ""

    entered_key = '';
    
    if len(sys.argv) == 3:
        loadedFileName = sys.argv[2]
        entered_key = sys.argv[1] + ' ' + loadedFileName;
        argLoaded = True
        #fileLoaded = True

    while (entered_key != 'q'):
        if (entered_key.isdecimal()):
            entered_key_int = int(entered_key)
            if (entered_key_int in range(len(parms_list))):
                mod_parm_loop(entered_key_int)
        else:
            entered_keys_list = entered_key.split()
            setting_handler(entered_keys_list)
                    
        os.system('clear');
        for i, parm in enumerate(parms_list):
            print(str(i) + ":", parm.name);
        print()
        print("O: TURN CRT ON")
        print()        
        print("A: APPLY CONIFG")
        print("R: TOGGLE HOT RELOAD", "ON" if hot_reload else "OFF")
        print("L {name}: LOAD CONFIG FROM A SEPERATE FILE")
        print("S {name}: SAVE CONFIG TO A SEPERATE FILE")

        if fileLoaded:
            print("W: SAVE LOADED FILE")
        print() 
        print("q: QUIT")
        entered_key = input("... ")


def mod_parm_loop(parm_number):
    """Run an interective configuration on parameter at parm_number."""
    parm_info = parms_list[parm_number]
    mod_key = '';

    while (mod_key != 'q'):
        os.system('clear')
        # print("Currently modifiying:")
        print(parm_number, '|', parm_info.name, '| MIN', parm_info.min_val, '| MAX', parm_info.max_val)
        print("CURRENT VALUE:", user_config[parm_info.name])
        mod_key = input("... ")
        mod_handler(parm_info, mod_key)
        if (hot_reload): apply_config()

def setting_handler(settings):
    """Enact the requested setting with an optional option."""
    global fileLoaded
    global loadedFileName
    #prevent index out of bounds error
    if len(settings) < 1:
        return
        
    if settings[0] == 'A':
        apply_config()
    elif settings[0] == 'O':
        turn_crt_on()
    elif settings[0] == 'R':
        global hot_reload
        hot_reload = not hot_reload
    elif settings[0] == 'L':
        if len(settings) < 2:
            print("MUST PASS {name} ARUGMENT")
            input()
        else:
            global user_config
            try:
                with open(settings[1], 'r') as load_file:
                    user_config = json.load(load_file)
                print("LOADED!")
                input()
            except FileNotFoundError:
                print("FILE NOT FOUND")
                input()
    elif settings[0] == 'S':
        if len(settings) < 2:
            print("MUST PASS {name} ARUGMENT")
            input()
        else:
            with open(settings[1], 'w') as save_file:
                save_file.write(json.dumps(user_config))
            print("SAVED!")
            input()
    
    elif settings[0] == 'E':
        try:
            with open(loadedFileName, 'r') as load_file:
                user_config = json.load(load_file)
                fileLoaded = True
                apply_config()

        except FileNotFoundError:
            sys.exit() 


    elif settings[0] == 'W':
        with open(loadedFileName, 'w') as save_file:
            save_file.write(json.dumps(user_config))
            print("File saved")
            input()


    elif settings[0] == 'I':
        if len(settings) < 2:
            sys.exit()
        else:
            try:
                with open(loadedFileName, 'r') as load_file:
                    user_config = json.load(load_file)
                    turn_crt_on()
                    apply_config()
                    sys.exit()
            except FileNotFoundError:
                sys.exit()            
def mod_handler(parm_info, mod):
    """
    Apply the modifier to the given parameter.

        Arguments:
            parm_info (class Parm): The paramter to be modified 
            modifier (string): The modifier to be applied to the user conifg
                paramter that corresponds to parm_info. 

        Returns:
            Nothing for now.
    """
    if mod == '+':
        user_config[parm_info.name] += 1
    elif mod == '-':
        user_config[parm_info.name] -= 1
    elif mod.isdecimal():
        mod_int = int(mod)
        if(mod_int >= parm_info.min_val and mod_int <= parm_info.max_val):
            user_config[parm_info.name] = mod_int
        else:
            print("VALUE OUT OF BOUNDS")
            input()

    apply_config()
if __name__ == "__main__":
    os.system('clear');
    main_loop()
