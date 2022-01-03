from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response, Response, jsonify
import io
import csv
from fpdf import FPDF
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import hashlib
import qrcode 
import csv

app = Flask(__name__)

#MySQL Connection
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'retiros'
mysql = MySQL(app)

# settings
app.secret_key = 'mysecretkey'


#Direccion Principal 
@app.route('/')
def Index():
  try:
    if 'FullName' in session:
      return redirect('/home')
    else:
      return render_template('index.html')
  except:
      return render_template('index.html')

#Valida de usuario
@app.route('/validar_usuario', methods=['POST'])
def validarusuaro():
    if request.method == 'POST':
      usuario =  request.form['user']
      cur = mysql.connection.cursor()
      cur.execute('SELECT * FROM usuarios WHERE Usuario = \'{}\' LIMIT 1 '.format(usuario))
      data = cur.fetchall()
      if len(data) > 0 :
        username = data[0][1]
        user = data[0][3]
        return render_template('inicio.html',username=username,user=user)
      else:
        return render_template('index.html')    

#Validacion de Contraseña
@app.route('/validar_contrasena/<user>', methods=['POST'])
def validarcontrasena(user):
    if request.method == 'POST':
      usuario =  user
      password = request.form['password']
      cur = mysql.connection.cursor()
      cur.execute('SELECT * FROM usuarios WHERE Usuario = \'{}\' LIMIT 1 '.format(usuario))
      data = cur.fetchall()
      if len(data) > 0 :
          if check_password_hash(data[0][6],password):
            session['UserName'] = data[0][1]
            session['FullName'] = data[0][1] + data[0][2]
            session['User'] = data[0][3]
            session['FcName'] = data[0][4]
            session['SiteName'] = data[0][5]
            session['Rango'] = data[0][7]
            return redirect('/home')
          else:
            flash('Contraseña Incorrecta')
            return render_template('index.html')
      else:
        return render_template('index.html')   
#Pagina Principal
@app.route('/home',methods=['POST','GET'])
def home():
  if 'FullName' in session:
    return render_template('home.html',Datos = session)
  else:
    flash("Inicia Sesion")
    return render_template('index.html')

#formulario ordenes no Procesables 
@app.route('/Retiros',methods=['POST','GET'])
def No_procesable_form():
  if 'FullName' in session:
    return render_template('form/retiros.html',Datos = session)
  else:
    flash("Inicia Sesion")
    return render_template('index.html')
#Redirigie a el Formulario de Registro de Usuarios 
@app.route('/registro',methods=['POST','GET'])
def registro():
  try:
    if session['Rango'] == 'Administrador':
      return render_template('registro.html', Datos = session)
    else:
      flash("Acseso Denegado")
    return render_template('index.html')
  except:
    flash("Inicia Secion")
    return render_template('index.html')

#Registro de Usuarios 
@app.route('/registrar',methods=['POST'])
def registrar():
  try:
      if request.method == 'POST':
        nombre =  request.form['nombre']
        apellido =  request.form['apellido']
        rango = request.form['rango']
        ltrabajo =  request.form['ltrabajo']
        cdt = request.form['cdt']
        usuario =  request.form['usuario']

        password = _create_password(request.form['pass'])
        password2 = _create_password(request.form['pass2'])
        
        if check_password_hash(password,request.form['pass']) and check_password_hash(password,request.form['pass2']):
          
          cur = mysql.connection.cursor()
          cur.execute('SELECT * FROM usuarios WHERE Usuario = \'{}\'  LIMIT 1 '.format(usuario,password))
          data = cur.fetchall()
          if len(data) > 0:
            flash("El Usuario Ya Existe")
            return render_template('registro.html',Datos =session)
          else:
            cur = mysql.connection.cursor()
            cur.execute('INSERT INTO `usuarios` (Nombre,Apellido, Usuario, ltrabajo, cdt, contraseña, Rango) VALUES (%s,%s,%s,%s,%s,%s,%s)',(nombre,apellido,usuario,ltrabajo,cdt,password,rango))
            mysql.connection.commit()
            flash("Registro Correcto")
            return render_template('registro.html',Datos =session)
        else:
          flash("Las Contraceñas no Cionciden")
          return render_template('registro.html',Datos =session)
  except:
    return render_template('registro.html',Datos =session)
def _create_password(password):
   return generate_password_hash(password,'pbkdf2:sha256:30',30)

# Registro de Salidas Service Center
@app.route('/ubicacion',methods=['POST'])
def registro_s_s():
  try:
      if request.method == 'POST':
        meli = request.form['meli']
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM solicitud_retiros WHERE meli = \'{}\' AND status != \'Cerrado\' LIMIT 1 '.format(meli))
        retiros = cur.fetchall()
        print(retiros)
        if len(retiros)>0:
          if int(retiros[0][4]) > int(retiros[0][7]): 
            numeroOla=retiros[0][1]
            ubicacion =  'R-'+meli+'-'+str(retiros[0][3])
            now= datetime.now()
            responsable=session['FullName']
            cur = mysql.connection.cursor()
            cur.execute('INSERT INTO retiros (nuemro_de_ola, meli, cantidad, ubicacion, responsable, fecha, fecha_hora) VALUES (%s,%s,%s,%s,%s,%s,%s)',(numeroOla,meli,1,ubicacion,responsable,now,now))
            mysql.connection.commit() 
            piesas= int(retiros[0][7])+1
            idretiro =int(retiros[0][0])
            if  piesas < int(retiros[0][4]):
              status='En Proceso'
              cur = mysql.connection.cursor()
              cur.execute("""
              UPDATE solicitud_retiros 
              SET cantidad_susrtida = %s, 
              status = %s, 
              ubicacion = %s 
              WHERE id_tarea_retiros = %s""",
              (piesas,status,ubicacion,idretiro))
              mysql.connection.commit()
              session['ubicacionretiro']=ubicacion
              return render_template('actualizacion/finalizado.html',Datos = session)
            elif  piesas == int(retiros[0][4]):
              status='Cerrado'
              cur = mysql.connection.cursor()
              cur.execute("""
              UPDATE solicitud_retiros 
              SET cantidad_susrtida = %s, 
              status = %s, 
              ubicacion = %s 
              WHERE id_tarea_retiros = %s """,
              (piesas,status,ubicacion,idretiro))
              mysql.connection.commit()
              session['ubicacionretiro']=ubicacion
              return render_template('actualizacion/finalizado.html',Datos = session)
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM solicitud_donacion WHERE SKU = \'{}\' AND status != \'Cerrado\' LIMIT 1 '.format(meli))
        donacion = cur.fetchall()
        print(donacion)
        if len(donacion)>0:
          if int(donacion[0][3]) > int(donacion[0][7]): 
            numeroOla=donacion[0][1]
            ubicacion =  'D-'+meli+'-'+str(donacion[0][11])
            now= datetime.now()
            responsable=session['FullName']
            cur = mysql.connection.cursor()
            cur.execute('INSERT INTO donacion (nuemro_de_ola, SKU, cantidad, ubicacion, responsable, fecha, fecha_hora) VALUES (%s,%s,%s,%s,%s,%s,%s)',(numeroOla,meli,1,ubicacion,responsable,now,now))
            mysql.connection.commit() 
            piesas= int(donacion[0][7])+1
            iddonacion =int(donacion[0][0])
            if  piesas < int(donacion[0][3]):
              status='En Proceso'
              cur = mysql.connection.cursor()
              cur.execute("""
              UPDATE solicitud_donacion 
              SET cantidad_susrtida = %s, 
              status = %s, 
              ubicacion = %s 
              WHERE id_donacion = %s""",
              (piesas,status,ubicacion,iddonacion))
              mysql.connection.commit()
              session['ubicacionretiro']=ubicacion
              return render_template('actualizacion/finalizado.html',Datos = session)
            elif  piesas == int(retiros[0][4]):
              status='Cerrado'
              cur = mysql.connection.cursor()
              cur.execute("""
              UPDATE solicitud_donacion 
              SET cantidad_susrtida = %s, 
              status = %s, 
              ubicacion  = %s 
              WHERE id_donacion = %s """,
              (piesas,status,ubicacion,iddonacion))
              mysql.connection.commit()
              session['ubicacionretiro']=ubicacion
              return render_template('actualizacion/finalizado.html',Datos = session)
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM ingram WHERE SKU = \'{}\' AND estatus != \'Cerrado\' LIMIT 1 '.format(meli))
        ingram = cur.fetchall()
        if len(ingram)>0:
          if int(ingram[0][3]) > int(ingram[0][5]): 
            numeroOla=ingram[0][1]
            ubicacion =  'I-'+meli+'-'+str(ingram[0][9])
            now= datetime.now() 
            responsable=session['FullName']
            cur = mysql.connection.cursor()
            cur.execute('INSERT INTO retirio_ingram (nuemro_de_ola, SKU, cantidad, ubicacion, responsable, fecha, fecha_hora) VALUES (%s,%s,%s,%s,%s,%s,%s)',(numeroOla,meli,1,ubicacion,responsable,now,now))
            mysql.connection.commit() 
            piesas= int(ingram[0][5])+1
            idingram =int(ingram[0][0])
            if  piesas < int(ingram[0][3]):
              status='En Proceso'
              cur = mysql.connection.cursor()
              cur.execute("""
              UPDATE ingram 
              SET piezas_surtidas = %s, 
              estatus = %s, 
              ubicacion = %s 
              WHERE id_solicitud  = %s""",
              (piesas,status,ubicacion,idingram))
              mysql.connection.commit()
              session['ubicacionretiro']=ubicacion
              return render_template('actualizacion/finalizado.html',Datos = session)
            elif  piesas == int(ingram[0][4]):
              status='Cerrado'
              cur = mysql.connection.cursor()
              cur.execute("""
              UPDATE ingram 
              SET piezas_surtidas = %s, 
              estatus = %s, 
              ubicacion = %s 
              WHERE id_solicitud  = %s """,
              (piesas,status,ubicacion,idingram))
              mysql.connection.commit()
              session['ubicacionretiro']=ubicacion
              return render_template('actualizacion/finalizado.html',Datos = session)
        else:
          flash("No hay Tareas Pendientes")
          return render_template('form/retiros.html',Datos = session)
      else:
        flash("No has enviado un registro")
        return render_template('form/retiros.html',Datos = session)
  except:
    flash("Llena todos los Campos Correctamente")
    return render_template('form/retiros.html',Datos = session)

#Cerrar Session
@app.route('/logout')
def Cerrar_session():
  session.clear()
  return render_template('index.html')
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
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM retiros WHERE {} LIKE \'%{}%\' AND fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['filtro_recibo'],session['valor_recibo'],session['datefilter_recibo'],row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
              else:
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM retiros WHERE {} LIKE \'%{}%\'  LIMIT {}, {}'.format(session['filtro_recibo'],session['valor_recibo'],row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
            else:
              session.pop('datefilter_recibo')
              cur = mysql.connection.cursor()
              cur.execute('SELECT * FROM retiros WHERE {} LIKE \'%{}%\'  LIMIT {}, {}'.format(session['filtro_recibo'],session['valor_recibo'],row1,row2))
              data = cur.fetchall()
              return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
          else:
            if 'datefilter' in request.form:
              if len(request.form['datefilter'])>0:
                if 'valor_recibo' in session:
                  if len(session['valor_recibo'])>0:
                    daterangef=request.form['datefilter']
                    daterange=daterangef.replace("-", "' AND '")
                    session['datefilter_recibo']=daterange
                    cur = mysql.connection.cursor()
                    cur.execute('SELECT * FROM retiros WHERE {} LIKE \'%{}%\' AND fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['filtro_recibo'],session['valor_recibo'],session['datefilter_recibo'],row1,row2))
                    data = cur.fetchall()
                    return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
                  else:
                    session.pop('filtro_recibo')
                    session.pop('valor_recibo')
                    cur = mysql.connection.cursor()
                    cur.execute('SELECT * FROM retiros WHERE fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter_recibo'],row1,row2))
                    data = cur.fetchall()
                    return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
                else:
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM retiros WHERE fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter_recibo'],row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
              else:
                if 'valor_recibo' in session:
                  session.pop('filtro_recibo')
                  session.pop('valor_recibo')
                  if 'datefilter_recibo' in session:
                    session.pop('datefilter_recibo')
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM retiros  LIMIT {}, {}'.format(row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
                else:
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM retiros  LIMIT {}, {}'.format(row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
            else:
              if 'valor_recibo' in session:
                if 'datefilter_recibo' in session:
                    session.pop('datefilter_recibo')
                session.pop('filtro_recibo')
                session.pop('valor_recibo')
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM retiros  LIMIT {}, {}'.format(row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
              else:
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM retiros  LIMIT {}, {}'.format(row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_retiros.html',Datos = session,Infos =data)

        else:
          if 'valor_recibo' in session:
            if len(session['valor_recibo'])>0:
              if 'datefilter_recibo' in session:
                if len(session['datefilter_recibo'])>0:
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM retiros WHERE {} LIKE \'%{}%\' AND fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['filtro_recibo'],session['valor_recibo'],session['datefilter_recibo'],row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
                else:
                  session.pop('datefilter_recibo')
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM retiros WHERE {} LIKE \'%{}%\'  LIMIT {}, {}'.format(session['filtro_recibo'],session['valor_recibo'],row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
              else:
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM retiros WHERE {} LIKE \'%{}%\'  LIMIT {}, {}'.format(session['filtro_recibo'],session['valor_recibo'],row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_retiros.html',Datos = session,Infos =data) 
            else:
              session.pop('filtro_recibo')
              session.pop('valor_recibo')
              if 'datefilter_recibo' in session:
                if len(session['datefilter_recibo'])>0:
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM retiros WHERE fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter_recibo'],row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
                else:
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM retiros LIMIT {}, {}'.format(row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
              else:
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM retiros  LIMIT {}, {}'.format(row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
          else:
            if 'datefilter_recibo' in session:
              if len(session['datefilter_recibo'])>0:
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM retiros WHERE fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter_recibo'],row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
              else:
                session.pop('datefilter_recibo')
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM retiros LIMIT {}, {}'.format(row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
            else:
              if 'datefilter' in request.form:
                if len(request.form['datefilter'])>0:
                  daterangef=request.form['datefilter']
                  daterange=daterangef.replace("-", "' AND '")
                  session['datefilter_recibo']=daterange
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM retiros WHERE  fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter_recibo'],row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
                else:
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM retiros LIMIT {}, {}'.format(row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_retiros.html',Datos = session,Infos =data) 
              else:
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM retiros LIMIT {}, {}'.format(row1,row2))
                data = cur.fetchall()
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
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM retiros WHERE {} LIKE \'%{}%\' AND fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['filtro_recibo'],session['valor_recibo'],session['datefilter_recibo'],row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
              else:
                session.pop('datefilter_recibo')
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM retiros WHERE {} LIKE \'%{}%\'  LIMIT {}, {}'.format(session['filtro_recibo'],session['valor_recibo'],row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
            else:
              cur = mysql.connection.cursor()
              cur.execute('SELECT * FROM retiros WHERE {} LIKE \'%{}%\'  LIMIT {}, {}'.format(session['filtro_recibo'],session['valor_recibo'],row1,row2))
              data = cur.fetchall()
              return render_template('reportes/t_retiros.html',Datos = session,Infos =data) 
          else:
            session.pop('filtro_recibo')
            session.pop('valor_recibo')
            if 'datefilter_recibo' in session:
              if len(session['datefilter_recibo'])>0:
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM retiros WHERE fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter_recibo'],row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
              else:
                session.pop('datefilter_recibo')
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM retiros LIMIT {}, {}'.format(row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
            else:
              cur = mysql.connection.cursor()
              cur.execute('SELECT * FROM retiros  LIMIT {}, {}'.format(row1,row2))
              data = cur.fetchall()
              return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
        else:
          if 'datefilter_recibo' in session:
            if len(session['datefilter_recibo'])>0:
              cur = mysql.connection.cursor()
              cur.execute('SELECT * FROM retiros WHERE fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter_recibo'],row1,row2))
              data = cur.fetchall()
              return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
            else:
              session.pop('datefilter_recibo')
              cur = mysql.connection.cursor()
              cur.execute('SELECT * FROM retiros LIMIT {}, {}'.format(row1,row2))
              data = cur.fetchall()
              return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
          else:
            cur = mysql.connection.cursor()
            cur.execute('SELECT * FROM retiros  LIMIT {}, {}'.format(row1,row2))
            data = cur.fetchall()
            return render_template('reportes/t_retiros.html',Datos = session,Infos =data)         
  except:
    flash("Inicia Secion")
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
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM donacion WHERE {} LIKE \'%{}%\' AND fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['filtro_donacion'],session['valor_donacion'],session['datefilter_donacion'],row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_donacion.html',Datos = session,Infos =data)
              else:
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM donacion WHERE {} LIKE \'%{}%\'  LIMIT {}, {}'.format(session['filtro_donacion'],session['valor_donacion'],row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_donacion.html',Datos = session,Infos =data)
            else:
              session.pop('datefilter')
              cur = mysql.connection.cursor()
              cur.execute('SELECT * FROM donacion WHERE {} LIKE \'%{}%\'  LIMIT {}, {}'.format(session['filtro_donacion'],session['valor_donacion'],row1,row2))
              data = cur.fetchall()
              return render_template('reportes/t_donacion.html',Datos = session,Infos =data)
          else:
            if 'datefilter' in request.form:
              if len(request.form['datefilter'])>0:
                if 'valor_donacion' in session:
                  if len(session['valor_donacion'])>0:
                    daterangef=request.form['datefilter']
                    daterange=daterangef.replace("-", "' AND '")
                    session['datefilter_donacion']=daterange
                    cur = mysql.connection.cursor()
                    cur.execute('SELECT * FROM donacion WHERE {} LIKE \'%{}%\' AND fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['filtro_donacion'],session['valor_donacion'],session['datefilter_donacion'],row1,row2))
                    data = cur.fetchall()
                    return render_template('reportes/t_donacion.html',Datos = session,Infos =data)
                  else:
                    session.pop('filtro_donacion')
                    session.pop('valor_donacion')
                    cur = mysql.connection.cursor()
                    cur.execute('SELECT * FROM donacion WHERE fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter_donacion'],row1,row2))
                    data = cur.fetchall()
                    return render_template('reportes/t_donacion.html',Datos = session,Infos =data)
                else:
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM donacion WHERE fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter_donacion'],row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_donacion.html',Datos = session,Infos =data)
              else:
                if 'valor_donacion' in session:
                  session.pop('filtro_donacion')
                  session.pop('valor_donacion')
                  if 'datefilter_donacion' in session:
                    session.pop('datefilter_donacion')
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM donacion  LIMIT {}, {}'.format(row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_donacion.html',Datos = session,Infos =data)
                else:
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM donacion  LIMIT {}, {}'.format(row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_donacion.html',Datos = session,Infos =data)
            else:
              if 'valor_donacion' in session:
                if 'datefilter_donacion' in session:
                    session.pop('datefilter_donacion')
                session.pop('filtro_donacion')
                session.pop('valor_donacion')
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM donacion  LIMIT {}, {}'.format(row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_donacion.html',Datos = session,Infos =data)
              else:
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM donacion  LIMIT {}, {}'.format(row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_donacion.html',Datos = session,Infos =data)

        else:
          if 'valor_donacion' in session:
            if len(session['valor_donacion'])>0:
              if 'datefilter_donacion' in session:
                if len(session['datefilter_donacion'])>0:
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM donacion WHERE {} LIKE \'%{}%\' AND fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['filtro_donacion'],session['valor_donacion'],session['datefilter_donacion'],row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_donacion.html',Datos = session,Infos =data)
                else:
                  session.pop('datefilter_donacion')
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM donacion WHERE {} LIKE \'%{}%\'  LIMIT {}, {}'.format(session['filtro_donacion'],session['valor_donacion'],row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_donacion.html',Datos = session,Infos =data)
              else:
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM donacion WHERE {} LIKE \'%{}%\'  LIMIT {}, {}'.format(session['filtro_donacion'],session['valor_donacion'],row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_donacion.html',Datos = session,Infos =data) 
            else:
              session.pop('filtro_donacion')
              session.pop('valor_donacion')
              if 'datefilter_donacion' in session:
                if len(session['datefilter_donacion'])>0:
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM donacion WHERE fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter_donacion'],row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_donacion.html',Datos = session,Infos =data)
                else:
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM donacion LIMIT {}, {}'.format(row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_donacion.html',Datos = session,Infos =data)
              else:
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM donacion  LIMIT {}, {}'.format(row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_donacion.html',Datos = session,Infos =data)
          else:
            if 'datefilter_donacion' in session:
              if len(session['datefilter_donacion'])>0:
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM donacion WHERE fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter_donacion'],row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_donacion.html',Datos = session,Infos =data)
              else:
                session.pop('datefilter_donacion')
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM donacion LIMIT {}, {}'.format(row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_donacion.html',Datos = session,Infos =data)
            else:
              if 'datefilter' in request.form:
                if len(request.form['datefilter'])>0:
                  daterangef=request.form['datefilter']
                  daterange=daterangef.replace("-", "' AND '")
                  session['datefilter_donacion']=daterange
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM donacion WHERE  fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter_donacion'],row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_donacion.html',Datos = session,Infos =data)
                else:
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM donacion LIMIT {}, {}'.format(row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_donacion.html',Datos = session,Infos =data) 
              else:
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM donacion LIMIT {}, {}'.format(row1,row2))
                data = cur.fetchall()
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
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM donacion WHERE {} LIKE \'%{}%\' AND fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['filtro_donacion'],session['valor_donacion'],session['datefilter_donacion'],row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_donacion.html',Datos = session,Infos =data)
              else:
                session.pop('datefilter_donacion')
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM donacion WHERE {} LIKE \'%{}%\'  LIMIT {}, {}'.format(session['filtro_donacion'],session['valor_donacion'],row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_donacion.html',Datos = session,Infos =data)
            else:
              cur = mysql.connection.cursor()
              cur.execute('SELECT * FROM donacion WHERE {} LIKE \'%{}%\'  LIMIT {}, {}'.format(session['filtro_donacion'],session['valor_donacion'],row1,row2))
              data = cur.fetchall()
              return render_template('reportes/t_donacion.html',Datos = session,Infos =data) 
          else:
            session.pop('filtro_donacion')
            session.pop('valor_donacion')
            if 'datefilter_donacion' in session:
              if len(session['datefilter_donacion'])>0:
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM donacion WHERE fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter_donacion'],row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_donacion.html',Datos = session,Infos =data)
              else:
                session.pop('datefilter_donacion')
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM donacion LIMIT {}, {}'.format(row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_donacion.html',Datos = session,Infos =data)
            else:
              cur = mysql.connection.cursor()
              cur.execute('SELECT * FROM donacion  LIMIT {}, {}'.format(row1,row2))
              data = cur.fetchall()
              return render_template('reportes/t_donacion.html',Datos = session,Infos =data)
        else:
          if 'datefilter_donacion' in session:
            if len(session['datefilter_recibo'])>0:
              cur = mysql.connection.cursor()
              cur.execute('SELECT * FROM donacion WHERE fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter_donacion'],row1,row2))
              data = cur.fetchall()
              return render_template('reportes/t_donacion.html',Datos = session,Infos =data)
            else:
              session.pop('datefilter_donacion')
              cur = mysql.connection.cursor()
              cur.execute('SELECT * FROM donacion LIMIT {}, {}'.format(row1,row2))
              data = cur.fetchall()
              return render_template('reportes/t_donacion.html',Datos = session,Infos =data)
          else:
            cur = mysql.connection.cursor()
            cur.execute('SELECT * FROM donacion  LIMIT {}, {}'.format(row1,row2))
            data = cur.fetchall()
            return render_template('reportes/t_donacion.html',Datos = session,Infos =data)         
  except:
    flash("Inicia Secion")
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
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM retirio_ingram WHERE {} LIKE \'%{}%\' AND fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['filtro_ingram'],session['valor_ingram'],session['datefilter_ingram'],row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_ingram.html',Datos = session,Infos =data)
              else:
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM retirio_ingram WHERE {} LIKE \'%{}%\'  LIMIT {}, {}'.format(session['filtro_ingram'],session['valor_ingram'],row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_ingram.html',Datos = session,Infos =data)
            else:
              session.pop('datefilter_ingram')
              cur = mysql.connection.cursor()
              cur.execute('SELECT * FROM retirio_ingram WHERE {} LIKE \'%{}%\'  LIMIT {}, {}'.format(session['filtro_ingram'],session['valor_ingram'],row1,row2))
              data = cur.fetchall()
              return render_template('reportes/t_ingram.html',Datos = session,Infos =data)
          else:
            if 'datefilter' in request.form:
              if len(request.form['datefilter'])>0:
                if 'valor_ingram' in session:
                  if len(session['valor_ingram'])>0:
                    daterangef=request.form['datefilter']
                    daterange=daterangef.replace("-", "' AND '")
                    session['datefilter_ingram']=daterange
                    cur = mysql.connection.cursor()
                    cur.execute('SELECT * FROM retirio_ingram WHERE {} LIKE \'%{}%\' AND fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['filtro_ingram'],session['valor_ingram'],session['datefilter_ingram'],row1,row2))
                    data = cur.fetchall()
                    return render_template('reportes/t_ingram.html',Datos = session,Infos =data)
                  else:
                    session.pop('filtro_ingram')
                    session.pop('valor_ingram')
                    cur = mysql.connection.cursor()
                    cur.execute('SELECT * FROM retirio_ingram WHERE fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter_ingram'],row1,row2))
                    data = cur.fetchall()
                    return render_template('reportes/t_ingram.html',Datos = session,Infos =data)
                else:
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM retirio_ingram WHERE fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter_ingram'],row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_ingram.html',Datos = session,Infos =data)
              else:
                if 'valor_ingram' in session:
                  session.pop('filtro_ingram')
                  session.pop('valor_ingram')
                  if 'datefilter_ingram' in session:
                    session.pop('datefilter_ingram')
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM retirio_ingram  LIMIT {}, {}'.format(row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_ingram.html',Datos = session,Infos =data)
                else:
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM retirio_ingram  LIMIT {}, {}'.format(row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_ingram.html',Datos = session,Infos =data)
            else:
              if 'valor_ingram' in session:
                if 'datefilter_ingram' in session:
                    session.pop('datefilter_ingram')
                session.pop('filtro_ingram')
                session.pop('valor_ingram')
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM retirio_ingram  LIMIT {}, {}'.format(row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_ingram.html',Datos = session,Infos =data)
              else:
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM retirio_ingram  LIMIT {}, {}'.format(row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_ingram.html',Datos = session,Infos =data)

        else:
          if 'valor_ingram' in session:
            if len(session['valor_ingram'])>0:
              if 'datefilter_ingram' in session:
                if len(session['datefilter_ingram'])>0:
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM retirio_ingram WHERE {} LIKE \'%{}%\' AND fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['filtro_ingram'],session['valor_ingram'],session['datefilter_ingram'],row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_ingram.html',Datos = session,Infos =data)
                else:
                  session.pop('datefilter_ingram')
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM retirio_ingram WHERE {} LIKE \'%{}%\'  LIMIT {}, {}'.format(session['filtro_ingram'],session['valor_ingram'],row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_ingram.html',Datos = session,Infos =data)
              else:
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM retirio_ingram WHERE {} LIKE \'%{}%\'  LIMIT {}, {}'.format(session['filtro_ingram'],session['valor_ingram'],row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_ingram.html',Datos = session,Infos =data) 
            else:
              session.pop('filtro_ingram')
              session.pop('valor_ingram')
              if 'datefilter_ingram' in session:
                if len(session['datefilter_ingram'])>0:
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM retirio_ingram WHERE fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter_ingram'],row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_ingram.html',Datos = session,Infos =data)
                else:
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM retirio_ingram LIMIT {}, {}'.format(row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_ingram.html',Datos = session,Infos =data)
              else:
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM retirio_ingram  LIMIT {}, {}'.format(row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_ingram.html',Datos = session,Infos =data)
          else:
            if 'datefilter_ingram' in session:
              if len(session['datefilter_ingram'])>0:
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM retirio_ingram WHERE fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter_ingram'],row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_ingram.html',Datos = session,Infos =data)
              else:
                session.pop('datefilter_ingram')
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM retirio_ingram LIMIT {}, {}'.format(row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_ingram.html',Datos = session,Infos =data)
            else:
              if 'datefilter' in request.form:
                if len(request.form['datefilter'])>0:
                  daterangef=request.form['datefilter']
                  daterange=daterangef.replace("-", "' AND '")
                  session['datefilter_ingram']=daterange
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM retirio_ingram WHERE  fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter_ingram'],row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_ingram.html',Datos = session,Infos =data)
                else:
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM retirio_ingram LIMIT {}, {}'.format(row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_ingram.html',Datos = session,Infos =data) 
              else:
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM retirio_ingram LIMIT {}, {}'.format(row1,row2))
                data = cur.fetchall()
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
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM retirio_ingram WHERE {} LIKE \'%{}%\' AND fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['filtro_ingram'],session['valor_ingram'],session['datefilter_ingram'],row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_ingram.html',Datos = session,Infos =data)
              else:
                session.pop('datefilter_ingram')
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM retirio_ingram WHERE {} LIKE \'%{}%\'  LIMIT {}, {}'.format(session['filtro_ingram'],session['valor_ingram'],row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_ingram.html',Datos = session,Infos =data)
            else:
              cur = mysql.connection.cursor()
              cur.execute('SELECT * FROM retirio_ingram WHERE {} LIKE \'%{}%\'  LIMIT {}, {}'.format(session['filtro_ingram'],session['valor_ingram'],row1,row2))
              data = cur.fetchall()
              return render_template('reportes/t_ingram.html',Datos = session,Infos =data) 
          else:
            session.pop('filtro_ingram')
            session.pop('valor_ingram')
            if 'datefilter_ingram' in session:
              if len(session['datefilter_ingram'])>0:
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM retirio_ingram WHERE fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter_ingram'],row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_ingram.html',Datos = session,Infos =data)
              else:
                session.pop('datefilter_ingram')
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM retirio_ingram LIMIT {}, {}'.format(row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_ingram.html',Datos = session,Infos =data)
            else:
              cur = mysql.connection.cursor()
              cur.execute('SELECT * FROM retirio_ingram  LIMIT {}, {}'.format(row1,row2))
              data = cur.fetchall()
              return render_template('reportes/t_ingram.html',Datos = session,Infos =data)
        else:
          if 'datefilter_ingram' in session:
            if len(session['datefilter_ingram'])>0:
              cur = mysql.connection.cursor()
              cur.execute('SELECT * FROM retirio_ingram WHERE fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter_ingram'],row1,row2))
              data = cur.fetchall()
              return render_template('reportes/t_ingram.html',Datos = session,Infos =data)
            else:
              session.pop('datefilter_ingram')
              cur = mysql.connection.cursor()
              cur.execute('SELECT * FROM retirio_ingram LIMIT {}, {}'.format(row1,row2))
              data = cur.fetchall()
              return render_template('reportes/t_ingram.html',Datos = session,Infos =data)
          else:
            cur = mysql.connection.cursor()
            cur.execute('SELECT * FROM retirio_ingram  LIMIT {}, {}'.format(row1,row2))
            data = cur.fetchall()
            return render_template('reportes/t_ingram.html',Datos = session,Infos =data)         
  except:
    flash("Inicia Secion")
    return render_template('index.html')

@app.route('/csvretiros',methods=['POST','GET'])
def crear_csvretiros():
    site=session['SiteName']
    row1 = int(session['rowi_recibo'])
    row2 =50
    if 'valor_recibo' in session:
      if len(session['valor_recibo'])>0:
        if 'datefilter_recibo' in session:
          if len(session['datefilter_recibo'])>0:
            cur = mysql.connection.cursor()
            cur.execute('SELECT * FROM retiros WHERE {} LIKE \'%{}%\' AND fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['filtro_recibo'],session['valor_recibo'],session['datefilter_recibo'],row1,row2))
            data = cur.fetchall()
          else:
            cur = mysql.connection.cursor()
            cur.execute('SELECT * FROM retiros WHERE {} LIKE \'%{}%\'  LIMIT {}, {}'.format(session['filtro_recibo'],session['valor_recibo'],row1,row2))
            data = cur.fetchall()
        else:
          cur = mysql.connection.cursor()
          cur.execute('SELECT * FROM retiros WHERE {} LIKE \'%{}%\'  LIMIT {}, {}'.format(session['filtro_recibo'],session['valor_recibo'],row1,row2))
          data = cur.fetchall()
      else:
        if 'datefilter_recibo' in session:
          if len(session['datefilter_recibo'])>0:
            cur = mysql.connection.cursor()
            cur.execute('SELECT * FROM retiros WHERE fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter_recibo'],row1,row2))
            data = cur.fetchall()
          else:
            cur = mysql.connection.cursor()
            cur.execute('SELECT * FROM retiros LIMIT {}, {}'.format(row1,row2))
            data = cur.fetchall()
        else:
          cur = mysql.connection.cursor()
          cur.execute('SELECT * FROM retiros  LIMIT {}, {}'.format(row1,row2))
          data = cur.fetchall()
    else:
      if 'datefilter_recibo' in session:
        if len(session['datefilter_recibo'])>0:
          cur = mysql.connection.cursor()
          cur.execute('SELECT * FROM retiros WHERE fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter_recibo'],row1,row2))
          data = cur.fetchall()
        else:
          cur = mysql.connection.cursor()
          cur.execute('SELECT * FROM retiros LIMIT {}, {}'.format(row1,row2))
      else:
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM retiros  LIMIT {}, {}'.format(row1,row2))
        data = cur.fetchall()
    datos="Id"+","+"Ola"+","+"Meli"+","+"Cantidad"+","+"Ubicacion"+","+"Responsable"+","+"Fecha"+","+"Fecha y Hora"+"\n"
    for res in data:
      datos+=str(res[0])
      datos+=","+str(res[1])
      datos+=","+str(res[2])
      datos+=","+str(res[3])
      datos+=","+str(res[4])
      datos+=","+str(res[5])
      datos+=","+str(res[6])
      datos+=","+str(res[7])
      datos+="\n"

    response = make_response(datos)
    response.headers["Content-Disposition"] = "attachment; filename="+"Reportre_Recibo-"+str(datetime.today())+".csv"; 
    return response

@app.route('/csvdonacion',methods=['POST','GET'])
def crear_csvdonacion():
    site=session['SiteName']
    row1 = int(session['rowi_donacion'])
    row2 =50
    if 'valor_donacion' in session:
      if len(session['valor_donacion'])>0:
        if 'datefilter_donacion' in session:
          if len(session['datefilter_donacion'])>0:
            cur = mysql.connection.cursor()
            cur.execute('SELECT * FROM donacion WHERE {} LIKE \'%{}%\' AND fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['filtro_donacion'],session['valor_donacion'],session['datefilter_donacion'],row1,row2))
            data = cur.fetchall()
          else:
            cur = mysql.connection.cursor()
            cur.execute('SELECT * FROM donacion WHERE {} LIKE \'%{}%\'  LIMIT {}, {}'.format(session['filtro_donacion'],session['valor_donacion'],row1,row2))
            data = cur.fetchall()
        else:
          cur = mysql.connection.cursor()
          cur.execute('SELECT * FROM donacion WHERE {} LIKE \'%{}%\'  LIMIT {}, {}'.format(session['filtro_donacion'],session['valor_donacion'],row1,row2))
          data = cur.fetchall()
      else:
        if 'datefilter_donacion' in session:
          if len(session['datefilter_donacion'])>0:
            cur = mysql.connection.cursor()
            cur.execute('SELECT * FROM donacion WHERE fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter_donacion'],row1,row2))
            data = cur.fetchall()
          else:
            cur = mysql.connection.cursor()
            cur.execute('SELECT * FROM donacion LIMIT {}, {}'.format(row1,row2))
            data = cur.fetchall()
        else:
          cur = mysql.connection.cursor()
          cur.execute('SELECT * FROM donacion  LIMIT {}, {}'.format(row1,row2))
          data = cur.fetchall()
    else:
      if 'datefilter_donacion' in session:
        if len(session['datefilter_donacion'])>0:
          cur = mysql.connection.cursor()
          cur.execute('SELECT * FROM donacion WHERE fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter_donacion'],row1,row2))
          data = cur.fetchall()
        else:
          cur = mysql.connection.cursor()
          cur.execute('SELECT * FROM donacion LIMIT {}, {}'.format(row1,row2))
      else:
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM donacion  LIMIT {}, {}'.format(row1,row2))
        data = cur.fetchall()
    datos="Id"+","+"Ola"+","+"SKU"+","+"Cantidad"+","+"Ubicacion"+","+"Responsable"+","+"Fecha"+","+"Fecha y Hora"+","+"\n"
    for res in data:
      datos+=str(res[0])
      datos+=","+str(res[1])
      datos+=","+str(res[2])
      datos+=","+str(res[3])
      datos+=","+str(res[4])
      datos+=","+str(res[5])
      datos+=","+str(res[6])
      datos+=","+str(res[7])
      datos+="\n"

    response = make_response(datos)
    response.headers["Content-Disposition"] = "attachment; filename="+"Donacion-"+str(datetime.today())+".csv"; 
    return response

@app.route('/csvingram',methods=['POST','GET'])
def crear_ccsvingram():
    site=session['SiteName']
    row1 = int(session['rowi_ingram'])
    row2 =50
    if 'valor_ingram' in session:
      if len(session['valor_ingram'])>0:
        if 'datefilter_ingram' in session:
          if len(session['datefilter'])>0:
            cur = mysql.connection.cursor()
            cur.execute('SELECT * FROM retirio_ingram WHERE {} LIKE \'%{}%\' AND fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['filtro_ingram'],session['valor_ingram'],session['datefilter_ingram'],row1,row2))
            data = cur.fetchall()
          else:
            cur = mysql.connection.cursor()
            cur.execute('SELECT * FROM retirio_ingram WHERE {} LIKE \'%{}%\'  LIMIT {}, {}'.format(session['filtro_ingram'],session['valor_ingram'],row1,row2))
            data = cur.fetchall()
        else:
          cur = mysql.connection.cursor()
          cur.execute('SELECT * FROM retirio_ingram WHERE {} LIKE \'%{}%\'  LIMIT {}, {}'.format(session['filtro_ingram'],session['valor_ingram'],row1,row2))
          data = cur.fetchall()
      else:
        if 'datefilter_ingram' in session:
          if len(session['datefilter_ingram'])>0:
            cur = mysql.connection.cursor()
            cur.execute('SELECT * FROM retirio_ingram WHERE fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter_ingram'],row1,row2))
            data = cur.fetchall()
          else:
            cur = mysql.connection.cursor()
            cur.execute('SELECT * FROM retirio_ingram LIMIT {}, {}'.format(row1,row2))
            data = cur.fetchall()
        else:
          cur = mysql.connection.cursor()
          cur.execute('SELECT * FROM retirio_ingram  LIMIT {}, {}'.format(row1,row2))
          data = cur.fetchall()
    else:
      if 'datefilter_ingram' in session:
        if len(session['datefilter_ingram'])>0:
          cur = mysql.connection.cursor()
          cur.execute('SELECT * FROM retirio_ingram WHERE fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter_ingram'],row1,row2))
          data = cur.fetchall()
        else:
          cur = mysql.connection.cursor()
          cur.execute('SELECT * FROM retirio_ingram LIMIT {}, {}'.format(row1,row2))
      else:
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM retirio_ingram  LIMIT {}, {}'.format(row1,row2))
        data = cur.fetchall()
    datos="Id"+","+"Ola"+","+"SKU"+","+"Cantidad"+","+"Ubicacion"+","+"Responsable"+","+"Fecha"+","+"Fecha y Hora"+","+"\n"
    for res in data:
      datos+=str(res[0])
      datos+=","+str(res[1])
      datos+=","+str(res[2])
      datos+=","+str(res[3])
      datos+=","+str(res[4])
      datos+=","+str(res[5])
      datos+=","+str(res[6])
      datos+=","+str(res[7])
      datos+="\n"

    response = make_response(datos)
    response.headers["Content-Disposition"] = "attachment; filename="+"Ingram-"+str(datetime.today())+".csv"; 
    return response

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
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM solicitud_retiros WHERE {} LIKE \'%{}%\' AND fecha_de_entrega BETWEEN \'{}\'  LIMIT {}, {}'.format(session['filtro_solicitudrecibo'],session['valor_solicitudrecibo'],session['datefilter_solicitudrecibo'],row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data)
              else:
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM solicitud_retiros WHERE {} LIKE \'%{}%\'  LIMIT {}, {}'.format(session['filtro_solicitudrecibo'],session['valor_solicitudrecibo'],row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data)
            else:
              session.pop('datefilter_solicitudrecibo')
              cur = mysql.connection.cursor()
              cur.execute('SELECT * FROM solicitud_retiros WHERE {} LIKE \'%{}%\'  LIMIT {}, {}'.format(session['filtro_solicitudrecibo'],session['valor_solicitudrecibo'],row1,row2))
              data = cur.fetchall()
              return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data)
          else:
            if 'datefilter' in request.form:
              if len(request.form['datefilter'])>0:
                if 'valor_solicitudrecibo' in session:
                  if len(session['valor_solicitudrecibo'])>0:
                    daterangef=request.form['datefilter']
                    daterange=daterangef.replace("-", "' AND '")
                    session['datefilter_solicitudrecibo']=daterange
                    cur = mysql.connection.cursor()
                    cur.execute('SELECT * FROM solicitud_retiros WHERE {} LIKE \'%{}%\' AND fecha_de_entrega BETWEEN \'{}\'  LIMIT {}, {}'.format(session['filtro_solicitudrecibo'],session['valor_solicitudrecibo'],session['datefilter_solicitudrecibo'],row1,row2))
                    data = cur.fetchall()
                    return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data)
                  else:
                    session.pop('filtro_solicitudrecibo')
                    session.pop('valor_solicitudrecibo')
                    cur = mysql.connection.cursor()
                    cur.execute('SELECT * FROM solicitud_retiros WHERE fecha_de_entrega BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter_solicitudrecibo'],row1,row2))
                    data = cur.fetchall()
                    return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data)
                else:
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM solicitud_retiros WHERE fecha_de_entrega BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter_solicitudrecibo'],row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data)
              else:
                if 'valor_solicitudrecibo' in session:
                  session.pop('filtro_solicitudrecibo')
                  session.pop('valor_solicitudrecibo')
                  if 'datefilter_solicitudrecibo' in session:
                    session.pop('datefilter_solicitudrecibo')
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM solicitud_retiros  LIMIT {}, {}'.format(row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_retiros.html',Datos = session,Infos =data)
                else:
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM solicitud_retiros  LIMIT {}, {}'.format(row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data)
            else:
              if 'valor_solicitudrecibo' in session:
                if 'datefilter_solicitudrecibo' in session:
                    session.pop('datefilter_solicitudrecibo')
                session.pop('filtro_solicitudrecibo')
                session.pop('valor_solicitudrecibo')
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM solicitud_retiros  LIMIT {}, {}'.format(row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data)
              else:
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM solicitud_retiros  LIMIT {}, {}'.format(row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data)

        else:
          if 'valor_solicitudrecibo' in session:
            if len(session['valor_solicitudrecibo'])>0:
              if 'datefilter_solicitudrecibo' in session:
                if len(session['datefilter_solicitudrecibo'])>0:
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM solicitud_retiros WHERE {} LIKE \'%{}%\' AND fecha_de_entrega BETWEEN \'{}\'  LIMIT {}, {}'.format(session['filtro_solicitudrecibo'],session['valor_solicitudrecibo'],session['datefilter_solicitudrecibo'],row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data)
                else:
                  session.pop('datefilter_solicitudrecibo')
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM solicitud_retiros WHERE {} LIKE \'%{}%\'  LIMIT {}, {}'.format(session['filtro_solicitudrecibo'],session['valor_solicitudrecibo'],row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data)
              else:
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM solicitud_retiros WHERE {} LIKE \'%{}%\'  LIMIT {}, {}'.format(session['filtro_solicitudrecibo'],session['valor_solicitudrecibo'],row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data) 
            else:
              session.pop('filtro_solicitudrecibo')
              session.pop('valor_solicitudrecibo')
              if 'datefilter_solicitudrecibo' in session:
                if len(session['datefilter_solicitudrecibo'])>0:
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM solicitud_retiros WHERE fecha_de_entrega BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter_solicitudrecibo'],row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data)
                else:
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM solicitud_retiros LIMIT {}, {}'.format(row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data)
              else:
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM solicitud_retiros  LIMIT {}, {}'.format(row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data)
          else:
            if 'datefilter_solicitudrecibo' in session:
              if len(session['datefilter_solicitudrecibo'])>0:
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM solicitud_retiros WHERE fecha_de_entrega BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter_solicitudrecibo'],row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data)
              else:
                session.pop('datefilter_solicitudrecibo')
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM solicitud_retiros LIMIT {}, {}'.format(row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data)
            else:
              if 'datefilter' in request.form:
                if len(request.form['datefilter'])>0:
                  daterangef=request.form['datefilter']
                  daterange=daterangef.replace("-", "' AND '")
                  session['datefilter_solicitudrecibo']=daterange
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM solicitud_retiros WHERE  fecha_de_entrega BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter_solicitudrecibo'],row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data)
                else:
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM solicitud_retiros LIMIT {}, {}'.format(row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data) 
              else:
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM solicitud_retiros LIMIT {}, {}'.format(row1,row2))
                data = cur.fetchall()
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
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM solicitud_retiros WHERE {} LIKE \'%{}%\' AND fecha_de_entrega BETWEEN \'{}\'  LIMIT {}, {}'.format(session['filtro_solicitudrecibo'],session['valor_solicitudrecibo'],session['datefilter_solicitudrecibo'],row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data)
              else:
                session.pop('datefilter_solicitudrecibo')
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM solicitud_retiros WHERE {} LIKE \'%{}%\'  LIMIT {}, {}'.format(session['filtro_solicitudrecibo'],session['valor_solicitudrecibo'],row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data)
            else:
              cur = mysql.connection.cursor()
              cur.execute('SELECT * FROM solicitud_retiros WHERE {} LIKE \'%{}%\'  LIMIT {}, {}'.format(session['filtro_solicitudrecibo'],session['valor_solicitudrecibo'],row1,row2))
              data = cur.fetchall()
              return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data) 
          else:
            session.pop('filtro_solicitudrecibo')
            session.pop('valor_solicitudrecibo')
            if 'datefilter_solicitudrecibo' in session:
              if len(session['datefilter_solicitudrecibo'])>0:
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM solicitud_retiros WHERE fecha_de_entrega BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter_solicitudrecibo'],row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data)
              else:
                session.pop('datefilter_solicitudrecibo')
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM solicitud_retiros LIMIT {}, {}'.format(row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data)
            else:
              cur = mysql.connection.cursor()
              cur.execute('SELECT * FROM solicitud_retiros  LIMIT {}, {}'.format(row1,row2))
              data = cur.fetchall()
              return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data)
        else:
          if 'datefilter_solicitudrecibo' in session:
            if len(session['datefilter_solicitudrecibo'])>0:
              cur = mysql.connection.cursor()
              cur.execute('SELECT * FROM solicitud_retiros WHERE fecha_de_entrega BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter_solicitudrecibo'],row1,row2))
              data = cur.fetchall()
              return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data)
            else:
              session.pop('datefilter_solicitudrecibo')
              cur = mysql.connection.cursor()
              cur.execute('SELECT * FROM solicitud_retiros LIMIT {}, {}'.format(row1,row2))
              data = cur.fetchall()
              return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data)
          else:
            cur = mysql.connection.cursor()
            cur.execute('SELECT * FROM solicitud_retiros  LIMIT {}, {}'.format(row1,row2))
            data = cur.fetchall()
            return render_template('reportes/t_solicitudretiros.html',Datos = session,Infos =data)         
  except:
    flash("Inicia Secion")
    return render_template('index.html')

@app.route('/Solicitudes_donacion/<rowi>',methods=['POST','GET'])
def solicitud_donacion(rowi):
  try:
      if request.method == 'POST':
        if request.method == 'GET':
          session['rowi_t_p']=rowi
          row1 = int(session['rowi_t_p'])
          row2 = 50
        else:
            row1 = int(session['rowi_t_p'])
            row2 =50
        if 'valor' in request.form:
          if len(request.form['valor'])>0:
            session['filtro_t_p']=request.form['filtro']
            session['valor_t_p']=request.form['valor']
            if 'datefilter' in request.form:
              if len(request.form['datefilter'])>0:
                daterangef=request.form['datefilter']
                daterange=daterangef.replace("-", "' AND '")
                session['datefilter']=daterange
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM prealert WHERE {} LIKE \'%{}%\' AND Fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['filtro_t_p'],session['valor_t_p'],session['datefilter'],row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_p.html',Datos = session,Infos =data)
              else:
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM prealert WHERE {} LIKE \'%{}%\'  LIMIT {}, {}'.format(session['filtro_t_p'],session['valor_t_p'],row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_p.html',Datos = session,Infos =data)
            else:
              session.pop('datefilter')
              cur = mysql.connection.cursor()
              cur.execute('SELECT * FROM prealert WHERE {} LIKE \'%{}%\'  LIMIT {}, {}'.format(session['filtro_t_p'],session['valor_t_p'],row1,row2))
              data = cur.fetchall()
              return render_template('reportes/t_p.html',Datos = session,Infos =data)
          else:
            if 'datefilter' in request.form:
              if len(request.form['datefilter'])>0:
                if 'valor_t_p' in session:
                  if len(session['valor_t_p'])>0:
                    daterangef=request.form['datefilter']
                    daterange=daterangef.replace("-", "' AND '")
                    session['datefilter']=daterange
                    cur = mysql.connection.cursor()
                    cur.execute('SELECT * FROM prealert WHERE {} LIKE \'%{}%\' AND Fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['filtro_t_p'],session['valor_t_p'],session['datefilter'],row1,row2))
                    data = cur.fetchall()
                    return render_template('reportes/t_p.html',Datos = session,Infos =data)
                  else:
                    session.pop('filtro_t_p')
                    session.pop('valor_t_p')
                    cur = mysql.connection.cursor()
                    cur.execute('SELECT * FROM prealert WHERE Fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter'],row1,row2))
                    data = cur.fetchall()
                    return render_template('reportes/t_p.html',Datos = session,Infos =data)
                else:
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM prealert WHERE Fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter'],row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_p.html',Datos = session,Infos =data)
              else:
                if 'valor_t_p' in session:
                  session.pop('filtro_t_p')
                  session.pop('valor_t_p')
                  if 'datefilter' in session:
                    session.pop('datefilter')
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM prealert  LIMIT {}, {}'.format(row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_p.html',Datos = session,Infos =data)
                else:
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM prealert  LIMIT {}, {}'.format(row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_p.html',Datos = session,Infos =data)
            else:
              if 'valor_t_p' in session:
                if 'datefilter' in session:
                    session.pop('datefilter')
                session.pop('filtro_t_p')
                session.pop('valor_t_p')
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM prealert  LIMIT {}, {}'.format(row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_p.html',Datos = session,Infos =data)
              else:
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM prealert  LIMIT {}, {}'.format(row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_p.html',Datos = session,Infos =data)

        else:
          if 'valor_t_p' in session:
            if len(session['valor_t_p'])>0:
              if 'datefilter' in session:
                if len(session['datefilter'])>0:
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM prealert WHERE {} LIKE \'%{}%\' AND Fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['filtro_t_p'],session['valor_t_p'],session['datefilter'],row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_p.html',Datos = session,Infos =data)
                else:
                  session.pop('datefilter')
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM prealert WHERE {} LIKE \'%{}%\'  LIMIT {}, {}'.format(session['filtro_t_p'],session['valor_t_p'],row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_p.html',Datos = session,Infos =data)
              else:
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM prealert WHERE {} LIKE \'%{}%\'  LIMIT {}, {}'.format(session['filtro_t_p'],session['valor_t_p'],row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_p.html',Datos = session,Infos =data) 
            else:
              session.pop('filtro_t_p')
              session.pop('valor_t_p')
              if 'datefilter' in session:
                if len(session['datefilter'])>0:
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM prealert WHERE Fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter'],row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_p.html',Datos = session,Infos =data)
                else:
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM prealert LIMIT {}, {}'.format(row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_p.html',Datos = session,Infos =data)
              else:
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM prealert  LIMIT {}, {}'.format(row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_p.html',Datos = session,Infos =data)
          else:
            if 'datefilter' in session:
              if len(session['datefilter'])>0:
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM prealert WHERE Fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter'],row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_p.html',Datos = session,Infos =data)
              else:
                session.pop('datefilter')
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM prealert LIMIT {}, {}'.format(row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_p.html',Datos = session,Infos =data)
            else:
              if 'datefilter' in request.form:
                if len(request.form['datefilter'])>0:
                  daterangef=request.form['datefilter']
                  daterange=daterangef.replace("-", "' AND '")
                  session['datefilter']=daterange
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM prealert WHERE  Fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter'],row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_p.html',Datos = session,Infos =data)
                else:
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM prealert LIMIT {}, {}'.format(row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_p.html',Datos = session,Infos =data) 
              else:
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM prealert LIMIT {}, {}'.format(row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_p.html',Datos = session,Infos =data) 
      else: 
        if request.method == 'GET':
          session['rowi_t_p']=rowi
          row1 = int(session['rowi_t_p'])
          row2 = 50
        else:
          row1 = int(session['rowi_t_p'])
          row2 =50
        if 'valor_t_p' in session:
          if len(session['valor_t_p'])>0:
            if 'datefilter' in session:
              if len(session['datefilter'])>0:
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM prealert WHERE {} LIKE \'%{}%\' AND Fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['filtro_t_p'],session['valor_t_p'],session['datefilter'],row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_p.html',Datos = session,Infos =data)
              else:
                session.pop('datefilter')
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM prealert WHERE {} LIKE \'%{}%\'  LIMIT {}, {}'.format(session['filtro_t_p'],session['valor_t_p'],row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_p.html',Datos = session,Infos =data)
            else:
              cur = mysql.connection.cursor()
              cur.execute('SELECT * FROM prealert WHERE {} LIKE \'%{}%\'  LIMIT {}, {}'.format(session['filtro_t_p'],session['valor_t_p'],row1,row2))
              data = cur.fetchall()
              return render_template('reportes/t_p.html',Datos = session,Infos =data) 
          else:
            session.pop('filtro_t_p')
            session.pop('valor_t_p')
            if 'datefilter' in session:
              if len(session['datefilter'])>0:
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM prealert WHERE Fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter'],row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_p.html',Datos = session,Infos =data)
              else:
                session.pop('datefilter')
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM prealert LIMIT {}, {}'.format(row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_p.html',Datos = session,Infos =data)
            else:
              cur = mysql.connection.cursor()
              cur.execute('SELECT * FROM prealert  LIMIT {}, {}'.format(row1,row2))
              data = cur.fetchall()
              return render_template('reportes/t_p.html',Datos = session,Infos =data)
        else:
          if 'datefilter' in session:
            if len(session['datefilter_recibo'])>0:
              cur = mysql.connection.cursor()
              cur.execute('SELECT * FROM prealert WHERE Fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter'],row1,row2))
              data = cur.fetchall()
              return render_template('reportes/t_p.html',Datos = session,Infos =data)
            else:
              session.pop('datefilter')
              cur = mysql.connection.cursor()
              cur.execute('SELECT * FROM prealert LIMIT {}, {}'.format(row1,row2))
              data = cur.fetchall()
              return render_template('reportes/t_p.html',Datos = session,Infos =data)
          else:
            cur = mysql.connection.cursor()
            cur.execute('SELECT * FROM prealert  LIMIT {}, {}'.format(row1,row2))
            data = cur.fetchall()
            return render_template('reportes/t_p.html',Datos = session,Infos =data)         
  except:
    flash("Inicia Secion")
    return render_template('index.html')

@app.route('/Solicitudes_Ingram/<rowi>',methods=['POST','GET'])
def solicitud_ingram(rowi):
  try:
      if request.method == 'POST':
        if request.method == 'GET':
          session['rowi_t_p']=rowi
          row1 = int(session['rowi_t_p'])
          row2 = 50
        else:
            row1 = int(session['rowi_t_p'])
            row2 =50
        if 'valor' in request.form:
          if len(request.form['valor'])>0:
            session['filtro_t_p']=request.form['filtro']
            session['valor_t_p']=request.form['valor']
            if 'datefilter' in request.form:
              if len(request.form['datefilter'])>0:
                daterangef=request.form['datefilter']
                daterange=daterangef.replace("-", "' AND '")
                session['datefilter']=daterange
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM prealert WHERE {} LIKE \'%{}%\' AND Fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['filtro_t_p'],session['valor_t_p'],session['datefilter'],row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_p.html',Datos = session,Infos =data)
              else:
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM prealert WHERE {} LIKE \'%{}%\'  LIMIT {}, {}'.format(session['filtro_t_p'],session['valor_t_p'],row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_p.html',Datos = session,Infos =data)
            else:
              session.pop('datefilter')
              cur = mysql.connection.cursor()
              cur.execute('SELECT * FROM prealert WHERE {} LIKE \'%{}%\'  LIMIT {}, {}'.format(session['filtro_t_p'],session['valor_t_p'],row1,row2))
              data = cur.fetchall()
              return render_template('reportes/t_p.html',Datos = session,Infos =data)
          else:
            if 'datefilter' in request.form:
              if len(request.form['datefilter'])>0:
                if 'valor_t_p' in session:
                  if len(session['valor_t_p'])>0:
                    daterangef=request.form['datefilter']
                    daterange=daterangef.replace("-", "' AND '")
                    session['datefilter']=daterange
                    cur = mysql.connection.cursor()
                    cur.execute('SELECT * FROM prealert WHERE {} LIKE \'%{}%\' AND Fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['filtro_t_p'],session['valor_t_p'],session['datefilter'],row1,row2))
                    data = cur.fetchall()
                    return render_template('reportes/t_p.html',Datos = session,Infos =data)
                  else:
                    session.pop('filtro_t_p')
                    session.pop('valor_t_p')
                    cur = mysql.connection.cursor()
                    cur.execute('SELECT * FROM prealert WHERE Fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter'],row1,row2))
                    data = cur.fetchall()
                    return render_template('reportes/t_p.html',Datos = session,Infos =data)
                else:
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM prealert WHERE Fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter'],row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_p.html',Datos = session,Infos =data)
              else:
                if 'valor_t_p' in session:
                  session.pop('filtro_t_p')
                  session.pop('valor_t_p')
                  if 'datefilter' in session:
                    session.pop('datefilter')
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM prealert  LIMIT {}, {}'.format(row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_p.html',Datos = session,Infos =data)
                else:
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM prealert  LIMIT {}, {}'.format(row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_p.html',Datos = session,Infos =data)
            else:
              if 'valor_t_p' in session:
                if 'datefilter' in session:
                    session.pop('datefilter')
                session.pop('filtro_t_p')
                session.pop('valor_t_p')
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM prealert  LIMIT {}, {}'.format(row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_p.html',Datos = session,Infos =data)
              else:
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM prealert  LIMIT {}, {}'.format(row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_p.html',Datos = session,Infos =data)

        else:
          if 'valor_t_p' in session:
            if len(session['valor_t_p'])>0:
              if 'datefilter' in session:
                if len(session['datefilter'])>0:
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM prealert WHERE {} LIKE \'%{}%\' AND Fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['filtro_t_p'],session['valor_t_p'],session['datefilter'],row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_p.html',Datos = session,Infos =data)
                else:
                  session.pop('datefilter')
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM prealert WHERE {} LIKE \'%{}%\'  LIMIT {}, {}'.format(session['filtro_t_p'],session['valor_t_p'],row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_p.html',Datos = session,Infos =data)
              else:
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM prealert WHERE {} LIKE \'%{}%\'  LIMIT {}, {}'.format(session['filtro_t_p'],session['valor_t_p'],row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_p.html',Datos = session,Infos =data) 
            else:
              session.pop('filtro_t_p')
              session.pop('valor_t_p')
              if 'datefilter' in session:
                if len(session['datefilter'])>0:
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM prealert WHERE Fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter'],row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_p.html',Datos = session,Infos =data)
                else:
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM prealert LIMIT {}, {}'.format(row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_p.html',Datos = session,Infos =data)
              else:
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM prealert  LIMIT {}, {}'.format(row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_p.html',Datos = session,Infos =data)
          else:
            if 'datefilter' in session:
              if len(session['datefilter'])>0:
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM prealert WHERE Fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter'],row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_p.html',Datos = session,Infos =data)
              else:
                session.pop('datefilter')
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM prealert LIMIT {}, {}'.format(row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_p.html',Datos = session,Infos =data)
            else:
              if 'datefilter' in request.form:
                if len(request.form['datefilter'])>0:
                  daterangef=request.form['datefilter']
                  daterange=daterangef.replace("-", "' AND '")
                  session['datefilter']=daterange
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM prealert WHERE  Fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter'],row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_p.html',Datos = session,Infos =data)
                else:
                  cur = mysql.connection.cursor()
                  cur.execute('SELECT * FROM prealert LIMIT {}, {}'.format(row1,row2))
                  data = cur.fetchall()
                  return render_template('reportes/t_p.html',Datos = session,Infos =data) 
              else:
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM prealert LIMIT {}, {}'.format(row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_p.html',Datos = session,Infos =data) 
      else: 
        if request.method == 'GET':
          session['rowi_t_p']=rowi
          row1 = int(session['rowi_t_p'])
          row2 = 50
        else:
          row1 = int(session['rowi_t_p'])
          row2 =50
        if 'valor_t_p' in session:
          if len(session['valor_t_p'])>0:
            if 'datefilter' in session:
              if len(session['datefilter'])>0:
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM prealert WHERE {} LIKE \'%{}%\' AND Fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['filtro_t_p'],session['valor_t_p'],session['datefilter'],row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_p.html',Datos = session,Infos =data)
              else:
                session.pop('datefilter')
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM prealert WHERE {} LIKE \'%{}%\'  LIMIT {}, {}'.format(session['filtro_t_p'],session['valor_t_p'],row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_p.html',Datos = session,Infos =data)
            else:
              cur = mysql.connection.cursor()
              cur.execute('SELECT * FROM prealert WHERE {} LIKE \'%{}%\'  LIMIT {}, {}'.format(session['filtro_t_p'],session['valor_t_p'],row1,row2))
              data = cur.fetchall()
              return render_template('reportes/t_p.html',Datos = session,Infos =data) 
          else:
            session.pop('filtro_t_p')
            session.pop('valor_t_p')
            if 'datefilter' in session:
              if len(session['datefilter'])>0:
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM prealert WHERE Fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter'],row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_p.html',Datos = session,Infos =data)
              else:
                session.pop('datefilter')
                cur = mysql.connection.cursor()
                cur.execute('SELECT * FROM prealert LIMIT {}, {}'.format(row1,row2))
                data = cur.fetchall()
                return render_template('reportes/t_p.html',Datos = session,Infos =data)
            else:
              cur = mysql.connection.cursor()
              cur.execute('SELECT * FROM prealert  LIMIT {}, {}'.format(row1,row2))
              data = cur.fetchall()
              return render_template('reportes/t_p.html',Datos = session,Infos =data)
        else:
          if 'datefilter' in session:
            if len(session['datefilter'])>0:
              cur = mysql.connection.cursor()
              cur.execute('SELECT * FROM prealert WHERE Fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter'],row1,row2))
              data = cur.fetchall()
              return render_template('reportes/t_p.html',Datos = session,Infos =data)
            else:
              session.pop('datefilter')
              cur = mysql.connection.cursor()
              cur.execute('SELECT * FROM prealert LIMIT {}, {}'.format(row1,row2))
              data = cur.fetchall()
              return render_template('reportes/t_p.html',Datos = session,Infos =data)
          else:
            cur = mysql.connection.cursor()
            cur.execute('SELECT * FROM prealert  LIMIT {}, {}'.format(row1,row2))
            data = cur.fetchall()
            return render_template('reportes/t_p.html',Datos = session,Infos =data)         
  except:
    flash("Inicia Secion")
    return render_template('index.html')

@app.route('/csvsolicitudretiros',methods=['POST','GET'])
def crear_csvsolicitudretiros():
    site=session['SiteName']
    row1 = int(session['rowi_solicitudrecibo'])
    row2 =5000
    if 'valor_solicitudrecibo' in session:
      if len(session['valor_solicitudrecibo'])>0:
        if 'datefilter_solicitudrecibo' in session:
          if len(session['datefilter_solicitudrecibo'])>0:
            cur = mysql.connection.cursor()
            cur.execute('SELECT * FROM solicitud_retiros WHERE {} LIKE \'%{}%\' AND fecha_de_entrega BETWEEN \'{}\'  LIMIT {}, {}'.format(session['filtro_solicitudrecibo'],session['valor_solicitudrecibo'],session['datefilter_solicitudrecibo'],row1,row2))
            data = cur.fetchall()
          else:
            cur = mysql.connection.cursor()
            cur.execute('SELECT * FROM solicitud_retiros WHERE {} LIKE \'%{}%\'  LIMIT {}, {}'.format(session['filtro_solicitudrecibo'],session['valor_solicitudrecibo'],row1,row2))
            data = cur.fetchall()
        else:
          cur = mysql.connection.cursor()
          cur.execute('SELECT * FROM solicitud_retiros WHERE {} LIKE \'%{}%\'  LIMIT {}, {}'.format(session['filtro_solicitudrecibo'],session['valor_solicitudrecibo'],row1,row2))
          data = cur.fetchall()
      else:
        if 'datefilter_solicitudrecibo' in session:
          if len(session['datefilter_solicitudrecibo'])>0:
            cur = mysql.connection.cursor()
            cur.execute('SELECT * FROM solicitud_retiros WHERE fecha_de_entrega BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter_solicitudrecibo'],row1,row2))
            data = cur.fetchall()
          else:
            cur = mysql.connection.cursor()
            cur.execute('SELECT * FROM solicitud_retiros LIMIT {}, {}'.format(row1,row2))
            data = cur.fetchall()
        else:
          cur = mysql.connection.cursor()
          cur.execute('SELECT * FROM solicitud_retiros  LIMIT {}, {}'.format(row1,row2))
          data = cur.fetchall()
    else:
      if 'datefilter_solicitudrecibo' in session:
        if len(session['datefilter_solicitudrecibo'])>0:
          cur = mysql.connection.cursor()
          cur.execute('SELECT * FROM solicitud_retiros WHERE fecha_de_entrega BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter_solicitudrecibo'],row1,row2))
          data = cur.fetchall()
        else:
          cur = mysql.connection.cursor()
          cur.execute('SELECT * FROM solicitud_retiros LIMIT {}, {}'.format(row1,row2))
      else:
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM solicitud_retiros  LIMIT {}, {}'.format(row1,row2))
        data = cur.fetchall()
    datos="Id"+","+"Ola"+","+"Meli"+","+"Fecha de Entrega"+","+"Cantidad Solicitada"+","+"QTY_DISP_WMS"+","+"Descripción"+","+"cantidad_susrtida"+","+"Estatus"+","+"Ubicacion"+","+"Fecha de creacion"+"\n"
    for res in data:
      datos+=str(res[0])
      datos+=","+str(res[1])
      datos+=","+str(res[2])
      datos+=","+str(res[3])
      datos+=","+str(res[4])
      datos+=","+str(res[5])
      datos+=","+str(res[6])
      datos+=","+str(res[7])
      datos+=","+str(res[8])
      datos+=","+str(res[9])
      datos+=","+str(res[10])
      datos+="\n"

    response = make_response(datos)
    response.headers["Content-Disposition"] = "attachment; filename="+"solicitud_retiros-"+str(datetime.today())+".csv"; 
    return response

@app.route('/csvsolicituddonacion',methods=['POST','GET'])
def crear_csvsolicituddonacion():
    site=session['SiteName']
    row1 = int(session['rowi_t_p'])
    row2 =50
    if 'valor_t_p' in session:
      if len(session['valor_t_p'])>0:
        if 'datefilter' in session:
          if len(session['datefilter'])>0:
            cur = mysql.connection.cursor()
            cur.execute('SELECT * FROM prealert WHERE {} LIKE \'%{}%\' AND Fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['filtro_t_p'],session['valor_t_p'],session['datefilter'],row1,row2))
            data = cur.fetchall()
          else:
            cur = mysql.connection.cursor()
            cur.execute('SELECT * FROM prealert WHERE {} LIKE \'%{}%\'  LIMIT {}, {}'.format(session['filtro_t_p'],session['valor_t_p'],row1,row2))
            data = cur.fetchall()
        else:
          cur = mysql.connection.cursor()
          cur.execute('SELECT * FROM prealert WHERE {} LIKE \'%{}%\'  LIMIT {}, {}'.format(session['filtro_t_p'],session['valor_t_p'],row1,row2))
          data = cur.fetchall()
      else:
        if 'datefilter' in session:
          if len(session['datefilter'])>0:
            cur = mysql.connection.cursor()
            cur.execute('SELECT * FROM prealert WHERE Fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter'],row1,row2))
            data = cur.fetchall()
          else:
            cur = mysql.connection.cursor()
            cur.execute('SELECT * FROM prealert LIMIT {}, {}'.format(row1,row2))
            data = cur.fetchall()
        else:
          cur = mysql.connection.cursor()
          cur.execute('SELECT * FROM prealert  LIMIT {}, {}'.format(row1,row2))
          data = cur.fetchall()
    else:
      if 'datefilter' in session:
        if len(session['datefilter'])>0:
          cur = mysql.connection.cursor()
          cur.execute('SELECT * FROM prealert WHERE Fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter'],row1,row2))
          data = cur.fetchall()
        else:
          cur = mysql.connection.cursor()
          cur.execute('SELECT * FROM prealert LIMIT {}, {}'.format(row1,row2))
      else:
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM prealert  LIMIT {}, {}'.format(row1,row2))
        data = cur.fetchall()
    datos="Id"+","+"Pre-Alert key"+","+"Facility Origen"+","+"Site Origen"+","+"Facility Destino"+","+"Site Destino"+","+"Transporte"+","+"Transportista"+","+"Placas"+","+"Orden"+","+"Paquetera"+","+"Marchamo"+","+"Responsable"+","+"Fecha y Hora"+","+"\n"
    for res in data:
      datos+=str(res[0])
      datos+=","+str(res[1])
      datos+=","+str(res[2])
      datos+=","+str(res[3])
      datos+=","+str(res[4])
      datos+=","+str(res[5])
      datos+=","+str(res[6])
      datos+=","+str(res[7])
      datos+=","+str(res[8])
      datos+=","+str(res[9])
      datos+=","+str(res[10])
      datos+=","+str(res[11])
      datos+=","+str(res[12])
      datos+=","+str(res[14])
      datos+="\n"

    response = make_response(datos)
    response.headers["Content-Disposition"] = "attachment; filename="+"Prealert"+str(datetime.today())+".csv"; 
    return response

@app.route('/csvsolicitudingram',methods=['POST','GET'])
def crear_ccsvsolicitudingram():
    site=session['SiteName']
    row1 = int(session['rowi_t_p'])
    row2 =50
    if 'valor_t_p' in session:
      if len(session['valor_t_p'])>0:
        if 'datefilter' in session:
          if len(session['datefilter'])>0:
            cur = mysql.connection.cursor()
            cur.execute('SELECT * FROM prealert WHERE {} LIKE \'%{}%\' AND Fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['filtro_t_p'],session['valor_t_p'],session['datefilter'],row1,row2))
            data = cur.fetchall()
          else:
            cur = mysql.connection.cursor()
            cur.execute('SELECT * FROM prealert WHERE {} LIKE \'%{}%\'  LIMIT {}, {}'.format(session['filtro_t_p'],session['valor_t_p'],row1,row2))
            data = cur.fetchall()
        else:
          cur = mysql.connection.cursor()
          cur.execute('SELECT * FROM prealert WHERE {} LIKE \'%{}%\'  LIMIT {}, {}'.format(session['filtro_t_p'],session['valor_t_p'],row1,row2))
          data = cur.fetchall()
      else:
        if 'datefilter' in session:
          if len(session['datefilter'])>0:
            cur = mysql.connection.cursor()
            cur.execute('SELECT * FROM prealert WHERE Fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter'],row1,row2))
            data = cur.fetchall()
          else:
            cur = mysql.connection.cursor()
            cur.execute('SELECT * FROM prealert LIMIT {}, {}'.format(row1,row2))
            data = cur.fetchall()
        else:
          cur = mysql.connection.cursor()
          cur.execute('SELECT * FROM prealert  LIMIT {}, {}'.format(row1,row2))
          data = cur.fetchall()
    else:
      if 'datefilter' in session:
        if len(session['datefilter'])>0:
          cur = mysql.connection.cursor()
          cur.execute('SELECT * FROM prealert WHERE Fecha BETWEEN \'{}\'  LIMIT {}, {}'.format(session['datefilter'],row1,row2))
          data = cur.fetchall()
        else:
          cur = mysql.connection.cursor()
          cur.execute('SELECT * FROM prealert LIMIT {}, {}'.format(row1,row2))
      else:
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM prealert  LIMIT {}, {}'.format(row1,row2))
        data = cur.fetchall()
    datos="Id"+","+"Pre-Alert key"+","+"Facility Origen"+","+"Site Origen"+","+"Facility Destino"+","+"Site Destino"+","+"Transporte"+","+"Transportista"+","+"Placas"+","+"Orden"+","+"Paquetera"+","+"Marchamo"+","+"Responsable"+","+"Fecha y Hora"+","+"\n"
    for res in data:
      datos+=str(res[0])
      datos+=","+str(res[1])
      datos+=","+str(res[2])
      datos+=","+str(res[3])
      datos+=","+str(res[4])
      datos+=","+str(res[5])
      datos+=","+str(res[6])
      datos+=","+str(res[7])
      datos+=","+str(res[8])
      datos+=","+str(res[9])
      datos+=","+str(res[10])
      datos+=","+str(res[11])
      datos+=","+str(res[12])
      datos+=","+str(res[14])
      datos+="\n"

    response = make_response(datos)
    response.headers["Content-Disposition"] = "attachment; filename="+"Prealert"+str(datetime.today())+".csv"; 
    return response


#PDF Ubicacion
@app.route('/pdf/<ubicacion>',methods=['POST','GET'])
def pdf_template(ubicacion):
  
        qr =  ubicacion
        img =qrcode.make(qr)
        file =open('qr.png','wb')
        img.save(file)
        lugar = 'De: '+session['FcName']+' | '+session['SiteName']
        facility = session['FcName']
        site = session['SiteName']
        today= datetime.today()
 
        pdf = FPDF(orientation = 'P',unit = 'mm', format='128x60mm')
        pdf.add_page()
         
        page_width = pdf.w - 2 * pdf.l_margin
         
        pdf.ln(5)
        pdf.image('static/img/MercadoLibre_logo.png', x= 20, y = 10, w=50, h = 20)
        pdf.set_font('Times','B',30)
        pdf.set_text_color(0,47,109)  
        pdf.text(x = 80, y = 19 ,txt =  "Withdrawal System" )
        pdf.ln(80)
        
        pdf.image('qr.png', x= 20, y = 45, w=40, h = 40)

        pdf.set_font('Times','B',12) 
        
        pdf.set_text_color(0,0,0) 
        pdf.text( x= 70, y = 57, txt = str(today))
        pdf.text( x= 70, y = 67, txt = "Ubicacion:")
        pdf.text( x= 70, y = 77, txt = qr)

        col_widt3 = page_width/2
        pdf.ln(15)
        pdf.set_font('Times','B',12)
        pdf.cell(page_width, 8.0, '_______________________________________________________________________', align='C')
         
        return Response(pdf.output(dest='S').encode('latin-1'), mimetype='application/pdf', headers={'Content-Disposition':'Atachment;filename=Ubicacion-'+qr+'.pdf'})




if __name__=='__main__':
    app.run(port = 3000, debug =True)