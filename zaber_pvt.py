from zaber_motion import Units, Library, Measurement
from zaber_motion.ascii import Connection, AllAxes
from zaber_motion import *

import numpy as np
import pandas as pd


DEVICE_ROT_MIRROR=1
DEVICE_ROT_PLATFORM=2

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
    
    npoint=0
    # add PVT points from LUT in Excel file
    for index, row in df_zlut.iloc[idxs].iterrows():

        #print( index, idxs[-1], len(df_zlut), index==idxs[-1] )
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

        if ( row["Velocity (mm/s)"] is None) and (index<idxs[-1]):
            vels=[None]*NDIMS
        else:
            # TODO: This is suspicious singleton vs. list
            value=row["Velocity (mm/s)"] if (index < idxs[-1]) else 0   # Make final vel 0
            vels=[Measurement(value, Units.VELOCITY_MILLIMETRES_PER_SECOND)]*NDIMS   

        # Toggle the DIO (first channel): at 0 will be 1, at 1 will be 0, at 2 will be 1, etc..
        # use +1 mod 2. TODO (this is pretty hacky and inflexible)
        # pvt.set_digital_output(1,(index+1)%2)

        pvt.point(poses, vels , Measurement(row["Time(s)"], Units.TIME_SECONDS) )

        if index==0:
            start_pos=[poses,vels, Measurement(2.0, Units.TIME_SECONDS) ] # Let it take x seconds to get to start pos
            
        npoint += 1 # Can't use "index" in loop since it may skip points

    # pvt.set_digital_output(1,0)

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

def DEG2RAD(angl):
    return angl/180.0 * np.pi
    
# Build the PVT table algorithmic ally based on the specified parameters    
def cos_to_pvt(device, npts=51, npvt=1, nbuffer=1, ndims=3,
        ax1_sweep_lims=[0,10], ax3_sweep_lims=[10,0], bounds=[-40,40],
        mult=0,duration_sec=3.0):
    pvt = device.get_pvt(npvt)
    pvt.disable()

    pvt_buffer = device.get_pvt_buffer(nbuffer)
    pvt_buffer.erase()

    NDIMS=ndims
    arr_axes=np.arange(NDIMS)+1
    # set up PVT to store points to PVT buffer 1 and
    # to use the first axis for unit conversion
    pvt.setup_store(pvt_buffer, *arr_axes )

    idxs=np.arange(npts)
    
    npoint=0
    # add PVT points from LUT in Excel file
    for nidx,index in enumerate(idxs):

        val=(1-np.cos( (DEG2RAD((bounds[1]-bounds[0])/(npts-1)*(index) + bounds[0] )))) * mult
        #print( val )
        # Add each point in a loop
        if NDIMS==1:
            poses=[Measurement(val, Units.LENGTH_MILLIMETRES)]
        elif NDIMS==2:
            ax1_pos = ax1_sweep_lims[0] + (index+1)*(ax1_sweep_lims[1]-ax1_sweep_lims[0])/npts
            poses=[Measurement(ax1_pos, Units.LENGTH_MILLIMETRES),
                   Measurement(val, Units.LENGTH_MILLIMETRES)]
        else: # Assume 3
            ax1_pos = ax1_sweep_lims[0] + (index)*(ax1_sweep_lims[1]-ax1_sweep_lims[0])/(npts-1)
            ax3_pos = ax3_sweep_lims[0] + (index)*(ax3_sweep_lims[1]-ax3_sweep_lims[0])/(npts-1)
            poses = [ax1_pos, val, ax3_pos]
            poses_meas=[Measurement(pos1, Units.LENGTH_MILLIMETRES) for pos1 in poses]

        #if ( row["Velocity (mm/s)"] is None) and (index<idxs[-1]):
        if nidx==0:
            vels=[Measurement(0, Units.VELOCITY_MILLIMETRES_PER_SECOND)]*NDIMS
            poses0=poses # Save position_0 to get velocity later
        elif nidx==1:
            # Compute first velocity as diff between start position and first sweep pos
            diffs=[ax1_pos-poses0[0],val-poses0[1],ax3_pos-poses0[2]]
            vels=[Measurement(d1/(duration_sec/(npts-1)),Units.VELOCITY_MILLIMETRES_PER_SECOND) for d1 in diffs]
        elif index==idxs[-1]:
            vels=[Measurement(0, Units.VELOCITY_MILLIMETRES_PER_SECOND)]*NDIMS  
        else:
            vels=[None]*NDIMS
        #else:
        #    # TODO: This is suspicious singleton vs. list
        #    value=row["Velocity (mm/s)"] if (index < idxs[-1]) else 0   # Make final vel 0
        #    vels=[Measurement(value, Units.VELOCITY_MILLIMETRES_PER_SECOND)]*NDIMS   

        # Toggle the DIO (first channel): at 0 will be 1, at 1 will be 0, at 2 will be 1, etc..
        # use +1 mod 2. TODO (this is pretty hacky and inflexible)
        pvt.set_digital_output(1,(index+1)%2)

        # Don't add first point to PVT path. Instead note it as start pos
        if index==0:
            vels0=[Measurement(0, Units.VELOCITY_MILLIMETRES_PER_SECOND)]*NDIMS  
            start_pos=[poses_meas,vels0, Measurement(5.0, Units.TIME_SECONDS) ] # Let it take x seconds to get to start pos
        else:
            pvt.point(poses_meas, vels, Measurement(duration_sec/(npts-1), Units.TIME_SECONDS) ) # TODO: Entire duration
            
            
        npoint += 1 # Can't use "index" in loop since it may skip points

    pvt.set_digital_output(1,0)

    # finish writing to the buffer
    pvt.disable()

    # The table starts with the first move (last entry is final/start position)
    # Limits start start with first of pair 
    #start_pos=[[Measurement(ax1_sweep_lims[0], Units.LENGTH_MILLIMETRES),
    #               Measurement(df_zlut.iloc[-1]["Displacement(mm)"], Units.LENGTH_MILLIMETRES),
    #               Measurement(ax3_sweep_lims[0], Units.LENGTH_MILLIMETRES) ],
    #            [None,None,None],
    #            Measurement(2.0, Units.TIME_SECONDS) ];

    return pvt_buffer,arr_axes,start_pos


class ZaberPVT:
    def __init__(self,port="COM4"):
        self.port=port

    def connect(self):
        Library.enable_device_db_store()
        connection=Connection.open_serial_port(self.port)  # confirm that this is the right serial port

        self.devices = connection.detect_devices()
        print("Found {} devices".format(len(self.devices)))

        #self.setup_zlut([0,10],[10,0])

    def setup_zlut(self,ax1_lims,ax3_lims,step_size=5,duration_sec=3,npts=51,mult=1):
        df_zlut=table_to_df() # Probably don't need anymore
        #self.pvt_buffer,self.arr_pvt_axes,self.start_pos=df_to_pvt(self.devices[0],df_zlut,
        #    ax1_sweep_lims=ax1_lims, ax3_sweep_lims=ax3_lims, step_size=step_size)
        self.pvt_buffer,self.arr_pvt_axes,self.start_pos=cos_to_pvt(self.devices[0],npts,
            ax1_sweep_lims=ax1_lims, ax3_sweep_lims=ax3_lims, duration_sec=duration_sec,mult=mult)

        # for execution:
        self.live_pvt = self.devices[0].get_pvt(2)
        self.live_pvt.disable()
        self.live_pvt.setup_live(*self.arr_pvt_axes) # Execute on axis Z

    def execute_pvt(self):
        self.live_pvt.call( self.pvt_buffer)

    def home3(self):
        self.devices[0].all_axes.home()
        self.devices[DEVICE_ROT_PLATFORM].all_axes.home()

    def sweep3(self, amt_deg=45, duration=3.0):
        self.live_pvt.call(self.pvt_buffer)
        amt_deg=-30
        self.devices[DEVICE_ROT_PLATFORM].get_axis(1).move_absolute(amt_deg, Units.ANGLE_DEGREES,
                                          velocity=abs(amt_deg)*2/duration, velocity_unit=Units.ANGULAR_VELOCITY_DEGREES_PER_SECOND,
                                          wait_until_idle=False)
                                          
    def to_start3(self, amt_deg=45, duration=3.0):
        self.live_pvt.point(*self.start_pos)
        self.devices[DEVICE_ROT_PLATFORM].get_axis(1).move_absolute(30, Units.ANGLE_DEGREES,
                                          velocity=amt_deg/duration, velocity_unit=Units.ANGULAR_VELOCITY_DEGREES_PER_SECOND,
                                          wait_until_idle=False)





