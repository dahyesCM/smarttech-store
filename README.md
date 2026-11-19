# SmartTech Store

Proyecto académico de desarrollo full stack. La tienda usa Django REST Framework y SQLite en Fedora, con un frontend en HTML, CSS y JavaScript. La demostración integra gestión de pedidos, realidad aumentada en Unity y clasificación de imágenes.

## Estado del proyecto

| Parte | Qué hicimos | Qué queda |
|---|---|---|
| **1 · Django en Fedora** | Landing, catálogo con fotos, búsqueda y orden por precio. Registro, inicio de sesión, perfil y roles de cliente y administrador. Carrito, dirección de entrega, confirmación de compra e historial. CRUD, API REST y persistencia en SQLite verificados. | Parte 1 terminada. Las instrucciones de evidencia están en la [guía de capturas](PARTE_1_CAPTURAS.md). |
| **2 · Unity y Vuforia en Windows** | Dos marcadores PNG y un script C# que genera los modelos de teclado y laptop, muestra u oculta el modelo según el seguimiento y consulta la API para obtener nombre y precio. | Montar la escena, configurar Vuforia y probar la cámara. Luego verificar la conexión Windows–Fedora. |
| **3 · Hugging Face en Fedora** | Carga de fotos, clasificación real con MobileNetV2 de Hugging Face en Fedora y resultados con confianza y productos relacionados. | Tomar las capturas de sustentación. |

El checkout se verificó con **pago simulado**. Stripe Checkout está integrado en modo de prueba y requiere credenciales de prueba para verificarlo con Stripe.

## Django en Fedora

Desde la carpeta del proyecto, con Python 3.12 o posterior:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py createsuperuser
python manage.py runserver
```

Abre http://127.0.0.1:8000. Crea una cuenta desde **Ingresar → Crea una cuenta** y agrega productos al carrito y finaliza la compra. Un cliente ve sus propios pedidos. Inicia sesión con el superusuario y entra a **Gestión** para gestionar productos y pedidos. Los pedidos registrados por el administrador se pueden eliminar. Las compras conservan sus líneas y pueden marcarse como canceladas. Para conservar el historial, un producto referenciado por un pedido puede ocultarse desactivando **Visible**. Los pedidos conservan el precio unitario registrado.

| Ruta | Uso |
|---|---|
| `GET /api/products/` | Catálogo público |
| `GET /api/products/teclado/` | Producto por SKU |
| `GET, POST /api/orders/` | Listar los pedidos propios. El personal también puede crear pedidos manuales. |
| `GET, PATCH, DELETE /api/orders/<id>/` | Consultar un pedido propio o administrarlo como personal |
| `POST /api/classify/` | Clasificar un archivo en el campo multipart `image` |

Las operaciones de escritura en productos requieren personal autorizado. La interfaz envía la cookie de sesión y el token CSRF. SQLite guarda los datos en `db.sqlite3`.

## Clasificación de imágenes

SmartTech ejecuta en Fedora [MobileNetV2 de Hugging Face](https://huggingface.co/onnxmodelzoo/mobilenetv2-12) con ONNX Runtime y CPU. La descarga inicial requiere internet. La clasificación local funciona después sin token y sin enviar la foto fuera de Fedora.

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py download_vision_model
python manage.py runserver 8001
```

Para la demostración, entra a [Analizar imagen](http://127.0.0.1:8001/#analizar) con una cuenta de cliente. Descarga la foto de prueba del mouse desde esa sección, selecciónala y pulsa **Analizar foto**. Captura la foto seleccionada y luego el resultado con el modelo, las etiquetas, sus porcentajes y **Mouse inalámbrico** como producto relacionado.

Django recibe la imagen en `POST /api/classify/`, valida el formato y el tamaño, devuelve las tres predicciones de mayor puntuación y compara sus etiquetas con las de los productos activos. Las coincidencias identifican una clase visual. El valor de confianza corresponde al puntaje del modelo.

Opcionalmente, si el servidor tiene `HF_TOKEN` configurado, Django usa el servicio alojado de Hugging Face y el [modelo ViT](https://huggingface.co/google/vit-base-patch16-224).

## Realidad aumentada en Windows

Empieza por [la guía de montaje](ar/README.md). El repositorio incluye estos recursos:

- [SmartTechAugmentation.cs](ar/Assets/SmartTech/SmartTechAugmentation.cs) con los modelos 3D y el cliente de la API.
- [Marcador del teclado](store/static/store/smarttech-marker.png) y [marcador de la laptop](store/static/store/laptop-marker.png).

Copia la carpeta `ar/Assets/SmartTech` dentro de `Assets` en el proyecto de Unity. Monta primero una escena con el teclado. El criterio de éxito es que el teclado aparezca al mostrar el marcador a la cámara y se oculte al retirarlo. Luego agrega la laptop.

En la prueba previa, Django respondió en Fedora por `10.0.2.15:8001`, pero el navegador de Windows rechazó la conexión. Si Fedora sigue en VirtualBox con NAT y Windows es el anfitrión, configura el reenvío TCP de `127.0.0.1:8001` en Windows al puerto `8001` de Fedora. Mantén la VM y Django encendidos y verifica primero desde Windows `http://127.0.0.1:8001/api/products/teclado/?format=json`. Si devuelve el nombre y el precio, configura `http://127.0.0.1:8001` como **Api Base** en Unity. Si cambia la IP de Fedora, actualiza la regla de VirtualBox.

En Fedora, si necesitas volver a iniciar el servidor para esa prueba:

```bash
source .venv/bin/activate
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,10.0.2.15 python manage.py runserver 0.0.0.0:8001
```

### Prompt para continuar en Codex desde Windows

Clona [el repositorio de SmartTech Store](https://github.com/dahyesCM/smarttech-store) con la cuenta de GitHub que tiene acceso, abre la carpeta clonada en Codex y pega esto:

```text
Estoy en Windows con Unity abierto y quiero continuar la Parte 2 de
SmartTech Store. Lee README.md y ar/README.md. La Parte 1 ya funciona
en Fedora con Django REST Framework y SQLite. El repositorio trae
SmartTechAugmentation.cs y los dos marcadores PNG para Vuforia.
Todavía falta montar y verificar la escena con cámara en Windows.

Revisa mi proyecto de Unity y aprovecha lo que ya esté configurado.
La PC está lenta, así que empieza con una escena ligera para el teclado.
Configura AR Camera, licencia de Vuforia e Image Target de 0.20 m.
Selecciona Keyboard en SmartTechAugmentation y conecta On Target Found
con ShowProduct y On Target Lost con HideProduct. Comprueba en Webcam
Play Mode que el modelo aparezca sobre el marcador y se oculte al retirarlo.
Indícame cuándo capturar la configuración y la vista Game para sustentar.

Después agrega la laptop y valida la API. Antes, el navegador de Windows
rechazó la conexión a Fedora. Verifica primero el JSON del teclado desde
Windows y configura Api Base cuando la URL responda. Conserva Django en
Fedora. Cuando la parte de Unity funcione, prepara un commit con la escena
y los archivos fuente, excluyendo cachés de Unity, credenciales y licencias.
```

## Sustentación de la Parte 1

Consulta la [guía de comandos, páginas y capturas](PARTE_1_CAPTURAS.md).

Las fotos de referencia del catálogo se sirven como archivos locales. Créditos en Unsplash a [Jakub Żerdzicki](https://unsplash.com/photos/person-is-using-a-mechanical-keyboard-and-mouse-2ADlI3Nv6g0), [Alex de Koning](https://unsplash.com/photos/mechanical-keyboard-glasses-and-mouse-on-a-beige-desk-mat-VuxOlb5GjCk), [Auguras Pipiras](https://unsplash.com/photos/black-cordless-computer-mouse-on-white-surface-d62p4lEN4R0) y [Faisal Waheed](https://unsplash.com/photos/half-opened-laptop-computer-on-desk-qfJd62ZVU6U).

## Carrito y pagos

El carrito se guarda en la sesión de Django, incluso antes de iniciar sesión. En el checkout puedes revisar el total y modificar la dirección para ese envío. La compra guarda la dirección y los precios del momento. En el perfil puedes actualizar los datos de entrega que se proponen en futuras compras.

Sin credenciales externas, la tienda muestra **Pago simulado**. Al confirmar, guarda el pedido, vacía el carrito y muestra **¡Compra exitosa!**. El historial identifica el pago como simulado.

Para probar la pasarela alojada [Stripe Checkout](https://docs.stripe.com/checkout/quickstart), inicia Django con una clave secreta de **prueba** en `STRIPE_SECRET_KEY`. Desde el entorno virtual, puedes cargarla sin escribirla en el historial del terminal:

```bash
read -rsp 'Clave de Stripe de prueba: ' STRIPE_SECRET_KEY
export STRIPE_SECRET_KEY
printf '\n'
python manage.py runserver
```

El cliente introduce los datos de una tarjeta de prueba en Stripe. Django confirma importe, moneda y estado con Stripe antes de mostrar éxito. Para probar también la confirmación aunque el cliente cierre la página, usa [Stripe CLI](https://docs.stripe.com/stripe-cli/use-cli) para reenviar el evento `checkout.session.completed` a `http://127.0.0.1:8000/pagos/stripe/webhook/` y carga el secreto de firma de la CLI como `STRIPE_WEBHOOK_SECRET`. Esta integración se ejecuta en modo de prueba y trabaja con soles (PEN).
