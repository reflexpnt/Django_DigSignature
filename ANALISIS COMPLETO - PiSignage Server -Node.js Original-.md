# **ANÁLISIS COMPLETO \- PiSignage Server (Node.js Original)**

## **📊 INFORMACIÓN BASADA EN EL REPOSITORIO ANALIZADO**

### **Stack Tecnológico Confirmado:**

* **Backend**: Node.js \+ Express.js 4.16.4+  
* **Base de Datos**: MongoDB con Mongoose 5.13.20  
* **Templates**: Pug 3.0.2 (Motor de plantillas server-side)  
* **Comunicación**: Socket.io 0.9.x (versión custom)  
* **Media Processing**: FFmpeg \+ ImageMagick (GraphicsMagick)  
* **Autenticación**: HTTP-Auth 4.1.9 (credentials: pi:pi por defecto)

### **Arquitectura de Archivos (Inferida):**

pisignage-server/  
├── app/  
│   ├── controllers/     \# Lógica de negocio  
│   ├── models/          \# Esquemas MongoDB/Mongoose    
│   ├── routes/          \# Definición de rutas  
│   └── views/           \# Templates Pug  
├── public/  
│   └── app/  
│       ├── partials/    \# Fragmentos de UI Angular  
│       └── templates/   \# Templates del frontend  
├── config/  
│   └── env/            \# Configuraciones por ambiente  
├── media/              \# Almacenamiento de assets

└── data/               \# Base de datos MongoDB

## **🏗️ ENTIDADES PRINCIPALES DEL SISTEMA**

### **1\. Players (Dispositivos)**

javascript  
*// Campos principales inferidos:*  
{  
  deviceId: String,        *// Identificador único*  
  name: String,  
  groupId: ObjectId,       *// Referencia a Group*  
  status: String,          *// online/offline/error*  
  lastSeen: Date,  
  currentPlaylist: String,  
  resolution: String,      *// 1080p/720p*  
  orientation: String,     *// landscape/portrait*  
  ipAddress: String,  
  macAddress: String,  
  location: String,  
  version: String          *// Versión del software*

}

### **2\. Groups (Grupos)**

javascript  
*// Configuración por grupos:*  
{  
  name: String,  
  description: String,  
  defaultPlaylist: ObjectId,  
  playlists: \[ObjectId\],   *// Array de playlists*  
  settings: {  
    resolution: String,    *// 1080p/720p*  
    orientation: String,   *// landscape/portrait*  
    syncInterval: Number,  
    audioEnabled: Boolean,  
    tvControl: Boolean     *// CEC control*  
  },  
  loadPlaylistOnConnect: Boolean

}

### **3\. Assets (Contenido Multimedia)**

javascript  
*// Tipos de assets soportados:*  
{  
  name: String,  
  filename: String,  
  originalName: String,  
  path: String,  
  type: String,            *// video/image/html/link/rss*  
  size: Number,  
  duration: Number,        *// Para videos*  
  resolution: String,      *// Para videos/imágenes*  
  thumbnail: String,       *// Path al thumbnail*  
  labels: \[String\],        *// Etiquetas para organización*  
  metadata: {  
    codec: String,  
    bitrate: Number,  
    fps: Number  
  },  
  uploadDate: Date

}

### **4\. Playlists**

javascript  
*// Estructura de playlists:*  
{  
  name: String,  
  layout: String,          *// "1", "2a", "2b", "3a", "3b", "4", "4b", "2ab"*  
  isAdvertisement: Boolean,  
  adInterval: Number,      *// Para playlists de anuncios*  
  assets: \[{  
    assetId: ObjectId,  
    duration: Number,      *// Duración de reproducción*  
    zone: String,          *// "main", "side", "bottom", "zone4"*  
    order: Number,  
    transition: String  
  }\],  
  ticker: {  
    enabled: Boolean,  
    text: String,  
    speed: Number,  
    position: String       *// "bottom"*  
  },  
  shuffle: Boolean,  
  repeat: Boolean

}

### **5\. Layouts Predefinidos**

Basándome en la documentación, los layouts son:

* **Layout 1**: Pantalla completa  
* **Layout 2a**: Principal \+ zona lateral  
* **Layout 2b**: Principal \+ zona inferior  
* **Layout 3a**: Principal \+ 2 zonas laterales  
* **Layout 3b**: Principal \+ lateral \+ inferior  
* **Layout 4**: 4 cuadrantes  
* **Layout 4b**: Principal \+ 3 zonas pequeñas  
* **Layout 2ab**: Principal \+ lateral \+ inferior  
* **Custom**: Layouts personalizados con HTML/CSS

## **📡 APIS Y COMUNICACIÓN**

### **WebSocket Events (Socket.io):**

javascript  
*// Eventos principales:*  
'player-connected'     *// Player se conecta*  
'player-disconnected'  *// Player se desconecta*  
'playlist-change'      *// Cambio de playlist*  
'sync-request'         *// Solicitud de sincronización*  
'emergency-message'    *// Mensaje de emergencia*  
'group-ticker'         *// Ticker del grupo*

'system-command'       *// Comandos del sistema (reboot, etc.)*

### **REST Endpoints (Inferidos):**

javascript  
*// Assets*  
GET    /assets              *// Lista de assets*  
POST   /assets              *// Subir asset*  
DELETE /assets/:id          *// Eliminar asset*  
GET    /assets/:id/download *// Descargar asset*

*// Playlists*    
GET    /playlists           *// Lista de playlists*  
POST   /playlists           *// Crear playlist*  
PUT    /playlists/:id       *// Actualizar playlist*  
DELETE /playlists/:id       *// Eliminar playlist*

*// Groups*  
GET    /groups              *// Lista de grupos*  
POST   /groups              *// Crear grupo*  
PUT    /groups/:id          *// Actualizar grupo*  
POST   /groups/:id/deploy   *// Desplegar a grupo*

*// Players*  
GET    /players             *// Lista de players*  
PUT    /players/:id         *// Actualizar player*  
POST   /players/:id/sync    *// Sincronizar player*  
POST   /players/:id/shell   *// Comando shell remoto*

GET    /players/:id/snapshot *// Captura de pantalla*

## **🔄 LÓGICA DE SINCRONIZACIÓN**

### **Proceso de Sync (WebSocket):**

1. **Player conecta** → Envía handshake con device info  
2. **Server valida** → Comprueba licencia y registro  
3. **Sync check** → Compara versiones de playlist/assets  
4. **Download list** → Envía lista de assets a descargar  
5. **Progressive download** → Player descarga assets incrementalmente  
6. **Confirmation** → Player confirma descarga y aplicación

### **Datos de Sincronización:**

javascript  
*// Mensaje de sync enviado al player:*  
{  
  playlists: \[{  
    id: "playlist\_id",  
    name: "playlist\_name",   
    layout: "1",  
    assets: \[{  
      id: "asset\_id",  
      name: "video.mp4",  
      duration: 30,  
      zone: "main",  
      order: 1  
    }\]  
  }\],  
  assets: \[{  
    id: "asset\_id",  
    name: "video.mp4",  
    url: "/media/video.mp4",  
    checksum: "sha256hash",  
    size: 15728640  
  }\],  
  settings: {  
    resolution: "1080p",  
    orientation: "landscape"  
  }

}

## **🎯 FUNCIONALIDADES CONFIRMADAS**

### **Asset Management:**

* ✅ Upload multiformato (video, imagen, HTML, audio, links)  
* ✅ Conversión automática de video a MP4 (FFmpeg)  
* ✅ Generación de thumbnails (ImageMagick)  
* ✅ Sistema de etiquetas (labels)  
* ✅ Metadata extraction (duración, resolución, codec)

### **Playlist Management:**

* ✅ Drag & drop asset ordering  
* ✅ Multiple layout support (8 layouts predefinidos)  
* ✅ Ticker integration (texto estático o RSS)  
* ✅ Advertisement playlists con intervalos  
* ✅ Zone-specific content (main, side, bottom)

### **Group & Player Management:**

* ✅ Auto-discovery de players en red  
* ✅ Group-based configuration  
* ✅ Remote control (shell, screenshot, reboot)  
* ✅ Real-time monitoring  
* ✅ License management

### **Communication:**

* ✅ WebSocket real-time communication  
* ✅ Progressive asset download  
* ✅ Emergency messaging  
* ✅ Offline capability con fallback

## **🔧 CONFIGURACIONES IMPORTANTES**

### **Media Processing:**

* **FFmpeg**: Conversión de video a MP4 H.264  
* **ImageMagick**: Thumbnails y procesamiento de imágenes  
* **Formatos soportados**: MP4, AVI, MOV, JPG, PNG, PDF, HTML, ZIP, MP3  
* **Directorios**: `../media/` y `../media/_thumbnails`

### **Network & Deployment:**

* **Puerto por defecto**: 3000  
* **Autenticación**: HTTP Basic Auth (pi:pi)  
* **WebSocket**: Socket.io 0.9.x custom  
* **Auto-discovery**: Broadcast en subnet local

---

## **🎯 CONCLUSIÓN PARA EL PORT DJANGO**

Con esta información confirmada, ahora tengo una base sólida para implementar:

1. **Modelos Django** equivalentes a los esquemas MongoDB  
2. **APIs REST** que repliquen la funcionalidad sin WebSockets  
3. **Media processing** con las mismas capacidades  
4. **Layout system** con los 8 layouts predefinidos  
5. **Sync logic** basada en hash comparison  
6. **PyQt6 simulator** que implemente el comportamiento del player

