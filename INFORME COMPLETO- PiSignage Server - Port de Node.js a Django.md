# **INFORME COMPLETO: PiSignage Server \- Port de Node.js a Django**

## **🎯 RESUMEN EJECUTIVO**

Este proyecto es un **port completo** del sistema PiSignage Server desde **Node.js** a **Django/Python**, manteniendo la funcionalidad core pero **eliminando WebSockets** y reemplazándolos con un sistema de polling basado en **APIs REST** y **JSON**.

## **📚 ORIGEN Y CONTEXTO**

### **Proyecto Original: PiSignage Server (Node.js)**

* **Repositorio**: [https://github.com/colloqi/pisignage-server.git](https://github.com/colloqi/pisignage-server.git)  
* **Tecnología**: Node.js \+ Express \+ MongoDB \+ Socket.io \+ Pug  
* **Propósito**: Sistema de señalización digital para gestionar reproductores Raspberry Pi  
* **Comunicación**: WebSockets en tiempo real  
* **Arquitectura**: Servidor centralizado \+ Dispositivos Raspberry Pi

### **Motivación del Port**

* **Lenguaje preferido**: Python/Django vs Node.js  
* **Simplificación**: Eliminar WebSockets complejos  
* **Dispositivos target**: Android tablets en lugar de solo Raspberry Pi  
* **Mantenibilidad**: Django Admin para gestión vs interfaces custom

## **🏗️ ARQUITECTURA DEL SISTEMA DJANGO**

### **Stack Tecnológico**

* **Backend**: Django 5.2.1 \+ Python  
* **Base de Datos**: SQLite (desarrollo) / PostgreSQL (producción)  
* **Frontend**: Django Templates \+ Bootstrap \+ HTMX  
* **Comunicación**: REST APIs \+ JSON (sin WebSockets)  
* **Dispositivos**: Android tablets con app Kotlin

### **Apps Django Implementadas**

DigSignature\_server/  
├── core/          \# Dashboard y configuración global  
├── players/       \# Gestión de dispositivos y grupos  
├── content/       \# Assets, layouts y contenido multimedia  
├── playlists/     \# Listas de reproducción

└── scheduling/    \# Programación y despliegues

## **📱 SISTEMA DE COMUNICACIÓN (REEMPLAZO DE WEBSOCKETS)**

### **Estrategia de Sincronización**

En lugar de WebSockets en tiempo real, implementamos:

1. **Polling periódico** desde dispositivos Android  
2. **Hash-based sync detection** para optimizar transferencias  
3. **APIs REST** para todas las comunicaciones  
4. **Batch processing** para logs y datos

### **Flujo de Sincronización**

1\. Device → check\_server API (cada X segundos)  
2\. Server calcula hash de contenido actual  
3\. Si hash ≠ último hash del device → needs\_sync \= true  
4\. Server envía datos completos de sincronización

5\. Device descarga assets y actualiza estado local

## **🔧 MODELOS DE DATOS PRINCIPALES**

### **Player Model (Dispositivos)**

python  
\- device\_id: 16 caracteres hexadecimales (identificador único)  
\- name: Nombre descriptivo  
\- group: Grupo al que pertenece  
\- status: online/offline/error/syncing  
\- last\_sync: Última sincronización exitosa  
\- last\_sync\_hash: Hash SHA256 para detectar cambios  
\- app\_version: Versión de la app Android  
\- firmware\_version: Versión Android  
\- battery\_level: Nivel de batería (0\-100)  
\- storage\_free\_mb: Almacenamiento libre en MB  
\- temperature\_celsius: Temperatura del dispositivo  
\- connection\_type: wifi/mobile/ethernet  
\- signal\_strength: Fuerza de señal en dBm  
\- custom\_resolution: Resolución específica del device  
\- custom\_orientation: Orientación específica del device

\- timezone: Zona horaria del dispositivo

### **Group Model (Grupos de Dispositivos)**

python  
\- name: Nombre del grupo  
\- default\_playlist: Playlist por defecto  
\- sync\_interval: Intervalo de sincronización (segundos)  
\- resolution: 1920x1080, 1280x720, etc.  
\- orientation: landscape/portrait  
\- audio\_enabled: Habilitar audio

\- tv\_control: Control CEC de TV

### **DeviceLog Model (Logging Centralizado)**

python  
\- player: Relación con Player  
\- device\_timestamp: Timestamp del dispositivo  
\- level: VERBOSE/DEBUG/INFO/WARN/ERROR/FATAL  
\- category: SYSTEM/SYNC/PLAYBACK/NETWORK/STORAGE/UI/HARDWARE/APP  
\- tag: Tag del log (como Android Log.tag)  
\- message: Mensaje del log  
\- thread\_name: Hilo que generó el log  
\- method\_name: Método donde ocurrió  
\- line\_number: Línea de código  
\- exception\_class: Clase de excepción si existe  
\- stack\_trace: Stack trace completo

\- extra\_data: JSON con datos adicionales

## **📡 APIS REST IMPLEMENTADAS**

### **1\. Device Check Server API**

**Endpoint**: `POST /scheduling/api/v1/device/check_server/`

**Request JSON**:

json  
{  
    "action": "check\_server",  
    "device\_id": "A1B2C3D4E5F6G7H8",  
    "last\_sync\_hash": "abc123def456...",  
    "app\_version": "1.2.3",  
    "firmware\_version": "12",  
    "battery\_level": 85,  
    "storage\_free\_mb": 2048,  
    "connection\_type": "wifi",  
    "device\_health": {  
        "temperature\_celsius": 38,  
        "signal\_strength": \-45  
    }

}

**Response JSON (Sync Needed)**:

json  
{  
    "status": "success",  
    "server\_timestamp": "2024-01-15T10:30:05Z",  
    "device\_registered": true,  
    "needs\_sync": true,  
    "sync\_data": {  
        "sync\_id": "sync\_20240115\_103005",  
        "new\_sync\_hash": "def456ghi789...",  
        "playlists": \[  
            {  
                "id": "playlist\_123",  
                "name": "welcome\_playlist\_v3",  
                "layout": "single\_zone",  
                "active": true,  
                "items": \[  
                    {  
                        "id": 1,  
                        "asset\_id": "video\_001",  
                        "duration": 30,  
                        "zone": "main",  
                        "order": 1  
                    }  
                \]  
            }  
        \],  
        "assets": \[  
            {  
                "id": "video\_001",  
                "name": "welcome\_video\_v2.mp4",  
                "type": "video",  
                "url": "/api/v1/assets/video\_001/download/",  
                "checksum": "sha256:abc123def456...",  
                "size\_bytes": 15728640,  
                "metadata": {  
                    "duration": 30,  
                    "resolution": "1920x1080"  
                }  
            }  
        \],  
        "deleted\_assets": \["old\_video\_001"\]  
    }

}

**Response JSON (No Sync Needed)**:

json  
{  
    "status": "success",  
    "server\_timestamp": "2024-01-15T10:30:05Z",  
    "device\_registered": true,  
    "needs\_sync": false,  
    "next\_check\_interval": 300

}

### **2\. Device Registration API**

**Endpoint**: `POST /players/api/register/`

**Request JSON**:

json  
{  
    "device\_id": "A1B2C3D4E5F6G7H8",  
    "name": "Test Player 1",  
    "app\_version": "1.0.0",  
    "firmware\_version": "12"

}

### **3\. Device Logging API**

#### **Single Log**

**Endpoint**: `POST /players/api/logs/single/`

**Request JSON**:

json  
{  
    "device\_id": "A1B2C3D4E5F6G7H8",  
    "timestamp": "2025-07-24T17:10:00.000Z",  
    "level": "ERROR",  
    "category": "PLAYBACK",  
    "tag": "VideoPlayer",  
    "message": "Failed to load video",  
    "exception\_class": "IOException",  
    "stack\_trace": "java.io.IOException: Connection timeout\\n\\tat VideoPlayer.load(123)",  
    "thread\_name": "MainThread",  
    "method\_name": "loadVideo",  
    "line\_number": 123,  
    "extra\_data": {"video\_url": "http://example.com/video.mp4"}

}

#### **Batch Logs**

**Endpoint**: `POST /players/api/logs/batch/`

**Request JSON**:

json  
{  
    "device\_id": "A1B2C3D4E5F6G7H8",  
    "app\_version": "1.0.0",  
    "logs": \[  
        {  
            "timestamp": "2025-07-24T17:10:00.000Z",  
            "level": "INFO",  
            "category": "SYNC",  
            "tag": "SyncManager",  
            "message": "Starting sync process"  
        },  
        {  
            "timestamp": "2025-07-24T17:10:05.000Z",  
            "level": "ERROR",  
            "category": "NETWORK",  
            "tag": "NetworkManager",  
            "message": "Connection failed"  
        }  
    \],  
    "device\_context": {  
        "battery\_level": 85,  
        "memory\_available\_mb": 1024  
    }

}

## **🎨 INTERFAZ DE ADMINISTRACIÓN**

### **Django Admin Customizado**

* **Rich dashboard** con estado en tiempo real  
* **Color coding** para estados de dispositivos  
* **Filtros avanzados** por grupo, estado, versión  
* **Acciones bulk** (reset sync, force offline, etc.)  
* **Health monitoring** visual (batería, temperatura, señal)

### **Vista Terminal de Logs**

* **URL**: `/players/{device_id}/logs/`  
* **Estilo terminal** con colores y símbolos  
* **Auto-refresh** cada 30 segundos  
* **Filtros**: nivel, categoría, tiempo, búsqueda  
* **Responsive design** para móviles  
* **Keyboard shortcuts** (Ctrl+R, Ctrl+F, Esc)

## **📋 CARACTERÍSTICAS IMPLEMENTADAS**

### **✅ Completado**

* ✅ Modelos de datos completos (Player, Group, DeviceLog, etc.)  
* ✅ APIs REST para registro y sincronización  
* ✅ Sistema de logging centralizado  
* ✅ Admin interface rica con monitoreo  
* ✅ Vista terminal para logs en tiempo real  
* ✅ Hash-based sync detection  
* ✅ Health monitoring de dispositivos  
* ✅ Gestión de grupos y configuraciones

### **🔄 En Desarrollo / Pendiente**

* 🔄 Content management (assets, layouts)  
* 🔄 Playlist builder y gestión  
* 🔄 Scheduling system  
* 🔄 Asset conversion y thumbnails  
* 🔄 Download APIs para assets  
* 🔄 Emergency commands system

## **🔧 CONFIGURACIÓN TÉCNICA**

### **Settings Django Relevantes**

python  
INSTALLED\_APPS \= \[  
    'core',      *\# Dashboard y configuración*  
    'players',   *\# Gestión de dispositivos*  
    'content',   *\# Assets y contenido*  
    'playlists', *\# Listas de reproducción*  
    'scheduling' *\# Programación*  
\]

*\# Configuración para archivos grandes (videos)*  
FILE\_UPLOAD\_MAX\_MEMORY\_SIZE \= 100 \* 1024 \* 1024  *\# 100MB*

DATA\_UPLOAD\_MAX\_MEMORY\_SIZE \= 500 \* 1024 \* 1024  *\# 500MB*

### **URLs Structure**

/                                    \# Dashboard  
/players/                           \# Lista de dispositivos  
/players/api/register/              \# Registro de dispositivos  
/players/api/logs/single/           \# Log individual  
/players/api/logs/batch/            \# Batch de logs  
/players/{device\_id}/logs/          \# Vista terminal de logs

/scheduling/api/v1/device/check\_server/  \# Check server API

## **🎯 DIFERENCIAS CLAVE CON EL ORIGINAL**

| Aspecto | Node.js Original | Django Port |
| ----- | ----- | ----- |
| **Comunicación** | WebSockets tiempo real | REST APIs \+ Polling |
| **Base de Datos** | MongoDB | SQLite/PostgreSQL |
| **Dispositivos** | Raspberry Pi | Android Tablets |
| **UI Backend** | Pug templates | Django templates |
| **Admin Interface** | Custom built | Django Admin |
| **Logging** | Local files | Centralized DB |
| **Sync Detection** | Push notifications | Hash comparison |
| **Device ID** | Auto-generated | App-generated 16-hex |

## **🚀 PRÓXIMOS PASOS SUGERIDOS**

1. **Completar Content Management**: Assets, layouts, conversión de video  
2. **Implementar Playlist Builder**: Editor visual drag & drop  
3. **Desarrollar Scheduling**: Programación temporal de contenido  
4. **Crear Android App**: Cliente Kotlin para tablets  
5. **Asset Download APIs**: Streaming y descarga progresiva  
6. **Emergency Commands**: Reboot, update, emergency content  
7. **Analytics Dashboard**: Métricas de reproducción y salud  
8. **Multi-tenancy**: Soporte para múltiples instalaciones

## **📝 COMANDOS DE PRUEBA ÚTILES**

### **Registrar dispositivo:**

bash

curl \-X POST "http://localhost:8000/players/api/register/" \-H "Content-Type: application/json" \-d '{"device\_id":"A1B2C3D4E5F6G7H8","name":"Test Player"}'

### **Enviar log:**

bash

curl \-X POST "http://localhost:8000/players/api/logs/single/" \-H "Content-Type: application/json" \-d '{"device\_id":"A1B2C3D4E5F6G7H8","timestamp":"2025-07-24T17:10:00.000Z","level":"INFO","category":"APP","tag":"Test","message":"Hello World"}'

---

Este informe proporciona una visión completa del proyecto, su origen, arquitectura actual y los formatos JSON implementados. El sistema está diseñado para ser escalable, mantenible y fácil de debuggear con un enfoque en simplicidad sobre la complejidad de WebSockets.

