# SmartTech Store

Catálogo y pedidos en Django con SQLite, clasificación de imágenes con Hugging Face y visualización de productos con Unity y Vuforia. La interfaz usa plantillas HTML, CSS y JavaScript.

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

Crea un [token de Hugging Face](https://huggingface.co/settings/tokens) con permiso para realizar llamadas a Inference Providers. En Bash, antes de iniciar Django, carga el token sin escribirlo en el historial:

```bash
read -rsp 'Token de Hugging Face: ' HF_TOKEN
export HF_TOKEN
printf '\n'
python manage.py runserver
```

Ingresa a la tienda y sube una foto de un teclado, mouse o laptop en **Analizar imagen**. Django valida y redimensiona la foto, la envía a [ViT en Hugging Face](https://huggingface.co/google/vit-base-patch16-224) y devuelve hasta tres etiquetas con su puntuación cuando está disponible. Compara las etiquetas con el campo **Etiquetas de IA** de los productos visibles. El resultado sugiere productos de la misma clase visual.

## Realidad aumentada en Windows

Los archivos de integración están en [ar](ar/README.md). Incluyen modelos 3D procedurales y el cliente que consulta el catálogo de Django. Los marcadores se descargan desde **Realidad aumentada** en la tienda.

Para que Windows acceda a Fedora por la red local, identifica la IP de Fedora y configura el servidor de desarrollo. Sustituye el ejemplo por la IP real:

```bash
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.25 python manage.py runserver 0.0.0.0:8000
```

Comprueba desde Windows que abre `http://192.168.1.25:8000/api/products/teclado/`. Ambas máquinas deben tener conectividad y el puerto 8000 debe estar permitido en la red de demostración. Configura esa misma dirección como **Api Base** en Unity.

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
