from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    conn = sqlite3.connect('empleados.db')
    c = conn.cursor()

    # Obtener la lista de empleados
    c.execute('SELECT id, nombre FROM empleados')
    empleados = c.fetchall()

    # Si se envía un registro
    if request.method == 'POST':
        id_empleado = request.form['empleado']
        tipo_registro = request.form['tipo_registro']
        fecha_hora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        c.execute('INSERT INTO registros_horarios (id_empleado, tipo_registro, fecha_hora) VALUES (?, ?, ?)', 
                  (id_empleado, tipo_registro, fecha_hora))
        conn.commit()

        return redirect('/')

    # Obtener los últimos registros
    c.execute('''SELECT empleados.nombre, registros_horarios.fecha_hora, registros_horarios.tipo_registro
                 FROM registros_horarios
                 JOIN empleados ON registros_horarios.id_empleado = empleados.id
                 ORDER BY registros_horarios.fecha_hora DESC
                 LIMIT 10''')
    registros = c.fetchall()

    conn.close()

    return render_template('index.html', empleados=empleados, registros=registros)

if __name__ == '__main__':
    app.run(debug=True)
