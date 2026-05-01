# 💵 Liquidación Quincenal

App web en Python (Streamlit) para liquidar sueldos quincenales y vacaciones, con datos en Supabase y recibos en PDF. Pensada para abrirse desde PC o celular vía link público con contraseña.

## Reglas de cálculo

```
Quincena base       = sueldo / 2
Valor día           = sueldo / 30
Valor día vacaciones= sueldo / 25
Hora simple         = sueldo / 200
Hora extra 50%      = hora_simple × 1,5
Hora extra 100%     = hora_simple × 2

Total quincena = quincena_base
              + (hs_50  × hora_50)
              + (hs_100 × hora_100)
              − (hs_ausencia × hora_simple)
              − adelantos

Total vacaciones = (sueldo / 25) × días_vacaciones
```

Sandra tiene flag `modo_pago = mensual`: cobra el sueldo entero el día 5, sin extras ni descuentos.

## Estructura de la base de datos (Supabase / Postgres)

- **empleados**: `id, nombre, sueldo_mensual, activo, modo_pago, fecha_alta, notas`
- **liquidaciones**: `id, empleado_id, tipo, anio, mes, quincena, fecha_pago, fecha_inicio_vac, fecha_fin_vac, hs_50, hs_100, hs_ausencia, dias_vacaciones, adelantos, total_calculado, total_pagado, estado, observaciones, updated_at`

Las tablas se crean ejecutando un SQL una sola vez (ver paso 1). Los empleados se precargan automáticamente la primera vez que apretás "Inicializar base de datos" en la app.

---

## 1) Setup en Supabase (una sola vez)

1. Crear cuenta en https://supabase.com (login con GitHub o Google).
2. **New project** → nombre: `quincena-app`, contraseña fuerte, región **South America (São Paulo)** o la más cercana.
3. Esperar 1-2 min a que el proyecto esté listo.
4. **SQL Editor → New query** → pegar y correr el script de `setup_supabase.sql` (acá abajo). Cuando salga la advertencia de RLS, click en **"Ejecutar sin RLS"**.
5. **Project Settings → Claves API** → copiar:
   - **Project URL** (algo como `https://xxxx.supabase.co`)
   - **service_role secret** (empieza con `sb_secret_...`)

```sql
-- setup_supabase.sql
create table empleados (
    id bigserial primary key,
    nombre text not null,
    sueldo_mensual numeric not null default 0,
    activo text default 'SI',
    modo_pago text default 'quincenal',
    fecha_alta date,
    notas text default ''
);

create table liquidaciones (
    id bigserial primary key,
    empleado_id bigint references empleados(id) on delete cascade,
    tipo text default 'quincena',
    anio int,
    mes int,
    quincena int default 0,
    fecha_pago date,
    fecha_inicio_vac date,
    fecha_fin_vac date,
    hs_50 numeric default 0,
    hs_100 numeric default 0,
    hs_ausencia numeric default 0,
    dias_vacaciones int default 0,
    adelantos numeric default 0,
    total_calculado numeric default 0,
    total_pagado numeric default 0,
    estado text default 'pendiente',
    observaciones text default '',
    updated_at timestamptz default now()
);

create index liquidaciones_periodo_idx on liquidaciones (anio, mes, quincena);
create index liquidaciones_empleado_idx on liquidaciones (empleado_id);

alter table empleados disable row level security;
alter table liquidaciones disable row level security;
```

## 2) Setup local

```bash
cd quincena_app
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
```

Crear el archivo `.streamlit/secrets.toml` (copiando `secrets.toml.example`) y completarlo:
- `password`: la que quieras (por defecto `Ka181297`)
- `url`: el Project URL de Supabase
- `service_key`: la clave `service_role` (`sb_secret_...`)

Correr:
```bash
streamlit run app.py
```

Abre `http://localhost:8501`. Pedir contraseña, entrar, y desde el menú principal apretar **Inicializar base de datos**: precarga los 11 empleados.

## 3) Deploy en Streamlit Cloud (link público con contraseña)

1. Subir el proyecto a un repositorio **privado** de GitHub. El archivo `secrets.toml` queda fuera por el `.gitignore`.
2. https://share.streamlit.io/ → **New app** → seleccionar el repo, branch, `app.py`.
3. **Advanced settings → Secrets** → pegar el mismo contenido de `secrets.toml`.
4. Deploy. URL pública del tipo `https://tu-app.streamlit.app`. Pide contraseña al entrar.

## 4) Pantallas

- **Inicio**: estado general, próxima fecha de pago, total liquidado del mes.
- **Liquidación**: cargás horas extras, ausencias, adelantos por cada empleado de la quincena.
- **Vacaciones**: liquidás vacaciones en recibo aparte (sueldo / 25 × días).
- **Empleados**: alta / edición / baja, cambio de sueldo.
- **Histórico**: filtros por año, mes, quincena, tipo, empleado.
- **Recibos PDF**: descargás el PDF (4 recibos por hoja A4 horizontal).

## 5) Mantenimiento

- **Cambio de sueldo**: editás el empleado y se aplica desde la próxima liquidación.
- **Sueldo de Sebastián**: en la pantalla de Liquidación tiene un campo extra para sobreescribir el sueldo solo para ese mes.
- **Ver datos crudos**: Supabase tiene un **Table Editor** en su dashboard, parecido a una planilla. Ahí podés ver/editar cualquier registro a mano.
- **Backup**: Supabase hace snapshots automáticos del proyecto.
