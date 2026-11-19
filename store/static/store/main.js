async function request(url, options) {
  const response = await fetch(url, options);
  const json = response.headers.get("Content-Type")?.includes("application/json");
  if (!json) throw new Error("La solicitud falló. Actualiza la página e inténtalo de nuevo.");
  const data = await response.json();
  if (!response.ok) {
    const details = Object.values(data).flat().filter(value => typeof value === "string");
    throw new Error(details.join(" ") || "No se pudo completar la solicitud.");
  }
  return data;
}

function post(form, action) {
  const body = new FormData(form);
  if (action) body.set("action", action);
  return request(form.getAttribute("action"), {
    method: "POST",
    headers: { "X-CSRFToken": body.get("csrfmiddlewaretoken"), Accept: "application/json" },
    body,
  });
}

function renderRows(container, values) {
  container.replaceChildren(...values.map(value => {
    const row = document.createElement("li");
    row.textContent = value;
    return row;
  }));
}

function handleForm(form, status, submit) {
  form.addEventListener("submit", async event => {
    event.preventDefault();
    const button = form.querySelector("button");
    button.disabled = true;
    status.textContent = "Procesando…";
    try {
      await submit(form);
    } catch (error) {
      status.textContent = error.message;
    } finally {
      button.disabled = false;
    }
  });
}

const vision = document.querySelector("#vision-form");
if (vision) {
  const status = document.querySelector("#vision-status");
  const predictions = document.querySelector("#predictions");
  const matches = document.querySelector("#matches");
  const model = document.querySelector("#vision-model");
  handleForm(vision, status, async () => {
    predictions.replaceChildren();
    matches.replaceChildren();
    model.hidden = true;
    const data = await post(vision);
    status.textContent = data.products.length
      ? "Productos relacionados en el catálogo"
      : "La clasificación no encontró coincidencias en el catálogo.";
    model.textContent = `Modelo de Hugging Face · ${data.model}`;
    model.hidden = false;
    renderRows(predictions, data.predictions.map(({ label, score }) =>
      Number.isFinite(score) ? `${label} · ${(score * 100).toFixed(1)} %` : label
    ));
    renderRows(matches, data.products.map(product =>
      `${product.name} · ${money.format(product.price)}`
    ));
  });
}

const catalogTools = document.querySelector("#catalog-tools");
if (catalogTools) {
  const search = document.querySelector("#catalog-search");
  const sort = document.querySelector("#catalog-sort");
  const list = document.querySelector("#product-list");
  const normalise = value => value.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLocaleLowerCase("es");
  const collator = new Intl.Collator("es");
  const products = Array.from(list.querySelectorAll(".product-row"), row => {
    const name = row.querySelector("h3").textContent;
    const detail = row.querySelector(".product-summary p").textContent;
    return { row, name, price: Number(row.dataset.price), text: normalise(`${name} ${row.dataset.sku} ${detail}`) };
  });

  function filterProducts() {
    const words = normalise(search.value.trim()).split(/\s+/);
    let visible = 0;
    const sorted = [...products].sort((first, second) => {
      if (sort.value === "price-up") return first.price - second.price;
      if (sort.value === "price-down") return second.price - first.price;
      return collator.compare(first.name, second.name);
    });
    sorted.forEach(({ row, text }) => {
      row.hidden = !words.every(word => text.includes(word));
      if (!row.hidden) visible += 1;
      list.append(row);
    });
    document.querySelector("#catalog-empty").hidden = visible !== 0;
    document.querySelector("#catalog-count").textContent = `${visible} de ${products.length} productos`;
  }

  search.addEventListener("input", filterProducts);
  sort.addEventListener("change", filterProducts);
  catalogTools.hidden = false;
  filterProducts();
}


document.querySelectorAll("[data-stepper]").forEach(control => {
  const input = control.querySelector("input");
  control.querySelectorAll("[data-step]").forEach(button => {
    button.addEventListener("click", () => {
      const value = input.valueAsNumber || Number(input.min);
      input.value = Math.min(Number(input.max), Math.max(Number(input.min), value + Number(button.dataset.step)));
      input.dispatchEvent(new Event("change", { bubbles: true }));
    });
  });
});

document.querySelectorAll("[data-password]").forEach(button => {
  const input = button.parentElement.querySelector("input");
  button.addEventListener("click", () => {
    const visible = input.type === "password";
    input.type = visible ? "text" : "password";
    button.textContent = visible ? "Ocultar" : "Mostrar";
    button.setAttribute("aria-pressed", String(visible));
  });
});

const toast = document.querySelector("#store-toast");
let toastTimer;
function notify(message) {
  clearTimeout(toastTimer);
  toast.textContent = message;
  toast.classList.add("is-visible");
  toastTimer = setTimeout(() => toast.classList.remove("is-visible"), 3600);
}

let cartQueue = Promise.resolve();
document.querySelectorAll(".add-to-cart").forEach(form => {
  form.addEventListener("submit", event => {
    event.preventDefault();
    const button = form.querySelector('[type="submit"]');
    button.disabled = true;
    cartQueue = cartQueue.then(async () => {
      try {
        const result = await post(form);
        document.querySelector("[data-cart-count]").textContent = result.count;
        notify(`${result.name} se agregó al carrito.`);
      } catch (error) {
        notify(error.message);
      } finally {
        button.disabled = false;
      }
    });
  });
});


const formatMoney = new Intl.NumberFormat("es-PE", { style: "currency", currency: "PEN" });
document.querySelectorAll(".cart-row-controls").forEach(form => {
  form.addEventListener("submit", event => {
    event.preventDefault();
    const action = event.submitter;
    if (!action) return;
    const buttons = form.querySelectorAll('button[name="action"]');
    cartQueue = cartQueue.then(async () => {
      buttons.forEach(button => { button.disabled = true; });
      try {
        const result = await post(form, action.value);
        if (result.count === 0) {
          window.location.reload();
          return;
        }
        const row = form.closest(".cart-row");
        if (action.value === "remove") row.remove();
        else row.querySelector("[data-subtotal]").textContent = formatMoney.format(result.subtotal);
        document.querySelector("[data-cart-total]").textContent = formatMoney.format(result.total);
        document.querySelector("[data-cart-count]").textContent = result.count;
        notify(action.value === "remove" ? "Producto retirado del carrito." : "Actualizamos la cantidad.");
      } catch (error) {
        notify(error.message);
      } finally {
        buttons.forEach(button => { button.disabled = false; });
      }
    });
  });
});
