"""
generate_data.py — Regenerate dashboard CSVs from raw Client files.
Produces:
  1. asignaciones_v2.csv: pais,mes,tipo_asignacion,estado,servicios,expedientes
  2. nodos_detalle.csv: nodo,pais_asistencia,mes,estado,servicios,expedientes
"""
import csv
import os
import pandas as pd
from collections import defaultdict

PAISES_DIR = r'C:\Users\Ricardo\OneDrive - Global Solutions Center SAS\Escritorio\Paises'
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

# All Client files
CLIENT_FILES = [
    ('Client01_Puerto_Rico_20251027.csv', 'Puerto Rico'),
    ('Client03_Dominicana_20251027.csv', 'Dominicana'),
    ('Client04_Salvador_20251027.csv', 'El Salvador'),
    ('Client05_Mexico_20251027.csv', 'Mexico'),
    ('Client06_Argentina_20251027.csv', 'Argentina'),
    ('Client07_Egipto_20251027.csv', 'Egipto'),
    ('Client08_Costa_Rica_20251027.csv', 'Costa Rica'),
    ('Client10_Ecuador_20251027.csv', 'Ecuador'),
    ('Client11_Chile_20251027.csv', 'Chile'),
    ('Client12_Uruguay_20251027.csv', 'Uruguay'),
    ('Client13_Bolivia_20251027.csv', 'Bolivia'),
    ('Client15_Guatemala_20251027.csv', 'Guatemala'),
    ('Client17_Peru_20251027.csv', 'Peru'),
    ('Client18_Paraguay_20251027.csv', 'Paraguay'),
    ('Client19_Colombia_20251027.csv', 'Colombia'),
    ('Client20_Honduras_20251027.csv', 'Honduras'),
    ('Client22_Nicaragua_20251027.csv', 'Nicaragua'),
    ('Client24_Estados_Unidos_20251027.csv', 'Estados Unidos'),
]

def load_nodo_map():
    """Load expediente -> nodo mapping from soa_nodos.csv."""
    nodo_map = {}
    soa_path = os.path.join(DATA_DIR, 'soa_nodos.csv')
    if os.path.exists(soa_path):
        with open(soa_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                exp_id = row.get('Id_Expediente', '').strip()
                nodo = row.get('Nodo', '').strip()
                if exp_id and nodo:
                    nodo_map[exp_id] = nodo
    print(f"  Loaded {len(nodo_map):,} expediente->nodo mappings")
    return nodo_map

def process_client_files(nodo_map):
    """Process all Client CSVs and aggregate data."""
    # Key: (pais, mes, tipo_asignacion, estado) -> {servicios: count, expedientes: set}
    asig_data = defaultdict(lambda: {'servicios': 0, 'expedientes': set()})
    # Key: (nodo, pais, mes, estado) -> {servicios: count, expedientes: set}
    nodo_data = defaultdict(lambda: {'servicios': 0, 'expedientes': set()})
    
    for filename, pais in CLIENT_FILES:
        filepath = os.path.join(PAISES_DIR, filename)
        if not os.path.exists(filepath):
            print(f"  SKIP (not found): {filename}")
            continue
        
        print(f"  Processing {pais} ({filename})...")
        row_count = 0
        
        with open(filepath, 'r', encoding='latin-1') as f:
            reader = csv.reader(f, delimiter=';')
            headers = next(reader)
            
            # Find column indices
            cols = {h: i for i, h in enumerate(headers)}
            idx_exp = cols['id_expediente']
            idx_asist = cols['id_asistencia']
            idx_estado = cols['estado_asistencia']
            idx_tipo = cols['tipo_asignacion']
            idx_creacion = cols['creacion_asistencia']
            
            for row in reader:
                try:
                    fecha = row[idx_creacion]
                    if not fecha or len(fecha) < 7:
                        continue
                    
                    mes = fecha[:7]  # "2025-01"
                    estado = row[idx_estado].strip().upper() if row[idx_estado].strip() else 'SIN_ESTADO'
                    tipo = row[idx_tipo].strip().upper() if row[idx_tipo].strip() else 'SIN_TIPO'
                    exp_id = row[idx_exp].strip()
                    
                    # Normalize estado
                    if estado not in ('CONCLUIDA', 'CANCELADA', 'PROCESO'):
                        estado = 'OTRO'
                    
                    # Asignaciones aggregation
                    key_asig = (pais, mes, tipo, estado)
                    asig_data[key_asig]['servicios'] += 1
                    asig_data[key_asig]['expedientes'].add(exp_id)
                    
                    # Nodo aggregation
                    nodo = nodo_map.get(exp_id, 'Sin Nodo')
                    key_nodo = (nodo, pais, mes, estado)
                    nodo_data[key_nodo]['servicios'] += 1
                    nodo_data[key_nodo]['expedientes'].add(exp_id)
                    
                    row_count += 1
                except (ValueError, IndexError):
                    continue
        
        print(f"    -> {row_count:,} rows processed")
    
    return asig_data, nodo_data

def write_asignaciones(asig_data):
    """Write asignaciones_v2.csv."""
    out_path = os.path.join(DATA_DIR, 'asignaciones_v2.csv')
    rows = []
    for (pais, mes, tipo, estado), vals in asig_data.items():
        rows.append({
            'pais': pais,
            'mes': mes,
            'tipo_asignacion': tipo,
            'estado': estado,
            'servicios': vals['servicios'],
            'expedientes': len(vals['expedientes']),
        })
    
    df = pd.DataFrame(rows)
    df = df.sort_values(['pais', 'mes', 'tipo_asignacion', 'estado'])
    df.to_csv(out_path, index=False)
    print(f"\n  Written {len(df):,} rows to {out_path}")
    
    # Summary
    print(f"\n  === ASIGNACIONES SUMMARY ===")
    total = df.groupby('estado').agg({'servicios': 'sum', 'expedientes': 'sum'})
    print(total)
    print(f"\n  By country (CONCLUIDA only):")
    concl = df[df['estado'] == 'CONCLUIDA'].groupby('pais')['servicios'].sum().sort_values(ascending=False)
    print(concl)

def write_nodos(nodo_data):
    """Write nodos_detalle.csv."""
    out_path = os.path.join(DATA_DIR, 'nodos_detalle.csv')
    rows = []
    for (nodo, pais, mes, estado), vals in nodo_data.items():
        rows.append({
            'nodo': nodo,
            'pais_asistencia': pais,
            'mes': mes,
            'estado': estado,
            'servicios': vals['servicios'],
            'expedientes': len(vals['expedientes']),
        })
    
    df = pd.DataFrame(rows)
    df = df.sort_values(['nodo', 'pais_asistencia', 'mes', 'estado'])
    df.to_csv(out_path, index=False)
    print(f"\n  Written {len(df):,} rows to {out_path}")
    
    # Summary
    print(f"\n  === NODOS SUMMARY ===")
    nodo_sum = df.groupby('nodo').agg({'servicios': 'sum', 'expedientes': 'sum'}).sort_values('servicios', ascending=False)
    print(nodo_sum)

if __name__ == '__main__':
    print("=" * 60)
    print("Generating dashboard data files...")
    print("=" * 60)
    
    print("\n1. Loading nodo mapping...")
    nodo_map = load_nodo_map()
    
    print("\n2. Processing Client files...")
    asig_data, nodo_data = process_client_files(nodo_map)
    
    print("\n3. Writing asignaciones_v2.csv...")
    write_asignaciones(asig_data)
    
    print("\n4. Writing nodos_detalle.csv...")
    write_nodos(nodo_data)
    
    print("\n" + "=" * 60)
    print("DONE!")
    print("=" * 60)
