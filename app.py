from flask import Flask, render_template, request, redirect, send_file
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import io

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    conn = sqlite3.connect('empleados.db')
    c = conn.cursor()

    if request.method == 'POST':
        id_empleado = request.form['empleado']
        tipo = request.form['tipo_registro']
        fecha_hora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute('INSERT INTO registros_horarios (id_empleado, tipo_registro, fecha_hora) VALUES (?, ?, ?)',
                  (id_empleado, tipo, fecha_hora))
        conn.commit()

    empleados = c.execute('SELECT * FROM empleados').fetchall()
    registros = c.execute('''SELECT e.nombre, r.fecha_hora, r.tipo_registro
                             FROM registros_horarios r
                             JOIN empleados e ON r.id_empleado = e.id
                             ORDER BY r.fecha_hora DESC
                             LIMIT 20''').fetchall()
    conn.close()
    return render_template('index.html', empleados=empleados, registros=registros)

@app.route('/admin')
def admin():
    conn = sqlite3.connect('empleados.db')
    c = conn.cursor()

    hoy = datetime.now()
    lunes = hoy - timedelta(days=hoy.weekday())
    domingo = lunes + timedelta(days=6)
    fecha_desde = lunes.strftime('%Y-%m-%d 00:00:00')
    fecha_hasta = domingo.strftime('%Y-%m-%d 23:59:59')

    c.execute('SELECT id, nombre, valor_hora FROM empleados')
    empleados = c.fetchall()
    resumen = []

    for emp in empleados:
        id_emp, nombre, valor_hora = emp
        c.execute('''SELECT fecha_hora, tipo_registro FROM registros_horarios
                     WHERE id_empleado = ? AND fecha_hora BETWEEN ? AND ?
                     ORDER BY fecha_hora ASC''', (id_emp, fecha_desde, fecha_hasta))
        registros = c.fetchall()

        entrada = None
        total_por_dia = []

        for reg in registros:
            fecha = datetime.strptime(reg[0], '%Y-%m-%d %H:%M:%S')
            tipo = reg[1]
            if tipo == 'entrada':
                entrada = fecha
            elif tipo == 'salida' and entrada:
                diff = fecha - entrada
                horas = round(diff.total_seconds() / 3600, 2)
                total = round(horas * valor_hora, 2)
                total_por_dia.append({
                    'dia': entrada.strftime('%d/%m/%Y'),
                    'entrada': entrada.strftime('%H:%M'),
                    'salida': fecha.strftime('%H:%M'),
                    'horas': '{:02.0f}:{:02.0f}'.format(*divmod(horas * 60, 60)),
                    'valor_hora': valor_hora,
                    'total': total
                })
                entrada = None

        resumen.append({
            'nombre': nombre,
            'detalle': total_por_dia
        })

    registros = c.execute('''SELECT r.id, e.nombre, r.fecha_hora, r.tipo_registro
                              FROM registros_horarios r
                              JOIN empleados e ON r.id_empleado = e.id
                              ORDER BY r.fecha_hora DESC
                              LIMIT 20''').fetchall()

    conn.close()
    return render_template('admin.html', resumen=resumen, registros=registros)

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    conn = sqlite3.connect('empleados.db')
    c = conn.cursor()
    if request.method == 'POST':
        nueva_fecha = request.form['fecha_hora']
        nuevo_tipo = request.form['tipo_registro']
        c.execute('UPDATE registros_horarios SET fecha_hora = ?, tipo_registro = ? WHERE id = ?',
                  (nueva_fecha, nuevo_tipo, id))
        conn.commit()
        conn.close()
        return redirect('/admin')
    else:
        c.execute('SELECT id, fecha_hora, tipo_registro FROM registros_horarios WHERE id = ?', (id,))
        registro = c.fetchone()
        conn.close()
        return render_template('editar.html', registro=registro)

@app.route('/exportar_excel')
def exportar_excel():
    conn = sqlite3.connect('empleados.db')
    c = conn.cursor()
    hoy = datetime.now()
    lunes = hoy - timedelta(days=hoy.weekday())
    domingo = lunes + timedelta(days=6)
    fecha_desde = lunes.strftime('%Y-%m-%d 00:00:00')
    fecha_hasta = domingo.strftime('%Y-%m-%d 23:59:59')

    c.execute('''SELECT e.nombre, r.fecha_hora, r.tipo_registro
                 FROM registros_horarios r
                 JOIN empleados e ON r.id_empleado = e.id
                 WHERE r.fecha_hora BETWEEN ? AND ?
                 ORDER BY r.fecha_hora ASC''', (fecha_desde, fecha_hasta))
    rows = c.fetchall()
    conn.close()

    df = pd.DataFrame(rows, columns=['Empleado', 'Fecha y Hora', 'Tipo'])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Reporte Semanal')
    output.seek(0)
    return send_file(output, as_attachment=True, download_name='reporte_semanal.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# SOLO si lo ejecutás localmente
if __name__ == '__main__':
    app.run(debug=True)
