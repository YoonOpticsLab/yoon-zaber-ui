from zaber_motion import Units, Library, Measurement
from zaber_motion.ascii import Connection, AllAxes
from tkinter import *
from tkinter import ttk
 
Library.enable_device_db_store()
 
connection=Connection.open_serial_port("COM4")  # confirm that this is the right serial port
if True:
    device_list = connection.detect_devices()
    print("Found {} devices".format(len(device_list)))
 
    device1 = device_list[0]  # device1 is the X-MCC
    LSQx = device1.get_axis(1)  # "LSQx" refers to your first LSQ
    #LSQy = device1.get_axis(2)  # "LSQy" refers to your second LSQ
    LSQz = device1.get_axis(3)  # "LSQz" refers to your third LSQ
 
    if False:
        #device2 = device_list[1]
        #RSW1 = device2.get_axis(1)
     
        #device3 = device_list[2]
        #SRSW2 = device3.get_axis(1)
     
        # define sinusoidal moves to be used later (amplitude, period, # of cycles)
     
        sinMove1 = RSW1.prepare_command("move sin ? ? ?",
                                        Measurement(value=25, unit=Units.ANGLE_DEGREES),
                                        Measurement(value=2,  unit=Units.TIME_SECONDS),
                                        Measurement(value=1)
                                        )
     
    sinMove2 = LSQx.prepare_command("move sin ? ? ?",
                                        Measurement(value=10, unit=Units.LENGTH_MILLIMETRES),
                                        Measurement(value=1,  unit=Units.TIME_SECONDS),
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
			
			
root = Tk()
root.title('Zaber - Simple UI')
root.geometry('256x256')
f = ttk.Frame(root, width=512); f.grid()

b_move1 = ttk.Button(f, text="Send move1 commands", command=move1); b_move1.grid(row=0, column=0, padx=5, pady=5)

root.mainloop()
