import os
import subprocess
from os.path import join, dirname, realpath

# -*- coding: utf-8 -*-
subprocess.call("apt-get update",shell=True)
subprocess.call("apt-get -y install libsasl2-dev python-dev libldap2-dev libssl-dev",shell=True)
subprocess.call("pip install python-ldap pyopenssl",shell=True)

from flask import Flask, Blueprint, render_template, request, redirect, url_for, flash, session, make_response, Response, jsonify
import io
import csv
import json
from fpdf import FPDF
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import hashlib
import qrcode
import pymysql
import ldap
from app.app.connect import connectBD


app = Blueprint("app",__name__)

UPLOAD_FOLDER = 'app/app/file/'

#FUNCIONES

#Direccion Principal 
@app.route('/')
def Index():
  try:
    if 'FullName' in session:
      return redirect('/home')
    else:
      return render_template('index.html')
  except Exception as error:
    flash(str(error))
    return render_template('index.html')

#Valida de usuario
@app.route('/validar_usuario', methods=['POST'])
def validarusuaro():
  try:
    if request.method == 'POST':
      usuario =  request.form['user']
      clave = request.form['clave']
      validar = check_credentials( usuario, clave )
      if validar:
        link = connectBD()
        db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
        cur= db_connection.cursor()
        # Read a single record
        cur.execute("SELECT * FROM roles WHERE Usuario= \'{}\' Limit 1".format(usuario))
        data = cur.fetchone()
        cur.close()
        if data != None :
          session['UserName'] = data[1]
          session['FullName'] = data[1] +" "+ data[2]
          session['User'] = data[3]
          session['FcName'] = data[4]
          session['SiteName'] = data[5]
          session['Rango'] = data[6]
          return redirect('/home')
        else:
          return redirect('/')
      else:
        flash('Usuario o Clave Incorreto')
        return redirect('/')

  except Exception as error:
    flash(str(error))
    return redirect('/')  


#Pagina Principal
@app.route('/home',methods=['POST','GET'])
def home():
  try:
    if 'FullName' in session:
      return render_template('home.html',Datos = session)
    else:
      flash("Inicia Sesion")
      return render_template('index.html')

  except Exception as error:
    flash(str(error))
    return redirect('/') 

#proceso de retiros
@app.route('/Retiros',methods=['POST','GET'])
def No_procesable_form():
  try:
    if 'FullName' in session:
      return render_template('form/retiros.html',Datos = session)
    else:
      flash("Inicia Sesion")
      return render_template('index.html')
  except Exception as error:
    flash(str(error))
    return redirect('/') 

#Redirigie a el Formulario de Registro de Usuarios 
@app.route('/registro',methods=['POST','GET'])
def registro():
  try:
    if session['Rango'] == 'Administrador' or session['Rango'] == 'Training' :
      return render_template('registro.html', Datos = session)
    else:
      flash("Acseso Denegado")
    return render_template('index.html')
  except Exception as error:
    flash(str(error))
    return redirect('/')

#Registro de Usuarios 
@app.route('/registrar',methods=['POST'])
def registrar():
  try:
      if request.method == 'POST':
        nombre =  request.form['nombre']
        apellido =  request.form['apellido']
        rango = request.form['rango']
        Facility =  request.form['ltrabajo']
        Site = request.form['cdt']
        usuario =  request.form['usuario']
        link = connectBD()
        db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
        cur= db_connection.cursor()
        # Read a single record
        sql = "SELECT * FROM `roles` WHERE `Usuario`=%s Limit 1"
        cur.execute(sql, (usuario,))
        data = cur.fetchone()
        cur.close()
        if data != None:
          flash("El Usuario Ya Existe")
          return render_template('registro.html',Datos =session)
        else:
          try:
            link = connectBD()
            db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
            cur= db_connection.cursor()
            # Create a new record
            sql = "INSERT INTO roles (Nombre,Apellido, Usuario, facility, Site, Rango) VALUES (%s,%s,%s,%s,%s,%s)"
            cur.execute(sql,(nombre,apellido,usuario,Facility,Site,rango,))
            # connection is not autocommit by default. So you must commit to save
            # your changes.
            db_connection.commit()
            cur.close()
            flash("Registro Correcto")
            return render_template('registro.html',Datos =session)
          except Exception as error: 
            flash(str(error))
            return render_template('registro.html',Datos =session)
  except Exception as error: 
    flash(str(error))
    return render_template('registro.html',Datos =session)

# Registro de meli
@app.route('/ubicacion',methods=['POST'])
def registro_s_s():
  try:
      if request.method == 'POST':
        meli = request.form['meli']
        link = connectBD()
        db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
        cur= db_connection.cursor()
        # Read a single record
        sql = "SELECT * FROM solicitud_retiros WHERE meli = %s AND status != \'Cerrado\' AND Site =%s LIMIT 1"
        cur.execute(sql, (meli,session['SiteName']))
        retiros = cur.fetchone()
        if retiros != None:
          if int(retiros[4]) > int(retiros[7]): 
            return render_template('form/retiros.html',Datos = session,base="Retiros",meli=meli)
        link = connectBD()
        db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
        cur= db_connection.cursor()
        # Read a single record
        sql = "SELECT * FROM solicitud_donacion WHERE SKU = %s AND status != \'Cerrado\' AND Site =%s LIMIT 1 "
        cur.execute(sql, (meli,session['SiteName']))
        donacion = cur.fetchone()
        if donacion != None:
          if int(donacion[3]) > int(donacion[7]): 
            return render_template('form/retiros.html',Datos = session,base="Donacion",meli=meli)
        link = connectBD()
        db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
        cur= db_connection.cursor()
        # Read a single record
        sql = "SELECT * FROM ingram WHERE SKU = %s AND estatus != \'Cerrado\' AND Site =%s LIMIT 1 "
        cur.execute(sql, (meli,session['SiteName']))
        ingram = cur.fetchone()
        if ingram != None:
          if int(ingram[3]) > int(ingram[5]): 
            return render_template('form/retiros.html',Datos = session,base="rezagos",meli=meli)
        flash("No hay Tareas Pendientes")
        return render_template('form/retiros.html',Datos = session)
      else:
        flash("No has enviado un registro")
        return render_template('form/retiros.html',Datos = session)
  except Exception as error: 
    flash(str(error))
    return render_template('form/retiros.html',Datos = session)

# Registro de Ubicacion
@app.route('/RegistrarUbicacion/<meli>/<base>',methods=['POST'])
def registro_ubicacion(meli,base):
  try:
      if request.method == 'POST':
        ubicacion = request.form['Ubicacion']
        if base == "Retiros":  
          link = connectBD()
          db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
          cur= db_connection.cursor()
          # Read a single record
          sql = "SELECT * FROM solicitud_retiros WHERE meli = %s AND status != \'Cerrado\' AND Site =%s LIMIT 1"
          cur.execute(sql, (meli,session['SiteName']))
          retiros = cur.fetchone()
          if int(retiros[4]) > int(retiros[7]): 
            numeroOla=retiros[1]
            now= datetime.now()
            responsable=session['FullName']
            link = connectBD()
            db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
            cur= db_connection.cursor()
            # Create a new record
            sql = "INSERT INTO retiros (nuemro_de_ola, meli, cantidad, ubicacion, responsable, fecha, fecha_hora,facility ,Site) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            cur.execute(sql,(numeroOla,meli,1,ubicacion,responsable,now,now,session['FcName'],session['SiteName']))
            # connection is not autocommit by default. So you must commit to save
            # your changes.
            db_connection.commit()
            cur.close()
            piesas= int(retiros[7])+1
            idretiro =int(retiros[0])
            if  piesas < int(retiros[4]):
              status='En Proceso'
            elif  piesas == int(retiros[4]):
              status='Cerrado'
            link = connectBD()
            db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
            cur= db_connection.cursor()
            # Create a new record
            sql = "UPDATE solicitud_retiros SET cantidad_susrtida = %s, status = %s, ubicacion = %s WHERE id_tarea_retiros = %s"
            cur.execute(sql,(piesas,status,ubicacion,idretiro,))
            # connection is not autocommit by default. So you must commit to save
            # your changes.
            db_connection.commit()
            cur.close()
            session['ubicacionretiro']=ubicacion
            return render_template('form/retiros.html',Datos = session)
        elif base == "Donacion":
          link = connectBD()
          db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
          cur= db_connection.cursor()
          # Read a single record
          sql = "SELECT * FROM solicitud_donacion WHERE SKU = %s AND status != \'Cerrado\' AND Site =%s LIMIT 1 "
          cur.execute(sql, (meli,session['SiteName']))
          donacion = cur.fetchone()
          if int(donacion[3]) > int(donacion[7]): 
            numeroOla=donacion[1]
            now= datetime.now()
            responsable=session['FullName']
            link = connectBD()
            db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
            cur= db_connection.cursor()
            # Create a new record
            sql = "INSERT INTO donacion (nuemro_de_ola, SKU, cantidad, ubicacion, responsable, fecha, fecha_hora,facility ,Site) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            cur.execute(sql,(numeroOla,meli,1,ubicacion,responsable,now,now,session['FcName'],session['SiteName']))
            # connection is not autocommit by default. So you must commit to save
            # your changes.
            db_connection.commit()
            cur.close()
            piesas= int(donacion[7])+1
            iddonacion =int(donacion[0])
            if  piesas < int(donacion[3]):
              status='En Proceso'
            elif  piesas == int(donacion[3]):
              status='Cerrado'
            link = connectBD()
            db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
            cur= db_connection.cursor()
            # Create a new record
            sql = "UPDATE solicitud_donacion SET cantidad_susrtida = %s, status = %s, ubicacion = %s WHERE id_donacion = %s"
            cur.execute(sql,(piesas,status,ubicacion,iddonacion,))
            # connection is not autocommit by default. So you must commit to save
            # your changes.
            db_connection.commit()
            cur.close()
            session['ubicacionretiro']=ubicacion
            return render_template('form/retiros.html',Datos = session)
        elif base == "rezagos":
          link = connectBD()
          db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
          cur= db_connection.cursor()
          # Read a single record
          sql = "SELECT * FROM ingram WHERE SKU = %s AND estatus != \'Cerrado\' AND Site =%s LIMIT 1 "
          cur.execute(sql, (meli,session['SiteName']))
          ingram = cur.fetchone()
          if int(ingram[3]) > int(ingram[5]): 
            numeroOla=ingram[1]
            now= datetime.now() 
            responsable=session['FullName']
            link = connectBD()
            db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
            cur= db_connection.cursor()
            # Create a new record
            sql = "INSERT INTO retirio_ingram (nuemro_de_ola, SKU, cantidad, ubicacion, responsable, fecha, fecha_hora,facility ,Site) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            cur.execute(sql,(numeroOla,meli,1,ubicacion,responsable,now,now,session['FcName'],session['SiteName']))
            # connection is not autocommit by default. So you must commit to save
            # your changes.
            db_connection.commit()
            cur.close()
            piesas= int(ingram[5])+1
            idingram =int(ingram[0])
            if  piesas < int(ingram[3]):
              status='En Proceso'
            elif  piesas == int(ingram[4]):
              status='Cerrado'
            link = connectBD()
            db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
            cur= db_connection.cursor()
            # Create a new record
            sql = "UPDATE ingram SET piezas_surtidas = %s, estatus = %s, ubicacion = %s WHERE id_solicitud  = %s"
            cur.execute(sql,(piesas,status,ubicacion,idingram,))
            # connection is not autocommit by default. So you must commit to save
            # your changes.
            db_connection.commit()
            cur.close()
            session['ubicacionretiro']=ubicacion
            return render_template('form/retiros.html',Datos = session)
        flash("No hay Tareas Pendientes")
        return render_template('form/retiros.html',Datos = session)
      else:
        flash("No has enviado un registro")
        return render_template('form/retiros.html',Datos = session)
  except Exception as error: 
    flash(str(error))
    return render_template('form/retiros.html',Datos = session)

#Cerrar Session
@app.route('/logout')
def Cerrar_session():
  try:
    session.clear()
    return redirect('/')
  except Exception as error: 
    flash(str(error))
    return redirect('/')

#Reportes
@app.route('/Reporte_Retiros/<rowi>',methods=['POST','GET'])
def Reporte_retiros(rowi):
  try:
      if request.method == 'POST':
        if request.method == 'GET':
          session['rowi_recibo']=rowi
          row1 = int(session['rowi_recibo'])
          row2 = 50
        else:
            row1 = int(session['rowi_recibo'])
            row2 =50
        if 'valor' in request.form:
          if len(request.form['valor'])>0:
            session['filtro_recibo']=request.form['filtro']
            session['valor_recibo']=request.form['valor']
            if 'datefilter' in request.form:
              if len(request.form['datefilter'])>0:
                daterangef=request.form['datefilter']
                daterange=daterangef.replace("-", "' AND '")
                session['datefilter_recibo']=daterange
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                # Read a single record
                sql = "SELECT * FROM retiros WHERE {} LIKE \'%{}%\' AND fecha BETWEEN \'{}\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['filtro_recibo'],session['valor_recibo'],session['datefilter_recibo'],session['SiteName'],row1,row2)
                cur.execute(sql)
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
              else:
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                # Read a single record
                sql = "SELECT * FROM retiros WHERE {} LIKE \'%{}%\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['filtro_recibo'],session['valor_recibo'],session['SiteName'],row1,row2)
                cur.execute(sql)
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
            else:
              session.pop('datefilter_recibo')
              link = connectBD()
              db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
              cur= db_connection.cursor()
              # Read a single record
              sql = "SELECT * FROM retiros WHERE {} LIKE \'%{}%\' WHERE Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['filtro_recibo'],session['valor_recibo'],session['SiteName'],row1,row2)
              cur.execute(sql)
              data = cur.fetchall()
              cur.close()
              return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
          else:
            if 'datefilter' in request.form:
              if len(request.form['datefilter'])>0:
                if 'valor_recibo' in session:
                  if len(session['valor_recibo'])>0:
                    daterangef=request.form['datefilter']
                    daterange=daterangef.replace("-", "' AND '")
                    session['datefilter_recibo']=daterange
                    link = connectBD()
                    db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                    cur= db_connection.cursor()
                    # Read a single record
                    sql = "SELECT * FROM retiros WHERE {} LIKE \'%{}%\' AND fecha BETWEEN \'{}\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['filtro_recibo'],session['valor_recibo'],session['datefilter_recibo'],session['SiteName'],row1,row2)
                    cur.execute(sql)
                    data = cur.fetchall()
                    cur.close()
                    return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
                  else:
                    session.pop('filtro_recibo')
                    session.pop('valor_recibo')
                    link = connectBD()
                    db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                    cur= db_connection.cursor()
                    # Read a single record
                    sql = "SELECT * FROM retiros WHERE fecha BETWEEN \'{}\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['datefilter_recibo'],session['SiteName'],row1,row2)
                    cur.execute(sql)
                    data = cur.fetchall()
                    cur.close()
                    return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
                else:
                  daterangef=request.form['datefilter']
                  daterange=daterangef.replace("-", "' AND '")
                  session['datefilter_recibo']=daterange
                  link = connectBD()
                  db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                  cur= db_connection.cursor()
                  # Read a single record
                  sql = "SELECT * FROM retiros WHERE fecha BETWEEN \'{}\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['datefilter_recibo'],session['SiteName'],row1,row2)
                  cur.execute(sql)
                  data = cur.fetchall()
                  cur.close()
                  return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
              else:
                if 'valor_recibo' in session:
                  session.pop('filtro_recibo')
                  session.pop('valor_recibo')
                  if 'datefilter_recibo' in session:
                    session.pop('datefilter_recibo')
                  link = connectBD()
                  db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                  cur= db_connection.cursor()
                  # Read a single record
                  sql = "SELECT * FROM retiros WHERE Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['SiteName'],row1,row2)
                  cur.execute(sql)
                  data = cur.fetchall()
                  cur.close()
                  return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
                else:
                  link = connectBD()
                  db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                  cur= db_connection.cursor()
                  # Read a single record
                  sql = "SELECT * FROM retiros WHERE Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['SiteName'],row1,row2)
                  cur.execute(sql)
                  data = cur.fetchall()
                  cur.close()
                  return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
            else:
              if 'valor_recibo' in session:
                session.pop('filtro_recibo')
                session.pop('valor_recibo')
              if 'datefilter_recibo' in session:
                session.pop('datefilter_recibo')
              link = connectBD()
              db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
              cur= db_connection.cursor()
              # Read a single record
              sql = "SELECT * FROM retiros WHERE Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['SiteName'],row1,row2)
              cur.execute(sql)
              data = cur.fetchall()
              cur.close()
              return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
        elif 'datefilter' in request.form:
          if len(request.form['datefilter'])>0:
            if 'valor_recibo' in session:
              if len(session['valor_recibo'])>0:
                daterangef=request.form['datefilter']
                daterange=daterangef.replace("-", "' AND '")
                session['datefilter_recibo']=daterange
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                # Read a single record
                sql = "SELECT * FROM retiros WHERE {} LIKE \'%{}%\' AND fecha BETWEEN \'{}\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['filtro_recibo'],session['valor_recibo'],session['datefilter_recibo'],session['SiteName'],row1,row2)
                cur.execute(sql)
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
              else:
                session.pop('filtro_recibo')
                session.pop('valor_recibo')
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                # Read a single record
                sql = "SELECT * FROM retiros WHERE fecha BETWEEN \'{}\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['datefilter_recibo'],session['SiteName'],row1,row2)
                cur.execute(sql)
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
            else:
              link = connectBD()
              db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
              cur= db_connection.cursor()
              # Read a single record
              sql = "SELECT * FROM retiros WHERE fecha BETWEEN \'{}\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['datefilter_recibo'],session['SiteName'],row1,row2)
              cur.execute(sql)
              data = cur.fetchall()
              cur.close()
              return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
          else:
            if 'valor_recibo' in session:
              session.pop('filtro_recibo')
              session.pop('valor_recibo')
            if 'datefilter_recibo' in session:
                session.pop('datefilter_recibo')
            link = connectBD()
            db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
            cur= db_connection.cursor()
            # Read a single record
            sql = "SELECT * FROM retiros WHERE Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['SiteName'],row1,row2)
            cur.execute(sql)
            data = cur.fetchall()
            cur.close()
            return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
        else:
          if 'valor_recibo' in session:
            if len(session['valor_recibo'])>0:
              if 'datefilter_recibo' in session:
                if len(session['datefilter_recibo'])>0:
                  link = connectBD()
                  db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                  cur= db_connection.cursor()
                  # Read a single record
                  sql = "SELECT * FROM retiros WHERE {} LIKE \'%{}%\' AND fecha BETWEEN \'{}\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['filtro_recibo'],session['valor_recibo'],session['datefilter_recibo'],session['SiteName'],row1,row2)
                  cur.execute(sql)
                  data = cur.fetchall()
                  cur.close()
                  return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
                else:
                  session.pop('datefilter_recibo')
                  link = connectBD()
                  db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                  cur= db_connection.cursor()
                  # Read a single record
                  sql = "SELECT * FROM retiros WHERE {} LIKE \'%{}%\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['filtro_recibo'],session['valor_recibo'],session['SiteName'],row1,row2)
                  cur.execute(sql)
                  data = cur.fetchall()
                  cur.close()
                  return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
              else:
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                # Read a single record
                sql = "SELECT * FROM retiros WHERE {} LIKE \'%{}%\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['filtro_recibo'],session['valor_recibo'],session['SiteName'],row1,row2)
                cur.execute(sql)
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_retiros.html',Datos = session,Infos =data) 
            else:
              session.pop('filtro_recibo')
              session.pop('valor_recibo')
              if 'datefilter_recibo' in session:
                if len(session['datefilter_recibo'])>0:
                  link = connectBD()
                  db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                  cur= db_connection.cursor()
                  # Read a single record
                  sql = "SELECT * FROM retiros WHERE fecha BETWEEN \'{}\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['datefilter_recibo'],session['SiteName'],row1,row2)
                  cur.execute(sql)
                  data = cur.fetchall()
                  cur.close()
                  return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
                else:
                  link = connectBD()
                  db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                  cur= db_connection.cursor()
                  # Read a single record
                  sql = "SELECT * FROM retiros WHERE Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['SiteName'],row1,row2)
                  cur.execute(sql)
                  data = cur.fetchall()
                  cur.close()
                  return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
              else:
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                # Read a single record
                sql = "SELECT * FROM retiros WHERE Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['SiteName'],row1,row2)
                cur.execute(sql)
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
          else:
            if 'datefilter_recibo' in session:
              if len(session['datefilter_recibo'])>0:
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                # Read a single record
                sql = "SELECT * FROM retiros WHERE fecha BETWEEN \'{}\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['datefilter_recibo'],session['SiteName'],row1,row2)
                cur.execute(sql)
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
              else:
                session.pop('datefilter_recibo')
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                # Read a single record
                sql = "SELECT * FROM retiros WHERE Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['SiteName'],row1,row2)
                cur.execute(sql)
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
            else:
              if 'datefilter' in request.form:
                if len(request.form['datefilter'])>0:
                  daterangef=request.form['datefilter']
                  daterange=daterangef.replace("-", "' AND '")
                  session['datefilter_recibo']=daterange
                  link = connectBD()
                  db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                  cur= db_connection.cursor()
                  # Read a single record
                  sql = "SELECT * FROM retiros WHERE  fecha BETWEEN \'{}\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['datefilter_recibo'],session['SiteName'],row1,row2)
                  cur.execute(sql)
                  data = cur.fetchall()
                  cur.close()
                  return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
                else:
                  link = connectBD()
                  db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                  cur= db_connection.cursor()
                  # Read a single record
                  sql = "SELECT * FROM retiros WHERE Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['SiteName'],row1,row2)
                  cur.execute(sql)
                  data = cur.fetchall()
                  cur.close()
                  return render_template('reportes/t_retiros.html',Datos = session,Infos =data) 
              else:
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                # Read a single record
                sql = "SELECT * FROM retiros WHERE Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['SiteName'],row1,row2)
                cur.execute(sql)
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_retiros.html',Datos = session,Infos =data) 
        
      else: 
        if request.method == 'GET':
          session['rowi_recibo']=rowi
          row1 = int(session['rowi_recibo'])
          row2 = 50
        else:
          row1 = int(session['rowi_recibo'])
          row2 =50
        if 'valor_recibo' in session:
          if len(session['valor_recibo'])>0:
            if 'datefilter_recibo' in session:
              if len(session['datefilter_recibo'])>0:
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                # Read a single record
                sql = "SELECT * FROM retiros WHERE {} LIKE \'%{}%\' AND fecha BETWEEN \'{}\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['filtro_recibo'],session['valor_recibo'],session['datefilter_recibo'],session['SiteName'],row1,row2)
                cur.execute(sql)
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
              else:
                session.pop('datefilter_recibo')
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                # Read a single record
                sql = "SELECT * FROM retiros WHERE {} LIKE \'%{}%\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['filtro_recibo'],session['valor_recibo'],session['SiteName'],row1,row2)
                cur.execute(sql)
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
            else:
              link = connectBD()
              db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
              cur= db_connection.cursor()
              # Read a single record
              sql = "SELECT * FROM retiros WHERE {} LIKE \'%{}%\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['filtro_recibo'],session['valor_recibo'],session['SiteName'],row1,row2)
              cur.execute(sql)
              data = cur.fetchall()
              cur.close()
              return render_template('reportes/t_retiros.html',Datos = session,Infos =data) 
          else:
            session.pop('filtro_recibo')
            session.pop('valor_recibo')
            if 'datefilter_recibo' in session:
              if len(session['datefilter_recibo'])>0:
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                # Read a single record
                sql = "SELECT * FROM retiros WHERE fecha BETWEEN \'{}\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['datefilter_recibo'],session['SiteName'],row1,row2)
                cur.execute(sql)
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
              else:
                session.pop('datefilter_recibo')
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                # Read a single record
                sql = "SELECT * FROM retiros WHERE Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['SiteName'],row1,row2)
                cur.execute(sql)
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
            else:
              link = connectBD()
              db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
              cur= db_connection.cursor()
              # Read a single record
              sql = "SELECT * FROM retiros WHERE Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['SiteName'],row1,row2)
              cur.execute(sql)
              data = cur.fetchall()
              cur.close()
              return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
        else:
          if 'datefilter_recibo' in session:
            if len(session['datefilter_recibo'])>0:
              link = connectBD()
              db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
              cur= db_connection.cursor()
              # Read a single record
              sql = "SELECT * FROM retiros WHERE fecha BETWEEN \'{}\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['datefilter_recibo'],session['SiteName'],row1,row2)
              cur.execute(sql)
              data = cur.fetchall()
              cur.close()
              return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
            else:
              session.pop('datefilter_recibo')
              link = connectBD()
              db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
              cur= db_connection.cursor()
              # Read a single record
              sql = "SELECT * FROM retiros WHERE Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['SiteName'],row1,row2)
              cur.execute(sql)
              data = cur.fetchall()
              cur.close()
              return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
          else:
            link = connectBD()
            db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
            cur= db_connection.cursor()
            # Read a single record
            sql = "SELECT * FROM retiros WHERE Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['SiteName'],row1,row2)
            cur.execute(sql)
            data = cur.fetchall()
            cur.close()
            return render_template('reportes/t_retiros.html',Datos = session,Infos =data)         
  except Exception as error: 
    flash(str(error))
    return render_template('index.html')


@app.route('/Reporte_donacion/<rowi>',methods=['POST','GET'])
def Reporte_donacion(rowi):
  try:
      if request.method == 'POST':
        if request.method == 'GET':
          session['rowi_donacion']=rowi
          row1 = int(session['rowi_donacion'])
          row2 = 50
        else:
            row1 = int(session['rowi_donacion'])
            row2 =50
        if 'valor' in request.form:
          if len(request.form['valor'])>0:
            session['filtro_donacion']=request.form['filtro']
            session['valor_donacion']=request.form['valor']
            if 'datefilter' in request.form:
              if len(request.form['datefilter'])>0:
                daterangef=request.form['datefilter']
                daterange=daterangef.replace("-", "' AND '")
                session['datefilter_donacion']=daterange
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                # Read a single record
                sql = "SELECT * FROM donacion WHERE {} LIKE \'%{}%\' AND fecha BETWEEN \'{}\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['filtro_donacion'],session['valor_donacion'],session['datefilter_donacion'],session['SiteName'],row1,row2)
                cur.execute(sql)
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_donacion.html',Datos = session,Infos =data)
              else:
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                # Read a single record
                sql = "SELECT * FROM donacion WHERE {} LIKE \'%{}%\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['filtro_donacion'],session['valor_donacion'],session['SiteName'],row1,row2)
                cur.execute(sql)
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_donacion.html',Datos = session,Infos =data)
            else:
              session.pop('datefilter')
              link = connectBD()
              db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
              cur= db_connection.cursor()
              # Read a single record
              sql = "SELECT * FROM donacion WHERE {} LIKE \'%{}%\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['filtro_donacion'],session['valor_donacion'],session['SiteName'],row1,row2)
              cur.execute(sql)
              data = cur.fetchall()
              cur.close()
              return render_template('reportes/t_donacion.html',Datos = session,Infos =data)
          else:
            if 'datefilter' in request.form:
              if len(request.form['datefilter'])>0:
                if 'valor_donacion' in session:
                  if len(session['valor_donacion'])>0:
                    daterangef=request.form['datefilter']
                    daterange=daterangef.replace("-", "' AND '")
                    session['datefilter_donacion']=daterange
                    link = connectBD()
                    db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                    cur= db_connection.cursor()
                    # Read a single record
                    sql = "SELECT * FROM donacion WHERE {} LIKE \'%{}%\' AND fecha BETWEEN \'{}\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['filtro_donacion'],session['valor_donacion'],session['datefilter_donacion'],session['SiteName'],row1,row2)
                    cur.execute(sql)
                    data = cur.fetchall()
                    cur.close()
                    return render_template('reportes/t_donacion.html',Datos = session,Infos =data)
                  else:
                    session.pop('filtro_donacion')
                    session.pop('valor_donacion')
                    link = connectBD()
                    db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                    cur= db_connection.cursor()
                    # Read a single record
                    sql = "SELECT * FROM donacion WHERE fecha BETWEEN \'{}\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['datefilter_donacion'],session['SiteName'],row1,row2)
                    cur.execute(sql)
                    data = cur.fetchall()
                    cur.close()
                    return render_template('reportes/t_donacion.html',Datos = session,Infos =data)
                else:
                  daterangef=request.form['datefilter']
                  daterange=daterangef.replace("-", "' AND '")
                  session['datefilter_donacion']=daterange
                  link = connectBD()
                  db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                  cur= db_connection.cursor()
                  # Read a single record
                  sql = "SELECT * FROM donacion WHERE fecha BETWEEN \'{}\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['datefilter_donacion'],session['SiteName'],row1,row2)
                  cur.execute(sql)
                  data = cur.fetchall()
                  cur.close()
                  return render_template('reportes/t_donacion.html',Datos = session,Infos =data)
              else:
                if 'valor_donacion' in session:
                  session.pop('filtro_donacion')
                  session.pop('valor_donacion')
                if 'datefilter_donacion' in session:
                  session.pop('datefilter_donacion')
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                # Read a single record
                sql = "SELECT * FROM donacion WHERE Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['SiteName'],row1,row2)
                cur.execute(sql)
                data = cur.fetchall()
                cur.close()
            else:
              if 'valor_donacion' in session:
                session.pop('filtro_donacion')
                session.pop('valor_donacion')
              if 'datefilter_donacion' in session:
                  session.pop('datefilter_donacion')
              link = connectBD()
              db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
              cur= db_connection.cursor()
              # Read a single record
              sql = "SELECT * FROM donacion WHERE Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['SiteName'],row1,row2)
              cur.execute(sql)
              data = cur.fetchall()
              cur.close()
              return render_template('reportes/t_donacion.html',Datos = session,Infos =data)

        else:
          if 'valor_donacion' in session:
            if len(session['valor_donacion'])>0:
              if 'datefilter_donacion' in session:
                if len(session['datefilter_donacion'])>0:
                  link = connectBD()
                  db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                  cur= db_connection.cursor()
                  # Read a single record
                  sql = "SELECT * FROM donacion WHERE {} LIKE \'%{}%\' AND fecha BETWEEN \'{}\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['filtro_donacion'],session['valor_donacion'],session['datefilter_donacion'],session['SiteName'],row1,row2)
                  cur.execute(sql)
                  data = cur.fetchall()
                  cur.close()
                  return render_template('reportes/t_donacion.html',Datos = session,Infos =data)
                else:
                  session.pop('datefilter_donacion')
                  link = connectBD()
                  db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                  cur= db_connection.cursor()
                  # Read a single record
                  sql = "SELECT * FROM donacion WHERE {} LIKE \'%{}%\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['filtro_donacion'],session['valor_donacion'],session['SiteName'],row1,row2)
                  cur.execute(sql)
                  data = cur.fetchall()
                  cur.close()
                  return render_template('reportes/t_donacion.html',Datos = session,Infos =data)
              else:
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                # Read a single record
                sql = "SELECT * FROM donacion WHERE {} LIKE \'%{}%\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['filtro_donacion'],session['valor_donacion'],session['SiteName'],row1,row2)
                cur.execute(sql)
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_donacion.html',Datos = session,Infos =data) 
            else:
              session.pop('filtro_donacion')
              session.pop('valor_donacion')
              if 'datefilter_donacion' in session:
                if len(session['datefilter_donacion'])>0:
                  link = connectBD()
                  db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                  cur= db_connection.cursor()
                  # Read a single record
                  sql = "SELECT * FROM donacion WHERE fecha BETWEEN \'{}\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['datefilter_donacion'],session['SiteName'],row1,row2)
                  cur.execute(sql)
                  data = cur.fetchall()
                  cur.close()
                  return render_template('reportes/t_donacion.html',Datos = session,Infos =data)
                else:
                  link = connectBD()
                  db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                  cur= db_connection.cursor()
                  # Read a single record
                  sql = "SELECT * FROM donacion WHERE Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['SiteName'],row1,row2)
                  cur.execute(sql)
                  data = cur.fetchall()
                  cur.close()
                  return render_template('reportes/t_donacion.html',Datos = session,Infos =data)
              else:
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                # Read a single record
                sql = "SELECT * FROM donacion WHERE Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['SiteName'],row1,row2)
                cur.execute(sql)
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_donacion.html',Datos = session,Infos =data)
          else:
            if 'datefilter_donacion' in session:
              if len(session['datefilter_donacion'])>0:
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                # Read a single record
                sql = "SELECT * FROM donacion WHERE fecha BETWEEN \'{}\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['datefilter_donacion'],session['SiteName'],row1,row2)
                cur.execute(sql)
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_donacion.html',Datos = session,Infos =data)
              else:
                session.pop('datefilter_donacion')
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                cur.execute('SELECT * FROM donacion WHERE Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_donacion.html',Datos = session,Infos =data)
            else:
              if 'datefilter' in request.form:
                if len(request.form['datefilter'])>0:
                  daterangef=request.form['datefilter']
                  daterange=daterangef.replace("-", "' AND '")
                  session['datefilter_donacion']=daterange
                  link = connectBD()
                  db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                  cur= db_connection.cursor()
                  # Read a single record
                  sql = "SELECT * FROM donacion WHERE  fecha BETWEEN \'{}\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['datefilter_donacion'],session['SiteName'],row1,row2)
                  cur.execute(sql)
                  data = cur.fetchall()
                  cur.close()
                  return render_template('reportes/t_donacion.html',Datos = session,Infos =data)
                else:
                  link = connectBD()
                  db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                  cur= db_connection.cursor()
                  # Read a single record
                  sql = "SELECT * FROM donacion WHERE Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['SiteName'],row1,row2)
                  cur.execute(sql)
                  data = cur.fetchall()
                  cur.close()
                  return render_template('reportes/t_donacion.html',Datos = session,Infos =data) 
              else:
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                # Read a single record
                sql = "SELECT * FROM donacion WHERE Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['SiteName'],row1,row2)
                cur.execute(sql)
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_donacion.html',Datos = session,Infos =data) 
      else: 
        if request.method == 'GET':
          session['rowi_donacion']=rowi
          row1 = int(session['rowi_donacion'])
          row2 = 50
        else:
          row1 = int(session['rowi_donacion'])
          row2 =50
        if 'valor_donacion' in session:
          if len(session['valor_donacion'])>0:
            if 'datefilter_donacion' in session:
              if len(session['datefilter_donacion'])>0:
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                # Read a single record
                sql = "SELECT * FROM donacion WHERE {} LIKE \'%{}%\' AND fecha BETWEEN \'{}\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['filtro_donacion'],session['valor_donacion'],session['datefilter_donacion'],session['SiteName'],row1,row2)
                cur.execute(sql)
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_donacion.html',Datos = session,Infos =data)
              else:
                session.pop('datefilter_donacion')
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                # Read a single record
                sql = "SELECT * FROM donacion WHERE {} LIKE \'%{}%\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['filtro_donacion'],session['valor_donacion'],session['SiteName'],row1,row2)
                cur.execute(sql)
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_donacion.html',Datos = session,Infos =data)
            else:
              link = connectBD()
              db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
              cur= db_connection.cursor()
              # Read a single record
              sql = "SELECT * FROM donacion WHERE {} LIKE \'%{}%\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['filtro_donacion'],session['valor_donacion'],session['SiteName'],row1,row2)
              cur.execute(sql)
              data = cur.fetchall()
              cur.close()
              return render_template('reportes/t_donacion.html',Datos = session,Infos =data) 
          else:
            session.pop('filtro_donacion')
            session.pop('valor_donacion')
            if 'datefilter_donacion' in session:
              if len(session['datefilter_donacion'])>0:
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                # Read a single record
                sql = "SELECT * FROM donacion WHERE fecha BETWEEN \'{}\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['datefilter_donacion'],session['SiteName'],row1,row2)
                cur.execute(sql)
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_donacion.html',Datos = session,Infos =data)
              else:
                session.pop('datefilter_donacion')
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                # Read a single record
                sql = "SELECT * FROM donacion WHERE Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['SiteName'],row1,row2)
                cur.execute(sql)
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_donacion.html',Datos = session,Infos =data)
            else:
              link = connectBD()
              db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
              cur= db_connection.cursor()
              # Read a single record
              sql = "SELECT * FROM donacion WHERE Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['SiteName'],row1,row2)
              cur.execute(sql)
              data = cur.fetchall()
              cur.close()
              return render_template('reportes/t_donacion.html',Datos = session,Infos =data)
        else:
          if 'datefilter_donacion' in session:
            if len(session['datefilter_recibo'])>0:
              link = connectBD()
              db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
              cur= db_connection.cursor()
              # Read a single record
              sql = "SELECT * FROM donacion WHERE fecha BETWEEN \'{}\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['datefilter_donacion'],session['SiteName'],row1,row2)
              cur.execute(sql)
              data = cur.fetchall()
              cur.close()
              return render_template('reportes/t_donacion.html',Datos = session,Infos =data)
            else:
              session.pop('datefilter_donacion')
              link = connectBD()
              db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
              cur= db_connection.cursor()
              # Read a single record
              sql = "SELECT * FROM donacion WHERE Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['SiteName'],row1,row2)
              cur.execute(sql)
              data = cur.fetchall()
              cur.close()
              return render_template('reportes/t_donacion.html',Datos = session,Infos =data)
          else:
            link = connectBD()
            db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
            cur= db_connection.cursor()
            # Read a single record
            sql = "SELECT * FROM donacion WHERE Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['SiteName'],row1,row2)
            cur.execute(sql)
            data = cur.fetchall()
            cur.close()
            return render_template('reportes/t_donacion.html',Datos = session,Infos =data)         
  except Exception as error: 
    flash(str(error))
    return render_template('index.html')


@app.route('/Reporte_Ingram/<rowi>',methods=['POST','GET'])
def Reporte_ingram(rowi):
  try:
      if request.method == 'POST':
        if request.method == 'GET':
          session['rowi_ingram']=rowi
          row1 = int(session['rowi_ingram'])
          row2 = 50
        else:
            row1 = int(session['rowi_ingram'])
            row2 =50
        if 'valor' in request.form:
          if len(request.form['valor'])>0:
            session['filtro_ingram']=request.form['filtro']
            session['valor_ingram']=request.form['valor']
            if 'datefilter' in request.form:
              if len(request.form['datefilter'])>0:
                daterangef=request.form['datefilter']
                daterange=daterangef.replace("-", "' AND '")
                session['datefilter_ingram']=daterange
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                # Read a single record
                sql = "SELECT * FROM retirio_ingram WHERE {} LIKE \'%{}%\' AND fecha BETWEEN \'{}\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['filtro_ingram'],session['valor_ingram'],session['datefilter_ingram'],session['SiteName'],row1,row2)
                cur.execute(sql)
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_ingram.html',Datos = session,Infos =data)
              else:
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                # Read a single record
                sql = "SELECT * FROM retirio_ingram WHERE {} LIKE \'%{}%\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['filtro_ingram'],session['valor_ingram'],session['SiteName'],row1,row2)
                cur.execute(sql)
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_ingram.html',Datos = session,Infos =data)
            else:
              session.pop('datefilter_ingram')
              link = connectBD()
              db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
              cur= db_connection.cursor()
              # Read a single record
              sql = "SELECT * FROM retirio_ingram WHERE {} LIKE \'%{}%\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['filtro_ingram'],session['valor_ingram'],session['SiteName'],row1,row2)
              cur.execute(sql)
              data = cur.fetchall()
              cur.close()
              return render_template('reportes/t_ingram.html',Datos = session,Infos =data)
          else:
            if 'datefilter' in request.form:
              if len(request.form['datefilter'])>0:
                if 'valor_ingram' in session:
                  if len(session['valor_ingram'])>0:
                    daterangef=request.form['datefilter']
                    daterange=daterangef.replace("-", "' AND '")
                    session['datefilter_ingram']=daterange
                    link = connectBD()
                    db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                    cur= db_connection.cursor()
                    # Read a single record
                    sql = "SELECT * FROM retirio_ingram WHERE {} LIKE \'%{}%\' AND fecha BETWEEN \'{}\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['filtro_ingram'],session['valor_ingram'],session['datefilter_ingram'],session['SiteName'],row1,row2)
                    cur.execute(sql)
                    data = cur.fetchall()
                    cur.close()
                    return render_template('reportes/t_ingram.html',Datos = session,Infos =data)
                  else:
                    session.pop('filtro_ingram')
                    session.pop('valor_ingram')
                    link = connectBD()
                    db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                    cur= db_connection.cursor()
                    # Read a single record
                    sql = "SELECT * FROM retirio_ingram WHERE fecha BETWEEN \'{}\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['datefilter_ingram'],session['SiteName'],row1,row2)
                    cur.execute(sql)
                    data = cur.fetchall()
                    cur.close()
                    return render_template('reportes/t_ingram.html',Datos = session,Infos =data)
                else:
                  link = connectBD()
                  db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                  cur= db_connection.cursor()
                  # Read a single record
                  sql = "SELECT * FROM retirio_ingram WHERE fecha BETWEEN \'{}\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['datefilter_ingram'],session['SiteName'],row1,row2)
                  cur.execute(sql)
                  data = cur.fetchall()
                  cur.close()
                  return render_template('reportes/t_ingram.html',Datos = session,Infos =data)
              else:
                if 'valor_ingram' in session:
                  session.pop('filtro_ingram')
                  session.pop('valor_ingram')
                if 'datefilter_ingram' in session:
                  session.pop('datefilter_ingram')
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                # Read a single record
                sql = "SELECT * FROM retirio_ingram WHERE Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['SiteName'],row1,row2)
                cur.execute(sql)
                data = cur.fetchall()
                cur.close()
            else:
              if 'valor_ingram' in session:
                session.pop('filtro_ingram')
                session.pop('valor_ingram')
              if 'datefilter_ingram' in session:
                session.pop('datefilter_ingram')
              link = connectBD()
              db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
              cur= db_connection.cursor()
              # Read a single record
              sql = "SELECT * FROM retirio_ingram WHERE Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['SiteName'],row1,row2)
              cur.execute(sql)
              data = cur.fetchall()
              cur.close()
        else:
          if 'valor_ingram' in session:
            if len(session['valor_ingram'])>0:
              if 'datefilter_ingram' in session:
                if len(session['datefilter_ingram'])>0:
                  link = connectBD()
                  db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                  cur= db_connection.cursor()
                  # Read a single record
                  sql = "SELECT * FROM retirio_ingram WHERE {} LIKE \'%{}%\' AND fecha BETWEEN \'{}\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['filtro_ingram'],session['valor_ingram'],session['datefilter_ingram'],session['SiteName'],row1,row2)
                  cur.execute(sql)
                  data = cur.fetchall()
                  cur.close()
                  return render_template('reportes/t_ingram.html',Datos = session,Infos =data)
                else:
                  session.pop('datefilter_ingram')
                  link = connectBD()
                  db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                  cur= db_connection.cursor()
                  # Read a single record
                  sql = "SELECT * FROM retirio_ingram WHERE {} LIKE \'%{}%\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['filtro_ingram'],session['valor_ingram'],session['SiteName'],row1,row2)
                  cur.execute(sql)
                  data = cur.fetchall()
                  cur.close()
                  return render_template('reportes/t_ingram.html',Datos = session,Infos =data)
              else:
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                # Read a single record
                sql = "SELECT * FROM retirio_ingram WHERE {} LIKE \'%{}%\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['filtro_ingram'],session['valor_ingram'],session['SiteName'],row1,row2)
                cur.execute(sql)
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_ingram.html',Datos = session,Infos =data) 
            else:
              session.pop('filtro_ingram')
              session.pop('valor_ingram')
              if 'datefilter_ingram' in session:
                if len(session['datefilter_ingram'])>0:
                  link = connectBD()
                  db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                  cur= db_connection.cursor()
                  # Read a single record
                  sql = "SELECT * FROM retirio_ingram WHERE fecha BETWEEN \'{}\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['datefilter_ingram'],session['SiteName'],row1,row2)
                  cur.execute(sql)
                  data = cur.fetchall()
                  cur.close()
                  return render_template('reportes/t_ingram.html',Datos = session,Infos =data)
                else:
                  link = connectBD()
                  db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                  cur= db_connection.cursor()
                  # Read a single record
                  sql = "SELECT * FROM retirio_ingram WHERE Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['SiteName'],row1,row2)
                  cur.execute(sql)
                  data = cur.fetchall()
                  cur.close()
                  return render_template('reportes/t_ingram.html',Datos = session,Infos =data)
              else:
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                # Read a single record
                sql = "SELECT * FROM retirio_ingram WHERE Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['SiteName'],row1,row2)
                cur.execute(sql)
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_ingram.html',Datos = session,Infos =data)
          else:
            if 'datefilter_ingram' in session:
              if len(session['datefilter_ingram'])>0:
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                # Read a single record
                sql = "SELECT * FROM retirio_ingram WHERE fecha BETWEEN \'{}\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['datefilter_ingram'],session['SiteName'],row1,row2)
                cur.execute(sql)
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_ingram.html',Datos = session,Infos =data)
              else:
                session.pop('datefilter_ingram')
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                # Read a single record
                sql = "SELECT * FROM retirio_ingram WHERE Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['SiteName'],row1,row2)
                cur.execute(sql)
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_ingram.html',Datos = session,Infos =data)
            else:
              if 'datefilter' in request.form:
                if len(request.form['datefilter'])>0:
                  daterangef=request.form['datefilter']
                  daterange=daterangef.replace("-", "' AND '")
                  session['datefilter_ingram']=daterange
                  link = connectBD()
                  db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                  cur= db_connection.cursor()
                  # Read a single record
                  sql = "SELECT * FROM retirio_ingram WHERE  fecha BETWEEN \'{}\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['datefilter_ingram'],session['SiteName'],row1,row2)
                  cur.execute(sql)
                  data = cur.fetchall()
                  cur.close()
                  return render_template('reportes/t_ingram.html',Datos = session,Infos =data)
                else:
                  link = connectBD()
                  db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                  cur= db_connection.cursor()
                  # Read a single record
                  sql = "SELECT * FROM retirio_ingram WHERE Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['SiteName'],row1,row2)
                  cur.execute(sql)
                  data = cur.fetchall()
                  cur.close()
                  return render_template('reportes/t_ingram.html',Datos = session,Infos =data) 
              else:
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                # Read a single record
                sql = "SELECT * FROM retirio_ingram WHERE Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['SiteName'],row1,row2)
                cur.execute(sql)
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_ingram.html',Datos = session,Infos =data) 
      else: 
        if request.method == 'GET':
          session['rowi_ingram']=rowi
          row1 = int(session['rowi_ingram'])
          row2 = 50
        else:
          row1 = int(session['rowi_ingram'])
          row2 =50
        if 'valor_ingram' in session:
          if len(session['valor_ingram'])>0:
            if 'datefilter_ingram' in session:
              if len(session['datefilter_ingram'])>0:
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                # Read a single record
                sql = "SELECT * FROM retirio_ingram WHERE {} LIKE \'%{}%\' AND fecha BETWEEN \'{}\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['filtro_ingram'],session['valor_ingram'],session['datefilter_ingram'],session['SiteName'],row1,row2)
                cur.execute(sql)
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_ingram.html',Datos = session,Infos =data)
              else:
                session.pop('datefilter_ingram')
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                # Read a single record
                sql = "SELECT * FROM retirio_ingram WHERE {} LIKE \'%{}%\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['filtro_ingram'],session['valor_ingram'],session['SiteName'],row1,row2)
                cur.execute(sql)
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_ingram.html',Datos = session,Infos =data)
            else:
              link = connectBD()
              db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
              cur= db_connection.cursor()
              # Read a single record
              sql = "SELECT * FROM retirio_ingram WHERE {} LIKE \'%{}%\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['filtro_ingram'],session['valor_ingram'],session['SiteName'],row1,row2)
              cur.execute(sql)
              data = cur.fetchall()
              cur.close()
              return render_template('reportes/t_ingram.html',Datos = session,Infos =data) 
          else:
            session.pop('filtro_ingram')
            session.pop('valor_ingram')
            if 'datefilter_ingram' in session:
              if len(session['datefilter_ingram'])>0:
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                # Read a single record
                sql = "SELECT * FROM retirio_ingram WHERE fecha BETWEEN \'{}\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['datefilter_ingram'],session['SiteName'],row1,row2)
                cur.execute(sql)
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_ingram.html',Datos = session,Infos =data)
              else:
                session.pop('datefilter_ingram')
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                # Read a single record
                sql = "SELECT * FROM retirio_ingram WHERE Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['SiteName'],row1,row2)
                cur.execute(sql)
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_ingram.html',Datos = session,Infos =data)
            else:
              link = connectBD()
              db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
              cur= db_connection.cursor()
              # Read a single record
              sql = "SELECT * FROM retirio_ingram WHERE Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['SiteName'],row1,row2)
              cur.execute(sql)
              data = cur.fetchall()
              cur.close()
              return render_template('reportes/t_ingram.html',Datos = session,Infos =data)
        else:
          if 'datefilter_ingram' in session:
            if len(session['datefilter_ingram'])>0:
              link = connectBD()
              db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
              cur= db_connection.cursor()
              # Read a single record
              sql = "SELECT * FROM retirio_ingram WHERE fecha BETWEEN \'{}\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['datefilter_ingram'],session['SiteName'],row1,row2)
              cur.execute(sql)
              data = cur.fetchall()
              cur.close()
              return render_template('reportes/t_ingram.html',Datos = session,Infos =data)
            else:
              session.pop('datefilter_ingram')
              link = connectBD()
              db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
              cur= db_connection.cursor()
              # Read a single record
              sql = "SELECT * FROM retirio_ingram WHERE Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['SiteName'],row1,row2)
              cur.execute(sql)
              data = cur.fetchall()
              cur.close()
              return render_template('reportes/t_ingram.html',Datos = session,Infos =data)
          else:
            link = connectBD()
            db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
            cur= db_connection.cursor()
            # Read a single record
            sql = "SELECT * FROM retirio_ingram WHERE Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}".format(session['SiteName'],row1,row2)
            cur.execute(sql)
            data = cur.fetchall()
            cur.close()
            return render_template('reportes/t_ingram.html',Datos = session,Infos =data)         
  except Exception as error: 
    flash(str(error))
    return render_template('index.html')


@app.route('/csvretiros',methods=['POST','GET'])
def crear_csvretiros():
  try:
    site=session['SiteName']
    row1 = 0
    row2 =5000
    if 'valor_recibo' in session:
      if len(session['valor_recibo'])>0:
        if 'datefilter_recibo' in session:
          if len(session['datefilter_recibo'])>0:
            link = connectBD()
            db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
            cur= db_connection.cursor()
            cur.execute('SELECT * FROM retiros WHERE {} LIKE \'%{}%\' AND fecha BETWEEN \'{}\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}'.format(session['filtro_recibo'],session['valor_recibo'],session['datefilter_recibo'],session['SiteName'],row1,row2))
            data = cur.fetchall()
            cur.close()
          else:
            link = connectBD()
            db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
            cur= db_connection.cursor()
            cur.execute('SELECT * FROM retiros WHERE {} LIKE \'%{}%\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}'.format(session['filtro_recibo'],session['valor_recibo'],session['SiteName'],row1,row2))
            data = cur.fetchall()
            cur.close()
        else:
          link = connectBD()
          db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
          cur= db_connection.cursor()
          cur.execute('SELECT * FROM retiros WHERE {} LIKE \'%{}%\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}'.format(session['filtro_recibo'],session['valor_recibo'],session['SiteName'],row1,row2))
          data = cur.fetchall()
          cur.close()
      else:
        if 'datefilter_recibo' in session:
          if len(session['datefilter_recibo'])>0:
            link = connectBD()
            db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
            cur= db_connection.cursor()
            cur.execute('SELECT * FROM retiros WHERE fecha BETWEEN \'{}\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}'.format(session['datefilter_recibo'],session['SiteName'],row1,row2))
            data = cur.fetchall()
            cur.close()
          else:
            link = connectBD()
            db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
            cur= db_connection.cursor()
            cur.execute('SELECT * FROM retiros WHERE Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
            data = cur.fetchall()
            cur.close()
        else:
          link = connectBD()
          db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
          cur= db_connection.cursor()
          cur.execute('SELECT * FROM retiros WHERE Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
          data = cur.fetchall()
          cur.close()
    else:
      if 'datefilter_recibo' in session:
        if len(session['datefilter_recibo'])>0:
          link = connectBD()
          db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
          cur= db_connection.cursor()
          cur.execute('SELECT * FROM retiros WHERE fecha BETWEEN \'{}\' AND ORDER BY fecha DESC  Site =\'{}\' LIMIT {}, {}'.format(session['datefilter_recibo'],session['SiteName'],row1,row2))
          data = cur.fetchall()
          cur.close()
        else:
          link = connectBD()
          db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
          cur= db_connection.cursor()
          cur.execute('SELECT * FROM retiros WHERE Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
          data = cur.fetchall()
          cur.close()
      else:
        link = connectBD()
        db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
        cur= db_connection.cursor()
        cur.execute('SELECT * FROM retiros WHERE Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
        data = cur.fetchall()
        cur.close()
    datos="Id"+","+"Ola"+","+"Meli"+","+"Cantidad"+","+"Ubicacion"+","+"Responsable"+","+"Fecha"+","+"Fecha y Hora"+"\n"
    for res in data:
      datos+=str(res[0])
      datos+=","+str(res[1]).replace(","," ")
      datos+=","+str(res[2]).replace(","," ")
      datos+=","+str(res[3]).replace(","," ")
      datos+=","+str(res[4]).replace(","," ")
      datos+=","+str(res[5]).replace(","," ")
      datos+=","+str(res[6]).replace(","," ")
      datos+=","+str(res[7]).replace(","," ")
      datos+="\n"

    response = make_response(datos)
    response.headers["Content-Disposition"] = "attachment; filename="+"Reportre_Recibo-"+str(datetime.today())+".csv"; 
    return response
  except Exception as error: 
    flash(str(error))


@app.route('/csvdonacion',methods=['POST','GET'])
def crear_csvdonacion():
  try:
    site=session['SiteName']
    row1 = 0
    row2 =5000
    if 'valor_donacion' in session:
      if len(session['valor_donacion'])>0:
        if 'datefilter_donacion' in session:
          if len(session['datefilter_donacion'])>0:
            link = connectBD()
            db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
            cur= db_connection.cursor()
            cur.execute('SELECT * FROM donacion WHERE {} LIKE \'%{}%\' AND fecha BETWEEN \'{}\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}'.format(session['filtro_donacion'],session['valor_donacion'],session['datefilter_donacion'],session['SiteName'],row1,row2))
            data = cur.fetchall()
            cur.close()
          else:
            link = connectBD()
            db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
            cur= db_connection.cursor()
            cur.execute('SELECT * FROM donacion WHERE {} LIKE \'%{}%\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}'.format(session['filtro_donacion'],session['valor_donacion'],session['SiteName'],row1,row2))
            data = cur.fetchall()
            cur.close()
        else:
          link = connectBD()
          db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
          cur= db_connection.cursor()
          cur.execute('SELECT * FROM donacion WHERE {} LIKE \'%{}%\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}'.format(session['filtro_donacion'],session['valor_donacion'],session['SiteName'],row1,row2))
          data = cur.fetchall()
          cur.close()
      else:
        if 'datefilter_donacion' in session:
          if len(session['datefilter_donacion'])>0:
            link = connectBD()
            db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
            cur= db_connection.cursor()
            cur.execute('SELECT * FROM donacion WHERE fecha BETWEEN \'{}\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}'.format(session['datefilter_donacion'],session['SiteName'],row1,row2))
            data = cur.fetchall()
            cur.close()
          else:
            link = connectBD()
            db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
            cur= db_connection.cursor()
            cur.execute('SELECT * FROM donacion WHERE Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
            data = cur.fetchall()
            cur.close()
        else:
          link = connectBD()
          db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
          cur= db_connection.cursor()
          cur.execute('SELECT * FROM donacion WHERE Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
          data = cur.fetchall()
          cur.close()
    else:
      if 'datefilter_donacion' in session:
        if len(session['datefilter_donacion'])>0:
          link = connectBD()
          db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
          cur= db_connection.cursor()
          cur.execute('SELECT * FROM donacion WHERE fecha BETWEEN \'{}\' AND Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}'.format(session['datefilter_donacion'],session['SiteName'],row1,row2))
          data = cur.fetchall()
          cur.close()
        else:
          link = connectBD()
          db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
          cur= db_connection.cursor()
          cur.execute('SELECT * FROM donacion WHERE Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
          data = cur.fetchall()
          cur.close()
      else:
        link = connectBD()
        db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
        cur= db_connection.cursor()
        cur.execute('SELECT * FROM donacion WHERE Site =\'{}\' ORDER BY fecha DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
        data = cur.fetchall()
        cur.close()
    datos="Id"+","+"Ola"+","+"SKU"+","+"Cantidad"+","+"Ubicacion"+","+"Responsable"+","+"Fecha"+","+"Fecha y Hora"+","+"\n"
    for res in data:
      datos+=str(res[0]).replace(","," ")
      datos+=","+str(res[1]).replace(","," ")
      datos+=","+str(res[2]).replace(","," ")
      datos+=","+str(res[3]).replace(","," ")
      datos+=","+str(res[4]).replace(","," ")
      datos+=","+str(res[5]).replace(","," ")
      datos+=","+str(res[6]).replace(","," ")
      datos+=","+str(res[7]).replace(","," ")
      datos+="\n"

    response = make_response(datos)
    response.headers["Content-Disposition"] = "attachment; filename="+"Donacion-"+str(datetime.today())+".csv"; 
    return response
  except Exception as error: 
    flash(str(error))


@app.route('/csvingram',methods=['POST','GET'])
def crear_ccsvingram():
  try:
    site=session['SiteName']
    row1 = 0
    row2 =5000
    if 'valor_ingram' in session:
      if len(session['valor_ingram'])>0:
        if 'datefilter_ingram' in session:
          if len(session['datefilter'])>0:
            link = connectBD()
            db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
            cur= db_connection.cursor()
            cur.execute('SELECT * FROM retirio_ingram WHERE {} LIKE \'%{}%\' AND fecha BETWEEN \'{}\' AND Site =\'{}\'  ORDER BY fecha DESC  LIMIT {}, {}'.format(session['filtro_ingram'],session['valor_ingram'],session['datefilter_ingram'],session['SiteName'],row1,row2))
            data = cur.fetchall()
            cur.close()
          else:
            link = connectBD()
            db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
            cur= db_connection.cursor()
            cur.execute('SELECT * FROM retirio_ingram WHERE {} LIKE \'%{}%\' AND Site =\'{}\'  ORDER BY fecha DESC  LIMIT {}, {}'.format(session['filtro_ingram'],session['valor_ingram'],session['SiteName'],row1,row2))
            data = cur.fetchall()
            cur.close()
        else:
          link = connectBD()
          db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
          cur= db_connection.cursor()
          cur.execute('SELECT * FROM retirio_ingram WHERE {} LIKE \'%{}%\' AND Site =\'{}\'  ORDER BY fecha DESC  LIMIT {}, {}'.format(session['filtro_ingram'],session['valor_ingram'],session['SiteName'],row1,row2))
          data = cur.fetchall()
          cur.close()
      else:
        if 'datefilter_ingram' in session:
          if len(session['datefilter_ingram'])>0:
            link = connectBD()
            db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
            cur= db_connection.cursor()
            cur.execute('SELECT * FROM retirio_ingram WHERE fecha BETWEEN \'{}\' AND Site =\'{}\'  ORDER BY fecha DESC  LIMIT {}, {}'.format(session['datefilter_ingram'],session['SiteName'],row1,row2))
            data = cur.fetchall()
            cur.close()
          else:
            link = connectBD()
            db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
            cur= db_connection.cursor()
            cur.execute('SELECT * FROM retirio_ingram WHERE Site =\'{}\'  ORDER BY fecha DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
            data = cur.fetchall()
            cur.close()
        else:
          link = connectBD()
          db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
          cur= db_connection.cursor()
          cur.execute('SELECT * FROM retirio_ingram WHERE Site =\'{}\'  ORDER BY fecha DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
          data = cur.fetchall()
          cur.close()
    else:
      if 'datefilter_ingram' in session:
        if len(session['datefilter_ingram'])>0:
          link = connectBD()
          db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
          cur= db_connection.cursor()
          cur.execute('SELECT * FROM retirio_ingram WHERE fecha BETWEEN \'{}\' AND Site =\'{}\'  ORDER BY fecha DESC  LIMIT {}, {}'.format(session['datefilter_ingram'],session['SiteName'],row1,row2))
          data = cur.fetchall()
          cur.close()
        else:
          link = connectBD()
          db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
          cur= db_connection.cursor()
          cur.execute('SELECT * FROM retirio_ingram WHERE Site =\'{}\'  ORDER BY fecha DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
          data = cur.fetchall()
          cur.close()
      else:
        link = connectBD()
        db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
        cur= db_connection.cursor()
        cur.execute('SELECT * FROM retirio_ingram WHERE Site =\'{}\'  ORDER BY fecha DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
        data = cur.fetchall()
        cur.close()
    datos="Id"+","+"Ola"+","+"SKU"+","+"Cantidad"+","+"Ubicacion"+","+"Responsable"+","+"Fecha"+","+"Fecha y Hora"+","+"\n"
    for res in data:
      datos+=str(res[0]).replace(","," ")
      datos+=","+str(res[1]).replace(","," ")
      datos+=","+str(res[2]).replace(","," ")
      datos+=","+str(res[3]).replace(","," ")
      datos+=","+str(res[4]).replace(","," ")
      datos+=","+str(res[5]).replace(","," ")
      datos+=","+str(res[6]).replace(","," ")
      datos+=","+str(res[7]).replace(","," ")
      datos+="\n"

    response = make_response(datos)
    response.headers["Content-Disposition"] = "attachment; filename="+"Rezagos-"+str(datetime.today())+".csv"; 
    return response
  except Exception as error: 
    flash(str(error))

#Solicitudes
@app.route('/Solicitudes_Retiros/<rowi>',methods=['POST','GET'])
def solicitudes_retiros(rowi):
  try:
      if request.method == 'POST':
        if request.method == 'GET':
          session['rowi_solicitudrecibo']=rowi
          row1 = int(session['rowi_solicitudrecibo'])
          row2 = 50
        else:
            row1 = int(session['rowi_solicitudrecibo'])
            row2 =50
        if 'valor' in request.form:
          if len(request.form['valor'])>0:
            session['filtro_solicitudrecibo']=request.form['filtro']
            session['valor_solicitudrecibo']=request.form['valor']
            if 'datefilter' in request.form:
              if len(request.form['datefilter'])>0:
                daterangef=request.form['datefilter']
                daterange=daterangef.replace("-", "' AND '")
                session['datefilter_solicitudrecibo']=daterange
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                cur.execute('SELECT * FROM solicitud_retiros WHERE {} LIKE \'%{}%\' AND fecha_de_entrega BETWEEN \'{}\' AND Site =\'{}\'  ORDER BY fecha_de_entrega DESC  LIMIT {}, {}'.format(session['filtro_solicitudrecibo'],session['valor_solicitudrecibo'],session['datefilter_solicitudrecibo'],session['SiteName'],row1,row2))
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data)
              else:
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                cur.execute('SELECT * FROM solicitud_retiros WHERE {} LIKE \'%{}%\' AND Site =\'{}\'  ORDER BY fecha_de_entrega DESC  LIMIT {}, {}'.format(session['filtro_solicitudrecibo'],session['valor_solicitudrecibo'],session['SiteName'],row1,row2))
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data)
            else:
              session.pop('datefilter_solicitudrecibo')
              link = connectBD()
              db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
              cur= db_connection.cursor()
              cur.execute('SELECT * FROM solicitud_retiros WHERE {} LIKE \'%{}%\' AND Site =\'{}\'  ORDER BY fecha_de_entrega DESC  LIMIT {}, {}'.format(session['filtro_solicitudrecibo'],session['valor_solicitudrecibo'],session['SiteName'],row1,row2))
              data = cur.fetchall()
              cur.close()
              return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data)
          else:
            if 'datefilter' in request.form:
              if len(request.form['datefilter'])>0:
                if 'valor_solicitudrecibo' in session:
                  if len(session['valor_solicitudrecibo'])>0:
                    daterangef=request.form['datefilter']
                    daterange=daterangef.replace("-", "' AND '")
                    session['datefilter_solicitudrecibo']=daterange
                    link = connectBD()
                    db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                    cur= db_connection.cursor()
                    cur.execute('SELECT * FROM solicitud_retiros WHERE {} LIKE \'%{}%\' AND fecha_de_entrega BETWEEN \'{}\' AND Site =\'{}\'  ORDER BY fecha_de_entrega DESC  LIMIT {}, {}'.format(session['filtro_solicitudrecibo'],session['valor_solicitudrecibo'],session['datefilter_solicitudrecibo'],session['SiteName'],row1,row2))
                    data = cur.fetchall()
                    cur.close()
                    return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data)
                  else:
                    session.pop('filtro_solicitudrecibo')
                    session.pop('valor_solicitudrecibo')
                    link = connectBD()
                    db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                    cur= db_connection.cursor()
                    cur.execute('SELECT * FROM solicitud_retiros WHERE fecha_de_entrega BETWEEN \'{}\' AND Site =\'{}\'  ORDER BY fecha_de_entrega DESC  LIMIT {}, {}'.format(session['datefilter_solicitudrecibo'],session['SiteName'],row1,row2))
                    data = cur.fetchall()
                    cur.close()
                    return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data)
                else:
                  daterangef=request.form['datefilter']
                  daterange=daterangef.replace("-", "' AND '")
                  session['datefilter_solicitudrecibo']=daterange
                  link = connectBD()
                  db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                  cur= db_connection.cursor()
                  cur.execute('SELECT * FROM solicitud_retiros WHERE fecha_de_entrega BETWEEN \'{}\' AND Site =\'{}\'  ORDER BY fecha_de_entrega DESC  LIMIT {}, {}'.format(session['datefilter_solicitudrecibo'],session['SiteName'],row1,row2))
                  data = cur.fetchall()
                  cur.close()
                  return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data)
              else:
                if 'valor_solicitudrecibo' in session:
                  session.pop('filtro_solicitudrecibo')
                  session.pop('valor_solicitudrecibo')
                if 'datefilter_solicitudrecibo' in session:
                  session.pop('datefilter_solicitudrecibo')
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                cur.execute('SELECT * FROM solicitud_retiros WHERE Site =\'{}\' ORDER BY fecha_de_entrega DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
            else:
              if 'valor_solicitudrecibo' in session:
                session.pop('filtro_solicitudrecibo')
                session.pop('valor_solicitudrecibo')
              if 'datefilter_solicitudrecibo' in session:
                session.pop('datefilter_solicitudrecibo')
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                cur.execute('SELECT * FROM solicitud_retiros WHERE Site =\'{}\' ORDER BY fecha_de_entrega DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data)

        else:
          if 'valor_solicitudrecibo' in session:
            if len(session['valor_solicitudrecibo'])>0:
              if 'datefilter_solicitudrecibo' in session:
                if len(session['datefilter_solicitudrecibo'])>0:
                  link = connectBD()
                  db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                  cur= db_connection.cursor()
                  cur.execute('SELECT * FROM solicitud_retiros WHERE {} LIKE \'%{}%\' AND fecha_de_entrega BETWEEN \'{}\' AND Site =\'{}\'  ORDER BY fecha_de_entrega DESC  LIMIT {}, {}'.format(session['filtro_solicitudrecibo'],session['valor_solicitudrecibo'],session['datefilter_solicitudrecibo'],session['SiteName'],row1,row2))
                  data = cur.fetchall()
                  cur.close()
                  return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data)
                else:
                  session.pop('datefilter_solicitudrecibo')
                  link = connectBD()
                  db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                  cur= db_connection.cursor()
                  cur.execute('SELECT * FROM solicitud_retiros WHERE {} LIKE \'%{}%\' AND Site =\'{}\'  ORDER BY fecha_de_entrega DESC  LIMIT {}, {}'.format(session['filtro_solicitudrecibo'],session['valor_solicitudrecibo'],session['SiteName'],row1,row2))
                  data = cur.fetchall()
                  cur.close()
                  return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data)
              else:
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                cur.execute('SELECT * FROM solicitud_retiros WHERE {} LIKE \'%{}%\' AND Site =\'{}\'  ORDER BY fecha_de_entrega DESC  LIMIT {}, {}'.format(session['filtro_solicitudrecibo'],session['valor_solicitudrecibo'],session['SiteName'],row1,row2))
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data) 
            else:
              session.pop('filtro_solicitudrecibo')
              session.pop('valor_solicitudrecibo')
              if 'datefilter_solicitudrecibo' in session:
                if len(session['datefilter_solicitudrecibo'])>0:
                  link = connectBD()
                  db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                  cur= db_connection.cursor()
                  cur.execute('SELECT * FROM solicitud_retiros WHERE fecha_de_entrega BETWEEN \'{}\' AND Site =\'{}\'  ORDER BY fecha_de_entrega DESC  LIMIT {}, {}'.format(session['datefilter_solicitudrecibo'],session['SiteName'],row1,row2))
                  data = cur.fetchall()
                  cur.close()
                  return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data)
                else:
                  link = connectBD()
                  db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                  cur= db_connection.cursor()
                  cur.execute('SELECT * FROM solicitud_retiros WHERE Site =\'{}\' ORDER BY fecha_de_entrega DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
                  data = cur.fetchall()
                  cur.close()
                  return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data)
              else:
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                cur.execute('SELECT * FROM solicitud_retiros WHERE Site =\'{}\' ORDER BY fecha_de_entrega DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data)
          else:
            if 'datefilter_solicitudrecibo' in session:
              if len(session['datefilter_solicitudrecibo'])>0:
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                cur.execute('SELECT * FROM solicitud_retiros WHERE fecha_de_entrega BETWEEN \'{}\' AND Site =\'{}\'  ORDER BY fecha_de_entrega DESC  LIMIT {}, {}'.format(session['datefilter_solicitudrecibo'],session['SiteName'],row1,row2))
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data)
              else:
                session.pop('datefilter_solicitudrecibo')
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                cur.execute('SELECT * FROM solicitud_retiros WHERE Site =\'{}\' ORDER BY fecha_de_entrega DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data)
            else:
              if 'datefilter' in request.form:
                if len(request.form['datefilter'])>0:
                  daterangef=request.form['datefilter']
                  daterange=daterangef.replace("-", "' AND '")
                  session['datefilter_solicitudrecibo']=daterange
                  link = connectBD()
                  db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                  cur= db_connection.cursor()
                  cur.execute('SELECT * FROM solicitud_retiros WHERE  fecha_de_entrega BETWEEN \'{}\' AND Site =\'{}\'  ORDER BY fecha_de_entrega DESC  LIMIT {}, {}'.format(session['datefilter_solicitudrecibo'],session['SiteName'],row1,row2))
                  data = cur.fetchall()
                  cur.close()
                  return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data)
                else:
                  link = connectBD()
                  db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                  cur= db_connection.cursor()
                  cur.execute('SELECT * FROM solicitud_retiros WHERE Site =\'{}\' ORDER BY fecha_de_entrega DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
                  data = cur.fetchall()
                  cur.close()
                  return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data) 
              else:
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                cur.execute('SELECT * FROM solicitud_retiros WHERE Site =\'{}\' ORDER BY fecha_de_entrega DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data) 
      else: 
        if request.method == 'GET':
          session['rowi_solicitudrecibo']=rowi
          row1 = int(session['rowi_solicitudrecibo'])
          row2 = 50
        else:
          row1 = int(session['rowi_solicitudrecibo'])
          row2 =50
        if 'valor_solicitudrecibo' in session:
          if len(session['valor_solicitudrecibo'])>0:
            if 'datefilter_solicitudrecibo' in session:
              if len(session['datefilter_solicitudrecibo'])>0:
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                cur.execute('SELECT * FROM solicitud_retiros WHERE {} LIKE \'%{}%\' AND fecha_de_entrega BETWEEN \'{}\' AND Site =\'{}\'  ORDER BY fecha_de_entrega DESC  LIMIT {}, {}'.format(session['filtro_solicitudrecibo'],session['valor_solicitudrecibo'],session['datefilter_solicitudrecibo'],session['SiteName'],row1,row2))
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data)
              else:
                session.pop('datefilter_solicitudrecibo')
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                cur.execute('SELECT * FROM solicitud_retiros WHERE {} LIKE \'%{}%\' AND Site =\'{}\'  ORDER BY fecha_de_entrega DESC  LIMIT {}, {}'.format(session['filtro_solicitudrecibo'],session['valor_solicitudrecibo'],session['SiteName'],row1,row2))
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data)
            else:
              link = connectBD()
              db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
              cur= db_connection.cursor()
              cur.execute('SELECT * FROM solicitud_retiros WHERE {} LIKE \'%{}%\' AND Site =\'{}\'  ORDER BY fecha_de_entrega DESC  LIMIT {}, {}'.format(session['filtro_solicitudrecibo'],session['valor_solicitudrecibo'],session['SiteName'],row1,row2))
              data = cur.fetchall()
              cur.close()
              return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data) 
          else:
            session.pop('filtro_solicitudrecibo')
            session.pop('valor_solicitudrecibo')
            if 'datefilter_solicitudrecibo' in session:
              if len(session['datefilter_solicitudrecibo'])>0:
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                cur.execute('SELECT * FROM solicitud_retiros WHERE fecha_de_entrega BETWEEN \'{}\' AND Site =\'{}\'  ORDER BY fecha_de_entrega DESC  LIMIT {}, {}'.format(session['datefilter_solicitudrecibo'],session['SiteName'],row1,row2))
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data)
              else:
                session.pop('datefilter_solicitudrecibo')
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                cur.execute('SELECT * FROM solicitud_retiros WHERE Site =\'{}\' ORDER BY fecha_de_entrega DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data)
            else:
              link = connectBD()
              db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
              cur= db_connection.cursor()
              cur.execute('SELECT * FROM solicitud_retiros WHERE Site =\'{}\' ORDER BY fecha_de_entrega DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
              data = cur.fetchall()
              cur.close()
              return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data)
        else:
          if 'datefilter_solicitudrecibo' in session:
            if len(session['datefilter_solicitudrecibo'])>0:
              link = connectBD()
              db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
              cur= db_connection.cursor()
              cur.execute('SELECT * FROM solicitud_retiros WHERE fecha_de_entrega BETWEEN \'{}\' AND Site =\'{}\'  ORDER BY fecha_de_entrega DESC  LIMIT {}, {}'.format(session['datefilter_solicitudrecibo'],session['SiteName'],row1,row2))
              data = cur.fetchall()
              cur.close()
              return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data)
            else:
              session.pop('datefilter_solicitudrecibo')
              link = connectBD()
              db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
              cur= db_connection.cursor()
              cur.execute('SELECT * FROM solicitud_retiros ORDER BY fecha_de_entrega DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
              data = cur.fetchall()
              cur.close()
              return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data)
          else:
            link = connectBD()
            db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
            cur= db_connection.cursor()
            cur.execute('SELECT * FROM solicitud_retiros WHERE Site =\'{}\' ORDER BY fecha_de_entrega DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
            data = cur.fetchall()
            cur.close()
            return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data)         
  except Exception as error: 
    flash(str(error))
    return render_template('index.html')


@app.route('/Solicitudes_donacion/<rowi>',methods=['POST','GET'])
def solicitud_donacion(rowi):
  try:
      if request.method == 'POST':
        if request.method == 'GET':
          session['rowi_solicituddonacion']=rowi
          row1 = int(session['rowi_solicituddonacion'])
          row2 = 50
        else:
            row1 = int(session['rowi_solicituddonacion'])
            row2 =50
        if 'valor' in request.form:
          if len(request.form['valor'])>0:
            session['filtro_solicituddonacion']=request.form['filtro']
            session['valor_solicituddonacion']=request.form['valor']
            if 'datefilter' in request.form:
              if len(request.form['datefilter'])>0:
                daterangef=request.form['datefilter']
                daterange=daterangef.replace("-", "' AND '")
                session['datefilter_solicituddonacion']=daterange
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                cur.execute('SELECT * FROM solicitud_donacion WHERE {} LIKE \'%{}%\' AND fecha_de_solicitud BETWEEN \'{}\' AND  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['filtro_solicituddonacion'],session['valor_solicituddonacion'],session['datefilter_solicituddonacion'],session['SiteName'],row1,row2))
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_solicituddonacion.html',Datos = session,Infos =data)
              else:
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                cur.execute('SELECT * FROM solicitud_donacion WHERE {} LIKE \'%{}%\' AND  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['filtro_solicituddonacion'],session['valor_solicituddonacion'],session['SiteName'],row1,row2))
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_solicituddonacion.html',Datos = session,Infos =data)
            else:
              session.pop('datefilter_solicituddonacion')
              link = connectBD()
              db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
              cur= db_connection.cursor()
              cur.execute('SELECT * FROM solicitud_donacion WHERE {} LIKE \'%{}%\' AND  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['filtro_solicituddonacion'],session['valor_solicituddonacion'],session['SiteName'],row1,row2))
              data = cur.fetchall()
              cur.close()
              return render_template('reportes/t_solicituddonacion.html',Datos = session,Infos =data)
          else:
            if 'datefilter' in request.form:
              if len(request.form['datefilter'])>0:
                if 'valor_solicituddonacion' in session:
                  if len(session['valor_solicituddonacion'])>0:
                    daterangef=request.form['datefilter']
                    daterange=daterangef.replace("-", "' AND '")
                    session['datefilter_solicituddonacion']=daterange
                    link = connectBD()
                    db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                    cur= db_connection.cursor()
                    cur.execute('SELECT * FROM solicitud_donacion WHERE {} LIKE \'%{}%\' AND fecha_de_solicitud BETWEEN \'{}\' AND  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['filtro_solicituddonacion'],session['valor_solicituddonacion'],session['datefilter_solicituddonacion'],session['SiteName'],row1,row2))
                    data = cur.fetchall()
                    cur.close()
                    return render_template('reportes/t_solicituddonacion.html',Datos = session,Infos =data)
                  else:
                    session.pop('filtro_solicituddonacion')
                    session.pop('valor_solicituddonacion')
                    link = connectBD()
                    db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                    cur= db_connection.cursor()
                    cur.execute('SELECT * FROM solicitud_donacion WHERE fecha_de_solicitud BETWEEN \'{}\' AND  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['datefilter_solicituddonacion'],session['SiteName'],row1,row2))
                    data = cur.fetchall()
                    cur.close()
                    return render_template('reportes/t_solicituddonacion.html',Datos = session,Infos =data)
                else:
                  link = connectBD()
                  db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                  cur= db_connection.cursor()
                  cur.execute('SELECT * FROM solicitud_donacion WHERE fecha_de_solicitud BETWEEN \'{}\' AND  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['datefilter_solicituddonacion'],session['SiteName'],row1,row2))
                  data = cur.fetchall()
                  cur.close()
                  return render_template('reportes/t_solicituddonacion.html',Datos = session,Infos =data)
              else:
                if 'valor_solicituddonacion' in session:
                  session.pop('filtro_solicituddonacion')
                  session.pop('valor_solicituddonacion')
                  if 'datefilter_solicituddonacion' in session:
                    session.pop('datefilter_solicituddonacion')
                  link = connectBD()
                  db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                  cur= db_connection.cursor()
                  cur.execute('SELECT * FROM solicitud_donacion WHERE  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
                  data = cur.fetchall()
                  cur.close()
                  return render_template('reportes/t_solicituddonacion.html',Datos = session,Infos =data)
                else:
                  link = connectBD()
                  db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                  cur= db_connection.cursor()
                  cur.execute('SELECT * FROM solicitud_donacion WHERE  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
                  data = cur.fetchall()
                  cur.close()
                  return render_template('reportes/t_solicituddonacion.html',Datos = session,Infos =data)
            else:
              if 'valor_solicituddonacion' in session:
                if 'datefilter_solicituddonacion' in session:
                    session.pop('datefilter_solicituddonacion')
                session.pop('filtro_solicituddonacion')
                session.pop('valor_solicituddonacion')
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                cur.execute('SELECT * FROM solicitud_donacion WHERE  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_solicituddonacion.html',Datos = session,Infos =data)
              else:
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                cur.execute('SELECT * FROM solicitud_donacion WHERE  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_solicituddonacion.html',Datos = session,Infos =data)

        else:
          if 'valor_solicituddonacion' in session:
            if len(session['valor_solicituddonacion'])>0:
              if 'datefilter_solicituddonacion' in session:
                if len(session['datefilter_solicituddonacion'])>0:
                  link = connectBD()
                  db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                  cur= db_connection.cursor()
                  cur.execute('SELECT * FROM solicitud_donacion WHERE {} LIKE \'%{}%\' AND fecha_de_solicitud BETWEEN \'{}\' AND  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['filtro_solicituddonacion'],session['valor_solicituddonacion'],session['datefilter_solicituddonacion'],session['SiteName'],row1,row2))
                  data = cur.fetchall()
                  cur.close()
                  return render_template('reportes/t_solicituddonacion.html',Datos = session,Infos =data)
                else:
                  session.pop('datefilter_solicituddonacion')
                  link = connectBD()
                  db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                  cur= db_connection.cursor()
                  cur.execute('SELECT * FROM solicitud_donacion WHERE {} LIKE \'%{}%\' AND  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['filtro_solicituddonacion'],session['valor_solicituddonacion'],session['SiteName'],row1,row2))
                  data = cur.fetchall()
                  cur.close()
                  return render_template('reportes/t_solicituddonacion.html',Datos = session,Infos =data)
              else:
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                cur.execute('SELECT * FROM solicitud_donacion WHERE {} LIKE \'%{}%\' AND  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['filtro_solicituddonacion'],session['valor_solicituddonacion'],session['SiteName'],row1,row2))
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_solicituddonacion.html',Datos = session,Infos =data) 
            else:
              session.pop('filtro_solicituddonacion')
              session.pop('valor_solicituddonacion')
              if 'datefilter_solicituddonacion' in session:
                if len(session['datefilter_solicituddonacion'])>0:
                  link = connectBD()
                  db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                  cur= db_connection.cursor()
                  cur.execute('SELECT * FROM solicitud_donacion WHERE Fecha BETWEEN \'{}\' AND  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['datefilter_solicituddonacion'],session['SiteName'],row1,row2))
                  data = cur.fetchall()
                  cur.close()
                  return render_template('reportes/t_solicituddonacion.html',Datos = session,Infos =data)
                else:
                  link = connectBD()
                  db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                  cur= db_connection.cursor()
                  cur.execute('SELECT * FROM solicitud_donacion WHERE  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
                  data = cur.fetchall()
                  cur.close()
                  return render_template('reportes/t_solicituddonacion.html',Datos = session,Infos =data)
              else:
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                cur.execute('SELECT * FROM solicitud_donacion WHERE  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_solicituddonacion.html',Datos = session,Infos =data)
          else:
            if 'datefilter_solicituddonacion' in session:
              if len(session['datefilter_solicituddonacion'])>0:
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                cur.execute('SELECT * FROM solicitud_donacion WHERE fecha_de_solicitud BETWEEN \'{}\' AND  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['datefilter_solicituddonacion'],session['SiteName'],row1,row2))
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_solicituddonacion.html',Datos = session,Infos =data)
              else:
                session.pop('datefilter_solicituddonacion')
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                cur.execute('SELECT * FROM solicitud_donacion AND  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_solicituddonacion.html',Datos = session,Infos =data)
            else:
              if 'datefilter' in request.form:
                if len(request.form['datefilter'])>0:
                  daterangef=request.form['datefilter']
                  daterange=daterangef.replace("-", "' AND '")
                  session['datefilter_solicituddonacion']=daterange
                  link = connectBD()
                  db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                  cur= db_connection.cursor()
                  cur.execute('SELECT * FROM solicitud_donacion WHERE  fecha_de_solicitud BETWEEN \'{}\' AND  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['datefilter_solicituddonacion'],session['SiteName'],row1,row2))
                  data = cur.fetchall()
                  cur.close()
                  return render_template('reportes/t_solicituddonacion.html',Datos = session,Infos =data)
                else:
                  link = connectBD()
                  db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                  cur= db_connection.cursor()
                  cur.execute('SELECT * FROM solicitud_donacion ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(row1,row2))
                  data = cur.fetchall()
                  cur.close()
                  return render_template('reportes/t_solicituddonacion.html',Datos = session,Infos =data) 
              else:
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                cur.execute('SELECT * FROM solicitud_donacion WHERE  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_solicituddonacion.html',Datos = session,Infos =data) 
      else: 
        if request.method == 'GET':
          session['rowi_solicituddonacion']=rowi
          row1 = int(session['rowi_solicituddonacion'])
          row2 = 50
        else:
          row1 = int(session['rowi_solicituddonacion'])
          row2 =50
        if 'valor_solicituddonacion' in session:
          if len(session['valor_solicituddonacion'])>0:
            if 'datefilter_solicituddonacion' in session:
              if len(session['datefilter_solicituddonacion'])>0:
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                cur.execute('SELECT * FROM solicitud_donacion WHERE {} LIKE \'%{}%\' AND fecha_de_solicitud BETWEEN \'{}\' AND  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['filtro_solicituddonacion'],session['valor_solicituddonacion'],session['datefilter_solicituddonacion'],session['SiteName'],row1,row2))
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_solicituddonacion.html',Datos = session,Infos =data)
              else:
                session.pop('datefilter_solicituddonacion')
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                cur.execute('SELECT * FROM solicitud_donacion WHERE {} LIKE \'%{}%\' AND  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['filtro_solicituddonacion'],session['valor_solicituddonacion'],session['SiteName'],row1,row2))
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_solicituddonacion.html',Datos = session,Infos =data)
            else:
              link = connectBD()
              db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
              cur= db_connection.cursor()
              cur.execute('SELECT * FROM solicitud_donacion WHERE {} LIKE \'%{}%\' AND  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['filtro_solicituddonacion'],session['valor_solicituddonacion'],session['SiteName'],row1,row2))
              data = cur.fetchall()
              cur.close()
              return render_template('reportes/t_solicituddonacion.html',Datos = session,Infos =data) 
          else:
            session.pop('filtro_solicituddonacion')
            session.pop('valor_solicituddonacion')
            if 'datefilter_solicituddonacion' in session:
              if len(session['datefilter_solicituddonacion'])>0:
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                cur.execute('SELECT * FROM solicitud_donacion WHERE fecha_de_solicitud BETWEEN \'{}\' AND  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['datefilter_solicituddonacion'],session['SiteName'],row1,row2))
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_solicituddonacion.html',Datos = session,Infos =data)
              else:
                session.pop('datefilter_solicituddonacion')
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                cur.execute('SELECT * FROM solicitud_donacion WHERE  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_solicituddonacion.html',Datos = session,Infos =data)
            else:
              link = connectBD()
              db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
              cur= db_connection.cursor()
              cur.execute('SELECT * FROM solicitud_donacion WHERE  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
              data = cur.fetchall()
              cur.close()
              return render_template('reportes/t_solicituddonacion.html',Datos = session,Infos =data)
        else:
          if 'datefilter_solicituddonacion' in session:
            if len(session['datefilter_recibo'])>0:
              link = connectBD()
              db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
              cur= db_connection.cursor()
              cur.execute('SELECT * FROM solicitud_donacion WHERE fecha_de_solicitud BETWEEN \'{}\' AND  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['datefilter_solicituddonacion'],session['SiteName'],row1,row2))
              data = cur.fetchall()
              cur.close()
              return render_template('reportes/t_solicituddonacion.html',Datos = session,Infos =data)
            else:
              session.pop('datefilter_solicituddonacion')
              link = connectBD()
              db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
              cur= db_connection.cursor()
              cur.execute('SELECT * FROM solicitud_donacion WHERE  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
              data = cur.fetchall()
              cur.close()
              return render_template('reportes/t_solicituddonacion.html',Datos = session,Infos =data)
          else:
            link = connectBD()
            db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
            cur= db_connection.cursor()
            cur.execute('SELECT * FROM solicitud_donacion WHERE  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
            data = cur.fetchall()
            cur.close()
            return render_template('reportes/t_solicituddonacion.html',Datos = session,Infos =data)         
  except Exception as error: 
    flash(str(error))
    return render_template('index.html')


@app.route('/Solicitudes_Ingram/<rowi>',methods=['POST','GET'])
def solicitud_ingram(rowi):
  try:
      if request.method == 'POST':
        if request.method == 'GET':
          session['rowi_solicitudingram']=rowi
          row1 = int(session['rowi_solicitudingram'])
          row2 = 50
        else:
            row1 = int(session['rowi_solicitudingram'])
            row2 =50
        if 'valor' in request.form:
          if len(request.form['valor'])>0:
            session['filtro_solicitudingram']=request.form['filtro']
            session['valor_solicitudingram']=request.form['valor']
            if 'datefilter' in request.form:
              if len(request.form['datefilter'])>0:
                daterangef=request.form['datefilter']
                daterange=daterangef.replace("-", "' AND '")
                session['datefilter_solicitudingram']=daterange
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                cur.execute('SELECT * FROM ingram WHERE {} LIKE \'%{}%\' AND fecha_de_solicitud BETWEEN \'{}\' AND  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['filtro_solicitudingram'],session['valor_solicitudingram'],session['datefilter_solicitudingram'],session['SiteName'],row1,row2))
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_solicitudingram.html',Datos = session,Infos =data)
              else:
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                cur.execute('SELECT * FROM ingram WHERE {} LIKE \'%{}%\' AND  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['filtro_solicitudingram'],session['valor_solicitudingram'],session['SiteName'],row1,row2))
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_solicitudingram.html',Datos = session,Infos =data)
            else:
              session.pop('datefilter_solicitudingram')
              link = connectBD()
              db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
              cur= db_connection.cursor()
              cur.execute('SELECT * FROM ingram WHERE {} LIKE \'%{}%\' AND  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['filtro_solicitudingram'],session['valor_solicitudingram'],session['SiteName'],row1,row2))
              data = cur.fetchall()
              cur.close()
              return render_template('reportes/t_solicitudingram.html',Datos = session,Infos =data)
          else:
            if 'datefilter' in request.form:
              if len(request.form['datefilter'])>0:
                if 'valor_solicitudingram' in session:
                  if len(session['valor_solicitudingram'])>0:
                    daterangef=request.form['datefilter']
                    daterange=daterangef.replace("-", "' AND '")
                    session['datefilter_solicitudingram']=daterange
                    link = connectBD()
                    db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                    cur= db_connection.cursor()
                    cur.execute('SELECT * FROM ingram WHERE {} LIKE \'%{}%\' AND fecha_de_solicitud BETWEEN \'{}\' AND  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['filtro_solicitudingram'],session['valor_solicitudingram'],session['datefilter_solicitudingram'],session['SiteName'],row1,row2))
                    data = cur.fetchall()
                    cur.close()
                    return render_template('reportes/t_solicitudingram.html',Datos = session,Infos =data)
                  else:
                    session.pop('filtro_solicitudingram')
                    session.pop('valor_solicitudingram')
                    link = connectBD()
                    db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                    cur= db_connection.cursor()
                    cur.execute('SELECT * FROM ingram WHERE fecha_de_solicitud BETWEEN \'{}\' AND  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['datefilter_solicitudingram'],session['SiteName'],row1,row2))
                    data = cur.fetchall()
                    cur.close()
                    return render_template('reportes/t_solicitudingram.html',Datos = session,Infos =data)
                else:
                  link = connectBD()
                  db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                  cur= db_connection.cursor()
                  cur.execute('SELECT * FROM ingram WHERE fecha_de_solicitud BETWEEN \'{}\' AND  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['datefilter_solicitudingram'],session['SiteName'],row1,row2))
                  data = cur.fetchall()
                  cur.close()
                  return render_template('reportes/t_solicitudingram.html',Datos = session,Infos =data)
              else:
                if 'valor_solicitudingram' in session:
                  session.pop('filtro_solicitudingram')
                  session.pop('valor_solicitudingram')
                  if 'datefilter_solicitudingram' in session:
                    session.pop('datefilter_solicitudingram')
                  link = connectBD()
                  db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                  cur= db_connection.cursor()
                  cur.execute('SELECT * FROM ingram WHERE  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
                  data = cur.fetchall()
                  cur.close()
                  return render_template('reportes/t_solicitudingram.html',Datos = session,Infos =data)
                else:
                  link = connectBD()
                  db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                  cur= db_connection.cursor()
                  cur.execute('SELECT * FROM ingram WHERE  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
                  data = cur.fetchall()
                  cur.close()
                  return render_template('reportes/t_solicitudingram.html',Datos = session,Infos =data)
            else:
              if 'valor_solicitudingram' in session:
                if 'datefilter_solicitudingram' in session:
                    session.pop('datefilter_solicitudingram')
                session.pop('filtro_solicitudingram')
                session.pop('valor_solicitudingram')
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                cur.execute('SELECT * FROM ingram WHERE  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_solicitudingram.html',Datos = session,Infos =data)
              else:
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                cur.execute('SELECT * FROM ingram WHERE  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_solicitudingram.html',Datos = session,Infos =data)

        else:
          if 'valor_solicitudingram' in session:
            if len(session['valor_solicitudingram'])>0:
              if 'datefilter_solicitudingram' in session:
                if len(session['datefilter_solicitudingram'])>0:
                  link = connectBD()
                  db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                  cur= db_connection.cursor()
                  cur.execute('SELECT * FROM ingram WHERE {} LIKE \'%{}%\' AND fecha_de_solicitud BETWEEN \'{}\' AND  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['filtro_solicitudingram'],session['valor_solicitudingram'],session['datefilter_solicitudingram'],session['SiteName'],row1,row2))
                  data = cur.fetchall()
                  cur.close()
                  return render_template('reportes/t_solicitudingram.html',Datos = session,Infos =data)
                else:
                  session.pop('datefilter_solicitudingram')
                  link = connectBD()
                  db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                  cur= db_connection.cursor()
                  cur.execute('SELECT * FROM ingram WHERE {} LIKE \'%{}%\' AND  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['filtro_solicitudingram'],session['valor_solicitudingram'],session['SiteName'],row1,row2))
                  data = cur.fetchall()
                  cur.close()
                  return render_template('reportes/t_solicitudingram.html',Datos = session,Infos =data)
              else:
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                cur.execute('SELECT * FROM ingram WHERE {} LIKE \'%{}%\' AND  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['filtro_solicitudingram'],session['valor_solicitudingram'],session['SiteName'],row1,row2))
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_solicitudingram.html',Datos = session,Infos =data) 
            else:
              session.pop('filtro_solicitudingram')
              session.pop('valor_solicitudingram')
              if 'datefilter_solicitudingram' in session:
                if len(session['datefilter_solicitudingram'])>0:
                  link = connectBD()
                  db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                  cur= db_connection.cursor()
                  cur.execute('SELECT * FROM ingram WHERE fecha_de_solicitud BETWEEN \'{}\' AND  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['datefilter_solicitudingram'],session['SiteName'],row1,row2))
                  data = cur.fetchall()
                  cur.close()
                  return render_template('reportes/t_solicitudingram.html',Datos = session,Infos =data)
                else:
                  link = connectBD()
                  db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                  cur= db_connection.cursor()
                  cur.execute('SELECT * FROM ingram WHERE  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
                  data = cur.fetchall()
                  cur.close()
                  return render_template('reportes/t_solicitudingram.html',Datos = session,Infos =data)
              else:
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                cur.execute('SELECT * FROM ingram WHERE  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_solicitudingram.html',Datos = session,Infos =data)
          else:
            if 'datefilter_solicitudingram' in session:
              if len(session['datefilter_solicitudingram'])>0:
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                cur.execute('SELECT * FROM ingram WHERE fecha_de_solicitud BETWEEN \'{}\' AND  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['datefilter_solicitudingram'],session['SiteName'],row1,row2))
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_solicitudingram.html',Datos = session,Infos =data)
              else:
                session.pop('datefilter_solicitudingram')
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                cur.execute('SELECT * FROM ingram WHERE  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_solicitudingram.html',Datos = session,Infos =data)
            else:
              if 'datefilter' in request.form:
                if len(request.form['datefilter'])>0:
                  daterangef=request.form['datefilter']
                  daterange=daterangef.replace("-", "' AND '")
                  session['datefilter_solicitudingram']=daterange
                  link = connectBD()
                  db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                  cur= db_connection.cursor()
                  cur.execute('SELECT * FROM ingram WHERE  fecha_de_solicitud BETWEEN \'{}\' AND  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['datefilter_solicitudingram'],session['SiteName'],row1,row2))
                  data = cur.fetchall()
                  cur.close()
                  return render_template('reportes/t_solicitudingram.html',Datos = session,Infos =data)
                else:
                  link = connectBD()
                  db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                  cur= db_connection.cursor()
                  cur.execute('SELECT * FROM ingram WHERE  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
                  data = cur.fetchall()
                  cur.close()
                  return render_template('reportes/t_solicitudingram.html',Datos = session,Infos =data) 
              else:
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                cur.execute('SELECT * FROM ingram WHERE  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_solicitudingram.html',Datos = session,Infos =data) 
      else: 
        if request.method == 'GET':
          session['rowi_solicitudingram']=rowi
          row1 = int(session['rowi_solicitudingram'])
          row2 = 50
        else:
          row1 = int(session['rowi_solicitudingram'])
          row2 =50
        if 'valor_solicitudingram' in session:
          if len(session['valor_solicitudingram'])>0:
            if 'datefilter_solicitudingram' in session:
              if len(session['datefilter_solicitudingram'])>0:
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                cur.execute('SELECT * FROM ingram WHERE {} LIKE \'%{}%\' AND fecha_de_solicitud BETWEEN \'{}\' AND  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['filtro_solicitudingram'],session['valor_solicitudingram'],session['datefilter_solicitudingram'],session['SiteName'],row1,row2))
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_solicitudingram.html',Datos = session,Infos =data)
              else:
                session.pop('datefilter_solicitudingram')
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                cur.execute('SELECT * FROM ingram WHERE {} LIKE \'%{}%\' AND  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['filtro_solicitudingram'],session['valor_solicitudingram'],session['SiteName'],row1,row2))
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_solicitudingram.html',Datos = session,Infos =data)
            else:
              link = connectBD()
              db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
              cur= db_connection.cursor()
              cur.execute('SELECT * FROM ingram WHERE {} LIKE \'%{}%\' AND  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['filtro_solicitudingram'],session['valor_solicitudingram'],session['SiteName'],row1,row2))
              data = cur.fetchall()
              cur.close()
              return render_template('reportes/t_solicitudingram.html',Datos = session,Infos =data) 
          else:
            session.pop('filtro_solicitudingram')
            session.pop('valor_solicitudingram')
            if 'datefilter_solicitudingram' in session:
              if len(session['datefilter_solicitudingram'])>0:
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                cur.execute('SELECT * FROM ingram WHERE fecha_de_solicitud BETWEEN \'{}\' AND  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['datefilter_solicitudingram'],session['SiteName'],row1,row2))
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_solicitudingram.html',Datos = session,Infos =data)
              else:
                session.pop('datefilter_solicitudingram')
                link = connectBD()
                db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
                cur= db_connection.cursor()
                cur.execute('SELECT * FROM ingram WHERE  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
                data = cur.fetchall()
                cur.close()
                return render_template('reportes/t_solicitudingram.html',Datos = session,Infos =data)
            else:
              link = connectBD()
              db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
              cur= db_connection.cursor()
              cur.execute('SELECT * FROM ingram WHERE  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
              data = cur.fetchall()
              cur.close()
              return render_template('reportes/t_solicitudingram.html',Datos = session,Infos =data)
        else:
          if 'datefilter_solicitudingram' in session:
            if len(session['datefilter_solicitudingram'])>0:
              link = connectBD()
              db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
              cur= db_connection.cursor()
              cur.execute('SELECT * FROM ingram WHERE fecha_de_solicitud BETWEEN \'{}\' AND  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['datefilter_solicitudingram'],session['SiteName'],row1,row2))
              data = cur.fetchall()
              cur.close()
              return render_template('reportes/t_solicitudingram.html',Datos = session,Infos =data)
            else:
              session.pop('datefilter_solicitudingram')
              link = connectBD()
              db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
              cur= db_connection.cursor()
              cur.execute('SELECT * FROM ingram WHERE  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
              data = cur.fetchall()
              cur.close()
              return render_template('reportes/t_solicitudingram.html',Datos = session,Infos =data)
          else:
            link = connectBD()
            db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
            cur= db_connection.cursor()
            cur.execute('SELECT * FROM ingram WHERE  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
            data = cur.fetchall()
            cur.close()
            return render_template('reportes/t_solicitudingram.html',Datos = session,Infos =data)         
  except Exception as error: 
    flash(str(error))
    return render_template('index.html')


@app.route('/csvsolicitudretiros',methods=['POST','GET'])
def crear_csvsolicitudretiros():
  try:
    site=session['SiteName']
    row1 = 0
    row2 =5000
    if 'valor_solicitudrecibo' in session:
      if len(session['valor_solicitudrecibo'])>0:
        if 'datefilter_solicitudrecibo' in session:
          if len(session['datefilter_solicitudrecibo'])>0:
            link = connectBD()
            db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
            cur= db_connection.cursor()
            cur.execute('SELECT * FROM solicitud_retiros WHERE {} LIKE \'%{}%\' AND fecha_de_entrega BETWEEN \'{}\'  AND  Site =  \'{}\'  ORDER BY fecha_de_entrega DESC  LIMIT {}, {}'.format(session['filtro_solicitudrecibo'],session['valor_solicitudrecibo'],session['datefilter_solicitudrecibo'],session['SiteName'],row1,row2))
            data = cur.fetchall()
            cur.close()
          else:
            link = connectBD()
            db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
            cur= db_connection.cursor()
            cur.execute('SELECT * FROM solicitud_retiros WHERE {} LIKE \'%{}%\'  AND  Site =  \'{}\'  ORDER BY fecha_de_entrega DESC  LIMIT {}, {}'.format(session['filtro_solicitudrecibo'],session['valor_solicitudrecibo'],session['SiteName'],row1,row2))
            data = cur.fetchall()
            cur.close()
        else:
          link = connectBD()
          db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
          cur= db_connection.cursor()
          cur.execute('SELECT * FROM solicitud_retiros WHERE {} LIKE \'%{}%\'  AND  Site =  \'{}\'  ORDER BY fecha_de_entrega DESC  LIMIT {}, {}'.format(session['filtro_solicitudrecibo'],session['valor_solicitudrecibo'],session['SiteName'],row1,row2))
          data = cur.fetchall()
          cur.close()
      else:
        if 'datefilter_solicitudrecibo' in session:
          if len(session['datefilter_solicitudrecibo'])>0:
            link = connectBD()
            db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
            cur= db_connection.cursor()
            cur.execute('SELECT * FROM solicitud_retiros WHERE fecha_de_entrega BETWEEN \'{}\'  AND  Site =  \'{}\'  ORDER BY fecha_de_entrega DESC  LIMIT {}, {}'.format(session['datefilter_solicitudrecibo'],session['SiteName'],row1,row2))
            data = cur.fetchall()
            cur.close()
          else:
            link = connectBD()
            db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
            cur= db_connection.cursor()
            cur.execute('SELECT * FROM solicitud_retiros WHERE  Site =  \'{}\'  ORDER BY fecha_de_entrega DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
            data = cur.fetchall()
            cur.close()
        else:
          link = connectBD()
          db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
          cur= db_connection.cursor()
          cur.execute('SELECT * FROM solicitud_retiros  WHERE  Site =  \'{}\'  ORDER BY fecha_de_entrega DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
          data = cur.fetchall()
          cur.close()
    else:
      if 'datefilter_solicitudrecibo' in session:
        if len(session['datefilter_solicitudrecibo'])>0:
          link = connectBD()
          db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
          cur= db_connection.cursor()
          cur.execute('SELECT * FROM solicitud_retiros WHERE fecha_de_entrega BETWEEN \'{}\'  AND  Site =  \'{}\'  ORDER BY fecha_de_entrega DESC  LIMIT {}, {}'.format(session['datefilter_solicitudrecibo'],session['SiteName'],row1,row2))
          data = cur.fetchall()
          cur.close()
        else:
          link = connectBD()
          db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
          cur= db_connection.cursor()
          cur.execute('SELECT * FROM solicitud_retiros WHERE  Site =  \'{}\'  ORDER BY fecha_de_entrega DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
          data = cur.fetchall()
          cur.close()
      else:
        link = connectBD()
        db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
        cur= db_connection.cursor()
        cur.execute('SELECT * FROM solicitud_retiros WHERE  Site =  \'{}\'   ORDER BY fecha_de_entrega DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
        data = cur.fetchall()
        cur.close()
    datos="Id"+","+"Ola"+","+"Meli"+","+"Fecha de Entrega"+","+"Cantidad Solicitada"+","+"QTY_DISP_WMS"+","+"Descripción"+","+"cantidad_susrtida"+","+"Estatus"+","+"Ubicacion"+","+"Fecha de creacion"+"\n"
    for res in data:
      datos+=str(res[0])
      datos+=","+str(res[1]).replace(","," ")
      datos+=","+str(res[2]).replace(","," ")
      datos+=","+str(res[3]).replace(","," ")
      datos+=","+str(res[4]).replace(","," ")
      datos+=","+str(res[5]).replace(","," ")
      datos+=","+str(res[6]).replace(","," ")
      datos+=","+str(res[7]).replace(","," ")
      datos+=","+str(res[8]).replace(","," ")
      datos+=","+str(res[9]).replace(","," ")
      datos+=","+str(res[10]).replace(","," ")
      datos+="\n"

    response = make_response(datos)
    response.headers["Content-Disposition"] = "attachment; filename="+"solicitud_retiros-"+str(datetime.today())+".csv"; 
    return response
  except Exception as error: 
    flash(str(error))


@app.route('/csvsolicituddonacion',methods=['POST','GET'])
def crear_csvsolicituddonacion():
  try:
    site=session['SiteName']
    row1 = 0
    row2 =5000
    if 'valor_solicituddonacion' in session:
      if len(session['valor_solicituddonacion'])>0:
        if 'datefilter_solicituddonacion' in session:
          if len(session['datefilter_solicituddonacion'])>0:
            link = connectBD()
            db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
            cur= db_connection.cursor()
            cur.execute('SELECT * FROM solicitud_donacion WHERE {} LIKE \'%{}%\' AND fecha_de_solicitud BETWEEN \'{}\'  AND  Site =  \'{}\'  ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['filtro_solicituddonacion'],session['valor_solicituddonacion'],session['datefilter_solicituddonacion'],session['SiteName'],row1,row2))
            data = cur.fetchall()
            cur.close()
          else:
            link = connectBD()
            db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
            cur= db_connection.cursor()
            cur.execute('SELECT * FROM solicitud_donacion WHERE {} LIKE \'%{}%\'  AND  Site =  \'{}\'  ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['filtro_solicituddonacion'],session['valor_solicituddonacion'],session['SiteName'],row1,row2))
            data = cur.fetchall()
            cur.close()
        else:
          link = connectBD()
          db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
          cur= db_connection.cursor()
          cur.execute('SELECT * FROM solicitud_donacion WHERE {} LIKE \'%{}%\'  AND  Site =  \'{}\'  ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['filtro_solicituddonacion'],session['valor_solicituddonacion'],session['SiteName'],row1,row2))
          data = cur.fetchall()
          cur.close()
      else:
        if 'datefilter_solicituddonacion' in session:
          if len(session['datefilter_solicituddonacion'])>0:
            link = connectBD()
            db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
            cur= db_connection.cursor()
            cur.execute('SELECT * FROM solicitud_donacion WHERE fecha_de_solicitud BETWEEN \'{}\'  AND  Site =  \'{}\'  ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['datefilter_solicituddonacion'],session['SiteName'],row1,row2))
            data = cur.fetchall()
            cur.close()
          else:
            link = connectBD()
            db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
            cur= db_connection.cursor()
            cur.execute('SELECT * FROM solicitud_donacion  WHERE  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
            data = cur.fetchall()
            cur.close()
        else:
          link = connectBD()
          db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
          cur= db_connection.cursor()
          cur.execute('SELECT * FROM solicitud_donacion  WHERE  Site =  \'{}\'  ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
          data = cur.fetchall()
          cur.close()
    else:
      if 'datefilter_solicituddonacion' in session:
        if len(session['datefilter'])>0:
          link = connectBD()
          db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
          cur= db_connection.cursor()
          cur.execute('SELECT * FROM solicitud_donacion WHERE fecha_de_solicitud BETWEEN \'{}\'  AND  Site =  \'{}\'  ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['datefilter_solicituddonacion'],session['SiteName'],row1,row2))
          data = cur.fetchall()
          cur.close()
        else:
          link = connectBD()
          db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
          cur= db_connection.cursor()
          cur.execute('SELECT * FROM solicitud_donacion  WHERE  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
          data = cur.fetchall()
          cur.close()
      else:
        link = connectBD()
        db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
        cur= db_connection.cursor()
        cur.execute('SELECT * FROM solicitud_donacion  WHERE  Site =  \'{}\'  ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
        data = cur.fetchall()
        cur.close()
    datos="Id"+","+"Ola"+","+"SKU"+","+"Cantidad Solicitada"+","+"Costo Unitario"+","+"Suma de GMV"+","+"Descripcion"+","+"Cantidad Surtida "+","+"Status"+","+"Ubicacion"+","+"Fecha "+"\n"
    for res in data:
      datos+=str(res[0]).replace(","," ")
      datos+=","+str(res[1]).replace(","," ")
      datos+=","+str(res[2]).replace(","," ")
      datos+=","+str(res[3]).replace(","," ")
      datos+=","+str(res[4]).replace(","," ")
      datos+=","+str(res[5]).replace(","," ")
      datos+=","+str(res[6]).replace(","," ")
      datos+=","+str(res[7]).replace(","," ")
      datos+=","+str(res[8]).replace(","," ")
      datos+=","+str(res[9]).replace(","," ")
      datos+=","+str(res[10]).replace(","," ")
      datos+="\n"

    response = make_response(datos)
    response.headers["Content-Disposition"] = "attachment;filename= Solicitud_Donacion-"+str(datetime.today())+".csv"; 
    return response
  except Exception as error: 
    flash(str(error))


@app.route('/csvsolicitudingram',methods=['POST','GET'])
def crear_ccsvsolicitudingram():
  try:
    site=session['SiteName']
    row1 = 0
    row2 =5000
    if 'valor_solicitudingram' in session:
      if len(session['valor_solicitudingram'])>0:
        if 'datefilter_solicitudingram' in session:
          if len(session['datefilter_solicitudingram'])>0:
            link = connectBD()
            db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
            cur= db_connection.cursor()
            cur.execute('SELECT * FROM ingram WHERE {} LIKE \'%{}%\' AND fecha_de_solicitud BETWEEN \'{}\'  AND  Site =  \'{}\'  ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['filtro_solicitudingram'],session['valor_solicitudingram'],session['datefilter_solicitudingram'],session['SiteName'],row1,row2))
            data = cur.fetchall()
            cur.close()
          else:
            link = connectBD()
            db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
            cur= db_connection.cursor()
            cur.execute('SELECT * FROM ingram WHERE {} LIKE \'%{}%\' AND  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['filtro_solicitudingram'],session['valor_solicitudingram'],session['SiteName'],row1,row2))
            data = cur.fetchall()
            cur.close()
        else:
          link = connectBD()
          db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
          cur= db_connection.cursor()
          cur.execute('SELECT * FROM ingram WHERE {} LIKE \'%{}%\' AND  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['filtro_solicitudingram'],session['valor_solicitudingram'],session['SiteName'],row1,row2))
          data = cur.fetchall()
          cur.close()
      else:
        if 'datefilter_solicitudingram' in session:
          if len(session['datefilter_solicitudingram'])>0:
            link = connectBD()
            db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
            cur= db_connection.cursor()
            cur.execute('SELECT * FROM ingram WHERE fecha_de_solicitud BETWEEN \'{}\' AND  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['datefilter_solicitudingram'],session['SiteName'],row1,row2))
            data = cur.fetchall()
            cur.close()
          else:
            link = connectBD()
            db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
            cur= db_connection.cursor()
            cur.execute('SELECT * FROM ingram WHERE  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
            data = cur.fetchall()
            cur.close()
        else:
          link = connectBD()
          db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
          cur= db_connection.cursor()
          cur.execute('SELECT * FROM ingram WHERE  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
          data = cur.fetchall()
          cur.close()
    else:
      if 'datefilter_solicitudingram' in session:
        if len(session['datefilter'])>0:
          link = connectBD()
          db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
          cur= db_connection.cursor()
          cur.execute('SELECT * FROM ingram WHERE fecha_de_solicitud BETWEEN \'{}\' AND  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['datefilter_solicitudingram'],session['SiteName'],row1,row2))
          data = cur.fetchall()
          cur.close()
        else:
          link = connectBD()
          db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
          cur= db_connection.cursor()
          cur.execute('SELECT * FROM ingram WHERE  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
          data = cur.fetchall()
          cur.close()
      else:
        link = connectBD()
        db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
        cur= db_connection.cursor()
        cur.execute('SELECT * FROM ingram  WHERE  Site =  \'{}\' ORDER BY fecha_de_solicitud DESC  LIMIT {}, {}'.format(session['SiteName'],row1,row2))
        data = cur.fetchall()
        cur.close()
    datos="Id"+","+"Ola"+","+"SKU"+","+"Cantidad Solicitada"+","+"Cantidad Disponible"+","+"Piezas Surtidas"+","+"Descripcion"+","+"Estatus"+","+"Ubicacion"+","+"Fecha"+"\n"
    for res in data:
      datos+=str(res[0]).replace(","," ")
      datos+=","+str(res[1]).replace(","," ")
      datos+=","+str(res[2]).replace(","," ")
      datos+=","+str(res[3]).replace(","," ")
      datos+=","+str(res[4]).replace(","," ")
      datos+=","+str(res[5]).replace(","," ")
      datos+=","+str(res[6]).replace(","," ")
      datos+=","+str(res[7]).replace(","," ")
      datos+=","+str(res[8]).replace(","," ")
      datos+=","+str(res[9]).replace(","," ")
      datos+="\n"

    response = make_response(datos)
    response.headers["Content-Disposition"] = "attachment; filename="+"Solicitud_rezagos-"+str(datetime.today())+".csv"; 
    return response
  except Exception as error: 
    flash(str(error))

#PDF Ubicacion
@app.route('/pdf/<ubicacion>',methods=['POST','GET'])
def pdf_template(ubicacion):
  try:
    qr =  ubicacion
    img =qrcode.make(qr)
    file =open('app/static/img/qr.png','wb')
    img.save(file)
    lugar = 'De: '+session['FcName']+' | '+session['SiteName']
    facility = session['FcName']
    site = session['SiteName']
    today= datetime.today()

    pdf = FPDF(orientation = 'P',unit = 'mm',format= (128,60))
    pdf.add_page()
     
    page_width = pdf.w - 2 * pdf.l_margin
     
    pdf.ln(5)
    pdf.image('app/static/img/MercadoLibre_logo.png', x= 5, y = 5, w=25, h = 10)
    pdf.set_font('Times','B',30)
    pdf.set_text_color(0,47,109)  
    pdf.text(x = 35, y = 15 ,txt =  "Withdrawal System" )
    pdf.ln(80)

    pdf.image('app/static/img/qr.png', x= 10, y = 20, w=40, h = 40)

    pdf.set_font('Times','B',12) 

    pdf.set_text_color(0,0,0) 
    pdf.text( x= 70, y = 27, txt = str(today))
    pdf.text( x= 70, y = 37, txt = "Ubicacion:")
    pdf.text( x= 70, y = 47, txt = qr)

    return Response(pdf.output(dest='S').encode('latin-1'), mimetype='application/pdf', headers={'Content-Disposition':'Atachment;filename=Ubicacion-'+qr+'.pdf'})
  except Exception as error: 
    flash(str(error))

@app.route('/files',methods=['POST','GET'])
def Files_():
  try:
    if 'FullName' in session:
      return render_template('form/files.html',Datos=session)
    else:
      return redirect('/')
  except Exception as error: 
    flash(str(error))



@app.route('/CargarDatos',methods=['POST','GET'])
def uploadFiles():
  try:
    if 'FullName' in session:
      # get the uploaded file
      file =request.files['datos']
      base = request.form['base']
      
      if base == 'Donacion':
        file.save(os.path.join(UPLOAD_FOLDER, "donacioncsv.csv"))
        with open('app/app/file/donacioncsv.csv',"r", encoding="utf8") as csv_file:
          data=csv.reader(csv_file, delimiter=',')
          i=0
          for row in data:
            if i >0:
              now= datetime.now()
              link = connectBD()
              db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
              cur= db_connection.cursor()
              # Create a new record
              sql = "INSERT INTO solicitud_donacion (numero_ola,  SKU, Cantidad_Solicitada, costo_unitario, suma_de_gmv_total, descripcion, cantidad_susrtida,  fecha_de_solicitud, facility, Site) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
              cur.execute(sql,(row[0], row[1], row[2], row[3], row[4], row[5].decode('utf8'),0,now,session['FcName'],session['SiteName'],))
              # connection is not autocommit by default. So you must commit to save
              # your changes.
              db_connection.commit()
              cur.close()
            i+=1 
        flash(str(i)+' Registros Exitoso')
        return redirect('/files')
      elif base == 'Retiros':
        file.save(os.path.join(UPLOAD_FOLDER, "retiroscsv.csv"))
        with open('app/app/file/retiroscsv.csv',"r", encoding="utf8") as csv_file:
          data=csv.reader(csv_file, delimiter=',')
          i=0
          for row in data:
            if i>0:
              now= datetime.now()
              link = connectBD()
              db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
              cur= db_connection.cursor()
              # Create a new record
              sql = "INSERT INTO solicitud_retiros (nuemro_de_ola,  meli, fecha_de_entrega, cantidad_solizitada, QTY_DISP_WMS, Descripción, Fecha_de_creacion,  facility, Site) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
              cur.execute(sql,(row[0], row[1], row[2], row[3], row[4], row[5].decode('utf8'),now,session['FcName'],session['SiteName'],))
              # connection is not autocommit by default. So you must commit to save
              # your changes.
              db_connection.commit()
              cur.close()
            i+=1
        
        flash(str(i)+' Registros Exitoso')
        return redirect('/files')
      elif base == 'Ingram':
        file.save(os.path.join(UPLOAD_FOLDER, "ingramcsv.csv"))
        with open('app/app/file/ingramcsv.csv',"r", encoding="utf8") as csv_file:
          data=csv.reader(csv_file, delimiter=',')
          i=0
          for row in data:
            if i>0:
              now= datetime.now()
              link = connectBD()
              db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
              cur= db_connection.cursor()
              # Create a new record
              sql = "INSERT INTO ingram (numero_ola,  SKU, Cantidad_Solicitada, cantidad_disponible, descripcion, fecha_de_solicitud, facility, Site) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"
              cur.execute(sql,(row[0], row[1], row[2], row[3], row[4].decode('utf8'),now,session['FcName'],session['SiteName'],))
              # connection is not autocommit by default. So you must commit to save
              # your changes.
              db_connection.commit()
              cur.close()
            i+=1
        
        flash(str(i)+' Registros Exitoso')
        return redirect('/files')
      elif base == 'Inventario Seller':
        file.save(os.path.join(UPLOAD_FOLDER, "inventariosellercsv.csv"))
        with open('app/app/file/inventariosellercsv.csv',"r", encoding="utf8") as csv_file:
          data=csv.reader(csv_file, delimiter=',')
          i=0
          for row in data:
            if i>0:
              now= datetime.now()
              link = connectBD()
              db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
              cur= db_connection.cursor()
              # Create a new record
              sql = "INSERT INTO inventario_seller (INVENTORY_ID,  ADDRESS_ID_TO, Seller, Holding, Cantidad, fecha_de_actualizacion, facility, Site) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"
              cur.execute(sql,(row[1], row[2], row[3].decode('utf8'), row[4].decode('utf8'), row[5],now,session['FcName'],session['SiteName'],))
              # connection is not autocommit by default. So you must commit to save
              # your changes.
              db_connection.commit()
              cur.close()
            i+=1
        
        flash(str(i)+' Registros Exitoso')
        return redirect('/files')
    else:
      return redirect('/')
  except Exception as error:
    flash(str(error))
    return redirect('/files')



@app.route('/dashboard',methods=['POST','GET'])
def dash():
  try:
    if request.method == 'POST':
      daterangef=request.form['datefilter']
      daterange=daterangef.replace("-", "' AND '")
      link = connectBD()
      db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
      cur= db_connection.cursor()
      cur.execute('SELECT  SUM(cantidad_solizitada), COUNT(id_tarea_retiros) FROM solicitud_retiros WHERE status = \'Pendiente\' AND fecha_de_entrega BETWEEN \'{}\' AND  Site =  \'{}\' LIMIT 1'.format(daterange, session['SiteName']))
      retiropendientes = cur.fetchone()
      cur.close()
      link = connectBD()
      db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
      cur= db_connection.cursor()
      cur.execute('SELECT  SUM(cantidad_solizitada), COUNT(id_tarea_retiros) FROM solicitud_retiros WHERE status = \'En Proceso\' AND fecha_de_entrega BETWEEN \'{}\' AND  Site =  \'{}\'  LIMIT 1'.format(daterange, session['SiteName']))
      retiroenproceso = cur.fetchone()
      cur.close()
      link = connectBD()
      db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
      cur= db_connection.cursor()
      cur.execute('SELECT  SUM(cantidad_solizitada), COUNT(id_tarea_retiros) FROM solicitud_retiros WHERE status = \'Cerrado\' AND fecha_de_entrega BETWEEN \'{}\' AND  Site =  \'{}\'  LIMIT 1'.format(daterange, session['SiteName']))
      retirocerrado = cur.fetchone()
      cur.close()
      link = connectBD()
      db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
      cur= db_connection.cursor()
      cur.execute('SELECT  SUM(Cantidad_Solicitada), COUNT(id_donacion) FROM solicitud_donacion WHERE status = \'Pendiente\' AND fecha_de_solicitud BETWEEN \'{}\' AND  Site =  \'{}\' LIMIT 1'.format(daterange, session['SiteName']))
      donacionpendientes = cur.fetchone()
      cur.close()
      link = connectBD()
      db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
      cur= db_connection.cursor()
      cur.execute('SELECT  SUM(Cantidad_Solicitada), COUNT(id_donacion) FROM solicitud_donacion WHERE status = \'En Proceso\' AND fecha_de_solicitud BETWEEN \'{}\' AND  Site =  \'{}\'  LIMIT 1'.format(daterange, session['SiteName']))
      donacionenproceso = cur.fetchone()
      cur.close()
      link = connectBD()
      db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
      cur= db_connection.cursor()
      cur.execute('SELECT  SUM(Cantidad_Solicitada), COUNT(id_donacion) FROM solicitud_donacion WHERE status = \'Cerrado\' AND fecha_de_solicitud BETWEEN \'{}\' AND  Site =  \'{}\'  LIMIT 1'.format(daterange, session['SiteName']))
      donacionocerrado = cur.fetchone()
      cur.close()
      link = connectBD()
      db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
      cur= db_connection.cursor()
      cur.execute('SELECT  SUM(Cantidad_Solicitada), COUNT(id_solicitud) FROM ingram WHERE estatus = \'Pendiente\' AND fecha_de_solicitud BETWEEN \'{}\' AND  Site =  \'{}\' LIMIT 1'.format(daterange, session['SiteName']))
      ingrampendientes = cur.fetchone()
      cur.close()
      link = connectBD()
      db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
      cur= db_connection.cursor()
      cur.execute('SELECT  SUM(Cantidad_Solicitada), COUNT(id_solicitud) FROM ingram WHERE estatus = \'En Proceso\' AND fecha_de_solicitud BETWEEN \'{}\' AND  Site =  \'{}\'  LIMIT 1'.format(daterange, session['SiteName']))
      ingramenproceso = cur.fetchone()
      cur.close()
      link = connectBD()
      db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
      cur= db_connection.cursor()
      cur.execute('SELECT  SUM(Cantidad_Solicitada), COUNT(id_solicitud) FROM ingram WHERE estatus = \'Cerrado\' AND fecha_de_solicitud BETWEEN \'{}\' AND  Site =  \'{}\'  LIMIT 1'.format(daterange, session['SiteName']))
      ingramcerrado = cur.fetchone()
      cur.close()
      return render_template('dashboard.html',Datos=session,retiropendientes=retiropendientes,retiroenproceso=retiroenproceso,retirocerrado=retirocerrado,donacionpendientes=donacionpendientes,donacionenproceso=donacionenproceso,donacionocerrado=donacionocerrado,ingrampendientes=ingrampendientes,ingramenproceso=ingramenproceso,ingramcerrado=ingramcerrado)
    else:
      link = connectBD()
      db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
      cur= db_connection.cursor()
      cur.execute('SELECT  SUM(cantidad_solizitada), COUNT(id_tarea_retiros) FROM solicitud_retiros WHERE status = \'Pendiente\' AND fecha_de_entrega BETWEEN (CURRENT_DATE-30) AND (CURRENT_DATE) AND  Site =  \'{}\'  LIMIT 1'.format(session['SiteName']))
      retiropendientes = cur.fetchone()
      cur.close()
      link = connectBD()
      db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
      cur= db_connection.cursor()
      cur.execute('SELECT  SUM(cantidad_solizitada), COUNT(id_tarea_retiros) FROM solicitud_retiros WHERE status = \'En Proceso\' AND fecha_de_entrega BETWEEN (CURRENT_DATE-30) AND (CURRENT_DATE) AND  Site =  \'{}\' LIMIT 1'.format(session['SiteName']))
      retiroenproceso = cur.fetchone()
      cur.close()
      link = connectBD()
      db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
      cur= db_connection.cursor()
      cur.execute('SELECT  SUM(cantidad_solizitada), COUNT(id_tarea_retiros) FROM solicitud_retiros WHERE status = \'Cerrado\' AND fecha_de_entrega BETWEEN (CURRENT_DATE-30) AND (CURRENT_DATE)  AND  Site =  \'{}\' LIMIT 1'.format(session['SiteName']))
      retirocerrado = cur.fetchone()
      cur.close()
      link = connectBD()
      db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
      cur= db_connection.cursor()
      cur.execute('SELECT  SUM(Cantidad_Solicitada), COUNT(id_donacion) FROM solicitud_donacion WHERE status = \'Pendiente\' AND fecha_de_solicitud BETWEEN (CURRENT_DATE-30) AND (CURRENT_DATE) AND  Site =  \'{}\' LIMIT 1'.format(session['SiteName']))
      donacionpendientes = cur.fetchone()
      cur.close()
      link = connectBD()
      db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
      cur= db_connection.cursor()
      cur.execute('SELECT  SUM(Cantidad_Solicitada), COUNT(id_donacion) FROM solicitud_donacion WHERE status = \'En Proceso\' AND fecha_de_solicitud BETWEEN (CURRENT_DATE-30) AND (CURRENT_DATE) AND  Site =  \'{}\'  LIMIT 1'.format(session['SiteName']))
      donacionenproceso = cur.fetchone()
      cur.close()
      link = connectBD()
      db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
      cur= db_connection.cursor()
      cur.execute('SELECT  SUM(Cantidad_Solicitada), COUNT(id_donacion) FROM solicitud_donacion WHERE status = \'Cerrado\' AND fecha_de_solicitud BETWEEN (CURRENT_DATE-30) AND (CURRENT_DATE) AND  Site =  \'{}\'  LIMIT 1'.format(session['SiteName']))
      donacionocerrado = cur.fetchone()
      cur.close()
      link = connectBD()
      db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
      cur= db_connection.cursor()
      cur.execute('SELECT  SUM(Cantidad_Solicitada), COUNT(id_solicitud) FROM ingram WHERE estatus = \'Pendiente\' AND fecha_de_solicitud BETWEEN (CURRENT_DATE-30) AND (CURRENT_DATE) AND  Site =  \'{}\' LIMIT 1'.format(session['SiteName']))
      ingrampendientes = cur.fetchone()
      cur.close()
      link = connectBD()
      db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
      cur= db_connection.cursor()
      cur.execute('SELECT  SUM(Cantidad_Solicitada), COUNT(id_solicitud) FROM ingram WHERE estatus = \'En Proceso\' AND fecha_de_solicitud BETWEEN (CURRENT_DATE-30) AND (CURRENT_DATE) AND  Site =  \'{}\'  LIMIT 1'.format(session['SiteName']))
      ingramenproceso = cur.fetchone()
      cur.close()
      link = connectBD()
      db_connection = pymysql.connect(host=link[0], port=link[1], user=link[2], passwd=link[3], db=link[4]) 
      cur= db_connection.cursor()
      cur.execute('SELECT  SUM(Cantidad_Solicitada), COUNT(id_solicitud) FROM ingram WHERE estatus = \'Cerrado\' AND fecha_de_solicitud BETWEEN (CURRENT_DATE-30) AND (CURRENT_DATE) AND  Site =  \'{}\'  LIMIT 1'.format(session['SiteName']))
      ingramcerrado = cur.fetchone()
      cur.close()
      return render_template('dashboard.html',Datos=session,retiropendientes=retiropendientes,retiroenproceso=retiroenproceso,retirocerrado=retirocerrado,donacionpendientes=donacionpendientes,donacionenproceso=donacionenproceso,donacionocerrado=donacionocerrado,ingrampendientes=ingrampendientes,ingramenproceso=ingramenproceso,ingramcerrado=ingramcerrado)
  except Exception as error:
    flash(str(error))
    return redirect('/')