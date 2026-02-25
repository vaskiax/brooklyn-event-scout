# Guía de Simulación de Despliegue en Google Cloud Platform (Cuenta Nueva)

Esta guía detalla el proceso paso a paso para desplegar el agente en una cuenta de Google totalmente nueva. El objetivo es simular un entorno de producción desde cero y validar que todo el flujo (web scraping, envío de correos, integraciones) funcione correctamente.

---

## FASE 1: Preparación de la Cuenta y Proyecto (Consola de Google Cloud)

Como vas a utilizar una cuenta de Google diferente, todo debe configurarse desde la interfaz web (la consola de Google Cloud) antes de ejecutar el script de despliegue.

### 1. Iniciar sesión y acceder a Google Cloud Console
1. Abre tu navegador en una ventana de incógnito o con un perfil nuevo.
2. Inicia sesión con la **nueva cuenta de Google**.
3. Ve a [Google Cloud Console](https://console.cloud.google.com/).
4. Acepta los Términos de Servicio si es la primera vez que ingresas.

### 2. Crear el Proyecto
1. En la barra superior, haz clic en el menú desplegable de proyectos (suele decir "Selecciona un proyecto").
2. Haz clic en **"Proyecto Nuevo"** (New Project).
3. Asigna un nombre al proyecto (ej. `event-driven-alerts-test`).
4. Anota el **ID del proyecto** (se genera automáticamente debajo del nombre, por ejemplo: `event-driven-alerts-test-12345`). Lo necesitarás más adelante.
5. Haz clic en **Crear**.
6. Una vez creado, selecciónalo en la barra superior para asegurarte de que estás trabajando dentro de él.

### 3. Configurar la Cuenta de Facturación (Billing)
Para usar Google Cloud Functions, Secret Manager y Scheduler, *es obligatorio* tener facturación activa, aunque estemos en la capa gratuita.
1. En el menú de navegación izquierdo (las tres líneas), ve a **"Facturación"** (Billing).
2. Haz clic en **"Vincular una cuenta de facturación"** o **"Gestionar cuentas de facturación"**.
3. Si la cuenta nueva no tiene facturación, haz clic en **"Añadir cuenta de facturación"** y sigue los pasos para ingresar los datos de tu tarjeta (Google no cobrará nada sin avisar y da saldo de prueba a cuentas nuevas).
4. Asegúrate de que tu nuevo proyecto esté vinculado a esta cuenta de facturación.

---

## FASE 2: Configuración de OAuth 2.0 (Para el Agente)

El agente necesita permisos para leer/enviar correos (Gmail API) u otros servicios. Para ello, necesitamos configurar la Pantalla de Consentimiento y generar las credenciales.

### 1. Habilitar la API de Gmail (y otras si aplica)
1. En el buscador superior de la consola, escribe **"Gmail API"** y selecciónala.
2. Haz clic en el botón azul **"Habilitar"**.

### 2. Configurar la Pantalla de Consentimiento de OAuth
1. En el menú izquierdo, ve a **"API y Servicios"** > **"Pantalla de consentimiento de OAuth"** (OAuth consent screen).
2. Selecciona **"Externo"** (External) ya que es una cuenta de prueba personal, y haz clic en **Crear**.
3. En **Información de la aplicación**:
   - **Nombre de la aplicación**: `Event Scout Agent` (o el que prefieras).
   - **Correo electrónico de asistencia**: Selecciona tu correo nuevo.
   - **Información de contacto del desarrollador**: Ingresa tu correo nuevo.
4. Haz clic en **Guardar y Continuar**.
5. En **Permisos** (Scopes), haz clic en **Añadir o Quitar Permisos**.
   - Busca y selecciona los permisos necesarios (por lo general `https://www.googleapis.com/auth/gmail.modify` o el que el agente utilice).
   - Haz clic en Guardar y Continuar.
6. En **Usuarios de prueba**:
   - Haz clic en **"+ Add Users"** y **agrega la dirección de correo de la cuenta nueva**. Al estar en modo prueba, solo los correos aquí listados podrán autorizarse.
7. Guarda y finaliza.

### 3. Crear las Credenciales del Cliente OAuth (credentials.json)
1. Ve a **"API y Servicios"** > **"Credenciales"**.
2. Haz clic en **"+ CREAR CREDENCIALES"** en la parte superior y selecciona **"ID de cliente de OAuth"**.
3. En **Tipo de aplicación**, selecciona **"Aplicación de escritorio"** (Desktop app) o "Aplicación web" según como lo tengas manejado en tu código local. (Normalmente para scripts locales se usa *App de escritorio*).
4. Ponle un nombre (ej. `Agente Local`).
5. Haz clic en **Crear**.
6. Aparecerá una ventana emergente. Haz clic en **DESCARGAR JSON** para obtener el archivo con el secreto de cliente.
7. Guarda ese archivo en tu computadora y **renómbralo a `credentials.json`**.
8. Mueve o copia el `credentials.json` a la **carpeta raíz de tu proyecto local** (`c:\Users\ANDREY\OneDrive\Escritorio\event-driven-alerts\`).

---

## FASE 3: Despliegue a Producción y Pruebas

Ahora que la infraestructura base de Google y el acceso OAuth están listos, ejecutamos tu script.

### 1. Autenticar la CLI Localmente con la Cuenta Nueva
Debes decirle a tu terminal que ahora operará bajo la nueva cuenta de Google, no la vieja.
Abre tu consola/terminal y ejecuta:
```bash
gcloud auth login
```
*Se abrirá el navegador. Inicia sesión y autoriza con tu CUENTA NUEVA.*

```bash
gcloud auth application-default login
```
*Haz lo mismo para autorizar las Application Default Credentials en la nueva cuenta.*

### 2. Ejecutar el Script de Despliegue Automático
1. En tu terminal, asegúrate de estar en la carpeta raíz del proyecto.
2. Ejecuta el script pasándole el **ID del Proyecto** que creaste en el paso 2:
```bash
bash scripts/setup_gcp.sh TUID_DE_PROYECTO_AQUI
```
*Sigue las instrucciones en pantalla (vincular billing si el script lo pide, ingresar las contraseñas necesarias).*

### 3. Verificación de Funcionamiento (Scraping e Integración)
1. **Generar Token (Si aplica):** Si tu agente requiere generar un `token.json` local primero, corre el script principal una vez en local (`python main.py`) para que se abra la ventana de autorización y se guarde el token antes de subirlo, o verifica que la Cloud Function lo maneje adecuadamente.
2. **Forzar ejecución del Agente en la Nube:**
   Ve a **Cloud Scheduler** en la consola de Google Cloud, busca el trabajo `weekly-ingestion-job`, haz clic en los 3 puntos y luego en **"Forzar ejecución"** (Force run).
3. **Revisar Logs:**
   Ve a **Cloud Functions** y luego a **Registros (Logs)** para confirmar que el scraping ha iniciado correctamente, no hay errores de autenticación y se envían los datos/alertas como se espera.
