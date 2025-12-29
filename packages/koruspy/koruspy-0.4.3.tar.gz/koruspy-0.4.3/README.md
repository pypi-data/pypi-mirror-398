# 🦀 Koruspy 0.4.0 – Atualização

Koruspy é uma biblioteca ultra-leve que traz **segurança do Rust** e **elegância do Kotlin** para o Python.  
Desenvolvida totalmente via Termux, ela elimina a necessidade de verificações manuais de `None` e blocos repetitivos `try/except`, usando **Pattern Matching** (Python 3.10+) e programação funcional.

---

## 🆕 Novidades

- funções assincronas foram adicionadas como `map_async()` ou `Filter_async()`
- `to_float` retorna `nothing` em caso de falha, mantendo consistência do singleton `_NoneOption`.
- Novos testes para reforçar a robustez:
  - Conversão inválida com `to_float`.
  - `Some.map` lidando com `None`.
  - `Filter` lidando com funções que levantam exceções.
  - `Result.map` captura exceções e retorna `Err`.

---

## 🛠️ Correções / Ajustes

- `Filter` agora retorna `nothing` de forma segura, sem propagar exceções.
- `Result.map` captura erros e retorna `Err` sem quebrar o fluxo.
- Garantida compatibilidade com pytest e identidade do singleton `nothing`.

---

## ✅ Testes

- Todos os 26 testes passam, cobrindo: `Some`, `nothing`, `Okay`, `Err`, `map`, `Filter`, `unwrap_or`, `to_float` e integração com generators.
- Casos de sucesso, falha e edge cases validados.

---

## 🚀 Diferenciais

- **Zero NoneErrors**: use `Option` (`Some` ou `nothing`) para lidar com valores ausentes.  
- **Result Pattern**: trate sucessos e falhas como dados, não exceções.  
- **Estilo Kotlin**: métodos encadeáveis como `.map()`, `.Filter()`, `.and_then()`, `.getattr()`.  
- **Pipeline seguro**: `option_of` trata corretamente `None` e `nothing`, preservando valores falsy (`0`, `False`).  
- **Fallback elegante**: `.unwrap_or(default)` e `.unwrap_or_else(func)`.  
- **Finalização clara**: `.finalize()` encerra pipelines com valor garantido.  
- **Terminal colorido**: substitua `print` por `println`, com suporte a tipos e cores ANSI.

---

## 📦 Instalação

Modo editável (Termux ou ambiente mobile):

```bash
pip install -e .
```
---
## 📝 exemplos
```option_of()```
```python
from koruspy import Some, nothing, option_of, println

idade = option_of(0, 18)
println(idade)  # Some(0)

idade2 = option_of(None, 18)
println(idade2)  # Some(18)
```
---
```to_float()```
```python
Some("3.14").to_float()   # Some(3.14)
Some("abc").to_float()    # nothing
nothing.to_float()        # nothing
```
--- 
Pipeline com ```.Filter``` e ```.finalize``
```python
idade_valida = (
    option_of(idade2, 0)
    .get_value()                        # mantém dentro do Option
    .Filter(lambda x: x >= 18)          # F maiúsculo
    .on_nothing(lambda: println("valor inválido"))
    .finalize()                         # sai do pipeline
)
println(idade_valida)
```
---
Fallbacks
```python
val = option_of(None, nothing).unwrap_or(42)
println(val)  # 42

val2 = option_of(None, nothing).unwrap_or_else(lambda: 99)
println(val2)  # 99
```
---
```get_value()``` em Loops
```python
from koruspy import option_of, println

arquivos = ["config.yaml", "", None, "dados.json"]

for nome in arquivos:
    resultado = (
        option_of(nome, "")                  # default obrigatório
        .get_value()                         # mantém Option
        .Filter(lambda x: x.endswith((".yaml", ".json")))
        .map(lambda x: x.upper())
        .unwrap_or("IGNORADO")               # fallback
    )
    println(resultado)
```
## ⚡ Funções Assíncronas (Async)

A koruspy também funciona com pipelines assíncronos, permitindo integrar `Some` e `nothing` com `asyncio` e coroutines de forma elegante e segura.  

### Principais funções async

| Método | Descrição |
| :--- | :--- |
| `map_async(fn)` | Transforma o valor interno usando uma função async. Retorna um novo `Some` ou `nothing`. |
| `Filter_async(cond)` | Filtra o valor com base em uma condição async. Retorna `Some` se a condição for verdadeira, `nothing` caso contrário. |
| `unwrap_or_else_async(fn)` | Retorna o valor interno ou executa a função async `fn()` para fornecer um fallback. |
| `on_nothing_async(fn)` | Executa uma função async quando o Option é `nothing`. |
| `if_present_async(fn)` | Executa uma função async quando o Option contém um valor (`Some`). |

### Exemplos de uso
```python
import asyncio
from koruspy import Some, nothing

async def fetch_data(x):
    # Simula uma operação assíncrona, retorna Some ou nothing
    await asyncio.sleep(0.1)
    if x > 0:
        return Some(x * 2)
    return nothing

async def is_multiple_of_five(x):
    await asyncio.sleep(0.05)
    return x % 5 == 0

async def default_value():
    await asyncio.sleep(0.05)
    return 42

async def main():
    inputs = [3, 5, -1, 10]

    # Busca dados assíncronos
    results = await asyncio.gather(*(fetch_data(i) for i in inputs))

    # Pipeline async completo
    for r in results:
        r = await r.Filter_async(is_multiple_of_five) \
                   .map_async(lambda x: x + 1) \
                   .unwrap_or_else_async(default_value)

        print(r)

asyncio.run(main())
```
### resultado esperado
```
42    # 3*2=6 não é múltiplo de 5 → fallback
11    # 5*2=10 é múltiplo de 5 → 10+1=11
42    # -1*2=-2 não é múltiplo de 5 → fallback
21    # 10*2=20 é múltiplo de 5 → 20+1=21
```
---
```python
import asyncio
from koruspy import Some, nothing

async def is_even(x):
    await asyncio.sleep(0.1)
    return x % 2 == 0

async def multiply(x):
    await asyncio.sleep(0.1)
    return x * 10

async def default_value():
    await asyncio.sleep(0.1)
    return 42

async def main():
    val = Some(5)
    val2 = nothing

    # Pipeline async com map_async e Filter_async
    res1 = await val.Filter_async(is_even).map_async(multiply)
    res2 = await val2.unwrap_or_else_async(default_value)

    print(res1)  # Some(50) se passar o filter
    print(res2)  # 42

asyncio.run(main())
```
> Dica: funções async podem ser combinadas em pipelines paralelos usando asyncio.gather, garantindo execução eficiente mesmo com múltiplas operações assíncronas.
> Dica: use get_value() para permanecer no fluxo Option. Use finalize() para obter o valor cru e sair do pipeline.
## English-version 🇺🇸🇬🇧
---
# 🦀 Koruspy 0.4.0 – Update

Koruspy is an ultra-lightweight library bringing Rust safety and Kotlin elegance to Python.
Eliminates repetitive None checks and try/except blocks via Pattern Matching (Python 3.10+) and functional programming.


---

## 🆕 New Features

- to_float now returns nothing on failure, ensuring singleton _NoneOption consistency.

- Additional tests added to reinforce library robustness:

Invalid conversion with to_float.

Some.map handling None.

Filter handling functions that raise exceptions.

Result.map captures exceptions and returns Err.




---

## 🛠️ Fixes / Adjustments

Filter keeps safe behavior, returning nothing instead of propagating exceptions.

Result.map captures errors and returns Err instead of breaking the flow.

Adjustments to ensure pytest compatibility and singleton nothing identity.



---

## ✅ Tests

All 26 current tests passed, covering: Some, nothing, Okay, Err, map, Filter, unwrap_or, to_float and generator integration.

Includes validation of success cases, failure cases, and edge cases.



---

## 🚀 Highlights

Zero NoneErrors: use Option (Some or nothing) to safely handle missing values.

Result Pattern: handle success/failure as data, not exceptions.

Kotlin-style API: chainable methods like .map(), .Filter(), .and_then(), .getattr().

Safe pipeline: option_of correctly handles None and nothing, preserving falsy values (0, False).

Elegant fallbacks: .unwrap_or(default) and .unwrap_or_else(func).

Clear finalization: .finalize() terminates pipelines with guaranteed values.

Colored terminal output: replace print with println, with type-aware ANSI colors.



---

## 📦 Installation

Editable mode (Termux or mobile environment):

pip install -e .


---

## 📝 Examples

option_of with default

```python
from koruspy import Some, nothing, option_of, println

age = option_of(0, 18)
println(age)  # Some(0)

age2 = option_of(None, 18)
println(age2)  # Some(18)
```

---

to_float
```python
Some("3.14").to_float()   # Some(3.14)
Some("abc").to_float()    # nothing
nothing.to_float()        # nothing
```

---

## Pipeline with Filter and finalize

```python
valid_age = (
    option_of(age2, 0)
    .get_value()                        # stays in Option flow
    .Filter(lambda x: x >= 18)          # F uppercase
    .on_nothing(lambda: println("invalid value"))
    .finalize()                          # exits pipeline
)
println(valid_age)
```

---

## Fallbacks

```python
val = option_of(None, 42).unwrap_or(42)
println(val)  # 42

val2 = option_of(None, 99).unwrap_or_else(lambda: 99)
println(val2)  # 99
```

---

get_value() in loops

```python
from koruspy import option_of, println

files = ["config.yaml", "", None, "dados.json"]

for name in files:
    result = (
        option_of(name, "")                  # default required
        .get_value()                         # stays in Option
        .Filter(lambda x: x.endswith((".yaml", ".json")))
        .map(lambda x: x.upper())
        .unwrap_or("IGNORED")                # fallback
    )
    println(result)
```    
## ⚡ Asynchronous Functions (Async)

Koruspy also supports asynchronous pipelines, allowing you to integrate `Some` and `nothing` with `asyncio` and coroutines in a clean and safe way.  

### Main async methods

| Method | Description |
| :--- | :--- |
| `map_async(fn)` | Transforms the internal value using an async function. Returns a new `Some` or `nothing`. |
| `Filter_async(cond)` | Filters the value based on an async condition. Returns `Some` if the condition is true, otherwise `nothing`. |
| `unwrap_or_else_async(fn)` | Returns the internal value or executes the async function `fn()` to provide a fallback. |
| `on_nothing_async(fn)` | Executes an async function when the Option is `nothing`. |
| `if_present_async(fn)` | Executes an async function when the Option contains a value (`Some`). |

### Usage examplew
```python
import asyncio
from koruspy import Some, nothing

async def fetch_data(x):
    # Simulate an async operation, return Some or nothing
    await asyncio.sleep(0.1)
    if x > 0:
        return Some(x * 2)
    return nothing

async def is_multiple_of_five(x):
    await asyncio.sleep(0.05)
    return x % 5 == 0

async def default_value():
    await asyncio.sleep(0.05)
    return 42

async def main():
    inputs = [3, 5, -1, 10]

    # Fetch async data
    results = await asyncio.gather(*(fetch_data(i) for i in inputs))

    # Full async pipeline
    for r in results:
        r = await r.Filter_async(is_multiple_of_five) \
                   .map_async(lambda x: x + 1) \
                   .unwrap_or_else_async(default_value)

        print(r)

asyncio.run(main())
```
### Expected output
```
42    # 3*2=6 is not multiple of 5 → fallback
11    # 5*2=10 is multiple of 5 → 10+1=11
42    # -1*2=-2 is not multiple of 5 → fallback
21    # 10*2=20 is multiple of 5 → 20+1=21
```
---
```python
import asyncio
from koruspy import Some, nothing

async def is_even(x):
    await asyncio.sleep(0.1)
    return x % 2 == 0

async def multiply(x):
    await asyncio.sleep(0.1)
    return x * 10

async def default_value():
    await asyncio.sleep(0.1)
    return 42

async def main():
    val = Some(5)
    val2 = nothing

    # Async pipeline with map_async and Filter_async
    res1 = await val.Filter_async(is_even).map_async(multiply)
    res2 = await val2.unwrap_or_else_async(default_value)

    print(res1)  # Some(50) if the filter passes
    print(res2)  # 42

asyncio.run(main())
```
> Tip: Async functions can be combined in parallel pipelines using asyncio.gather, allowing efficient execution even with multiple asynchronous operations.
> Tip: use get_value() to stay in the Option pipeline. Use finalize() to exit the pipeline and retrieve raw value.