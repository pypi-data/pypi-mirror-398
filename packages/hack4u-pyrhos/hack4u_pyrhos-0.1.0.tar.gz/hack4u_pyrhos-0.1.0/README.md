pip3 install hack4u

## Uso básico

### Listar todos los cursos

```python3
from hack4u import list_courses

for course in list_courses()
  print(course)
```

### Obtener un curso por nombre

```python3
from hack4u import get_course_by_name

course = get_course_by_name("Introducción a Linux")
print(course)
```

### Calcular duración total de cursos

```python3
from hack4u.utils import total_duration

print(f"Duración total: {total_duration()} horas
")
```
