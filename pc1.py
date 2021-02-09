# -*- coding: utf-8 -*-
"""
Created on Fri Nov 20 09:25:08 2020

@author: camil_000
"""
#!/usr/bin/python

import sys
from subprocess import call
import os
from lxml import etree


##### Función ayuda(n): función que enseña los comandos disponibles a usar en este script
def ayuda():
	if(len(sys.argv) > 2):
		nombre = sys.argv[2]
	else:
		nombre = ""

	if(nombre == "crear"):
		print("\nCrea tantas maquinas virtuales como se le especifique con 'crear <NºMáquinas>'")
		print("Si no se especifica ningún número por defecto se crean s1 y s2")
		print("Como máximo se pueden crear hasta 5\n")

	elif(nombre == "arrancar"):
		print("\nArranca todas las máquinas virtuales creadas, o las especificada, con 'arrancar <NºdeMáquinas>'\n")

	elif(nombre == "arrancarmaq"):
		print("\nArranca la máquina virtual especificada, con 'arrancar1 <NombreMaquina>'\n")

	elif(nombre == "parar"):
		print("\nDetiene todas las maquinas virtuales, o las especificadas, con 'parar <NºdeMaquinas>'\n")

	elif(nombre == "pararmaq"):
		print("\nDetiene la maquina virtual especificada, con 'parar1 <NombredeMaquina>'\n")

	elif(nombre == "destruir"):
		print("\nDestruye todas las maquinas virtuales creadas, o la especificada con 'destruir <NombreMáquina>'\n")

    	elif(nombre == "monitor"):
        	print("\nDiferentes estadisticas y comprobaciones de nuestro sistema")
        	print("Opción 'monitor ping máquina' muestra el tráfico del host a la máquina seleccionada")
        	print("Opción 'monitor cpu' muestra los stats de la cpu")
        	print("Opción 'monitor watch' muestra el tamaño de la máquina y los permisos\n")

	else:
		print("\nLos comandos disponibles son 'crear', 'arrancar', 'arrancarmaq, 'parar', 'pararmaq', 'destruir','monitor' y 'ayuda'")	
		print("Si se necesita más información de algun comando en concreto, escribe 'ayuda <comando>' \n")


##### Función crear(num): para crear los ficheros *.qcow2 de diferencias y los de especificación en XML de cada MV, 
##### así como los bridges virtuales que soportan las LAN del escenario

def crear(num):

    # Si no se introduce un tercer parámetro utilizamos por defecto el valor de 2 (se crearán por defecto los servidores s1 y s2)
    if len(sys.argv) == 2:
        num_serv = 2
    else:
        num = sys.argv[2]

    # Guardamos el número de máquinas que se introduce como parámetro
    if((int(num) >= 1) and (int(num) <= 5)):
        num_serv = int(num)
	# Creamos los bridges a las dos redes virtuales
    	os.system("sudo brctl addbr LAN1")
    	os.system("sudo brctl addbr LAN2")
    	os.system("sudo ifconfig LAN1 up")
    	os.system("sudo ifconfig LAN2 up")
    else:
	# Si el parámetro introducido no está entre las posibilidades del programa mostramos mensaje de error.
        sys.exit("ERROR: Valor incorrecto del tercer parámetro")
     
    #Guardamos el número de máquinas en un fichero (pc1.cfg) para que el resto de funciones del script pueda acceder a ellas    
    os.system("touch pc1.cfg")
    os.system("echo "+str(num_serv)+" > pc1.cfg")

    # Creamos el directorio temporal donde vamos a modificar los ficheros que tenemos que actualizar en las maquinas
    os.system("mkdir mnt")
    os.system("mkdir mnt/tmp")

    # Se crean siempre lb y c1
    os.system('chmod 644 cdps-vm-base-pc1.qcow2')
    os.system('qemu-img create -f qcow2 -b cdps-vm-base-pc1.qcow2 lb.qcow2')
    os.system('cp plantilla-vm-pc1.xml lb.xml')
    os.system('qemu-img create -f qcow2 -b cdps-vm-base-pc1.qcow2 c1.qcow2')
    os.system('cp plantilla-vm-pc1.xml c1.xml')

    # Configuracion de C1
    # Cargamos el fichero XML de c1 y obtenemos el nodo raíz
    tree = etree.parse('c1.xml')
    root = tree.getroot()

    # Guardamos en 'aux' el fichero XML que vamos a modificar
    aux = etree.ElementTree(root)

    # Cambiamos el campo nombre
    nameField = root.find("name")
    nameField.text = 'c1'
    
    # Cambiamos el campo source 
    source = root.find("./devices/disk/source")
    source.set("file","/mnt/tmp/pc1/c1.qcow2")

    # Cambiamos el campo bridge
    interfaceSource = root.find("./devices/interface/source")
    interfaceSource.set("bridge" ,"LAN1")

    # Sustituimos el fichero c1.xml por el modificado y lo guardamos con el mismo nombre
    outFile = open('c1.xml', 'w')
    aux.write("outFile")
    os.system("rm c1.xml")
    os.system("mv outFile c1.xml")

    # Definimos la máquina en el gestor
    os.system("sudo virsh define c1.xml")
    # Configuramos el host
    os.system("sudo ifconfig LAN1 10.0.1.3/24")
    os.system("sudo ip route add 10.0.0.0/16 via 10.0.1.1")
    # Creamos el fichero hostname en el que definimos el nombre de la máquina virtual
    os.system("touch ./mnt/tmp/hostname")
    os.system("echo c1 > ./mnt/tmp/hostname")
    # Copiamos el fichero hostname en el directorio /etc de nuestra máquina para actualizar el fichero hostname
    os.system("sudo virt-copy-in -d c1 ./mnt/tmp/hostname /etc")
   
    # Creamos el fichero hosts 
    os.system("touch ./mnt/tmp/hosts")
    # Reescribimos el fichero hosts para asociar la dirección 127.0.1.1 
    n = open('./mnt/tmp/hosts',"w") 	    
    n.write("127.0.1.1 c1\n127.0.0.1 localhost\n::1 ip6-localhost ip6-loopback\nfe00::0 ip6-localnet\nff00::0 ip6-mcastprefix\nff02::1 ip6-allnodes\nff02::2 ip6-allrouters\nff02::3 ip6-allhosts")      		
    n.close()
    # Copiamos el fichero hosts en el directorio /etc de nuestra máquina para actualizar el fichero host
    os.system("sudo virt-copy-in -d c1 ./mnt/tmp/hosts /etc")
	
    # Creamos el fichero interfaces
    os.system("touch ./mnt/tmp/interfaces") 
    # Lo reescribimos para introducir las interfaces correspondientes de nuestra red para c1
    n = open('./mnt/tmp/interfaces',"w") 	    
    n.write("auto lo\niface lo inet loopback\n\nauto eth0\niface eth0 inet dhcp\n\niface eth0 inet static\naddress 10.0.1.2\nnetmask 255.255.255.0\ngateway 10.0.1.1\ndns-nameservers 10.0.1.1 ")      		
    n.close()
    # Copiamos el fichero interfaces en el directorio /etc/network de nuestra máquina para actualizar el fichero interfaces
    os.system("sudo virt-copy-in -d c1 ./mnt/tmp/interfaces /etc/network")

    # Imprimimos por pantalla la creación de C1
    print("Se ha creado C1")
    

    # Configuración de LB
    # Cargamos el fichero XML de lb y obtenemos el nodo raíz
    tree = etree.parse('lb.xml')
    root = tree.getroot()
    
    # Guardamos en 'aux' el fichero XML que vamos a modificar
    aux = etree.ElementTree(root)
    
    # Cambiamos el campo nombre
    nameField = root.find("name")
    nameField.text = 'lb'

    # Cambiamos el campo source
    source = root.find("./devices/disk/source")	
    source.set("file", '/mnt/tmp/pc1/lb.qcow2')

    # Cambiamos el campo bridge
    interfaceSource = root.find("./devices/interface/source")
    interfaceSource.set("bridge", 'LAN1')

    # Creamos la 2ª interfaz de red del balanceador (lb)
    interfaceSource2 = root.find("devices")
    sub_interfaceSource2 = etree.SubElement(interfaceSource2, "interface", type='bridge')
    sub_Source2 = etree.SubElement(sub_interfaceSource2, "source", bridge='LAN2')
    sub_model = etree.SubElement(sub_Source2, "model", type='virtio')

    # Sustituimos el fichero lb.xml por el modificado y lo guardamos con el mismo nombre
    outFile = open('lb.xml', 'w')
    aux.write("outFile")
    os.system("rm lb.xml")
    os.system("mv outFile lb.xml")

    # Definimos la máquina en el gestor
    os.system("sudo virsh define lb.xml")

    # Definimos el nombre de la máquina virtual
    os.system("echo lb > ./mnt/tmp/hostname")

    # Copiamos el fichero hostname en el directorio /etc de nuestra máquina para actualizar el fichero hostname
    os.system("sudo virt-copy-in -d lb ./mnt/tmp/hostname /etc")

    # Reescribimos el fichero hosts para asociar la direccion 127.0.1.1
    n = open('./mnt/tmp/hosts',"w") 	    
    n.write("127.0.1.1 lb\n127.0.0.1 localhost\n::1 ip6-localhost ip6-loopback\nfe00::0 ip6-localnet\nff00::0 ip6-mcastprefix\nff02::1 ip6-allnodes\nff02::2 ip6-allrouters\nff02::3 ip6-allhosts")      		
    n.close()
    # Copiamos el fichero hosts en el directorio /etc de nuestra máquina para actualizar el fichero hosts
    os.system("sudo virt-copy-in -d lb ./mnt/tmp/hosts /etc")

    # Reescribimos el fichero interfaces para introducir las interfaces correspondientes de nuestra red para lb
    n = open('./mnt/tmp/interfaces',"w") 	    
    n.write("auto lo\niface lo inet loopback\n\nauto eth0\niface eth0 inet dhcp\n\niface eth0 inet static\naddress 10.0.1.1\nnetmask 255.255.255.0\ngateway 10.0.1.2\ndns-nameservers 10.0.1.2\n\nauto eth1\niface eth1 inet dhcp\n\niface eth1 inet static\naddress 10.0.2.1\nnetmask 255.255.255.0\ngateway 10.0.2.0\ndns-nameservers 10.0.2.0\n ")      		
    n.close()
    # Copiamos el fichero interfaces en el directorio /etc/network de nuestra máquina para actualizar el fichero interfaces
    os.system("sudo virt-copy-in -d lb ./mnt/tmp/interfaces /etc/network")

    # Edicion del fichero /etc/sysctl.conf para configurar el balanceador como router
    os.system("sudo virt-edit -a lb.qcow2 /etc/sysctl.conf -e 's/#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/'")

    # Imprimimos por pantalla la creación de LB
    print("Se ha creado LB")


    # Creamos servidores depende del nº que indiquemos como tercer parámetro (1-5)
    if ((num_serv >= 1) and (num_serv <= 5)):

	# si el valor introducido es 1 deberemos crear s1
        os.system("qemu-img create -f qcow2 -b cdps-vm-base-pc1.qcow2 s1.qcow2")
        os.system("cp plantilla-vm-pc1.xml s1.xml")

	# Configuración de S1
        # Cargamos el fichero XML de s1 y obtenemos el nodo raíz
        tree = etree.parse('s1.xml')
        root = tree.getroot()
        
        # Guardamos en 'aux' el fichero XML que vamos a modificar
        aux = etree.ElementTree(root)
        
	# Cambiamos el campo nombre
        nameField = root.find("name")
        nameField.text = 's1'

	# Cambiamos el campo source
        source = root.find("./devices/disk/source")	
        source.set("file", '/mnt/tmp/pc1/s1.qcow2')
		
        # Cambiamos el campo bridge
        interfaceSource = root.find("./devices/interface/source")
        interfaceSource.set("bridge", 'LAN2')
        
        # Sustituimos el fichero s1.xml por el modificado y lo guardamos con el mismo nombre
        outFile = open('s1.xml', 'w')
        aux.write("outFile")
        os.system("rm s1.xml")
        os.system("mv outFile s1.xml")

	# Definimos la máquina en el gestor
        os.system("sudo virsh define s1.xml")

	# Definimos el nombre de la máquina virtual s1
	os.system("echo s1 > ./mnt/tmp/hostname")

	# Copiamos el fichero hostname en el directorio /etc de nuestra máquina para actualizar el fichero hostname
	os.system("sudo virt-copy-in -d s1 ./mnt/tmp/hostname /etc")

	# Reescribimos el fichero hosts para asociar la direccion 127.0.1.1
	n = open('./mnt/tmp/hosts',"w") 	    
	n.write("127.0.1.1 s1\n127.0.0.1 localhost\n::1 ip6-localhost ip6-loopback\nfe00::0 ip6-localnet\nff00::0 ip6-mcastprefix\nff02::1 ip6-allnodes\nff02::2 ip6-allrouters\nff02::3 ip6-allhosts")      		
	n.close()
	# Copiamos el fichero hosts en el directorio /etc de nuestra máquina para actualizar el fichero hosts
	os.system("sudo virt-copy-in -d s1 ./mnt/tmp/hosts /etc")

	# Introducimos en index.html el contenido de la página html inicial de la máquina s1
	os.system("echo S1 > ./mnt/tmp/index.html")
	# Copiamos el fichero index.html en el directorio /var/www/html de nuestra máquina para actualizar el fichero index.html
	os.system("sudo virt-copy-in -d s1 ./mnt/tmp/index.html /var/www/html")

	# Reescribimos el fichero interfaces para introducir las interfaces correspondientes de nuestra red para s1
	n = open('./mnt/tmp/interfaces',"w") 	    
	n.write("auto lo\niface lo inet loopback\n\nauto eth0\niface eth0 inet dhcp\n\niface eth0 inet static\naddress 10.0.2.11\nnetmask 255.255.255.0\ngateway 10.0.2.1\ndns-nameservers 10.0.2.1\n ")      		
	n.close()
	# Copiamos el fichero interfaces en el directorio /etc/network de nuestra máquina para actualizar el fichero interfaces
	os.system("sudo virt-copy-in -d s1 ./mnt/tmp/interfaces /etc/network")
        
	# Imprimimos por pantalla la creación de S1
        print("Se ha creado S1")


	# Para un parámetro mayor que 1 deberemos crear además S2 
        if (num_serv >= 2):
            
            os.system("qemu-img create -f qcow2 -b cdps-vm-base-pc1.qcow2 s2.qcow2")
            os.system("cp plantilla-vm-pc1.xml s2.xml")

	    # Configuración de S2
            # Cargamos el fichero XML de s2 y obtenemos el nodo raíz
            tree = etree.parse('s2.xml')
            root = tree.getroot()

            # Guardamos en 'aux' el fichero XML que vamos a modificar       
            aux = etree.ElementTree(root)

            # Cambiamos el campo nombre
            nameField = root.find("name")
            nameField.text = 's2'

	    # Cambiamos el campo source
            source = root.find("./devices/disk/source")	
            source.set("file", 'mnt/tmp/pc1/s2.qcow2')

	    # Cambiamos el campo bridge
            interfaceSource = root.find("./devices/interface/source")
            interfaceSource.set("bridge", 'LAN2')
            
            # Sustituimos el fichero s2.xml por el modificado y lo guardamos con el mismo nombre
            outFile = open('s2.xml', 'w')
            aux.write("outFile")
            os.system("rm s2.xml")
            os.system("mv outFile s2.xml")

	    # Definimos la máquina en el gestor
            os.system("sudo virsh define s2.xml")

	    # Definimos el nombre de la máquina virtual s2
	    os.system("echo s2 > ./mnt/tmp/hostname")

	    # Copiamos el fichero hostname en el directorio /etc de nuestra máquina para actualizar el fichero hostname
	    os.system("sudo virt-copy-in -a s2.qcow2 ./mnt/tmp/hostname /etc")

	    # Reescribimos el fichero hosts para asociar la direccion 127.0.1.1
	    n = open("./mnt/tmp/hosts","w") 	    
	    n.write("127.0.1.1 s2\n127.0.0.1 localhost\n::1 ip6-localhost ip6-loopback\nfe00::0 ip6-localnet\nff00::0 ip6-mcastprefix\nff02::1 ip6-allnodes\nff02::2 ip6-allrouters\nff02::3 ip6-allhosts")      		
	    n.close()
	    # Copiamos el fichero hosts en el directorio /etc de nuestra máquina para actualizar el fichero hosts
	    os.system("sudo virt-copy-in -a s2.qcow2 ./mnt/tmp/hosts /etc")

	    # Introducimos en index.html el contenido de la página html inicial de la máquina s1
	    os.system("echo S2 > ./mnt/tmp/index.html")
            # Copiamos el fichero index.html en el directorio /var/www/html de nuestra maquina para actualizar el fichero index.html de esta
	    os.system("sudo virt-copy-in -a s2.qcow2 ./mnt/tmp/index.html /var/www/html")

	    # Reescribimos el fichero interfaces para introducir las interfaces correspondientes de nuestra red para s2
	    n = open("./mnt/tmp/interfaces","w") 	    
	    n.write("auto lo\niface lo inet loopback\n\nauto eth0\niface eth0 inet dhcp\n\niface eth0 inet static\naddress 10.0.2.12\nnetmask 255.255.255.0\ngateway 10.0.2.1\ndns-nameservers 10.0.2.1\n ")      		
	    n.close()
	    # Copiamos el fichero interfaces en el directorio /etc/network de nuestra máquina para actualizar el fichero interfaces
	    os.system("sudo virt-copy-in -a s2.qcow2 ./mnt/tmp/interfaces /etc/network")

            # Imprimimos por pantalla la creación de S2
            print("Se ha creado S2")


	# Para un parámetro mayor que 2 deberemos crear además S3 
        if (num_serv >= 3):	

            os.system("qemu-img create -f qcow2 -b cdps-vm-base-pc1.qcow2 s3.qcow2")
            os.system("cp plantilla-vm-pc1.xml s3.xml")

	    # Procedemos a cargar el fichero XML de s3 y obtener el nodo raiz
            tree = etree.parse('s3.xml')
            root = tree.getroot()

	    # Guardamos en "aux" el fichero XML que vamos a modificar
            aux = etree.ElementTree(root)

	    # Cambiamos el campo nombre
            nameField = root.find("name")
            nameField.text = 's3'

	    # Cambiamos el campo source
            source = root.find("./devices/disk/source")	
            source.set("file", '/mnt/tmp/pc1/s3.qcow2')

	    # Cambiamos el campo bridge
            interfaceSource = root.find("./devices/interface/source")
            interfaceSource.set("bridge", 'LAN2')
            
            # Sustituimos el fichero s3.xml por el modificado y lo guardamos con el mismo nombre
            outFile = open('s3.xml', 'w')
            aux.write("outFile")
            os.system("rm s3.xml")
            os.system("mv outFile s3.xml")

	    # Definimos la máquina en el gestor
            os.system("sudo virsh define s3.xml")

	    # Definimos el nombre de la máquina virtual s3
	    os.system("echo s3 > ./mnt/tmp/hostname")

	    # Copiamos el fichero hostname en el directorio /etc de nuestra máquina para actualizar el fichero hostname 
	    os.system("sudo virt-copy-in -d s3 ./mnt/tmp/hostname /etc")

	    # Reescribimos el fichero hosts para asociar la direccion 127.0.1.1
	    n = open('./mnt/tmp/hosts',"w") 	    
	    n.write("127.0.1.1 s3\n127.0.0.1 localhost\n::1 ip6-localhost ip6-loopback\nfe00::0 ip6-localnet\nff00::0 ip6-mcastprefix\nff02::1 ip6-allnodes\nff02::2 ip6-allrouters\nff02::3 ip6-allhosts")      		
	    n.close()
	    # Copiamos el fichero hosts en el directorio /etc de nuestra máquina para actualizar el fichero hosts
	    os.system("sudo virt-copy-in -d s3 ./mnt/tmp/hosts /etc")

	    # Introducimos en index.html el contenido de la página html inicial de la máquina s3
	    os.system("echo S3 > ./mnt/tmp/index.html")
	    # Copiamos el fichero index.html en el directorio /var/www/html de nuestra máquina para actualizar el fichero index.html
	    os.system("sudo virt-copy-in -d s3 ./mnt/tmp/index.html /var/www/html")

	    # Reescribimos el fichero interfaces para introducir las interfaces correspondientes de nuestra red para s3
	    n = open('./mnt/tmp/interfaces',"w") 	    
	    n.write("auto lo\niface lo inet loopback\n\nauto eth0\niface eth0 inet dhcp\n\niface eth0 inet static\naddress 10.0.2.13\nnetmask 255.255.255.0\ngateway 10.0.2.1\ndns-nameservers 10.0.2.1\n ")      		
	    n.close()
	    # Copiamos el fichero interfaces en el directorio /etc/network de nuestra máquina para actualizar el fichero interfaces
	    os.system("sudo virt-copy-in -d s3 ./mnt/tmp/interfaces /etc/network")

            # Imprimimos por pantalla la creación de S3
            print("Se ha creado S3")


	# Para un parámetro mayor que 3 deberemos crear además S4 
        if (num_serv >= 4):	

            os.system("qemu-img create -f qcow2 -b cdps-vm-base-pc1.qcow2 s4.qcow2")
            os.system("cp plantilla-vm-pc1.xml s4.xml")

	    # Procedemos a cargar el fichero XML de s4 y obtener el nodo raiz
            tree = etree.parse('s4.xml')
            root = tree.getroot()
            
            # Guardamos en "aux" el fichero XML que vamos a modificar
            aux = etree.ElementTree(root)

	    # Cambiamos el campo nombre
            nameField = root.find("name")
            nameField.text = 's4'

	    # Cambiamos el campo source 
            source = root.find("./devices/disk/source")	
            source.set("file", '/mnt/tmp/pc1/s4.qcow2')

	    # Cambiamos el campo bridge
            interfaceSource = root.find("./devices/interface/source")
            interfaceSource.set("bridge", 'LAN2')

            # Sustituimos el fichero s4.xml por el modificado y lo guardamos con el mismo nombr
            outFile = open('s4.xml', 'w')
            aux.write("outFile")
            os.system("rm s4.xml")
            os.system("mv outFile s4.xml")

	    # Definimos la máquina en el gestor
            os.system("sudo virsh define s4.xml")

	    # Definimos el nombre de la máquina virtual s4
	    os.system("echo s4 > ./mnt/tmp/hostname")

	    # Copiamos el fichero hostname en el directorio /etc de nuestra máquina para actualizar el fichero hostname
	    os.system("sudo virt-copy-in -d s4 ./mnt/tmp/hostname /etc")

	    # Reescribimos el fichero hosts para asociar la direccion 127.0.1.1
	    n = open('./mnt/tmp/hosts',"w") 	    
	    n.write("127.0.1.1 s4\n127.0.0.1 localhost\n::1 ip6-localhost ip6-loopback\nfe00::0 ip6-localnet\nff00::0 ip6-mcastprefix\nff02::1 ip6-allnodes\nff02::2 ip6-allrouters\nff02::3 ip6-allhosts")      		
	    n.close()
	    # Copiamos el fichero hosts en el directorio /etc de nuestra máquina para actualizar el fichero hosts
	    os.system("sudo virt-copy-in -d s4 ./mnt/tmp/hosts /etc")

	    # Introducimos en index.html el contenido de la página html inicial de la máquina s4
	    os.system("echo S4 > ./mnt/tmp/index.html")
	    # Copiamos el fichero index.html en el directorio /var/www/html de nuestra máquina para actualizar el fichero index.html
	    os.system("sudo virt-copy-in -d s4 ./mnt/tmp/index.html /var/www/html")

	    # Reescribimos el fichero interfaces para introducir las interfaces correspondientes de nuestra red para s4
	    n = open('./mnt/tmp/interfaces',"w") 	    
	    n.write("auto lo\niface lo inet loopback\n\nauto eth0\niface eth0 inet dhcp\n\niface eth0 inet static\naddress 10.0.2.14\nnetmask 255.255.255.0\ngateway 10.0.2.1\ndns-nameservers 10.0.2.1\n ")      		
	    n.close()
	    # Copiamos el fichero interfaces en el directorio /etc/network de nuestra máquina para actualizar el fichero interfaces
	    os.system("sudo virt-copy-in -d s4 ./mnt/tmp/interfaces /etc/network")

            # Imprimimos por pantalla la creación de S4
            print("Se ha creado S4")


	# Para un parámetro mayor que 4 deberemos crear además S5 
        if (num_serv == 5):	

            os.system("qemu-img create -f qcow2 -b cdps-vm-base-pc1.qcow2 s5.qcow2")
            os.system("cp plantilla-vm-pc1.xml s5.xml")

	    # Procedemos a cargar el fichero XML de s5 y obtener el nodo raiz
            tree = etree.parse('s5.xml')
            root = tree.getroot()
            
            # Guardamos en 'aux' el fichero XML que vamos a modificar  
            aux = etree.ElementTree(root)

	    # Cambiamos el campo nombre
            nameField = root.find("name")
            nameField.text = 's5'

     	    # Cambiamos el campo source 
            source = root.find("./devices/disk/source")	
            source.set("file", '/mnt/tmp/pc1/s5.qcow2')

	    # Cambiamos el campo bridge
            interfaceSource = root.find("./devices/interface/source")
            interfaceSource.set("bridge", 'LAN2')

            # Sustituimos el fichero s5.xml por el modificado y lo guardamos con el mismo nombr
            outFile = open('s5.xml', 'w')
            aux.write("outFile")
            os.system("rm s5.xml")
            os.system("mv outFile s5.xml")

	    # Definimos la máquina en el gestor
            os.system("sudo virsh define s5.xml")

	    # Definimos el nombre de la máquina virtual s5
	    os.system("echo s5 > ./mnt/tmp/hostname")

	    # Copiamos el fichero hostname en el directorio /etc de nuestra máquina para actualizar el fichero hostname
	    os.system("sudo virt-copy-in -d s5 ./mnt/tmp/hostname /etc")

	    # Reescribimos el fichero hosts para asociar la direccion 127.0.1.1
	    n = open('./mnt/tmp/hosts',"w") 	    
	    n.write("127.0.1.1 s5\n127.0.0.1 localhost\n::1 ip6-localhost ip6-loopback\nfe00::0 ip6-localnet\nff00::0 ip6-mcastprefix\nff02::1 ip6-allnodes\nff02::2 ip6-allrouters\nff02::3 ip6-allhosts")      		
	    n.close()
	    # Copiamos el fichero hosts en el directorio /etc de nuestra máquina para actualizar el fichero hosts
	    os.system("sudo virt-copy-in -d s5 ./mnt/tmp/hosts /etc")

	    # Introducimos en index.html el contenido de la página html inicial de la máquina s5
	    os.system("echo S5 > ./mnt/tmp/index.html")
	    # Copiamos el fichero index.html en el directorio /var/www/html de nuestra máquina para actualizar el fichero index.html 
	    os.system("sudo virt-copy-in -d s5 ./mnt/tmp/index.html /var/www/html")

	    # Reescribimos el fichero interfaces para introducir las interfaces correspondientes de nuestra red para s5
	    n = open('./mnt/tmp/interfaces',"w") 	    
	    n.write("auto lo\niface lo inet loopback\n\nauto eth0\niface eth0 inet dhcp\n\niface eth0 inet static\naddress 10.0.2.15\nnetmask 255.255.255.0\ngateway 10.0.2.1\ndns-nameservers 10.0.2.1\n ")      		
	    n.close()
            # Copiamos el fichero interfaces en el directorio /etc/network de nuestra máquina para actualizar el fichero interfaces
	    os.system("sudo virt-copy-in -d s5 ./mnt/tmp/interfaces /etc/network")

            # Imprimimos por pantalla la creación de s5
            print("Se ha creado S5")

    # Arrancamos el gestor de máquinas virtuales
    os.system("HOME=/mnt/tmp sudo virt-manager")



##### Función arrancar(num): para arrancar las máquinas virtuales y mostrar su consola.

def arrancar(num):

	# Leemos el contenido del fichero donde tenemos guardado el nº de servidores a crear introducidos en la orden "crear y lo guardamos en la variable num_serv

	f = open("pc1.cfg", "r")
	num_serv = int(f.read())
	f.close()
	
	# Si no introducimos parámetro arrancamos por defecto: 2 servidores + c1 y lb 
	
	if len(sys.argv) == 2:

		# Se arrancan las máquinas por defecto (c1, lb, s1 y s2)
		os.system("sudo virsh start c1")
		os.system("sudo virsh start lb")
		os.system("sudo virsh start s1")
		os.system("sudo virsh start s2")	

		# Se lanzan las máquinas en terminales separados
		os.system("xterm -rv -sb -rightbar -fa monospace -fs 10 -title 'c1' -e 'sudo virsh console c1' &")
		os.system("xterm -rv -sb -rightbar -fa monospace -fs 10 -title 'lb' -e 'sudo virsh console lb' &")
		os.system("xterm -rv -sb -rightbar -fa monospace -fs 10 -title 's1' -e 'sudo virsh console s1' &")
		os.system("xterm -rv -sb -rightbar -fa monospace -fs 10 -title 's2' -e 'sudo virsh console s2' &")
		
		print("Máquinas c1, lb, s1 y s2 arrancadas.")

	# Si introducimos como tercer parámetro un nº configurable de 1 a 5, lanzará las máquinas correspondientes al nº indicado

	if len(sys.argv) == 3:

		if ((num_serv >= 1 and num_serv <= 5) and (int(num) >= 1 and int(num) <= 5)):
			
			if(int(num) >= 1 and num_serv >= 1):
				#  Repetimos el proceso de arranque con s1
				os.system("sudo virsh start c1")
				os.system("sudo virsh start lb")
				os.system("sudo virsh start s1")
				os.system("xterm -rv -sb -rightbar -fa monospace -fs 10 -title 'c1' -e 'sudo virsh console c1' &")
				os.system("xterm -rv -sb -rightbar -fa monospace -fs 10 -title 'lb' -e 'sudo virsh console lb' &")
				os.system("xterm -rv -sb -rightbar -fa monospace -fs 10 -title 's1' -e 'sudo virsh console s1' &")

				print("Maquina S1 arrancada.")


				# Si el parámetro es superior a 1 arrancaremos s2
			if(int(num) >= 2 and num_serv >= 2):

				# Repetimos el proceso de arranque con s2	
				os.system("sudo virsh start s2")
				os.system("xterm -rv -sb -rightbar -fa monospace -fs 10 -title 's2' -e 'sudo virsh console s2' &")

				print("Maquina S2 arrancada.")


				# Si el parámetro es superior a 2 arrancaremos s3
			if(int(num) >= 3 and num_serv >= 3):

				# Repetimos el proceso de arranque con s3	
				os.system("sudo virsh start s3")
				os.system("xterm -rv -sb -rightbar -fa monospace -fs 10 -title 's3' -e 'sudo virsh console s3' &")

				print("Maquina S3 arrancada.")


				# Si el parámetro es superior a 3 arrancaremos s4
			if(int(num) >= 4 and num_serv >= 4):

				# Repetimos el proceso de arranque con s4	
				os.system("sudo virsh start s4")
				os.system("xterm -rv -sb -rightbar -fa monospace -fs 10 -title 's4' -e 'sudo virsh console s4' &")

				print("Maquina S4 arrancada.")


				# Si el parámetro es igual a 5 arrancaremos s5
			if(int(num) == 5 and num_serv == 5):

				# Repetimos el proceso de arranque con s5
				os.system("sudo virsh start s5")
				os.system("xterm -rv -sb -rightbar -fa monospace -fs 10 -title 's5' -e 'sudo virsh console s5' &")

				print("Maquina S5 arrancada.")

		else: 
			print("Parámetro fuera de rango, use un rango comprendido entre 1 y 5")



##### Función arrancarmaq(maquina): para arrancar unicamente la máquina especificada como tercer parámetro.

def arrancarmaq(maquina):

	if len(sys.argv) == 3:

		# En cada caso solo arrancamos la máquina correspondiente
		if(maquina == "c1"):
			os.system("sudo virsh start c1")
			os.system("xterm -rv -sb -rightbar -fa monospace -fs 10 -title 'c1' -e 'sudo virsh console c1' &")

			print("Arrancando C1 ...")

		if(maquina == "lb"):
			os.system("sudo virsh start lb")
			os.system("xterm -rv -sb -rightbar -fa monospace -fs 10 -title 'lb' -e 'sudo virsh console lb' &")

			print("Arrancando LB ...")

		if(maquina == "s1"):
			os.system("sudo virsh start s1")
			os.system("xterm -rv -sb -rightbar -fa monospace -fs 10 -title 's1' -e 'sudo virsh console s1' &")

			print("Arrancando S1 ...")

		if(maquina == "s2"):
			os.system("sudo virsh start s2")
			os.system("xterm -rv -sb -rightbar -fa monospace -fs 10 -title 's2' -e 'sudo virsh console s2' &")

			print("Arrancando S2 ...")

		if(maquina == "s3"):
			os.system("sudo virsh start s3")
			os.system("xterm -rv -sb -rightbar -fa monospace -fs 10 -title 's3' -e 'sudo virsh console s3' &")

			print("Arrancando S3 ...")

		if(maquina == "s4"):
			os.system("sudo virsh start s4")
			os.system("xterm -rv -sb -rightbar -fa monospace -fs 10 -title 's4' -e 'sudo virsh console s4' &")

			print("Arrancando s4 ...")

		if(maquina == "s5"):
			os.system("sudo virsh start s5")
			os.system("xterm -rv -sb -rightbar -fa monospace -fs 10 -title 's5' -e 'sudo virsh console s5' &")

			print("Arrancando S5 ...")

	else:
		print("introduzca un parámetro correcto")



##### Función parar(): para parar las máquinas virtuales

def parar():
	
	# Si no introducimos parámetro pararemos todas las máquinas (nº especificado en funcion crear y guardado en fichero "num_serv.txt")
	if len(sys.argv) == 2:
		# Leemos el contenido del fichero donde tenemos guardado el nº de servidores a crear introducidos en la orden "crear" y lo guardamos en una variable
		f = open("pc1.cfg", "r")
		num_serv = int(f.read())
		f.close()


		if(num_serv >= 0):
			os.system("sudo virsh shutdown c1")
			os.system("sudo virsh shutdown lb")

			print("Parando C1 Y LB ...")

		if(num_serv >= 1):
			os.system("sudo virsh shutdown s1")

			print("Parando S1 ...")

		if(num_serv >= 2):
			os.system("sudo virsh shutdown s2")

			print("Parando S2 ...")

		if(num_serv >= 3):
			os.system("sudo virsh shutdown s3")

			print("Parando S3 ...")

		if(num_serv >= 4):
			os.system("sudo virsh shutdown s4")

			print("Parando s4 ...")

		if(num_serv >= 5):
			os.system("sudo virsh shutdown s5")

			print("Parando S5 ...")
	else:
		print("No introduzca un tercer parámetro, para parar por máquina utilice la función pararmaq")



##### Función pararmaq(maquina): para parar unicamente la máquina especificada como tercer parámetro.

def pararmaq(maquina):

	if len(sys.argv) == 3:
		
		# En cada caso solo paramos la máquina correspondiente
		if(maquina == "c1"):
			os.system("sudo virsh shutdown c1")

			print("Parando C1 ...")

		if(maquina == "lb"):
			os.system("sudo virsh shutdown lb")

			print("Parando LB ...")

		if(maquina == "s1"):
			os.system("sudo virsh shutdown s1")

			print("Parando S1 ...")

		if(maquina == "s2"):
			os.system("sudo virsh shutdown s2")

			print("Parando S2 ...")

		if(maquina == "s3"):
			os.system("sudo virsh shutdown s3")

			print("Parando S3 ...")

		if(maquina == "s4"):
			os.system("sudo virsh shutdown s4")

			print("Parando s4 ...")

		if(maquina == "s5"):
			os.system("sudo virsh shutdown s5")

			print("Parando S5 ...")
	else:
		print("introduzca un parámetro correcto")


		
##### Función destruir(n): libera el escenario, borrando todos los ficheros creados 
	
def destruir(maquina):
	
   # Si no indicamos ninguna máquina específica destruimos todas
		if len(sys.argv) == 2:    
			if os.path.exists("c1.qcow2"):
				os.system("sudo virsh destroy c1")
				os.system("sudo virsh undefine c1")
				os.system("rm c1.qcow2 -f")
	
			if os.path.exists("c1.xml"):
				os.system("rm c1.xml -f")
	
			if os.path.exists("lb.qcow2"):
				os.system("sudo virsh destroy lb")
				os.system("sudo virsh undefine lb")
				os.system("rm lb.qcow2 -f")
	
			if os.path.exists("lb.xml"):
				os.system("rm lb.xml -f") 
	
			if os.path.exists("s1.qcow2"):
				os.system("sudo virsh destroy s1")
				os.system("sudo virsh undefine s1")
				os.system("rm s1.qcow2 -f")
	
			if os.path.exists("s1.xml"):
				os.system("rm s1.xml -f")
	
			if os.path.exists("s2.qcow2"):
				os.system("sudo virsh destroy s2")
				os.system("sudo virsh undefine s2")
				os.system("rm s2.qcow2 -f")
	
			if os.path.exists("s2.xml"):
				os.system("rm s2.xml -f")
	
			if os.path.exists("s3.xml"):
				os.system("rm s3.xml -f")
	
			if os.path.exists("s3.qcow2"):
				os.system("sudo virsh destroy s3")
				os.system("sudo virsh undefine s3")
				os.system("rm s3.qcow2 -f")
	
			if os.path.exists("s4.xml"):
				os.system("rm s4.xml -f")
	
			if os.path.exists("s4.qcow2"):
				os.system("sudo virsh destroy s4")
				os.system("sudo virsh undefine s4")
				os.system("rm s4.qcow2 -f")
	
			if os.path.exists("s5.xml"):
				os.system("rm s5.xml -f")
	
			if os.path.exists("s5.qcow2"):
				os.system("sudo virsh destroy s5")
				os.system("sudo virsh undefine s5")
				os.system("rm s5.qcow2 -f")
	
			#Borramos el fichero de configuración donde se guarda número de servidores especificado en la funcion "crear"
			if os.path.exists("pc1.cfg"):		
				os.system("rm ./pc1.cfg")
			#Borramos el fichero donde se guardan los archivos de configuración"
			os.system("rm -r mnt")


			print(" Se han destruido todas las máquinas")
		
		
		# En caso de introducir parámetro a la funcion destruir, destruiremos exlusivamente la máquina especificada
		if len(sys.argv) == 3:
			
			# En cada caso solo destruimos la máquina correspondiente
			if(maquina == "c1"):
				os.system("sudo virsh destroy c1")
				os.system("sudo virsh undefine c1")
				os.system("rm c1.qcow2 -f")
				os.system("rm c1.xml -f")
				print("destruida máquina c1")
	
			if(maquina == "lb"):
				os.system("sudo virsh destroy lb")
				os.system("sudo virsh undefine lb")
				os.system("rm lb.qcow2 -f")
				os.system("rm lb.xml -f")
				print("Destruida máquina lb")
	
			if(maquina == "s1"):
				os.system("sudo virsh destroy s1")
				os.system("sudo virsh undefine s1")
				os.system("rm s1.qcow2 -f")
				os.system("rm s1.xml -f")
				print("Destruida máquina s1")
	
			if(maquina == "s2"):
				os.system("sudo virsh destroy s2")
				os.system("sudo virsh undefine s2")
				os.system("rm s2.qcow2 -f")
				os.system("rm s2.xml -f")
				print("Destruida máquina s2")
	
			if(maquina == "s3"):
				os.system("sudo virsh destroy s3")
				os.system("sudo virsh undefine s3")
				os.system("rm s3.qcow2 -f")
				os.system("rm s3.xml -f")
				print("Destruida máquina s3")
	
			if(maquina == "s4"):
				os.system("sudo virsh destroy s4")
				os.system("sudo virsh undefine s4")
				os.system("rm s4.qcow2 -f")
				os.system("rm s4.xml -f")
				print("Destruida máquina s4")
	
			if(maquina == "s5"):
				os.system("sudo virsh destroy s5")
				os.system("sudo virsh undefine s5")
				os.system("rm s5.qcow2 -f")
				os.system("rm s5.xml -f")
				print("Destruida máquina s5")


##### Función monitor(): muestra distintas funcionalidades, asi como el tráfico del host a cualquier máquina, el estado de la cpu

def monitor():

	if len(sys.argv) >= 3:
		argumento = sys.argv[2]
	else:
		print("Por favor introduzca un parámetro válido")
    	if argumento == "lista":
		os.system("sudo virsh list")
	
	# El argumento ping nos permite comprobar si hay conexión con la máquina seleccionada mostrando el tráfico hacia la misma
	elif argumento == "ping":
		if len(sys.argv) < 4:
			print("introduzca el nombre de la máquina a la que quiere hacer ping")
		else: 
			maquina = sys.argv[3]
			if maquina == "c1":
				
				os.system("ping -c 5 10.0.1.2")
			elif maquina == "lb":
				os.system("ping -c 5 10.0.1.1")
				os.system("ping -c 5 10.0.2.1")

			elif maquina == "s1":
				os.system("ping -c 5 10.0.2.11")

			elif maquina == "s2":
				os.system("ping -c 5 10.0.2.12")

			elif maquina == "s3":
				os.system("ping -c 5 10.0.2.13")

			elif maquina == "s4":
				os.system("ping -c 5 10.0.2.14")

			elif maquina == "s5":
				os.system("ping -c 5 10.0.2.15")

	# El argumento cpu nos permite ver las stats de la cpu de cada máquina
	elif argumento == "cpu":
		if len(sys.argv) < 4:
			print("introduzca el nombre de la máquina a la que quiere ver las stats de la cpu")
		else:
			maquina = sys.argv[3]
			if maquina == "c1":
				os.system("xterm -title 'Monitor c1' -e watch sudo virsh cpu-stats c1")
			elif maquina == "lb":
				os.system("xterm -title 'Monitor lb' -e watch sudo virsh cpu-stats lb")
				
			elif maquina == "s1":
				os.system("xterm -title 'Monitor s1' -e watch sudo virsh cpu-stats s1")
			elif maquina == "s2":
				os.system("xterm -title 'Monitor s2' -e watch sudo virsh cpu-stats s2")
			elif maquina == "s3":
				os.system("xterm -title 'Monitor s4' -e watch sudo virsh cpu-stats s3")
			elif maquina == "s4":
				os.system("xterm -title 'Monitor s4' -e watch sudo virsh cpu-stats s4")
			elif maquina == "s5":
				os.system("xterm -title 'Monitor s5' -e watch sudo virsh cpu-stats s5")

	#El watch nos permite ver el tamañao que ocupa la máquina y los permisos
	elif argumento == "watch":
		if len(sys.argv) < 4:
			print("introduzca el nombre de la máquina a la que quiere hacer watch")
		else:
			maquina = sys.argv[3]
			if maquina == "c1":
				os.system("xterm -title 'Monitor c1' -e watch ls -al /mnt/tmp/pc1/c1.qcow2")
			elif maquina == "lb":
				os.system("xterm -title 'Monitor lb' -e watch ls -al /mnt/tmp/pc1/lb.qcow2")
			elif maquina == "s1":
				os.system("xterm -title 'Monitor s1' -e watch ls -al /mnt/tmp/pc1/s1.qcow2")
			elif maquina == "s2":
				os.system("xterm -title 'Monitor s2' -e watch ls -al /mnt/tmp/pc1/s2.qcow2")
			elif maquina == "s3":
				os.system("xterm -title 'Monitor s3' -e watch ls -al /mnt/tmp/pc1/s3.qcow2")
			elif maquina == "s4":
				os.system("xterm -title 'Monitor s4' -e watch ls -al /mnt/tmp/pc1/s4.qcow2")
			elif maquina == "s5":
				os.system("xterm -title 'Monitor s5' -e watch ls -al /mnt/tmp/pc1/s5.qcow2")
	
# Las diferentes funcionalidades que podemos ejecutar			
options = { 
	    "ayuda": ayuda,  
	    "crear": crear,       
	    "arrancar": arrancar,
	    "parar": parar,
	    "arrancarmaq": arrancarmaq,
	    "pararmaq": pararmaq,
	    "destruir": destruir,
	    "monitor": monitor,
           }

# Aqui se comprueban los argumentos que pasamos y nos lleva a una opción u otra
if len(sys.argv) <= 1:
	sys.exit("Incorrecto uso del script, por favor introduzca parametros: pc1.py <orden> <otros_parametros> Si necesita ayuda escriba pc1.py ayuda")
else:
	orden = sys.argv[1]
	if len(sys.argv) == 2:
		num = 2
	if len(sys.argv) == 3:
		num = sys.argv[2]
	elif (len(sys.argv) >= 5):
		sys.exit("Incorrecto uso del script, por favor introduzca parametros: pc1.py <orden> <otros_parametros> Si necesita ayuda escriba pc1.py ayuda")

# Dependiendo de lo que se haya pasado como parámetro se ejecuta la función correspondiente
if orden in options:	
	if(orden == "ayuda" or orden == "parar" or orden == "monitor"):
		options[orden]()
	else:
		options[orden](num)

else:
	sys.exit("Incorrecto uso del script, por favor introduzca parametros: pc1.py <orden> <otros_parametros> Si necesita ayuda escriba pc1.py ayuda")
