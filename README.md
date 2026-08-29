# Comunidad Inteligente — reconstrucción funcional

Esta es una reconstrucción limpia y funcional de los tres módulos observados en el proyecto de referencia. No es una copia línea por línea: fue creada desde cero con la misma separación general, corrigiendo dependencias ausentes y evitando subir claves, entornos virtuales o archivos temporales.

## Módulos

- `vc-master`: interfaz React + TypeScript + Vite.
- `auth_core-master`: Django REST para acceso, perfiles, publicaciones, actividades, documentos, mensajes, solicitudes e IA.
- `organizacion_core-master`: Django REST para organización, directiva, regiones, provincias y comunas.

## Certificados de residencia

El módulo `Certificados` implementa un trámite completo y trazable:

1. El vecino ingresa RUT, domicilio, finalidad y fecha del comprobante.
2. Adjunta un respaldo PDF, JPG o PNG de hasta 5 MB y acepta la declaración de veracidad.
3. El sistema valida RUT, formato real, integridad, antigüedad, comuna y posibles archivos duplicados.
4. La directiva descarga el respaldo y puede aprobar, solicitar una corrección o rechazar.
5. Al aprobar, la plataforma emite un PDF con folio único, firma de la persona revisora y código QR.
6. El QR abre una página pública que confirma la vigencia sin revelar el comprobante ni la dirección completa.

La prevalidación automática no reemplaza la revisión humana. Los respaldos se guardan en
`auth_core-master/private_uploads/`, no se publican como archivos estáticos y están excluidos de Git.

La demostración poblada contiene un certificado ficticio emitido para `vecino` y una solicitud pendiente de `ana.soto`, preparada para que `directiva` practique su revisión.

## Preparar y ejecutar

1. Instalar Python 3.12 o superior y Node.js LTS.
2. Ejecutar `preparar-proyecto.ps1` una sola vez.
3. Ejecutar `iniciar-aplicacion.ps1` para iniciar los tres módulos.
4. Abrir `http://127.0.0.1:5173`.

También se puede abrir todo el código ejecutando `abrir-en-visual-studio-code.ps1`.

## Usuarios ficticios

| Perfil | Usuario | Contraseña |
|---|---|---|
| Administrador y Django admin | `administrador` | `Admin1234!` |
| Directiva | `directiva` | `Demo1234!` |
| Vecino | `vecino` | `Demo1234!` |

El comando `seed_demo` crea además doce vecinos ficticios, publicaciones, actividades, documentos, mensajes y solicitudes.

## Base de datos

Cada backend usa SQLite para que el proyecto funcione sin instalar MySQL o PostgreSQL:

- `auth_core-master/db.sqlite3`: usuarios y vida comunitaria.
- `organizacion_core-master/db.sqlite3`: identidad legal, territorio y directiva.

Administración principal: `http://127.0.0.1:8000/admin/`.

## Asistente IA

Sin clave externa, el asistente usa respuestas seguras basadas en los datos autorizados de la junta. Para conectarlo a una API compatible con `chat/completions`:

1. Copiar `.env.example` como `.env`.
2. Completar `AI_API_URL`, `AI_API_KEY` y `AI_MODEL`.
3. No subir `.env` a Git; ya está protegido por `.gitignore`.

Si la API externa falla, la plataforma continúa funcionando con el modo local controlado.

## Pruebas

```powershell
.\.venv\Scripts\python.exe auth_core-master\manage.py test community
.\.venv\Scripts\python.exe organizacion_core-master\manage.py test organizations
cd vc-master
npm run build
```

Las pruebas del backend cubren la solicitud, validación de RUT y archivo, permisos, aprobación,
generación del PDF, descarga autenticada y verificación pública.
