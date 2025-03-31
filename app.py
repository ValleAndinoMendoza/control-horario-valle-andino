from datetime import datetime, timedelta

@app.route('/admin')
def admin():
    conn = sqlite3.connect('empleados.db')
    c = conn.cursor()

    # Calcular semana actual
    hoy = datetime.now()
    lunes = hoy - timedelta(days=hoy.weekday())
    domingo = lunes + timedelta(days=6)

    fecha_desde = lunes.strftime('%Y-%m-%d 00:00:00')
    fecha_hasta = domingo.strftime('%Y-%m-%d 23:59:59')

    # Traer empleados
    c.execute('SELECT id, nombre, valor_hora FROM empleados')
    empleados = c.fetchall()

    resumen = []

    for emp in empleados:
        id_emp = emp[0]
        nombre = emp[1]
        valor_hora = emp[2]

        # Traer registros de la semana para este empleado
        c.execute('''
            SELECT fecha_hora, tipo_registro FROM registros_horarios
            WHERE id_empleado = ? AND fecha_hora BETWEEN ? AND ?
            ORDER BY fecha_hora ASC
        ''', (id_emp, fecha_desde, fecha_hasta))
        registros = c.fetchall()

        # Agrupar en pares entrada/salida
        horas_totales = 0.0
        entrada_actual = None

        for reg in registros:
            fecha = datetime.strptime(reg[0], '%Y-%m-%d %H:%M:%S')
            tipo = reg[1]
            if tipo == 'entrada':
                entrada_actual = fecha
            elif tipo == 'salida' and entrada_actual:
                diff = fecha - entrada_actual
                horas = diff.total_seconds() / 3600
                horas_totales += round(horas, 2)
                entrada_actual = None

        total_pagar = round(horas_totales * valor_hora, 2)

        resumen.append({
            'nombre': nombre,
            'horas': round(horas_totales, 2),
            'valor_hora': valor_hora,
            'total': total_pagar
        })

    conn.close()
    return render_template('admin.html', resumen=resumen)
@app.route('/admin')
def admin():
    conn = sqlite3.connect('empleados.db')
    c = conn.cursor()
    registros = c.execute('''
        SELECT e.nombre, r.fecha_hora, r.tipo_registro
        FROM registros_horarios r
        JOIN empleados e ON r.id_empleado = e.id
        ORDER BY r.fecha_hora DESC
        LIMIT 20
    ''').fetchall()
    conn.close()
    return render_template('admin.html', registros=registros)
