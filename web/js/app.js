// Demo descartable: login/registro + CRUD de notas con edicion inline (PATCH).
// Reemplazar entero por la UI real del proyecto; api.js (agnostico al dominio)
// se conserva.

const $ = (sel) => document.querySelector(sel);

const vistaAuth = $('#vista-auth');
const vistaNotas = $('#vista-notas');
const formLogin = $('#form-login');
const formRegistro = $('#form-registro');
const formNota = $('#form-nota');
const listaNotas = $('#lista-notas');
const errorAuth = $('#error-auth');
const errorNota = $('#error-nota');
const btnLogout = $('#btn-logout');

function mostrarError(el, err) {
  el.textContent = err.errores
    ? Object.values(err.errores).join(' ')
    : err.message;
  el.hidden = false;
}

function ocultarError(el) {
  el.hidden = true;
  el.textContent = '';
}

async function refrescarVista() {
  if (API.haySesion()) {
    vistaAuth.hidden = true;
    vistaNotas.hidden = false;
    await cargarNotas();
  } else {
    vistaAuth.hidden = false;
    vistaNotas.hidden = true;
  }
}

async function cargarNotas() {
  const { datos } = await API.get('/notas');
  listaNotas.innerHTML = '';

  for (const nota of datos) {
    const li = document.createElement('li');
    li.className = 'nota';
    li.dataset.id = nota.id;
    li.innerHTML = `
      <div class="nota-vista">
        <strong>${nota.titulo}</strong>
        <p>${nota.cuerpo}</p>
        <button class="editar">Editar</button>
        <button class="borrar">Borrar</button>
      </div>
      <form class="nota-edicion" hidden>
        <input class="edit-titulo" value="${nota.titulo}" required>
        <textarea class="edit-cuerpo">${nota.cuerpo}</textarea>
        <button type="submit">Guardar</button>
        <button type="button" class="cancelar">Cancelar</button>
      </form>
    `;
    listaNotas.appendChild(li);
  }
}

formLogin.addEventListener('submit', async (e) => {
  e.preventDefault();
  ocultarError(errorAuth);
  const email = formLogin.email.value;
  const password = formLogin.password.value;
  try {
    await API.login(email, password);
    formLogin.reset();
    await refrescarVista();
  } catch (err) {
    mostrarError(errorAuth, err);
  }
});

formRegistro.addEventListener('submit', async (e) => {
  e.preventDefault();
  ocultarError(errorAuth);
  const nombre = formRegistro.nombre.value;
  const email = formRegistro.email.value;
  const password = formRegistro.password.value;

  // Validar en el navegador ANTES de llamar a la API: mismas reglas, sin
  // esperar la ida y vuelta de red para el error mas comun (campo vacio).
  const invalido = await Validador.validar('auth_register', { nombre, email, password });
  if (invalido) return mostrarError(errorAuth, invalido);

  try {
    await API.register(nombre, email, password);
    await API.login(email, password);
    formRegistro.reset();
    await refrescarVista();
  } catch (err) {
    mostrarError(errorAuth, err);
  }
});

btnLogout.addEventListener('click', async () => {
  await API.logout();
  await refrescarVista();
});

formNota.addEventListener('submit', async (e) => {
  e.preventDefault();
  ocultarError(errorNota);
  const titulo = formNota.titulo.value;
  const cuerpo = formNota.cuerpo.value;

  const invalido = await Validador.validar('notas', { titulo, cuerpo });
  if (invalido) return mostrarError(errorNota, invalido);

  try {
    await API.post('/notas', { titulo, cuerpo });
    formNota.reset();
    await cargarNotas();
  } catch (err) {
    mostrarError(errorNota, err);
  }
});

listaNotas.addEventListener('click', async (e) => {
  const li = e.target.closest('.nota');
  if (!li) return;
  const id = li.dataset.id;

  if (e.target.classList.contains('borrar')) {
    await API.del(`/notas/${id}`);
    await cargarNotas();
    return;
  }

  if (e.target.classList.contains('editar')) {
    li.querySelector('.nota-vista').hidden = true;
    li.querySelector('.nota-edicion').hidden = false;
    return;
  }

  if (e.target.classList.contains('cancelar')) {
    li.querySelector('.nota-vista').hidden = false;
    li.querySelector('.nota-edicion').hidden = true;
  }
});

listaNotas.addEventListener('submit', async (e) => {
  const form = e.target.closest('.nota-edicion');
  if (!form) return;
  e.preventDefault();

  const li = e.target.closest('.nota');
  const id = li.dataset.id;
  const titulo = form.querySelector('.edit-titulo').value;
  const cuerpo = form.querySelector('.edit-cuerpo').value;

  const invalido = await Validador.validar('notas', { titulo, cuerpo });
  if (invalido) return alert(Object.values(invalido.errores).join(' '));

  await API.patch(`/notas/${id}`, { titulo, cuerpo });
  await cargarNotas();
});

refrescarVista();
