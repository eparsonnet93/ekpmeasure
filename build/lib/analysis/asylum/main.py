import pandas as pd
import numpy as np

import matplotlib.pyplot as plt

from igor.binarywave import load as loadibw

__all__ = ('load_image_from_binary','plot_pfm', 'load_pfmloop_from_binary')


def plot_pfm(imgdata_dict, meta_data, cmap='viridis', figsize = (20,10)):
    l = len(imgdata_dict)
    fig, axs = plt.subplots(ncols = int(l/2), nrows = 2, figsize = figsize)
    axs = axs.flatten()
    d = float(meta_data['ScanSize'])*1e6/int(meta_data['ScanLines'])
    for i, key in enumerate(imgdata_dict):
        image, ax = imgdata_dict[key], axs[i]
        ax.imshow(image,cmap=cmap, extent = [0, d*image.shape[1], 0, d*image.shape[0]])
        ax.set_title(key, size = 20)
        ax.tick_params(labelsize = 20)
        
    return fig, axs

def load_image_from_binary(path, return_meta_data = False):
    """
    loads data from binary file (from asylum research) into a numpy array
    
    Returns: pandas.DataFrame({'label':(numpy array) imgdata})
    ----
    
    path: str
    return_meta_data: bool - True returns (dict({'label':(numpy array) imgdata}, meta_data)  
        meta_data (dict) -> {ScanLines:(str)... etc}
    
    """
    
    data = loadibw(path)
    
    list_of_metadata = str(data['wave']['note']).replace("b'", "").split('\\r') #clean up binary 
    meta_data = dict()
    for x in list_of_metadata:
        spl = x.split(': ')
        try:
            meta_data.update({'{}'.format(spl[0]):spl[1]})
        except IndexError:
            try:
                spl = x.split(':')
                meta_data.update({'{}'.format(spl[0]):spl[1]})
            except:
                pass
            
    for x in data['wave']['labels']:
        if len(x)>1:
            labels = x[1:]
            labels = [str(label).replace("b'", "").replace("'", "") for label in labels]
            
    out = dict()
    for ijk, label in enumerate(labels):
        try:
            imgdata = data['wave']['wData'][:,:,ijk]
        except IndexError:
            raise IndexError('label count does not match data count. i.e. imgdata does not have data for each label (is this file a pfm loop??)')
        out.update({label: imgdata})

    #out = pd.DataFrame(out, index = [0])
        
    if return_meta_data:
        return out, meta_data
    else:
        return out

def load_pfmloop_from_binary(path, return_meta_data = False):
    """
    loads data from binary file (from asylum research) into a numpy array
    
    Returns: dict({'label':(numpy array) imgdata}
    ----
    
    path: str
    return_meta_data: bool - True returns (dict({'label':(numpy array) imgdata}, meta_data)  
        meta_data (dict) -> {ScanLines:(str)... etc}
        
    The complete list of included keys in meta_data is given here:
    
    ['ScanSize', 'FastScanSize', 'SlowScanSize', 'ScanRate', 'XOffset', 'YOffset', 'PointsLines', 'ScanPoints', 'ScanLines', 'ScanAngle', 'ImagingMode', 'InvOLS', 'SpringConstant', 'AmpInvOLS', 'Amp2Invols', 'FastRatio', 'SlowRatio', 'TopLine', 'BottomLine', 'ScanMode', 'NapMode', 'FMapScanTime', 'FMapScanPoints', 'FMapScanLines', 'FMapXYVelocity', 'FMapBookWise', 'Channel1DataType', 'DataTypeSum', 'PhaseOffset', 'PhaseOffset1', 'NapPhaseOffset', 'VoltageParm', 'NapParms', 'PreScanSetting', 'OrcaOffset', 'OrcaOffset2', 'UserIn0Gain', 'UserIn0Offset', 'UserIn1Gain', 'UserIn1Offset', 'UserIn2Gain', 'UserIn2Offset', 'LateralGain', 'LateralOffset', 'OrcaGain', 'OrcaGain2', 'FastMapScanRate', 'FastMapZRate', 'Real Parms', 'Initial Parms', 'Initial ScanSize', 'Initial FastScanSize', 'Initial SlowScanSize', 'Initial ScanRate', 'ScanSpeed', 'Initial XOffset', 'Initial YOffset', 'Initial ScanPoints', 'Initial ScanLines', 'RoundFactor', 'IntegralGain', 'ProportionalGain', 'Initial ScanAngle', 'ScanAngleFactor', 'AmplitudeSetpointVolts', 'AmplitudeSetpointMeters', 'DriveAmplitude', 'DriveFrequency', 'SweepWidth', 'SlowScanEnabled', 'DeflectionSetpointVolts', 'DeflectionSetpointMeters', 'DeflectionSetpointNewtons', 'Initial ImagingMode', 'MaxScanSize', 'Initial InvOLS', 'Initial SpringConstant', 'DisplaySpringConstant', 'ScanStateChanged', 'ScanDown', 'XLVDTSens', 'YLVDTSens', 'ZLVDTSens', 'XLVDTOffset', 'YLVDTOffset', 'ZLVDTOffset', 'YIgain', 'YPgain', 'XIgain', 'XPgain', 'LastScan', 'XPiezoSens', 'YPiezoSens', 'ZPiezoSens', 'XDriveOffset', 'YDriveOffset', 'SweepPoints', 'SecretGain', 'YSgain', 'XSgain', 'DIsplayLVDTTraces', 'Initial PhaseOffset', 'BaseSuffix', 'SaveImage', 'ParmChange', 'ADCgain', 'OldADCgain', 'OldScanSize', 'OldYOffset', 'OldXOffset', 'ZIgain', 'ZPgain', 'ZSgain', 'Initial AmpInvOLS', 'UpdateCounter', 'DoMunge', 'XMungeAlpha', 'YMungeAlpha', 'ZMungeAlpha', 'StartHeadTemp', 'StartScannerTemp', 'Has1xACDeflGain', 'DontChangeXPT', 'LowNoise', 'ScreenRatio', 'XDriftRate', 'YDriftRate', 'XDriftTotal', 'YDriftTotal', 'DriftBIts', 'DriftCount', 'Setpoint', 'Initial FastRatio', 'Initial SlowRatio', 'Initial TopLine', 'Initial BottomLine', 'ScanStatus', 'Is1DPlus', 'DelayUpdate', 'MarkerRatio', 'StartLineCount', 'OldAmplitudeSetpointVolts', 'OldDeflectionSetPointVolts', 'Initial ScanMode', 'Interpolate', 'TipVoltage', 'SurfaceVoltage', 'FreqIgain', 'FreqPgain', 'FreqSgain', 'Initial OrcaGain', 'FreqGainOn', 'Initial UserIn0Gain', 'Initial UserIn1Gain', 'Initial UserIn2Gain', 'Initial LateralGain', 'IsBipolar', 'FrequencyHack', 'MagneticField', 'DriveGainOn', 'DriveIGain', 'DrivePGain', 'DriveSGain', 'Initial UserIn0Offset', 'Initial UserIn1Offset', 'Initial UserIn2Offset', 'Initial LateralOffset', 'LastImage', 'ZoomSize', 'ZoomXOffset', 'ZoomYOffset', 'User0Voltage', 'User1Voltage', 'ExtendedZ', 'DriveAmplitude1', 'DriveFrequency1', 'SweepWidth1', 'Initial PhaseOffset1', 'Initial Amp2InvOLS', 'Initial VoltageParm', 'MicroscopeID', 'CapacitanceSens', 'CapacitanceOffset', 'CapPhaseOffset', 'TipBiasOffset', 'TipHeaterOffset', 'SurfaceBiasOffset', 'UseCantHolder', 'CurrentCantHolder', 'HasClickRing', 'XScanDirection', 'YScanDirection', 'SaveImageCount', 'SaveImageLines', 'Initial OrcaGain2', 'UpdateSlowWave', 'FBFilterBW', 'CurrentSetpointAmps', 'CurrentSetpointVolts', 'OldCurrentSetpointVolts', 'OldCurrentSetpointAmps', 'HasFM', 'LastScanWithdraw', 'HasLaserRelay', 'ToggleLaserRelay', 'Decimation', 'DARTIGain', 'DARTPGain', 'SampleHolder', 'ManualSampleHolder', 'CypherXPTLock', 'XPTLock', 'LogFeedback', 'ARSysScanBusy', 'SimpleControls', 'Initial PointsLines', 'FreeAirAmplitude', 'FreeAirPhase', 'FreeAirDeflection', 'FreeAirDriveAmplitude', 'ContinualRetune', 'ForceFilter', 'TemperatureSens', 'TemperatureOffset', 'OffsetBehavior', 'InputRange', 'XLVDTSensSlope', 'YLVDTSensSlope', 'XLVDTSensIntercept', 'YLVDTSensIntercept', 'HaveWeKilledTheProgressBar', 'Initial PreScanSetting', 'ImageFrameTime', 'FBFilterSelectivity', 'HasDriveChoke', 'DriveChokeOn', 'CFCWFOS', 'SkewAngle', 'ContinualRetuneTime', 'DRTimeStamp', 'CRTimeStamp', 'Cypher15VPower', 'HasBlueDrive', 'BlueDriveOn', 'blueDriveOffset', 'blueDriveMaxAmplitude', 'bDDriveAmplitude', 'bDDriveAmplitude1', 'bDDiffEfficiencyV', 'BackPackIn0Gain', 'BackPackIn0Offset', 'BackPackIn1Gain', 'BackPackIn1Offset', 'BackPackIn2Gain', 'BackPackIn2Offset', 'BackPackIn3Gain', 'BackPackIn3Offset', 'BackPackIn4Gain', 'BackPackIn4Offset', 'bdReCalibrateTime', 'bdMotorError', 'ScanModeGUI', 'FastMapSetpointVolts', 'FastMapSetpointNewtons', 'OldFastMapSetpointVolts', 'OldFastMapSetpointNewtons', 'Initial FastMapZRate', 'FastMapAmplitude', 'FastMapFBMethod', 'FastMapFBPhase', 'FastMapFBWindow', 'FastMapAmpSetpointVolts', 'FastMapAmpSetpointMeters', 'FastMapIndex', 'QueueProgress', 'QueueEstimate', 'QueueExpand', 'FastMapIGain', 'Initial FastMapScanRate', 'FastMapBaseLine', 'blueThermOn', 'FastMapScanPoints', 'FastMapScanLines', 'FastMapOptScanPoints', 'FastMapOptScanLines', 'FreqDGain', 'DriveDGain', 'ImageSaveExpand', 'Saturated', 'FrameCount', 'SinusoidalOn', 'StartHeaterTemp', 'StartHeaterHumidity', 'MicroscopeModel', 'BlueDriveDissipationInWatts', 'NapIntegralGain', 'NapProportionalGain', 'NapDeflectionSetpointVolts', 'NapAmplitudeSetpointVolts', 'NapDissipationSetpointVolts', 'NapFrequencySetPointHz', 'NapCurrentSetpointAmps', 'NapDriveAmplitude', 'NapDriveFrequency', 'NapDriveAmplitude1', 'NapDriveFrequency1', 'NapTipVoltage', 'NapSurfaceVoltage', 'NapUser0Voltage', 'NapUser1Voltage', 'NapHeight', 'NapStartHeight', 'NapTime', 'PotentialIGain', 'PotentialPGain', 'PotentialGainOn', 'ElectricTune', 'NapCurrentSetpointVolts', 'PotentialLoopLimit', 'ClosedNap', 'NapZIGain', 'NapZPGain', 'AutoNapZGain', 'bDNapDriveAmplitude', 'bDNapDriveAmplitude1', 'Channel2DataType', 'Channel3DataType', 'Channel4DataType', 'Channel5DataType', 'Channel6DataType', 'Channel7DataType', 'Channel8DataType', 'UserCalcFunc', 'UserCalcBFunc', 'FastMap1DataType', 'FastMap2DataType', 'FastMap3DataType', 'FastMap4DataType', 'FastMapCapture', 'InA', 'InB', 'InFast', 'InAOffset', 'InBOffset', 'InFastOffset', 'OutXMod', 'OutYMod', 'OutZMod', 'FilterIn', 'BNCOut0', 'BNCOut1', 'BNCOut2', 'PogoOut', 'Chip', 'Shake', 'Input.Z.Filter.Freq', 'Input.X.Filter.Freq', 'Input.Y.Filter.Freq', 'Input.A.Filter.Freq', 'Input.B.Filter.Freq', 'Input.Fast.Filter.Freq', 'Lockin.0.Filter.Freq', 'Lockin.1.Filter.Freq', 'Sample Rate', 'ThermalDC', 'ThermalQ', 'ThermalFrequency', 'ThermalWhiteNoise', 'ScaleLog', 'FitWidth', 'ThermalSamples', 'ThermalCounter', 'SectionSamples', 'SectionCounter', 'DoThermal', 'ThermalResolution', 'ThermalZoom', 'DoCantTune', 'ZoomCounter', 'AutoTuneLow', 'AutoTuneHigh', 'TargetVoltage', 'TargetPercent', 'CheckTuneTraces', 'ButtonTime', 'ShowThermalFit', 'AppendThermalBit', 'TuneQ', 'TuneGain', 'TunePeakResult', 'TuneFreqResult', 'TuneQResult', 'ThermalSamplesLimit', 'TuneFeedback', 'TuneDDSOutput', 'TipVoltCenter', 'TipVoltWidth', 'ThermalFrequencyRange', 'AutoTuneLimit', 'AutoTuneLow1', 'AutoTuneHigh1', 'TargetVoltage1', 'TargetPercent1', 'DualACMode', 'WhichACMode', 'BackwardsTune', 'TuneCaptureRate', 'TuneTime', 'TuneFilter', 'iDriveOn', 'FrequencyRatio', 'DFRTFrequencyCenter', 'DFRTFrequencyWidth', 'DFRTOn', 'ThermalCenter', 'ThermalWidth', 'DFWMAMT', 'LastXPos', 'LastYPos', 'PFMFrequencyLimit', 'TuneLockin', 'TipHeaterDrive', 'AdjustSpringConstant', 'DrawThermalFit', 'LateralTune', 'ThermalTemperature', 'UseCypherThermal', 'UseCypherMultiThread', 'Illumination', 'ARCZ', 'TuneAngle', 'IsDefaultFrequency', 'TargetAmplitude', 'TargetPhase', 'LossTanAmp1', 'LossTanPhase1', 'LossTanAmp2', 'LossTanPhase2', 'LossTanFreq1', 'LossTanFreq2', 'LossTanQ1', 'LossTanQ2', 'SecondFrequency', 'TryFitAgain', 'HighFrequencyMode', 'ThermalLever', 'DoSader', 'CustomLeverLength', 'CustomLeverWidth', 'CustomLeverFrequency', 'ResFreq1', 'ResFreq2', 'GetStartedRoughness', 'GetStartedOn', 'GSGainGain', 'GSSetpointPercent', 'GSHardness', 'GSLeverRange', 'GetStartedMorePanel', 'GSUseManualThermal', 'GSMotorHeight', 'GSStickySample', 'GSDateTime', 'YourVariablesStartHere', 'DARTAnalysisImage', 'DARTAmplitude1Label', 'DARTAmplitude2Label', 'DARTPhase1Label', 'DARTPhase2Label', 'DARTFrequency1Label', 'Log File', 'Date', 'Time', 'Seconds', 'UserCalcUnit', 'UserIn0Unit', 'UserIn1Unit', 'UserIn2Unit', 'LateralUnit', 'ARUserPanelName', 'UserIn0Name', 'UserIn1Name', 'UserIn2Name', 'UserCalcName', 'UserIn0Ab', 'UserIn1Ab', 'UserIn2Ab', 'UserCalcAb', 'UserIn0Force', 'UserIn1Force', 'UserIn2Force', 'UserCalcForce', 'SaveForce', 'LastSaveImage', 'LastSaveForce', 'NavLoadPath', 'LastNavLoadPath', 'UserCalcBUnit', 'UserCalcBName', 'UserCalcBForce', 'UserCalcBAb', 'BackPackIn0Unit', 'BackPackIn0Name', 'BackPackIn0Ab', 'BackPackIn0Force', 'BackPackIn1Unit', 'BackPackIn1Name', 'BackPackIn1Ab', 'BackPackIn1Force', 'BackPackIn2Unit', 'BackPackIn2Name', 'BackPackIn2Ab', 'BackPackIn2Force', 'BackPackIn3Unit', 'BackPackIn3Name', 'BackPackIn3Ab', 'BackPackIn3Force', 'BackPackIn4Unit', 'BackPackIn4Name', 'BackPackIn4Ab', 'BackPackIn4Force', 'DetectorSum', 'XSensor', 'YSensor', 'ZSensor', 'DDSAmplitude0', 'DDSDCOffset0', 'DDSFrequency0', 'DDSFrequencyOffset0', 'DDSPhaseOffset0', 'DDSAmplitude1', 'DDSFrequency1', 'DDSPhaseOffset1', 'Amplitude', 'Phase', 'Inputi', 'Inputq', 'Inputi1', 'Inputq1', 'Count', 'Count2', 'Potential', 'Amplitude1', 'Phase1', 'DDSQGain0', 'DDSQAngle0', 'DDSFrequencyOffset1', 'Deflection', 'Lateral', 'Frequency', 'LockIn', 'Height', 'DeflectionValue', 'TipBias', 'DartAmp', 'VerDate', 'Version', 'XopVersion', 'OSVersion', 'IgorFileVersion', 'BaseName', 'SkewAngleRead', 'ImageNote', 'TipSerialNumber', 'Planefit 0', 'PlanefitOrder 0', 'FlattenOrder 0', 'Planefit Offset 0', 'Planefit X Slope 0', 'Planefit Y Slope 0', 'Flatten Offsets 0', 'Flatten Slopes 0', 'Display Offset 0', 'Display Range 0', 'ColorMap 0', 'Planefit 1', 'PlanefitOrder 1', 'FlattenOrder 1', 'Planefit Offset 1', 'Planefit X Slope 1', 'Planefit Y Slope 1', 'Display Offset 1', 'Display Range 1', 'ColorMap 1', 'Planefit 2', 'PlanefitOrder 2', 'FlattenOrder 2', 'Planefit Offset 2', 'Planefit X Slope 2', 'Planefit Y Slope 2', 'Display Offset 2', 'Display Range 2', 'ColorMap 2', 'Planefit 3', 'PlanefitOrder 3', 'FlattenOrder 3', 'Planefit Offset 3', 'Planefit X Slope 3', 'Planefit Y Slope 3', 'Display Offset 3', 'Display Range 3', 'ColorMap 3', 'Planefit 4', 'PlanefitOrder 4', 'FlattenOrder 4', 'Planefit Offset 4', 'Planefit X Slope 4', 'Planefit Y Slope 4', 'Display Offset 4', 'Display Range 4', 'ColorMap 4', 'Planefit 5', 'PlanefitOrder 5', 'FlattenOrder 5', 'Planefit Offset 5', 'Planefit X Slope 5', 'Planefit Y Slope 5', 'Display Offset 5', 'Display Range 5', 'ColorMap 5', 'EndHeadTemp', 'EndScannerTemp', 'EndHeaterTemp', 'EndHeaterHumidity']
    """
    
    data = loadibw(path)
    
    list_of_metadata = str(data['wave']['note']).replace("b'", "").split('\\r') #clean up binary 
    meta_data = dict()
    for x in list_of_metadata:
        spl = x.split(': ')
        try:
            meta_data.update({'{}'.format(spl[0]):spl[1]})
        except IndexError:
            try:
                spl = x.split(':')
                meta_data.update({'{}'.format(spl[0]):spl[1]})
            except:
                pass
            
    for x in data['wave']['labels']:
        if len(x)>1:
            labels = x[1:]
            labels = [str(label).replace("b'", "").replace("'", "") for label in labels]
            
    out = dict()
    for ijk, label in enumerate(labels):
        try:
            imgdata = data['wave']['wData'][:,ijk]
        except IndexError:
            raise IndexError('label count does not match data count. i.e. imgdata does not have data for each label (is this file a pfm loop??)')
        out.update({label: imgdata})
        
    if return_meta_data:
        return out, meta_data
    else:
        return out