from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import json
import plotly
import plotly.graph_objs as go

app = Flask(__name__)
DB_NAME = "cat_data.db"

# --- Logic Functions ---
def calculate_age_months(current_date, birth_date):
    if current_date < birth_date: return 0.0
    rd = relativedelta(current_date, birth_date)
    full_months = rd.years * 12 + rd.months
    start_of_month = birth_date + pd.DateOffset(months=full_months)
    end_of_month = birth_date + pd.DateOffset(months=full_months + 1)
    days_in_month = (end_of_month - start_of_month).days
    fraction = rd.days / days_in_month if days_in_month > 0 else 0
    return full_months + fraction

# Reference Data
MALE_REF = [
    (0.0, 0.08, 0.17), (7/30.44, 0.18, 0.29), (14/30.44, 0.29, 0.43), (21/30.44, 0.42, 0.60),
    (1.0, 0.61, 0.82), (2.0, 0.9, 1.8), (3.0, 1.7, 2.3), (4.0, 2.9, 4.1),
    (5.0, 3.3, 5.4), (6.0, 3.4, 5.9), (7.0, 4.1, 6.3), (8.0, 4.4, 6.8), (9.0, 5.0, 7.3), (10.0, 5.1, 7.7)
]
FEMALE_REF = [
    (0.0, 0.08, 0.15), (7/30.44, 0.15, 0.26), (14/30.44, 0.27, 0.41), (21/30.44, 0.41, 0.55),
    (1.0, 0.55, 0.74), (2.0, 0.9, 1.4), (3.0, 1.4, 2.3), (4.0, 2.5, 3.6),
    (5.0, 2.7, 4.2), (6.0, 3.1, 4.5), (7.0, 3.3, 4.5), (8.0, 3.7, 5.0), (9.0, 4.1, 5.4), (10.0, 4.0, 5.4)
]

def create_interactive_plot(df, cat_name, ref_data, birth_date):
    """Generates a Plotly JSON graph object"""
    
    # 1. Filter Data
    cat_df = df[df['cat_name'] == cat_name].sort_values('date')
    
    # 2. Determine View Limits (Global Min/Max + 7 days)
    min_date = df['date'].min()
    max_date = df['date'].max()
    start_view = calculate_age_months(min_date - timedelta(days=7), birth_date)
    end_view = calculate_age_months(max_date + timedelta(days=7), birth_date)

    # 3. Create Reference Band (Interpolation)
    ref_months = [x[0] for x in ref_data]
    ref_min = [x[1] for x in ref_data]
    ref_max = [x[2] for x in ref_data]
    
    max_interp_x = max(end_view, max(ref_months))
    interp_months = np.linspace(0, max_interp_x, 300)
    interp_min = np.interp(interp_months, ref_months, ref_min)
    interp_max = np.interp(interp_months, ref_months, ref_max)

    # 4. Build Plotly Figure
    fig = go.Figure()

    # Reference Band (Upper and Lower bound trick)
    # We plot the lower bound (invisible) and then fill the upper bound down to it
    fig.add_trace(go.Scatter(
        x=interp_months, y=interp_min,
        mode='lines', line=dict(width=0),
        showlegend=False, hoverinfo='skip',
        name='Lower Bound'
    ))
    fig.add_trace(go.Scatter(
        x=interp_months, y=interp_max,
        mode='lines', line=dict(width=0),
        fill='tonexty', # Fills down to the previous trace
        fillcolor='rgba(173, 216, 230, 0.4)', # Light blue, transparent
        name='Reference Range',
        hoverinfo='skip'
    ))

    # Cat Data Line
    if not cat_df.empty:
        # Create custom hover text
        hover_text = [
            f"Date: {d.strftime('%Y-%m-%d')}<br>Age: {m:.2f} months<br>Weight: {w}kg"
            for d, m, w in zip(cat_df['date'], cat_df['age_months'], cat_df['weight'])
        ]
        
        fig.add_trace(go.Scatter(
            x=cat_df['age_months'], 
            y=cat_df['weight'],
            mode='lines+markers',
            name=cat_name,
            marker=dict(size=8, color='green'),
            line=dict(color='green', width=2),
            text=hover_text,
            hoverinfo='text'
        ))

    # Layout Settings
    fig.update_layout(
        title=f"{cat_name} Growth Chart",
        xaxis_title="Age (Months)",
        yaxis_title="Weight (kg)",
        xaxis=dict(range=[start_view, end_view], fixedrange=False), # fixedrange=False allows zoom
        yaxis=dict(fixedrange=False),
        hovermode="closest",
        template="simple_white",
        margin=dict(l=40, r=40, t=40, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    # Return as dict for Jinja tojson filter
    return fig.to_dict()

@app.route('/')
def index():
    conn = sqlite3.connect(DB_NAME)
    try:
        df = pd.read_sql_query("SELECT * FROM weights ORDER BY date_str DESC", conn)
    except:
        df = pd.DataFrame()
    finally:
        conn.close()
    
    simba_json = None
    nala_json = None
    table_data = []

    if not df.empty:
        birth_date = pd.Timestamp("2025-08-30")
        
        # Ensure weight is numeric and date parses cleanly
        df['weight'] = pd.to_numeric(df['weight'], errors='coerce')
        df = df.dropna(subset=['weight'])
        
        df['date'] = pd.to_datetime(df['date_str'], errors='coerce')
        df = df.dropna(subset=['date'])
        
        df['age_months'] = df['date'].apply(lambda x: calculate_age_months(x, birth_date))
        
        # Generate two separate interactive plots
        simba_json = create_interactive_plot(df, "Simba", MALE_REF, birth_date)
        nala_json = create_interactive_plot(df, "Nala", FEMALE_REF, birth_date)
        
        # Pass raw data to template for custom rendering
        table_data = df[['id', 'cat_name', 'date_str', 'weight']].values.tolist()

    # Pass today's date for the input field default
    today_str = datetime.today().strftime('%Y-%m-%d')

    return render_template('index.html', 
                           simba_plot=simba_json, 
                           nala_plot=nala_json, 
                           table_data=table_data,
                           today=today_str)

@app.route('/add', methods=['POST'])
def add_entry():
    cat = request.form.get('cat_name')
    weight = request.form.get('weight')
    date = request.form.get('date')
    time = request.form.get('time') # Get the time input
    
    # Logic: If time is provided by user, use it. Otherwise default to current time
    if time:
        date_str = f"{date} {time}"
    else:
        current_time = datetime.now().strftime('%H:%M')
        date_str = f"{date} {current_time}"
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO weights (cat_name, date_str, weight) VALUES (?, ?, ?)", 
              (cat, date_str, float(weight)))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete/<int:entry_id>', methods=['POST'])
def delete_entry(entry_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM weights WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)