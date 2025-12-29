![Tests](https://img.shields.io/badge/tests-passing-brightgreen)
## koruspy 0.3.0/3.1
### Mudanças
- Padronização do sistema de erros, tornando o comportamento mais previsível.
- Ajustes em funções para maior consistência da API.
- Adição de testes automatizados com pytest, aumentando a confiabilidade da biblioteca.
- Adição da função `to_float` para conversão segura de valores para ponto flutuante.
## koruspy 0.3.0/3.1 En🇬🇧🇺🇸
### Changes
- Standardization of the error system, making behavior more predictable.
- Function adjustments to improve API consistency.
- Addition of automated tests using pytest, increasing library reliability.
- Added the `to_float` function for safe conversion of values to floating-point numbers.
🦀 Koruspy

Koruspy é uma biblioteca ultra-leve que traz a segurança do Rust e a elegância do Kotlin para o ecossistema Python.

Desenvolvida inteiramente via Termux, esta biblioteca elimina a necessidade de verificações manuais de None e blocos try/except repetitivos, utilizando o poder do Pattern Matching (Python 3.10+) e programação funcional.


---

🚀 Diferenciais

Zero NoneErrors: Use Option (Some ou nothing) para lidar com valores ausentes.

Result Pattern: Trate sucessos e falhas como dados, não como exceções que quebram o código.

Estilo Kotlin: Métodos encadeáveis como .map(), .Filter(), .and_then() e o operador de navegação segura .getattr().

Pipeline seguro: option_of agora trata corretamente None e nothing, preservando valores falsy como 0 e False.

Finalização clara: .finalize() encerra pipelines que já têm valor garantido.

Fallback elegante: .unwrap_or(default) e .unwrap_or_else(func) fornecem valores quando necessário.

Terminal Colorido: Substitua o print padrão pelo println com suporte a tipos e cores ANSI.



---

📦 Instalação

Como você está desenvolvendo no Termux ou em ambiente mobile, instale via modo editável:

pip install -e .


---

## 📝 Exemplos 3.1
option_of trata None e nothing, preservando falsy
```python
from koruspy import Some, nothing, option_of, println


idade = option_of(0, 18)
println(idade)  # Some(0)

idade2 = option_of(None, 18)
println(idade2)  # Some(18)
```
---
### ```to_float```

Converte o valor contido em `Some` para `float` de forma segura.

- Retorna `Some(float)` se a conversão for bem-sucedida.
- Retorna `NoneOption` caso a conversão falhe.
- Em `NoneOption`, o método retorna a própria instância.

Exemplo:

```python
Some("3.14").to_float()   # Some(3.14)
Some("abc").to_float()    # NoneOption
NoneOption.to_float()     # NoneOption
```
---
## Pipeline com Filter e finalize
```python
idade_valida = (
    option_of(idade2, 0)
    .get_value()
    .Filter(lambda x: x >= 18)
    .on_nothing(lambda: println("valor inválido"))
    .finalize()
)
println(idade_valida)
```
---
## Fallbacks
```python
val = option_of(None).unwrap_or(42)
println(val)  # 42

val2 = option_of(None).unwrap_or_else(lambda: 99)
println(val2)  # 99
```
## função `get_value()`:
```python
from koruspy import option_of

arquivos = ["config.yaml", "", None, "dados.json"]

for nome in arquivos:
    opt = option_of(nome)

    resultado = (
        opt
        .get_value()                      # 👈 retorna Option
        .Filter(lambda x: x.endswith((".yaml", ".json")))
        .map(lambda x: x.upper())
    )

    print(resultado)
```
> Regra de ouro:
> Use `get_value()` para permanecer dentro do pipeline `Option`.
> Use `finalize()` para sair do pipeline e obter o valor crua.

## English Version 🇺🇸🇬🇧:

🦀 Koruspy

Koruspy is an ultra-lightweight library that brings Rust’s safety and Kotlin’s elegance to the Python ecosystem.

Developed entirely via Termux, this library removes the need for manual None checks and repetitive try/except blocks by leveraging the power of Pattern Matching (Python 3.10+) and functional programming.


---

🚀 Highlights

Zero NoneErrors: Use Option (Some or nothing) to safely handle missing values.

Result Pattern: Handle success and failure as data, not as exceptions that break control flow.

Kotlin-style API: Chainable methods like .map(), .Filter(), .and_then(), and the safe navigation operator .getattr().

Safe pipeline: option_of now correctly handles None and nothing, while preserving falsy values such as 0 and False.

Clear finalization: .finalize() terminates pipelines when a value is guaranteed.

Elegant fallbacks: .unwrap_or(default) and .unwrap_or_else(func) provide values when needed.

Colored terminal output: Replace the standard print with println, with type-aware ANSI color support.



---

📦 Installation

If you are developing on Termux or in a mobile environment, install using editable mode:

pip install -e .


---

# 📝 Examples 3.1
option_of handles None and nothing, preserving falsy values
```python
from koruspy import Some, nothing, option_of, println


age = option_of(0, 18)
println(age)  # Some(0)

age2 = option_of(None, 18)
println(age2)  # Some(18)
```
---
### ```to_float```

Safely converts the value contained in `Some` to `float`.

- Returns `Some(float)` if the conversion succeeds.
- Returns `NoneOption` if the conversion fails.
- When called on `NoneOption`, the method returns itself.

Example:

```python
Some("3.14").to_float()   # Some(3.14)
Some("abc").to_float()    # NoneOption
NoneOption.to_float()     # NoneOption
```
---

# Pipeline with Filter and finalize
```python
valid_age = (
    option_of(age2, 0)
    .get_value()
    .Filter(lambda x: x >= 18)
    .on_nothing(lambda: println("invalid value"))
    .finalize()
)
println(valid_age)
```

---

# Fallbacks

```python
val = option_of(None).unwrap_or(42)
println(val)  # 42

val2 = option_of(None).unwrap_or_else(lambda: 99)
println(val2)  # 99
```
---
# function `get_value()`:
```python
from koruspy import option_of

user_inputs = ["42", "", None, "abc"]

for value in user_inputs:
    result = (
        option_of(value)
        .get_value()                 # 👈 returns a new Option
        .map(int)
        .Filter(lambda x: x > 0)
    )

    print(result)
```
> Rule of thumb:
> Use `get_value()` to stay inside the Option pipeline.
> Use `finalize()` to exit the pipeline and retrieve the raw value.