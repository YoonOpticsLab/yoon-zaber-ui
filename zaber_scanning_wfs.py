from tkinter import *
from tkinter import ttk
from functools import partial
import numpy as np
from zaber_motion import Units, Library, Measurement
from zaber_motion.ascii import Connection, AllAxes
import xml.etree.ElementTree as ET

import zaber_pvt # UHCO wrapper

import camera_window

### Config/settings
SETTINGS={}

MOVE_TIME_S=1.0

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

# Amount the buttons move, in cm or degrees
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
    #sweep_time=str_sweep_time.get()

    #if not(cam0 is None):
    cam0.start_sweep("TEST");
    #if not(cam1 is None):
    #    cam1.start_sweep("TEST");

    #str_filename
    if arg==0:
        val=-int( str_H.get()  )
        zpvt.sweep3(val)
    elif arg==1:
        val=-int( str_V.get()  )
        zpvt.sweep3v(val*2)

def DEG2RAD(angl):
    return angl/180.0*np.pi

def do_pos(arg,event):
    which_sweep=arg[0]
    which_pos=arg[1]

    if which_sweep==0 and which_pos==1:
        for nmotor in [0,1,2]:
            val=int( str_entries1[nmotor].get() )
            val_meas=Measurement(value=val, unit=Units.LENGTH_MILLIMETRES)

            motors[nmotor].move_absolute( val, Units.LENGTH_MILLIMETRES, wait_until_idle=False,
                velocity=val/MOVE_TIME_S, velocity_unit=Units.VELOCITY_MILLIMETRES_PER_SECOND)

        try:
            pos3=int(str_entries1[3].get())
            motors[3].move_absolute(pos3, Units.ANGLE_DEGREES, wait_until_idle=False,
                                          velocity=20/2.0, velocity_unit=Units.ANGULAR_VELOCITY_DEGREES_PER_SECOND)
        except:
            pass

        try:
            pos4=int(str_entries1[4].get())
            motors[4].move_absolute(pos4, Units.ANGLE_DEGREES, wait_until_idle=False,
                                          velocity=20/2.0, velocity_unit=Units.ANGULAR_VELOCITY_DEGREES_PER_SECOND)
        except:
            pass

    if which_sweep==0 and which_pos==0:
        angle=int( str_H.get()  )
        mid3=motors[2].get_position("mm")
        mid1=motors[0].get_position("mm") # Remain at same position

        mult=float(SETTINGS['horiz_sweep_mult']))
        move_mm=np.sin(angle/180.0 * np.pi) * mult
        print( move_mm)

        zpvt.setup_zlut([mid1,mid1],[mid3-move_mm,mid3+move_mm],
            duration_sec=float(SETTINGS['horiz_sweep_dur']),
            npts=int(SETTINGS['horiz_sweep_npts']),
                        mult=mult)
        zpvt.to_start3(angle)
        
    if which_sweep==1 and which_pos==0:
        angle=int( str_V.get()  )
        mid3=motors[2].get_position("mm") # remain
        mid1=motors[0].get_position("mm")

        mult=float(SETTINGS['horiz_sweep_mult']))
        move_mm=np.sin(angle/180.0 * np.pi) * mult
        print( move_mm)

        zpvt.setup_zlut([mid1-move_mm,mid1+move_mm],[mid3,mid3],
            duration_sec=float(SETTINGS['horiz_sweep_dur']),
            npts=int(SETTINGS['horiz_sweep_npts']),
            mult=mult)
        zpvt.to_start3v(angle)
        

# Zaber Motor Commands
def connect(port="COM4"):
    global motors, device_list
    global zpvt

    if True: #New way
        zpvt=zaber_pvt.ZaberPVT(port)
        zpvt.connect()

        device_list=zpvt.devices
 
    if len(device_list)>1:
        motors=[device_list[0].get_axis(1),
                device_list[0].get_axis(2),
                device_list[0].get_axis(3),
                device_list[1].get_axis(1),
                device_list[2].get_axis(1)]
    else:
        motors=[device_list[0].get_axis(1),
                device_list[0].get_axis(2),
                device_list[0].get_axis(3), None, None]

    l_status.configure(text="OK!")

def connected():
    if motors[0]=="0":
        print("Not connected")
        return False
    else:
        return True

def setup_sweep():
    zpvt.setup_zlut(
        [float(str_H.get()),float(str_H.get() )],
        [float(str_V.get()),float(str_V.get() )] )

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

# Main code starts here
SETTINGS=read_config() # Read settings from XML file

root = Tk()
root.title('Zaber - Simple UI')
root.geometry('900x350')
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

# Numerical tables (populated from XML) for sweep pos's
#str_entries0=[StringVar() for n in range(5)]
str_entries1=[StringVar() for n in range(5)]
#str_entries2=[StringVar() for n in range(5)]
#entries0 = [ttk.Entry(f, width=7, textvariable=s) for n,s in enumerate(str_entries0)]
entries1 = [ttk.Entry(f, width=7, textvariable=s) for n,s in enumerate(str_entries1)]
#entries2 = [ttk.Entry(f, width=7, textvariable=s) for n,s in enumerate(str_entries2)]

enables = [BooleanVar(f,True) for n in range(5)]

widget_enables = [Checkbutton(f, variable=enables[n]) for n,s in enumerate(str_entries1)]

l_0 = ttk.Label(f, text="0 (abs)"); l_0.grid(row=0, column=7, padx=5, pady=5)

# Horizontal scan values:
for n in range(5):
    entries1[n].grid(row=n+1,column=7,padx=5,pady=5)
    widget_enables[n].grid(row=n+1,column=8,padx=5,pady=5)

    sets=SETTINGS['pos%d_horiz'%(n+1)]
    vals=sets.split(',')
    str_entries1[n].set(vals[1])


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

b_middle = ttk.Button(f, text="Middle")
b_middle.grid(row=6, column=7, padx=5, pady=5)
b_middle.bind('<ButtonPress-1>',partial(do_pos,[0,1]) )

b_h_s = ttk.Button(f, text="H Start")
b_h_s.grid(row=7, column=6, padx=5, pady=5)
b_h_s.bind('<ButtonPress-1>',partial(do_pos,[0,0]) )

b_h_sw = ttk.Button(f, text="H Sweep")
b_h_sw.grid(row=7, column=8, padx=5, pady=5)
b_h_sw.bind('<ButtonPress-1>',partial(do_sweep,0) )

b_v_s = ttk.Button(f, text="V Start")
b_v_s.grid(row=8, column=6, padx=5, pady=5)
b_v_s.bind('<ButtonPress-1>',partial(do_pos,[1,0]) )

b_v_sw = ttk.Button(f, text="V Sweep")
b_v_sw.grid(row=8, column=8, padx=5, pady=5)
b_v_sw.bind('<ButtonPress-1>',partial(do_sweep,1) )

str_H=StringVar()
str_V=StringVar()
entryH = ttk.Entry(f, width=7, textvariable=str_H)
entryH.grid(row=7,column=4,padx=5,pady=5)
entryV = ttk.Entry(f, width=7, textvariable=str_V)
entryV.grid(row=8,column=5,padx=5,pady=5)
lblH = ttk.Label(f, text="Horizontal:"); lblH.grid(row=6,column=4)
lblV = ttk.Label(f, text="Vertical:"); lblV.grid(row=6,column=5)
#entries1[n].grid(row=n+1,column=7,padx=5,pady=5)
#entries2[n].grid(row=n+1,column=8,padx=5,pady=5)

str_filename=StringVar(); #"Enter Subject ID");
str_filename.set("TEST")
e_sweep_filename = ttk.Entry(f, textvariable=str_filename); e_sweep_filename.grid(row=7, column=0, padx=5, pady=5)

set_start_H=SETTINGS['horiz_sweep_start']
str_H.set(set_start_H)
set_start_V=SETTINGS['vert_sweep_start']
str_V.set(set_start_V)
#str_entries0[n].set(vals[0])
#vals=sets.split(',')
#str_entries1[n].set(vals[1])

# TODO/tmp
root.settings=SETTINGS
if int(SETTINGS['camera_preview'])>0:
    cam0=camera_window.open_window(root,0)
    cam1=camera_window.open_window(root,1)

if not(SETTINGS['autoconnect'] is None) and not (SETTINGS['autoconnect']=="None"):
    root.after(100, partial(connect,SETTINGS['autoconnect']) )

root.mainloop()

if not(cam0 is None):
    cam0.stop()
if not(cam1 is None):
    cam1.stop()
