from tkinter import *
from tkinter import ttk
from zaber_motion import Units, Library, Measurement
from zaber_motion.ascii import Connection, AllAxes
 
def home1():
    global connection,LSQx,LSQz,LSQz,device1,device2,device3,RSW1,RSW2
    device1.all_axes.home();
def home2():
    global connection,LSQx,LSQz,LSQz,device1,device2,device3,RSW1,RSW2
    device1.all_axes.home();
def home3():
    global connection,LSQx,LSQz,LSQz,device1,device2,device3,RSW1,RSW2
    device1.all_axes.home();
def home4():
    global connection,LSQx,LSQz,LSQz,device1,device2,device3,RSW1,RSW2
    device4.home();
def home5():
    global connection,LSQx,LSQz,LSQz,device1,device2,device3,RSW1,RSW2
    device5.home();

def connect():
    global connection,LSQx,LSQy,LSQz,device1,device2,device3,RSW1,RSW2

    Library.enable_device_db_store()
    connection=Connection.open_serial_port("COM4")  # confirm that this is the right serial port

    device_list = connection.detect_devices()
    print("Found {} devices".format(len(device_list)))
 
    device1 = device_list[0]  # device1 is the X-MCC
    LSQx = device1.get_axis(1)  # "LSQx" refers to your first LSQ
    LSQy = device1.get_axis(2)  # "LSQy" refers to your second LSQ
    LSQz = device1.get_axis(3)  # "LSQz" refers to your third LSQ

    device2 = device_list[1]  # device1 is the X-MCC
    RSW1 = device2.get_axis(1)

    device3 = device_list[2]  # device1 is the X-MCC
    RSW2 = device2.get_axis(1)
 
    speed=LSQx.settings.get("maxspeed",Units.VELOCITY_MILLIMETRES_PER_SECOND)
    print(speed)
    
    if False:
        #device2 = device_list[1]
        #RSW1 = device2.get_axis(1)
     
        #device3 = device_list[2]
        #SRSW2 = device3.get_axis(1)
     
        # define sinusoidal moves to be used later (amplitude, period, # of cycles)
     
        sinMove1 = RSW1.prepare_command("move sin ? ? ?",
                                        Measurement(value=25, unit=Units.ANGLE_DEGREES),
                                        Measurement(value=3,  unit=Units.TIME_SECONDS),
                                        Measurement(value=1)
                                        )
     
        sinMove2 = LSQx.prepare_command("move sin ? ? ?",
                                        Measurement(value=10, unit=Units.LENGTH_MILLIMETRES),
                                        Measurement(value=3,  unit=Units.TIME_SECONDS),
                                        Measurement(value=1)
                                        )
     
 
def move1():

		# move LSQ stages to the (20 mm, 50 mm, 70 mm)
		#LSQx.move_absolute(20, Units.c)
		#LSQy.move_absolute(50, Units.LENGTH_MILLIMETRES)
		#LSQz.move_absolute(70, Units.LENGTH_MILLIMETRES)

		# move rsw stages sinusoidally

		#RSW1.generic_command(sinMove1)
		#RSW2.generic_command(sinMove2)
        
        #Experiment, try siniousoidal on xrange
        LSQx.generic_command(sinMove2)
			
def sweep1():
    global connection,LSQx,LSQy,LSQz,device1,device2,device3,RSW1,RSW2
     
    sweep_time=3 
    sinMove1 = LSQz.prepare_command("move sin ? ? ?",
                                        Measurement(value=25, unit=Units.LENGTH_MILLIMETRES),
                                        Measurement(value=sweep_time,  unit=Units.TIME_SECONDS),
                                        Measurement(value=1)
                                        )
     
    sinMove2 = RSW1.prepare_command("move sin ? ? ?",
                                        Measurement(value=90, unit=Units.ANGLE_DEGREES),
                                        Measurement(value=sweep_time,  unit=Units.TIME_SECONDS),
                                        Measurement(value=1)
                                        )
     
    LSQy.move_absolute(50, Units.LENGTH_MILLIMETRES, wait_until_idle=False,
            velocity=50/sweep_time, velocity_unit=Units.VELOCITY_MILLIMETRES_PER_SECOND)
    LSQx.move_absolute(50, Units.LENGTH_MILLIMETRES, wait_until_idle=False,
            velocity=50/sweep_time, velocity_unit=Units.VELOCITY_MILLIMETRES_PER_SECOND)
    LSQz.generic_command( sinMove1 );
    RSW1.generic_command(sinMove2);
    RSW2.move_absolute( 90, Units.ANGLE_DEGREES, wait_until_idle=False );

def sweep2():
    global connection,LSQx,LSQz,LSQz,device1,device2,device3,RSW1,RSW2
    LSQx.move_absolute(100, Units.LENGTH_MILLIMETRES, velocity=100/10.0, velocity_unit=Units.VELOCITY_MILLIMETRES_PER_SECOND);
    #SQx.generic_command(sinMove2)
		 	
root = Tk()
root.title('Zaber - Simple UI')
root.geometry('256x256')
f = ttk.Frame(root, width=512); f.grid()

b_connect = ttk.Button(f, text="connect", command=connect); b_connect.grid(row=0, column=0, padx=5, pady=5)
b_home1 = ttk.Button(f, text="Home1", command=home1); b_home1.grid(row=1, column=0, padx=5, pady=5)
b_home2 = ttk.Button(f, text="Home2", command=home2); b_home2.grid(row=2, column=0, padx=5, pady=5)
b_home3 = ttk.Button(f, text="Home3", command=home3); b_home3.grid(row=3, column=0, padx=5, pady=5)
b_home4 = ttk.Button(f, text="Home4", command=home4); b_home4.grid(row=4, column=0, padx=5, pady=5)
b_home5 = ttk.Button(f, text="Home5", command=home5); b_home5.grid(row=5, column=0, padx=5, pady=5)

b_sweep1 = ttk.Button(f, text="Sweep1", command=sweep1); b_sweep1.grid(row=1, column=3, padx=5, pady=5)
b_sweep2 = ttk.Button(f, text="Sweep2", command=sweep2); b_sweep2.grid(row=2, column=3, padx=5, pady=5)

root.mainloop()
