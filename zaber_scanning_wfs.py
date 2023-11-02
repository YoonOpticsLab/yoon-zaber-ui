from tkinter import *
from tkinter import ttk
from functools import partial
import numpy as np
from zaber_motion import Units, Library, Measurement
from zaber_motion.ascii import Connection, AllAxes
import xml.etree.ElementTree as ET

import zaber_pvt # UHCO wrapper

### Config/settings
SETTINGS={}

def read_config(fname='./config.xml'):
    settings={}
    tree=ET.parse(fname)

    for child in tree.getroot(): # Assume root is "settings"
        print( child.tag, child.text )
        settings[child.tag]=child.text
    return settings

def write_config(settings, fname='./config.xml'):
    tree = ET.Element('settings')
    for key,val in settings.items():
        child=ET.Element(key)
        child.text=str(val)
        tree.append(child)
    ET.indent(tree, '    ')
    ET.ElementTree(tree).write(fname,encoding='utf-8',xml_declaration=True)


motors=["0","1","2","3","3"]
nx,ny,nz,r1,r2=[0,1,2,3,4]
poses=np.zeros(5,dtype='int')

nudge_amount= [
    [1,10],
    [1,10],
    [1,10],
    [1,10],
    [1,10],
];

# Set the current position. Is either a 0 or a relative amt.
def set_val(n,val,is_relative=True):
    # If val==0, home operation, else add to current
    global poses
    if (val==0):
        poses[n]=0
    else:
        poses[n] += val
    pos_strings[n].set(poses[n])

# Interface
def do_home(arg,event):
    set_val(arg,0)
    motor_home(arg)

    if arg==2:
        sinMove1 = device_list[0].prepare_command("pvt 1 setup live 3")
        device_list[0].generic_command( sinMove1 );
        print ("Set live")

def do_home_all():
    for n in range(5):
        if enables[n].get():
            do_home(n,0)

def do_move(arg,event):
    nmotor=arg[0]
    amt=arg[1]*nudge_amount[nmotor][arg[2]]
    #print(  nmotor, arg[1] )
    move_motor_relative(nmotor,amt)
    set_val(nmotor,amt)

def do_start(arg,event):
    sweep_time=str_sweep_time.get()
    if arg==0:
        sweep1()

def do_sweep(arg,event):
    sweep_time=str_sweep_time.get()
    if arg==0:
        sweep1()

def DEG2RAD(angl):
    return angl/180.0*np.pi
    
def do_pos(arg,event):
    which_sweep=arg[0]
    which_sweep_str=["horizontal","vertical","diagonal"][which_sweep]

    which_pos=arg[1]
    which_pos_str=["middle","start"][which_pos]
    for nmotor,motor1 in enumerate(motors):
        limit1=int( motor1.settings.get("limit.max") )
        frac=float( SETTINGS["pos_%s_%s%d"%(which_pos_str,which_sweep_str,nmotor+1)] )
        print (nmotor, limit1, frac )
        if which_pos==0:
            motor1.move_absolute(limit1 * frac, wait_until_idle=False)
        elif which_pos==1:
            if nmotor==1:
                desired=(1-np.cos(DEG2RAD(float(SETTINGS["min_angle_horizontal"])))) * float(SETTINGS["mult_horizontal"])
                print(desired)
                move_motor_relative(nmotor, desired )
            else:
                move_motor_relative(nmotor, frac )
        
# Zaber Motor Commands
def connect(port="COM4"):
    global motors, device_list
    global zpvt

    if True: #New way
        zpvt=zaber_pvt.ZaberPVT()
        zpvt.connect()

        device_list=zpvt.devices
    else:

        Library.enable_device_db_store()
        connection=Connection.open_serial_port(port)  # confirm that this is the right serial port

        device_list = connection.detect_devices()
        print("Found {} devices".format(len(device_list)))
 
    device1 = device_list[0]  # device1 is the X-MCC

    LSQx = device1.get_axis(1)  # "LSQx" refers to your first LSQ
    LSQy = device1.get_axis(2)  # "LSQy" refers to your second LSQ
    LSQz = device1.get_axis(3)  # "LSQz" refers to your third LSQ

    if len(device_list)>1:
        device2 = device_list[1]  # device1 is the X-MCC
        RSW1 = device2.get_axis(1)

        device3 = device_list[2]  # device1 is the X-MCC
        RSW2 = device3.get_axis(1)
    else:
        RSW1 = None
        RSW2 = None

    motors=[LSQx, LSQy, LSQz, RSW1, RSW2]
    l_status.configure(text="OK!")

def connected():
    if motors[0]=="0":
        print("Not connected")
        return False
    else:
        return True

def setup_sweep():
    zpvt.setup_zlut(
        [float(str_entries0[0].get()),float(str_entries1[0].get() )],
        [float(str_entries0[2].get()),float(str_entries1[2].get() )] )

def sweep1():
    if connected()==False:
        return 

    zpvt.execute_pvt() # EXecute PVT array on first driver (3 linear axes)
    return
    
    sweep_time=float(str_sweep_time.get() )
    vals=[float(str1.get()) for str1 in str_entries1]
    print( vals[0], vals[1], vals[0]*1.0 )
    # sinMove1 = motors[2].prepare_command("move sin ? ? ?", # Amp period count
                                        # Measurement(value=vals[2], unit=Units.LENGTH_MILLIMETRES),
                                        # Measurement(value=sweep_time,  unit=Units.TIME_SECONDS),
                                        # Measurement(value=1)
                                        # )
    sinMove1 = device_list[0].prepare_command("pvt 1 call 1")

    motors[0].move_absolute(
        Measurement(value=vals[0], unit=Units.LENGTH_MILLIMETRES), Units.LENGTH_MILLIMETRES, wait_until_idle=False,
            velocity=abs(vals[0])/sweep_time, velocity_unit=Units.VELOCITY_MILLIMETRES_PER_SECOND)
    motors[1].move_absolute( 
        Measurement(value=vals[1], unit=Units.LENGTH_MILLIMETRES), Units.LENGTH_MILLIMETRES, wait_until_idle=False,
            velocity=abs(vals[1])/sweep_time, velocity_unit=Units.VELOCITY_MILLIMETRES_PER_SECOND)
    if vals[2] > 0:
        #sinMove1 = device_list[0].prepare_command("pvt 1 setup live 3")
        #device_list[0].generic_command( sinMove1 );
        sinMove1 = device_list[0].prepare_command("pvt 1 call 1")
        device_list[0].generic_command( sinMove1 );
    if not(vals[3] == 0):
        motors[3].move_relative( vals[3], Units.ANGLE_DEGREES, wait_until_idle=False );
    if not(vals[4] == 0):
        motors[4].move_relative( vals[4], Units.ANGLE_DEGREES, wait_until_idle=False );
    ##motors[4].move_absolute( vals[4], Units.ANGLE_DEGREES, wait_until_idle=False );

    for nmotor in range(5):
        set_val(nmotor,vals[nmotor],False) # set new absolute positions

def move_motor(nmotor):
    if connected():
        val=poses[nmotor]
        if nmotor<3:
            # Linear motors
            motors[nmotor].move_absolute(val, Units.LENGTH_MILLIMETRES,wait_until_idle=False)
        else:
            motors[nmotor].move_absolute(val, Units.ANGLE_DEGREES,wait_until_idle=False)

def move_motor_relative(nmotor,amt):
    if connected():
        val=amt #poses[nmotor]
        if nmotor<3:
            # Linear motors
            motors[nmotor].move_relative(val, Units.LENGTH_MILLIMETRES,wait_until_idle=False)
        else:
            motors[nmotor].move_relative(val, Units.ANGLE_DEGREES,wait_until_idle=False)

def motor_home(nmotor):
    if connected():
        motors[nmotor].home(wait_until_idle = True)

root = Tk()
root.title('Zaber - Simple UI')
root.geometry('900x400')
f = ttk.Frame(root, width=512); f.grid()

b_connect = ttk.Button(f, text="Connect", command=connect); b_connect.grid(row=0, column=0, padx=5, pady=5)

l_status = ttk.Label(f, text='NOT CONNECTED'); l_status.grid(row=0, column=1)

pos_strings=[StringVar() for n in range(5)]

# Movements:
b_homes = [ttk.Button(f, text="Home%d"%(nmotor+1)) for nmotor in range(5)];
b_m_big = [ttk.Button(f, text="--") for nmotor in range(5)];
b_m_small = [ttk.Button(f, text="-") for nmotor in range(5)];
b_p_big = [ttk.Button(f, text="++") for nmotor in range(5)];
b_p_small = [ttk.Button(f, text="+") for nmotor in range(5)];

# Homes
for nb,b1 in enumerate(b_homes):
    b1.grid(row=nb+1, column=0, padx=5, pady=5)
    b1.bind('<ButtonPress-1>',partial(do_home,nb) )

b_home_all= ttk.Button(f, text="Home ALL",command=do_home_all)
b_home_all.grid(row=6, column=0, padx=5, pady=5)

# Relative moves
for nb,b1 in enumerate(b_m_big):
    b1.grid(row=nb+1, column=1, padx=5, pady=5)
    b1.bind('<ButtonPress-1>',partial(do_move,(nb,-1,1) ) )
for nb,b1 in enumerate(b_m_small):
    b1.grid(row=nb+1, column=2, padx=5, pady=5)
    b1.bind('<ButtonPress-1>',partial(do_move,(nb,-1, 0) ) )
for nb,b1 in enumerate(b_p_small):
    b1.grid(row=nb+1, column=4, padx=5, pady=5)
    b1.bind('<ButtonPress-1>',partial(do_move,(nb,+1, 0) ) )
for nb,b1 in enumerate(b_p_big):
    b1.grid(row=nb+1, column=5, padx=5, pady=5)
    
    b1.bind('<ButtonPress-1>',partial(do_move,(nb,+1, 1) ) )
l_pos = [ttk.Label(f, textvariable=pos_strings[nmotor]) for nmotor in range(5)];
for nb,l1 in enumerate(l_pos):
    pos_strings[nb].set('? %d'%(nb+1))
    l1.grid(row=nb+1, column=3, padx=5, pady=5)

str_entries0=[StringVar() for n in range(5)]
str_entries1=[StringVar() for n in range(5)]
str_entries2=[StringVar() for n in range(5)]
entries0 = [ttk.Entry(f, width=7, textvariable=s) for n,s in enumerate(str_entries0)]
entries1 = [ttk.Entry(f, width=7, textvariable=s) for n,s in enumerate(str_entries1)]
entries2 = [ttk.Entry(f, width=7, textvariable=s) for n,s in enumerate(str_entries2)]

enables = [BooleanVar(f,True) for n in range(5)]
enables[3].set(False)
widget_enables = [Checkbutton(f, variable=enables[n]) for n,s in enumerate(str_entries2)]

for n in range(5):
    entries0[n].grid(row=n+1,column=6,padx=5,pady=5)
    entries1[n].grid(row=n+1,column=7,padx=5,pady=5)
    entries2[n].grid(row=n+1,column=8,padx=5,pady=5)
    str_entries0[n].set('2')
    str_entries1[n].set('10')
    str_entries2[n].set('')

    widget_enables[n].grid(row=n+1,column=10)

if 0:
    # Sweep buttons
    b_start = ttk.Button(f, text="ToStart")
    b_start.grid(row=0, column=6, padx=5, pady=5)
    b_start.bind('<ButtonPress-1>',partial(do_start,0) )

    # Sweep buttons
    b_sweep1 = ttk.Button(f, text="SweepTo1")
    b_sweep1.grid(row=0, column=7, padx=5, pady=5)
    b_sweep1.bind('<ButtonPress-1>',partial(do_sweep,0) )

    # Sweep time
    str_sweep_time=StringVar()
    str_sweep_time.set("3")
    time_entry = ttk.Entry(f, width=7, textvariable=str_sweep_time)
    time_entry.grid(row=8, column=6, padx=5, pady=5)
    lblTime = ttk.Label(f, text="Time (s):")
    lblTime.grid(row=8,column=5,padx=5,pady=5)

    strUnits=['mm','mm','mm (sin)','deg (sin)','deg']
    l_units=[ttk.Label(f,text=txt,anchor="w",justify=LEFT) for n,txt in enumerate(strUnits)]
    for n,l in enumerate(l_units):
        l.grid(row=n+1,column=9)

    b_start = ttk.Button(f, text="Setup Sweep", command=setup_sweep)
    b_start.grid(row=0, column=10, padx=5, pady=5)

b_h_m = ttk.Button(f, text="Horiz Middle")
b_h_m.grid(row=8, column=3, padx=5, pady=5)
b_h_m.bind('<ButtonPress-1>',partial(do_pos,[0,0]) )

b_h_s = ttk.Button(f, text="Horiz Start")
b_h_s.grid(row=8, column=1, padx=5, pady=5)
b_h_s.bind('<ButtonPress-1>',partial(do_pos,[0,1]) )

b_h_sw = ttk.Button(f, text="Horiz Sweep")
b_h_sw.grid(row=8, column=5, padx=5, pady=5)
b_h_sw.bind('<ButtonPress-1>',partial(do_sweep,0) )

SETTINGS=read_config()

if not(SETTINGS['autoconnect'] is None) and not (SETTINGS['autoconnect']=="None"):
    root.after(100, partial(connect,SETTINGS['autoconnect']) )

root.mainloop()
