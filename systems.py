import streamlit as st
import pandas as pd
import datetime
from datetime import date
import numpy as np
import math

st.header('**Sucker Rod Pump**')

wellName = st.selectbox('Well:', ('A'))

col1, col2 = st.beta_columns(2)
method = col1.selectbox('Method:',
                        ('SRP', ''))
surfaceUnit = col2.selectbox('Surface unit:', ('M-640D-305-168', ''))

col1, col2 = st.beta_columns(2)
opeStart_d = col1.date_input(
    "Operations started:", datetime.date(2019, 6, 26))
col2.text_input('Seating nipple at (ft):', value='5060')

downholePump = st.selectbox('Downhole pump:', ('API 25-200-RWBC-24-4-H0', ''))

col1, col2, col3 = st.beta_columns(3)
rodsCent_opt = col1.selectbox('Rods Centralizers:', ('No', 'Yes'))
tubA_opt = col2.selectbox('Tubing anchored:', ('Yes', 'No'))
fit = col3.text_input('Fit (mils):', value='3')

barrelsTable = [
    ['106', '1.0625'],
    ['125', '1.25'],
    ['150', '1.5'],
    ['175', '1.75'],
    ['178', '1.78125'],
    ['200', '2'],
    ['225', '2.25'],
    ['275', '2.75'],
    ['375', '3.75']]

df = pd.DataFrame(barrelsTable, columns=['Nomenclature', 'Basic bore (in)'])

st.table(df)

SurfaceMaxStroke = int(int(surfaceUnit[-3:])/12)

col1, col2 = st.beta_columns(2)

col1.info('Surface max. Stroke: ' + str(SurfaceMaxStroke))
valueMatch = downholePump[7:10]
pumpBasicBore = int(df[df['Nomenclature'] == valueMatch]['Basic bore (in)'])
col2.info('Pump basic bore: ' + str(pumpBasicBore))

col1.info('Barrel length: ' + str(int(downholePump[16:18])))
col2.info('Plunger length: ' + str(int(downholePump[19:20])))

st.subheader('**Card Analysis parameters**')

col1, col2 = st.beta_columns(2)

poundPointLB = col1.text_input(
    'Pound point look back:', value=10)

poundGasCA = col2.text_input(
    'Pound/Gas change angle (degrees):', value=85)

col1, col2, col3 = st.beta_columns(3)

MinPumpFillage = col1.text_input(
    'Min. Pump Fillage:', value=0.8)

MaxIncidenceAngle = col2.text_input(
    'Max Incidence Angle (degrees):', value=15)

optimumSPMLimit = col3.text_input(
    'Optimum SPM limit (SPM):', value=8)

st.subheader('**Data operations**')

uploaded_file = st.file_uploader("Choose a CSV file")
if uploaded_file is not None:

    dataframe = pd.read_csv(uploaded_file)
    st.write(dataframe)

    # Estimate of 'Geometric Load vector'
    dataframe['Load_1(lbs)'] = dataframe['Geometric Load']-811.9

    # Estimate of 'area vector'
    dataframe['area'] = abs(dataframe['pos(in)']) * \
        abs(dataframe['Geometric Load'])

    # Estimate of 'direction vector'
    difpos = dataframe['pos(in)']-dataframe['pos(in)'].shift(1)

    dif = []
    dif.append('')
    len(difpos)

    for x in range(1, len(difpos)):
        if abs(difpos[x]) > 0.02:
            dif.append(np.sign(difpos[x]))
        else:
            dif.append(dif[x-1])

    dataframe['direction'] = dif

    # Estimate of 'Change of Dir count vector'

    cdc = []
    cdc.append('')
    cdc.append('')

    if dif[2] != dif[2-1]:
        cdc.append(0+1)
    else:
        cdc.append(0)

    for x in range(3, len(difpos)):
        if dif[x] != dif[x-1] and dif[x] != 0:
            cdc.append(cdc[x-1]+1)
        else:
            cdc.append(cdc[x-1])

    dataframe['Change of Dir count'] = cdc

    # Estimate of 'Stop row'
    srow = []
    srow.append('')
    srow.append('')
    srow.append(0)

    for x in range(3, len(difpos)):
        if srow[x-1] == 1:
            srow.append(1)
        else:
            if abs(dataframe['pos(in)'][x]) > abs(dataframe['pos(in)'][0]) and cdc[x] >= 2:
                srow.append(1)
            else:
                srow.append(0)

    dataframe['Stop row'] = srow

    st.subheader('**Results**')

    st.write(dataframe)

    num = 0 + 1
    for x in range(2, len(difpos)):
        if srow[x] == 0:
            num = num + 1

    # Estimate of 'Percentiles: Geometric Load & Pos.'

    glFilter = []
    posFilter = []
    load_1Filter = []

    for x in range(0, num+1):
        glFilter.append(dataframe['Geometric Load'][x])
        posFilter.append(dataframe['pos(in)'][x])
        load_1Filter.append(dataframe['Load_1(lbs)'][x])

    percentiles = [95, 90, 85, 80, 75, 70, 50, 30, 25, 20, 15, 10, 5]

    def GeometricLoad(glFilterArray, Percentile):
        return int(np.percentile(glFilterArray, Percentile))

    def Pos(posFilterArray, Percentile):
        return int(np.percentile(posFilterArray, Percentile))

    glPercentiles = []
    posPercentiles = []

    for x in percentiles:
        glPercentiles.append(GeometricLoad(glFilter, x))
        posPercentiles.append(Pos(posFilter, x))

    perDF = pd.DataFrame()

    perDF['P%'] = percentiles
    perDF['Geometric Load'] = glPercentiles
    perDF['Pos.'] = posPercentiles

    st.write(perDF)

    col1, col2 = st.beta_columns(2)

    # Estimate of 'Strokes'
    StrokeBottom = perDF['Pos.'][len(percentiles)-1]
    col1.info('Stroke bottom: ' + str(StrokeBottom))
    StrokeTop = perDF['Pos.'][0]
    col2.info('Stroke top: ' + str(StrokeTop))
    DownholeStrokeLength = StrokeTop-StrokeBottom
    dsl = DownholeStrokeLength
    col1.info('Downhole stroke length: ' + str(DownholeStrokeLength))

    # Estimate of 'SPM vector'
    spm = []
    spm.append('')
    for x in range(1, len(difpos)):
        spm.append((abs(dataframe['pos(in)'][x]-dataframe['pos(in)'][x-1])/dsl)/(
            (dataframe['time(sec)'][x]-dataframe['time(sec)'][x-1])/60))

    dataframe['SPM'] = spm

    spmFilter = []

    for x in range(1, num+1):
        spmFilter.append(dataframe['SPM'][x])

    averageSPM = np.mean(spmFilter)

    col1.info('Load displacement: ' + str(min(load_1Filter)))
    col2.info('Average SPM: ' + str(round(averageSPM, 1)))

   # Estimate of 'Segment'
    gl_p85 = perDF['Geometric Load'][2]
    gl_p15 = perDF['Geometric Load'][10]
    pos_p15 = perDF['Pos.'][10]
    gl_p5 = perDF['Geometric Load'][12]

    segment = []

    for x in range(0, len(difpos)):
        if dataframe['pos(in)'][x] <= pos_p15 and dataframe['Geometric Load'][x] <= gl_p85 and dataframe['Geometric Load'][x] >= gl_p15:
            segment.append(1)
        else:
            segment.append(0)

    dataframe['Segment'] = segment
    st.write(dataframe)

    dfFilter = pd.DataFrame()
    dfFilter['pos(in)'] = posFilter
    dfFilter['Geometric Load'] = glFilter

    st.write(dfFilter)

    # Estimate of 'Pound point'
    dfFilter['posMax'] = dfFilter['pos(in)'].where(
        dfFilter['Geometric Load'] < gl_p5)

    poundPoint = dfFilter['posMax'].max()

    posMax = dfFilter['posMax'].tolist()

    row_pp = posMax.index(poundPoint)

    row_sp = row_pp-int(poundPointLB)

    st.subheader('**Pound curve analysis**')

    col1, col2 = st.beta_columns(2)

    startPoint = dataframe['pos(in)'][row_sp]
    col1.info('Start point: ' + str(startPoint))
    col2.info('Pound point: ' + str(poundPoint))

    # Estimate of 'Incidence slope'
    ys = []
    xs = []
    for x in range(row_sp, row_pp+1):
        ys.append(dataframe['Geometric Load'][x])
        xs.append(dataframe['pos(in)'][x])

    slope, intercept = np.polyfit(xs, ys, 1)
    col1.info('Incidence slope: ' + str(round(slope, 5)))

    # Estimate of 'Incidence angle'
    incidenceAngle = round(math.degrees(math.atan(slope)), 5)
    col2.info('Incidence angle: ' + str(incidenceAngle))

    pumpFillage = round((poundPoint-StrokeBottom)/(StrokeTop-StrokeBottom), 5)
    col1.info('Pump fillage: ' + str(pumpFillage))

    st.subheader('**RTTF Calculation**')

    # Estimate of 'Absence of Fluid Pound'
    # =IF('Data operations'!Q38>Entries!B22,1,IF(AND('Data operations'!Q38<Entries!B22,'Data operations'!Q37>Entries!B21),0))
    if pumpFillage > float(MinPumpFillage):
        AbsenceOfFluidPound = int(1)
    elif pumpFillage < float(MinPumpFillage) and incidenceAngle > float(poundGasCA):
        AbsenceOfFluidPound = int(0)

    col1, col2 = st.beta_columns(2)

    col1.info('Absence of Fluid Pound: ' + str(AbsenceOfFluidPound))

    # Estimate of 'Absence of Gas interference'
    # =IF('Data operations'!Q38>Entries!B22,1,IF(AND('Data operations'!Q38<Entries!B22,'Data operations'!Q37<Entries!B21,'Data operations'!Q37>Entries!B23),0,1))
    if pumpFillage > float(MinPumpFillage):
        AbsenceOfGasInterference = 1
    elif pumpFillage < float(MinPumpFillage) and incidenceAngle < float(poundGasCA) and incidenceAngle > float(MaxIncidenceAngle):
        AbsenceOfGasInterference = 0
    else:
        AbsenceOfGasInterference = 1

    col2.info('Absence of Gas interference: ' + str(AbsenceOfGasInterference))

    # Estimate of 'Good Pump Fillage'
    # =IF('Data operations'!Q38>=Entries!B22,1,0)
    if pumpFillage >= float(MinPumpFillage):
        GoodPumpFillage = 1
    else:
        GoodPumpFillage = 0

    col1.info('Good Pump Fillage: ' + str(GoodPumpFillage))

    # Estimate of 'Slower SPM'
    # =IF('Data operations'!$Q$22<=Entries!B24,1,0)
    if averageSPM <= float(optimumSPMLimit):
        SlowerSPM = 1
    else:
        SlowerSPM = 0
    col2.info('Slower SPM: ' + str(SlowerSPM))

    # Estimate of 'Presence of RodGuides'
    # =IF(Entries!B8="Yes",1,0)
    if rodsCent_opt == "Yes":
        PresenceOfRodGuides = 1
    else:
        PresenceOfRodGuides = 0

    col1.info('Presence of Rod Guides: ' + str(PresenceOfRodGuides))

    # Estimate of 'Fit factor'
    # =IF(Entries!B16<=3,1,0)
    if float(fit) <= 3:
        fitFactor = 1
    else:
        fitFactor = 0

    col2.info('Fit factor: ' + str(fitFactor))

    otherFactors = 1

    col1.info('Other factors: ' + str(otherFactors))

    # Estimate of 'Optimum Runlife Index'
    w1 = 0.08
    w2 = 0.03
    w3 = 0.06
    w4 = 0.06
    w5 = 0.04
    w6 = 0.03
    w7 = 0.7

    optimumRunlifeIndex = AbsenceOfFluidPound*w1 + AbsenceOfGasInterference*w2 + \
        GoodPumpFillage*w3 + SlowerSPM*w4+PresenceOfRodGuides * \
        w5+fitFactor*w6 + otherFactors*w7

    col2.warning('Optimum Runlife Index: ' + str(optimumRunlifeIndex))

    optimumTTF = 968

    col1.info('Optimum TTF (days): ' + str(optimumTTF))

    # Estimate of 'Projected TTF'
    projectedTTF = int(optimumTTF*optimumRunlifeIndex)

    col2.info('Projected TTF (days): ' + str(projectedTTF))

    # Estimate of 'Remaining TTF'
    today = date.today()

    def days_360(date1, date2):
        days_diff = (date2.year - date1.year) * 360
        days_diff += (date2.month - date1.month) * 30
        days_diff += (date2.day - date1.day)
        return days_diff

    remainingTTF = projectedTTF-days_360(opeStart_d, today)

    st.success('Remaining TTF (days): ' + str(remainingTTF))
