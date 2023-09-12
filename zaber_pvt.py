from zaber_motion import Units, Library, Measurement
from zaber_motion.ascii import Connection, AllAxes
from zaber_motion import *

import numpy as np
import pandas as pd


# Take xls table and make it into a PVT table
def table_to_df(filename='z_table.xlsx', NO_VELOCITY=True):
    # True=Let Zaber figure out what the velocities should be
    # False=Use computed vels from xls. But the sign is important, unlike in xls.

    df_zlut=pd.read_excel(filename)

    #idxs_subset=np.arange(0,len(df_zlut_full),step_size)
    #df_zlut=df_zlut_full.iloc[idxs_subset,:]

    # Times are a period, not absolute time
    # Assume they are equally spaced in time, and use the first one.
    df_zlut.iloc[:,0]=np.diff( df_zlut.iloc[:,0] )[0]

    # https://software.zaber.com/motion-library/docs/guides/pvt: 
    # Make the velocity of the last one zero: necessary, it seems !

    # Let Zaber figure out what the velocities should be
    if NO_VELOCITY:
        df_zlut.iloc[:,1]=None
        df_zlut.iloc[0,1]=0
        df_zlut.iloc[-1,1]=0 #len(df_zlut.index),"Velocity (mm/s)"]=0

        #df_zlut.iloc[df_zlut["Displacement(mm)"]==0,1]=0
    #print( df_zlut)
    return df_zlut

def df_to_pvt(device, df_zlut, npvt=1, nbuffer=1, ndims=3, ax1_sweep_lims=[0,10], ax3_sweep_lims=[10,0], step_size=5):
    pvt = device.get_pvt(npvt)
    pvt.disable()

    pvt_buffer = device.get_pvt_buffer(nbuffer)
    pvt_buffer.erase()

    NDIMS=ndims
    arr_axes=np.arange(NDIMS)+1
    # set up PVT to store points to PVT buffer 1 and
    # to use the first axis for unit conversion
    pvt.setup_store(pvt_buffer, *arr_axes )

    idxs=np.arange(0,len(df_zlut),step_size)
    # add PVT points from LUT in Excel file
    for index, row in df_zlut.iloc[idxs].iterrows():

        print( index, idxs[-1] )
        # Add each point in a loop
        if NDIMS==1:
            poses=[Measurement(row["Displacement(mm)"], Units.LENGTH_MILLIMETRES)]
        elif NDIMS==2:
            ax1_pos = ax1_sweep_lims[0] + (index+1)*(ax1_sweep_lims[1]-ax1_sweep_lims[0])/len(df_zlut)
            poses=[Measurement(ax1_pos, Units.LENGTH_MILLIMETRES),
                   Measurement(row["Displacement(mm)"], Units.LENGTH_MILLIMETRES)]
        else: # Assume 3
            ax1_pos = ax1_sweep_lims[0] + (index+1)*(ax1_sweep_lims[1]-ax1_sweep_lims[0])/len(df_zlut)
            ax3_pos = ax3_sweep_lims[0] + (index+1)*(ax3_sweep_lims[1]-ax3_sweep_lims[0])/len(df_zlut)
            poses=[Measurement(ax1_pos, Units.LENGTH_MILLIMETRES),
                   Measurement(row["Displacement(mm)"], Units.LENGTH_MILLIMETRES),
                   Measurement(ax3_pos, Units.LENGTH_MILLIMETRES) ];
            
        if (row["Velocity (mm/s)"] is None):
            vels=[None]*NDIMS
        else:
            value=row["Velocity (mm/s)"] if (index <= idxs[-1]) else [0]*NDIMS   # Make final vel 0
            vels=[Measurement(value, Units.VELOCITY_MILLIMETRES_PER_SECOND)]*NDIMS   
     
        # Toggle the DIO (first channel): at 0 will be 1, at 1 will be 0, at 2 will be 1, etc..
        # use +1 mod 2. TODO (this is pretty hacky and inflexible)
        pvt.set_digital_output(1,(index+1)%2)
        
        pvt.point(poses, vels , Measurement(row["Time(s)"], Units.TIME_SECONDS) )
        
        #time.sleep(0.01)
        if index==0:
            start_pos=[poses,vels, Measurement(2.0, Units.TIME_SECONDS) ] # Let it take x seconds to get to start pos

    pvt.set_digital_output(1,0)

    # finish writing to the buffer
    pvt.disable()
    
    # The table starts with the first move (last entry is final/start position)
    # Limits start start with first of pair 
    start_pos=[[Measurement(ax1_sweep_lims[0], Units.LENGTH_MILLIMETRES),
                   Measurement(df_zlut.iloc[-1]["Displacement(mm)"], Units.LENGTH_MILLIMETRES),
                   Measurement(ax3_sweep_lims[0], Units.LENGTH_MILLIMETRES) ],
                [None,None,None],
                Measurement(2.0, Units.TIME_SECONDS) ];
                
    return pvt_buffer,arr_axes,start_pos
    
class ZaberPVT:
    def __init__(self,port="COM4"):
        self.port=port
        
    def connect(self):
        Library.enable_device_db_store()
        connection=Connection.open_serial_port(self.port)  # confirm that this is the right serial port

        self.devices = connection.detect_devices()
        print("Found {} devices".format(len(self.devices)))
        
    def setup_zlut(self):
        df_zlut=table_to_df()
        self.pvt_buffer,self.arr_pvt_axes,self.start_pos=df_to_pvt(self.devices[0],df_zlut)
        
        # for execution:
        self.live_pvt = self.devices[0].get_pvt(2)
        self.live_pvt.disable()
        self.live_pvt.setup_live(*self.arr_pvt_axes) # Execute on axis Z
        
    def execute_pvt(self):
        self.live_pvt.call( self.pvt_buffer)
        
    def home3(self):
        self.devices[0].all_axes.home()
        self.devices[2].all_axes.home()
        
    def move3(self, amt_deg=45):
        self.live_pvt.call(self.pvt_buffer)
        self.devices[2].get_axis(1).move_absolute(amt_deg, Units.ANGLE_DEGREES,
                                          velocity=amt_deg/3.0, velocity_unit=Units.ANGULAR_VELOCITY_DEGREES_PER_SECOND,
                                          wait_until_idle=False)    
        

    
    
	