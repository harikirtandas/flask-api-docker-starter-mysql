// Validacion de formularios en el navegador con JSON Schema (Ajv), ANTES de
// llamar a la API -- mismas reglas que usa el backend (ver
// src/app/schemas/*.json y app/core/validator.py en el repo de la API),
// duplicadas a mano en web/schemas/*.json porque no hay build step que las
// comparta entre los dos proyectos (dos procesos/repos separados a
// proposito). Si llegan a divergir, gana el backend: esto es solo feedback
// instantaneo para el usuario, la API sigue siendo la que valida de verdad
// antes de tocar la base.
const Validador = (() => {
  const ajv = new window.ajv7({ allErrors: true });
  const compilados = {};

  async function compilar(nombreSchema) {
    if (!compilados[nombreSchema]) {
      const schema = await fetch(`/schemas/${nombreSchema}.json`).then((r) => r.json());
      compilados[nombreSchema] = ajv.compile(schema);
    }
    return compilados[nombreSchema];
  }

  // Traduce un error de Ajv a [campo, mensaje]. 'required' no tiene
  // instancePath util (apunta al objeto entero, no al campo que falta): el
  // nombre del campo viene en err.params.missingProperty -- mismo caso que
  // el 'required' de jsonschema-rs del lado del backend.
  function traducir(err) {
    if (err.keyword === 'required') {
      return [err.params.missingProperty, 'Requerido.'];
    }

    const campo = err.instancePath.replace(/^\//, '') || '?';

    if (err.keyword === 'minLength') {
      return [campo, err.params.limit <= 1 ? 'Requerido.' : `Minimo ${err.params.limit} caracteres.`];
    }
    if (err.keyword === 'maxLength') {
      return [campo, `Maximo ${err.params.limit} caracteres.`];
    }
    if (err.keyword === 'type') {
      const tipos = {
        string: 'Tiene que ser texto.',
        integer: 'Tiene que ser un numero entero.',
        number: 'Tiene que ser numerico.',
      };
      return [campo, tipos[err.params.type] || 'Tipo de dato invalido.'];
    }
    return [campo, 'Dato invalido.'];
  }

  return {
    // Devuelve null si datos es valido contra el schema, o { errores: {campo:
    // mensaje} } -- mismo shape que usa api.js para los 422 del backend, asi
    // que se puede pasar directo a mostrarError() sin distinguir el origen.
    async validar(nombreSchema, datos) {
      const validate = await compilar(nombreSchema);
      if (validate(datos)) return null;

      const errores = {};
      for (const err of validate.errors) {
        const [campo, mensaje] = traducir(err);
        if (!(campo in errores)) errores[campo] = mensaje;
      }
      return { errores };
    },
  };
})();
