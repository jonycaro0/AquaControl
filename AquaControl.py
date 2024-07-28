#Librerias de USO
import network, time, urequests, sys 
import ujson
from utelegram import Bot
from machine import Pin, ADC, PWM, Timer
from dht import DHT11, DHT22
from umqtt.simple import MQTTClient
from utelegram import Bot

#token Bot Telegram
TOKEN = "7294517075:AAHK22ReiHyk7rYxhBcUVpclz2bdHCyigAs"
bot = Bot(TOKEN)

chat_ids = ['1508466632', '7487460221']


MQTT_CLIENT_ID 	= "HBUhHTkFAgAXCCwAEBEpGww"
MQTT_SERVER 	= "mqtt3.thingspeak.com"
MQTT_PORT       = 1883
MQTT_TOPIC      = "channels/2553589/publish"
MQTT_USER 		= "HBUhHTkFAgAXCCwAEBEpGww"
MQTT_PASSWORD	= "qdQNyNDvABtyVg/fRdQMb2ed"
MQTT_TOPIC 		= "channels/2610638/publish/"
UPDATE_TIME_INTERVAL = 5000

#Conexion Wifi
def conectaWifi(red, password):
    global miRed
    miRed = network.WLAN(network.STA_IF)
    if not miRed.isconnected():
        miRed.active(True)
        miRed.connect(red, password)
        print('Conectado a la red', red +"..")
        timeout= time.time ()
        while not miRed.isconnected():
            if (time.ticks_diff (time.time (), timeout) > 10):
                return False
    return True
                
if conectaWifi ("FAMILIA_LOPEZ","Toreto2020*"):
    print ("Conexion Exitosa!")
    print ('Datos de la red (IP/netmask/gw/DNS):', miRed.ifconfig())
    
    #conexion MQTT            
    print("Connecting to MQTT server.... ", end="")
    client = MQTTClient(MQTT_CLIENT_ID, MQTT_SERVER, port=MQTT_PORT, user=MQTT_USER, password=MQTT_PASSWORD, keepalive=60)
    try:
        client.connect(clean_session=True)
        print("Connected!")
    except Exception as e:
        print("Failed to connect to MQTT server:", e)


    adc = ADC(Pin(34)) 
    adc.width(ADC.WIDTH_12BIT)
    adc.atten(ADC.ATTN_11DB)

    led = PWM(Pin(2), freq=5000)
    rele = Pin(13, Pin.OUT)
    
    rele.value(1)
    print("Rele Encendido")
    
    
    
    time.sleep(5)
    
    flow_sensor_pin = Pin(14, Pin.IN, Pin.PULL_UP)

    # Variables globales
    pulse_count = 0
    flow_rate = 0
    flow_milliliters = 0
    previous_time = time.ticks_ms()
    counter =0
    stop_program = False

    # Función de interrupción para contar los pulsos
    def pulse_counter(pin):
        global pulse_count
        pulse_count += 1

    # Configuración de la interrupción en el pin del sensor
    flow_sensor_pin.irq(trigger=Pin.IRQ_RISING, handler=pulse_counter)
    
    # Función para calcular el flujo de agua
    def calculate_flow_rate(timer):
        
        
        global pulse_count, flow_rate, flow_milliliters, previous_time, counter, stop_program
        
        current_time = time.ticks_ms()
        elapsed_time = time.ticks_diff(current_time, previous_time)
        previous_time = current_time
        
        last_update = time.ticks_ms()


        
        # YFS201 genera 450 pulsos por litro
        pulses_per_liter = 450.0
        pulses_per_milliliter = pulses_per_liter / 1000.0
        
        # Calcula el flujo de agua en mililitros por segundo
        flow_rate = (pulse_count / pulses_per_milliliter) / (elapsed_time / 1000.0)
        
        # Calcula el volumen de agua en mililitros
        flow_milliliters += pulse_count / pulses_per_milliliter
        
        # Reinicia el contador de pulsos
        pulse_count = 0
        estado=rele.value()
        Estado_Tuberia = estado
        print("Flujo de agua: {:.2f} mL/s, Volumen total: {:.2f} mL y el estado es {:.2f}".format(flow_rate, flow_milliliters, estado))
        payload = f"field1={flow_rate}&field2={Estado_Tuberia}&field3={flow_milliliters}"
        try:
            if not client.connect(clean_session=False):
                print("Reconnected to MQTT server")
            client.publish(MQTT_TOPIC, payload)
            client.disconnect()

            print("Published payload:", payload)
        except Exception as e:
            print("Failed to publish to MQTT server:", e)
        #Si el flujo es bajo (<10) detenga el flujo de Agua y envie una notificacion a el Bot de Telegram
        if flow_rate <= 10:
            rele.value(0)
            men = "Se detecto Fuga de Agua y se cerro el Flujo de agua: mL/s"
            for elemento in chat_ids:
                bot.send_message(elemento, men)
            stop_program = True
            print ("Se detecto Fuga de Agua y perdida de Presion!")
            
            


    # Configuración de un temporizador para calcular el flujo de agua cada segundo
    timer = Timer(0)
    timer.init(period=1000, mode=Timer.PERIODIC, callback=calculate_flow_rate)

    # Bucle principal
    try:
        while True:
            if stop_program:
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("Medición detenida")
        
    finally:
        timer.deinit()
        rele.value(0)
            




