###LIBRERIAS###
import pandas as pd
import numpy as np
import pandas_gbq
from google.cloud import bigquery
import datetime
import pyodbc
import pickle
import openpyxl
from tqdm import tqdm
from datetime import date, timedelta, datetime
from pandas.io import gbq
import warnings
warnings.filterwarnings('ignore')
from cmath import nan
import pandas as pd
import pandas_gbq
import ctypes
import chardet
import os
import gcsfs

################



## -------- INDICE LIBRERIAS ------ ##

# ---- 1. Control_input 
# ---- 2. check_pipeline_data
# ---- 3. cargasBO
# ---- 4. Check_Meetings_GGC
# ---- 5. Check_input_Cvent
# ---- 6. Cargas_Agent_CRO
# ---- 7. upload_Arrivals_Origins_QtAllStatus
# ---- 8. Upload_Cvent Data
# ---- 9. Upload_Various_TrueIt_Data_Days
# ---- 10. upload_TMS_Data_CRO
# ---- 11. Transformer

##-----------##

### ----- 1. Control_input: Function for the daily morning control of Trueit load Process ----- ###

def control_input(modo = None):
    """It allows you to check if Data for CRO Reports have beend loaded corrected in Google Cloud
        
        Args:
            - None: Diference Between Yesterday data and same day last week.
            - "control": Visualization all data.
            - "comparativo":Visualization only for yesterday data and same day last week
    
    """
    control = pandas_gbq.read_gbq("""SELECT * FROM `nh-cro-forecast.Evolution.Control` LIMIT 1000 """,project_id="nh-cro-forecast")
    hoy = control.loc[0]
    lw = control.loc[7]
    comparativo = pd.DataFrame([hoy,lw])
    columnas_numericas = control.select_dtypes(include=[float,int]).columns
    diferencia = hoy[columnas_numericas] - lw[columnas_numericas]
    if modo == "control":
        print(control)
    elif modo == "comparativo":
        print(comparativo)
    else:
        print("La diferencia entre hoy y los datos de hace una semana son:\n",diferencia)

##### ------------------------------------------------------------------------------------- #####


### ----- 2. check_pipeline_data: Function to control the daily load of Pipeline data ----- ###

def check_pipeline_data():
    """Allow to check if data for Daily Pipeline has been loaded correctly.
        You will find data for:
          - BO.Hist_BO_Clean_Full 
          - BO.Pipeline_Data

        Args are not requested
    """
    check = pandas_gbq.read_gbq("""SELECT Fecha, COUNT(1)
                                    FROM `nh-gem.BO.Hist_BO_Clean_Full`
                                    GROUP BY 1 ORDER BY 1 DESC
                                    LIMIT 1000 """,project_id="nh-cro-forecast")
    check_2 = pandas_gbq.read_gbq("""SELECT Correct_fecha, COUNT(1)
                                    FROM `nh-gem.BO.Pipeline_Data`
                                    GROUP BY 1
                                    ORDER BY 1 DESC
                                    LIMIT 1000 """,project_id="nh-cro-forecast")
    return("Datos BO.Hist_BO_Clean_Full: ",check.head(22),"Datos BO.Pipeline_Data: ",check_2.head(22))


##### ------------------------------------------------------------------------------------- #####

### -----3. cargasBO: Function to load manually data for pipeline, when our daily automatic process has failed. ----- ###


def cargasBO(start=datetime(2024, 7, 31),end=datetime(2024, 7, 31)):
    
    """
    To load 'BO.Hist_BO_Clean_Full' in Google Cloud.

    Args: 
    - Start: By default: datetime(2024,7,31) Change dat keeping datetime function
    - End: By default: date(2024,7,31) Change date keeping datetime function
    """

    def date_range(start, end):
        delta = end - start 
        days = [(start + timedelta(days=i)).strftime('%d%m%Y') for i in range(delta. days + 1)]
        days_with_format = [(start + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(delta. days + 1)]
        months = [(start + timedelta(days=i)).strftime('%m') for i in range(delta. days + 1)]
        years = [(start + timedelta(days=i)).strftime('%Y') for i in range(delta. days + 1)]
        return days, months, years, days_with_format

    start_date = start
    end_date = end
    old = datetime(1900, 1, 1)
    dias = date_range(start_date, end_date)

    def preparar_gbq(dataset):
        if '2nd_Creator_id' in dataset.columns:
            dataset.rename(columns={'2nd_Creator_id':'Second_Creator_id', '2nd_Agent_Center':'Second_Agent_Center'}, inplace=True)
        Call = dataset.astype(str)
        dictionary = {} 
        [dictionary.update({f'{i}':str}) for i in dataset.columns]
        Call_db = Call.astype(dictionary)
        return Call_db
        
    new_columns_created = ['BF', 'Reservation_id', 'Fin_Rev', 'Rev_Room', 'Rev_FB', 'Rev_Meeting', 'Rev_Other', 'Total_Rev', 'Room', 'FB', 'Meeting', 'Other', 'Room_night', 'Last_Change_Date', 'Creation_date', 'Start_date', 
    'End_date', 'BF_Confirmation_Date', 'BF_Cancellation_date', 'Main_Hotel_id', 'Client_id', 'BF_Commercial_Client_Name', 'Company_Responsible_id', 'BF_Company_Responsible_Name', 'CRS_id', 'BF_CRS_Name', 'BF_Status', 
    'MultiHotel', 'Booking_group_name', 'Event_Type', 'Creator_id', 'Creator_Center', 'Previous_Status', 'Deadline', 'Data_tracking', 'CUT_OFF_date', 'Cxl_reason_id', 'Rate', 'Second_Creator_id', 'Second_Creator_Center', 'Organizer_center', 
    'Market_Segment', 'Subsegment', 'Channel_ID', 'SubChannel_id', 'Language', 'Promotion', 'Reservation_status', 'Contact_person', 'Contact_Tel', 'Email', 'Serie', 'Hotel_id', 'External_reference', 'Date_last_status_change', 'Reservation_cancelled_by', 
    'AH_Main_Customer_PID', 'AH_Main_Customer_Name', 'Branch_main_customer', 'Branch_name', 'BID_AH', 'BID_AH_Name', 'BID_Agency_AH', 'BID_Agency_AH_Name', 'BID_Intermediary_AH', 'BID_Intermediary_AH_Name', 'BF_Promotion', 'Remarks', 'Quick_Denial', 
    'Quotation_ID', 'Net', 'Workflow_Step', 'Quotation_Tool_Dates_Creation_date', 'QT_Creator', 'QT_Creator_name', 'Canc_Reason_ID', 'Canc_Reason_Text', 'Remark_QD', 'Serie_Offer_BF', 'BF_PAX', 'Origin', 'Organizer', 'Organizer_Name']

    new_columns_mod = ['BF', 'Reservation_id', 'Fin_Rev', 'Rev_Room', 'Rev_FB', 'Rev_Meeting', 'Rev_Other', 'Total_Rev', 'Room', 'FB', 'Meeting', 'Other', 'Room_night', 'Last_Change_Date', 'Creation_date', 'Start_date', 
    'End_date', 'BF_Confirmation_Date', 'BF_Cancellation_date', 'Main_Hotel_id', 'Client_id', 'BF_Commercial_Client_Name', 'Company_Responsible_id', 'BF_Company_Responsible_Name', 'CRS_id', 'BF_CRS_Name', 'BF_Status', 
    'MultiHotel', 'Booking_group_name', 'Event_Type', 'Creator_id', 'Creator_Center', 'Previous_Status', 'Deadline', 'Data_tracking', 'CUT_OFF_date', 'Cxl_reason_id', 'Rate', 'Second_Creator_id', 'Second_Creator_Center', 'Organizer_center', 
    'Market_Segment', 'Subsegment', 'Channel_ID', 'SubChannel_id', 'Language', 'Promotion', 'Reservation_status', 'Contact_person', 'Contact_Tel', 'Email', 'Serie', 'Hotel_id', 'External_reference', 'Date_last_status_change', 'Reservation_cancelled_by', 
    'AH_Main_Customer_PID', 'AH_Main_Customer_Name', 'Branch_main_customer', 'Branch_name', 'BID_AH', 'BID_AH_Name', 'BID_Agency_AH', 'BID_Agency_AH_Name', 'BID_Intermediary_AH', 'BID_Intermediary_AH_Name', 'Serie_Offer_BF', 'BF_PAX', 'Organizer', 'Organizer_Name']

    Hist_BO_Creations = pd.DataFrame(columns=new_columns_created)
    Hist_BO_Mod = pd.DataFrame(columns=new_columns_mod)

    for i in range(len(dias[0])):
        dia = dias[0][i][:2]
        mes = dias[1][i]
        año = dias[2][i]
        format_day = dias[3][i]
        print(format_day)
        raw_data = pd.read_excel(fr'W:\DB\RAW DATA\{año}\{mes}\{dia}\BO\GEM_OPS_Creation.xlsx').iloc[:,1:]
        raw_data.columns = new_columns_created
        raw_data['Fecha'] = format_day
        Hist_BO_Creations = pd.concat([Hist_BO_Creations, raw_data], axis=0, ignore_index=True)
        raw_data2 = pd.read_excel(fr'W:\DB\RAW DATA\{año}\{mes}\{dia}\BO\GEM_OPS_Mod.xlsx').iloc[:,:]
        raw_data2.columns = new_columns_mod
        raw_data2['Fecha'] = format_day
        Hist_BO_Mod = pd.concat([Hist_BO_Mod, raw_data2], axis=0, ignore_index=True)
        
    old = datetime(1900, 1, 1)
    Hist_BO_Creations.reset_index(drop=True, inplace=True)
    Hist_BO_Mod.reset_index(drop=True, inplace=True)

    Hist_BO_Creations['Work_Type'] = 'Created'
    Hist_BO_Creations['Offer_Type']  = 'Main_offer'
    Hist_BO_Creations['Offer_Type'][Hist_BO_Creations['MultiHotel']=='X'] = "Multihotel"
    Hist_BO_Creations['Main_Hotel_id'][Hist_BO_Creations['MultiHotel']=='X'] = Hist_BO_Creations['Hotel_id'][Hist_BO_Creations['MultiHotel']=='X']
    Hist_BO_Creations['Offer_Type'][(Hist_BO_Creations['BF'].str[:2] == 'MB')&(Hist_BO_Creations['Main_Hotel_id'] != Hist_BO_Creations['Hotel_id'])&(Hist_BO_Creations['MultiHotel']!='X')] = 'Second_Offer'
    Hist_BO_Creations['Reservation_id'] = Hist_BO_Creations['Reservation_id'].fillna('0000000000').astype(int).astype(str).str.zfill(10)
    Hist_BO_Creations['Creation_date'][Hist_BO_Creations['Creation_date'].isna()] = Hist_BO_Creations['Fecha']
    Hist_BO_Creations['Creation_date'] = Hist_BO_Creations['Creation_date'].astype('datetime64[ns]').dt.strftime('%Y-%m-%d')
    Hist_BO_Creations['Start_date'][Hist_BO_Creations['Start_date'].isna()] = old.strftime('%Y-%m-%d')
    Hist_BO_Creations['Start_date'] = pd.to_datetime(Hist_BO_Creations['Start_date'], errors='coerce').dt.strftime('%Y-%m-%d')
    Hist_BO_Creations['End_date'][Hist_BO_Creations['End_date'].isna()] = old.strftime('%Y-%m-%d')
    Hist_BO_Creations['End_date'] = pd.to_datetime(Hist_BO_Creations['End_date'], errors='coerce').dt.strftime('%Y-%m-%d')
    Hist_BO_Creations['BF_Confirmation_Date'][Hist_BO_Creations['BF_Confirmation_Date'].isna()] = '19000101'
    Hist_BO_Creations['BF_Confirmation_Date'][Hist_BO_Creations['BF_Confirmation_Date']==0.0] = '19000101'
    Hist_BO_Creations['BF_Confirmation_Date'][Hist_BO_Creations['BF_Status'] != 'CONFI'] = '19000101'
    Hist_BO_Creations['BF_Cancellation_date'][~Hist_BO_Creations['BF_Cancellation_date'].isna()] = pd.to_datetime(Hist_BO_Creations['BF_Cancellation_date'][~Hist_BO_Creations['BF_Cancellation_date'].isna()]).dt.strftime('%Y-%m-%d')
    print('Fechas - Actualizadas')

    Hist_BO_Creations['Last_Change_Date'] = Hist_BO_Creations['Fecha']
    print('check_duplicados_created - Actualizado')
    Hist_BO_Creations['Creation_date'][Hist_BO_Creations['Creation_date'].isna()] = Hist_BO_Creations['Fecha'][Hist_BO_Creations['Creation_date'].isna()]
    print('check_creation_date - Actualizado')
    Hist_BO_Creations['Start_date'][Hist_BO_Creations['BF'].str[:2] != 'MB'] = Hist_BO_Creations['Fecha'][Hist_BO_Creations['BF'].str[:2] != 'MB'] 
    print('check_start_date - Actualizado')
    Hist_BO_Creations['End_date'][Hist_BO_Creations['BF'].str[:2] != 'MB'] = Hist_BO_Creations['Fecha'][Hist_BO_Creations['BF'].str[:2] != 'MB']
    print('check_end_date - Actualizado')


    # Hist_BO_Creations['BF_Confirmation_Date'][Hist_BO_Creations['BF_Confirmation_Date'].str.len() ==8] = Hist_BO_Creations['BF_Confirmation_Date'][Hist_BO_Creations['BF_Confirmation_Date'].str.len() ==8].astype(int).astype(str).str[:4]+Hist_BO_Creations['BF_Confirmation_Date'][Hist_BO_Creations['BF_Confirmation_Date'].str.len() ==8].astype(int).astype(str).str[4:6]+Hist_BO_Creations['BF_Confirmation_Date'][Hist_BO_Creations['BF_Confirmation_Date'].str.len() ==8].astype(int).astype(str).str[6:]
    # Hist_BO_Creations['BF_Confirmation_Date'][Hist_BO_Creations['BF_Status'] != 'CONFI'] = '19000101'
    Hist_BO_Creations['BF_Confirmation_Date'][Hist_BO_Creations['BF_Confirmation_Date'].str.len()==10] = Hist_BO_Creations['BF_Confirmation_Date'][Hist_BO_Creations['BF_Confirmation_Date'].str.len()==10].str[:4]+Hist_BO_Creations['BF_Confirmation_Date'][Hist_BO_Creations['BF_Confirmation_Date'].str.len()==10].str[5:7]+Hist_BO_Creations['BF_Confirmation_Date'][Hist_BO_Creations['BF_Confirmation_Date'].str.len()==10].str[8:]
    Hist_BO_Creations['BF_Confirmation_Date'] = Hist_BO_Creations['BF_Confirmation_Date'].astype(float).astype(int).astype(str).str[:4]+"-"+Hist_BO_Creations['BF_Confirmation_Date'].astype(float).astype(int).astype(str).str[4:6]+"-"+Hist_BO_Creations['BF_Confirmation_Date'].astype(float).astype(int).astype(str).str[6:]
    Hist_BO_Creations['BF_Cancellation_date'][Hist_BO_Creations['BF_Cancellation_date'].isna()] = old.strftime('%Y-%m-%d')
    Hist_BO_Creations['BF_Cancellation_date'] = Hist_BO_Creations['BF_Cancellation_date'].astype('datetime64[ns]').dt.strftime('%Y-%m-%d')
    Hist_BO_Creations['Deadline'].fillna('19000101', inplace=True)
    Hist_BO_Creations['Deadline'][Hist_BO_Creations['Deadline']==0] = '19000101'
    Hist_BO_Creations['Deadline'][Hist_BO_Creations['Deadline'].str.len() ==10] = Hist_BO_Creations['Deadline'][Hist_BO_Creations['Deadline'].str.len() ==10].astype(str).str[:4]+Hist_BO_Creations['Deadline'][Hist_BO_Creations['Deadline'].str.len() ==10].astype(str).str[5:7]+Hist_BO_Creations['Deadline'][Hist_BO_Creations['Deadline'].str.len() ==10].astype(str).str[8:]
    Hist_BO_Creations['Deadline'] = Hist_BO_Creations['Deadline'].astype(str).str[:4]+"-"+Hist_BO_Creations['Deadline'].astype(str).str[4:6]+"-"+Hist_BO_Creations['Deadline'].astype(str).str[6:]
    Hist_BO_Creations['Data_tracking'].fillna('19000101', inplace=True)
    Hist_BO_Creations['Data_tracking'][Hist_BO_Creations['Data_tracking']==0] = '19000101'
    Hist_BO_Creations['Data_tracking'][Hist_BO_Creations['Data_tracking'].str.len() ==10] = Hist_BO_Creations['Data_tracking'][Hist_BO_Creations['Data_tracking'].str.len() ==10].astype(str).str[:4]+Hist_BO_Creations['Data_tracking'][Hist_BO_Creations['Data_tracking'].str.len() ==10].astype(str).str[5:7]+Hist_BO_Creations['Data_tracking'][Hist_BO_Creations['Data_tracking'].str.len() ==10].astype(str).str[8:]
    Hist_BO_Creations['Data_tracking'] = Hist_BO_Creations['Data_tracking'].astype(str).str[:4]+'-'+Hist_BO_Creations['Data_tracking'].astype(str).str[4:6]+'-'+Hist_BO_Creations['Data_tracking'].astype(str).str[6:]
    Hist_BO_Creations['CUT_OFF_date'].fillna('19000101', inplace=True)
    Hist_BO_Creations['CUT_OFF_date'][Hist_BO_Creations['CUT_OFF_date']==0] = '19000101'
    Hist_BO_Creations['CUT_OFF_date'][Hist_BO_Creations['CUT_OFF_date'].str.len() ==10] = Hist_BO_Creations['CUT_OFF_date'][Hist_BO_Creations['CUT_OFF_date'].str.len() ==10].astype(str).str[:4]+Hist_BO_Creations['CUT_OFF_date'][Hist_BO_Creations['CUT_OFF_date'].str.len() ==10].astype(str).str[5:7]+Hist_BO_Creations['CUT_OFF_date'][Hist_BO_Creations['CUT_OFF_date'].str.len() ==10].astype(str).str[8:]
    Hist_BO_Creations['CUT_OFF_date'] = Hist_BO_Creations['CUT_OFF_date'].astype(str).str[:4]+"-"+Hist_BO_Creations['CUT_OFF_date'].astype(str).str[4:6]+"-"+Hist_BO_Creations['CUT_OFF_date'].astype(str).str[6:]
    Hist_BO_Creations['Date_last_status_change'][Hist_BO_Creations['Date_last_status_change'].isna()] = old.strftime('%Y-%m-%d')
    Hist_BO_Creations['Date_last_status_change'] = Hist_BO_Creations['Date_last_status_change'].astype('datetime64[ns]').dt.strftime('%Y-%m-%d')
    Hist_BO_Creations['Quotation_Tool_Dates_Creation_date'][~Hist_BO_Creations['Quotation_Tool_Dates_Creation_date'].isna()] = Hist_BO_Creations['Quotation_Tool_Dates_Creation_date'][~Hist_BO_Creations['Quotation_Tool_Dates_Creation_date'].isna()].astype('datetime64[ns]').dt.strftime('%Y-%m-%d')
    Hist_BO_Creations['Quotation_Tool_Dates_Creation_date'][Hist_BO_Creations['Quotation_Tool_Dates_Creation_date'].isna()] = old.strftime('%Y-%m-%d')
    print('Fechas - Corregidas')

    Hist_BO_Mod['Work_Type'] = 'Mod_Status'
    Hist_BO_Mod['Offer_Type']  = 'Main_offer'
    Hist_BO_Mod['Offer_Type'][Hist_BO_Mod['MultiHotel']=='X'] = "Multihotel"
    Hist_BO_Mod['Main_Hotel_id'][Hist_BO_Mod['MultiHotel']=='X'] = Hist_BO_Mod['Hotel_id'][Hist_BO_Mod['MultiHotel']=='X']
    Hist_BO_Mod['Offer_Type'][(Hist_BO_Mod['BF'].str[:2] == 'MB')&(Hist_BO_Mod['Main_Hotel_id'] != Hist_BO_Mod['Hotel_id'])&(Hist_BO_Mod['MultiHotel']!='X')] = 'Second_Offer'
    Hist_BO_Mod['Reservation_id'] = Hist_BO_Mod['Reservation_id'].fillna('0000000000').astype(int).astype(str).str.zfill(10)
    Hist_BO_Mod['Creation_date'] = Hist_BO_Mod['Creation_date'].astype('datetime64[ns]').dt.strftime('%Y-%m-%d')
    Hist_BO_Mod['Start_date'] = pd.to_datetime(Hist_BO_Mod['Start_date'], errors='coerce').dt.strftime('%Y-%m-%d')
    Hist_BO_Mod['End_date'] = pd.to_datetime(Hist_BO_Mod['End_date'], errors='coerce').dt.strftime('%Y-%m-%d')
    Hist_BO_Mod['End_date'][Hist_BO_Mod['End_date'].isna()] = old.strftime('%Y-%m-%d')
    Hist_BO_Mod['BF_Confirmation_Date'][Hist_BO_Mod['BF_Confirmation_Date'].isna()] = '19000101'
    Hist_BO_Mod['BF_Confirmation_Date'][Hist_BO_Mod['BF_Confirmation_Date']==0.0] = '19000101'
    Hist_BO_Mod['BF_Confirmation_Date'][Hist_BO_Mod['BF_Status'] != 'CONFI'] = '19000101'
    Hist_BO_Mod['BF_Cancellation_date'][~Hist_BO_Mod['BF_Cancellation_date'].isna()] = pd.to_datetime(Hist_BO_Mod['BF_Cancellation_date'][~Hist_BO_Mod['BF_Cancellation_date'].isna()]).dt.strftime('%Y-%m-%d')
    print('Fechas - Actualizadas')

    check_duplicados = Hist_BO_Mod[Hist_BO_Mod['Last_Change_Date'] != Hist_BO_Mod['Fecha']]
    print('check_duplicados - Actualizado')
    Hist_BO_Mod['Creation_date'][Hist_BO_Mod['Creation_date'].isna()] = old.strftime('%Y-%m-%d')
    Hist_BO_Mod['Start_date'][Hist_BO_Mod['Start_date'].isna()] = old.strftime('%Y-%m-%d')
    print('check_start_date - Actualizado')
    Hist_BO_Mod['End_date'][Hist_BO_Mod['End_date'].isna()] = old.strftime('%Y-%m-%d')
    print('check_end_date - Actualizado')

    # Hist_BO_Mod['BF_Confirmation_Date'][Hist_BO_Mod['BF_Confirmation_Date'].str.len() ==8] = Hist_BO_Mod['BF_Confirmation_Date'][Hist_BO_Mod['BF_Confirmation_Date'].str.len() ==8].astype(int).astype(str).str[:4]+Hist_BO_Mod['BF_Confirmation_Date'][Hist_BO_Mod['BF_Confirmation_Date'].str.len() ==8].astype(int).astype(str).str[4:6]+Hist_BO_Mod['BF_Confirmation_Date'][Hist_BO_Mod['BF_Confirmation_Date'].str.len() ==8].astype(int).astype(str).str[6:]
    Hist_BO_Mod['BF_Confirmation_Date'][Hist_BO_Mod['BF_Confirmation_Date'].str.len()==10] = Hist_BO_Mod['BF_Confirmation_Date'][Hist_BO_Mod['BF_Confirmation_Date'].str.len()==10].str[:4]+Hist_BO_Mod['BF_Confirmation_Date'][Hist_BO_Mod['BF_Confirmation_Date'].str.len()==10].str[5:7]+Hist_BO_Mod['BF_Confirmation_Date'][Hist_BO_Mod['BF_Confirmation_Date'].str.len()==10].str[8:]
    Hist_BO_Mod['BF_Confirmation_Date'] = Hist_BO_Mod['BF_Confirmation_Date'].astype(float).astype(int).astype(str).str[:4]+"-"+Hist_BO_Mod['BF_Confirmation_Date'].astype(float).astype(int).astype(str).str[4:6]+"-"+Hist_BO_Mod['BF_Confirmation_Date'].astype(float).astype(int).astype(str).str[6:]
    Hist_BO_Mod['BF_Cancellation_date'][Hist_BO_Mod['BF_Cancellation_date'].isna()] = old.strftime('%Y-%m-%d')
    Hist_BO_Mod['BF_Cancellation_date'] = Hist_BO_Mod['BF_Cancellation_date'].astype('datetime64[ns]').dt.strftime('%Y-%m-%d')
    Hist_BO_Mod['Deadline'].fillna('19000101', inplace=True)
    Hist_BO_Mod['Deadline'][Hist_BO_Mod['Deadline']==0] = '19000101'
    Hist_BO_Mod['Deadline'][Hist_BO_Mod['Deadline'].str.len() ==10] = Hist_BO_Mod['Deadline'][Hist_BO_Mod['Deadline'].str.len() ==10].astype(str).str[:4]+Hist_BO_Mod['Deadline'][Hist_BO_Mod['Deadline'].str.len() ==10].astype(str).str[5:7]+Hist_BO_Mod['Deadline'][Hist_BO_Mod['Deadline'].str.len() ==10].astype(str).str[8:]
    Hist_BO_Mod['Deadline'] = Hist_BO_Mod['Deadline'].astype(str).str[:4]+"-"+Hist_BO_Mod['Deadline'].astype(str).str[4:6]+"-"+Hist_BO_Mod['Deadline'].astype(str).str[6:]
    Hist_BO_Mod['Data_tracking'].fillna('19000101', inplace=True)
    Hist_BO_Mod['Data_tracking'][Hist_BO_Mod['Data_tracking']==0] = '19000101'
    Hist_BO_Mod['Data_tracking'][Hist_BO_Mod['Data_tracking'].str.len() ==10] = Hist_BO_Mod['Data_tracking'][Hist_BO_Mod['Data_tracking'].str.len() ==10].astype(str).str[:4]+Hist_BO_Mod['Data_tracking'][Hist_BO_Mod['Data_tracking'].str.len() ==10].astype(str).str[5:7]+Hist_BO_Mod['Data_tracking'][Hist_BO_Mod['Data_tracking'].str.len() ==10].astype(str).str[8:]
    Hist_BO_Mod['Data_tracking'] = Hist_BO_Mod['Data_tracking'].astype(str).str[:4]+'-'+Hist_BO_Mod['Data_tracking'].astype(str).str[4:6]+'-'+Hist_BO_Mod['Data_tracking'].astype(str).str[6:]
    Hist_BO_Mod['CUT_OFF_date'].fillna('19000101', inplace=True)
    Hist_BO_Mod['CUT_OFF_date'][Hist_BO_Mod['CUT_OFF_date']==0] = '19000101'
    Hist_BO_Mod['CUT_OFF_date'][Hist_BO_Mod['CUT_OFF_date'].str.len() ==10] = Hist_BO_Mod['CUT_OFF_date'][Hist_BO_Mod['CUT_OFF_date'].str.len() ==10].astype(str).str[:4]+Hist_BO_Mod['CUT_OFF_date'][Hist_BO_Mod['CUT_OFF_date'].str.len() ==10].astype(str).str[5:7]+Hist_BO_Mod['CUT_OFF_date'][Hist_BO_Mod['CUT_OFF_date'].str.len() ==10].astype(str).str[8:]
    Hist_BO_Mod['CUT_OFF_date'] = Hist_BO_Mod['CUT_OFF_date'].astype(str).str[:4]+"-"+Hist_BO_Mod['CUT_OFF_date'].astype(str).str[4:6]+"-"+Hist_BO_Mod['CUT_OFF_date'].astype(str).str[6:]
    Hist_BO_Mod['Date_last_status_change'][Hist_BO_Mod['Date_last_status_change'].isna()] = old.strftime('%Y-%m-%d')
    Hist_BO_Mod['Date_last_status_change'] = Hist_BO_Mod['Date_last_status_change'].astype('datetime64[ns]').dt.strftime('%Y-%m-%d')
    Hist_BO_Mod['Work_Type'][Hist_BO_Mod['Date_last_status_change']!=Hist_BO_Mod['Fecha']]='Other_Mod'
    print('Fechas - Corregidas')

    Hist_BO = pd.concat([Hist_BO_Creations, Hist_BO_Mod], axis=0)
    Hist_BO.reset_index(inplace=True)
    Hist_BO.drop(['index'], axis=1, inplace=True)
    Hist_BO['Offer_Type'][(Hist_BO['Reservation_id']=='0000000000')&(Hist_BO['Quick_Denial']!='Quick Denial')] = 'KKKKK'
    Hist_BO['Offer_Type'][Hist_BO['BF'].str[:2]=='QD'] = 'Main_offer'
    # Hist_BO['Offer_Type'][Hist_BO['BF'].str[:2]=='MQ'] = 'Main_offer'
    no_valid = Hist_BO[Hist_BO['Offer_Type']=='KKKKK']
    Hist_BO = Hist_BO[Hist_BO['Offer_Type']!='KKKKK']
    print('Limpieza 1')

    Hist_BO[['Fin_Rev', 'Rev_Room', 'Rev_FB', 'Rev_Meeting', 'Rev_Other', 'Total_Rev']] = Hist_BO[['Fin_Rev', 'Rev_Room', 'Rev_FB', 'Rev_Meeting', 'Rev_Other', 'Total_Rev']].fillna(0)
    Hist_BO[['Room', 'FB', 'Meeting', 'Other']] = Hist_BO[['Room', 'FB', 'Meeting', 'Other']].fillna(0)
    Hist_BO['Fin_Rev'][Hist_BO['Fin_Rev']<0] = 0
    Hist_BO['Rev_Room'][Hist_BO['Rev_Room']<0] = 0
    Hist_BO['Rev_FB'][Hist_BO['Rev_FB']<0] = 0
    Hist_BO['Rev_Meeting'][Hist_BO['Rev_Meeting']<0] = 0
    Hist_BO['Rev_Other'][Hist_BO['Rev_Other']<0] = 0
    Hist_BO['Total_Rev'][Hist_BO['Total_Rev']<0] = 0
    Hist_BO['Room'][Hist_BO['Room']<0] = 0
    Hist_BO['FB'][Hist_BO['FB']<0] = 0
    Hist_BO['Meeting'][Hist_BO['Meeting']<0] = 0
    Hist_BO['Other'][Hist_BO['Other']<0] = 0
    Hist_BO['Room'][Hist_BO['Room']!=0] = 1
    Hist_BO['FB'][Hist_BO['FB']!=0] = 1
    Hist_BO['Meeting'][Hist_BO['Meeting']!=0] = 1
    Hist_BO['Other'][Hist_BO['Other']!=0] = 1
    Hist_BO['Room_night'] = Hist_BO['Room_night'].fillna('0000000000').astype(float).astype(int)
    Hist_BO['Room_night'][Hist_BO['Room_night']<0] = 0
    print('Limpieza 2')

    Hist_BO['Main_Hotel_id'][(Hist_BO['Main_Hotel_id'].isna())&(Hist_BO['Offer_Type']!='Second_Offer')&(Hist_BO['Offer_Type']!='Multihotel')] = Hist_BO['Hotel_id']
    Hist_BO['Main_Hotel_id'][(Hist_BO['Main_Hotel_id'].isna())&(Hist_BO['Offer_Type']=='Second_Offer')] = 'Second_Offer'
    Hist_BO['Client_id'].fillna('0000000000', inplace=True)
    Hist_BO['Client_id'][Hist_BO['Client_id'].astype(str).str[:2]=='MB'] = '0000000000'
    Hist_BO['Client_id'][Hist_BO['Client_id'].astype(str).str[:1]=='D'] = '0000000000'
    Hist_BO['Client_id'][Hist_BO['Client_id'].astype(str).str[:1]=='G'] = '0000000000'
    Hist_BO['Client_id'][Hist_BO['Client_id'].astype(str).str[:1]=='B'] = '0000000000'
    Hist_BO['Client_id'][Hist_BO['Client_id']=='[\u200e14/\u200e01/\u200e'] = '0000000000'
    Hist_BO['Client_id'] = Hist_BO['Client_id'].astype(str).str.zfill(10).str[:10]
    Hist_BO['Company_Responsible_id'].fillna('0000000000', inplace=True)
    Hist_BO['Company_Responsible_id'][Hist_BO['Company_Responsible_id'].str[:1]=='S'] = '0000000000'
    Hist_BO['Company_Responsible_id'][Hist_BO['Company_Responsible_id'].str[:1]=='J'] = '0000000000'
    Hist_BO['Company_Responsible_id'][Hist_BO['Company_Responsible_id'].str[:1]=='B'] = '0000000000'
    Hist_BO['Company_Responsible_id'][Hist_BO['Company_Responsible_id'].str[:1]=='¿'] = '0000000000'
    Hist_BO['Company_Responsible_id'][Hist_BO['Company_Responsible_id'].str[:1]=='K'] = '0000000000'
    Hist_BO['Company_Responsible_id'] = Hist_BO['Company_Responsible_id'].astype(str).str[:10]
    Hist_BO['Company_Responsible_id'][Hist_BO['Company_Responsible_id'].str[-2:-1]=='.'] = Hist_BO['Company_Responsible_id'][Hist_BO['Company_Responsible_id'].str[-2:-1]=='.'].astype(float).astype(int).astype(str).str.zfill(10)
    Hist_BO['CRS_id'].fillna('0000000000', inplace=True)
    Hist_BO['CRS_id'] = Hist_BO['CRS_id'].astype(float).astype(int).astype(str).str.zfill(10).str[:10]
    print('Limpieza 3')

    Hist_BO['BF_Status'][(Hist_BO['BF'].str[:2]=='MQ')&(Hist_BO['Quick_Denial'].isna())] = 'Pending'
    Hist_BO['BF_Status'][(Hist_BO['BF'].str[:2]=='MQ')&(~Hist_BO['Quick_Denial'].isna())] = 'Quick_Denial'
    Hist_BO['BF_Status'][Hist_BO['BF_Status'].isna()] = 'KKKKK'
    no_status = Hist_BO[Hist_BO['BF_Status'] == 'KKKKK']
    print('Limpieza 4')

    Hist_BO['MultiHotel'].fillna('No', inplace=True)
    Hist_BO['MultiHotel'][Hist_BO['MultiHotel']=='X'] = 'Multihotel'
    Hist_BO['Creator_id'].fillna('0000000000', inplace=True)
    Hist_BO['Creator_id'][Hist_BO['BF'].str[:2]=='MQ'] = Hist_BO['QT_Creator'][Hist_BO['BF'].str[:2]=='MQ']
    Hist_BO['Creator_id'][Hist_BO['BF'].str[:2]!='QD'] = Hist_BO['Creator_id'][Hist_BO['BF'].str[:2]!='QD'].astype(float).astype(int).astype(str).str.zfill(10)
    # Hist_BO['Creator_id'][Hist_BO['Creator_id'].astype(str).str[:1]=='E'] = '0000000000'
    # Hist_BO['Creator_id'][Hist_BO['Creator_id'].astype(str).str[:1]=='H'] = '0000000000'
    # Hist_BO['Creator_id'][Hist_BO['Creator_id'].astype(str).str[:1]=='I'] = '0000000000'
    # Hist_BO['Creator_id'][Hist_BO['Creator_id'].astype(str).str[:1]=='X'] = '0000000000'
    # Hist_BO['Creator_id'] = Hist_BO['Creator_id'].astype(float).astype(int).astype(str).str.zfill(10)
    Hist_BO['Second_Creator_id'].fillna('0000000000', inplace=True)
    Hist_BO['Second_Creator_id'] = Hist_BO['Second_Creator_id'].astype(float).astype(int).astype(str).str.zfill(10)
    Hist_BO['Main_Creator_id'] =  (Hist_BO['Second_Creator_id']).astype(str)
    Hist_BO['Main_Creator_id'][Hist_BO['Creator_id'] == Hist_BO['Second_Creator_id']] =  (Hist_BO['Creator_id'][Hist_BO['Creator_id'] == Hist_BO['Second_Creator_id']]).astype(str)
    Hist_BO['Main_Creator_id'][Hist_BO['Second_Creator_id']=='0000000000'] =  (Hist_BO['Creator_id'][Hist_BO['Second_Creator_id']=='0000000000']).astype(str)
    Hist_BO['Main_Creator_id'][Hist_BO['BF'].str[:2]!='QD'] = Hist_BO['Main_Creator_id'][Hist_BO['BF'].str[:2]!='QD'].astype(float).astype(int).astype(str).str.zfill(10)
    Hist_BO['Main_Creator_id'][(Hist_BO['BF'].str[:2]=='QD')&(Hist_BO['Main_Creator_id'].str[:1]!='E')&(Hist_BO['Main_Creator_id'].str[:1]!='X')&(Hist_BO['Main_Creator_id'].str[:1]!='I')]= "E"+Hist_BO['Main_Creator_id'][(Hist_BO['BF'].str[:2]=='QD')&(Hist_BO['Main_Creator_id'].str[:1]!='E')&(Hist_BO['Main_Creator_id'].str[:1]!='X')&(Hist_BO['Main_Creator_id'].str[:1]!='I')].astype(float).astype(int).astype(str).str.zfill(11)

    print('Limpieza 5')

    Hist_BO['Creator_Center'][Hist_BO['Creator_Center'].isna()] = 'KKKKK'
    Hist_BO['Previous_Status'][Hist_BO['Previous_Status'].isna()] = 'KKKKK'
    Hist_BO['Previous_Status'][Hist_BO['Previous_Status'] == 0] = 'KKKKK'
    Hist_BO['Previous_Status'][(Hist_BO['Previous_Status'] =="CONFI")] = 'Confirmed'
    Hist_BO['Previous_Status'][(Hist_BO['Previous_Status'] =='OFFER')] = 'Offer'
    Hist_BO['Previous_Status'][(Hist_BO['Previous_Status'] =='TENTA')] = 'Tentative'
    Hist_BO['Previous_Status'][(Hist_BO['Previous_Status'] =='OPTIO')] = 'Optional'
    Hist_BO['Previous_Status'][(Hist_BO['Previous_Status'] =='SCOPT')] = 'Second Option'
    print('Limpieza 6')

    Hist_BO['Reservation_status'].fillna('KKKKK', inplace=True)
    Hist_BO['Reservation_status'][Hist_BO['Reservation_status']==0] = 'KKKKK'
    Hist_BO['Reservation_cancelled_by'].fillna('000000000000', inplace=True)
    Hist_BO['Reservation_cancelled_by'] = Hist_BO['Reservation_cancelled_by'].str[-12:]
    Hist_BO['AH_Main_Customer_PID'].fillna('0000000000', inplace=True)
    Hist_BO['AH_Main_Customer_PID'] = Hist_BO['AH_Main_Customer_PID'].astype(float).astype(int).astype(str).str.zfill(10)
    Hist_BO['Branch_main_customer'].fillna('0000000000', inplace=True)
    Hist_BO['Branch_main_customer'] = Hist_BO['Branch_main_customer'].astype(float).astype(int).astype(str).str.zfill(10)
    Hist_BO['BID_AH'].fillna('0000000000', inplace=True)
    Hist_BO['BID_AH'] = Hist_BO['BID_AH'].astype(float).astype(int).astype(str).str.zfill(10)
    Hist_BO['BID_AH'][Hist_BO['BID_AH'].astype(int)<0] = '9999999999'
    Hist_BO['BID_Agency_AH'].fillna('0000000000', inplace=True)
    Hist_BO['BID_Agency_AH'] = Hist_BO['BID_Agency_AH'].astype(float).astype(int).astype(str).str.zfill(10)
    Hist_BO['BID_Intermediary_AH'].fillna('0000000000', inplace=True)
    Hist_BO['BID_Intermediary_AH'] = Hist_BO['BID_Intermediary_AH'].astype(float).astype(int).astype(str).str.zfill(10)
    Hist_BO['Quotation_ID'].fillna('000000000000', inplace=True)
    Hist_BO['Quick_Denial'].fillna('0000000000', inplace=True)
    Hist_BO['Quick_Denial'][Hist_BO['Quick_Denial']==0] = '0000000000'
    Hist_BO['Net'].fillna(0, inplace=True)
    Hist_BO['Workflow_Step'].fillna('0000000000', inplace=True)
    Hist_BO['Cxl_reason_id'].fillna('0000000000', inplace=True)
    Hist_BO['Cxl_reason_id'][Hist_BO['Cxl_reason_id']==0] = '0000000000'
    Hist_BO['QT_Creator'].fillna('0000000000', inplace=True)
    Hist_BO['QT_Creator'] = Hist_BO['QT_Creator'].astype(float).astype(int).astype(str).str.zfill(10)
    Hist_BO['Canc_Reason_ID'].fillna('0000000000', inplace=True)
    Hist_BO['BF_PAX'].fillna(0, inplace=True)
    Hist_BO['BF_PAX'][Hist_BO['BF_PAX']=='0000000000'] = 0
    print('Limpieza 7')

    Hist_BO['BF_Commercial_Client_Name'].fillna('KKKKK', inplace=True)
    Hist_BO['BF_Company_Responsible_Name'].fillna('KKKKK', inplace=True)
    Hist_BO['BF_CRS_Name'].fillna('KKKKK', inplace=True)
    Hist_BO['Booking_group_name'].fillna('KKKKK', inplace=True)
    Hist_BO['Event_Type'].fillna('KKKKK', inplace=True)
    Hist_BO['Rate'].fillna('KKKKK', inplace=True)
    Hist_BO['Second_Creator_Center'].fillna('KKKKK', inplace=True)
    Hist_BO['Organizer_center'].fillna('KKKKK', inplace=True)
    Hist_BO['Market_Segment'].fillna('KKKKK', inplace=True)
    Hist_BO['Subsegment'].fillna('KKKKK', inplace=True)
    Hist_BO['Channel_ID'].fillna('KKKKK', inplace=True)
    Hist_BO['SubChannel_id'].fillna('KKKKK', inplace=True)
    Hist_BO['Language'].fillna('KKKKK', inplace=True)
    Hist_BO['Promotion'].fillna('KKKKK', inplace=True)
    Hist_BO['Contact_person'].fillna('KKKKK', inplace=True)
    Hist_BO['Contact_Tel'].fillna('KKKKK', inplace=True)
    Hist_BO['Email'].fillna('KKKKK', inplace=True)
    Hist_BO['Serie'].fillna('KKKKK', inplace=True)
    Hist_BO['Hotel_id'].fillna('KKKKK', inplace=True)
    Hist_BO['External_reference'].fillna('KKKKK', inplace=True)
    Hist_BO['AH_Main_Customer_Name'].fillna('KKKKK', inplace=True)
    Hist_BO['Branch_name'].fillna('KKKKK', inplace=True)
    Hist_BO['BID_AH_Name'].fillna('KKKKK', inplace=True)
    Hist_BO['BID_Agency_AH_Name'].fillna('KKKKK', inplace=True)
    Hist_BO['BID_Intermediary_AH_Name'].fillna('KKKKK', inplace=True)
    Hist_BO['BF_Promotion'].fillna('KKKKK', inplace=True)
    Hist_BO['Remarks'].fillna('KKKKK', inplace=True)
    Hist_BO['QT_Creator_name'].fillna('KKKKK', inplace=True)
    Hist_BO['Canc_Reason_Text'].fillna('KKKKK', inplace=True)
    Hist_BO['Remark_QD'].fillna('KKKKK', inplace=True)
    Hist_BO['Serie_Offer_BF'].fillna('KKKKK', inplace=True)
    # Hist_BO['Origin'] = 'KKKKK'
    column_to_move = Hist_BO.pop('Origin')
    Hist_BO.insert(len(Hist_BO.columns)-1, 'Origin', column_to_move)
    column_to_move = Hist_BO.pop('Main_Creator_id')
    Hist_BO.insert(len(Hist_BO.columns)-1, 'Main_Creator_id', column_to_move)
    Hist_BO['Origin'].fillna(0, inplace=True)
    Hist_BO['Origin'] = Hist_BO['Origin'].astype(float).astype(int)
    Hist_BO['Origin'][Hist_BO['Origin']==9] = 'QT'
    Hist_BO['Origin'][Hist_BO['Origin']!='QT'] = 'KKKKK'
    print('Limpieza 8')

    Call_db = preparar_gbq(Hist_BO)
    pandas_gbq.to_gbq(Call_db, destination_table='BO.Hist_BO_Clean_Full', project_id='nh-gem', if_exists='append')
    print('DONE!!')

##### ------------------------------------------------------------------------------------- #####

### ----- 4. Check_Meetings_GGC: Function to check the data loaded to Google Cloud Every Week Also we can Check the historical of dates in which we have uploaded the data. ----- ###


def Check_Meetings_GGC(modo= None):

        """
        Function to check the data loaded to Google Cloud Every Week Also we can Check the historical of dates in which we have uploaded the data.

        Args:
         - "Yes":        To view the historical
         - Blank:        you will have to put dates to check like for eixample:
                 - First Input:  '2024-07-30'
                 - Second Input:         '2024-07-23'
                
        """


        if modo == "Yes":
                df_view_dates_load = pandas_gbq.read_gbq("""SELECT Load_Date, count(1) as contador 
                                FROM `nh-ops.Meetings.BO_MT_Inputs_Partitioned` 
                                WHERE Load_Date >'2024-01-01'
                                GROUP BY 1
                                ORDER BY 1 DESC""", project_id="nh-ops")
                print(df_view_dates_load)
        else:
                TW = input("Indica Fecha más reciente")
                LW = input("Indica Fecha anterior")
                df = pandas_gbq.read_gbq("""with datos as (

                                        select right(BF_id,2) as Term, count(1) as Contador from `nh-ops.Meetings.BO_MT_Inputs_Partitioned` where Load_Date= '"""+TW+"""'  and Obs_Key='TODAY' group by 1 order by 1 asc),
                                
                                        LW as (select right(BF_id,2) as Term_LW, count(1) as Contador_LW from `nh-ops.Meetings.BO_MT_Inputs_Partitioned` where Load_Date= '"""+LW+"""' and Obs_Key='TODAY' group by 1 order by 1 asc)
                                
                                        select * from datos left join LW on term=term_LW """, project_id="nh-ops" )
                                    

                return (df)


##### ------------------------------------------------------------------------------------- #####

### ----- 5. Check_input_Cvent: Function to Check the data from Cvent per month and year we have received and uploaded to Cloud ----- ###


def Check_input_Cvent():

    """
    Function to Check the data from Cvent per month and year we have received and uploaded to Cloud
    
        Args: "NO ARGS"
    """

    check = pandas_gbq.read_gbq("""
                             SELECT EXTRACT(MONTH FROM CAST(RFP_RECEIVED_DATE AS DATE)) AS MONTH,EXTRACT(YEAR FROM CAST(RFP_RECEIVED_DATE AS DATE)) AS YEAR, COUNT(1) AS CONTEO, 
                            FROM `nh-gem.CVENT.Received_RFP`
                            GROUP BY 1,2 ORDER BY 2 DESC,1 DESC""",
                             project_id="nh-gem"
                            )
    return(check)


##### ------------------------------------------------------------------------------------- #####

### ----- 6. Cargas_Agent_CRO: Function to Reload data for CRO Agents, when for x reason there was not data ----- ###


def Cargas_Agent_CRO(start_date=datetime(2024, 7, 31),end_date=datetime(2024, 7, 31),agent=str):

    """
    Function to Reload data for CRO Agents, when for x reason there was not data

        Args: 
            - Start: By default: datetime(2024,7,31) Change date keeping datetime function
            - End: By default: date(2024,7,31) Change date keeping datetime function
            - Agent: str, number of the agent including the firs letter. Ex: 'E00000269337'
    """


    def date_range(start, end):
        delta = end - start 
        days = [(start + timedelta(days=i)).strftime('%d%m%Y') for i in range(delta. days + 1)]
        days_with_format = [(start + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(delta. days + 1)]
        months = [(start + timedelta(days=i)).strftime('%m') for i in range(delta. days + 1)]
        years = [(start + timedelta(days=i)).strftime('%Y') for i in range(delta. days + 1)]
        return days, months, years, days_with_format

    agente = agent
    start_date = start_date
    end_date = end_date
    dias = date_range(start_date, end_date)

    ## DEFINIMOS LISTA CON MESES PARA IR A LA UBICACION EXACTA Y CARGAMOS EL DIRECTORIO DE FILES ##
    meses = ['01. ENERO', '02. FEBRERO','03. MARZO','04. ABRIL','05. MAYO','06. JUNIO','07. JULIO','08. AGOSTO','09. SEPTIEMBRE','10. OCTUBRE','11. NOVIEMBRE','12. DICIEMBRE']
    datos = pd.DataFrame(columns=['RS_HOTEL', 'Hotel_Currency', 'RS_RESERVA',
        'Status_Reservation_Origin_ID', 'RS_FECHA_RESERVA', 'RS_LLEGADA',
        'RS_SALIDA', 'RS_TIPO_HAB', 'RO_Room_type_generic_upgrade',
        'Flag_Room_Upgrade', 'RS_REGIMEN', 'RS_TARIFA', 'RS_MARKET_SEGMENT',
        'RS_MARKET_SUBSEGMENT', 'RS_CANAL', 'RS_SUBCANAL',
        'RO_Commercial_Subchannel', 'RS_CONTACTO', 'RS_MAIN_CUSTOMER',
        'RS_COMPANY_ID', 'RS_CRS', 'RO_Reservation_Done_by', 'US_RES_BY',
        'USER_GROUP', 'XBOOKING_FILE_ID', 'QUEUE_CRO', 'XRESERVA_GRP_ID',
        'RO_Contact_person', 'Room_Nights', 'Room_Nights_Cancellation',
        'Room_Nights_No_Show', 'Room_Nights_Ok', 'Total_Book_Revenue_FIN_EUR',
        'Book_Room_Revenue_EUR', 'Book_Breakfast_Revenue_EUR',
        'Cancelled_Book_Revenue_EUR', 'No_Show_Book_Revenue_EUR',
        'Total_Other_Revenue_FIN_EUR_new', 'Total_Book_Revenue_FIN_LC',
        'Book_Room_Revenue_LC', 'Book_Breakfast_Revenue_LC',
        'Cancelled_Book_Revenue_LC', 'No_Show_Book_Revenue_LC',
        'Total_Other_Revenue_FIN_LC_new', 'RO_Reservation_type',
        'RO_Branch_Company_Responsible_TMS', 'RO_Guarantee_Category',
        'Creation_Time_Origin', 'Creation_Date_Origin_CET',
        'Creation_Time_Origin_CET'])

    for i in range(len(dias[3])):
        load_day =      int(dias[3][i][-2:])
        load_month =    dias[1][i]
        load_year =     dias[2][i]

    files = os.listdir(fr"V:\Central reservations office\Area-3\SOPORTE OPERACIONES\\01. INFORMES DIARIOS\\{load_year}\\{meses[int(load_month)-1]} {load_year}\\{load_day}")
    print(load_day)
    for file in files: 
        if file[:7]=='CRO_TMS':
            file2 = fr"V:\Central reservations office\Area-3\SOPORTE OPERACIONES\\01. INFORMES DIARIOS\\{load_year}\\{meses[int(load_month)-1]} {load_year}\\{load_day}\\{file}"
            TMS = pd.read_excel(file2,dtype=str).replace(['NaN','None','NaT',' ','nan',nan],[None,None,None,None,None,None]).rename(columns={'Hotel Currency':'Hotel_Currency',
                                                                                                                                                    'Status Reservation Origin ID':'Status_Reservation_Origin_ID',
                                                                                                                                                    'RO Room type generic (upgrade)':'RO_Room_type_generic_upgrade',
                                                                                                                                                    'RO Commercial Subchannel':'RO_Commercial_Subchannel',
                                                                                                                                                    'RO Reservation Done By':'RO_Reservation_Done_by',
                                                                                                                                                    'RO Contact person':'RO_Contact_person',
                                                                                                                                                    'Room Nights':'Room_Nights',
                                                                                                                                                    'Room Nights CXL':'Room_Nights_Cancellation',
                                                                                                                                                    'Room Nights No Show':'Room_Nights_No_Show',
                                                                                                                                                    'Room Nights OK':'Room_Nights_Ok',
                                                                                                                                                    'Total Book Revenue FIN EUR':'Total_Book_Revenue_FIN_EUR',
                                                                                                                                                    'Book Room Revenue EUR':'Book_Room_Revenue_EUR',
                                                                                                                                                    'Book Breakfast Revenue EUR':'Book_Breakfast_Revenue_EUR',
                                                                                                                                                    'Cancelled Book Revenue EUR':'Cancelled_Book_Revenue_EUR',
                                                                                                                                                    'No Show Book Revenue EUR':'No_Show_Book_Revenue_EUR',
                                                                                                                                                    'Total Other Revenue FIN EUR (new)':'Total_Other_Revenue_FIN_EUR_new',
                                                                                                                                                    'Total Book Revenue FIN LC':'Total_Book_Revenue_FIN_LC',
                                                                                                                                                    'Book Room Revenue LC':'Book_Room_Revenue_LC',
                                                                                                                                                    'Book Breakfast Revenue LC':'Book_Breakfast_Revenue_LC',
                                                                                                                                                    'Cancelled Book Revenue LC':'Cancelled_Book_Revenue_LC',
                                                                                                                                                    'No Show Book Revenue LC':'No_Show_Book_Revenue_LC',
                                                                                                                                                    'Total Other Revenue FIN LC (new)':'Total_Other_Revenue_FIN_LC_new',
                                                                                                                                                    'RO Reservation type':'RO_Reservation_type',
                                                                                                                                                    'RO Branch Company Responsible TMS':'RO_Branch_Company_Responsible_TMS',
                                                                                                                                                    'RO Guarantee Category':'RO_Guarantee_Category',
                                                                                                                                                    'Creation Time Origin':'Creation_Time_Origin',
                                                                                                                                                    'Creation Date Origin CET':'Creation_Date_Origin_CET',
                                                                                                                                                    'Creation Time Origin CET':'Creation_Time_Origin_CET'})
            TMS['RS_RESERVA'] = TMS['RS_RESERVA'].astype(float).astype(int)
            TMS = TMS.astype(str)
            TMS.replace(['NaN','None','NaT',' ','nan',nan],[None,None,None,None,None,None], inplace=True)
            TMS = TMS[TMS['RO_Reservation_Done_by']==agente]
            # datos = datos.append(TMS)
            datos = pd.concat([datos,TMS],ignore_index=True)


    datos.to_gbq(destination_table='TMS.b_Reservation_entry_data_raw_temporal',project_id='nh-cro-forecast',if_exists='replace')    

##### ------------------------------------------------------------------------------------- #####

### ----- 7. upload_Arrivals_Origins_QtAllStatus: Function to load data from BO to update Group Lead Management Report with QT_Arrivals, Creation_Origin and QT_ALL_STATUS ----- ###



def upload_Arrivals_Origins_QtAllStatus(path,files):

    """
    Function to load data from BO to update Group Lead Management Report with QT_Arrivals, Creation_Origin and QT_ALL_STATUS. 
    With the second argument you will be able to choos if you want to upload all 3 files, or upload individually.

        Args: 
            - Path with raw string format
            - All: you will upload the 3 files.
            - QT_ARRIVALS
            - CREATION ORIGIN
            - QT_ALL_STATUS
    """


    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"F:\BI_for_Reservations\GCP Python credentials\nh-gem.json"

    def preparar_gbq(dataset):
        Call = dataset.astype(str)
        dictionary = {} 
        [dictionary.update({f'{i}':str}) for i in dataset.columns]
        Call_db = Call.astype(dictionary)
        return Call_db
    
    if files == "All":
    ## SUBIMOS QT_ARRIVALS

        QT_ARRIVALS = pd.read_excel(path+r'\QT_Arrivals.xlsx', engine='openpyxl')
        QT_ARRIVALS.columns = ['Booking_File_ID', 'Creation_date', 'Arrival_date', 'Departure_date',
            'Quotation_ID', 'Rate', 'Creator', 'Creator_Name', 'Workflow_step',
            'Quick_Denial', 'CXL_Reason_Type', 'Canc_Type_Text',
            'Cancellation_Reason_identifier', 'Canc_Reason_Text', 'Main_Customer',
            'Remarks_QD', 'Item', 'Net', 'Quantity', 'Item_Price',
            'Room_Amount', 'Hotel_Id']
        Call_db = preparar_gbq(QT_ARRIVALS)
        print('Uploading QT_ARRIVALS')
        pandas_gbq.to_gbq(Call_db, destination_table='BO.QT_Arrivals',project_id='nh-gem', if_exists='append')
        print('QT_ARRIVALS Uploaded')

        ## SUBIMOS CREATION ORIGIN

        reservas = pd.read_excel(path+r'\Creation_Origin.xlsx').iloc[:,:]
        reservas.columns = ['BF','Origin','Creation_date']
        reservas[['BF','Creation_date']]
        Call_db = preparar_gbq(reservas)
        print("Uploading Creation Origin")
        pandas_gbq.to_gbq(Call_db, destination_table='BO.quotation_tool',project_id='nh-gem', if_exists='append')
        print("Creation Origin Uploaded")

        ## SUBIMOS QT_ALL_STATUS

        reservas = pd.read_excel(path+r'\QT_All_STATUS.xlsx', engine="openpyxl").iloc[1:,1:]
        reservas.columns = ['Business_Unit_D',	'Check_in_Date_D',	'Date_Creation_D',	'Name_Creator_D',	'Quotation_Id_D',	'Status_D',	'Status_Date_D',	'Status_Description_D',	'Status_Hotel_D',	'Status_Number_D',	'Status_Time_D',	'User_Creator_D']
        reservas['Status_Date_D'] = reservas['Status_Date_D'].str[:4] + '-' + reservas['Status_Date_D'].str[4:6] + '-' +  reservas['Status_Date_D'].str[6:]
        Call_db = preparar_gbq(reservas)
        print("Uploading QT_ALL_STATUS")
        pandas_gbq.to_gbq(Call_db, destination_table='BO.QT_ALL_STATUS',project_id='nh-gem', if_exists='append')
        print('QT_ALL_STATUS Uploaded')

    elif files == 'QT_ARRIVALS':
             ## SUBIMOS QT_ARRIVALS

        QT_ARRIVALS = pd.read_excel(path+r'\QT_Arrivals.xlsx', engine='openpyxl')
        QT_ARRIVALS.columns = ['Booking_File_ID', 'Creation_date', 'Arrival_date', 'Departure_date',
            'Quotation_ID', 'Rate', 'Creator', 'Creator_Name', 'Workflow_step',
            'Quick_Denial', 'CXL_Reason_Type', 'Canc_Type_Text',
            'Cancellation_Reason_identifier', 'Canc_Reason_Text', 'Main_Customer',
            'Remarks_QD', 'Item', 'Net', 'Quantity', 'Item_Price',
            'Room_Amount', 'Hotel_Id']
        Call_db = preparar_gbq(QT_ARRIVALS)
        print('Uploading QT_ARRIVALS')
        pandas_gbq.to_gbq(Call_db, destination_table='BO.QT_Arrivals',project_id='nh-gem', if_exists='append')
        print('QT_ARRIVALS Uploaded')
    
    elif files == 'CREATION ORIGIN':
         ## SUBIMOS CREATION ORIGIN

        reservas = pd.read_excel(path+r'\Creation_Origin.xlsx').iloc[:,:]
        reservas.columns = ['BF','Origin','Creation_date']
        reservas[['BF','Creation_date']]
        Call_db = preparar_gbq(reservas)
        print("Uploading Creation Origin")
        pandas_gbq.to_gbq(Call_db, destination_table='BO.quotation_tool',project_id='nh-gem', if_exists='append')
        print("Creation Origin Uploaded")
    
    elif files == 'QT_ALL_STATUS':
        ## SUBIMOS QT_ALL_STATUS
        
        reservas = pd.read_excel(path+r'\QT_All_STATUS.xlsx', engine="openpyxl").iloc[1:,1:]
        reservas.columns = ['Business_Unit_D',	'Check_in_Date_D',	'Date_Creation_D',	'Name_Creator_D',	'Quotation_Id_D',	'Status_D',	'Status_Date_D',	'Status_Description_D',	'Status_Hotel_D',	'Status_Number_D',	'Status_Time_D',	'User_Creator_D']
        reservas['Status_Date_D'] = reservas['Status_Date_D'].str[:4] + '-' + reservas['Status_Date_D'].str[4:6] + '-' +  reservas['Status_Date_D'].str[6:]
        Call_db = preparar_gbq(reservas)
        print("Uploading QT_ALL_STATUS")
        pandas_gbq.to_gbq(Call_db, destination_table='BO.QT_ALL_STATUS',project_id='nh-gem', if_exists='append')
        print('QT_ALL_STATUS Uploaded')
         
         
         
### ----- 8. Upload Cvent Data: Function to upload to Cloud the data we receive from Cvent, and also to update Database and and WordCloud ----- ###




### ----- 9. Upload_Various_TrueIt_Data_Days: Function to upload data from the bucket of Trueit when we have to upload more than one day ----- ###

def TrueItUpload(path_json_google_credential,year,month,start_day,end_day,bucket_number):
    """
    Function to upload data from Trueit when we need to upload more than one day.

        Args:
            - path_json_google_credential: It must be in r format.
            - year: int. 
            - month: str, (01,02,03,04,05,06,07,08,09,10,11,12)
            - start_day: int, Day of when the file has been uploaded to the bucket (1,2,3,4,5,6,7,8,9,10....)
            - end_day: int, Day of when the file has been uploaded to the bucket (1,2,3,4,5,6,7,8,9,10....)
            - bucket_number: int, number of the bucket we have in the .py with which we upload the data to google
    """
     
     # Credentials to extract data from the Bucket
    json = path_json_google_credential
    fs = gcsfs.GCSFileSystem(project='nh-cro-forecast', token = json)

    #DEFINIMOS AÑO, MES E INICIO DE DIA Y FINAL DE DIA
    Year = str(year)
    print('Año: ',Year)
    time.sleep(0.5)
    Month = str(month)
    print("Mes: ",Month)
    time.sleep(0.5)

    inicio_dia = str(start_day)
    print("Día inicio:", inicio_dia)
    time.sleep(0.5)

    fin_dia = str(end_day)
    print("Día fin:", fin_dia)
    time.sleep(0.5)

# INDICAMOS NUMERO DE QUERY QUE QUEREMOS EJECUTAR
    Query_number =  bucket_number
#### PROCESS ####

    if Query_number == 1:

        for i in range(int(inicio_dia),int(fin_dia)+1):
                if i <10: 
                    Day = "0"+str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('Traffic_Calls UPLOADING')
                    with fs.open('trueit_external/Calls_Distribution/Calls_Distribution_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')
                    doc.columns=['Date',
                                'Service',
                                'Campaign',
                                'Campaign_number',
                                'Language',
                                'IVR_option',
                                'Time_slot',
                                'Incoming_calls',
                                'Answered_calls',
                                'Abandoned_less_10s',
                                'Abandoned_greater_10s']
                    doc["Date"] = pd.to_datetime(doc["Date"], format = '%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    Output = doc.astype(str)
                    convert_dict = {'Date':object,
                                    'Service':object,
                                    'Campaign':object,
                                    'Campaign_number':object,
                                    'Language':object,
                                    'IVR_option':object,
                                    'Time_slot':object,
                                    'Incoming_calls':int,
                                    'Answered_calls':int,
                                    'Abandoned_less_10s':int,
                                    'Abandoned_greater_10s':int,
                                    }
                    Call_db = Output.astype(convert_dict)
                    Call_db = Call_db.astype(str)
                    Call_db['Service'] = Call_db['Service'].astype(str)
                    Call_db['Incoming_calls'] = Call_db['Incoming_calls'].astype(int)
                    Call_db['Answered_calls'] = Call_db['Answered_calls'].astype(int)
                    Call_db['Abandoned_less_10s'] = Call_db['Abandoned_less_10s'].astype(int)
                    Call_db['Abandoned_greater_10s'] = Call_db['Abandoned_greater_10s'].astype(int)
                    Call_db.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)
                    # Call_db.to_gbq(destination_table='Evolution.Traffic_Calls',project_id='nh-cro-forecast', if_exists='append')
                    
                else:
                    Day = str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('Traffic_Calls UPLOADING')
                    with fs.open('trueit_external/Calls_Distribution/Calls_Distribution_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')
                    doc.columns=['Date',
                                'Service',
                                'Campaign',
                                'Campaign_number',
                                'Language',
                                'IVR_option',
                                'Time_slot',
                                'Incoming_calls',
                                'Answered_calls',
                                'Abandoned_less_10s',
                                'Abandoned_greater_10s']
                    doc["Date"] = pd.to_datetime(doc["Date"], format = '%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    Output = doc.astype(str)
                    convert_dict = {'Date':object,
                                    'Service':object,
                                    'Campaign':object,
                                    'Campaign_number':object,
                                    'Language':object,
                                    'IVR_option':object,
                                    'Time_slot':object,
                                    'Incoming_calls':int,
                                    'Answered_calls':int,
                                    'Abandoned_less_10s':int,
                                    'Abandoned_greater_10s':int,
                                    }
                    Call_db = Output.astype(convert_dict)
                    Call_db = Call_db.astype(str)
                    Call_db['Service'] = Call_db['Service'].astype(str)
                    Call_db['Incoming_calls'] = Call_db['Incoming_calls'].astype(int)
                    Call_db['Answered_calls'] = Call_db['Answered_calls'].astype(int)
                    Call_db['Abandoned_less_10s'] = Call_db['Abandoned_less_10s'].astype(int)
                    Call_db['Abandoned_greater_10s'] = Call_db['Abandoned_greater_10s'].astype(int)
                    Call_db.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)
                    # Call_db.to_gbq(destination_table='Evolution.Traffic_Calls',project_id='nh-cro-forecast', if_exists='append')

    elif Query_number == 2:
            for i in range(int(inicio_dia),int(fin_dia)+1):
                if i <10: 
                    Day = "0"+str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('Agent_total_breaks UPLOADING')
                    with fs.open('trueit_external/Agent_By_Calls_And_Status/Agent_Total_Breaks_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')
                    doc.columns=['Date',
                                'Agent',
                                'Agent_ID',
                                'Agent_SAP',
                                'Transactions',
                                'Total_calls',
                                'Calls_in',
                                'Calls_out',
                                'Transfer_in',
                                'Transfer_out',
                                'Session',
                                'n_breaks',
                                'Time_break_general',
                                'Available',
                                'Preview',
                                'Time_on_call',
                                'Wrap_up_time',
                                'n_press',
                                'Time_press',
                                'n_sist',
                                'Time_sist',
                                'n_psup',
                                'Time_psup',
                                'n_ndef',
                                'Time_ndef',
                                'n_pfge',
                                'Time_pfge',
                                'n_pterr',
                                'Time_pterr',
                                'Time_administrative',
                                'n_best_buddy_training',
                                'time_best_buddy_training',
                                'n_break',
                                'Time_break',
                                'n_classroom_training',
                                'Time_classroom_training',
                                'n_external_meeting',
                                'Time_external_meeting',
                                'n_internal_meeting',
                                'Time_internal_meeting',
                                'n_manual_dispatching',
                                'Time_manual_dispatching',
                                'n_other_department_gem',
                                'Time_other_department_gem',
                                'n_special_adminwork',
                                'Time_special_adminwork',
                                'n_support',
                                'Time_support',
                                'n_training_on_the_job',
                                'Time_training_on_the_job',
                                'n_visual_rest',
                                'Time_visual_rest',
                                'n_prelogout',
                                'Time_prelogout',
                                'n_unnasociated_dispatching',
                                'Time_unnasociated_dispatching',
                                'n_meeting',
                                'Time_meeting',
                                'n_processing_time',
                                'Time_processing_time',
                                'n_support_supervisor',
                                'Time_support_supervisor',
                                'n_mail_fax',
                                'Time_mail_fax',
                                'n_other_department_individual',
                                'Time_other_deparment_individual',
                                'n_inbox',
                                'Time_inbox',
                                'n_chat',
                                'Time_chat',
                                'n_sdc',
                                'Time_sdc',
                                'n_Followup',
                                'Time_Followup',
                                'Service',
                                'ON_call_hold',
                                'ON_call_active',
                                'N_Assignation',
                                'T_Assignation',
                                'N_Stand_Prio',
                                'T_Stand_Prio',
                                'N_Bulk_and_Prio',
                                'T_Bulk_and_Prio',
                                'N_Overtime',
                                'T_Overtime',
                                'N_Site_Inspection',
                                'T_Site_Inspection', 
                                'N_GEM_Disp', 
                                'T_GEM_Disp',
                                'N_Multidestination',
                                'T_Multidestination',
                                'Number_Audits',
                                'Time_Audits',
                                'Number_Feedbacks',
                                'Time_Feedbacks',
                                'Number_Platforms',
                                'Time_Platforms',
                                'Number_Test',
                                'Time_Test',
                                'Number_Calibracion',
                                'Time_Calibracion', 
                                'Number_Duplicated_y_Spam',
                                'Time_Duplicated_y_Spam',
                                'Number_Break_after_transaction',
                                'Time_Break_after_transaction',
                                'Number_Face_to_Face',
                                'Time_Face_to_Face',
                                'Number_Rest',
                                'Time_Rest']
                    doc["Date"] = pd.to_datetime(doc["Date"], format = '%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    doc["Session"] = pd.to_datetime(doc["Session"]).dt.strftime('%H:%M:%S')
                    doc["Time_break_general"] = pd.to_datetime(doc["Time_break_general"]).dt.strftime('%H:%M:%S')
                    doc["Available"] = pd.to_datetime(doc["Available"]).dt.strftime('%H:%M:%S')
                    doc["Preview"] = pd.to_datetime(doc["Preview"]).dt.strftime('%H:%M:%S')
                    doc["Wrap_up_time"] = pd.to_datetime(doc["Wrap_up_time"]).dt.strftime('%H:%M:%S')
                    doc["Time_press"] = pd.to_datetime(doc["Time_press"]).dt.strftime('%H:%M:%S')
                    doc["Time_sist"] = pd.to_datetime(doc["Time_sist"]).dt.strftime('%H:%M:%S')
                    doc["Time_psup"] = pd.to_datetime(doc["Time_psup"]).dt.strftime('%H:%M:%S')
                    doc["Time_ndef"] = pd.to_datetime(doc["Time_ndef"]).dt.strftime('%H:%M:%S')
                    doc["Time_pfge"] = pd.to_datetime(doc["Time_pfge"]).dt.strftime('%H:%M:%S')
                    doc["Time_pterr"] = pd.to_datetime(doc["Time_pterr"]).dt.strftime('%H:%M:%S')
                    doc["Time_pterr"] = pd.to_datetime(doc["Time_pterr"]).dt.strftime('%H:%M:%S')
                    doc["Time_administrative"] = pd.to_datetime(doc["Time_administrative"]).dt.strftime('%H:%M:%S')
                    doc["time_best_buddy_training"] = pd.to_datetime(doc["time_best_buddy_training"]).dt.strftime('%H:%M:%S')
                    doc["Time_break"] = pd.to_datetime(doc["Time_break"]).dt.strftime('%H:%M:%S')
                    doc["Time_classroom_training"] = pd.to_datetime(doc["Time_classroom_training"]).dt.strftime('%H:%M:%S')
                    doc["Time_external_meeting"] = pd.to_datetime(doc["Time_external_meeting"]).dt.strftime('%H:%M:%S')
                    doc["Time_internal_meeting"] = pd.to_datetime(doc["Time_internal_meeting"]).dt.strftime('%H:%M:%S')
                    doc["Time_manual_dispatching"] = pd.to_datetime(doc["Time_manual_dispatching"]).dt.strftime('%H:%M:%S')
                    doc["Time_other_department_gemsion"] = pd.to_datetime(doc["Time_other_department_gem"]).dt.strftime('%H:%M:%S')
                    doc["Time_special_adminwork"] = pd.to_datetime(doc["Time_special_adminwork"]).dt.strftime('%H:%M:%S')
                    doc["Time_support"] = pd.to_datetime(doc["Time_support"]).dt.strftime('%H:%M:%S')
                    doc["Time_training_on_the_job"] = pd.to_datetime(doc["Time_training_on_the_job"]).dt.strftime('%H:%M:%S')
                    doc["Time_visual_rest"] = pd.to_datetime(doc["Time_visual_rest"]).dt.strftime('%H:%M:%S')
                    doc["Time_prelogout"] = pd.to_datetime(doc["Time_prelogout"]).dt.strftime('%H:%M:%S')
                    doc["Time_unnasociated_dispatching"] = pd.to_datetime(doc["Time_unnasociated_dispatching"]).dt.strftime('%H:%M:%S')
                    doc["Time_meeting"] = pd.to_datetime(doc["Time_meeting"]).dt.strftime('%H:%M:%S')
                    doc["Time_processing_time"] = pd.to_datetime(doc["Time_processing_time"]).dt.strftime('%H:%M:%S')
                    doc["Time_support_supervisor"] = pd.to_datetime(doc["Time_support_supervisor"]).dt.strftime('%H:%M:%S')
                    doc["Time_mail_fax"] = pd.to_datetime(doc["Time_mail_fax"]).dt.strftime('%H:%M:%S')
                    doc["Time_other_deparment_individual"] = pd.to_datetime(doc["Time_other_deparment_individual"]).dt.strftime('%H:%M:%S')
                    doc["Time_inbox"] = pd.to_datetime(doc["Time_inbox"]).dt.strftime('%H:%M:%S')
                    doc["Time_chat"] = pd.to_datetime(doc["Time_chat"]).dt.strftime('%H:%M:%S')
                    doc["Time_sdc"] = pd.to_datetime(doc["Time_sdc"]).dt.strftime('%H:%M:%S')
                    doc["Time_Followup"] = pd.to_datetime(doc["Time_Followup"]).dt.strftime('%H:%M:%S')
                    doc["ON_call_hold"] = pd.to_datetime(doc["ON_call_hold"]).dt.strftime('%H:%M:%S')
                    doc["ON_call_active"] = pd.to_datetime(doc["ON_call_active"]).dt.strftime('%H:%M:%S')
                    doc["Time_on_call"] = pd.to_datetime(doc["Time_on_call"]).dt.strftime('%H:%M:%S')
                    doc["T_Assignation"] = pd.to_datetime(doc["T_Assignation"]).dt.strftime('%H:%M:%S')
                    doc["T_Stand_Prio"] = pd.to_datetime(doc["T_Stand_Prio"]).dt.strftime('%H:%M:%S')
                    doc["T_Bulk_and_Prio"] = pd.to_datetime(doc["T_Bulk_and_Prio"]).dt.strftime('%H:%M:%S')
                    doc["T_Overtime"] = pd.to_datetime(doc["T_Overtime"]).dt.strftime('%H:%M:%S')
                    doc['T_Site_Inspection'] = pd.to_datetime(doc["T_Site_Inspection"]).dt.strftime('%H:%M:%S')
                    doc['T_GEM_Disp'] = pd.to_datetime(doc['T_GEM_Disp']).dt.strftime('%H:%M:%S')
                    doc['T_Multidestination'] = pd.to_datetime(doc['T_Multidestination']).dt.strftime('%H:%M:%S')
                    doc['Time_Audits'] = pd.to_datetime(doc['Time_Audits']).dt.strftime('%H:%M:%S')
                    doc['Time_Feedbacks'] = pd.to_datetime(doc['Time_Feedbacks']).dt.strftime('%H:%M:%S')
                    doc['Time_Platforms'] = pd.to_datetime(doc['Time_Platforms']).dt.strftime('%H:%M:%S')
                    doc['Time_Test'] = pd.to_datetime(doc['Time_Test']).dt.strftime('%H:%M:%S')
                    doc['Time_Calibracion'] = pd.to_datetime(doc['Time_Calibracion']).dt.strftime('%H:%M:%S')
                    doc['Time_Duplicated_y_Spam'] = pd.to_datetime(doc['Time_Duplicated_y_Spam']).dt.strftime('%H:%M:%S')
                    doc['Time_Break_after_transaction'] = pd.to_datetime(doc['Time_Break_after_transaction']).dt.strftime('%H:%M:%S')
                    doc['Time_Face_to_Face'] = pd.to_datetime(doc['Time_Face_to_Face']).dt.strftime('%H:%M:%S')
                    doc['Time_Rest'] = pd.to_datetime(doc['Time_Rest']).dt.strftime('%H:%M:%S')
                    Output = doc.astype(str)
                    convert_dict = {'Date':object,
                                    'Agent':object,
                                    'Agent_ID':object,
                                    'Agent_SAP':object,
                                    'Transactions':object,
                                    'Total_calls':object,
                                    'Calls_in':object,
                                    'Calls_out':object,
                                    'Transfer_in':object,
                                    'Transfer_out':object,
                                    'Session':object,
                                    'n_breaks':object,
                                    'Time_break_general':object,
                                    'Available':object,
                                    'Preview':object,
                                    'Time_on_call':object,
                                    'Wrap_up_time':object,
                                    'n_press':object,
                                    'Time_press':object,
                                    'n_sist':object,
                                    'Time_sist':object,
                                    'n_psup':object,
                                    'Time_psup':object,
                                    'n_ndef':object,
                                    'Time_ndef':object,
                                    'n_pfge':object,
                                    'Time_pfge':object,
                                    'n_pterr':object,
                                    'Time_pterr':object,
                                    'Time_administrative':object,
                                    'n_best_buddy_training':object,
                                    'time_best_buddy_training':object,
                                    'n_break':object,
                                    'Time_break':object,
                                    'n_classroom_training':object,
                                    'Time_classroom_training':object,
                                    'n_external_meeting':object,
                                    'Time_external_meeting':object,
                                    'n_internal_meeting':object,
                                    'Time_internal_meeting':object,
                                    'n_manual_dispatching':object,
                                    'Time_manual_dispatching':object,
                                    'n_other_department_gem':object,
                                    'Time_other_department_gem':object,
                                    'n_special_adminwork':object,
                                    'Time_special_adminwork':object,
                                    'n_support':object,
                                    'Time_support':object,
                                    'n_training_on_the_job':object,
                                    'Time_training_on_the_job':object,
                                    'n_visual_rest':object,
                                    'Time_visual_rest':object,
                                    'n_prelogout':object,
                                    'Time_prelogout':object,
                                    'n_unnasociated_dispatching':object,
                                    'Time_unnasociated_dispatching':object,
                                    'n_meeting':object,
                                    'Time_meeting':object,
                                    'n_processing_time':object,
                                    'Time_processing_time':object,
                                    'n_support_supervisor':object,
                                    'Time_support_supervisor':object,
                                    'n_mail_fax':object,
                                    'Time_mail_fax':object,
                                    'n_other_department_individual':object,
                                    'Time_other_deparment_individual':object,
                                    'n_inbox':object,
                                    'Time_inbox':object,
                                    'n_chat':object,
                                    'Time_chat':object,
                                    'n_sdc':object,
                                    'Time_sdc':object,
                                    'n_Followup':object,
                                    'Time_Followup':object,
                                    'Service':object,
                                    'ON_call_hold':object,
                                    'ON_call_active':object,
                                    'N_Assignation': object,
                                    'T_Assignation': object,
                                    'N_Stand_Prio': object,
                                    'T_Stand_Prio':object,
                                    'N_Bulk_and_Prio':object,
                                    'T_Bulk_and_Prio':object,
                                    'N_Overtime':object,
                                    'T_Overtime':object,
                                    'N_Site_Inspection':object,
                                    'T_Site_Inspection':object, 
                                    'N_GEM_Disp':object, 
                                    'T_GEM_Disp':object,
                                    'N_Multidestination':object,
                                    'T_Multidestination':object,
                                    'Number_Audits':object,
                                    'Time_Audits':object,
                                    'Number_Feedbacks':object,
                                    'Time_Feedbacks':object,
                                    'Number_Platforms':object,
                                    'Time_Platforms':object,
                                    'Number_Test':object,
                                    'Time_Test':object,
                                    'Number_Calibracion':object,
                                    'Time_Calibracion':object, 
                                    'Number_Duplicated_y_Spam':object,
                                    'Time_Duplicated_y_Spam':object,
                                    'Number_Break_after_transaction':object,
                                    'Time_Break_after_transaction':object,
                                    'Number_Face_to_Face':object,
                                    'Time_Face_to_Face':object,
                                    'Number_Rest':object,
                                    'Time_Rest':object} 
                    Output["Time_other_department_gem"] = pd.to_datetime(Output["Time_other_department_gem"]).dt.strftime('%H:%M:%S')
                    d = []
                    for i in range(0, len(Output["Agent"])):
                        d.append(Output["Agent"][i][:-1])
                    Output["Agent"] = d
                    Call_db = Output.astype(convert_dict)
                    Call_db = Call_db.iloc[:,:-1]
                    Call_db = Call_db.astype(str)
                    Call_db.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace = True)
                    Call_db.to_gbq(destination_table='Evolution.Agent_total_breaks',project_id='nh-cro-forecast', if_exists='append')

                else:
                    Day = str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('Agent_total_breaks UPLOADING')
                    with fs.open('trueit_external/Agent_By_Calls_And_Status/Agent_Total_Breaks_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')
                    doc.columns=['Date',
                                'Agent',
                                'Agent_ID',
                                'Agent_SAP',
                                'Transactions',
                                'Total_calls',
                                'Calls_in',
                                'Calls_out',
                                'Transfer_in',
                                'Transfer_out',
                                'Session',
                                'n_breaks',
                                'Time_break_general',
                                'Available',
                                'Preview',
                                'Time_on_call',
                                'Wrap_up_time',
                                'n_press',
                                'Time_press',
                                'n_sist',
                                'Time_sist',
                                'n_psup',
                                'Time_psup',
                                'n_ndef',
                                'Time_ndef',
                                'n_pfge',
                                'Time_pfge',
                                'n_pterr',
                                'Time_pterr',
                                'Time_administrative',
                                'n_best_buddy_training',
                                'time_best_buddy_training',
                                'n_break',
                                'Time_break',
                                'n_classroom_training',
                                'Time_classroom_training',
                                'n_external_meeting',
                                'Time_external_meeting',
                                'n_internal_meeting',
                                'Time_internal_meeting',
                                'n_manual_dispatching',
                                'Time_manual_dispatching',
                                'n_other_department_gem',
                                'Time_other_department_gem',
                                'n_special_adminwork',
                                'Time_special_adminwork',
                                'n_support',
                                'Time_support',
                                'n_training_on_the_job',
                                'Time_training_on_the_job',
                                'n_visual_rest',
                                'Time_visual_rest',
                                'n_prelogout',
                                'Time_prelogout',
                                'n_unnasociated_dispatching',
                                'Time_unnasociated_dispatching',
                                'n_meeting',
                                'Time_meeting',
                                'n_processing_time',
                                'Time_processing_time',
                                'n_support_supervisor',
                                'Time_support_supervisor',
                                'n_mail_fax',
                                'Time_mail_fax',
                                'n_other_department_individual',
                                'Time_other_deparment_individual',
                                'n_inbox',
                                'Time_inbox',
                                'n_chat',
                                'Time_chat',
                                'n_sdc',
                                'Time_sdc',
                                'n_Followup',
                                'Time_Followup',
                                'Service',
                                'ON_call_hold',
                                'ON_call_active',
                                'N_Assignation',
                                'T_Assignation',
                                'N_Stand_Prio',
                                'T_Stand_Prio',
                                'N_Bulk_and_Prio',
                                'T_Bulk_and_Prio',
                                'N_Overtime',
                                'T_Overtime',
                                'N_Site_Inspection',
                                'T_Site_Inspection', 
                                'N_GEM_Disp', 
                                'T_GEM_Disp',
                                'N_Multidestination',
                                'T_Multidestination',
                                'Number_Audits',
                                'Time_Audits',
                                'Number_Feedbacks',
                                'Time_Feedbacks',
                                'Number_Platforms',
                                'Time_Platforms',
                                'Number_Test',
                                'Time_Test',
                                'Number_Calibracion',
                                'Time_Calibracion', 
                                'Number_Duplicated_y_Spam',
                                'Time_Duplicated_y_Spam',
                                'Number_Break_after_transaction',
                                'Time_Break_after_transaction',
                                'Number_Face_to_Face',
                                'Time_Face_to_Face',
                                'Number_Rest',
                                'Time_Rest']
                    doc["Date"] = pd.to_datetime(doc["Date"], format = '%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    doc["Session"] = pd.to_datetime(doc["Session"]).dt.strftime('%H:%M:%S')
                    doc["Time_break_general"] = pd.to_datetime(doc["Time_break_general"]).dt.strftime('%H:%M:%S')
                    doc["Available"] = pd.to_datetime(doc["Available"]).dt.strftime('%H:%M:%S')
                    doc["Preview"] = pd.to_datetime(doc["Preview"]).dt.strftime('%H:%M:%S')
                    doc["Wrap_up_time"] = pd.to_datetime(doc["Wrap_up_time"]).dt.strftime('%H:%M:%S')
                    doc["Time_press"] = pd.to_datetime(doc["Time_press"]).dt.strftime('%H:%M:%S')
                    doc["Time_sist"] = pd.to_datetime(doc["Time_sist"]).dt.strftime('%H:%M:%S')
                    doc["Time_psup"] = pd.to_datetime(doc["Time_psup"]).dt.strftime('%H:%M:%S')
                    doc["Time_ndef"] = pd.to_datetime(doc["Time_ndef"]).dt.strftime('%H:%M:%S')
                    doc["Time_pfge"] = pd.to_datetime(doc["Time_pfge"]).dt.strftime('%H:%M:%S')
                    doc["Time_pterr"] = pd.to_datetime(doc["Time_pterr"]).dt.strftime('%H:%M:%S')
                    doc["Time_pterr"] = pd.to_datetime(doc["Time_pterr"]).dt.strftime('%H:%M:%S')
                    doc["Time_administrative"] = pd.to_datetime(doc["Time_administrative"]).dt.strftime('%H:%M:%S')
                    doc["time_best_buddy_training"] = pd.to_datetime(doc["time_best_buddy_training"]).dt.strftime('%H:%M:%S')
                    doc["Time_break"] = pd.to_datetime(doc["Time_break"]).dt.strftime('%H:%M:%S')
                    doc["Time_classroom_training"] = pd.to_datetime(doc["Time_classroom_training"]).dt.strftime('%H:%M:%S')
                    doc["Time_external_meeting"] = pd.to_datetime(doc["Time_external_meeting"]).dt.strftime('%H:%M:%S')
                    doc["Time_internal_meeting"] = pd.to_datetime(doc["Time_internal_meeting"]).dt.strftime('%H:%M:%S')
                    doc["Time_manual_dispatching"] = pd.to_datetime(doc["Time_manual_dispatching"]).dt.strftime('%H:%M:%S')
                    doc["Time_other_department_gemsion"] = pd.to_datetime(doc["Time_other_department_gem"]).dt.strftime('%H:%M:%S')
                    doc["Time_special_adminwork"] = pd.to_datetime(doc["Time_special_adminwork"]).dt.strftime('%H:%M:%S')
                    doc["Time_support"] = pd.to_datetime(doc["Time_support"]).dt.strftime('%H:%M:%S')
                    doc["Time_training_on_the_job"] = pd.to_datetime(doc["Time_training_on_the_job"]).dt.strftime('%H:%M:%S')
                    doc["Time_visual_rest"] = pd.to_datetime(doc["Time_visual_rest"]).dt.strftime('%H:%M:%S')
                    doc["Time_prelogout"] = pd.to_datetime(doc["Time_prelogout"]).dt.strftime('%H:%M:%S')
                    doc["Time_unnasociated_dispatching"] = pd.to_datetime(doc["Time_unnasociated_dispatching"]).dt.strftime('%H:%M:%S')
                    doc["Time_meeting"] = pd.to_datetime(doc["Time_meeting"]).dt.strftime('%H:%M:%S')
                    doc["Time_processing_time"] = pd.to_datetime(doc["Time_processing_time"]).dt.strftime('%H:%M:%S')
                    doc["Time_support_supervisor"] = pd.to_datetime(doc["Time_support_supervisor"]).dt.strftime('%H:%M:%S')
                    doc["Time_mail_fax"] = pd.to_datetime(doc["Time_mail_fax"]).dt.strftime('%H:%M:%S')
                    doc["Time_other_deparment_individual"] = pd.to_datetime(doc["Time_other_deparment_individual"]).dt.strftime('%H:%M:%S')
                    doc["Time_inbox"] = pd.to_datetime(doc["Time_inbox"]).dt.strftime('%H:%M:%S')
                    doc["Time_chat"] = pd.to_datetime(doc["Time_chat"]).dt.strftime('%H:%M:%S')
                    doc["Time_sdc"] = pd.to_datetime(doc["Time_sdc"]).dt.strftime('%H:%M:%S')
                    doc["Time_Followup"] = pd.to_datetime(doc["Time_Followup"]).dt.strftime('%H:%M:%S')
                    doc["ON_call_hold"] = pd.to_datetime(doc["ON_call_hold"]).dt.strftime('%H:%M:%S')
                    doc["ON_call_active"] = pd.to_datetime(doc["ON_call_active"]).dt.strftime('%H:%M:%S')
                    doc["Time_on_call"] = pd.to_datetime(doc["Time_on_call"]).dt.strftime('%H:%M:%S')
                    doc["T_Assignation"] = pd.to_datetime(doc["T_Assignation"]).dt.strftime('%H:%M:%S')
                    doc["T_Stand_Prio"] = pd.to_datetime(doc["T_Stand_Prio"]).dt.strftime('%H:%M:%S')
                    doc["T_Bulk_and_Prio"] = pd.to_datetime(doc["T_Bulk_and_Prio"]).dt.strftime('%H:%M:%S')
                    doc["T_Overtime"] = pd.to_datetime(doc["T_Overtime"]).dt.strftime('%H:%M:%S')
                    doc['T_Site_Inspection'] = pd.to_datetime(doc["T_Site_Inspection"]).dt.strftime('%H:%M:%S')
                    doc['T_GEM_Disp'] = pd.to_datetime(doc['T_GEM_Disp']).dt.strftime('%H:%M:%S')
                    doc['T_Multidestination'] = pd.to_datetime(doc['T_Multidestination']).dt.strftime('%H:%M:%S')
                    doc['Time_Audits'] = pd.to_datetime(doc['Time_Audits']).dt.strftime('%H:%M:%S')
                    doc['Time_Feedbacks'] = pd.to_datetime(doc['Time_Feedbacks']).dt.strftime('%H:%M:%S')
                    doc['Time_Platforms'] = pd.to_datetime(doc['Time_Platforms']).dt.strftime('%H:%M:%S')
                    doc['Time_Test'] = pd.to_datetime(doc['Time_Test']).dt.strftime('%H:%M:%S')
                    doc['Time_Calibracion'] = pd.to_datetime(doc['Time_Calibracion']).dt.strftime('%H:%M:%S')
                    doc['Time_Duplicated_y_Spam'] = pd.to_datetime(doc['Time_Duplicated_y_Spam']).dt.strftime('%H:%M:%S')
                    doc['Time_Break_after_transaction'] = pd.to_datetime(doc['Time_Break_after_transaction']).dt.strftime('%H:%M:%S')
                    doc['Time_Face_to_Face'] = pd.to_datetime(doc['Time_Face_to_Face']).dt.strftime('%H:%M:%S')
                    doc['Time_Rest'] = pd.to_datetime(doc['Time_Rest']).dt.strftime('%H:%M:%S')
                    Output = doc.astype(str)
                    convert_dict = {'Date':object,
                                    'Agent':object,
                                    'Agent_ID':object,
                                    'Agent_SAP':object,
                                    'Transactions':object,
                                    'Total_calls':object,
                                    'Calls_in':object,
                                    'Calls_out':object,
                                    'Transfer_in':object,
                                    'Transfer_out':object,
                                    'Session':object,
                                    'n_breaks':object,
                                    'Time_break_general':object,
                                    'Available':object,
                                    'Preview':object,
                                    'Time_on_call':object,
                                    'Wrap_up_time':object,
                                    'n_press':object,
                                    'Time_press':object,
                                    'n_sist':object,
                                    'Time_sist':object,
                                    'n_psup':object,
                                    'Time_psup':object,
                                    'n_ndef':object,
                                    'Time_ndef':object,
                                    'n_pfge':object,
                                    'Time_pfge':object,
                                    'n_pterr':object,
                                    'Time_pterr':object,
                                    'Time_administrative':object,
                                    'n_best_buddy_training':object,
                                    'time_best_buddy_training':object,
                                    'n_break':object,
                                    'Time_break':object,
                                    'n_classroom_training':object,
                                    'Time_classroom_training':object,
                                    'n_external_meeting':object,
                                    'Time_external_meeting':object,
                                    'n_internal_meeting':object,
                                    'Time_internal_meeting':object,
                                    'n_manual_dispatching':object,
                                    'Time_manual_dispatching':object,
                                    'n_other_department_gem':object,
                                    'Time_other_department_gem':object,
                                    'n_special_adminwork':object,
                                    'Time_special_adminwork':object,
                                    'n_support':object,
                                    'Time_support':object,
                                    'n_training_on_the_job':object,
                                    'Time_training_on_the_job':object,
                                    'n_visual_rest':object,
                                    'Time_visual_rest':object,
                                    'n_prelogout':object,
                                    'Time_prelogout':object,
                                    'n_unnasociated_dispatching':object,
                                    'Time_unnasociated_dispatching':object,
                                    'n_meeting':object,
                                    'Time_meeting':object,
                                    'n_processing_time':object,
                                    'Time_processing_time':object,
                                    'n_support_supervisor':object,
                                    'Time_support_supervisor':object,
                                    'n_mail_fax':object,
                                    'Time_mail_fax':object,
                                    'n_other_department_individual':object,
                                    'Time_other_deparment_individual':object,
                                    'n_inbox':object,
                                    'Time_inbox':object,
                                    'n_chat':object,
                                    'Time_chat':object,
                                    'n_sdc':object,
                                    'Time_sdc':object,
                                    'n_Followup':object,
                                    'Time_Followup':object,
                                    'Service':object,
                                    'ON_call_hold':object,
                                    'ON_call_active':object,
                                    'N_Assignation': object,
                                    'T_Assignation': object,
                                    'N_Stand_Prio': object,
                                    'T_Stand_Prio':object,
                                    'N_Bulk_and_Prio':object,
                                    'T_Bulk_and_Prio':object,
                                    'N_Overtime':object,
                                    'T_Overtime':object,
                                    'N_Site_Inspection':object,
                                    'T_Site_Inspection':object, 
                                    'N_GEM_Disp':object, 
                                    'T_GEM_Disp':object,
                                    'N_Multidestination':object,
                                    'T_Multidestination':object,
                                    'Number_Audits':object,
                                    'Time_Audits':object,
                                    'Number_Feedbacks':object,
                                    'Time_Feedbacks':object,
                                    'Number_Platforms':object,
                                    'Time_Platforms':object,
                                    'Number_Test':object,
                                    'Time_Test':object,
                                    'Number_Calibracion':object,
                                    'Time_Calibracion':object, 
                                    'Number_Duplicated_y_Spam':object,
                                    'Time_Duplicated_y_Spam':object,
                                    'Number_Break_after_transaction':object,
                                    'Time_Break_after_transaction':object,
                                    'Number_Face_to_Face':object,
                                    'Time_Face_to_Face':object,
                                    'Number_Rest':object,
                                    'Time_Rest':object} 
                    Output["Time_other_department_gem"] = pd.to_datetime(Output["Time_other_department_gem"]).dt.strftime('%H:%M:%S')
                    d = []
                    for i in range(0, len(Output["Agent"])):
                        d.append(Output["Agent"][i][:-1])
                    Output["Agent"] = d
                    Call_db = Output.astype(convert_dict)
                    Call_db = Call_db.iloc[:,:-1]
                    Call_db = Call_db.astype(str)
                    Call_db.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace = True)
                    Call_db.to_gbq(destination_table='Evolution.Agent_total_breaks',project_id='nh-cro-forecast', if_exists='append')
            
    elif Query_number == 3:
            for i in range(int(inicio_dia),int(fin_dia)+1):
                if i <10: 
                    Day = "0"+str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('Calls_per_queue UPLOADING')
                    with fs.open('trueit_external/Calls_By_Agent_Campaign/CDR_by_Agent_Campaign_Detail_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')
                    doc = doc.iloc[0:,1:]
                    doc.columns = ['Service',
                                'Date',
                                'Agent',
                                'Agent_ID',
                                'Campaign',
                                'Campaign_number',
                                'Language',
                                'IVR_option',
                                'Calls_in',
                                'Calls_out',
                                'Talk_time_in',
                                'Talk_time_out',
                                'Total_talk_time']
                    doc["Date"] = pd.to_datetime(doc["Date"], format = '%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    doc["Talk_time_in"] = pd.to_datetime(doc["Talk_time_in"]).dt.strftime('%H:%M:%S')
                    doc["Talk_time_out"] = pd.to_datetime(doc["Talk_time_out"]).dt.strftime('%H:%M:%S')
                    doc["Total_talk_time"] = pd.to_datetime(doc["Total_talk_time"]).dt.strftime('%H:%M:%S')
                    doc['Total_calls'] = doc['Calls_in'].astype(int) + doc['Calls_out'].astype(int)
                    Output = doc.astype(str)
                    Output
                    convert_dict = {'Date':object,
                                    'Service':object,
                                    'Campaign':object,
                                    'Campaign_number':object,
                                    'Language':object,
                                    'IVR_option':object,
                                    'Agent':object,
                                    'Agent_ID':object,
                                    'Calls_in':object,
                                    'Calls_out':object,
                                    'Total_calls':object,
                                    'Talk_time_in':object,
                                    'Talk_time_out':object,
                                    'Total_talk_time':object,
                                    } 
                    Call_db = Output.astype(convert_dict)
                    Call_db = Call_db[['Date', 'Service', 'Campaign', 'Campaign_number', 'Language', 'IVR_option','Agent', 'Agent_ID', 'Calls_in', 'Calls_out'
                            , 'Total_calls', 'Talk_time_in', 'Talk_time_out', 'Total_talk_time']]
                    Call_db = Call_db.astype(str)
                    Call_db.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None], inplace=True)
                    Call_db.to_gbq(destination_table='Evolution.Calls_per_queue',project_id='nh-cro-forecast', if_exists='append')
                else:
                    Day = str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('Calls_per_queue UPLOADING')
                    with fs.open('trueit_external/Calls_By_Agent_Campaign/CDR_by_Agent_Campaign_Detail_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')
                    doc = doc.iloc[0:,1:]
                    doc.columns = ['Service',
                                'Date',
                                'Agent',
                                'Agent_ID',
                                'Campaign',
                                'Campaign_number',
                                'Language',
                                'IVR_option',
                                'Calls_in',
                                'Calls_out',
                                'Talk_time_in',
                                'Talk_time_out',
                                'Total_talk_time']
                    doc["Date"] = pd.to_datetime(doc["Date"], format = '%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    doc["Talk_time_in"] = pd.to_datetime(doc["Talk_time_in"]).dt.strftime('%H:%M:%S')
                    doc["Talk_time_out"] = pd.to_datetime(doc["Talk_time_out"]).dt.strftime('%H:%M:%S')
                    doc["Total_talk_time"] = pd.to_datetime(doc["Total_talk_time"]).dt.strftime('%H:%M:%S')
                    doc['Total_calls'] = doc['Calls_in'].astype(int) + doc['Calls_out'].astype(int)
                    Output = doc.astype(str)
                    Output
                    convert_dict = {'Date':object,
                                    'Service':object,
                                    'Campaign':object,
                                    'Campaign_number':object,
                                    'Language':object,
                                    'IVR_option':object,
                                    'Agent':object,
                                    'Agent_ID':object,
                                    'Calls_in':object,
                                    'Calls_out':object,
                                    'Total_calls':object,
                                    'Talk_time_in':object,
                                    'Talk_time_out':object,
                                    'Total_talk_time':object,
                                    } 
                    Call_db = Output.astype(convert_dict)
                    Call_db = Call_db[['Date', 'Service', 'Campaign', 'Campaign_number', 'Language', 'IVR_option','Agent', 'Agent_ID', 'Calls_in', 'Calls_out'
                            , 'Total_calls', 'Talk_time_in', 'Talk_time_out', 'Total_talk_time']]
                    Call_db = Call_db.astype(str)
                    Call_db.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None], inplace=True)
                    Call_db.to_gbq(destination_table='Evolution.Calls_per_queue',project_id='nh-cro-forecast', if_exists='append')
    elif Query_number == 4:
            for i in range(int(inicio_dia),int(fin_dia)+1):
                if i <10: 
                    Day = "0"+str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('SLA_completed UPLOADING')
                    with fs.open('trueit_external/SLA_completed/SLA_Completed_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')
                    File = doc
                    File.columns=['group',
                                'Service',
                                'Entry_date',
                                'Entry_hour',
                                'Activity_ID',
                                'Case_ID',
                                'Alias',
                                'Agent_distributed',
                                'Distributed_date',
                                'Distributed_hour',
                                'Queue',
                                'Completed',
                                'Agent_completed',
                                'Completed_date',
                                'Completed_hour',
                                'Type',
                                'Subtype',
                                'due_on',
                                'From_mail',
                                'IN_OUT',
                                'Total_time']
                    b = []
                    for i in range(len(File["due_on"])):       
                        b.append(File["due_on"][i][File["due_on"][i].rfind(" ")+1:])
                    File["Due_on_hour"] = b
                    c = []
                    for i in range(len(File["due_on"])):
                        c.append(File["due_on"][i][:File["due_on"][i].rfind(" ")])
                    File["Due_on_date"] = c
                    File = File.iloc[1:len(File)]
                    File.drop(['group'],axis=1,inplace=True)
                    File["Entry_date"] = pd.to_datetime(File["Entry_date"], format = '%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    File["Completed_date"] = pd.to_datetime(File["Completed_date"], format = '%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    File["Distributed_date"] = pd.to_datetime(File["Distributed_date"], format = '%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    File.drop(columns=['due_on'],inplace = True)
                    Output = File.astype(str)
                    convert_dict = {'Service':object,
                                    'Entry_date':object,
                                    'Entry_hour':object,
                                    'Activity_ID':object,
                                    'Case_ID':object,
                                    'Alias':object,
                                    'Agent_distributed':object,
                                    'Distributed_date':object,
                                    'Distributed_hour':object,
                                    'Queue':object,
                                    'Completed':object,
                                    'Agent_completed':object,
                                    'Completed_date':object,
                                    'Completed_hour':object,
                                    'Type':object,
                                    'Subtype':object,
                                    'From_mail':object,
                                    'IN_OUT':object,
                                    'Total_time':object,
                                    'Due_on_hour':object,
                                    'Due_on_date':object} 
                    Call_db = Output.astype(convert_dict)
                    Call_db = Call_db.reindex(columns = ['Service',
                                                        'Entry_date',
                                                        'Entry_hour',
                                                        'Activity_ID',
                                                        'Case_ID',
                                                        'Alias',
                                                        'Agent_distributed',
                                                        'Distributed_date',
                                                        'Distributed_hour',
                                                        'Queue',
                                                        'Completed',
                                                        'Agent_completed',
                                                        'Completed_date',
                                                        'Completed_hour',
                                                        'Type',
                                                        'Subtype',
                                                        'From_mail',
                                                        'Due_on_date',
                                                        'Due_on_hour',
                                                        'IN_OUT',
                                                        'Total_time'])
                    Call_db.to_gbq(destination_table='Evolution.SLA_completed',project_id='nh-cro-forecast', if_exists='append')
                else:
                    Day = str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('SLA_completed UPLOADING')
                    with fs.open('trueit_external/SLA_completed/SLA_Completed_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')
                    File = doc
                    File.columns=['group',
                                'Service',
                                'Entry_date',
                                'Entry_hour',
                                'Activity_ID',
                                'Case_ID',
                                'Alias',
                                'Agent_distributed',
                                'Distributed_date',
                                'Distributed_hour',
                                'Queue',
                                'Completed',
                                'Agent_completed',
                                'Completed_date',
                                'Completed_hour',
                                'Type',
                                'Subtype',
                                'due_on',
                                'From_mail',
                                'IN_OUT',
                                'Total_time']
                    b = []
                    for i in range(len(File["due_on"])):       
                        b.append(File["due_on"][i][File["due_on"][i].rfind(" ")+1:])
                    File["Due_on_hour"] = b
                    c = []
                    for i in range(len(File["due_on"])):
                        c.append(File["due_on"][i][:File["due_on"][i].rfind(" ")])
                    File["Due_on_date"] = c
                    File = File.iloc[1:len(File)]
                    File.drop(['group'],axis=1,inplace=True)
                    File["Entry_date"] = pd.to_datetime(File["Entry_date"], format = '%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    File["Completed_date"] = pd.to_datetime(File["Completed_date"], format = '%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    File["Distributed_date"] = pd.to_datetime(File["Distributed_date"], format = '%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    File.drop(columns=['due_on'],inplace = True)
                    Output = File.astype(str)
                    convert_dict = {'Service':object,
                                    'Entry_date':object,
                                    'Entry_hour':object,
                                    'Activity_ID':object,
                                    'Case_ID':object,
                                    'Alias':object,
                                    'Agent_distributed':object,
                                    'Distributed_date':object,
                                    'Distributed_hour':object,
                                    'Queue':object,
                                    'Completed':object,
                                    'Agent_completed':object,
                                    'Completed_date':object,
                                    'Completed_hour':object,
                                    'Type':object,
                                    'Subtype':object,
                                    'From_mail':object,
                                    'IN_OUT':object,
                                    'Total_time':object,
                                    'Due_on_hour':object,
                                    'Due_on_date':object} 
                    Call_db = Output.astype(convert_dict)
                    Call_db = Call_db.reindex(columns = ['Service',
                                                        'Entry_date',
                                                        'Entry_hour',
                                                        'Activity_ID',
                                                        'Case_ID',
                                                        'Alias',
                                                        'Agent_distributed',
                                                        'Distributed_date',
                                                        'Distributed_hour',
                                                        'Queue',
                                                        'Completed',
                                                        'Agent_completed',
                                                        'Completed_date',
                                                        'Completed_hour',
                                                        'Type',
                                                        'Subtype',
                                                        'From_mail',
                                                        'Due_on_date',
                                                        'Due_on_hour',
                                                        'IN_OUT',
                                                        'Total_time'])
                    Call_db.to_gbq(destination_table='Evolution.SLA_completed',project_id='nh-cro-forecast', if_exists='append')
    elif Query_number == 5:
            for i in range(int(inicio_dia),int(fin_dia)+1):
                if i <10: 
                    Day = "0"+str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('Codifications_Mails UPLOADING')
                    with fs.open('trueit_external/Mail_Codifications/Incoming_Category_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')
                    doc.columns=['grouplevel',
                                'Group',
                                'Group_2',
                                'Agent',
                                'Client',
                                'Type',
                                'Subtype',
                                'Category',
                                'Subcategory',
                                'Queue',
                                'Created_on_date',
                                'Created_on_hour',
                                'Completed_on_date',
                                'Completed_on_hour',
                                'Activity_ID',
                                'Case_ID']
                    doc["Created_on_date"] = pd.to_datetime(doc["Created_on_date"], format=('%d/%m/%Y')).dt.strftime('%Y-%m-%d')
                    doc["Completed_on_date"] = pd.to_datetime(doc["Completed_on_date"], format=('%d/%m/%Y')).dt.strftime('%Y-%m-%d')
                    Output = doc.astype(str)
                    Output.drop(['grouplevel'],axis = 1, inplace = True)
                    convert_dict = {'Group':object,
                                    'Group_2':object,
                                    'Agent':object,
                                    'Client':object,
                                    'Type':object,
                                    'Subtype':object,
                                    'Category':object,
                                    'Subcategory':object,
                                    'Queue':object,
                                    'Created_on_date':object,
                                    'Created_on_hour':object,
                                    'Completed_on_date':object,
                                    'Completed_on_hour':object,
                                    'Activity_ID':object,
                                    'Case_ID':object} 
                    Call_db = Output.astype(convert_dict)
                    Call_db = Call_db.astype(str)
                    Call_db.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)
                    Call_db.to_gbq(destination_table='Evolution.Codifications_Mails',project_id='nh-cro-forecast', if_exists='append')
                else:
                    Day = str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('Codifications_Mails UPLOADING')
                    with fs.open('trueit_external/Mail_Codifications/Incoming_Category_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')
                    doc.columns=['grouplevel',
                                'Group',
                                'Group_2',
                                'Agent',
                                'Client',
                                'Type',
                                'Subtype',
                                'Category',
                                'Subcategory',
                                'Queue',
                                'Created_on_date',
                                'Created_on_hour',
                                'Completed_on_date',
                                'Completed_on_hour',
                                'Activity_ID',
                                'Case_ID']
                    doc["Created_on_date"] = pd.to_datetime(doc["Created_on_date"], format=('%d/%m/%Y')).dt.strftime('%Y-%m-%d')
                    doc["Completed_on_date"] = pd.to_datetime(doc["Completed_on_date"], format=('%d/%m/%Y')).dt.strftime('%Y-%m-%d')
                    Output = doc.astype(str)
                    Output.drop(['grouplevel'],axis = 1, inplace = True)
                    convert_dict = {'Group':object,
                                    'Group_2':object,
                                    'Agent':object,
                                    'Client':object,
                                    'Type':object,
                                    'Subtype':object,
                                    'Category':object,
                                    'Subcategory':object,
                                    'Queue':object,
                                    'Created_on_date':object,
                                    'Created_on_hour':object,
                                    'Completed_on_date':object,
                                    'Completed_on_hour':object,
                                    'Activity_ID':object,
                                    'Case_ID':object} 
                    Call_db = Output.astype(convert_dict)
                    Call_db = Call_db.astype(str)
                    Call_db.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)
                    Call_db.to_gbq(destination_table='Evolution.Codifications_Mails',project_id='nh-cro-forecast', if_exists='append')
    elif Query_number == 6:
            for i in range(int(inicio_dia),int(fin_dia)+1):
                if i <10: 
                    Day = "0"+str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('a_Encuestas_Quality UPLOADING')
                    with fs.open('trueit_external/Survey_FRONT/Survey_Front_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')
                    doc = doc.iloc[1:,1:]
                    column = ['Fecha',
                            'ID_transaccion',
                            'Service',
                            'Agent',
                            'ID_Agent',
                            'Campaign',
                            'ID_Campaign', 
                            'Language', 
                            'IVR_option', 
                            'Codification',
                            'Answer_survey_transfered', 
                            'Non_answer_survey_transfered', 
                            'Question_1',
                            'Mark_1', 
                            'Question_2', 
                            'Mark_2', 
                            'Question_3',
                            'Mark_3']
                    doc.columns = column
                    doc = doc.iloc[:,[0,1,2,3,4,5,6,7,8,10,11,12,13,14,15,16,17,9]]
                    doc["Fecha"] = pd.to_datetime(doc["Fecha"], format=('%d/%m/%Y')).dt.strftime('%Y-%m-%d')
                    doc = doc.astype(object)
                    doc = doc.astype(str)
                    doc["Question_1"] = doc["Question_1"].replace('nan', '')
                    doc["Mark_1"] = doc["Mark_1"].replace('nan', '')
                    doc["Question_2"] = doc["Question_2"].replace('nan', '')
                    doc["Mark_2"] = doc["Mark_2"].replace('nan', '')
                    doc["Question_3"] = doc["Question_3"].replace('nan', '')
                    doc["Mark_3"] = doc["Mark_3"].replace('nan', '')
                    doc.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None], inplace=True)
                    doc.to_gbq(destination_table='Evolution.a_Encuestas_Quality',project_id='nh-cro-forecast', if_exists='append')
                else:
                    Day = str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('a_Encuestas_Quality UPLOADING')
                    with fs.open('trueit_external/Survey_FRONT/Survey_Front_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')
                    doc = doc.iloc[1:,1:]
                    column = ['Fecha',
                            'ID_transaccion',
                            'Service',
                            'Agent',
                            'ID_Agent',
                            'Campaign',
                            'ID_Campaign', 
                            'Language', 
                            'IVR_option', 
                            'Codification',
                            'Answer_survey_transfered', 
                            'Non_answer_survey_transfered', 
                            'Question_1',
                            'Mark_1', 
                            'Question_2', 
                            'Mark_2', 
                            'Question_3',
                            'Mark_3']
                    doc.columns = column
                    doc = doc.iloc[:,[0,1,2,3,4,5,6,7,8,10,11,12,13,14,15,16,17,9]]
                    doc["Fecha"] = pd.to_datetime(doc["Fecha"], format=('%d/%m/%Y')).dt.strftime('%Y-%m-%d')
                    doc = doc.astype(object)
                    doc = doc.astype(str)
                    doc["Question_1"] = doc["Question_1"].replace('nan', '')
                    doc["Mark_1"] = doc["Mark_1"].replace('nan', '')
                    doc["Question_2"] = doc["Question_2"].replace('nan', '')
                    doc["Mark_2"] = doc["Mark_2"].replace('nan', '')
                    doc["Question_3"] = doc["Question_3"].replace('nan', '')
                    doc["Mark_3"] = doc["Mark_3"].replace('nan', '')
                    doc.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None], inplace=True)
                    doc.to_gbq(destination_table='Evolution.a_Encuestas_Quality',project_id='nh-cro-forecast', if_exists='append')
    elif Query_number == 7:
            for i in range(int(inicio_dia),int(fin_dia)+1):
                if i <10: 
                    Day = "0"+str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('NH_Encuestas UPLOADING')
                    with fs.open('trueit_external/Survey_QUALITY/Survey_Quality_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')
                    File = doc.iloc[0:,1:]
                    File.columns = ['Date',
                                    'Transaction_ID',
                                    'Service',
                                    'Agent',
                                    'Agent_ID',
                                    'Campaign',
                                    'Campaign_ID',
                                    'Language',
                                    'IVR_option',
                                    'Closure',
                                    'N_survey_transfered',
                                    'N_survey_transfered_non_answer',
                                    'Question_1',
                                    'Mark_question_1',
                                    'Question_2',
                                    'Mark_question_2']
                    File['Date'] = pd.to_datetime(File["Date"],format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    Output = File.astype(str)
                    Out_1 = Output[['Date', 
                                    'Transaction_ID', 
                                    'Service', 
                                    'Agent', 
                                    'Agent_ID',
                                    'Campaign',
                                    'Campaign_ID',
                                    'Language',
                                    'IVR_option',
                                    'N_survey_transfered',
                                    'N_survey_transfered_non_answer',
                                    'Question_1',
                                    'Mark_question_1',
                                    'Question_2',
                                    'Mark_question_2',
                                    'Closure']]
                    Out_2 = Out_1.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None])
                    Out_2.to_gbq(destination_table='Evolution.NH_Encuestas',project_id='nh-cro-forecast', if_exists='append')
                else:
                    Day = str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('NH_Encuestas UPLOADING')
                    with fs.open('trueit_external/Survey_QUALITY/Survey_Quality_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')
                    File = doc.iloc[0:,1:]
                    File.columns = ['Date',
                                    'Transaction_ID',
                                    'Service',
                                    'Agent',
                                    'Agent_ID',
                                    'Campaign',
                                    'Campaign_ID',
                                    'Language',
                                    'IVR_option',
                                    'Closure',
                                    'N_survey_transfered',
                                    'N_survey_transfered_non_answer',
                                    'Question_1',
                                    'Mark_question_1',
                                    'Question_2',
                                    'Mark_question_2']
                    File['Date'] = pd.to_datetime(File["Date"],format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    Output = File.astype(str)
                    Out_1 = Output[['Date', 
                                    'Transaction_ID', 
                                    'Service', 
                                    'Agent', 
                                    'Agent_ID',
                                    'Campaign',
                                    'Campaign_ID',
                                    'Language',
                                    'IVR_option',
                                    'N_survey_transfered',
                                    'N_survey_transfered_non_answer',
                                    'Question_1',
                                    'Mark_question_1',
                                    'Question_2',
                                    'Mark_question_2',
                                    'Closure']]
                    Out_2 = Out_1.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None])
                    Out_2.to_gbq(destination_table='Evolution.NH_Encuestas',project_id='nh-cro-forecast', if_exists='append')
    elif Query_number == 8:
            for i in range(int(inicio_dia),int(fin_dia)+1):
                if i <10: 
                    Day = "0"+str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('e_3_NBA_Survey UPLOADING')
                    with fs.open('trueit_external/Survey_NBA/Calls_Survey_NBA_service_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')
                    doc = doc.iloc[0:,1:]
                    doc = doc.astype(str)
                    doc=doc.rename(columns={"Fecha":"Date",
                                            "Servicio":"Service",
                                            "Agente":"Agent",
                                            "Campaña":"Campaign",
                                            "Idioma":"Language",
                                            "IdTransaccion":"ID_Transaction",
                                            "ID Agente":"ID_Agent",
                                            "ID Campaña":"ID_Campaign",
                                            "IVR Option":"IVR_Option",
                                            "N encuestas transferidas":"Survey_transfered",
                                            "N encuestas transferidas NC":"Survey_transfered_not_answered",
                                            "Pregunta 1":"Question_1",
                                            "Nota Pregunta 1":"Question_1_mark",
                                            "Pregunta 2":"Question_2",
                                            "Nota Pregunta 2":"Question_2_mark",
                                            "Pregunta 3":"Question_3",
                                            "Nota Pregunta 3":"Question_3_mark"})
                    doc["Date"] = pd.to_datetime(doc["Date"],format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    doc.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)
                    output = doc.astype(str)
                    output.to_gbq(destination_table='Evolution.e_3_NBA_Survey',project_id='nh-cro-forecast', if_exists='append')
                else:
                    Day = str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('e_3_NBA_Survey UPLOADING')
                    with fs.open('trueit_external/Survey_NBA/Calls_Survey_NBA_service_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')
                    doc = doc.iloc[0:,1:]
                    doc = doc.astype(str)
                    doc=doc.rename(columns={"Fecha":"Date",
                                            "Servicio":"Service",
                                            "Agente":"Agent",
                                            "Campaña":"Campaign",
                                            "Idioma":"Language",
                                            "IdTransaccion":"ID_Transaction",
                                            "ID Agente":"ID_Agent",
                                            "ID Campaña":"ID_Campaign",
                                            "IVR Option":"IVR_Option",
                                            "N encuestas transferidas":"Survey_transfered",
                                            "N encuestas transferidas NC":"Survey_transfered_not_answered",
                                            "Pregunta 1":"Question_1",
                                            "Nota Pregunta 1":"Question_1_mark",
                                            "Pregunta 2":"Question_2",
                                            "Nota Pregunta 2":"Question_2_mark",
                                            "Pregunta 3":"Question_3",
                                            "Nota Pregunta 3":"Question_3_mark"})
                    doc["Date"] = pd.to_datetime(doc["Date"],format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    doc.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)
                    output = doc.astype(str)
                    output.to_gbq(destination_table='Evolution.e_3_NBA_Survey',project_id='nh-cro-forecast', if_exists='append')
    elif Query_number == 9:
            for i in range(int(inicio_dia),int(fin_dia)+1):
                if i <10: 
                    Day = "0"+str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('e_4_CAT_Survey UPLOADING')
                    with fs.open('trueit_external/Survey_NBA/Calls_Survey_CAT_service_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')  
                    doc = doc.iloc[0:,1:]
                    doc = doc.astype(str)
                    doc=doc.rename(columns={"Fecha":"Date",
                                            "Servicio":"Service",
                                            "Agente":"Agent",
                                            "Campaña":"Campaign",
                                            "Idioma":"Language",
                                            "IdTransaccion":"ID_Transaction",
                                            "ID Agente":"ID_Agent",
                                            "ID Campaña":"ID_Campaign",
                                            "IVR Option":"IVR_Option",
                                            "N encuestas transferidas":"Survey_transfered",
                                            "N encuestas transferidas NC":"Survey_transfered_not_answered",
                                            "Pregunta 1":"Question_1",
                                            "Nota Pregunta 1":"Question_1_mark",
                                            "Pregunta 2":"Question_2",
                                            "Nota Pregunta 2":"Question_2_mark",
                                            "Pregunta 3":"Question_3",
                                            "Nota Pregunta 3":"Question_3_mark"})
                    doc["Date"] = pd.to_datetime(doc["Date"],format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    doc.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)
                    output = doc.astype(str)
                    output.to_gbq(destination_table='Evolution.e_4_CAT_Survey',project_id='nh-cro-forecast', if_exists='append')
                else:
                    Day = str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('e_4_CAT_Survey UPLOADING')
                    with fs.open('trueit_external/Survey_NBA/Calls_Survey_CAT_service_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')  
                    doc = doc.iloc[0:,1:]
                    doc = doc.astype(str)
                    doc=doc.rename(columns={"Fecha":"Date",
                                            "Servicio":"Service",
                                            "Agente":"Agent",
                                            "Campaña":"Campaign",
                                            "Idioma":"Language",
                                            "IdTransaccion":"ID_Transaction",
                                            "ID Agente":"ID_Agent",
                                            "ID Campaña":"ID_Campaign",
                                            "IVR Option":"IVR_Option",
                                            "N encuestas transferidas":"Survey_transfered",
                                            "N encuestas transferidas NC":"Survey_transfered_not_answered",
                                            "Pregunta 1":"Question_1",
                                            "Nota Pregunta 1":"Question_1_mark",
                                            "Pregunta 2":"Question_2",
                                            "Nota Pregunta 2":"Question_2_mark",
                                            "Pregunta 3":"Question_3",
                                            "Nota Pregunta 3":"Question_3_mark"})
                    doc["Date"] = pd.to_datetime(doc["Date"],format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    doc.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)
                    output = doc.astype(str)
                    output.to_gbq(destination_table='Evolution.e_4_CAT_Survey',project_id='nh-cro-forecast', if_exists='append')
    elif Query_number == 10:
            for i in range(int(inicio_dia),int(fin_dia)+1):
                if i <10: 
                    Day = "0"+str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('e_6_Dispatching_oficial UPLOADING')
                    with fs.open('trueit_external/Dispatching/Dispatching_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1', dtype=str)
                    doc = doc.astype(str)
                    output = doc.astype(str)
                    output.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)
                    output.to_gbq(destination_table='Evolution.e_6_Dispatching_oficial',project_id='nh-cro-forecast', if_exists='append',location = 'EU') 
                else:
                    Day = str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('e_6_Dispatching_oficial UPLOADING')
                    with fs.open('trueit_external/Dispatching/Dispatching_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1', dtype=str)
                    doc = doc.astype(str)
                    output = doc.astype(str)
                    output.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)
                    output.to_gbq(destination_table='Evolution.e_6_Dispatching_oficial',project_id='nh-cro-forecast', if_exists='append',location = 'EU') 
    elif Query_number == 11:
            for i in range(int(inicio_dia),int(fin_dia)+1):
                if i <10: 
                    Day = "0"+str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('e_1_NBA_Calls_Codification UPLOADING')
                    with fs.open('trueit_external/Calls_Codifications_NBA/Calls_Codifications_NBA_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')
                    doc = doc.iloc[0:,1:]
                    doc = doc.astype(str)
                    doc=doc.rename(columns={"ID Campaign":"ID_Campaign",
                                            "ivr_opt":"IVR_Option",
                                            "Your company has used NH/contract with us in the past":"Question1_NH_contract_company",
                                            "What cities do they usually travel to?":"Question2_Cities",
                                            "Are you considering a particular property or several? Which / Which ones?":"Question3_Properties",
                                            "Could you tell us in general how many overnight stays you think you would make at the end of the year with us?":"Question4_Overnight_stays_per_year",
                                            "Do you make your reservations directly or through an intermediary?":"Question5_Reservations_intermediary",
                                            "Could you tell us the name of the reservations intermediary?":"Question6_Reservations_intermediary_name",
                                            "Booking - intermediary Name":"Question7_Booking_intermediary_number",
                                            "Are you going to require meeting rooms?":"Question8_Meeting_rooms",
                                            "Do you book your events directly or through an intermediary?":"Question9_Events_intermediary",
                                            "Events - Intermediary Name":"Question10_Events_intermediary_number",
                                            "Could you tell us the name of the events intermediary?":"Question11_Events_intermediary_name",
                                            "Do you accept the conditions of the GPDR?":"Question12_GPDR_conditions"})

                    doc["Date"] = pd.to_datetime(doc["Date"],format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    doc["Hour"] = pd.to_datetime(doc["Hour"]).dt.strftime('%H:%M:%S')
                    doc["Transaction_time"] = pd.to_datetime(doc["Transaction_time"]).dt.strftime('%H:%M:%S')
                    doc["Contact_time"] = pd.to_datetime(doc["Contact_time"]).dt.strftime('%H:%M:%S')
                    doc.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)
                    output = doc.astype(str)
                    output.to_gbq(destination_table='Evolution.e_1_NBA_Calls_Codification',project_id='nh-cro-forecast', if_exists='append')
                else:
                    Day = str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    with fs.open('trueit_external/Calls_Codifications_NBA/Calls_Codifications_NBA_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')
                    doc = doc.iloc[0:,1:]
                    doc = doc.astype(str)
                    doc=doc.rename(columns={"ID Campaign":"ID_Campaign",
                                            "ivr_opt":"IVR_Option",
                                            "Your company has used NH/contract with us in the past":"Question1_NH_contract_company",
                                            "What cities do they usually travel to?":"Question2_Cities",
                                            "Are you considering a particular property or several? Which / Which ones?":"Question3_Properties",
                                            "Could you tell us in general how many overnight stays you think you would make at the end of the year with us?":"Question4_Overnight_stays_per_year",
                                            "Do you make your reservations directly or through an intermediary?":"Question5_Reservations_intermediary",
                                            "Could you tell us the name of the reservations intermediary?":"Question6_Reservations_intermediary_name",
                                            "Booking - intermediary Name":"Question7_Booking_intermediary_number",
                                            "Are you going to require meeting rooms?":"Question8_Meeting_rooms",
                                            "Do you book your events directly or through an intermediary?":"Question9_Events_intermediary",
                                            "Events - Intermediary Name":"Question10_Events_intermediary_number",
                                            "Could you tell us the name of the events intermediary?":"Question11_Events_intermediary_name",
                                            "Do you accept the conditions of the GPDR?":"Question12_GPDR_conditions"})

                    doc["Date"] = pd.to_datetime(doc["Date"],format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    doc["Hour"] = pd.to_datetime(doc["Hour"]).dt.strftime('%H:%M:%S')
                    doc["Transaction_time"] = pd.to_datetime(doc["Transaction_time"]).dt.strftime('%H:%M:%S')
                    doc["Contact_time"] = pd.to_datetime(doc["Contact_time"]).dt.strftime('%H:%M:%S')
                    doc.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)
                    output = doc.astype(str)
                    output.to_gbq(destination_table='Evolution.e_1_NBA_Calls_Codification',project_id='nh-cro-forecast', if_exists='append')
    elif Query_number == 12:
            for i in range(int(inicio_dia),int(fin_dia)+1):
                if i <10: 
                    Day = "0"+str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('e_2_NBA_Mails_Codification UPLOADING')
                    with fs.open('trueit_external/Mails_Codifications_NBA/Mails_Codifications_NBA_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')
                    doc = doc.iloc[0:,1:]
                    doc = doc.astype(str)
                    doc=doc.rename(columns={"ENTRY_DATE":"Entry_date",
                                            "ENTRY_HOUR":"Entry_hour",
                                            "ACTIVITY_ID":"Activity_ID",
                                            "CASE_ID":"Case_ID",
                                            "AGENT_DISTRIBUTED":"Agent_distributed",
                                            "DISTRIBUTED_DATE":"Distributed_date",
                                            "DISTRIBUTED_HOUR":"Distributed_hour",
                                            "QUEUE":"Queue",
                                            "COMPLETED":"Completed",
                                            "AGENT_COMPLETED":"Agent_completed",
                                            "COMPLETED_DATE":"Completed_date",
                                            "COMPLETED_HOUR":"Completed_hour",
                                            "DIRECTION":"Direction",
                                            "Your company has used NH/contract with us in the past":"Question1_NH_contract_company",
                                            "What cities do they usually travel to?":"Question2_Cities",
                                            "Are you considering a particular property or several? Which / Which ones?":"Question3_Properties",
                                            "Could you tell us in general how many overnight stays you think you would make at the end of the year with us?":"Question4_Overnight_stays_per_year",
                                            "Do you make your reservations directly or through an intermediary?":"Question5_Reservations_intermediary",
                                            "Could you tell us the name of the reservations intermediary?":"Question6_Reservations_intermediary_name",
                                            "Booking - intermediary Name":"Question7_Booking_intermediary_number",
                                            "Are you going to require meeting rooms?":"Question8_Meeting_rooms",
                                            "Do you book your events directly or through an intermediary?":"Question9_Events_intermediary",
                                            "Events - Intermediary Name":"Question10_Events_intermediary_number",
                                            "Could you tell us the name of the events intermediary?":"Question11_Events_intermediary_name",
                                            "Do you accept the conditions of the GPDR?":"Question12_GPDR_conditions"})
                    doc["Entry_date"] = pd.to_datetime(doc["Entry_date"],format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    doc["Entry_hour"] = pd.to_datetime(doc["Entry_hour"]).dt.strftime('%H:%M:%S')
                    doc["Distributed_date"] = pd.to_datetime(doc["Distributed_date"],format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    doc["Distributed_hour"] = pd.to_datetime(doc["Distributed_hour"]).dt.strftime('%H:%M:%S')
                    doc["Completed_date"] = pd.to_datetime(doc["Completed_date"],format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    doc["Completed_hour"] = pd.to_datetime(doc["Completed_hour"]).dt.strftime('%H:%M:%S')
                    doc.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)
                    output = doc.astype(str)
                    output.to_gbq(destination_table='Evolution.e_2_NBA_Mails_Codification',project_id='nh-cro-forecast', if_exists='append')
                else:
                    Day = str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('e_2_NBA_Mails_Codification UPLOADING')
                    with fs.open('trueit_external/Mails_Codifications_NBA/Mails_Codifications_NBA_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')
                    doc = doc.iloc[0:,1:]
                    doc = doc.astype(str)
                    doc=doc.rename(columns={"ENTRY_DATE":"Entry_date",
                                            "ENTRY_HOUR":"Entry_hour",
                                            "ACTIVITY_ID":"Activity_ID",
                                            "CASE_ID":"Case_ID",
                                            "AGENT_DISTRIBUTED":"Agent_distributed",
                                            "DISTRIBUTED_DATE":"Distributed_date",
                                            "DISTRIBUTED_HOUR":"Distributed_hour",
                                            "QUEUE":"Queue",
                                            "COMPLETED":"Completed",
                                            "AGENT_COMPLETED":"Agent_completed",
                                            "COMPLETED_DATE":"Completed_date",
                                            "COMPLETED_HOUR":"Completed_hour",
                                            "DIRECTION":"Direction",
                                            "Your company has used NH/contract with us in the past":"Question1_NH_contract_company",
                                            "What cities do they usually travel to?":"Question2_Cities",
                                            "Are you considering a particular property or several? Which / Which ones?":"Question3_Properties",
                                            "Could you tell us in general how many overnight stays you think you would make at the end of the year with us?":"Question4_Overnight_stays_per_year",
                                            "Do you make your reservations directly or through an intermediary?":"Question5_Reservations_intermediary",
                                            "Could you tell us the name of the reservations intermediary?":"Question6_Reservations_intermediary_name",
                                            "Booking - intermediary Name":"Question7_Booking_intermediary_number",
                                            "Are you going to require meeting rooms?":"Question8_Meeting_rooms",
                                            "Do you book your events directly or through an intermediary?":"Question9_Events_intermediary",
                                            "Events - Intermediary Name":"Question10_Events_intermediary_number",
                                            "Could you tell us the name of the events intermediary?":"Question11_Events_intermediary_name",
                                            "Do you accept the conditions of the GPDR?":"Question12_GPDR_conditions"})
                    doc["Entry_date"] = pd.to_datetime(doc["Entry_date"],format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    doc["Entry_hour"] = pd.to_datetime(doc["Entry_hour"]).dt.strftime('%H:%M:%S')
                    doc["Distributed_date"] = pd.to_datetime(doc["Distributed_date"],format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    doc["Distributed_hour"] = pd.to_datetime(doc["Distributed_hour"]).dt.strftime('%H:%M:%S')
                    doc["Completed_date"] = pd.to_datetime(doc["Completed_date"],format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    doc["Completed_hour"] = pd.to_datetime(doc["Completed_hour"]).dt.strftime('%H:%M:%S')
                    doc.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)
                    output = doc.astype(str)
                    output.to_gbq(destination_table='Evolution.e_2_NBA_Mails_Codification',project_id='nh-cro-forecast', if_exists='append')
    elif Query_number == 13:
            for i in range(int(inicio_dia),int(fin_dia)+1):
                if i <10: 
                    Day = "0"+str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('d_1_Traduccion_mails UPLOADING')
                    with fs.open('trueit_external/Mail_Traductions/Mails_Traducciones_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')
                    doc = doc.iloc[0:,1:]
                    doc = doc.astype(str)
                    doc["Date"] = pd.to_datetime(doc["Date"],format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    doc["Time"] = pd.to_datetime(doc["Time"]).dt.strftime('%H:%M:%S')
                    doc["Queue_time"] = pd.to_datetime(doc["Queue_time"]).dt.strftime('%H:%M:%S')
                    doc["Agent_total_mail_time"] = pd.to_datetime(doc["Agent_total_mail_time"]).dt.strftime('%H:%M:%S')
                    doc["Agent_real_mail_time"] = pd.to_datetime(doc["Agent_real_mail_time"]).dt.strftime('%H:%M:%S')
                    doc["Transaction_time"] = pd.to_datetime(doc["Transaction_time"]).dt.strftime('%H:%M:%S')
                    doc["Traduction_time"] = pd.to_datetime(doc["Traduction_time"]).dt.strftime('%H:%M:%S')
                    doc["Agent_traduction_time"] = pd.to_datetime(doc["Agent_traduction_time"]).dt.strftime('%H:%M:%S')
                    doc.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)
                    output = doc.astype(str)
                    output.to_gbq(destination_table='Evolution.d_1_Traduccion_mails',project_id='nh-cro-forecast', if_exists='append')
                else:
                    Day = str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('d_1_Traduccion_mails UPLOADING')
                    with fs.open('trueit_external/Mail_Traductions/Mails_Traducciones_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')
                    doc = doc.iloc[0:,1:]
                    doc = doc.astype(str)
                    doc["Date"] = pd.to_datetime(doc["Date"],format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    doc["Time"] = pd.to_datetime(doc["Time"]).dt.strftime('%H:%M:%S')
                    doc["Queue_time"] = pd.to_datetime(doc["Queue_time"]).dt.strftime('%H:%M:%S')
                    doc["Agent_total_mail_time"] = pd.to_datetime(doc["Agent_total_mail_time"]).dt.strftime('%H:%M:%S')
                    doc["Agent_real_mail_time"] = pd.to_datetime(doc["Agent_real_mail_time"]).dt.strftime('%H:%M:%S')
                    doc["Transaction_time"] = pd.to_datetime(doc["Transaction_time"]).dt.strftime('%H:%M:%S')
                    doc["Traduction_time"] = pd.to_datetime(doc["Traduction_time"]).dt.strftime('%H:%M:%S')
                    doc["Agent_traduction_time"] = pd.to_datetime(doc["Agent_traduction_time"]).dt.strftime('%H:%M:%S')
                    doc.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)
                    output = doc.astype(str)
                    output.to_gbq(destination_table='Evolution.d_1_Traduccion_mails',project_id='nh-cro-forecast', if_exists='append')
    elif Query_number == 14:
            for i in range(int(inicio_dia),int(fin_dia)+1):
                if i <10: 
                    Day = "0"+str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('e_9_Calls_Cod_Transaction UPLOADING')
                    with fs.open('trueit_external/Calls_Codifications_Transaction/Calls_Cod_Transaction_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')
                    doc = doc.iloc[0:,1:]
                    doc = doc.astype(str)
                    doc=doc.rename(columns={"ID Agent":"ID_Agent",
                                            "Campaña":"Campaign",
                                            "ID Campaña":"ID_Campaign",
                                            "LANGUAGE":"Language",
                                            "IVR OPTION":"IVR_Option",
                                            "LLAMADAS_IN":"Calls_IN",
                                            "LLAMADAS_OUT":"Calls_OUT",
                                            "T_DURACION_IN":"T_Duration_IN",
                                            "T_DURACION_OUT":"T_Duration_OUT",
                                            "T_DURACION":"Time_Duration"})
                    doc = doc.astype(str)
                    doc["Date"] = pd.to_datetime(doc["Date"],format="%d/%m/%Y").dt.strftime('%Y-%m-%d')
                    doc["T_Duration_IN"] = pd.to_datetime(doc["T_Duration_IN"]).dt.strftime('%H:%M:%S')
                    doc["T_Duration_OUT"] = pd.to_datetime(doc["T_Duration_OUT"]).dt.strftime('%H:%M:%S')
                    doc["Time_Duration"] = pd.to_datetime(doc["Time_Duration"]).dt.strftime('%H:%M:%S')
                    doc.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)
                    output = doc.astype(str)
                    output.to_gbq(destination_table='Evolution.e_9_Calls_Cod_Transaction',project_id='nh-cro-forecast', if_exists='append')
                else:
                    Day = str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('e_9_Calls_Cod_Transaction UPLOADING')
                    with fs.open('trueit_external/Calls_Codifications_Transaction/Calls_Cod_Transaction_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')
                    doc = doc.iloc[0:,1:]
                    doc = doc.astype(str)
                    doc=doc.rename(columns={"ID Agent":"ID_Agent",
                                            "Campaña":"Campaign",
                                            "ID Campaña":"ID_Campaign",
                                            "LANGUAGE":"Language",
                                            "IVR OPTION":"IVR_Option",
                                            "LLAMADAS_IN":"Calls_IN",
                                            "LLAMADAS_OUT":"Calls_OUT",
                                            "T_DURACION_IN":"T_Duration_IN",
                                            "T_DURACION_OUT":"T_Duration_OUT",
                                            "T_DURACION":"Time_Duration"})
                    doc = doc.astype(str)
                    doc["Date"] = pd.to_datetime(doc["Date"],format="%d/%m/%Y").dt.strftime('%Y-%m-%d')
                    doc["T_Duration_IN"] = pd.to_datetime(doc["T_Duration_IN"]).dt.strftime('%H:%M:%S')
                    doc["T_Duration_OUT"] = pd.to_datetime(doc["T_Duration_OUT"]).dt.strftime('%H:%M:%S')
                    doc["Time_Duration"] = pd.to_datetime(doc["Time_Duration"]).dt.strftime('%H:%M:%S')
                    doc.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)
                    output = doc.astype(str)
                    output.to_gbq(destination_table='Evolution.e_9_Calls_Cod_Transaction',project_id='nh-cro-forecast', if_exists='append')
    elif Query_number == 15:
            for i in range(int(inicio_dia),int(fin_dia)+1):
                if i <10: 
                    Day = "0"+str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('e_10_Coordination_status UPLOADING')
                    with fs.open('trueit_external/Coordination_breaks/Status_Coordination_breaks_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')       
                    doc = doc.iloc[0:,1:]
                    r = doc.astype(str)
                    r["Date"] = pd.to_datetime(r["Date"],format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    r["Inicio_status_date"] = pd.to_datetime(r["Inicio_status"]).dt.strftime('%Y-%m-%d')
                    r["Inicio_status_hour"] = pd.to_datetime(r["Inicio_status"]).dt.strftime('%H:%M:%S')
                    r["End_status_date"] = pd.to_datetime(r["End_status"]).dt.strftime('%Y-%m-%d')
                    r["End_status_hour"] = pd.to_datetime(r["End_status"]).dt.strftime('%H:%M:%S')
                    output = r.astype(str)
                    output.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)
                    output.to_gbq(destination_table='Evolution.e_10_Coordination_status',project_id='nh-cro-forecast', if_exists='append')
                else:
                    Day = str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('e_10_Coordination_status UPLOADING')
                    with fs.open('trueit_external/Coordination_breaks/Status_Coordination_breaks_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')       
                    doc = doc.iloc[0:,1:]
                    r = doc.astype(str)
                    r["Date"] = pd.to_datetime(r["Date"],format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    r["Inicio_status_date"] = pd.to_datetime(r["Inicio_status"]).dt.strftime('%Y-%m-%d')
                    r["Inicio_status_hour"] = pd.to_datetime(r["Inicio_status"]).dt.strftime('%H:%M:%S')
                    r["End_status_date"] = pd.to_datetime(r["End_status"]).dt.strftime('%Y-%m-%d')
                    r["End_status_hour"] = pd.to_datetime(r["End_status"]).dt.strftime('%H:%M:%S')
                    output = r.astype(str)
                    output.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)
                    output.to_gbq(destination_table='Evolution.e_10_Coordination_status',project_id='nh-cro-forecast', if_exists='append')
    elif Query_number == 16:
            for i in range(int(inicio_dia),int(fin_dia)+1):
                if i <10: 
                    Day = "0"+str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('e_11_CAT_Mails_Codification UPLOADING')
                    with fs.open('trueit_external/Mails_Codifications_CAT/Mails_Codifications_CAT_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')
                    doc = doc.iloc[0:,1:]
                    doc = doc.astype(str)
                    doc=doc.rename(columns={"Service":"Service",
                                            "ENTRY_DATE":"Entry_date",
                                            "ENTRY_HOUR":"Entry_hour",
                                            "ACTIVITY_ID":"Activity_ID",
                                            "CASE_ID":"Case_ID",
                                            "Alias":"Alias",
                                            "AGENT_DISTRIBUTED":"Agent_distributed",
                                            "DISTRIBUTED_DATE":"Distributed_date",
                                            "DISTRIBUTED_HOUR":"Distributed_hour",
                                            "QUEUE":"Queue",
                                            "COMPLETED":"Completed",
                                            "AGENT_COMPLETED":"Agent_completed",
                                            "COMPLETED_DATE":"Completed_date",
                                            "COMPLETED_HOUR":"Completed_hour",
                                            "Subtype":"Subtype",
                                            "DIRECTION":"Direction",
                                            "Your company has used NH/contract with us in the past":"Question1_NH_contract_company",
                                            "What cities do they usually travel to?":"Question2_Cities",
                                            "Are you considering a particular property or several? Which / Which ones?":"Question3_Properties",
                                            "Could you tell us in general how many overnight stays you think you would make at the end of the year with us?":"Question4_Overnight_stays_per_year",
                                            "Do you make your reservations directly or through an intermediary?":"Question5_Reservations_intermediary",
                                            "Could you tell us the name of the reservations intermediary?":"Question6_Reservations_intermediary_name",
                                            "Booking - intermediary Name":"Question7_Booking_intermediary_number",
                                            "Are you going to require meeting rooms?":"Question8_Meeting_rooms",
                                            "Do you book your events directly or through an intermediary?":"Question9_Events_intermediary",
                                            "Events - Intermediary Name":"Question10_Events_intermediary_number",
                                            "Could you tell us the name of the events intermediary?":"Question11_Events_intermediary_name",
                                            "Do you accept the conditions of the GPDR?":"Question12_GDPR_conditions",
                                            "Remarks":"Remarks",
                                            "PID empresa":"PID",
                                            "nombre empresa":"Enterprise_name",
                                            "categoria A/B/C":"Category",
                                            "terms & conditions aceptados yes/no":"Terms_and_condition",
                                            "credentials yes/no":"Credentials",
                                            "total revenue last year":"Revenue_last_year",
                                            "email":"Email",
                                        })
                    doc["Entry_date"] = pd.to_datetime(doc["Entry_date"],format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    doc["Entry_hour"] = pd.to_datetime(doc["Entry_hour"]).dt.strftime('%H:%M:%S')
                    doc["Distributed_date"] = pd.to_datetime(doc["Distributed_date"],format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    doc["Distributed_hour"] = pd.to_datetime(doc["Distributed_hour"]).dt.strftime('%H:%M:%S')
                    doc["Completed_date"] = pd.to_datetime(doc["Completed_date"],format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    doc["Completed_hour"] = pd.to_datetime(doc["Completed_hour"]).dt.strftime('%H:%M:%S')
                    doc.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)
                    output = doc.astype(str)
                    output.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)
                    output.to_gbq(destination_table='Evolution.e_11_CAT_Mails_Codification',project_id='nh-cro-forecast', if_exists='append')
                else:
                    Day = str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('e_11_CAT_Mails_Codification UPLOADING')
                    with fs.open('trueit_external/Mails_Codifications_CAT/Mails_Codifications_CAT_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')
                    doc = doc.iloc[0:,1:]
                    doc = doc.astype(str)
                    doc=doc.rename(columns={"Service":"Service",
                                            "ENTRY_DATE":"Entry_date",
                                            "ENTRY_HOUR":"Entry_hour",
                                            "ACTIVITY_ID":"Activity_ID",
                                            "CASE_ID":"Case_ID",
                                            "Alias":"Alias",
                                            "AGENT_DISTRIBUTED":"Agent_distributed",
                                            "DISTRIBUTED_DATE":"Distributed_date",
                                            "DISTRIBUTED_HOUR":"Distributed_hour",
                                            "QUEUE":"Queue",
                                            "COMPLETED":"Completed",
                                            "AGENT_COMPLETED":"Agent_completed",
                                            "COMPLETED_DATE":"Completed_date",
                                            "COMPLETED_HOUR":"Completed_hour",
                                            "Subtype":"Subtype",
                                            "DIRECTION":"Direction",
                                            "Your company has used NH/contract with us in the past":"Question1_NH_contract_company",
                                            "What cities do they usually travel to?":"Question2_Cities",
                                            "Are you considering a particular property or several? Which / Which ones?":"Question3_Properties",
                                            "Could you tell us in general how many overnight stays you think you would make at the end of the year with us?":"Question4_Overnight_stays_per_year",
                                            "Do you make your reservations directly or through an intermediary?":"Question5_Reservations_intermediary",
                                            "Could you tell us the name of the reservations intermediary?":"Question6_Reservations_intermediary_name",
                                            "Booking - intermediary Name":"Question7_Booking_intermediary_number",
                                            "Are you going to require meeting rooms?":"Question8_Meeting_rooms",
                                            "Do you book your events directly or through an intermediary?":"Question9_Events_intermediary",
                                            "Events - Intermediary Name":"Question10_Events_intermediary_number",
                                            "Could you tell us the name of the events intermediary?":"Question11_Events_intermediary_name",
                                            "Do you accept the conditions of the GPDR?":"Question12_GDPR_conditions",
                                            "Remarks":"Remarks",
                                            "PID empresa":"PID",
                                            "nombre empresa":"Enterprise_name",
                                            "categoria A/B/C":"Category",
                                            "terms & conditions aceptados yes/no":"Terms_and_condition",
                                            "credentials yes/no":"Credentials",
                                            "total revenue last year":"Revenue_last_year",
                                            "email":"Email",
                                        })
                    doc["Entry_date"] = pd.to_datetime(doc["Entry_date"],format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    doc["Entry_hour"] = pd.to_datetime(doc["Entry_hour"]).dt.strftime('%H:%M:%S')
                    doc["Distributed_date"] = pd.to_datetime(doc["Distributed_date"],format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    doc["Distributed_hour"] = pd.to_datetime(doc["Distributed_hour"]).dt.strftime('%H:%M:%S')
                    doc["Completed_date"] = pd.to_datetime(doc["Completed_date"],format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    doc["Completed_hour"] = pd.to_datetime(doc["Completed_hour"]).dt.strftime('%H:%M:%S')
                    doc.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)
                    output = doc.astype(str)
                    output.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)
                    output.to_gbq(destination_table='Evolution.e_11_CAT_Mails_Codification',project_id='nh-cro-forecast', if_exists='append')
    elif Query_number == 17:
            for i in range(int(inicio_dia),int(fin_dia)+1):
                if i <10: 
                    Day = "0"+str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('e_12_CAT_Calls_Codification UPLOADING')
                    with fs.open('trueit_external/Calls_Codifications_CAT/Calls_Codifications_CAT_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')
                    doc = doc.iloc[0:,1:]
                    doc = doc.astype(str)
                    doc=doc.rename(columns={"Service":"Service",
                                            "Date":"Date",
                                            "Hour":"Hour",
                                            "Agent":"Agent",
                                            "ID_Agent":"Agent_ID",
                                            "Campaign":"Campaign",
                                            "ID Campaign":"ID_Campaign",
                                            "Lang":"Lang",
                                            "ivr_opt":"IVR_Option",
                                            "Type":"Type",
                                            "Transaction_time":"Transaction_time",
                                            "Contact_time":"Contact_time",
                                            "Closure":"Closure",
                                            "Your company has used NH/contract with us in the past":"Question1_NH_contract_company",
                                            "What cities do they usually travel to?":"Question2_cities",
                                            "Are you considering a particular property or several? Which / Which ones?":"Question3_Properties",
                                            "Could you tell us in general how many overnight stays you think you would make at the end of the year with us?":"Question4_Overnight_stays_per_year",
                                            "Do you make your reservations directly or through an intermediary?":"Question5_Reservations_intermediary",
                                            "Could you tell us the name of the reservations intermediary?":"Question6_Reservations_intermediary_name",
                                            "Booking - intermediary Name":"Question7_Booking_intermediary_number",
                                            "Are you going to require meeting rooms?":"Question8_Meeting_rooms",
                                            "Do you book your events directly or through an intermediary?":"Question9_Events_intermediary",
                                            "Events - Intermediary Name":"Question10_Events_intermediary_number",
                                            "Could you tell us the name of the events intermediary?":"Question11_Events_intermediary_name",
                                            "Do you accept the conditions of the GPDR?":"Question12_GDPR_conditions",
                                            "Remarks":"Remarks",
                                            "PID empresa":"PID",
                                            "nombre empresa":"Enterprise_name",
                                            "categoria A/B/C":"Category",
                                            "terms & conditions aceptados yes/no":"Terms_and_condition",
                                            "credentials yes/no":"Credentials",
                                            "total revenue last year":"Revenue_last_year",
                                            "email":"Email",
                                        })
                    doc["Date"] = pd.to_datetime(doc["Date"],format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    doc["Hour"] = pd.to_datetime(doc["Hour"]).dt.strftime('%H:%M:%S')
                    doc["Transaction_time"] = pd.to_datetime(doc["Transaction_time"]).dt.strftime('%H:%M:%S')
                    doc["Contact_time"] = pd.to_datetime(doc["Contact_time"]).dt.strftime('%H:%M:%S')
                    output = doc.astype(str)
                    output.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)
                    output.to_gbq(destination_table='Evolution.e_12_CAT_Calls_Codification',project_id='nh-cro-forecast', if_exists='append')
                else:
                    Day = str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('e_12_CAT_Calls_Codification UPLOADING')
                    with fs.open('trueit_external/Calls_Codifications_CAT/Calls_Codifications_CAT_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')
                    doc = doc.iloc[0:,1:]
                    doc = doc.astype(str)
                    doc=doc.rename(columns={"Service":"Service",
                                            "Date":"Date",
                                            "Hour":"Hour",
                                            "Agent":"Agent",
                                            "ID_Agent":"Agent_ID",
                                            "Campaign":"Campaign",
                                            "ID Campaign":"ID_Campaign",
                                            "Lang":"Lang",
                                            "ivr_opt":"IVR_Option",
                                            "Type":"Type",
                                            "Transaction_time":"Transaction_time",
                                            "Contact_time":"Contact_time",
                                            "Closure":"Closure",
                                            "Your company has used NH/contract with us in the past":"Question1_NH_contract_company",
                                            "What cities do they usually travel to?":"Question2_cities",
                                            "Are you considering a particular property or several? Which / Which ones?":"Question3_Properties",
                                            "Could you tell us in general how many overnight stays you think you would make at the end of the year with us?":"Question4_Overnight_stays_per_year",
                                            "Do you make your reservations directly or through an intermediary?":"Question5_Reservations_intermediary",
                                            "Could you tell us the name of the reservations intermediary?":"Question6_Reservations_intermediary_name",
                                            "Booking - intermediary Name":"Question7_Booking_intermediary_number",
                                            "Are you going to require meeting rooms?":"Question8_Meeting_rooms",
                                            "Do you book your events directly or through an intermediary?":"Question9_Events_intermediary",
                                            "Events - Intermediary Name":"Question10_Events_intermediary_number",
                                            "Could you tell us the name of the events intermediary?":"Question11_Events_intermediary_name",
                                            "Do you accept the conditions of the GPDR?":"Question12_GDPR_conditions",
                                            "Remarks":"Remarks",
                                            "PID empresa":"PID",
                                            "nombre empresa":"Enterprise_name",
                                            "categoria A/B/C":"Category",
                                            "terms & conditions aceptados yes/no":"Terms_and_condition",
                                            "credentials yes/no":"Credentials",
                                            "total revenue last year":"Revenue_last_year",
                                            "email":"Email",
                                        })
                    doc["Date"] = pd.to_datetime(doc["Date"],format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    doc["Hour"] = pd.to_datetime(doc["Hour"]).dt.strftime('%H:%M:%S')
                    doc["Transaction_time"] = pd.to_datetime(doc["Transaction_time"]).dt.strftime('%H:%M:%S')
                    doc["Contact_time"] = pd.to_datetime(doc["Contact_time"]).dt.strftime('%H:%M:%S')
                    output = doc.astype(str)
                    output.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)
                    output.to_gbq(destination_table='Evolution.e_12_CAT_Calls_Codification',project_id='nh-cro-forecast', if_exists='append')
    elif Query_number == 18:
            for i in range(int(inicio_dia),int(fin_dia)+1):
                if i <10: 
                    Day = "0"+str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('e_13_Guest_Experience_status UPLOADING')
                    with fs.open('trueit_external/Guest_experience_breaks/Status_Guest_Experience_breaks_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')       
                    doc = doc.iloc[0:,1:]
                    r = doc.astype(str)
                    r["Date"] = pd.to_datetime(r["Date"],format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    r["Inicio_status_date"] = pd.to_datetime(r["Inicio_status"]).dt.strftime('%Y-%m-%d')
                    r["Inicio_status_hour"] = pd.to_datetime(r["Inicio_status"]).dt.strftime('%H:%M:%S')
                    r["End_status_date"] = pd.to_datetime(r["End_status"]).dt.strftime('%Y-%m-%d')
                    r["End_status_hour"] = pd.to_datetime(r["End_status"]).dt.strftime('%H:%M:%S')
                    output = r.astype(str)
                    output.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)
                    output.to_gbq(destination_table='Evolution.e_13_Guest_Experience_status',project_id='nh-cro-forecast', if_exists='append')
                else:
                    Day = str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('e_13_Guest_Experience_status UPLOADING')
                    with fs.open('trueit_external/Guest_experience_breaks/Status_Guest_Experience_breaks_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')       
                    doc = doc.iloc[0:,1:]
                    r = doc.astype(str)
                    r["Date"] = pd.to_datetime(r["Date"],format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    r["Inicio_status_date"] = pd.to_datetime(r["Inicio_status"]).dt.strftime('%Y-%m-%d')
                    r["Inicio_status_hour"] = pd.to_datetime(r["Inicio_status"]).dt.strftime('%H:%M:%S')
                    r["End_status_date"] = pd.to_datetime(r["End_status"]).dt.strftime('%Y-%m-%d')
                    r["End_status_hour"] = pd.to_datetime(r["End_status"]).dt.strftime('%H:%M:%S')
                    output = r.astype(str)
                    output.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)
                    output.to_gbq(destination_table='Evolution.e_13_Guest_Experience_status',project_id='nh-cro-forecast', if_exists='append')
    elif Query_number == 19:
            for i in range(int(inicio_dia),int(fin_dia)+1):
                if i <10: 
                    Day = "0"+str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('e_14_waiting_time UPLOADING')
                    with fs.open('trueit_external/Waiting_time/Calls_Waiting_report_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')
                    r = doc.astype(str)
                    r["Fecha"] = pd.to_datetime(r["Fecha"]).dt.strftime('%Y-%m-%d')
                    r["Start_hour"] = pd.to_datetime(r["Start_hour"]).dt.strftime('%H:%M:%S')
                    r["End_hour"] = pd.to_datetime(r["End_hour"]).dt.strftime('%H:%M:%S')
                    r["Duration"] = pd.to_datetime(r["Duration"]).dt.strftime('%H:%M:%S')
                    r["T_DBR"] = pd.to_datetime(r["T_DBR"]).dt.strftime('%H:%M:%S')
                    r["T_COLA"] = pd.to_datetime(r["T_COLA"]).dt.strftime('%H:%M:%S')
                    r["T_ACW"] = pd.to_datetime(r["T_ACW"]).dt.strftime('%H:%M:%S')
                    output = r.astype(str)
                    output.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)
                    output.to_gbq(destination_table='Evolution.e_14_waiting_time',project_id='nh-cro-forecast', if_exists='append')
                else:
                    Day = str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('e_14_waiting_time UPLOADING')
                    with fs.open('trueit_external/Waiting_time/Calls_Waiting_report_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')
                    r = doc.astype(str)
                    r["Fecha"] = pd.to_datetime(r["Fecha"]).dt.strftime('%Y-%m-%d')
                    r["Start_hour"] = pd.to_datetime(r["Start_hour"]).dt.strftime('%H:%M:%S')
                    r["End_hour"] = pd.to_datetime(r["End_hour"]).dt.strftime('%H:%M:%S')
                    r["Duration"] = pd.to_datetime(r["Duration"]).dt.strftime('%H:%M:%S')
                    r["T_DBR"] = pd.to_datetime(r["T_DBR"]).dt.strftime('%H:%M:%S')
                    r["T_COLA"] = pd.to_datetime(r["T_COLA"]).dt.strftime('%H:%M:%S')
                    r["T_ACW"] = pd.to_datetime(r["T_ACW"]).dt.strftime('%H:%M:%S')
                    output = r.astype(str)
                    output.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)
                    output.to_gbq(destination_table='Evolution.e_14_waiting_time',project_id='nh-cro-forecast', if_exists='append')
    elif Query_number == 20:
            for i in range(int(inicio_dia),int(fin_dia)+1):
                if i <10: 
                    Day = "0"+str(i)
                    Day_1 = int(Day)-1
                    Day_1 = "0"+str(Day_1)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    time.sleep(0.5)
                    print('e_15_agent_session_control UPLOADING')
                    time.sleep(0.5)
                    with fs.open('trueit_external/Agent_session_control/Status_Agent_sessions_control_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')      
                    r = doc.astype(str)
                    f = r.rename(columns={"Agent ID":"Agent_ID",
                                        "Session Start":"Session_start",
                                        "Session Available":"Session_available",
                                        "Session End":"Session_end",
                                        "Time Connected":"Time_connected",
                                        "Time Available":"Time_available",
                                        "Time Break":"Time_break",
                                        "Time Visual Rest":"Time_visual_rest"
                                        })
                    f["Date"] = pd.to_datetime(f["Date"]).dt.strftime('%Y-%m-%d')
                    f['Date'] = Year+"-"+Month+"-"+Day_1
                    f["Session_start"] = pd.to_datetime(f["Session_start"]).dt.strftime('%Y-%m-%d %H:%M:%S')
                    f["Session_available"] = pd.to_datetime(f["Session_available"]).dt.strftime('%Y-%m-%d %H:%M:%S')
                    f["Session_end"] = pd.to_datetime(f["Session_end"]).dt.strftime('%Y-%m-%d %H:%M:%S')
                    f["Time_connected"] = pd.to_datetime(f["Time_connected"]).dt.strftime('%H:%M:%S')
                    f["Time_available"] = pd.to_datetime(f["Time_available"]).dt.strftime('%H:%M:%S')
                    f["Time_break"] = pd.to_datetime(f["Time_break"]).dt.strftime('%H:%M:%S')
                    output = f.astype(str)
                    output.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)
                    output.drop('GroupLevel', axis=1,inplace=True)
                    output.to_gbq(destination_table='Evolution.e_15_agent_session_control',project_id='nh-cro-forecast', if_exists='append')

                elif i == 10:
                     Day = str(i)
                     Day_1 = int(Day) -1
                     Day_1 = "0" + str(Day_1)
                     print(f"Subiendo datos del archivo de día:{Day}")
                     time.sleep(0.5)
                     print('e_15_agent_session_control UPLOADING')
                     time.sleep(0.5)
                     with fs.open('trueit_external/Agent_session_control/Status_Agent_sessions_control_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')      
                     r = doc.astype(str)
                     f = r.rename(columns={"Agent ID":"Agent_ID",
                                        "Session Start":"Session_start",
                                        "Session Available":"Session_available",
                                        "Session End":"Session_end",
                                        "Time Connected":"Time_connected",
                                        "Time Available":"Time_available",
                                        "Time Break":"Time_break",
                                        "Time Visual Rest":"Time_visual_rest"
                                        })
                     f["Date"] = pd.to_datetime(f["Date"]).dt.strftime('%Y-%m-%d')
                     f['Date'] = Year+"-"+Month+"-"+Day_1
                     f["Session_start"] = pd.to_datetime(f["Session_start"]).dt.strftime('%Y-%m-%d %H:%M:%S')
                     f["Session_available"] = pd.to_datetime(f["Session_available"]).dt.strftime('%Y-%m-%d %H:%M:%S')
                     f["Session_end"] = pd.to_datetime(f["Session_end"]).dt.strftime('%Y-%m-%d %H:%M:%S')
                     f["Time_connected"] = pd.to_datetime(f["Time_connected"]).dt.strftime('%H:%M:%S')
                     f["Time_available"] = pd.to_datetime(f["Time_available"]).dt.strftime('%H:%M:%S')
                     f["Time_break"] = pd.to_datetime(f["Time_break"]).dt.strftime('%H:%M:%S')
                     output = f.astype(str)
                     output.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)
                     output.drop('GroupLevel', axis=1,inplace=True)
                     output.to_gbq(destination_table='Evolution.e_15_agent_session_control',project_id='nh-cro-forecast', if_exists='append')


    
                else:
                    Day = str(i)
                    Day_1 = int(Day)-1
                    Day_1 = str(Day_1)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    time.sleep(0.5)
                    print('e_15_agent_session_control UPLOADING')
                    time.sleep(0.5)
                    with fs.open('trueit_external/Agent_session_control/Status_Agent_sessions_control_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')      
                    r = doc.astype(str)
                    f = r.rename(columns={"Agent ID":"Agent_ID",
                                        "Session Start":"Session_start",
                                        "Session Available":"Session_available",
                                        "Session End":"Session_end",
                                        "Time Connected":"Time_connected",
                                        "Time Available":"Time_available",
                                        "Time Break":"Time_break",
                                        "Time Visual Rest":"Time_visual_rest"
                                        })
                    f["Date"] = pd.to_datetime(f["Date"]).dt.strftime('%Y-%m-%d')
                    f['Date'] = Year+"-"+Month+"-"+Day_1
                    f["Session_start"] = pd.to_datetime(f["Session_start"]).dt.strftime('%Y-%m-%d %H:%M:%S')
                    f["Session_available"] = pd.to_datetime(f["Session_available"]).dt.strftime('%Y-%m-%d %H:%M:%S')
                    f["Session_end"] = pd.to_datetime(f["Session_end"]).dt.strftime('%Y-%m-%d %H:%M:%S')
                    f["Time_connected"] = pd.to_datetime(f["Time_connected"]).dt.strftime('%H:%M:%S')
                    f["Time_available"] = pd.to_datetime(f["Time_available"]).dt.strftime('%H:%M:%S')
                    f["Time_break"] = pd.to_datetime(f["Time_break"]).dt.strftime('%H:%M:%S')
                    output = f.astype(str)
                    output.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)
                    output.drop('GroupLevel', axis=1,inplace=True)
                    output.to_gbq(destination_table='Evolution.e_15_agent_session_control',project_id='nh-cro-forecast', if_exists='append')
    elif Query_number == 21:
            for i in range(int(inicio_dia),int(fin_dia)+1):
                if i <10: 
                    Day = "0"+str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('e_16_Auditorias UPLOADING')
                    with fs.open('trueit_external/Auditorias/Audit_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1',dtype = str)      
                    doc = doc.iloc[0:,1:]
                    r = doc.astype(str)   
                    r.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)   
                    r["Event_Date"] = pd.to_datetime(r["Event_Date"],format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    r["Event_Hour"] = pd.to_datetime(r["Event_Hour"]).dt.strftime('%H:%M:%S') 
                    r["Audit_Date"] = pd.to_datetime(r["Audit_Date"],format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    r["Audit_Hour"] = pd.to_datetime(r["Audit_Hour"]).dt.strftime('%H:%M:%S')   
                    r["Mark"] = r["Mark"].str.replace(',','.')
                    r["Mark_Factor"] = r["Mark_Factor"].str.replace(',','.')
                    r["Target"] = r["Target"].str.replace(',','.')  
                    r.to_gbq(destination_table='Evolution.e_16_Auditorias',project_id='nh-cro-forecast', if_exists='append')
                else:
                    Day = str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('e_16_Auditorias UPLOADING')
                    with fs.open('trueit_external/Auditorias/Audit_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1',dtype = str)      
                    doc = doc.iloc[0:,1:]
                    r = doc.astype(str)   
                    r.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)   
                    r["Event_Date"] = pd.to_datetime(r["Event_Date"],format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    r["Event_Hour"] = pd.to_datetime(r["Event_Hour"]).dt.strftime('%H:%M:%S') 
                    r["Audit_Date"] = pd.to_datetime(r["Audit_Date"],format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    r["Audit_Hour"] = pd.to_datetime(r["Audit_Hour"]).dt.strftime('%H:%M:%S')   
                    r["Mark"] = r["Mark"].str.replace(',','.')
                    r["Mark_Factor"] = r["Mark_Factor"].str.replace(',','.')
                    r["Target"] = r["Target"].str.replace(',','.')  
                    r.to_gbq(destination_table='Evolution.e_16_Auditorias',project_id='nh-cro-forecast', if_exists='append')
    elif Query_number == 22:
            for i in range(int(inicio_dia),int(fin_dia)+1):
                if i <10: 
                    Day = "0"+str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('Agents_sessions UPLOADING')
                    with fs.open('trueit_external/Agent_Sessions/Agents_Sessions_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')      
                    doc.columns = ['Date','Service','Agent','Agent_SAP','Agent_ID','Worktop','Begin_session_raw','Available_session_raw','End_session_raw','Session_duration','n_breaks','Break_reason','Break_ID','Break_duration']
                    doc["Date"] = pd.to_datetime(doc["Date"], format = '%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    doc["Begin_session_date"] = pd.to_datetime(doc["Begin_session_raw"]).dt.strftime('%Y-%m-%d')
                    doc["Begin_session_hour"] = pd.to_datetime(doc["Begin_session_raw"]).dt.strftime('%H:%M:%S')
                    doc["Available_session_date"] = pd.to_datetime(doc["Available_session_raw"]).dt.strftime('%Y-%m-%d')
                    doc["Available_session_hour"] = pd.to_datetime(doc["Available_session_raw"]).dt.strftime('%H:%M:%S')
                    doc["End_session_date"] = pd.to_datetime(doc["End_session_raw"]).dt.strftime('%Y-%m-%d')
                    doc["End_session_hour"] = pd.to_datetime(doc["End_session_raw"]).dt.strftime('%H:%M:%S')
                    doc["Agents_sessions"] = pd.to_datetime(doc["Session_duration"]).dt.strftime('%H:%M:%S')
                    doc["Break_duration"] = pd.to_datetime(doc["Break_duration"]).dt.strftime('%H:%M:%S')
                    doc["Session_duration"] = pd.to_datetime(doc["Session_duration"]).dt.strftime('%H:%M:%S')
                    Output = doc.astype(str)
                    Output = Output.iloc[:,[0,1,2,3,4,5,6,14,15,7,16,17,8,18,19,9,10,11,12,13]]
                    convert_dict = {'Date':object,
                                    'Service':object,
                                    'Agent':object,
                                    'Agent_SAP':object,
                                    'Agent_ID':object,
                                    'Worktop':object,
                                    'Begin_session_raw':object,
                                    'Begin_session_date':object,
                                    'Begin_session_hour':object,
                                    'Available_session_raw':object,
                                    'Available_session_date':object,
                                    'Available_session_hour':object,
                                    'End_session_raw':object,
                                    'End_session_date':object,
                                    'End_session_hour':object,
                                    'Session_duration':object,
                                    'n_breaks':object,
                                    'Break_reason':object,
                                    'Break_ID':object,
                                    'Break_duration':object} 
                    Call_db = Output.astype(convert_dict)
                    Call_db = Call_db.astype(str)
                    Call_db.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None], inplace=True)
                    Call_db.to_gbq(destination_table='Evolution.Agents_sessions',project_id='nh-cro-forecast', if_exists='append')
                else:
                    Day = str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('Agents_sessions UPLOADING')
                    with fs.open('trueit_external/Agent_Sessions/Agents_Sessions_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')      
                    doc.columns = ['Date','Service','Agent','Agent_SAP','Agent_ID','Worktop','Begin_session_raw','Available_session_raw','End_session_raw','Session_duration','n_breaks','Break_reason','Break_ID','Break_duration']
                    doc["Date"] = pd.to_datetime(doc["Date"], format = '%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    doc["Begin_session_date"] = pd.to_datetime(doc["Begin_session_raw"]).dt.strftime('%Y-%m-%d')
                    doc["Begin_session_hour"] = pd.to_datetime(doc["Begin_session_raw"]).dt.strftime('%H:%M:%S')
                    doc["Available_session_date"] = pd.to_datetime(doc["Available_session_raw"]).dt.strftime('%Y-%m-%d')
                    doc["Available_session_hour"] = pd.to_datetime(doc["Available_session_raw"]).dt.strftime('%H:%M:%S')
                    doc["End_session_date"] = pd.to_datetime(doc["End_session_raw"]).dt.strftime('%Y-%m-%d')
                    doc["End_session_hour"] = pd.to_datetime(doc["End_session_raw"]).dt.strftime('%H:%M:%S')
                    doc["Agents_sessions"] = pd.to_datetime(doc["Session_duration"]).dt.strftime('%H:%M:%S')
                    doc["Break_duration"] = pd.to_datetime(doc["Break_duration"]).dt.strftime('%H:%M:%S')
                    doc["Session_duration"] = pd.to_datetime(doc["Session_duration"]).dt.strftime('%H:%M:%S')
                    Output = doc.astype(str)
                    Output = Output.iloc[:,[0,1,2,3,4,5,6,14,15,7,16,17,8,18,19,9,10,11,12,13]]
                    convert_dict = {'Date':object,
                                    'Service':object,
                                    'Agent':object,
                                    'Agent_SAP':object,
                                    'Agent_ID':object,
                                    'Worktop':object,
                                    'Begin_session_raw':object,
                                    'Begin_session_date':object,
                                    'Begin_session_hour':object,
                                    'Available_session_raw':object,
                                    'Available_session_date':object,
                                    'Available_session_hour':object,
                                    'End_session_raw':object,
                                    'End_session_date':object,
                                    'End_session_hour':object,
                                    'Session_duration':object,
                                    'n_breaks':object,
                                    'Break_reason':object,
                                    'Break_ID':object,
                                    'Break_duration':object} 
                    Call_db = Output.astype(convert_dict)
                    Call_db = Call_db.astype(str)
                    Call_db.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None], inplace=True)
                    Call_db.to_gbq(destination_table='Evolution.Agents_sessions',project_id='nh-cro-forecast', if_exists='append')
    elif Query_number == 23:
            for i in range(int(inicio_dia),int(fin_dia)+1):
                if i <10: 
                    Day = "0"+str(i)
                    Day_1 = int(Day)-1
                    Day_1 = "0"+str(Day_1)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    time.sleep(0.5)
                    print('Calls_Hotel_Distribution UPLOADING')
                    time.sleep(0.5)
                    with fs.open('trueit_external/Calls_Hotel_Distribution/Calls_Hotel_Distribution_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')      
                    doc.drop('grouplevel', axis=1, inplace=True)
                    column = ['Date',
                            'Service',
                            'Hotel_name',
                            'Language',
                            'IVR_option',
                            'Campaign',
                            'Campaign_ID',
                            'Slot',
                            'Incoming_calls',
                            'Answered',
                            'Non_answered',
                            'Abandoned',
                            'Abandoned_less_10s',
                            'Out_service_hours']
                    doc['Date'] = Year+"-"+Month+"-"+Day_1
                    doc.columns = column
                    doc = doc.astype(str)
                    doc.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)
                    doc.to_gbq(destination_table='Evolution.Calls_Hotel_Distribution',project_id='nh-cro-forecast', if_exists='append')
                
                elif i == 10:
                     Day = str(i)
                     Day_1 = int(Day) -1
                     Day_1 = "0" + str(Day_1)
                     print(f"Subiendo datos del archivo de día:{Day}")
                     time.sleep(0.5)
                     print('Calls_Hotel_Distribution UPLOADING')
                     time.sleep(0.5)
                     with fs.open('trueit_external/Calls_Hotel_Distribution/Calls_Hotel_Distribution_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')      
                     doc.drop('grouplevel', axis=1, inplace=True)
                     column = ['Date',
                            'Service',
                            'Hotel_name',
                            'Language',
                            'IVR_option',
                            'Campaign',
                            'Campaign_ID',
                            'Slot',
                            'Incoming_calls',
                            'Answered',
                            'Non_answered',
                            'Abandoned',
                            'Abandoned_less_10s',
                            'Out_service_hours']
                     doc['Date'] = Year+"-"+Month+"-"+Day_1
                     doc.columns = column
                     doc = doc.astype(str)
                     doc.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)
                     doc.to_gbq(destination_table='Evolution.Calls_Hotel_Distribution',project_id='nh-cro-forecast', if_exists='append')

                else:
                    Day = str(i)
                    Day_1 = int(Day)-1
                    Day_1 = str(Day_1)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('Calls_Hotel_Distribution UPLOADING')
                    with fs.open('trueit_external/Calls_Hotel_Distribution/Calls_Hotel_Distribution_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')      
                    doc.drop('grouplevel', axis=1, inplace=True)
                    column = ['Date',
                            'Service',
                            'Hotel_name',
                            'Language',
                            'IVR_option',
                            'Campaign',
                            'Campaign_ID',
                            'Slot',
                            'Incoming_calls',
                            'Answered',
                            'Non_answered',
                            'Abandoned',
                            'Abandoned_less_10s',
                            'Out_service_hours']
                    doc['Date'] = Year+"-"+Month+"-"+Day_1
                    doc.columns = column
                    doc = doc.astype(str)
                    doc.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)
                    doc.to_gbq(destination_table='Evolution.Calls_Hotel_Distribution',project_id='nh-cro-forecast', if_exists='append')
    elif Query_number == 24:
            for i in range(int(inicio_dia),int(fin_dia)+1):
                if i <10: 
                    Day = "0"+str(i)
                    Day_1 = int(Day)-1
                    Day_1 = "0"+str(Day_1)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    time.sleep(0.5)
                    print('Calls_out_of_time UPLOADING')
                    time.sleep(0.5)
                    with fs.open('trueit_external/Calls_out_of_Time/Call_out_of_time_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')
                    doc = doc.iloc[1:,1:-1]
                    doc['Fecha'] = Year+"-"+Month+"-"+Day_1
                    column = ['Date',
                            'Service',
                            'Campaign',
                            'ID_Campaign',
                            'LANGUAGE',
                            'IVR_OPTION',
                            'Time_Slot',
                            'Total_Calls',
                            'Abandoned_Calls_less_10_secs',
                            'Abandoned_Calls_more_10_secs',
                            'Transfer_Calls',
                            'Calls_to_answering_machine']      
                    doc.columns = column           
                    doc = doc.astype(object)
                    doc = doc.astype(str)          
                    doc.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)           
                    doc.to_gbq(destination_table='Evolution.Calls_out_of_time',project_id='nh-cro-forecast', if_exists='append')
                
                elif i == 10:
                     Day = str(i)
                     Day_1 = int(Day)-1
                     Day_1 = "0" + str(Day_1)
                     print(f"Subiendo datos del archivo de día:{Day}")
                     time.sleep(0.5)
                     print('Calls_out_of_time UPLOADING')
                     time.sleep(0.5)
                     with fs.open('trueit_external/Calls_out_of_Time/Call_out_of_time_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')
                     doc = doc.iloc[1:,1:-1]
                     doc['Fecha'] = Year+"-"+Month+"-"+Day_1
                     column = ['Date',
                            'Service',
                            'Campaign',
                            'ID_Campaign',
                            'LANGUAGE',
                            'IVR_OPTION',
                            'Time_Slot',
                            'Total_Calls',
                            'Abandoned_Calls_less_10_secs',
                            'Abandoned_Calls_more_10_secs',
                            'Transfer_Calls',
                            'Calls_to_answering_machine']      
                     doc.columns = column           
                     doc = doc.astype(object)
                     doc = doc.astype(str)          
                     doc.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)           
                     doc.to_gbq(destination_table='Evolution.Calls_out_of_time',project_id='nh-cro-forecast', if_exists='append')

                else:
                    Day = str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    Day = "0"+str(i)
                    Day_1 = int(Day)-1
                    Day_1 = str(Day_1)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    time.sleep(0.5)
                    print('Calls_out_of_time UPLOADING')
                    time.sleep(0.5)
                    with fs.open('trueit_external/Calls_out_of_Time/Call_out_of_time_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')
                    doc = doc.iloc[1:,1:-1]
                    doc['Fecha'] = Year+"-"+Month+"-"+Day_1
                    column = ['Date',
                            'Service',
                            'Campaign',
                            'ID_Campaign',
                            'LANGUAGE',
                            'IVR_OPTION',
                            'Time_Slot',
                            'Total_Calls',
                            'Abandoned_Calls_less_10_secs',
                            'Abandoned_Calls_more_10_secs',
                            'Transfer_Calls',
                            'Calls_to_answering_machine']      
                    doc.columns = column           
                    doc = doc.astype(object)
                    doc = doc.astype(str)          
                    doc.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)           
                    doc.to_gbq(destination_table='Evolution.Calls_out_of_time',project_id='nh-cro-forecast', if_exists='append')
    elif Query_number == 25:
            for i in range(int(inicio_dia),int(fin_dia)+1):
                if i <10: 
                    Day = "0"+str(i)
                    Day_1 = int(Day)-1
                    Day_1 = "0"+str(Day_1)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('IVR UPLOADING')
                    with fs.open('trueit_external/IVR_Distribution/IVR_Distribution_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')
                    doc = doc.iloc[1:,1:]
                    doc['Date'] = Year+"-"+Month+"-"+Day_1
                    column = ['Date', 
                            'Service',
                            'Campaign',
                            'ID',
                            'LANGUAGE',
                            'Time_Zone',
                            'IVR_OPTION',
                            'Incoming_Calls',
                            'Abandoned',
                            'Abandoned_Before_Queue',
                            'Transfered_Calls']      
                    doc.columns = column         
                    doc = doc.astype(object)
                    doc = doc.astype(str)           
                    doc.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)
                    doc.to_gbq(destination_table='Evolution.IVR',project_id='nh-cro-forecast', if_exists='append')
                elif i == 10:
                     Day = str(i)
                     Day_1 = int(Day)-1
                     Day_1 = "0" + str(Day_1)
                     print(f"Subiendo datos del archivo de día:{Day}")
                     time.sleep(0.5)
                     print('IVR UPLOADING')
                     time.sleep(0.5)
                     with fs.open('trueit_external/IVR_Distribution/IVR_Distribution_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')
                     doc = doc.iloc[1:,1:]
                     doc['Date'] = Year+"-"+Month+"-"+Day_1
                     column = ['Date', 
                            'Service',
                            'Campaign',
                            'ID',
                            'LANGUAGE',
                            'Time_Zone',
                            'IVR_OPTION',
                            'Incoming_Calls',
                            'Abandoned',
                            'Abandoned_Before_Queue',
                            'Transfered_Calls']      
                     doc.columns = column         
                     doc = doc.astype(object)
                     doc = doc.astype(str)           
                     doc.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)
                     doc.to_gbq(destination_table='Evolution.IVR',project_id='nh-cro-forecast', if_exists='append')


                else:
                    Day = str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    Day_1 = int(Day)-1
                    Day_1 = str(Day_1)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('IVR UPLOADING')
                    with fs.open('trueit_external/IVR_Distribution/IVR_Distribution_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')
                    doc = doc.iloc[1:,1:]
                    doc['Date'] = Year+"-"+Month+"-"+Day_1
                    column = ['Date', 
                            'Service',
                            'Campaign',
                            'ID',
                            'LANGUAGE',
                            'Time_Zone',
                            'IVR_OPTION',
                            'Incoming_Calls',
                            'Abandoned',
                            'Abandoned_Before_Queue',
                            'Transfered_Calls']      
                    doc.columns = column         
                    doc = doc.astype(object)
                    doc = doc.astype(str)           
                    doc.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)
                    doc.to_gbq(destination_table='Evolution.IVR',project_id='nh-cro-forecast', if_exists='append')
    elif Query_number == 26:
            for i in range(int(inicio_dia),int(fin_dia)+1):
                if i <10: 
                    Day = "0"+str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('Rejected_calls UPLOADING')
                    with fs.open('trueit_external/Calls_Rejected/Reporte_Llamadas_rechazadas_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')
                    doc = doc.iloc[:,1:]
                    doc = doc.astype(str)
                    doc.columns=['Fecha',
                                'Service',
                                'Agent',
                                'Agent_ID',
                                'Campaign',
                                'Campaign_ID',
                                'Language',
                                'IVR_option',
                                'Transaction_ID',
                                'Contact_ID',
                                'Type',
                                'Time',
                                'Next_pause',
                                'Time_until_pause']
                    doc["Fecha"] = pd.to_datetime(doc["Fecha"], format=('%d/%m/%Y')).dt.strftime('%Y-%m-%d')
                    doc["Time"] = pd.to_datetime(doc["Time"]).dt.strftime('%H:%M:%S')
                    doc["Next_pause_date"] = pd.to_datetime(doc["Next_pause"]).dt.strftime('%Y-%m-%d')
                    doc["Next_pause_hour"] = pd.to_datetime(doc["Next_pause"]).dt.strftime('%H:%M:%S')
                    doc["Time_until_pause"] = pd.to_datetime(doc["Time_until_pause"]).dt.strftime('%H:%M:%S')
                    doc = doc[['Fecha', 
                            'Service',
                            'Agent',
                            'Agent_ID',
                            'Campaign',
                            'Campaign_ID',
                            'Language',
                            'IVR_option',
                            'Transaction_ID',
                            'Contact_ID',
                            'Type',
                            'Time',
                            'Next_pause_date',
                            'Next_pause_hour',
                            'Time_until_pause']]

                    doc.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None], inplace=True)
                    doc.to_gbq(destination_table='Evolution.Rejected_calls',project_id='nh-cro-forecast', if_exists='append')
                else:
                    Day = str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('Rejected_calls UPLOADING')
                    with fs.open('trueit_external/Calls_Rejected/Reporte_Llamadas_rechazadas_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')
                    doc = doc.iloc[:,1:]
                    doc = doc.astype(str)
                    doc.columns=['Fecha',
                                'Service',
                                'Agent',
                                'Agent_ID',
                                'Campaign',
                                'Campaign_ID',
                                'Language',
                                'IVR_option',
                                'Transaction_ID',
                                'Contact_ID',
                                'Type',
                                'Time',
                                'Next_pause',
                                'Time_until_pause']
                    doc["Fecha"] = pd.to_datetime(doc["Fecha"], format=('%d/%m/%Y')).dt.strftime('%Y-%m-%d')
                    doc["Time"] = pd.to_datetime(doc["Time"]).dt.strftime('%H:%M:%S')
                    doc["Next_pause_date"] = pd.to_datetime(doc["Next_pause"]).dt.strftime('%Y-%m-%d')
                    doc["Next_pause_hour"] = pd.to_datetime(doc["Next_pause"]).dt.strftime('%H:%M:%S')
                    doc["Time_until_pause"] = pd.to_datetime(doc["Time_until_pause"]).dt.strftime('%H:%M:%S')
                    doc = doc[['Fecha', 
                            'Service',
                            'Agent',
                            'Agent_ID',
                            'Campaign',
                            'Campaign_ID',
                            'Language',
                            'IVR_option',
                            'Transaction_ID',
                            'Contact_ID',
                            'Type',
                            'Time',
                            'Next_pause_date',
                            'Next_pause_hour',
                            'Time_until_pause']]

                    doc.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None], inplace=True)
                    doc.to_gbq(destination_table='Evolution.Rejected_calls',project_id='nh-cro-forecast', if_exists='append')
    elif Query_number == 27:
            for i in range(int(inicio_dia),int(fin_dia)+1):
                if i <10: 
                    Day = "0"+str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('Calls_per_queue_time_slot UPLOADING')
                    with fs.open('trueit_external/Calls_By_Agent_Campaign_Slot/CDRAgente_Campanya_Tramos_Tarde_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')
                    doc = doc.iloc[1:,1:]
                    doc = doc.astype(str)
                    doc.columns=['Service', 
                                'Date',
                                'Agent',
                                'Agent_ID',
                                'Campaign',
                                'Campaign_ID',
                                'Language',
                                'IVR_option',
                                'Time_zone',
                                'Calls_in',
                                'Calls_out',
                                'Call_time_in',
                                'Call_time_out',
                                'Call_total_time']
                    doc["Date"] = pd.to_datetime(doc["Date"],format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    doc["Call_time_in"] = pd.to_datetime(doc["Call_time_in"]).dt.strftime('%H:%M:%S')
                    doc["Call_time_out"] = pd.to_datetime(doc["Call_time_out"]).dt.strftime('%H:%M:%S')
                    doc["Call_total_time"] = pd.to_datetime(doc["Call_total_time"]).dt.strftime('%H:%M:%S')
                    doc = doc[['Service', 
                            'Date',
                            'Agent',
                            'Agent_ID',
                            'Campaign',
                            'Campaign_ID',
                            'Language',
                            'IVR_option',
                            'Time_zone',
                            'Calls_in',
                            'Calls_out',
                            'Call_time_in',
                            'Call_time_out',
                            'Call_total_time']]

                    doc.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None], inplace=True)
                    doc.to_gbq(destination_table='Evolution.Calls_per_queue_time_slot',project_id='nh-cro-forecast', if_exists='append')
                else:
                    Day = str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('Calls_per_queue_time_slot UPLOADING')
                    with fs.open('trueit_external/Calls_By_Agent_Campaign_Slot/CDRAgente_Campanya_Tramos_Tarde_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')
                    doc = doc.iloc[1:,1:]
                    doc = doc.astype(str)
                    doc.columns=['Service', 
                                'Date',
                                'Agent',
                                'Agent_ID',
                                'Campaign',
                                'Campaign_ID',
                                'Language',
                                'IVR_option',
                                'Time_zone',
                                'Calls_in',
                                'Calls_out',
                                'Call_time_in',
                                'Call_time_out',
                                'Call_total_time']
                    doc["Date"] = pd.to_datetime(doc["Date"],format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    doc["Call_time_in"] = pd.to_datetime(doc["Call_time_in"]).dt.strftime('%H:%M:%S')
                    doc["Call_time_out"] = pd.to_datetime(doc["Call_time_out"]).dt.strftime('%H:%M:%S')
                    doc["Call_total_time"] = pd.to_datetime(doc["Call_total_time"]).dt.strftime('%H:%M:%S')
                    doc = doc[['Service', 
                            'Date',
                            'Agent',
                            'Agent_ID',
                            'Campaign',
                            'Campaign_ID',
                            'Language',
                            'IVR_option',
                            'Time_zone',
                            'Calls_in',
                            'Calls_out',
                            'Call_time_in',
                            'Call_time_out',
                            'Call_total_time']]

                    doc.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None], inplace=True)
                    doc.to_gbq(destination_table='Evolution.Calls_per_queue_time_slot',project_id='nh-cro-forecast', if_exists='append')
    elif Query_number == 28:
            for i in range(int(inicio_dia),int(fin_dia)+1):
                if i <10: 
                    Day = "0"+str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('Calls_per_queue_time_slot UPLOADING')
                    with fs.open('trueit_external/Calls_By_Agent_Campaign_Slot/CDRAgente_Campanya_Tramos_Maniana_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')
                    doc = doc.iloc[1:,1:]
                    doc = doc.astype(str)
                    doc.columns=['Service', 
                                'Date',
                                'Agent',
                                'Agent_ID',
                                'Campaign',
                                'Campaign_ID',
                                'Language',
                                'IVR_option',
                                'Time_zone',
                                'Calls_in',
                                'Calls_out',
                                'Call_time_in',
                                'Call_time_out',
                                'Call_total_time']
                    doc["Date"] = pd.to_datetime(doc["Date"],format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    doc["Call_time_in"] = pd.to_datetime(doc["Call_time_in"]).dt.strftime('%H:%M:%S')
                    doc["Call_time_out"] = pd.to_datetime(doc["Call_time_out"]).dt.strftime('%H:%M:%S')
                    doc["Call_total_time"] = pd.to_datetime(doc["Call_total_time"]).dt.strftime('%H:%M:%S')
                    doc = doc[['Service', 
                            'Date',
                            'Agent',
                            'Agent_ID',
                            'Campaign',
                            'Campaign_ID',
                            'Language',
                            'IVR_option',
                            'Time_zone',
                            'Calls_in',
                            'Calls_out',
                            'Call_time_in',
                            'Call_time_out',
                            'Call_total_time']]

                    doc.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None], inplace=True)
                    doc.to_gbq(destination_table='Evolution.Calls_per_queue_time_slot',project_id='nh-cro-forecast', if_exists='append')
                else:
                    Day = str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('Calls_per_queue_time_slot UPLOADING')
                    with fs.open('trueit_external/Calls_By_Agent_Campaign_Slot/CDRAgente_Campanya_Tramos_Maniana_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')
                    doc = doc.iloc[1:,1:]
                    doc = doc.astype(str)
                    doc.columns=['Service', 
                                'Date',
                                'Agent',
                                'Agent_ID',
                                'Campaign',
                                'Campaign_ID',
                                'Language',
                                'IVR_option',
                                'Time_zone',
                                'Calls_in',
                                'Calls_out',
                                'Call_time_in',
                                'Call_time_out',
                                'Call_total_time']
                    doc["Date"] = pd.to_datetime(doc["Date"],format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    doc["Call_time_in"] = pd.to_datetime(doc["Call_time_in"]).dt.strftime('%H:%M:%S')
                    doc["Call_time_out"] = pd.to_datetime(doc["Call_time_out"]).dt.strftime('%H:%M:%S')
                    doc["Call_total_time"] = pd.to_datetime(doc["Call_total_time"]).dt.strftime('%H:%M:%S')
                    doc = doc[['Service', 
                            'Date',
                            'Agent',
                            'Agent_ID',
                            'Campaign',
                            'Campaign_ID',
                            'Language',
                            'IVR_option',
                            'Time_zone',
                            'Calls_in',
                            'Calls_out',
                            'Call_time_in',
                            'Call_time_out',
                            'Call_total_time']]

                    doc.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None], inplace=True)
                    doc.to_gbq(destination_table='Evolution.Calls_per_queue_time_slot',project_id='nh-cro-forecast', if_exists='append')
    elif Query_number == 29:
            for i in range(int(inicio_dia),int(fin_dia)+1):
                if i <10: 
                    Day = "0"+str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('Codifications UPLOADING')
                    with fs.open('trueit_external/Calls_Codifications/Call_Codification_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')           
                    doc.drop('grouplevel', axis=1, inplace=True)
                    doc.columns = ['Date',
                                'Service',
                                'Transaction_ID',
                                'Agent',
                                'Agent_ID',
                                'Campaign',
                                'Campaign_number',
                                'Language',
                                'IVR_option',
                                'Inbound_outbound',
                                'State',
                                'Client_type',
                                'Hotel_name',
                                'Reason_of_the_call',
                                'Reason_closure',
                                'Closure',
                                'Number_handled',
                                'Codification_time',
                                'Time_call_onhold',
                                'Time_call_active',
                                'Type_closure']  
                    doc["Date"] = pd.to_datetime(doc["Date"], format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    doc = doc.astype(str)
                    doc = doc[['Date',
                            'Service',
                            'Agent',
                            'Agent_ID',
                            'Transaction_ID',
                            'Campaign',
                            'Campaign_number',
                            'Language',
                            'IVR_option',
                            'Inbound_outbound',
                            'State',
                            'Client_type',
                            'Hotel_name',
                            'Reason_of_the_call',
                            'Reason_closure',
                            'Closure',
                            'Number_handled',
                            'Codification_time']]     
                    Call_db = doc.astype(object)  
                    Call_db['Number_handled'] = Call_db['Number_handled'].astype(int)
                    Call_db.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None], inplace=True)
                    Call_db.to_gbq(destination_table='Evolution.Codifications',project_id='nh-cro-forecast', if_exists='append')
                else:
                    Day = str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('Codifications UPLOADING')
                    with fs.open('trueit_external/Calls_Codifications/Call_Codification_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')           
                    doc.drop('grouplevel', axis=1, inplace=True)
                    doc.columns = ['Date',
                                'Service',
                                'Transaction_ID',
                                'Agent',
                                'Agent_ID',
                                'Campaign',
                                'Campaign_number',
                                'Language',
                                'IVR_option',
                                'Inbound_outbound',
                                'State',
                                'Client_type',
                                'Hotel_name',
                                'Reason_of_the_call',
                                'Reason_closure',
                                'Closure',
                                'Number_handled',
                                'Codification_time',
                                'Time_call_onhold',
                                'Time_call_active',
                                'Type_closure']  
                    doc["Date"] = pd.to_datetime(doc["Date"], format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    doc = doc.astype(str)
                    doc = doc[['Date',
                            'Service',
                            'Agent',
                            'Agent_ID',
                            'Transaction_ID',
                            'Campaign',
                            'Campaign_number',
                            'Language',
                            'IVR_option',
                            'Inbound_outbound',
                            'State',
                            'Client_type',
                            'Hotel_name',
                            'Reason_of_the_call',
                            'Reason_closure',
                            'Closure',
                            'Number_handled',
                            'Codification_time']]     
                    Call_db = doc.astype(object)  
                    Call_db['Number_handled'] = Call_db['Number_handled'].astype(int)
                    Call_db.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None], inplace=True)
                    Call_db.to_gbq(destination_table='Evolution.Codifications',project_id='nh-cro-forecast', if_exists='append')
    elif Query_number == 30:
            for i in range(int(inicio_dia),int(fin_dia)+1):
                if i <10: 
                    Day = "0"+str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('Agent_Nomenclature UPLOADING')
                    with fs.open('trueit_external/User_Nomenclatures/Nomenclaturas_Usuarios_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')
                    doc = doc.iloc[1:,0:]
                    doc.columns = ['Date','Service', 'Agent', 'Agent_ID']
                    doc["Date"] = pd.to_datetime(doc["Date"], format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    doc = doc.astype(str)
                    doc.to_gbq(destination_table='Evolution.Agent_Nomenclature',project_id='nh-cro-forecast', if_exists='append')
                else:
                    Day = str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('Agent_Nomenclature UPLOADING')
                    with fs.open('trueit_external/User_Nomenclatures/Nomenclaturas_Usuarios_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')
                    doc = doc.iloc[1:,0:]
                    doc.columns = ['Date','Service', 'Agent', 'Agent_ID']
                    doc["Date"] = pd.to_datetime(doc["Date"], format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    doc = doc.astype(str)
                    doc.to_gbq(destination_table='Evolution.Agent_Nomenclature',project_id='nh-cro-forecast', if_exists='append')
    elif Query_number == 31:
            for i in range(int(inicio_dia),int(fin_dia)+1):
                if i <10: 
                    Day = "0"+str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('e_17_Facturacion_logins UPLOADING')
                    with fs.open('trueit_external/Facturacion_current_logins/Concurrent_logins_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')
                    doc.columns=['grouplevel',
                                'Date',
                                'Service',
                                'Total_logins',
                                'Number_concurrente',
                                'Max_concurrente']

                    doc["Date"] = pd.to_datetime(doc["Date"], format = '%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    Output = doc.astype(str)
                    Output.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)
                    Output.to_gbq(destination_table='Evolution.e_17_Facturacion_logins',project_id='nh-cro-forecast', if_exists='append')
                else:
                    Day = str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('e_17_Facturacion_logins UPLOADING')
                    with fs.open('trueit_external/Facturacion_current_logins/Concurrent_logins_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')
                    doc.columns=['grouplevel',
                                'Date',
                                'Service',
                                'Total_logins',
                                'Number_concurrente',
                                'Max_concurrente']

                    doc["Date"] = pd.to_datetime(doc["Date"], format = '%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    Output = doc.astype(str)
                    Output.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)
                    Output.to_gbq(destination_table='Evolution.e_17_Facturacion_logins',project_id='nh-cro-forecast', if_exists='append')
    elif Query_number == 32:
            for i in range(int(inicio_dia),int(fin_dia)+1):
                if i <10: 
                    Day = "0"+str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('SLA_completed_Hotel_pdf UPLOADING')
                    with fs.open('trueit_external/SLA_Completed_Hotel/SLA_Completed_Hotel_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')
                    doc = doc.iloc[:,1:]
                    doc.columns=['Service',
                                'Entry_date',
                                'Entry_hour',
                                'Activity_ID',
                                'Case_ID',
                                'Alias',
                                'Agent_distributed',
                                'Distributed_date',
                                'Distributed_hour',
                                'Queue',
                                'Completed',
                                'Agent_completed',
                                'Completed_date',
                                'Completed_hour',
                                'Type',
                                'Subtype',
                                'due_on',
                                'From_mail',
                                'IN_OUT',
                                'Total_time',
                                'Match',
                                'Match_level',
                                'Hotel',
                                'Country',
                                'City',
                                'Hotel_ID']
                    raw = doc.astype(str)
                    raw = raw.loc[:,['Service',
                            'Entry_date',
                            'Entry_hour',
                            'Activity_ID',
                            'Case_ID',
                            'Alias',
                            'Agent_distributed',
                            'Distributed_date',
                            'Distributed_hour',
                            'Queue',
                            'Completed',
                            'Agent_completed',
                            'Completed_date',
                            'Completed_hour',
                            'Type',
                            'Subtype',
                            'due_on',
                            'From_mail',
                            'IN_OUT',
                            'Total_time',
                            'Match',
                            'Match_level',
                            'Country',
                            'City',
                            'Hotel',
                            'Hotel_ID']]
                    raw = doc.astype(str)
                    raw.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)
                    raw["Entry_date"] = pd.to_datetime(raw["Entry_date"], format = '%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    raw["Completed_date"] = pd.to_datetime(raw["Completed_date"], format = '%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    raw["Distributed_date"] = pd.to_datetime(raw["Distributed_date"], format = '%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    raw.to_gbq(destination_table='Evolution.SLA_completed_Hotel_pdf',project_id='nh-cro-forecast', if_exists='append')
                else:
                    Day = str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('SLA_completed_Hotel_pdf UPLOADING')
                    with fs.open('trueit_external/SLA_Completed_Hotel/SLA_Completed_Hotel_'+Year+Month+Day+'.csv') as f:
                        doc = pd.read_csv(f,delimiter = ';', encoding='latin-1')
                    doc = doc.iloc[:,1:]
                    doc.columns=['Service',
                                'Entry_date',
                                'Entry_hour',
                                'Activity_ID',
                                'Case_ID',
                                'Alias',
                                'Agent_distributed',
                                'Distributed_date',
                                'Distributed_hour',
                                'Queue',
                                'Completed',
                                'Agent_completed',
                                'Completed_date',
                                'Completed_hour',
                                'Type',
                                'Subtype',
                                'due_on',
                                'From_mail',
                                'IN_OUT',
                                'Total_time',
                                'Match',
                                'Match_level',
                                'Hotel',
                                'Country',
                                'City',
                                'Hotel_ID']
                    raw = doc.astype(str)
                    raw = raw.loc[:,['Service',
                            'Entry_date',
                            'Entry_hour',
                            'Activity_ID',
                            'Case_ID',
                            'Alias',
                            'Agent_distributed',
                            'Distributed_date',
                            'Distributed_hour',
                            'Queue',
                            'Completed',
                            'Agent_completed',
                            'Completed_date',
                            'Completed_hour',
                            'Type',
                            'Subtype',
                            'due_on',
                            'From_mail',
                            'IN_OUT',
                            'Total_time',
                            'Match',
                            'Match_level',
                            'Country',
                            'City',
                            'Hotel',
                            'Hotel_ID']]
                    raw = doc.astype(str)
                    raw.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)
                    raw["Entry_date"] = pd.to_datetime(raw["Entry_date"], format = '%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    raw["Completed_date"] = pd.to_datetime(raw["Completed_date"], format = '%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    raw["Distributed_date"] = pd.to_datetime(raw["Distributed_date"], format = '%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    raw.to_gbq(destination_table='Evolution.SLA_completed_Hotel_pdf',project_id='nh-cro-forecast', if_exists='append')
    elif Query_number == 33:
            for i in range(int(inicio_dia),int(fin_dia)+1):
                if i <10: 
                    Day = "0"+str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('e_301_GEM_Audits UPLOADING')
                    with fs.open('trueit_external/Auditorias/Audit_GEM_'+Year+Month+Day+'.csv') as f:
                        df_audits= pd.read_csv(f,delimiter=";", encoding='latin-1', on_bad_lines='skip', dtype='str')

                    df_audits.drop('GroupLevel', inplace=True, axis=1)
                    df_audits['Event_Date'] = pd.to_datetime(df_audits["Event_Date"], format = '%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    df_audits['Audit_Date'] = pd.to_datetime(df_audits["Audit_Date"], format = '%d/%m/%Y').dt.strftime('%Y-%m-%d')

                    df_audits.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)

                    df_audits.to_gbq(destination_table='Evolution.e_301_GEM_Audits',project_id='nh-cro-forecast', if_exists='append')
                else:
                    Day = str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('e_301_GEM_Audits UPLOADING')
                    with fs.open('trueit_external/Auditorias/Audit_GEM_'+Year+Month+Day+'.csv') as f:
                        df_audits= pd.read_csv(f,delimiter=";", encoding='latin-1', on_bad_lines='skip', dtype='str')

                    df_audits.drop('GroupLevel', inplace=True, axis=1)
                    df_audits['Event_Date'] = pd.to_datetime(df_audits["Event_Date"], format = '%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    df_audits['Audit_Date'] = pd.to_datetime(df_audits["Audit_Date"], format = '%d/%m/%Y').dt.strftime('%Y-%m-%d')

                    df_audits.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)

                    df_audits.to_gbq(destination_table='Evolution.e_301_GEM_Audits',project_id='nh-cro-forecast', if_exists='append')
    elif Query_number ==34:
            for i in range(int(inicio_dia),int(fin_dia)+1):
                if i <10: 
                    Day = "0"+str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('QA_Lista_Admin UPLOADING')
                    with fs.open('trueit_external/Auditorias/Reporte_QA_Lista_Admin_'+Year+Month+Day+'.csv') as f:
                        df_audits_coord= pd.read_csv(f,delimiter=";", encoding='latin-1', on_bad_lines='skip', dtype='str')

                    df_audits_coord.drop('GroupLevel',axis=1,inplace=True)
                    df_audits_coord['Fecha'] = pd.to_datetime(df_audits_coord["Fecha"], format = '%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    df_audits_coord.to_gbq(destination_table='Evolution.QA_Lista_Admin',project_id='nh-cro-forecast', if_exists='append')
                else:
                    Day = str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('QA_Lista_Admin UPLOADING')
                    with fs.open('trueit_external/Auditorias/Reporte_QA_Lista_Admin_'+Year+Month+Day+'.csv') as f:
                        df_audits_coord= pd.read_csv(f,delimiter=";", encoding='latin-1', on_bad_lines='skip', dtype='str')

                    df_audits_coord.drop('GroupLevel',axis=1,inplace=True)
                    df_audits_coord['Fecha'] = pd.to_datetime(df_audits_coord["Fecha"], format = '%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    df_audits_coord.to_gbq(destination_table='Evolution.QA_Lista_Admin',project_id='nh-cro-forecast', if_exists='append')
    elif Query_number == 35:
         for i in range(int(inicio_dia),int(fin_dia)+1):
                if i < 10:
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('e_309_GEM_Audits_with_Deleted UPLOADING')
                    with fs.open('trueit_external/Auditorias/Audit_GEM_with_deleted_'+Year+Month+Day+'.csv') as f:
                        df_audits= pd.read_csv(f,delimiter=";", encoding='latin-1', on_bad_lines='skip', dtype='str')
                    
                    df_audits.drop('GroupLevel', inplace=True, axis=1)
                    df_audits['Event_Date'] = pd.to_datetime(df_audits["Event_Date"], format = '%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    df_audits['Audit_Date'] = pd.to_datetime(df_audits["Audit_Date"], format = '%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    df_audits['Load_Date'] = pd.to_datetime(df_audits['Load_Date'], format = '%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    df_audits.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)
                    df_audits.to_gbq(destination_table='Evolution.e_309_GEM_Audits_with_Deleted',project_id='nh-cro-forecast', if_exists='append')
                    print("e_309_GEM_Audits_with_Deleted succesfully uploaded")

                else:
                    Day = str(i)
                    print(f"Subiendo datos del archivo de día:{Day}")
                    print('e_309_GEM_Audits_with_Deleted UPLOADING')
                    with fs.open('trueit_external/Auditorias/Audit_GEM_with_deleted_'+Year+Month+Day+'.csv') as f:
                        df_audits= pd.read_csv(f,delimiter=";", encoding='latin-1', on_bad_lines='skip', dtype='str')
                    
                    df_audits.drop('GroupLevel', inplace=True, axis=1)
                    df_audits['Event_Date'] = pd.to_datetime(df_audits["Event_Date"], format = '%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    df_audits['Audit_Date'] = pd.to_datetime(df_audits["Audit_Date"], format = '%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    # df_audits['Load_Date'] = pd.to_datetime(df_audits['Load_Date'], format = '%d/%m/%Y').dt.strftime('%Y-%m-%d')
                    df_audits['Load_Date'] = Year+"-"+Month+"-"+Day
                    df_audits.replace(['NaN','None','NaT',' ','nan'],[None,None,None,None,None],inplace=True)
                    df_audits.to_gbq(destination_table='Evolution.e_309_GEM_Audits_with_Deleted',project_id='nh-cro-forecast', if_exists='append')
                    print("e_309_GEM_Audits_with_Deleted succesfully uploaded")
    else:
         print('Bucket incorrecto')


### ----- 10. upload_TMS_Data_CRO ----- ###

def upload_TMS_Data_CRO(day=1,Server_Letter='V'):
    """
    Function to upload data from BO to have CRO KPI's.

        Args:
            - day: By default(int) = 1. day defines the day you want to upload in delta By default it is 1, what it means you will upload last day data.
            - Server_Letter: By default(str) = 'V'. If you have groups CRO Madrid server ubicated in ohter server Letter, please change it.
    """
    ## DEFINIMOS FECHAS DE CARGA ##
    today =         date.today()
    load_date =     today - timedelta(days = day)
    date_loaded =   load_date.strftime("%d/%m/%Y")
    load_day =      int(load_date.strftime("%d"))
    load_month =    load_date.strftime("%m")
    load_year =     load_date.strftime("%Y")

    print('load day',load_day)

    ## DEFINIMOS LISTA CON MESES PARA IR A LA UBICACION EXACTA Y CARGAMOS EL DIRECTORIO DE FILES ##
    meses = ['01. ENERO', '02. FEBRERO','03. MARZO','04. ABRIL','05. MAYO','06. JUNIO','07. JULIO','08. AGOSTO','09. SEPTIEMBRE','10. OCTUBRE','11. NOVIEMBRE','12. DICIEMBRE']
    files = os.listdir(fr"{Server_Letter}:\Central reservations office\Area-3\SOPORTE OPERACIONES\\01. INFORMES DIARIOS\\{load_year}\\{meses[int(load_month)-1]} {load_year}\\{load_day}")

    ## PROCEDEMOS A LA CARGA DE ARCHIVOS A CLOUD CON UN BUCLE QUE RECORRE LOS ARCHIVOS DEL DIRECTORIO PARA ENCONTRAR LOS 2 A SUBIR ##
    for file in files: 

        # BUSCAMOS EL ARCHIVO CRO_VS_HOTEL EN CLOUD PARA SABER SI TIENE DATOS Y NO DUPLICAR. SI SE HA SUBIDO, PASAMOS AL SIGUIENTE. SI NO SE HA SUBIDO, PROCEDEMOS A SUBIRLO ##
        if file[:6]=='CRO_Le':
            CHECK_CRO_VS_HOTEL = pandas_gbq.read_gbq("""SELECT Creation_date_origin FROM `nh-cro-forecast.TMS.c_Reservation_Share_Hotel_vs_CRO` ORDER BY Creation_date_origin DESC LIMIT 1""",project_id="nh-cro-forecast")

            if int(pd.to_datetime(CHECK_CRO_VS_HOTEL.values[0][0]).strftime("%d"))==int(load_day):
                print('CRO_VS_HOTEL DUPLICADO')
            else:
                file1 = fr"{Server_Letter}:\Central reservations office\Area-3\SOPORTE OPERACIONES\\01. INFORMES DIARIOS\\{load_year}\\{meses[int(load_month)-1]} {load_year}\\{load_day}\\{file}"
                CRO_vs_Hotel = pd.read_excel(file1).astype(str).replace(['NaN','None','NaT',' ','nan',nan],[None,None,None,None,None,None])
                CRO_vs_Hotel.columns = ['Hotel_ID','Hotel_name','Hotel_business_unit','Hotel_country','Hotel_city','Creation_year_month','Department','RO_channel','RO_subchannel_ID','Reservation_origin_ID','Total_revenue','Total_room_revenue',
                                        'Total_fb_revenue','Total_meeting_room_revenue','Total_other_revenue','Room_nights','Creation_date_origin','OK_LT']
                CRO_vs_Hotel["Creation_date_origin"] = pd.to_datetime(CRO_vs_Hotel["Creation_date_origin"]).dt.strftime('%Y-%m-%d')
                CRO_vs_Hotel["Rooms"] = '1'
                CRO_vs_Hotel['Reservation_origin_ID'] = CRO_vs_Hotel['Reservation_origin_ID'].astype(float).astype(int).astype(str)
                print('CRO_VS_HOTEL SUBIDO')
                CRO_vs_Hotel.to_gbq(destination_table='TMS.c_Reservation_Share_Hotel_vs_CRO',project_id='nh-cro-forecast',if_exists='append')

        # BUSCAMOS EL ARCHIVO TMS EN CLOUD PARA SABER SI TIENE DATOS Y NO DUPLICAR. SI SE HA SUBIDO, PASAMOS AL SIGUIENTE. SI NO SE HA SUBIDO, PROCEDEMOS A SUBIRLO ##
        else:
            if file[:6]=='CRO_TM':
                CHECK_TMS = pandas_gbq.read_gbq("""select RS_FECHA_RESERVA from `nh-cro-forecast.TMS.a_Reservation_entry_data_2022_raw` ORDER BY RS_FECHA_RESERVA DESC LIMIT 1""",project_id="nh-cro-forecast")

                if int(pd.to_datetime(CHECK_TMS.values[0][0]).strftime("%d"))==int(load_day):
                    print('TMS DUPLICADO')
                else:
                    file2 = fr"{Server_Letter}:\Central reservations office\Area-3\SOPORTE OPERACIONES\\01. INFORMES DIARIOS\\{load_year}\\{meses[int(load_month)-1]} {load_year}\\{load_day}\\{file}"
                    TMS = pd.read_excel(file2,dtype=str).replace(['NaN','None','NaT',' ','nan',nan],[None,None,None,None,None,None]).rename(columns={'Hotel Currency':'Hotel_Currency',
                                                                                                                                                'Status Reservation Origin ID':'Status_Reservation_Origin_ID',
                                                                                                                                                'RO Room type generic (upgrade)':'RO_Room_type_generic_upgrade',
                                                                                                                                                'RO Commercial Subchannel':'RO_Commercial_Subchannel',
                                                                                                                                                'RO Reservation Done By':'RO_Reservation_Done_by',
                                                                                                                                                'RO Contact person':'RO_Contact_person',
                                                                                                                                                'Room Nights':'Room_Nights',
                                                                                                                                                'Room Nights CXL':'Room_Nights_Cancellation',
                                                                                                                                                'Room Nights No Show':'Room_Nights_No_Show',
                                                                                                                                                'Room Nights OK':'Room_Nights_Ok',
                                                                                                                                                'Total Book Revenue FIN EUR':'Total_Book_Revenue_FIN_EUR',
                                                                                                                                                ## NUEVO ##
                                                                                                                                                'Total Room Revenue FIN EUR (new)':'Book_Room_Revenue_EUR',
                                                                                                                                                ###########
                                                                                                                                                # 'Book Room Revenue EUR':'Book_Room_Revenue_EUR',
                                                                                                                                                ## NUEVO ##
                                                                                                                                                'Total FB Revenue FIN EUR (new)':'Book_Breakfast_Revenue_EUR', 
                                                                                                                                                ############
                                                                                                                                                # 'Book Breakfast Revenue EUR':'Book_Breakfast_Revenue_EUR',
                                                                                                                                                'Cancelled Book Revenue EUR':'Cancelled_Book_Revenue_EUR',
                                                                                                                                                'No Show Book Revenue EUR':'No_Show_Book_Revenue_EUR',
                                                                                                                                                ## NUEVO ##
                                                                                                                                                'Other Revenue FIN EUR (new)':'Total_Other_Revenue_FIN_EUR_new',
                                                                                                                                                ############
                                                                                                                                                # 'Total Other Revenue FIN EUR (new)':'Total_Other_Revenue_FIN_EUR_new',
                                                                                                                                                'Total Book Revenue FIN LC':'Total_Book_Revenue_FIN_LC',
                                                                                                                                                ## NUEVO ##
                                                                                                                                                'Total Room Revenue FIN LC (new)':'Book_Room_Revenue_LC',
                                                                                                                                                ###########
                                                                                                                                                # 'Book Room Revenue LC':'Book_Room_Revenue_LC',
                                                                                                                                                ## NUEVO ##
                                                                                                                                                'Total FB Revenue FIN LC (new)':'Book_Breakfast_Revenue_LC',
                                                                                                                                                ############
                                                                                                                                                # 'Book Breakfast Revenue LC':'Book_Breakfast_Revenue_LC',
                                                                                                                                                'Cancelled Book Revenue LC':'Cancelled_Book_Revenue_LC',
                                                                                                                                                'No Show Book Revenue LC':'No_Show_Book_Revenue_LC',
                                                                                                                                                ## NUEVO ##
                                                                                                                                                'Other Revenue FIN LC (new)':'Total_Other_Revenue_FIN_LC_new',
                                                                                                                                                #############
                                                                                                                                                # 'Total Other Revenue FIN LC (new)':'Total_Other_Revenue_FIN_LC_new',
                                                                                                                                                'RO Reservation type':'RO_Reservation_type',
                                                                                                                                                'RO Branch Company Responsible TMS':'RO_Branch_Company_Responsible_TMS',
                                                                                                                                                'RO Guarantee Category':'RO_Guarantee_Category',
                                                                                                                                                'Creation Time Origin':'Creation_Time_Origin',
                                                                                                                                                'Creation Date Origin CET':'Creation_Date_Origin_CET',
                                                                                                                                                'Creation Time Origin CET':'Creation_Time_Origin_CET'})
                    TMS['RS_RESERVA'] = TMS['RS_RESERVA'].astype(float).astype(int)
                    TMS = TMS.astype(str)
                    TMS.replace(['NaN','None','NaT',' ','nan',nan],[None,None,None,None,None,None], inplace=True)
                    #Borramos las columnas antiguas
                    old_columns =['Book Room Revenue EUR', 'Book Breakfast Revenue EUR','Total Other Revenue FIN EUR (new)',
                                'Book Room Revenue LC', 'Book Breakfast Revenue LC','Total Other Revenue FIN LC (new)']
                    TMS = TMS.drop(columns=old_columns)
                    # Ordenamos las columnas tras haber añadido las nuevas
                    orden_columnas = [
                        'RS_HOTEL',
                        'Hotel_Currency',
                        'RS_RESERVA',
                        'Status_Reservation_Origin_ID',
                        'RS_FECHA_RESERVA',
                        'RS_LLEGADA',
                        'RS_SALIDA',
                        'RS_TIPO_HAB',
                        'RO_Room_type_generic_upgrade',
                        'Flag_Room_Upgrade',
                        'RS_REGIMEN',
                        'RS_TARIFA',
                        'RS_MARKET_SEGMENT',
                        'RS_MARKET_SUBSEGMENT',
                        'RS_CANAL',
                        'RS_SUBCANAL',
                        'RO_Commercial_Subchannel',
                        'RS_CONTACTO',
                        'RS_MAIN_CUSTOMER',
                        'RS_COMPANY_ID',
                        'RS_CRS',
                        'RO_Reservation_Done_by',
                        'US_RES_BY',
                        'USER_GROUP',
                        'XBOOKING_FILE_ID',
                        'QUEUE_CRO',
                        'XRESERVA_GRP_ID',
                        'RO_Contact_person',
                        'Room_Nights',
                        'Room_Nights_Cancellation',
                        'Room_Nights_No_Show',
                        'Room_Nights_Ok',
                        'Total_Book_Revenue_FIN_EUR',
                        'Book_Room_Revenue_EUR',
                        'Book_Breakfast_Revenue_EUR',
                        'Cancelled_Book_Revenue_EUR',
                        'No_Show_Book_Revenue_EUR',
                        'Total_Other_Revenue_FIN_EUR_new',
                        'Total_Book_Revenue_FIN_LC',
                        'Book_Room_Revenue_LC',
                        'Book_Breakfast_Revenue_LC',
                        'Cancelled_Book_Revenue_LC',
                        'No_Show_Book_Revenue_LC',
                        'Total_Other_Revenue_FIN_LC_new',
                        'RO_Reservation_type',
                        'RO_Branch_Company_Responsible_TMS',
                        'RO_Guarantee_Category',
                        'Creation_Time_Origin',
                        'Creation_Date_Origin_CET',
                        'Creation_Time_Origin_CET'
                    ]
                    TMS = TMS[orden_columnas]
                    print('TMS SUBIDO')
                    TMS.to_gbq(destination_table='TMS.b_Reservation_entry_data_raw_temporal',project_id='nh-cro-forecast',if_exists='replace')
                    TMS.to_gbq(destination_table='TMS.a_Reservation_entry_data_2022_raw',project_id='nh-cro-forecast',if_exists='append')
            else:
                next

### ----- 11. Transformer: Function to transform from sec/hours to hours/sec ----- ###

def transformer(transformation,sec):
    """
    Function to calculare seconds to hours and hours to miliseconds.

        Args:
            - Type of transformation (str): 
                            - 'Segundos': To transform from seconds to hours
                            - 'Horas': To transform from hours to miliseconds
            - sec (int): Indicate seconds or hours you want to tranfor
    """
    if transformation =='Segundos':
        #Transformar segundos a horas
        return sec/60
    elif transformation == 'Horas':
        #Transformar horas a milisegundos
        return sec * 3600000