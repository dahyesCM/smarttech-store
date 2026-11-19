# SmartTech Store · Parte 1

## 1. Arrancar Django desde Visual Studio Code en Fedora

Abre la carpeta `DEIAE_PC2` en Visual Studio Code. En el menú **Terminal → Nuevo terminal**, ejecuta:

```bash
cd /home/damaryschecasaca/DEIAE_PC2
source .venv/bin/activate
cat /etc/fedora-release
python --version
python -m pip show Django djangorestframework | rg '^(Name|Version):'
python manage.py check
python manage.py migrate
python manage.py seed_demo
```

**Captura 1.** Muestra el terminal con la versión de Fedora, Python, Django y DRF, y el resultado de `manage.py check`. Si Django dice «No migrations to apply», la base ya está migrada.

En una copia nueva sin entorno virtual, ejecuta `python3 -m venv .venv`, actívalo y usa `python -m pip install -r requirements.txt` antes de los comandos de Django.

Crea tu administrador una vez y arranca la tienda. Django te pedirá una contraseña que puedes escribir directamente en el terminal:

```bash
python manage.py createsuperuser --username administrador
python manage.py runserver
```

Si ese usuario ya existe, usa la cuenta existente. Si el servidor ya está funcionando en el puerto 8000, abre los enlaces de esta guía directamente. Si necesitas iniciarlo tú desde VS Code y el puerto está ocupado, ejecuta `python manage.py runserver 8001` y sustituye `8000` por `8001` en los enlaces.

## 2. Autenticación y roles

- **Captura 2.** Abre [Registro](http://127.0.0.1:8000/registro/) en una ventana privada. Crea una cuenta de cliente, por ejemplo `cliente_demo`. Puedes salir y volver a entrar en [Ingresar](http://127.0.0.1:8000/ingresar/) para demostrar el inicio de sesión.
- **Captura 3.** Con la sesión de cliente, abre [Catálogo](http://127.0.0.1:8000/#catalogo). Busca `teclado`, coloca cantidad `2` con **+**, pulsa **Agregar**, abre [Carrito](http://127.0.0.1:8000/carrito/) y finaliza la compra de prueba. Captura también **¡Compra exitosa!**. Abre [Mis pedidos](http://127.0.0.1:8000/pedidos/) y captura el pedido pendiente con su total.
- **Captura 4.** En una ventana normal entra a [Django Admin](http://127.0.0.1:8000/admin/) con tu administrador. Abre [Usuarios](http://127.0.0.1:8000/admin/auth/user/) y muestra los permisos de una de las cuentas. El cliente ve sus propios pedidos. El administrador puede gestionar productos y todos los pedidos.

## 3. CRUD de productos y pedidos

- **Capturas 5 y 6.** Abre [Productos](http://127.0.0.1:8000/admin/store/product/). Agrega un **Cable USB-C de prueba** con SKU `cable-demo`, una descripción y precio `29.90`. Guarda para que aparezca en el listado. Abre el producto, cambia el precio a `34.90` y guarda. Puedes mostrar la confirmación de **Eliminar** con este producto de prueba. Hazlo antes de asociarlo a un pedido.
- **Capturas 7 y 8.** Abre [Pedidos](http://127.0.0.1:8000/admin/store/order/) y localiza el pedido de `cliente_demo`. Cambia su estado de **Pendiente** a **Confirmado**. Actualiza **Mis pedidos** en la ventana privada para mostrar el cambio. Para demostrar la eliminación, crea un pedido manual de prueba desde el administrador y abre su confirmación de borrado. Conserva el primer pedido para mostrar persistencia.

## 4. API REST con Django REST Framework

- **Captura 9.** Abre la [API de productos](http://127.0.0.1:8000/api/products/) o el [detalle por SKU](http://127.0.0.1:8000/api/products/teclado/). Muestra la interfaz navegable de Django REST Framework y el resultado de `GET`. Para ver el JSON directo, abre [Productos en JSON](http://127.0.0.1:8000/api/products/?format=json).
- **Captura 10.** Abre la [API de pedidos](http://127.0.0.1:8000/api/orders/) en la ventana privada del cliente autenticado. Muestra la respuesta con su pedido. El administrador puede abrir esa misma URL en su ventana normal para mostrar todos los pedidos.

## 5. SQLite y persistencia

En un segundo terminal de VS Code activa el entorno y comprueba el archivo, el motor y el pedido guardado:

```bash
cd /home/damaryschecasaca/DEIAE_PC2
source .venv/bin/activate
ls -lh db.sqlite3
python manage.py shell -c "from django.db import connection; print(connection.settings_dict['ENGINE']); print(connection.settings_dict['NAME'])"
python manage.py shell -c "from store.models import Order; print(list(Order.objects.values('id', 'customer__username', 'product__name', 'quantity', 'status')))"
```

**Captura 11.** Muestra `django.db.backends.sqlite3`, la ruta a `db.sqlite3` y el pedido de prueba en la consulta. Para demostrar persistencia, detén el servidor que abriste con `Ctrl+C`, vuelve a ejecutar `python manage.py runserver` y comprueba que el pedido sigue visible.

## Qué explicar en la sustentación

«El sistema se ejecuta en Fedora. Django gestiona las cuentas y las sesiones, y comprueba los permisos según el rol. Django REST Framework expone los productos y pedidos como JSON. El frontend usa la sesión de Django para enviar los pedidos. SQLite guarda los datos en un archivo local, por eso siguen disponibles después de reiniciar el servidor».
