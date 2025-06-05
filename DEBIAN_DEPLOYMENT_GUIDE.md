# Guía de Despliegue en Servidor Debian

Esta guía proporciona instrucciones detalladas para desplegar el bot de trading de Hyperliquid en un servidor Debian.

## Requisitos del Sistema

- Debian 10 (Buster) o superior
- Python 3.8 o superior
- Acceso SSH al servidor
- Conexión a Internet estable
- Cuenta en Hyperliquid con fondos en la cuenta spot

## 1. Preparación del Servidor

### Actualizar el Sistema

```bash
sudo apt update
sudo apt upgrade -y
```

### Instalar Dependencias del Sistema

```bash
sudo apt install -y python3 python3-pip python3-venv git screen htop
```

## 2. Configuración del Entorno

### Crear Directorio para el Bot

```bash
mkdir -p ~/hyperliquid_bot
cd ~/hyperliquid_bot
```

### Extraer Archivos del Bot

Sube el archivo ZIP del bot al servidor y extráelo:

```bash
unzip hyperliquid_bot_final_with_test_20usdc.zip -d .
```

### Crear Entorno Virtual

```bash
python3 -m venv venv
source venv/bin/activate
```

### Instalar Dependencias de Python

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## 3. Configuración del Bot

### Editar Archivo de Configuración

Edita el archivo de configuración con tus credenciales:

```bash
nano config/config.json
```

Asegúrate de actualizar los siguientes campos:

```json
{
    "auth": {
        "account_address": "TU_DIRECCIÓN_DE_CUENTA",
        "secret_key": "TU_CLAVE_SECRETA"
    }
}
```

Para operar en mainnet, asegúrate de que la URL base esté configurada correctamente:

```json
{
    "general": {
        "base_url": "https://api.hyperliquid.xyz",
        "ws_url": "wss://api.hyperliquid.xyz/ws"
    }
}
```

## 4. Transferencia de Fondos y Prueba Inicial

### IMPORTANTE: Transferir Fondos de Spot a Perpetual

Antes de ejecutar el bot o el script de prueba, debes asegurarte de tener fondos en tu cuenta perpetual. Hyperliquid mantiene los fondos en dos cuentas separadas:

1. **Cuenta Spot**: Donde depositas inicialmente tus fondos
2. **Cuenta Perpetual**: Donde se realizan las operaciones de trading

Puedes transferir fondos de spot a perpetual utilizando el script de prueba con el parámetro `--transfer`:

```bash
# Activar el entorno virtual si no está activado
source venv/bin/activate

# Transferir 25 USDC de spot a perpetual
python test_trade.py --transfer 25
```

También puedes realizar esta transferencia a través de la interfaz web de Hyperliquid.

### Ejecutar el Script de Prueba

El script `test_trade.py` te permite abrir una posición de prueba de 20 USDC y cerrarla automáticamente después de un tiempo determinado:

```bash
# Activar el entorno virtual si no está activado
source venv/bin/activate

# Ejecutar el script con posición LONG (por defecto)
python test_trade.py

# O especificar opciones:
python test_trade.py --type long --time 60  # Posición larga, mantener 60 segundos
python test_trade.py --type short --time 30  # Posición corta, mantener 30 segundos
```

El script verificará automáticamente si hay fondos suficientes en tu cuenta perpetual y, si es necesario, intentará transferir fondos desde tu cuenta spot. Si no hay fondos suficientes en ninguna cuenta, el script mostrará un mensaje de error.

El script mostrará información detallada sobre:
- El saldo de tu cuenta antes y después de la operación
- Los detalles de la orden de apertura
- Los detalles de la orden de cierre
- Cualquier error que pueda ocurrir durante el proceso

### Verificar Resultados de la Prueba

Después de ejecutar el script de prueba, verifica los siguientes aspectos:

1. **Conexión a la API**: Confirma que el bot puede conectarse correctamente a la API de Hyperliquid.
2. **Autenticación**: Verifica que las credenciales son correctas y permiten realizar operaciones.
3. **Fondos en cuenta perpetual**: Asegúrate de que tienes fondos suficientes en la cuenta perpetual.
4. **Ejecución de órdenes**: Comprueba que las órdenes se ejecutan correctamente.
5. **Cierre de posiciones**: Asegúrate de que las posiciones se cierran correctamente.
6. **Saldo de la cuenta**: Verifica que el saldo se muestra correctamente antes y después de la operación.

## 5. Ejecución del Bot Principal

Una vez que hayas verificado que la configuración es correcta con el script de prueba, puedes ejecutar el bot principal:

### Prueba en Modo Test

```bash
python src/main.py --test
```

Si todo está configurado correctamente, deberías ver mensajes de log indicando que el bot se ha inicializado y está analizando el mercado.

### Ejecución en Segundo Plano con Screen

Para ejecutar el bot en segundo plano y que siga funcionando después de cerrar la sesión SSH:

```bash
screen -S hyperliquid_bot
source venv/bin/activate
python src/main.py
```

Para desconectarte de la sesión de screen sin detener el bot, presiona `Ctrl+A` seguido de `D`.

Para reconectar a la sesión:

```bash
screen -r hyperliquid_bot
```

## 6. Configuración como Servicio Systemd

Para una ejecución más robusta, puedes configurar el bot como un servicio systemd:

### Crear Archivo de Servicio

```bash
sudo nano /etc/systemd/system/hyperliquid-bot.service
```

Añade el siguiente contenido (ajusta las rutas según tu configuración):

```
[Unit]
Description=Hyperliquid Trading Bot
After=network.target

[Service]
Type=simple
User=tu_usuario
WorkingDirectory=/home/tu_usuario/hyperliquid_bot
ExecStart=/home/tu_usuario/hyperliquid_bot/venv/bin/python /home/tu_usuario/hyperliquid_bot/src/main.py
Restart=on-failure
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=hyperliquid-bot

[Install]
WantedBy=multi-user.target
```

Reemplaza `tu_usuario` con tu nombre de usuario en el servidor.

### Habilitar y Iniciar el Servicio

```bash
sudo systemctl daemon-reload
sudo systemctl enable hyperliquid-bot
sudo systemctl start hyperliquid-bot
```

### Verificar Estado del Servicio

```bash
sudo systemctl status hyperliquid-bot
```

### Ver Logs del Servicio

```bash
sudo journalctl -u hyperliquid-bot -f
```

## 7. Monitoreo y Mantenimiento

### Verificar Logs

Los logs del bot se guardan en el directorio `logs`:

```bash
tail -f logs/bot.log
```

### Monitorear Datos OHLC

El bot obtiene datos OHLC directamente desde la API de Hyperliquid, lo que garantiza la máxima precisión y fiabilidad para las operaciones de trading. Puedes verificar la obtención de datos revisando los logs:

```bash
grep "datos OHLC" logs/bot.log
```

### Actualizar el Bot

Para actualizar el bot con una nueva versión:

1. Detén el bot (si está ejecutándose como servicio: `sudo systemctl stop hyperliquid-bot`)
2. Haz una copia de seguridad de tu configuración: `cp config/config.json config/config.json.backup`
3. Extrae los nuevos archivos
4. Restaura tu configuración si es necesario: `cp config/config.json.backup config/config.json`
5. Reinicia el bot: `sudo systemctl start hyperliquid-bot`

## 8. Solución de Problemas

### Problema: Error de Dependencias

Si encuentras errores relacionados con módulos faltantes:

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Problema: Error de Conexión a la API

Verifica que las URLs en el archivo de configuración sean correctas y que tu conexión a Internet funcione correctamente.

### Problema: Error de Autenticación

Asegúrate de que la dirección de la cuenta y la clave secreta en el archivo de configuración sean correctas.

### Problema: Fondos Insuficientes

Si recibes errores relacionados con fondos insuficientes:

1. Verifica que tienes fondos en tu cuenta spot de Hyperliquid
2. Transfiere fondos de spot a perpetual:
   ```bash
   python test_trade.py --transfer 25
   ```
3. Verifica que la transferencia se haya completado correctamente
4. Si el problema persiste, verifica manualmente en la interfaz web de Hyperliquid

### Problema: Datos OHLC No Disponibles

Si el bot no puede obtener datos OHLC desde la API de Hyperliquid:

1. Verifica tu conexión a Internet
2. Asegúrate de que no hay restricciones de firewall que bloqueen las conexiones a la API
3. Revisa los logs para identificar el error específico
4. El bot utilizará datos en caché si están disponibles, o generará datos simulados como último recurso

### Problema: Error en el Script de Prueba

Si el script de prueba falla al abrir o cerrar posiciones:

1. Verifica que tienes fondos suficientes en tu cuenta perpetual
2. Comprueba que las credenciales son correctas
3. Asegúrate de que el mercado está abierto y operativo
4. Revisa los logs para identificar el error específico

## 9. Consideraciones de Seguridad

### Protección de Claves Privadas

La clave privada en `config.json` debe protegerse adecuadamente:

```bash
chmod 600 config/config.json
```

### Firewall

Configura un firewall para proteger tu servidor:

```bash
sudo apt install -y ufw
sudo ufw allow ssh
sudo ufw enable
```

### Actualizaciones Regulares

Mantén tu sistema actualizado:

```bash
sudo apt update && sudo apt upgrade -y
```

### Operaciones de Prueba

Cuando realices pruebas con el script `test_trade.py`:

1. Comienza con operaciones pequeñas (el script usa 20 USDC por defecto)
2. Verifica que las operaciones se cierren correctamente
3. Monitorea los logs para detectar cualquier error
4. Asegúrate de tener suficientes fondos en tu cuenta

## 10. Contacto y Soporte

Si encuentras problemas o necesitas ayuda adicional, consulta la documentación o contacta al soporte técnico.

---

**Nota importante**: Este bot opera con fondos reales en mainnet. Asegúrate de entender completamente su funcionamiento antes de utilizarlo con cantidades significativas. Comienza con pequeñas cantidades para probar el sistema.
