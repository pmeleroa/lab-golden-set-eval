# Guía de etiquetado

Criterio para etiquetar los tickets del golden set. Se escribió antes que los casos: cada etiqueta de `dev.jsonl` y `test.jsonl` se puede justificar con estas reglas.

Los tickets son ficticios. Llegan al soporte de una aplicación web de suscripción cualquiera.

## Categorías

| Categoría | Cuándo |
|---|---|
| `facturación` | Cobros, importes, facturas, reembolsos, cambios de plan o de método de pago. El sistema funciona, pero hay que revisar o corregir algo del dinero. |
| `bug` | El producto no hace lo que debería: errores, pantallas que fallan, datos que se guardan mal o funciones que han dejado de funcionar. |
| `acceso` | La persona no puede entrar o gestionar quién entra: contraseña, verificación en dos pasos, cuenta bloqueada, invitaciones, permisos. |
| `petición` | Algo que hoy funciona como está diseñado y la persona quiere que funcione de otra forma, o una funcionalidad que no existe. |

## Reglas

1. **Se etiqueta por lo que hay que hacer para resolverlo, no por las palabras del ticket.** "La página de facturas da error" es `bug`, aunque diga "facturas": hay que arreglar la página, no revisar un cobro.
2. **Si el ticket mezcla dos problemas, gana el que impide usar el producto ahora.** Orden de desempate: `acceso` > `bug` > `facturación` > `petición`.
3. **Si algo funciona como está diseñado, es `petición`, aunque la persona lo llame error.** "No me deja exportar más de 1.000 filas" es `petición` si ese límite existe a propósito.
4. **Las dudas sin problema concreto se etiquetan por el tema.** "¿Cuándo se renueva mi plan?" es `facturación`.

## Campos de cada caso

- `id`: identificador único entre los dos splits.
- `input`: texto del ticket, tal cual lo escribiría el cliente.
- `expected`: una de las cuatro categorías.
- `dificultad`: `fácil` (una categoría evidente), `ambiguo` (encaja en dos y decide una regla) o `trampa` (las palabras del ticket apuntan a otra categoría).
- `nota`: por qué la etiqueta es esa, citando la regla cuando aplica.
