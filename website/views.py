from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for, session
import pandas as pd
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta, date
from . import db
import os
import locale
from sqlalchemy import text
import json
import calendar
import random
import sqlite3



views = Blueprint('views', __name__)


@views.route('/', methods=('GET', 'POST'))
def home():
    '''
    motor = db.session.get_bind()                
    conexion = motor.connect()     
    conexion.execute(text("DROP TABLE IF EXISTS 'BASE INSPECCIONAR';"))
    conexion.commit()
    conexion.close()
    
    df_data = pd.read_excel("Cantidades.xlsx")
    df_data.to_sql("Cantidades",db.session.get_bind(), index=False, if_exists='replace' )
    
    df_data = pd.read_excel("BASE INSPECCIONAR.xlsx")
    df_data.to_sql("base_inspeccion",db.session.get_bind(), index=False, if_exists='replace' )
    
    df_data = pd.read_excel("INSPECCIONADOS.xlsx")
    df_data.to_sql("prox_inspecciones",db.session.get_bind(), index=False, if_exists='replace' )
    '''
     
    
              
    max_fija = 119
    max_movil = 94
    max_energia = 30
    max_transporte = 8
    max_redes_ip = 118
    
    capa_seleccionada = "CUALQUIERA"
    ip_seleccionado = "nada"
    
    df_cantidades = pd.read_sql_table('Cantidades', db.session.get_bind())
    df_inspecciones = pd.read_sql_table('base_inspeccion', db.session.get_bind())
    df_inspeccionados = pd.read_sql_table('prox_inspecciones', db.session.get_bind())
    df_inspeccionados = df_inspeccionados[~(df_inspeccionados['GRUPO INSPECCION']=='PEND INSPECCIONAR 20% MAYOR COSTO')]
    
    df_20percent = pd.read_sql_table('prox_inspecciones', db.session.get_bind())
    df_20percent = df_20percent[df_20percent['GRUPO INSPECCION']=='PEND INSPECCIONAR 20% MAYOR COSTO']
    df_20percent = df_20percent.groupby(['CAPA']).agg({'ITEMPLAN': 'count'})
    
    df_inspec_y_20 = pd.read_sql_table('prox_inspecciones', db.session.get_bind())
     
    
    df_ip_inspeccionados = pd.read_sql_table('prox_inspecciones', db.session.get_bind())['ITEMPLAN']
    
    df_seleccionado = pd.DataFrame(df_inspeccionados.iloc[-1]).transpose()
    
    if request.method == 'POST':
        session['redirected'] = True
        form_name = request.form.get('form_name')
        if form_name == 'generar_ip':
            capa_seleccionada = request.form.get('options')
            session['capa_seleccionada'] = capa_seleccionada
            
            if capa_seleccionada == "CUALQUIERA":
                pass
            else:
                df_inspecciones = df_inspecciones[df_inspecciones['CAPA']==capa_seleccionada]
            
            
            if df_cantidades['MOVIL'].iloc[0]>=max_movil:
                df_inspecciones = df_inspecciones[~(df_inspecciones['CAPA']=='MOVIL')]
            if df_cantidades['FIJA'].iloc[0]>=max_fija:
                df_inspecciones = df_inspecciones[~(df_inspecciones['CAPA']=='FIJA')]
            if  df_cantidades['ENERGIA'].iloc[0]>=max_energia:
                df_inspecciones = df_inspecciones[~(df_inspecciones['CAPA']=='ENERGIA')]   
            if  df_cantidades['TRANSPORTE'].iloc[0]>=max_transporte:
                df_inspecciones = df_inspecciones[~(df_inspecciones['CAPA']=='TRANSPORTE')]   
            if  df_cantidades['REDES IP'].iloc[0]>=max_redes_ip:
                df_inspecciones = df_inspecciones[~(df_inspecciones['CAPA']=='REDES IP')]   
            
            print("atento")
            df_inspecciones = df_inspecciones[~df_inspecciones['ITEMPLAN'].isin(df_ip_inspeccionados)]            
            max_aleatorio = len(df_inspecciones)
            
            if max_aleatorio>0:
                numero_aleatorio = random.randint(1, max_aleatorio)
                ip = df_inspecciones.iloc[numero_aleatorio-1]['ITEMPLAN'] 
                session['ip_seleccionado'] = ip
                
                ##elif form_name == 'cargar_ip':
                if df_ip_inspeccionados.isin([ip]).any():
                    print("El valor ya se encuentra guardado")
                else:   
                    
                    fila = df_inspecciones[df_inspecciones['ITEMPLAN']==ip].drop(columns=['ID'])  
                    fila['GRUPO INSPECCION'] =  'SE INSPECCIONARA, OCT-DIC '
                    fila['FECHA SELECCIONADO'] =  date.today()
                    #capa = fila['CAPA']
                    fila.to_sql("prox_inspecciones",db.session.get_bind(), index=False, if_exists='append')
                    df_seleccionado = fila
                    
                    
                    cant_capas_completo = {"MOVIL":0, "FIJA":0, "TRANSPORTE":0, "ENERGIA":0, "REDES IP":0}
                    df_inspeccionados = pd.read_sql_table('prox_inspecciones', db.session.get_bind())
                    df_inspeccionados = df_inspeccionados[df_inspeccionados['GRUPO INSPECCION'].str.contains('OCT-DIC', case=False, na=False)]
                    
                    cant_capas_actual = df_inspeccionados['CAPA'].value_counts().to_dict()
                    cant_capas_completo.update(cant_capas_actual)
                    df_cantidades = pd.DataFrame([cant_capas_completo])
                    df_cantidades.to_sql("Cantidades",db.session.get_bind(), index=False, if_exists='replace' )
            else:
                pass
        
        
        return redirect(url_for('views.home'))    
    
    redirected = session.pop('redirected', False)
    if redirected:
        ip_seleccionado = session.get('ip_seleccionado', 'nada')
        df_seleccionado = df_inspecciones[df_inspecciones['ITEMPLAN']==ip_seleccionado].drop(columns=['ID'])
        capa_seleccionada = session.get('capa_seleccionada', 'CUALQUIERA')
        
    else:
        ip_seleccionado = "nada"
    
    agregado = df_inspeccionados[df_inspeccionados['GRUPO INSPECCION'].str.contains('OCT-DIC', case=False, na=False)].groupby(['DISTRITO', 'CAPA']).agg({'ITEMPLAN': 'count'}).reset_index()
    df_distritos = agregado.pivot_table(index='DISTRITO', columns='CAPA', values='ITEMPLAN', fill_value=0)
    df_distritos = df_distritos.astype(int)

    df_distritos['Total_Fila'] = df_distritos.sum(axis=1)
    df_distritos.loc['Total_Columna'] = df_distritos.sum()
    
    #print(df_cantidades)    
    #print(df_cantidades.to_dict(orient='records')[0])
    
    percent20=df_20percent.to_dict()['ITEMPLAN']
    cant_por_capa=df_cantidades.to_dict(orient='records')[0]
    proyeccion = {key: percent20[key] + cant_por_capa[key] for key in percent20}
    return render_template("home.html", capa_seleccionada=capa_seleccionada, proyeccion = proyeccion, percent20=df_20percent.to_dict()['ITEMPLAN'], df_distritos=df_distritos, ip_seleccionado=ip_seleccionado, df_seleccionado=df_seleccionado, cant_por_capa=cant_por_capa, df_inspec_y_20=df_inspec_y_20)
    '''
        motor = db.session.get_bind()                
        conexion = motor.connect()     
        conexion.execute(text("DROP TABLE IF EXISTS data_materiales;"))
        conexion.commit()
        conexion.close()
    '''
    
    
    
    
    #df_data = pd.read_excel("Cantidades.xlsx")
    #df_data.to_sql("Cantidades",db.session.get_bind(), index=False, if_exists='replace' )
    
    #df_data = pd.read_excel("BASE INSPECCIONAR.xlsx")
    #df_data['F.ATENCION SOL']=df_data['F.ATENCION SOL'].dt.date
    #print(df_data['F.ATENCION SOL'].dtypes)
    #df_data.to_sql("base_inspeccion",db.session.get_bind(), index=False, if_exists='replace' )
    
    
    

    #df_inspecciones = pd.read_sql_table('base_inspeccion', db.session.get_bind())
    
    
    
    #df_cantidades = pd.read_sql_table('Cantidades', db.session.get_bind())
    
    
    
    #fila_df['ID'] = fila_df['ID'].astype(int)
    #print(fila_df['ID'].dtype)
    
    #df_prox_inspecciones = pd.read_sql_table('prox_inspecciones', db.session.get_bind())
    #print(df_prox_inspecciones)
    
    
    '''
    data = {
    'ID': [1],
    'ITEMPLAN': ['23-8318499815'],
    'F.ATENCION SOL': ['2024-05-21'],
    'PROYECTO': ['PIN REDES IP OPEX'],
    'DISTRITO': ['NO INDICA'],
    'CAPA': ['REDES IP']
    }
    df_data = pd.DataFrame(data)
    df_data.to_sql("prox_inspecciones",db.session.get_bind(), index=False, if_exists='replace' )
    '''
    
    
    
    '''
    data = {
    'FIJA': [0],
    'MOVIL': [0],
    'TRANSPORTE': [0],
    'ENERGIA': [0],
    'OBRA PUBLICA': [0],
    'REDES IP': [0]
    }
    df_data = pd.DataFrame(data)
    df_data.to_sql("Cantidades",db.session.get_bind(), index=False, if_exists='replace' )
    '''