import calendar
from datetime import datetime, timedelta
from sqlalchemy import func
from myapp.models import DriveFile, User


def get_file_types_stats():
    from app import db
    # Obtener distribución de tipos de archivo para el gráfico circular
    file_types_query = db.session.query(
        DriveFile.mimetype,
        func.count(DriveFile.id).label('count')
    ).group_by(DriveFile.mimetype).all()
    
    total_files = sum(type_count for _, type_count in file_types_query)
    
    # Colores para el gráfico
    colors = [
        '#0076a8',  # PDF
        '#00a8d4',  # Excel
        '#4ecdc4',  # Word
        '#ff6b6b',  # PNG
        '#f7b801',  # JPG
        '#7b68ee',  # Otra Imagen
        '#1a535c',  # Texto
        '#2ecc71',  # Comprimido
        '#e74c3c',  # Presentación
        '#95a5a6'   # Otro
    ]
    
    # Categorías predefinidas para agrupar los tipos MIME
    categories = {
        'PDF': 0,
        'Excel': 0,
        'Word': 0,
        'PNG': 0,
        'JPG': 0,
        'Otra Imagen': 0,
        'Texto': 0,
        'Comprimido': 0,
        'Presentación': 0,
        'Otro': 0
    }
    
    # Agrupar los recuentos por categoría
    for mimetype, count in file_types_query:
        friendly_type = get_friendly_mimetype(mimetype)
        categories[friendly_type] = categories.get(friendly_type, 0) + count
    
    # Filtrar categorías con 0 archivos y preparar los datos para el gráfico
    file_types = []
    color_index = 0
    
    for category, count in categories.items():
        if count > 0:
            percentage = round((count / total_files) * 100) if total_files > 0 else 0
            file_types.append({
                'name': category,
                'count': count,
                'percentage': percentage,
                'color': colors[color_index % len(colors)]
            })
            color_index += 1
    
    # Ordenar por cantidad descendente
    file_types.sort(key=lambda x: x['count'], reverse=True)
    
    return file_types


def calculate_percent_change(current, previous):
    if previous == 0:
        return 100 if current > 0 else 0
    
    percent = ((current - previous) / previous) * 100
    
    if percent > 100:
        return 100
    elif percent < -100:
        return -100
    
    return round(percent)

def get_friendly_mimetype(mimetype):
    if not mimetype:
        return "Desconocido"
    
    mimetype = mimetype.lower()
    if 'pdf' in mimetype:
        return "PDF"
    elif 'excel' in mimetype or 'spreadsheet' in mimetype or 'xlsx' in mimetype or 'xls' in mimetype:
        return "Excel"
    elif 'word' in mimetype or 'document' in mimetype or 'docx' in mimetype or 'doc' in mimetype:
        return "Word"
    elif 'image/png' in mimetype:
        return "PNG"
    elif 'image/jpeg' in mimetype or 'image/jpg' in mimetype:
        return "JPG"
    elif 'image' in mimetype:
        return "Otra Imagen"
    elif 'text' in mimetype:
        return "Texto"
    elif 'zip' in mimetype or 'compressed' in mimetype or 'archive' in mimetype:
        return "Comprimido"
    elif 'presentation' in mimetype or 'powerpoint' in mimetype or 'pptx' in mimetype:
        return "Presentación"
    else:
        return "Otro"

def get_charts_data():
    # Datos para los gráficos
    today = datetime.utcnow().date()
    
    # Datos para gráfico semanal
    week_data = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        count = DriveFile.query.filter(func.date(DriveFile.uploaded_at) == date).count()
        day_name = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"][date.weekday()]
        week_data.append({"label": day_name, "value": count})
    
    # Datos para gráfico mensual
    month_data = []
    first_day = today.replace(day=1)
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    
    # Agrupar por semanas
    for week in range(4):
        start_day = min(week * 7 + 1, days_in_month)
        end_day = min((week + 1) * 7, days_in_month)
        
        start_date = first_day.replace(day=start_day)
        end_date = first_day.replace(day=end_day)
        
        count = DriveFile.query.filter(
            func.date(DriveFile.uploaded_at) >= start_date,
            func.date(DriveFile.uploaded_at) <= end_date
        ).count()
        
        month_data.append({"label": f"Sem {week+1}", "value": count})
    
    # Datos para gráfico anual
    year_data = []
    current_year = today.year
    
    for month in range(1, 13):
        start_date = datetime(current_year, month, 1).date()
        if month == 12:
            end_date = datetime(current_year, month, 31).date()
        else:
            end_date = datetime(current_year, month + 1, 1).date() - timedelta(days=1)
        
        count = DriveFile.query.filter(
            func.date(DriveFile.uploaded_at) >= start_date,
            func.date(DriveFile.uploaded_at) <= end_date
        ).count()
        
        month_name = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"][month-1]
        year_data.append({"label": month_name, "value": count})
    
    # Datos similares para usuarios
    user_week_data = []
    user_month_data = []
    user_year_data = []
    
    # Datos para usuarios por semana
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        count = User.query.filter(func.date(User.created_at) == date).count()
        day_name = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"][date.weekday()]
        user_week_data.append({"label": day_name, "value": count})
    
    # Datos para usuarios por mes (semanas)
    for week in range(4):
        start_day = min(week * 7 + 1, days_in_month)
        end_day = min((week + 1) * 7, days_in_month)
        
        start_date = first_day.replace(day=start_day)
        end_date = first_day.replace(day=end_day)
        
        count = User.query.filter(
            func.date(User.created_at) >= start_date,
            func.date(User.created_at) <= end_date
        ).count()
        
        user_month_data.append({"label": f"Sem {week+1}", "value": count})
    
    # Datos para usuarios por año (meses)
    for month in range(1, 13):
        start_date = datetime(current_year, month, 1).date()
        if month == 12:
            end_date = datetime(current_year, month, 31).date()
        else:
            end_date = datetime(current_year, month + 1, 1).date() - timedelta(days=1)
        
        count = User.query.filter(
            func.date(User.created_at) >= start_date,
            func.date(User.created_at) <= end_date
        ).count()
        
        month_name = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"][month-1]
        user_year_data.append({"label": month_name, "value": count})
    
    return {
        "files": {
            "week": week_data,
            "month": month_data,
            "year": year_data
        },
        "users": {
            "week": user_week_data,
            "month": user_month_data,
            "year": user_year_data
        }
    }